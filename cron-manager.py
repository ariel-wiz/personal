# !/usr/bin/env python3
"""
Cron Manager Script - Runs daily at 5 AM
This script manages scheduled tasks and logs their execution.
"""

import os
import subprocess
import sys
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Union
from logger import logger


# Configure logging
LOG_DIR = '/Users/ariel/Documents/cron-files'
LOG_FILE = os.path.join(LOG_DIR, 'cron-manager.log')
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'cron-manager-error.log')
EXECUTION_LOG_FILE = os.path.join(LOG_DIR, 'execution.log')


class Frequency(Enum):
    DAILY = "daily"
    WEEKLY_SATURDAY = "saturday"
    WEEKLY_SUNDAY = "sunday"
    WEEKLY_MONDAY = "monday"
    WEEKLY_TUESDAY = "tuesday"
    WEEKLY_WEDNESDAY = "wednesday"
    WEEKLY_THURSDAY = "thursday"
    WEEKLY_FRIDAY = "friday"
    ONCE_A_MONTH = ["7/*"]
    TWICE_A_MONTH = ["7/*", "22/*"]


@dataclass
class ScriptConfig:
    name: str  # Descriptive name for the script
    path: str  # Full path to the script
    arg: str  # Command line argument
    frequency: Union[str, List[str]]
    python_path: Optional[str] = None  # Optional custom PYTHONPATH
    working_dir: Optional[str] = None  # Optional working directory

    def should_run_today(self, today_date: str, today_weekday: str) -> bool:
        if isinstance(self.frequency, list):
            # Handle list of monthly dates (e.g. ["1/*", "15/*"])
            day_of_month = today_date.split('/')[0]
            return any(day_of_month == date.split('/')[0] for date in self.frequency)

        # Handle monthly frequency (DD/* format)
        if isinstance(self.frequency, str) and '/*' in self.frequency:
            day_of_month = self.frequency.split('/')[0]
            return today_date.split('/')[0] == day_of_month

        # Handle daily/weekly frequency
        try:
            freq = Frequency(self.frequency.lower())
            return (freq == Frequency.DAILY or
                    today_weekday == freq.value.lower())
        except ValueError:
            logger.warning(f"Invalid frequency format for {self.name}: {self.frequency}")
            return False


class ScriptManager:
    def __init__(self, scripts: List[ScriptConfig], python_executable: str = '/usr/local/bin/python3.8'):
        self.scripts = scripts
        self.python_executable = python_executable
        self.today_date = datetime.now().strftime("%d/%m")
        self.today_weekday = datetime.now().strftime("%A").lower()

    def run_script(self, script: ScriptConfig):
        try:
            env = os.environ.copy()

            # Set up PYTHONPATH if specified
            if script.python_path:
                env['PYTHONPATH'] = script.python_path

            # Prepare the working directory
            working_dir = script.working_dir or os.path.dirname(script.path)

            logger.info(f" ++++ Running {script.name}: {script.path} with arguments {script.arg} ++++")

            # Run the script with the specified environment and working directory
            subprocess.run(
                [self.python_executable, script.path, script.arg],
                check=True,
                env=env,
                cwd=working_dir
            )

            logger.info(f" ++++ Successfully completed {script.name} ++++\n\n")

            # Log successful execution
            with open(EXECUTION_LOG_FILE, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"{timestamp} - {script.name} executed successfully\n")

        except subprocess.CalledProcessError as e:
            error_msg = f"Error running {script.name}: {e}"
            logger.error(error_msg)
            raise

    def run_all(self):
        for script in self.scripts:
            if script.should_run_today(self.today_date, self.today_weekday):
                try:
                    logger.debug(f" ---- Running {script.name}: {script.path} with arguments {script.arg} ----")
                    self.run_script(script)
                except Exception as e:
                    logger.error(f"There was an error in cron when attempting to run {script.name}: {str(e)}\n"
                                 f"Running the next script")
                    continue
            else:
                logger.debug(f" ---- Skipping {script.name}: {script.path} with arguments {script.arg} ----")


# Configuration
NOTION_SCRIPTS = [
    ScriptConfig(
        name="Garmin Update",
        path="/Users/ariel/PycharmProjects/personal/notion_py/notion.py",
        arg="--garmin",
        frequency=Frequency.DAILY.value,
        python_path="/Users/ariel/PycharmProjects/personal",
        working_dir="/Users/ariel/PycharmProjects/personal/notion_py"
    ),
    ScriptConfig(
        name="Uncheck Done Tasks",
        path="/Users/ariel/PycharmProjects/personal/notion_py/notion.py",
        arg="--uncheck_done",
        frequency=Frequency.WEEKLY_SATURDAY.value,
        python_path="/Users/ariel/PycharmProjects/personal",
        working_dir="/Users/ariel/PycharmProjects/personal/notion_py"
    ),
    ScriptConfig(
        name="Handle Done Tasks",
        path="/Users/ariel/PycharmProjects/personal/notion_py/notion.py",
        arg="--handle_done_tasks",
        frequency=Frequency.DAILY.value,
        python_path="/Users/ariel/PycharmProjects/personal",
        working_dir="/Users/ariel/PycharmProjects/personal/notion_py"
    ),
    ScriptConfig(
        name="Create Daily Pages",
        path="/Users/ariel/PycharmProjects/personal/notion_py/notion.py",
        arg="--create_daily_pages",
        frequency=Frequency.WEEKLY_TUESDAY.value,
        python_path="/Users/ariel/PycharmProjects/personal",
        working_dir="/Users/ariel/PycharmProjects/personal/notion_py"
    ),
    ScriptConfig(
        name="Copy Pages",
        path="/Users/ariel/PycharmProjects/personal/notion_py/notion.py",
        arg="--copy_pages",
        # frequency="15/*",  # Runs on the 15th of every month
        frequency=Frequency.WEEKLY_TUESDAY.value,
        python_path="/Users/ariel/PycharmProjects/personal",
        working_dir="/Users/ariel/PycharmProjects/personal/notion_py"
    ),
    ScriptConfig(
        name="Scheduled Tasks",
        path="/Users/ariel/PycharmProjects/personal/notion_py/notion.py",
        arg="--scheduled_tasks",
        frequency=Frequency.DAILY.value,
        python_path="/Users/ariel/PycharmProjects/personal",
        working_dir="/Users/ariel/PycharmProjects/personal/notion_py"
    ),
    ScriptConfig(
        name="Unset Done Recurring Tasks",
        path="/Users/ariel/PycharmProjects/personal/notion_py/notion.py",
        arg="--unset_done_recurring_tasks",
        frequency=Frequency.WEEKLY_TUESDAY.value,
        python_path="/Users/ariel/PycharmProjects/personal",
        working_dir="/Users/ariel/PycharmProjects/personal/notion_py"
    ),
    ScriptConfig(
        name="Unset Done Recurring Tasks",
        path="/Users/ariel/PycharmProjects/personal/notion_py/notion.py",
        arg="--create_recurring_tasks_summary",
        frequency=Frequency.DAILY.value,
        python_path="/Users/ariel/PycharmProjects/personal",
        working_dir="/Users/ariel/PycharmProjects/personal/notion_py"
    ),
    # ScriptConfig(
    #     name="Get Expenses",
    #     path="/Users/ariel/PycharmProjects/personal/notion_py/notion.py",
    #     arg="--get_expenses",
    #     frequency=Frequency.DAILY.value,
    #     python_path="/Users/ariel/PycharmProjects/personal",
    #     working_dir="/Users/ariel/PycharmProjects/personal/notion_py"
    # )
]


def should_sleep() -> bool:
    current_hour = datetime.now().hour
    return 2 <= current_hour < 8


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
        if "started" in result.stdout:
            logger.info("Supervisor is running")
            return True
        else:
            logger.warning("Supervisor is not running")
            return False
    except Exception as e:
        logger.error(f"Error checking supervisor status: {e}")
        return False


def start_supervisor():
    """Start supervisord if it's not running"""
    logger.info("Attempting to start supervisor")
    try:
        result = subprocess.run(
            "brew services start supervisor",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Supervisor start result: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start supervisor: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False


def main():
    try:
        # Log the start of the script
        with open("/Users/ariel/Documents/cron-files/daily-run.log", "a") as f:
            f.write(f"Script started at {datetime.now()}\n")

        date = datetime.now().strftime("%d/%m")
        logger.info(f"\n\n\n++++++++++++++++++++++++ Starting the cron script {date} ++++++++++++++++++++++++\n"
                    f"\tPYTHONPATH: {os.environ.get('PYTHONPATH')}\n"
                    f"\tUsing Python executable: {sys.executable}\n"
                    f"\tos.environ are: {os.environ}")

        # Ensure supervisor is running
        if not check_supervisor_status():
            if not start_supervisor():
                logger.error("Failed to start supervisor, continuing with script execution anyway")

        # Initialize and run script manager
        manager = ScriptManager(NOTION_SCRIPTS)
        manager.run_all()
        logger.info("Finished running the cron script")
        return 0
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())