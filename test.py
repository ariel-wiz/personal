import os
import logging
from datetime import datetime, timedelta, date
from getpass import getpass
from garminconnect import Garmin
from garth.exc import GarthHTTPError
import requests


class GarminConnectFixed(Garmin):
    """Custom Garmin Connect client that doesn't require profile data"""

    def login(self, tokenstore=None):
        """Modified login that skips profile verification"""
        try:
            if tokenstore:
                self.garth.load(tokenstore)
            else:
                self.garth.login(self.username, self.password)
            self.display_name = self.username
            return True
        except Exception as e:
            raise Exception(f"Login error: {str(e)}")


def format_seconds(seconds):
    """Format seconds into hours and minutes"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:01d}h{minutes:02d}m" if hours > 0 else f"{minutes:02d}m"


class GarminDataFetcher:
    def __init__(self, tokenstore_path="~/.garminconnect"):
        self.tokenstore_path = os.path.expanduser(tokenstore_path)
        self.client = None
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def connect(self, email=None, password=None):
        """Establish connection to Garmin"""
        try:
            self.logger.info("Attempting to connect to Garmin...")

            try:
                self.client = GarminConnectFixed()
                self.client.login(self.tokenstore_path)
                self.logger.info("Successfully connected using existing tokens")
                return True
            except (FileNotFoundError, GarthHTTPError) as token_error:
                if not email or not password:
                    raise ValueError("Email and password required for new login")

                self.client = GarminConnectFixed(
                    email=email,
                    password=password,
                    is_cn=False
                )

                if self.client.login():
                    self.client.garth.dump(self.tokenstore_path)
                    self.logger.info("Successfully logged in and saved new tokens")
                    return True

                return False

        except Exception as e:
            self.logger.error(f"Connection failed: {str(e)}")
            return False

    def validate_date(self, target_date: date) -> bool:
        """Validate that the target date is not in the future"""
        today = date.today()
        return target_date <= today

    def get_health_data(self, target_date: date = None) -> dict:
        """
        Get Garmin health data for a specific date

        Args:
            target_date: Date object for data retrieval. Defaults to yesterday.
        """
        if not self.client:
            raise Exception("Not connected - call connect() first")

        try:
            # Use provided date or default to yesterday
            if target_date is None:
                target_date = date.today() - timedelta(days=1)

            # Validate date
            if not self.validate_date(target_date):
                raise ValueError(f"Cannot get data for future date: {target_date}")

            date_str = target_date.isoformat()
            self.logger.info(f"Fetching health data for {date_str}")

            data = {
                'date': date_str,
                'metrics': {}
            }

            # Get steps
            try:
                steps_data = self.client.get_steps_data(date_str)
                if steps_data and steps_data.get('steps', 0) > 0:
                    data['metrics']['steps'] = {
                        'total': steps_data.get('steps', 0),
                        'goal': steps_data.get('dailyStepGoal', 0),
                        'goal_achieved': steps_data.get('steps', 0) >= steps_data.get('dailyStepGoal', 0)
                    }
            except Exception as e:
                self.logger.error(f"Error getting steps: {str(e)}")

            # Get sleep
            try:
                sleep_data = self.client.get_sleep_data(date_str)
                if sleep_data and sleep_data.get('sleepTimeSeconds', 0) > 0:
                    data['metrics']['sleep'] = {
                        'duration': format_seconds(sleep_data.get('sleepTimeSeconds', 0)),
                        'deep_sleep': format_seconds(sleep_data.get('deepSleepSeconds', 0)),
                        'light_sleep': format_seconds(sleep_data.get('lightSleepSeconds', 0)),
                        'start_time': sleep_data.get('sleepStartTimestamp', ''),
                        'end_time': sleep_data.get('sleepEndTimestamp', '')
                    }
            except Exception as e:
                self.logger.error(f"Error getting sleep: {str(e)}")

            # Get heart rate
            try:
                hr_data = self.client.get_heart_rates(date_str)
                if hr_data and hr_data.get('restingHeartRate', 0) > 0:
                    data['metrics']['heart_rate'] = {
                        'resting': hr_data.get('restingHeartRate', 0),
                        'max': hr_data.get('maxHeartRate', 0)
                    }
            except Exception as e:
                self.logger.error(f"Error getting heart rate: {str(e)}")

            # Get activities
            try:
                activities = self.client.get_activities_by_date(date_str, date_str)
                if activities:
                    data['metrics']['activities'] = [{
                        'type': activity.get('activityType', {}).get('typeKey', ''),
                        'name': activity.get('activityName', ''),
                        'duration': format_seconds(activity.get('duration', 0)),
                        'distance': f"{activity.get('distance', 0) / 1000:.2f}km",
                        'calories': activity.get('calories', 0)
                    } for activity in activities]
            except Exception as e:
                self.logger.error(f"Error getting activities: {str(e)}")

            if not data['metrics']:
                self.logger.warning(f"No data found for {date_str}")
                return None

            return data

        except Exception as e:
            self.logger.error(f"Error getting health data: {str(e)}")
            return None


def print_health_data(data: dict):
    """Print formatted health data"""
    if not data:
        print("No data available")
        return

    print(f"\nHealth Data for {data['date']}:")

    for metric, values in data['metrics'].items():
        print(f"\n{metric.replace('_', ' ').title()}:")
        if metric == 'activities':
            for activity in values:
                print("  -", end=" ")
                print(", ".join(f"{k}: {v}" for k, v in activity.items()))
        else:
            for key, value in values.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")


def main():
    fetcher = GarminDataFetcher()

    # Get credentials if needed
    email = input("Enter Garmin email: ")
    password = getpass("Enter Garmin password: ")

    # Connect
    if fetcher.connect(email, password):
        print("Connected successfully!")

        # Get data for the last 3 days
        for days_ago in range(1, 4):
            target_date = date.today() - timedelta(days=days_ago)
            data = fetcher.get_health_data(target_date)
            print_health_data(data)
    else:
        print("Failed to connect")


if __name__ == "__main__":
    main()