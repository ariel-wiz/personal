import argparse
from datetime import datetime, timedelta, date
import json
import os
from enum import Enum

import requests

from garmin import init_api
from logger import logger
from variables import Keys

today = date.today()
yesterday = today - timedelta(days=1)
day_before_yesterday = today - timedelta(days=2)

# https://developers.notion.com/reference/property-object

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {Keys.notion_api_key}",
    "Notion-Version": "2022-06-28"
}

UID = 'UID'
url = f"https://api.notion.com/v1/databases/{UID}/query"

tasks_db_id = Keys.tasks_db_id
day_summary_db_id = Keys.day_summary_db_id
day_summary_template_id = Keys.day_summary_template_id
recurring_db_id = Keys.recurring_db_id
zahar_nekeva_db_id = Keys.zahar_nekeva_db_id
trading_db_id = Keys.trading_db_id
garmin_db_id = Keys.garmin_db_id
daily_tasks_db_id = Keys.daily_tasks_db_id
weekly_task_page_id = Keys.weekly_task_page_id
birthday_db_id = Keys.birthday_db_id

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

next_month_filter = {
    "and": [
        {
            "property": "Date",
            "date": {
                "on_or_after": datetime.now().date().isoformat()
            }
        },
        {
            "property": "Date",
            "date": {
                "on_or_before": (datetime.now() + timedelta(days=30)).date().isoformat()
            }
        }
    ]
}

next_filter = {
        "and": [
            {"property": "State",
             "formula": {
                 "string": {
                     "is_not_empty": True
                 }}},
            {"property": "State",
             "formula": {
                 "string": {
                     "does_not_contain": "Done"
                 }}}]}

all_calendar_filter = {
    "and": [
        {
            "property": "Due",
            "date": {
                "on_or_after": date.today().isoformat()
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
        "property": "Category",
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

day_summary_sorts = [{
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


def get_day_summary_rows():
    habits_db_id = day_summary_db_id
    habits_url = url.replace(UID, habits_db_id)

    day_summary_payload = payload.copy()
    day_summary_payload['filter'] = recursive_filter
    day_summary_payload['sorts'] = day_summary_sorts

    response = invoke_notion_api(habits_url, day_summary_payload)

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


def create_date_range(input_date_str, range_days=7):
    # Parse the input date string to a datetime object
    input_date = datetime.strptime(input_date_str, '%Y-%m-%d').date()
    today = datetime.now().date()  # Get today's date

    date_list = []

    if input_date >= today:
        # If input date is today or in the future, create next 7 days starting from input date
        date_list = [(input_date + timedelta(days=i)).isoformat() for i in range(range_days)]
    else:
        # If input date is in the past, create dates from today to 7 days past input date
        date_list = [(today + timedelta(days=i)).isoformat() for i in range((input_date - today).days + range_days)]

    return date_list[1:]


def get_day_number(input_date_str):
    # Parse the input date string to a datetime object
    input_date = datetime.strptime(input_date_str, '%Y-%m-%d').date()

    # Get the weekday number (0 for Monday to 6 for Sunday)
    weekday_number = input_date.weekday()

    # Adjust so that Sunday is 0, Monday is 1, and so on
    day_number = (weekday_number + 1) % 7

    return day_number


def get_day_number_formatted(input_date_str):
    day_dict = {
        0: "1️⃣",
        1: "2️⃣",
        2: "3️⃣",
        3: "4️⃣",
        4: "5️⃣",
        5: "😎",
        6: "🤩"
    }
    day_number = get_day_number(input_date_str)
    return day_dict[day_number]


def create_day_summary_name(date_str):
    day_formatted = get_day_number_formatted(date_str)
    # Parse the input date string to a datetime object
    input_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    # Format the date as '17 October'
    formatted_date = input_date.strftime('%d %B')
    return f"{day_formatted} - {formatted_date}"


def get_template_content(template_id):
    url = f"https://api.notion.com/v1/blocks/{template_id}/children"
    response = invoke_notion_api(url, is_get=True)
    return response['results']


def process_blocks(blocks):
    processed_blocks = []
    for block in blocks:
        block_type = block['type']
        processed_blocks.append({
            "object": "block",
            "type": block_type,
            block_type: block[block_type]
        })

    return processed_blocks


def create_daily_summary_pages():
    daily_url = url.replace(UID, day_summary_db_id)

    day_summary_payload = payload.copy()
    day_summary_payload['filter'] = next_month_filter
    day_summary_payload['sorts'] = day_summary_sorts

    response = invoke_notion_api(daily_url, day_summary_payload)
    last_date = response['results'][0]['properties']['Date']['date']['start']
    days_to_create = create_date_range(last_date)

    for day_to_create in days_to_create:
        day_summary_name = create_day_summary_name(day_to_create)
        day_summary_payload = generate_create_page_payload(day_summary_db_id, {"Date": day_to_create, "Day": day_summary_name})

        response = invoke_notion_api(f"https://api.notion.com/v1/pages", day_summary_payload)
        logger.info(f"Created daily summary for {day_summary_name} with ID {response['id']}")

    get_tasks(all_calendar_filter, is_daily=True)


def copy_birthdays():
    # daily_tasks = get_daily_tasks()
    birthday_pages = get_birthdays()
    success_task_count = 0
    error_task_count = 0

    for birthday_page in birthday_pages['results']:
        next_birthday = birthday_page['properties']['Next Birthday']['formula']['date']['start']
        birthday_state = birthday_page['properties']['DailyTaskState']['formula']['string']

        # if task['properties']['Due']['date']['end'] and '00:00:00' not in \
        #         task['properties']['Due']['date']['end'].split('T')[1].split('+')[0]:
        #     task_due = [task_due_start, task_due_end]
        # else:
        #     task_due = task_due_start

        birthday_task_dict = {
            "Task": birthday_state,
            "Project": "OGg=",
            "Due": next_birthday
        }

        birthday_task_payload = generate_create_page_payload(daily_tasks_db_id, birthday_task_dict)
        response = invoke_notion_api(f"https://api.notion.com/v1/pages", birthday_task_payload)
        # if response:
        #     page_id = task['id']
        #     update_data = {
        #         "properties": {
        #             "copied": {
        #                 "checkbox": True
        #             }
        #         }
        #     }
        #     update_page(page_id, update_data)

        logger.info(f"Successfully created daily task for {birthday_state} with ID {response['id']}")
        success_task_count += 1
    else:
        logger.info(
            f"Failed to create daily task for daily task for {birthday_state} and birthday date {next_birthday} "
            f"- response {response}")
        error_task_count += 1
    logger.info(f"Successfully copied {success_task_count} tasks. Errors: {error_task_count}")


def get_tasks(task_filter=None, is_daily=False):
    if is_daily:
        tasks_url = url.replace(UID, daily_tasks_db_id)
    else:
        tasks_url = url.replace(UID, tasks_db_id)
    tasks_payload = payload.copy()
    if task_filter:
        tasks_payload['filter'] = task_filter
    else:
        tasks_payload['filter'] = tasks_filter
    tasks_payload['sorts'] = tasks_sorts
    response = invoke_notion_api(tasks_url, tasks_payload)
    print_response(response, 'tasks')
    return response


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


def get_daily_tasks():
    tasks_url = url.replace(UID, daily_tasks_db_id)
    tasks_payload = payload.copy()
    tasks_payload['filter'] = next_filter
    tasks_payload['sorts'] = tasks_sorts
    response = invoke_notion_api(tasks_url, tasks_payload)
    return response


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


def get_birthdays():
    birthday_url = url.replace(UID, birthday_db_id)
    birthday_payload = {'sorts': [{"property": "Next Birthday", "direction": "ascending"}]}
    response = invoke_notion_api(birthday_url, birthday_payload)
    return response


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
    target_date = datetime.now().date() - timedelta(days=offset.value)

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
        logger.info(f"No pages found for date {target_date_str} in Notion.")
    elif len(results) > 1:
        logger.info(f"Found multiple pages for date {target_date_str} in Notion.")
    else:
        logger.info(f"Successfully found pages for date {target_date_str} in Notion!")
    return results


def uncheck_done_daily_task():
    update_data = {
        "properties": {
            "Done": {
                "checkbox": False  # Set checkbox to False (uncheck)
            },
            "Due": {
                "date": {
                    "start": today.isoformat()
                }
            }
        }
    }
    update_page(weekly_task_page_id, update_data)


def update_page(page_id, update_data):
    url = f"https://api.notion.com/v1/pages/{page_id}"

    # Send PATCH request to update the page properties
    response = requests.patch(url, headers=headers, data=json.dumps(update_data))

    if response.status_code == 200:
        logger.info(f"Page '{page_id}' updated successfully!")
    else:
        logger.info(f"Failed to update the page. Status code: {response.status_code}")
        logger.info(f"Response: {response.text}")


def add_hours_to_time(time_str):
    # Parse the input string into a datetime object
    input_time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f')

    # Add 3 hours using timedelta
    adjusted_time = input_time + timedelta(hours=3)

    # Return the adjusted time in hh:mm format
    return adjusted_time.strftime('%H:%M')


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
    sleep_data = api.get_sleep_data(yesterday.isoformat())
    if not sleep_data.get('sleepMovement'):  # It means the data is empty
        return {}

    sleep_start = add_hours_to_time(sleep_data['sleepLevels'][0]['startGMT'])
    sleep_end = add_hours_to_time(sleep_data['sleepLevels'][-1]['endGMT'])
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


def replace_none_with_list_or_string(d, replacements):
    # If the argument is a string, convert it to a list with a single element
    if isinstance(replacements, str):
        replacements = [replacements]

    # Create an iterator from the replacements (works for both single string and list)
    replacement_iter = iter(replacements)

    # Recursive function to traverse the dictionary or list and replace None values
    def recursive_replace(item):
        if isinstance(item, dict):
            # If it's a dictionary, process its items
            new_dict = {}
            for k, v in item.items():
                new_dict[k] = recursive_replace(v)
            return new_dict
        elif isinstance(item, list):
            # If it's a list, process each element of the list
            return [recursive_replace(i) for i in item]
        elif item is None:
            # Replace None with the next element from the iterator
            return next(replacement_iter, None)  # Default to None if replacements run out
        else:
            # If it's not a dict, list, or None, return the item as is
            return item

    # Return the newly created structure
    return recursive_replace(d)


def generate_create_page_payload(database_id, db_dict):
    daily_task_payload = {"parent": {"database_id": database_id}, "properties": {}}  # Initialize the payload

    daily_db_items = {
        "Title": ["Task", "Day"],
        "Select": ["Project"],
        "Date": ["Due", "Date"],
        "Link": ["gCal Link"]
    }

    daily_db_playload = {
        "Title": {"title": [{"text": {"content": None}}]},
        "Select": {"select": {"id": None}},
        "Date": {"date": {"start": None}},
        "Link": {"url": None}
    }

    for daily_task_element in db_dict.items():
        key, value = daily_task_element
        for db_item_category_key in list(daily_db_items.keys()):
            if key in daily_db_items[db_item_category_key]:
                if db_item_category_key == "Date" and isinstance(value, list) and len(
                        value) == 2:  # Start date and end date
                    start_date = value[0]
                    end_date = value[1]
                    payload_element = replace_none_with_list_or_string(daily_db_playload[db_item_category_key],
                                                                       start_date)
                    payload_element["date"]["end"] = end_date
                else:
                    payload_element = replace_none_with_list_or_string(daily_db_playload[db_item_category_key], value)
                daily_task_payload["properties"][key] = payload_element
                break

    return daily_task_payload


def create_daily_task_row(payload):
    url = f"https://api.notion.com/v1/pages"
    response = invoke_notion_api(url, payload)
    logger.info(f"Successfully created daily task row with ID {response['id']}")


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
        if not garmin_dict:
            logger.info(f"No Garmin data found for {yesterday_date}")
            return

        logger.debug(garmin_dict)

        database_id = garmin_db_id
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
        daily_tasks = get_page_by_date_offset(day_summary_db_id, DateOffset.YESTERDAY)
        if daily_tasks:
            daily_task_id = daily_tasks[0]["id"]
            other_fields = get_notion_other_fields({FieldMap.exercise: activity_status})
            update_page_with_relation(daily_task_id, garmin_page_id, other_fields)
            logger.info(f"Successfully updated daily task with Garmin info for {yesterday_date}")


def main(selected_tasks):
    try:
        if selected_tasks:
            for task in selected_tasks:
                task_function = task_map.get(task)
                if task_function:
                    task_function()
        else:
            # Manually call the functions here
            copy_birthdays()
    except Exception as e:
        logger.error(f"Error: {e}")

    logger.info("Script completed successfully.")


if __name__ == '__main__':
    # Define the task mapping
    task_map = {
        'tasks': get_tasks,
        'trading': get_trading,
        'recursive': get_recursive,
        'zahar_nekeva': get_zahar_nekeva,
        'add_trading': lambda: create_row('ariel row', 'ariel description', "ariel large description", "ariel example"),
        'get_habits': get_day_summary_rows,
        'uncheck_done': uncheck_done_daily_task,
        'garmin': update_garmin_info,
        'create_daily_summary_pages': create_daily_summary_pages,
        'copy_birthdays': copy_birthdays,
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
