from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional

from common import seconds_to_hours_minutes, parse_duration_to_seconds, format_duration_days
from notion_py.helpers.notion_children_blocks import create_column_block, create_metrics_single_paragraph, \
    create_toggle_stats_block, create_two_column_section, create_section_text_with_bullet, create_toggle_heading_block
from notion_py.helpers.notion_common import get_db_pages
from notion_py.summary.base_component import BaseComponent


class TaskFields:
    """Constants for task field names"""
    DAILY_COMPLETED = "daily_completed"
    DAILY_TOTAL = "daily_total"
    DAILY_COMPLETION_RATE = "daily_completion_rate"
    DAILY_CREATED = "daily_created"
    REGULAR_COMPLETED = "regular_completed"
    REGULAR_TOTAL = "regular_total"
    REGULAR_COMPLETION_RATE = "regular_completion_rate"
    AVG_COMPLETION_TIME = "avg_completion_time"
    NEW_TASKS = "new_tasks"
    OVERDUE_TASKS = "overdue_tasks"
    PROJECTS = "projects"
    DAILY_INSPIRATION_RATE = "daily_inspiration_rate"


class TasksComponent(BaseComponent):
    def __init__(self, daily_tasks_db_id: str, tasks_db_id: str, daily_tasks_view_link: str, target_date: Optional[date] = None):
        super().__init__(target_date, TaskFields)
        self.daily_tasks_db_id = daily_tasks_db_id
        self.tasks_db_id = tasks_db_id
        self.daily_tasks_view_link = daily_tasks_view_link

    def _initialize_metrics(self):
        """Initialize task metrics for current and previous months"""
        self._current_metrics = self._get_month_metrics(self.target_date)
        self._previous_metrics = self._get_month_metrics(self.previous_month)

    def _get_month_metrics(self, target_date: date) -> Dict:
        """Get all metrics for a given month"""
        regular_tasks = self._get_pages_for_month(self.tasks_db_id, target_date, date_property="Due")
        daily_tasks = self._get_pages_for_month(self.daily_tasks_db_id, target_date, date_property="Due")

        return {
            **self._calculate_task_metrics(regular_tasks, daily_tasks),
            TaskFields.PROJECTS: self._get_project_breakdown(regular_tasks)
        }

    def _calculate_task_metrics(self, regular_tasks: List[Dict], daily_tasks: List[Dict]) -> Dict:
        """Calculate core task metrics"""
        daily_stats = self._calculate_completion_stats(daily_tasks)
        regular_stats = self._calculate_completion_stats(regular_tasks)
        daily_creation_stats = self._get_daily_task_creation_stats(daily_tasks)

        return {
            TaskFields.DAILY_COMPLETED: daily_stats['completed'],
            TaskFields.DAILY_TOTAL: daily_stats['total'],
            TaskFields.DAILY_COMPLETION_RATE: daily_stats['completion_rate'],
            TaskFields.DAILY_CREATED: daily_creation_stats['total_created'],
            TaskFields.REGULAR_COMPLETED: regular_stats['completed'],
            TaskFields.REGULAR_TOTAL: regular_stats['total'],
            TaskFields.REGULAR_COMPLETION_RATE: regular_stats['completion_rate'],
            TaskFields.AVG_COMPLETION_TIME: regular_stats['avg_completion_time'],
            TaskFields.NEW_TASKS: len(self._get_new_tasks_in_period(self.tasks_db_id, self.target_date)),
            TaskFields.OVERDUE_TASKS: len(self._get_overdue_tasks(self.tasks_db_id)),
            TaskFields.DAILY_INSPIRATION_RATE: self._calculate_daily_inspiration_rate(daily_tasks)
        }

    def _calculate_completion_stats(self, tasks: List[Dict]) -> Dict:
        """Calculate task completion statistics"""
        total = len(tasks)
        completed_tasks = []
        completion_times = []

        for task in tasks:
            if self._is_task_completed(task):
                completed_tasks.append(task)
                completion_time = self._calculate_task_completion_time(task)
                if completion_time:
                    completion_times.append(completion_time)

        return {
            'completed': len(completed_tasks),
            'total': total,
            'completion_rate': self._calculate_completion_rate(len(completed_tasks), total),
            'avg_completion_time': self._calculate_avg_time(completion_times)
        }

    def _is_task_completed(self, task: Dict) -> bool:
        """Check if a task is marked as completed"""
        return task['properties'].get('Done', {}).get('checkbox', False)

    def _calculate_task_completion_time(self, task: Dict) -> Optional[float]:
        """Calculate time from due date to completion"""
        try:
            if not self._is_task_completed(task):
                return None

            due_date = datetime.fromisoformat(task['properties'].get('Due', {}).get('date', {}).get('start'))
            completed_time = datetime.fromisoformat(task['last_edited_time'].replace('Z', '+00:00'))

            # Calculate days
            time_diff = completed_time - due_date
            return time_diff.total_seconds()
        except Exception:
            return None

    def _calculate_completion_rate(self, completed: int, total: int) -> float:
        """Calculate completion rate percentage"""
        return round((completed / total * 100) if total > 0 else 0, 1)

    def _calculate_avg_time(self, completion_times: List[float]) -> float:
        """Calculate average completion time from a list of times"""
        """Calculate average completion time from a list of times"""
        if not completion_times:
            return 0
        return sum(completion_times) / len(completion_times)

    def _get_daily_task_creation_stats(self, tasks: List[Dict]) -> Dict:
        """Get statistics about non-calendar daily tasks"""
        return {
            'total_created': len([
                task for task in tasks
                if not self._is_calendar_task(task)
            ])
        }

    def _is_calendar_task(self, task: Dict) -> bool:
        """Check if a task is a calendar task"""
        return task['properties'].get('is_calendar', {}).get('formula', {}).get('string') == 'true'

    def _get_project_breakdown(self, tasks: List[Dict]) -> List[Dict]:
        """Get task completion breakdown by project"""
        projects = defaultdict(lambda: {'completed': 0, 'total': 0})

        for task in tasks:
            project = self._get_task_project(task)
            projects[project]['total'] += 1
            if self._is_task_completed(task):
                projects[project]['completed'] += 1

        return self._format_project_stats(projects)

    def _get_task_project(self, task: Dict) -> str:
        """Get project name for a task"""
        return task['properties'].get('Project', {}).get('select', {}).get('name', 'Unassigned')

    def _format_project_stats(self, projects: Dict) -> List[Dict]:
        """Format project statistics for output"""
        return [
            {
                'name': project,
                'completed': stats['completed'],
                'total': stats['total']
            }
            for project, stats in sorted(projects.items(), key=lambda x: x[1]['total'], reverse=True)
        ]

    def get_daily_inspiration_rate(self) -> Dict:
        """Get completion rate for Daily Inspiration tasks"""
        metrics = self.get_metrics()
        return {
            "current": metrics[TaskFields.DAILY_INSPIRATION_RATE]['current']['rate'],
            "previous": metrics[TaskFields.DAILY_INSPIRATION_RATE]['previous']['rate'],
            "change": self.format_change_value(TaskFields.DAILY_INSPIRATION_RATE)
        }

    def create_notion_section(self) -> dict:
        """Create Notion section for tasks summary"""
        metrics = self.get_metrics()

        daily_section_bullets = [
            f"Completed: {metrics[TaskFields.DAILY_COMPLETED]['current']}/{metrics[TaskFields.DAILY_TOTAL]['current']} "
            f"({metrics[TaskFields.DAILY_COMPLETION_RATE]['current']}% {self.format_change_value(TaskFields.DAILY_COMPLETION_RATE)})",

            f"Daily Inspiration: {metrics[TaskFields.DAILY_INSPIRATION_RATE]['current']['completed']}/"
            f"{metrics[TaskFields.DAILY_INSPIRATION_RATE]['current']['total']} "
            f"({metrics[TaskFields.DAILY_INSPIRATION_RATE]['current']['rate']}% {self.format_change_value(TaskFields.DAILY_INSPIRATION_RATE)})",

            f"Non-Calendar Tasks: {metrics[TaskFields.DAILY_CREATED]['current']} "
            f"({self.format_change_value(TaskFields.DAILY_CREATED)})"
        ]

        avg_time = metrics[TaskFields.AVG_COMPLETION_TIME]['current']
        avg_time_formatted = format_duration_days(avg_time) if avg_time > 0 else "N/A"

        regular_section_bullets = [
            f"Completed: {metrics[TaskFields.REGULAR_COMPLETED]['current']}/{metrics[TaskFields.REGULAR_TOTAL]['current']} "
            f"({metrics[TaskFields.REGULAR_COMPLETION_RATE]['current']}%)",
        ]

        # Only add completion time if we have valid data
        if avg_time > 0:
            regular_section_bullets.append(
                f"Average Completion Time: {avg_time_formatted} "
                f"({self.format_change_value(TaskFields.AVG_COMPLETION_TIME, format_type='time', invert_comparison=True)})"
            )
        else:
            regular_section_bullets.append(f"Average Completion Time: {avg_time_formatted}")

        daily_blocks = create_section_text_with_bullet("Daily Tasks:", daily_section_bullets)
        regular_blocks = create_section_text_with_bullet("Regular Tasks:", regular_section_bullets)

        return create_toggle_heading_block(
            "✅ Task Completion - 🔗",
            [*daily_blocks, *regular_blocks],
            heading_number=2,
            link_url={
                "url": self.daily_tasks_view_link,
                "subword": "🔗"
            }

        )

    def _calculate_task_completion(self, tasks: List[Dict]) -> Dict:
        """Calculates task completion statistics with completion time"""
        total = len(tasks)
        completed_tasks = []
        completion_times = []

        for task in tasks:
            if task['properties'].get('Done', {}).get('checkbox', False):
                completed_tasks.append(task)

                # Calculate completion time
                created_time = datetime.fromisoformat(task['created_time'].replace('Z', '+00:00'))
                last_edited = datetime.fromisoformat(task['last_edited_time'].replace('Z', '+00:00'))
                completion_time = last_edited - created_time
                completion_times.append(completion_time.total_seconds())

        avg_completion_time = (
            seconds_to_hours_minutes(sum(completion_times) / len(completion_times))
            if completion_times else "N/A"
        )

        return {
            'completed': len(completed_tasks),
            'total': total,
            'completion_rate': round((len(completed_tasks) / total * 100) if total > 0 else 0, 1),
            'avg_completion_time': avg_completion_time
        }

    def _get_new_tasks_in_period(self, db_id: str, target_date: date) -> List[Dict]:
        """Gets tasks created in the specified month"""
        start_date = target_date.replace(day=1)
        end_date = (target_date.replace(day=1, month=target_date.month % 12 + 1)
                    if target_date.month < 12
                    else target_date.replace(year=target_date.year + 1, month=1, day=1)) - timedelta(days=1)

        filter_payload = {
            "and": [
                {
                    "property": "Due",
                    "date": {
                        "on_or_after": start_date.isoformat(),
                        "on_or_before": end_date.isoformat()
                    }
                },
                {
                    "timestamp": "last_edited_time",
                    "last_edited_time": {
                        "on_or_after": start_date.isoformat()
                    }
                }
            ]
        }

        return get_db_pages(db_id, {"filter": filter_payload})

    def _get_overdue_tasks(self, db_id: str) -> List[Dict]:
        """Gets tasks that are overdue"""
        filter_payload = {
            "and": [
                {
                    "property": "Due",
                    "date": {
                        "before": date.today().isoformat()
                    }
                },
                {
                    "property": "Done",
                    "checkbox": {
                        "equals": False
                    }
                }
            ]
        }

        return get_db_pages(db_id, {"filter": filter_payload})

    def _create_task_metrics(self, tasks: List[Dict], previous_tasks: List[Dict]) -> Dict:
        """Creates task metrics with comparisons"""
        current_stats = self._calculate_task_completion(tasks)
        previous_stats = self._calculate_task_completion(previous_tasks)

        # Get non-calendar daily tasks
        daily_creation_stats = self._get_daily_task_creation_stats(tasks)
        previous_daily_creation_stats = self._get_daily_task_creation_stats(previous_tasks)

        # Calculate average completion time
        avg_completion = self.calculate_avg_completion_time(tasks)
        prev_avg_completion = self.calculate_avg_completion_time(previous_tasks)

        return {
            'daily_completed': {
                'current': current_stats['completed'],
                'total': current_stats['total'],
                'rate': current_stats['completion_rate'],
                'comparison': self._format_comparison(
                    current_stats['completion_rate'],
                    previous_stats['completion_rate'],
                    'completion rate'
                )
            },
            'non_calendar_tasks': {
                'current': daily_creation_stats['total_created'],
                'comparison': self._format_comparison(
                    daily_creation_stats['total_created'],
                    previous_daily_creation_stats['total_created'],
                    'tasks created'
                )
            },
            'regular_tasks': {
                'completed': current_stats['completed'],
                'total': current_stats['total'],
                'rate': current_stats['completion_rate'],
                'avg_completion_time': avg_completion,
                'completion_time_comparison': self._format_comparison(
                    parse_duration_to_seconds(avg_completion),
                    parse_duration_to_seconds(prev_avg_completion),
                    'completion time',
                    reverse_comparison=True
                )
            }
        }

    def calculate_avg_completion_time(self, tasks: List[Dict]) -> str:
        """Calculates average completion time for tasks with due dates in current month"""
        completion_times = []

        for task in tasks:
            if task['properties'].get('Done', {}).get('checkbox', True):
                created_time = datetime.fromisoformat(task['created_time'].replace('Z', '+00:00'))
                completed_time = datetime.fromisoformat(task['last_edited_time'].replace('Z', '+00:00'))
                completion_time = completed_time - created_time
                completion_times.append(completion_time.total_seconds())

        if completion_times:
            avg_seconds = sum(completion_times) / len(completion_times)
            return seconds_to_hours_minutes(avg_seconds)
        return "N/A"

    def _calculate_avg_completion_time(self, tasks: List[Dict]) -> str:
        """Calculates average completion time for tasks with due dates in current month"""
        completion_times = []

        for task in tasks:
            if task['properties'].get('Done', {}).get('checkbox', True):
                created_time = datetime.fromisoformat(task['created_time'].replace('Z', '+00:00'))
                completed_time = datetime.fromisoformat(task['last_edited_time'].replace('Z', '+00:00'))
                completion_time = completed_time - created_time
                completion_times.append(completion_time.total_seconds())

        if completion_times:
            avg_seconds = sum(completion_times) / len(completion_times)
            return seconds_to_hours_minutes(avg_seconds)
        return "N/A"

    def _calculate_daily_inspiration_rate(self, daily_tasks: List[Dict]) -> Dict:
        """Calculate completion rate for Daily Inspiration tasks"""
        inspiration_tasks = [
            task for task in daily_tasks
            if 'Daily Inspiration' in task['properties'].get('Project', {}).get('select', {}).get('name')
        ]

        total = len(inspiration_tasks)
        completed = sum(1 for task in inspiration_tasks
                        if task['properties'].get('Done', {}).get('checkbox', False))

        return {
            'completed': completed,
            'total': total,
            'rate': round((completed / total * 100) if total > 0 else 0, 1)
        }
