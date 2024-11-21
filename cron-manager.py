import os
import subprocess
import sys
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Union
from logger import logger


class Frequency(Enum):
    DAILY = "daily"
    WEEKLY_SATURDAY = "saturday"
    WEEKLY_SUNDAY = "sunday"
    WEEKLY_MONDAY = "monday"
    WEEKLY_TUESDAY = "tuesday"
    WEEKLY_WEDNESDAY = "wednesday"
    WEEKLY_THURSDAY = "thursday"
    WEEKLY_FRIDAY = "friday"
    FIRST_AND_FIFTEENTH = ["1/*", "15/*"]


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
        if '/*' in self.frequency:
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

        except subprocess.CalledProcessError as e:
            logger.error(f"Error running {script.name}: {e}")
            raise

    def run_all(self):
        for script in self.scripts:
            if script.should_run_today(self.today_date, self.today_weekday):
                try:
                    logger.info(f" ---- Running {script.name}: {script.path} with arguments {script.arg} ----")
                    self.run_script(script)
                except Exception as e:
                    logger.error(f"There was an error in cron when attempting to run {script}: {str(e)}\n"
                                 f"Running the next script")
                    continue
            else:
                logger.info(f" ---- Skipping {script.name}: {script.path} with arguments {script.arg} ----")


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
        name="Get Expenses",
        path="/Users/ariel/PycharmProjects/personal/notion_py/notion.py",
        arg="--get_expenses",
        frequency=Frequency.DAILY.value,
        python_path="/Users/ariel/PycharmProjects/personal",
        working_dir="/Users/ariel/PycharmProjects/personal/notion_py"
    ),
    ScriptConfig(
        name="Copy Book Summaries",
        path="/Users/ariel/PycharmProjects/personal/notion_py/notion.py",
        arg="--copy_book_summary",
        frequency=Frequency.FIRST_AND_FIFTEENTH.value,
        python_path="/Users/ariel/PycharmProjects/personal",
        working_dir="/Users/ariel/PycharmProjects/personal/notion_py"
    )
]


def should_sleep() -> bool:
    current_hour = datetime.now().hour
    return 2 <= current_hour < 8


def main():
    with open("/Users/ariel/Documents/cron-files/daily-run.log", "a") as f:
        f.write(f"Script started at {datetime.now()}\n")

    date = datetime.now().strftime("%d/%m")
    logger.info(f"\n\n\n++++++++++++++++++++++++ Starting the cron script {date} ++++++++++++++++++++++++\n"
                f"\tPYTHONPATH: {os.environ.get('PYTHONPATH')}\n"
                f"\tUsing Python executable: {sys.executable}\n"
                f"\tos.environ are: {os.environ}")

    # Initialize and run script manager
    manager = ScriptManager(NOTION_SCRIPTS)
    manager.run_all()
    logger.info("Finished running the cron script")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e
