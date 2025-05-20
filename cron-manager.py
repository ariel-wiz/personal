#!/usr/bin/env python3
"""
Enhanced Cron Manager Script - Lightweight orchestrator for scheduled tasks
This script only handles scheduling and execution - all business logic stays in respective modules.
"""

import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Union, Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import json
import traceback

from notion_py.summary.summary import is_monthly_summary_exists
from notion_py.summary.weekly_summary import is_weekly_summary_exists
from logger import logger

# Configure logging first
LOG_DIR = '/Users/ariel/Documents/cron-files'
LOG_FILE = os.path.join(LOG_DIR, 'cron-manager.log')
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'cron-manager.err')
EXECUTION_LOG_FILE = os.path.join(LOG_DIR, 'execution.log')

try:
    # Add project root to Python path
    project_root = '/Users/ariel/PycharmProjects/personal'
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Import all the functions we need to schedule
    from notion_py.notion import (
        update_garmin_info, uncheck_done_weekly_task_id, copy_done_from_daily_to_copied_tasks,
        create_daily_pages, copy_pages_from_other_db_if_needed, get_expenses_to_notion,
        unset_done_recurring_tasks, create_recurring_tasks_summary, copy_book_summary,
        create_weekly_summary_standalone
)

    IMPORTS_AVAILABLE = True
    logger.info("Successfully imported all notion functions")

except ImportError as e:
    logger.error(f"Failed to import notion modules: {e}")
    IMPORTS_AVAILABLE = False


class Frequency(Enum):
    DAILY = "daily"
    WEEKLY_SATURDAY = "saturday"
    WEEKLY_SUNDAY = "sunday"
    WEEKLY_MONDAY = "monday"
    WEEKLY_TUESDAY = "tuesday"
    WEEKLY_WEDNESDAY = "wednesday"
    WEEKLY_THURSDAY = "thursday"
    WEEKLY_FRIDAY = "friday"
    CONDITIONAL = "conditional"


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class DeferredCheck:
    """Configuration for checking if a task needs to be re-run after N days"""
    check_func: Callable[[], bool]  # Function that returns True if task should be re-run
    check_following_days: int  # Number of days to keep checking (1 = tomorrow, 2 = next 2 days)
    description: str  # Human readable description


@dataclass
class TaskResult:
    """Result of task execution"""
    task_name: str
    success: bool
    message: str
    duration: float
    error: Optional[Exception] = None
    retry_count: int = 0


@dataclass
class TaskConfig:
    """Lightweight task configuration - only scheduling info, no business logic"""
    name: str
    function_to_run: Callable
    frequency: Union[str, List[str], Frequency]
    priority: TaskPriority = TaskPriority.NORMAL
    enabled: bool = True
    function_kwargs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    conditional_run_func: Optional[Callable[[], bool]] = None
    retry_count: int = 1
    retry_delay_seconds: int = 60
    timeout_seconds: Optional[int] = None
    deferred_checks: List[DeferredCheck] = field(default_factory=list)

    def should_run_today(self, today_date: str, today_weekday: str) -> bool:
        """Check if task should run today based on frequency"""
        # Handle conditional tasks
        if self.frequency == Frequency.CONDITIONAL:
            return self.conditional_run_func() if self.conditional_run_func else False

        # Handle list of monthly dates (e.g. ["1/*", "15/*"])
        if isinstance(self.frequency, list):
            day_of_month = today_date.split('/')[0]
            return any(day_of_month == date.split('/')[0] for date in self.frequency)

        # Handle monthly frequency (DD/* format)
        if isinstance(self.frequency, str) and '/*' in self.frequency:
            day_of_month = self.frequency.split('/')[0]
            return today_date.split('/')[0] == day_of_month

        # Handle daily/weekly frequency
        try:
            if isinstance(self.frequency, str):
                freq = Frequency(self.frequency.lower())
            else:
                freq = self.frequency

            return (freq == Frequency.DAILY or
                    today_weekday == freq.value.lower())
        except ValueError:
            logger.warning(f"Invalid frequency format for {self.name}: {self.frequency}")
            return False


class TaskExecutor:
    """Handles task execution with retry logic, timeouts, and error handling"""

    def execute_task(self, task: TaskConfig) -> TaskResult:
        """Execute a single task with retry logic"""
        start_time = time.time()
        last_error = None

        # Retry loop
        for attempt in range(task.retry_count + 1):
            try:
                if attempt > 0:
                    # Exponential backoff
                    delay = task.retry_delay_seconds * (2 ** (attempt - 1))
                    logger.info(
                        f"Retrying {task.name} (attempt {attempt + 1}) after {delay}s delay")
                    time.sleep(delay)

                # Execute the task with timeout
                if task.timeout_seconds:
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(task.function_to_run, **task.function_kwargs)
                        result = future.result(timeout=task.timeout_seconds)
                else:
                    result = task.function_to_run(**task.function_kwargs)

                # Success - if no exception was raised, consider it successful
                # regardless of return value (unless it explicitly returns False)
                success = result is not False  # Allow None, True, or any other value as success

                duration = time.time() - start_time
                return TaskResult(
                    task_name=task.name,
                    success=success,
                    message=f"Completed {'successfully' if success else 'with False return'} on attempt {attempt + 1}",
                    duration=duration,
                    retry_count=attempt
                )

            except TimeoutError:
                last_error = TimeoutError(f"Task timed out after {task.timeout_seconds}s")
                logger.error(f"Attempt {attempt + 1} timed out for {task.name}")
            except Exception as e:
                last_error = e
                logger.error(f"Attempt {attempt + 1} failed for {task.name}: {str(e)}")

                if attempt == task.retry_count:
                    # Final failure
                    duration = time.time() - start_time
                    return TaskResult(
                        task_name=task.name,
                        success=False,
                        message=f"Failed after {attempt + 1} attempts: {str(e)}",
                        duration=duration,
                        error=last_error,
                        retry_count=attempt
                    )

        # Should not reach here, but just in case
        duration = time.time() - start_time
        return TaskResult(
            task_name=task.name,
            success=False,
            message=f"Failed after all retry attempts: {str(last_error)}",
            duration=duration,
            error=last_error,
            retry_count=task.retry_count
        )


class TaskScheduler:
    """Main scheduler that manages task execution with dependency resolution"""

    def __init__(self, tasks: List[TaskConfig]):
        self.tasks = {task.name: task for task in tasks}
        self.executor = TaskExecutor()
        self.today_date = datetime.now().strftime("%d/%m")
        self.today_weekday = datetime.now().strftime("%A").lower()
        self.execution_results: Dict[str, TaskResult] = {}

    def run_all_tasks(self) -> Dict[str, TaskResult]:
        """Run all scheduled tasks with dependency resolution and deferred checks"""
        logger.info(f"Starting task scheduler on {self.today_date}")

        # 1. Filter tasks that should run today (regular schedule)
        regular_tasks = [
            task for task in self.tasks.values()
            if task.enabled and task.should_run_today(self.today_date, self.today_weekday)
        ]

        # 2. Check for deferred tasks that need to run
        deferred_tasks = self._get_deferred_tasks_for_today()

        # 3. Combine and deduplicate tasks
        all_tasks = self._deduplicate_tasks(regular_tasks + deferred_tasks)

        if not all_tasks:
            logger.info("No tasks scheduled to run today")
            return {}

        logger.info(f"{len(all_tasks)} tasks to run: {[t.name for t in all_tasks]}")

        # 4. Sort by priority and resolve dependencies
        execution_order = self._resolve_dependencies(all_tasks)

        # 5. Execute tasks
        for task in execution_order:
            logger.info(f"===== Executing task: {task.name} =====")
            result = self.executor.execute_task(task)
            self.execution_results[task.name] = result

            # Log result
            if result.success:
                logger.info(f"✓ {task.name} completed in {result.duration:.2f}s")
            else:
                logger.error(f"✗ {task.name} failed: {result.message}")

                # Check if this failure should stop dependent tasks
                if task.priority == TaskPriority.CRITICAL:
                    logger.error(f"Critical task {task.name} failed, stopping execution")
                    break

        # Log summary
        self._log_execution_summary()

        return self.execution_results

    def _get_deferred_tasks_for_today(self) -> List[TaskConfig]:
        """Check all tasks with deferred_checks to see if any should run today"""
        deferred_tasks = []
        current_date = datetime.now().date()

        for task in self.tasks.values():
            if not task.deferred_checks or not task.enabled:
                continue

            for deferred_check in task.deferred_checks:
                # Check each day from 1 to check_days
                for days_ago in range(1, deferred_check.check_following_days + 1):
                    check_date = current_date - timedelta(days=days_ago)

                    # See if the task was supposed to run on that day
                    check_date_str = check_date.strftime("%d/%m")
                    check_weekday = check_date.strftime("%A").lower()

                    if task.should_run_today(check_date_str, check_weekday):
                        # Task was supposed to run on check_date, see if it needs re-running
                        try:
                            if deferred_check.check_func():
                                logger.info(
                                    f"Deferred check triggered for {task.name}: {deferred_check.description}")
                                deferred_tasks.append(task)
                                break  # Only run once, even if multiple days trigger
                        except Exception as e:
                            logger.error(f"Error running deferred check for {task.name}: {e}")
                            continue

        return deferred_tasks

    def _deduplicate_tasks(self, tasks: List[TaskConfig]) -> List[TaskConfig]:
        """Remove duplicate tasks (same task might be scheduled normally AND by deferred check)"""
        seen_names = set()
        deduplicated = []

        for task in tasks:
            if task.name not in seen_names:
                deduplicated.append(task)
                seen_names.add(task.name)

        return deduplicated

    def _resolve_dependencies(self, tasks: List[TaskConfig]) -> List[TaskConfig]:
        """Resolve task dependencies and return execution order"""
        # Sort by priority first
        tasks_by_priority = sorted(tasks, key=lambda t: t.priority.value, reverse=True)

        # Simple dependency resolution
        execution_order = []
        remaining_tasks = tasks_by_priority.copy()

        while remaining_tasks:
            # Find tasks with no unfulfilled dependencies
            ready_tasks = []
            for task in remaining_tasks:
                dependencies_met = all(
                    dep_name in [t.name for t in execution_order]
                    for dep_name in task.dependencies
                )
                if dependencies_met:
                    ready_tasks.append(task)

            if not ready_tasks:
                # Circular dependency or missing dependency
                logger.warning("Unable to resolve all dependencies, adding remaining tasks")
                execution_order.extend(remaining_tasks)
                break

            # Add ready tasks to execution order
            execution_order.extend(ready_tasks)
            for task in ready_tasks:
                remaining_tasks.remove(task)

        return execution_order

    def _log_execution_summary(self):
        """Log summary of task execution"""
        successful = [r for r in self.execution_results.values() if r.success]
        failed = [r for r in self.execution_results.values() if not r.success]

        logger.info(f"\n{'=' * 50}")
        logger.info(f"EXECUTION SUMMARY")
        logger.info(f"{'=' * 50}")
        logger.info(f"Total tasks: {len(self.execution_results)}")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")

        if successful:
            logger.info("\nSuccessful tasks:")
            for result in successful:
                logger.info(f"  ✓ {result.task_name} ({result.duration:.2f}s)")

        if failed:
            logger.error("\nFailed tasks:")
            for result in failed:
                logger.error(f"  ✗ {result.task_name}: {result.message}")

        # Write to execution log
        with open(EXECUTION_LOG_FILE, 'a') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            summary = {
                'timestamp': timestamp,
                'total': len(self.execution_results),
                'successful': len(successful),
                'failed': len(failed),
                'details': {name: {'success': r.success, 'duration': r.duration}
                            for name, r in self.execution_results.items()}
            }
            f.write(json.dumps(summary) + '\n')


# ==========================================
# CONDITION FUNCTIONS - ALL SCHEDULING LOGIC HERE
# ==========================================

def should_copy_random_book() -> bool:
    """Simple random condition for book copying"""
    import random
    return random.random() < 0.1  # 10% chance per day


def should_create_monthly_summary() -> bool:
    """Check if monthly summary should be created"""
    if not IMPORTS_AVAILABLE:
        return False

    try:
        from expense.notion_expense_service import NotionExpenseService
        from notion_py.notion_globals import expense_tracker_db_id, monthly_category_expense_db

        expense_service = NotionExpenseService(
            expense_tracker_db_id=expense_tracker_db_id,
            monthly_category_expense_db_id=monthly_category_expense_db
        )
        return expense_service.should_create_monthly_summary()
    except Exception as e:
        logger.error(f"Error checking monthly summary condition: {e}")
        return False


def is_end_of_month_window(days_before: int = 7) -> bool:
    """Check if we're in the end-of-month window"""
    current_date = datetime.now()
    if current_date.month == 12:
        next_month = datetime(current_date.year + 1, 1, 1)
    else:
        next_month = datetime(current_date.year, current_date.month + 1, 1)

    days_until_next_month = (next_month.date() - current_date.date()).days
    return days_until_next_month <= days_before


# ==========================================
# SCHEDULED TASK FUNCTIONS - BUSINESS LOGIC
# ==========================================

def update_monthly_categories():
    """Update monthly expense categories"""
    if not IMPORTS_AVAILABLE:
        raise ImportError("Required modules not available")

    try:
        from expense.notion_expense_service import NotionExpenseService
        from notion_py.notion_globals import expense_tracker_db_id, monthly_category_expense_db

        expense_service = NotionExpenseService(
            expense_tracker_db_id=expense_tracker_db_id,
            monthly_category_expense_db_id=monthly_category_expense_db
        )
        expense_service.backfill_monthly_expenses(months_back=4)
        logger.info("Successfully updated monthly categories")
    except Exception as e:
        logger.error(f"Error updating monthly categories: {e}")
        raise


def create_monthly_summary_and_daily_task():
    """Creates monthly summary page and adds a daily task for review"""
    if not IMPORTS_AVAILABLE:
        raise ImportError("Required modules not available")

    try:
        from notion_py.summary.summary import create_monthly_summary_page
        from notion_py.helpers.notion_common import (
            create_page_with_db_dict_and_children_block, generate_icon_url
        )
        from notion_py.helpers.notion_children_blocks import generate_page_content_page_notion_link
        from notion_py.notion_globals import daily_tasks_db_id, IconType, IconColor
        from variables import Projects
        from common import today

        # Create monthly summary
        summary_response = create_monthly_summary_page()
        summary_page_id = summary_response['id']

        # Create daily task for review
        task_dict = {
            "Task": "Review Monthly Summary",
            "Project": Projects.notion,
            "Due": today.isoformat(),
            "Icon": generate_icon_url(IconType.CHECKLIST, IconColor.BLUE)
        }

        # Create daily task with link to summary
        children_block = generate_page_content_page_notion_link(summary_page_id)
        response = create_page_with_db_dict_and_children_block(
            daily_tasks_db_id,
            task_dict,
            children_block
        )

        logger.info(f"Created monthly summary review task with ID {response['id']}")
        return summary_page_id, response['id']

    except Exception as e:
        logger.error(f"Error creating monthly summary and daily task: {str(e)}")
        raise


def update_goals_recap():
    """Update goals recap page for end of month"""
    if not IMPORTS_AVAILABLE:
        raise ImportError("Required modules not available")

    try:
        from notion_py.helpers.notion_common import update_page
        from notion_py.helpers.notion_payload import uncheck_done_set_today_payload
        from notion_py.notion_globals import goals_recap_page_id

        update_page(goals_recap_page_id, uncheck_done_set_today_payload)
        logger.info("Successfully updated goals recap page")

    except Exception as e:
        logger.error(f"Error updating goals recap: {e}")
        raise


# ==========================================
# TASK CONFIGURATION - ONLY SCHEDULING INFO
# ==========================================

if IMPORTS_AVAILABLE:
    TASK_CONFIGURATIONS = [
        # Core Daily Tasks
        TaskConfig(
            name="Garmin Update",
            function_to_run=update_garmin_info,
            function_kwargs={'should_track': True},
            frequency=Frequency.DAILY,
            priority=TaskPriority.HIGH,
            retry_count=2,
            timeout_seconds=60
        ),

        TaskConfig(
            name="Handle Done Tasks",
            function_to_run=copy_done_from_daily_to_copied_tasks,
            function_kwargs={'should_track': True},
            frequency=Frequency.DAILY,
            priority=TaskPriority.NORMAL,
            retry_count=2,
        ),

        TaskConfig(
            name="Create Recurring Tasks Summary",
            function_to_run=create_recurring_tasks_summary,
            function_kwargs={'should_track': True},
            frequency=Frequency.DAILY,
            priority=TaskPriority.NORMAL,
            retry_count=2,
            timeout_seconds=60
        ),

        TaskConfig(
            name="Get Expenses",
            function_to_run=get_expenses_to_notion,
            function_kwargs={'should_track': True},
            frequency=Frequency.DAILY,
            priority=TaskPriority.NORMAL,
            retry_count=3,
            timeout_seconds=1000
        ),

        # Weekly Maintenance Tasks
        TaskConfig(
            name="Uncheck Done Tasks",
            function_to_run=uncheck_done_weekly_task_id,
            function_kwargs={'should_track': True},
            frequency=Frequency.WEEKLY_SATURDAY,
            priority=TaskPriority.NORMAL,
            retry_count=2,
        ),

        TaskConfig(
            name="Create Daily Pages",
            function_to_run=create_daily_pages,
            function_kwargs={'should_track': True},
            frequency=Frequency.WEEKLY_TUESDAY,
            priority=TaskPriority.NORMAL,
            retry_count=2,
        ),

        TaskConfig(
            name="Copy Pages",
            function_to_run=copy_pages_from_other_db_if_needed,
            function_kwargs={'should_track': True},
            frequency=Frequency.WEEKLY_TUESDAY,
            priority=TaskPriority.NORMAL,
            dependencies=["Create Daily Pages"],
            retry_count=2,
        ),

        TaskConfig(
            name="Unset Done Recurring Tasks",
            function_to_run=unset_done_recurring_tasks,
            function_kwargs={'should_track': True},
            frequency=Frequency.WEEKLY_TUESDAY,
            priority=TaskPriority.NORMAL,
            retry_count=2,
        ),

        # Monthly/End-of-month tasks
        TaskConfig(
            name="Update Monthly Categories",
            function_to_run=update_monthly_categories,
            frequency=Frequency.CONDITIONAL,
            conditional_run_func=should_create_monthly_summary,
            priority=TaskPriority.HIGH,
            dependencies=["Get Expenses"],
            retry_count=2,
        ),

        TaskConfig(
            name="Create Monthly Summary",
            function_to_run=create_monthly_summary_and_daily_task,
            frequency=Frequency.CONDITIONAL,
            conditional_run_func=should_create_monthly_summary,
            priority=TaskPriority.HIGH,
            dependencies=["Update Monthly Categories"],
            retry_count=1,
            deferred_checks=[
                DeferredCheck(
                    check_func=is_monthly_summary_exists,
                    check_following_days=5,
                    description="Review Monthly Summary task missing from today's tasks"
                )
            ]
        ),
        TaskConfig(
            name="Create Weekly Summary",
            function_to_run=create_weekly_summary_standalone,
            frequency=Frequency.WEEKLY_SUNDAY,
            priority=TaskPriority.HIGH,
            retry_count=2,
            deferred_checks=[
                DeferredCheck(
                    check_func=is_weekly_summary_exists,
                    check_following_days=3,
                    description="Create Weekly summary task missing for this week"
                )
            ]
        ),

        TaskConfig(
            name="Update Goals Recap",
            function_to_run=update_goals_recap,
            frequency=Frequency.CONDITIONAL,
            conditional_run_func=lambda: is_end_of_month_window(7),
            priority=TaskPriority.HIGH,
            retry_count=2,
        ),
    ]
else:
    TASK_CONFIGURATIONS = []


# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def check_supervisor_status():
    """Check if supervisord is running"""
    try:
        result = subprocess.run(
            "brew services list | grep supervisor",
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return "started" in result.stdout
    except Exception as e:
        logger.error(f"Error checking supervisor status: {e}")
        return False


def start_supervisor():
    """Start supervisord if it's not running"""
    try:
        subprocess.run("brew services start supervisor", shell=True, check=True)
        logger.info("Successfully started supervisor")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start supervisor: {e}")
        return False


# ==========================================
# MAIN EXECUTION
# ==========================================

def main():
    """Main execution function"""
    try:
        # Log the start
        date_str = datetime.now().strftime("%d/%m")
        logger.info(f"\n{'=' * 80}")
        logger.info(f"CRON MANAGER STARTING - {date_str}")
        logger.info(f"{'=' * 80}")
        logger.info(f"Imports available: {IMPORTS_AVAILABLE}")

        if not IMPORTS_AVAILABLE:
            logger.error("Cannot run without imports - exiting")
            return 1

        # Ensure supervisor is running
        if not check_supervisor_status():
            if not start_supervisor():
                logger.warning("Failed to start supervisor, continuing anyway")

        # Initialize and run the scheduler
        scheduler = TaskScheduler(TASK_CONFIGURATIONS)
        results = scheduler.run_all_tasks()

        # Final summary
        if results:
            success_count = sum(1 for r in results.values() if r.success)
            total_count = len(results)
            logger.info(f"EXECUTION COMPLETE: {success_count}/{total_count} tasks successful")
        else:
            logger.info("No tasks were executed today")

        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    # Write start log
    with open("/Users/ariel/Documents/cron-files/daily-run.log", "a") as f:
        f.write(f"Cron manager started at {datetime.now()}\n")

    sys.exit(main())