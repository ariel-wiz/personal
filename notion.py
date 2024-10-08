import argparse
import datetime
import json
import os
from enum import Enum

import requests

from garmin import init_api
from logger import logger
from variables import Keys

today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
day_before_yesterday = today - datetime.timedelta(days=2)

# https://developers.notion.com/reference/property-object

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {Keys.notion_api_key}",
    "Notion-Version": "2022-06-28"
}

UID = 'UID'
url = f"https://api.notion.com/v1/databases/{UID}/query"

tasks_db_id = Keys.tasks_db_id
daily_tasks_db_id = Keys.daily_tasks_db_id
recurring_db_id = Keys.recurring_db_id
zahar_nekeva_db_id = Keys.zahar_nekeva_db_id
trading_db_id = Keys.trading_db_id
garmin_db_id = Keys.garmin_db_id


class FieldMap:
    exercise = '🏃🏼\xa0Exercise'


tasks_filter = {
    "and": [
        {"and": [
            {"property": "State",
             "formula": {
                 "string": {
                     "is_not_empty": True
                 }}},
            {"property": "State",
             "formula": {
                 "string": {
                     "does_not_contain": "Done"
                 }}}]},
        {"property": "Follow up",
         "checkbox": {
             "equals": False
         }}
    ]
}

calendar_filter = {
    "and": [
        {"and": [
            {"property": "State",
             "formula": {
                 "string": {
                     "is_not_empty": True
                 }}},
            {"property": "State",
             "formula": {
                 "string": {
                     "does_not_contain": "Done"
                 }}}]},
        {"property": "is_calendar",
         "formula": {
             "string": {
                 "is_not_empty": True
             }
         }}
    ]
}

all_calendar_filter = {
    "and": [
        {
            "property": "Due",
            "date": {
                "on_or_after": datetime.date.today().isoformat()
            }
        },
        {"property": "is_calendar",
         "formula": {
             "string": {
                 "is_not_empty": True
             }
         }}
    ]
}

tasks_sorts = [
    {
        "property": "Due",
        "direction": "ascending"
    },
    {
        "property": "Icon",
        "direction": "ascending"
    },
    {
        "property": "Project",
        "direction": "ascending"
    }

]

recursive_filter = {

    "property": "State",
    "formula": {
        "string": {
            "is_not_empty": True
        }}
}

recursive_sorts = [
    {
        "property": "Delay",
        "direction": "descending"
    },
    {
        "property": "Next Due",
        "direction": "ascending"
    }
]

habits_sorts = [{
    "property": "Date",
    "direction": "descending"
}]

# Define the request payload
payload = {
    "filter": {},
    "sorts": {}
}

body = {}


def get_task_attributes_str(properties):
    notion_task_name = properties['Task']['title'][0]['plain_text']
    notion_state = properties['State']['formula']['string']
    priority = properties['Priority']['select']['name']
    return f"Task name {notion_task_name} - State {notion_state}"


def get_recursive_attributes_str(properties):
    notion_task_name = properties['Recurring Task']['title'][0]['plain_text']
    notion_state = properties['State']['formula']['string']
    notion_icon = properties['Icon']['formula']['string']
    return f"Task name {notion_task_name} - State {notion_state} - Icon {notion_icon}"


def get_zahar_nekeva_attributes_str(properties):
    notion_zahar_nekeva_word = properties['Name']['title'][0]['plain_text']
    notion_zahar_nekeva_type = properties['Type']['select']['name']
    return f"Word {notion_zahar_nekeva_word} - Type {notion_zahar_nekeva_type}"


def print_response(response, type=''):
    for result in response['results']:
        properties = result['properties']
        if type == 'tasks':
            logger.info(get_task_attributes_str(properties))
        if type == 'recursive':
            logger.info(get_recursive_attributes_str(properties))
        if type == 'zahar_nekeva':
            logger.info(get_zahar_nekeva_attributes_str(properties))
        else:
            logger.info(json.dumps(properties, indent=4))


def invoke_notion_api(url, payload={}, is_get=False):
    try:
        if payload:
            if is_get:
                response = requests.get(url, headers=headers, json=payload)
            else:
                response = requests.post(url, headers=headers, json=payload)
        else:
            if is_get:
                response = requests.get(url, headers=headers)
            else:
                response = requests.post(url, headers=headers)

        response.raise_for_status()  # Raise HTTPError for bad response status codes
        logger.info("Request successful!")
        return response.json()  # Assuming the response is JSON
    except requests.exceptions.RequestException as e:
        error_message = f"Request failed with status code {response.status_code}: {e}"
        logger.info(error_message)
        raise Exception(error_message)


def add_content_to_row(page_id, content):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"

    data = {
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                }
            }
        ]
    }

    response = requests.patch(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        logger.info("Content added successfully")
    else:
        logger.info(f"Error: {response.status_code}")
        logger.info(response.text)


def get_habit_rows():
    habits_db_id = daily_tasks_db_id
    habits_url = url.replace(UID, habits_db_id)

    habits_payload = payload.copy()
    habits_payload['filter'] = recursive_filter
    habits_payload['sorts'] = habits_sorts

    response = invoke_notion_api(habits_url, habits_payload)

    page_id = response['results'][0]['id']
    response_state = response['results'][0]['properties']['State']['formula']['string']

    content_page_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    content_page_response = invoke_notion_api(content_page_url, is_get=True)

    for i, result in enumerate(content_page_response['results']):
        rich_text = result[result['type']].get('rich_text', '')
        if rich_text:
            logger.info(rich_text[0]['plain_text'])
    print_response(f"{i} {content_page_response}")


def create_row(name_row, description, large_description, example):
    trading_db_url = 'https://api.notion.com/v1/pages'
    trading_payload = {
        "parent": {"database_id": trading_db_id},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": name_row
                        }
                    }
                ]
            },
            "Description": {
                "rich_text": [
                    {
                        "text": {
                            "content": description
                        }
                    }
                ]
            },
            "Category": {
                "select":
                    {"name": "Trading"}
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": large_description
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Example"
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": example
                            }
                        }
                    ]
                }
            }
        ]
    }

    response = invoke_notion_api(trading_db_url, trading_payload)


def get_tasks():
    tasks_url = url.replace(UID, tasks_db_id)
    tasks_payload = payload.copy()
    tasks_payload['filter'] = tasks_filter
    tasks_payload['sorts'] = tasks_sorts
    response = invoke_notion_api(tasks_url, tasks_payload)
    print_response(response, 'tasks')


def update_page_property(page_id, property_name, new_value):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    data = {
        "properties": {
            property_name: new_value
        }
    }
    response = requests.patch(url, headers=headers, json=data)
    return response.status_code == 200


def should_the_date_change(property):
    task_name = property.get('Task')['title'][0]['plain_text']
    try:
        due_property = property.get('Due')
        current_date = due_property["date"]["start"]
        hour = current_date.split("T")[1].split(".")[0]

        if hour == '00:00:00':
            return True
        return False

    except Exception as e:
        logger.info(f"Error: {e} while changing the date for task {task_name}")
        return False


def get_calendar(remove_time=False):
    tasks_url = url.replace(UID, tasks_db_id)
    tasks_payload = payload.copy()
    if remove_time:
        tasks_payload['filter'] = all_calendar_filter
    else:
        tasks_payload['filter'] = calendar_filter

    tasks_payload['sorts'] = tasks_sorts
    response = invoke_notion_api(tasks_url, tasks_payload)
    if remove_time:
        entries = response['results']
        for entry in entries:
            page_id = entry['id']
            due_property = entry['properties'].get('Due')
            page_name = entry['properties'].get('Task')['title'][0]['plain_text']
            if due_property and due_property["type"] == "date" and due_property["date"]:
                current_date = due_property["date"]["start"]
                if "T" in current_date and should_the_date_change(entry['properties']):
                    new_date = current_date.split("T")[0]

                    success = update_page_property(page_id, "Due", {"date": {"start": new_date}})
                    if success:
                        logger.info(f"Updated page {page_name}: {current_date} -> {new_date}")
                    else:
                        logger.info(f"Failed to update page {page_name}")
    else:
        print_response(response, 'tasks')


def get_daily_tasks():
    tasks_url = url.replace(UID, tasks_db_id)
    tasks_payload = payload.copy()
    tasks_payload['filter'] = calendar_filter
    tasks_payload['sorts'] = tasks_sorts
    response = invoke_notion_api(tasks_url, tasks_payload)
    print_response(response, 'tasks')


def get_trading():
    tasks_url = url.replace(UID, trading_db_id)
    response = invoke_notion_api(tasks_url)
    print_response(response)


def get_recursive():
    recursive_url = url.replace(UID, recurring_db_id)
    recursive_payload = payload.copy()
    recursive_payload['filter'] = recursive_filter
    recursive_payload['sorts'] = recursive_sorts
    response = invoke_notion_api(recursive_url, recursive_payload)
    print_response(response, 'recursive')


def get_zahar_nekeva():
    zahar_nekeva_url = url.replace(UID, zahar_nekeva_db_id)
    response = invoke_notion_api(zahar_nekeva_url)
    print_response(response, 'zahar_nekeva')


def get_db_id_info(db_id):
    get_db_id_url = url.replace(UID, db_id)
    response = invoke_notion_api(get_db_id_url)
    print_response(response)


def update_page_with_relation(page_id_add_relation, page_id_data_to_import, other_params={}):
    """
    Updates a page with a relation to another page.

    Parameters:
    - page_id_add_relation: The ID of the page where the relation will be added.
    - page_id_data_to_import: The ID of the page that will be linked as a relation.
    """
    update_url = f"https://api.notion.com/v1/pages/{page_id_add_relation}"

    # Payload for updating the relation
    data = {
        "properties": {
            "Watch Metrics": {
                "relation": [
                    {
                        "id": page_id_data_to_import  # Add this page as a relation
                    }
                ]
            }
        }
    }
    if other_params:
        data["properties"].update(other_params)

    # Make the API request to update the page
    response = requests.patch(update_url, headers=headers, json=data)

    if response.status_code == 200:
        logger.info("Relation added successfully!")
    else:
        logger.error(f"Failed to add relation: {response.status_code}")
        logger.error(response.json())


def search_notion(query):
    search_url = 'https://api.notion.com/v1/search'
    payload = {
        "query": query,
        "filter": {
            "value": "page",
            "property": "object"
        },
        "sort": {
            "direction": "descending",
            "timestamp": "last_edited_time"
        }
    }
    response = invoke_notion_api(search_url, payload)
    logger.info(json.dumps(response, indent=4))


# Enum for date offsets
class DateOffset(Enum):
    TODAY = 0
    YESTERDAY = 1
    TWO_DAYS_AGO = 2
    THREE_DAYS_AGO = 3


def get_page_by_date_offset(database_id, offset: DateOffset):
    """
    Queries the specified Notion database to find pages where the State is not empty
    and the Date is equal to the date corresponding to the provided offset.

    Parameters:
    - database_id: The ID of the database to query.
    - offset: The DateOffset enum value indicating how many days ago to look.

    Returns:
    - List of page IDs that match the criteria.
    """
    # Calculate the target date based on the offset
    target_date = datetime.datetime.now().date() - datetime.timedelta(days=offset.value)

    # Get the target date in YYYY-MM-DD format
    target_date_str = target_date.isoformat()

    # Prepare the query payload
    query_payload = {
        "filter":
            {
                "property": "Date",
                "date": {
                    "equals": target_date_str
                }
            }
    }

    # Send the request to the Notion API
    find_url = url.replace(UID, database_id)
    response = invoke_notion_api(find_url, query_payload)

    results = response.get("results", [])
    # Return the list of page IDs
    if len(results) == 0:
        logger.info(f"No pages found for date {target_date_str}.")
    elif len(results) > 1:
        logger.info(f"Found multiple pages for date {target_date_str}.")
    else:
        logger.info(f"Successfully found pages for date {target_date_str}!")
    return results


def uncheck_done_daily_task():
    page_id = '110afca4f8078019b286d3d64b058fa2'
    url = f"https://api.notion.com/v1/pages/{page_id}"
    update_data = {
        "properties": {
            "Done": {
                "checkbox": False  # Set checkbox to False (uncheck)
            }
        }
    }

    # Send PATCH request to update the page properties
    response = requests.patch(url, headers=headers, data=json.dumps(update_data))

    if response.status_code == 200:
        logger.info(f"Page '{page_id}' updated successfully!")
    else:
        logger.info(f"Failed to update the page. Status code: {response.status_code}")
        logger.info(f"Response: {response.text}")


def convert_to_date(date_str):
    # Timestamp in milliseconds
    timestamp_ms = date_str

    # Convert to seconds by dividing by 1000
    timestamp_sec = timestamp_ms / 1000

    # Convert to a UTC datetime object
    utc_dt = datetime.datetime.utcfromtimestamp(timestamp_sec)

    formatted_time = utc_dt.strftime('%H:%M')
    # formatted_time = utc_dt.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time


def seconds_to_hours_minutes(seconds):
    # Calculate hours and minutes from total seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    # Return the result as a tuple (hours, minutes)
    str_time = ''
    if hours > 0 and seconds > 0:
        str_time = f"{hours:02}h{minutes:02}"
    elif hours > 0:
        str_time = f"{hours:02}h00"
    elif minutes > 0:
        str_time = f"{minutes:02}m"
    else:
        str_time = "No activity"
    return str_time


def get_garmin_info():
    api = init_api()
    sleep_data = api.get_sleep_data(day_before_yesterday.isoformat())
    sleep_start = convert_to_date(sleep_data['dailySleepDTO']['sleepStartTimestampGMT'])
    sleep_end = convert_to_date(sleep_data['dailySleepDTO']['sleepEndTimestampGMT'])
    sleep_duration = seconds_to_hours_minutes(sleep_data['dailySleepDTO']['sleepTimeSeconds'])
    sleep_feedback_overall = sleep_data['dailySleepDTO']['sleepScores']['overall']['qualifierKey']
    sleep_feedback_note = sleep_data['dailySleepDTO']['sleepScores']['overall']['value']

    user_summary_data = api.get_user_summary(yesterday.isoformat())
    steps = user_summary_data['totalSteps']
    daily_steps_goal = user_summary_data['dailyStepGoal']
    total_calories = user_summary_data['totalKilocalories']

    activity_data = api.get_activities_by_date(day_before_yesterday.isoformat(), yesterday.isoformat())
    total_activity_duration = 0
    total_activity_calories = 0
    for activity in activity_data:
        activity_name = activity['activityName']
        if activity_name == 'Walking':
            continue
        total_activity_duration += activity['duration']
        total_activity_calories += activity['calories']

    return {
        "date": yesterday.isoformat(),
        "sleep_start": sleep_start,
        "sleep_end": sleep_end,
        "sleep_duration": sleep_duration,
        "sleep_feedback_overall": sleep_feedback_overall,
        "steps": steps,
        "daily_steps_goal": daily_steps_goal,
        "total_calories": total_calories,
        "total_activity_duration": seconds_to_hours_minutes(total_activity_duration),
        "total_activity_calories": total_activity_calories,
        "sleep_feedback_note": sleep_feedback_note
    }


def get_notion_other_fields(activity_status):
    if FieldMap.exercise in activity_status:
        activity = activity_status[FieldMap.exercise]
        if activity and "Nothing" not in activity:
            logger.debug(f"Checking {FieldMap.exercise} to true")
            return {FieldMap.exercise: {
                "checkbox": True
            }}

    return {
    }


def update_garmin_info(update_daily_tasks=True):
    yesterday_date = yesterday.strftime('%d-%m-%Y')
    logger.info(f"Updating Garmin info for {yesterday_date}")

    # Checking if the page exists already
    garmin_pages = get_page_by_date_offset(garmin_db_id, DateOffset.YESTERDAY)
    if garmin_pages:
        garmin_page_id = garmin_pages[0]["id"]
        activity_status = garmin_pages[0]["properties"]["Activity Status"]["formula"]["string"]
        logger.info(f"Garmin page for {yesterday_date} already exists with page ID {garmin_page_id}")
    else:
        garmin_dict = get_garmin_info()
        logger.debug(garmin_dict)

        database_id = '117afca4f807805d9787fdff0dee81af'
        url = f"https://api.notion.com/v1/pages"
        garmin_payload = {
            "parent": {"database_id": database_id},
            "properties": {
                "Name": {"title": [{"text": {"content": yesterday_date}}]},
                "Date": {"date": {"start": yesterday.isoformat()}},
                "Sleep Start": {"rich_text": [{"text": {"content": garmin_dict['sleep_start']}}]},
                "Sleep End": {"rich_text": [{"text": {"content": garmin_dict['sleep_end']}}]},
                "Sleep Feedback": {"select": {"name": garmin_dict['sleep_feedback_overall']}},
                "Sleep Note": {"number": garmin_dict['sleep_feedback_note']},
                "Sleep Duration": {"rich_text": [{"text": {"content": garmin_dict['sleep_duration']}}]},
                "Steps": {"number": garmin_dict['steps']},
                "Steps Goal": {"number": garmin_dict['daily_steps_goal']},
                "Calories": {"number": garmin_dict['total_calories']},
                "Activity Duration": {"rich_text": [{"text": {"content": garmin_dict['total_activity_duration']}}]},
                "Activity Calories": {"number": garmin_dict['total_activity_calories']},
            }
        }
        response = invoke_notion_api(url, garmin_payload)
        garmin_page_id = response['id']
        activity_status = response["properties"]["Activity Status"]["formula"]["string"]

        logger.info(f"Successfully created Garmin info for {yesterday_date}")

    if update_daily_tasks:
        daily_tasks = get_page_by_date_offset(daily_tasks_db_id, DateOffset.YESTERDAY)
        if daily_tasks:
            daily_task_id = daily_tasks[0]["id"]
            other_fields = get_notion_other_fields({FieldMap.exercise: activity_status})
            update_page_with_relation(daily_task_id, garmin_page_id, other_fields)
            logger.info(f"Successfully updated daily task with Garmin info for {yesterday_date}")


def main(selected_tasks):
    for task in selected_tasks:
        task_function = task_map.get(task)
        if task_function:
            task_function()


if __name__ == '__main__':
    # Define the task mapping
    task_map = {
        'tasks': get_tasks,
        'calendar': get_calendar,
        'trading': get_trading,
        'recursive': get_recursive,
        'zahar_nekeva': get_zahar_nekeva,
        'add_trading': lambda: create_row('ariel row', 'ariel description', "ariel large description", "ariel example"),
        'get_habits': get_habit_rows,
        'uncheck_done': uncheck_done_daily_task,
        'garmin': update_garmin_info,
    }

    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Run specified tasks.")
    for task in task_map.keys():
        parser.add_argument(f'--{task}', action='store_true', help=f"Run the task to {task.replace('_', ' ')}")

    args = parser.parse_args()

    # Gather selected tasks based on command-line arguments
    selected_tasks = [task for task in task_map.keys() if getattr(args, task)]

    # IMPORTANT !!!! Comment after usage !!!!
    # selected_tasks.append('garmin')  # Default task can be modified here

    # Call the main logic with the selected tasks
    main(selected_tasks)
