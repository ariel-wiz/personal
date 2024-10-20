import os
import subprocess
import sys
from datetime import datetime
from logger import logger


class ScriptExecution:
    path = 'path'
    arg = 'arg'
    frequency = 'frequency'


scripts_to_run = [
    {
        ScriptExecution.path: "/Users/ariel/PycharmProjects/personal/notion.py",
        ScriptExecution.arg: "--garmin",
        ScriptExecution.frequency: "daily"
    },
    {
        ScriptExecution.path: "/Users/ariel/PycharmProjects/personal/notion.py",
        ScriptExecution.arg: "--uncheck_done",
        ScriptExecution.frequency: "saturday"
    },
    {
        ScriptExecution.path: "/Users/ariel/PycharmProjects/personal/notion.py",
        ScriptExecution.arg: "--create_daily_summary_pages",
        ScriptExecution.frequency: "saturday"
    },
    {
        ScriptExecution.path: "/Users/ariel/PycharmProjects/personal/notion.py",
        ScriptExecution.arg: "--copy_birthdays",
        ScriptExecution.frequency: "saturday"
    }

]


def main():
    with open("/Users/ariel/Documents/cron-files/daily-run.log", "a") as f:
        f.write("Script started at {}\n".format(datetime.now()))

    logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
    logger.info(f"Using Python executable: {sys.executable}")
    logger.info(f"os.environ are: {os.environ}")

    today_date = datetime.now().strftime("%d/%m")  # Format for day/month
    today_weekday = datetime.now().strftime("%A").lower()  # %A gives the full weekday name

    # Your Python script logic here
    logger.info("Running the cron script...")

    for script in scripts_to_run:
        frequency = script.get('frequency')

        # Check if the frequency is a weekday or a specific date
        if frequency:
            if (today_weekday == frequency.lower() or frequency == 'daily' or
                    today_date == frequency):
                logger.info(f" ++++ Running {script['path']} with arguments {script['arg']} ++++")
                subprocess.run(['/usr/local/bin/python3.8', script['path'], script['arg']], check=True)
            else:
                logger.info(f" ---- Skipping {script['path']} with arguments {script['arg']} ----")

    current_hour = datetime.now().hour

    # Check if the hour is between 2 AM (2) and 8 AM (8)
    if 2 <= current_hour < 8:
        # After completing the script, put the Mac to sleep
        try:
            subprocess.run(['sudo', 'pmset', 'sleepnow'], check=True)
            logger.info("Successfully put the Mac to sleep.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to put the Mac to sleep: {e}")
    else:
        logger.info(f"Finished to run the cron script")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e
