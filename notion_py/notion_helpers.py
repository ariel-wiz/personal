import functools
import json
from datetime import datetime, timedelta

import requests

from helpers import replace_none_with_list_or_string, DateOffset, yesterday, create_date_range, create_day_summary_name
from logger import logger
from notion_py.notion_globals import next_month_filter, day_summary_sorts, api_db_id, day_summary_db_id, \
    NotionPropertyType, Method, NotionAPIStatus, NotionAPIOperation
from variables import Keys

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {Keys.notion_api_key}",
    "Notion-Version": "2022-06-28"
}


# Fundamental operations
def update_page(page_id, update_payload, print_response=False):
    has_properties = 'properties' in update_payload
    has_children = 'children' in update_payload

    if has_properties and has_children:
        raise Exception(
            "Cannot update properties and children in the same call. "
            "Please make separate calls for properties and children updates."
        )

    # Determine the correct URL based on payload type
    if has_children:
        update_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    else:
        update_url = f"https://api.notion.com/v1/pages/{page_id}"

    return _invoke_notion_api(
        update_url,
        update_payload,
        method=Method.PATCH,
        print_response=print_response
    )


def create_page(create_payload, print_response=False):
    create_url = f"https://api.notion.com/v1/pages"
    return _invoke_notion_api(create_url, create_payload, method=Method.POST, print_response=print_response)


def get_page(page_id, print_response=False):
    get_url = f"https://api.notion.com/v1/pages/{page_id}"
    return _invoke_notion_api(get_url, method=Method.GET, print_response=print_response)


def get_db_pages(db_id, get_db_payload={}, print_response=False, print_response_type=''):
    get_db_url = f"https://api.notion.com/v1/databases/{db_id}/query"
    return _invoke_notion_api(get_db_url, get_db_payload, method=Method.POST, print_response=print_response,
                              print_response_type=print_response_type)


# Payloads
def generate_payload(filter=None, sorts=None):
    new_payload = {}
    if filter:
        new_payload['filter'] = filter
    if sorts:
        new_payload['sorts'] = sorts
    return new_payload


def generate_create_page_payload(db_id, db_dict):
    daily_task_payload = {"parent": {"database_id": db_id}, "properties": {}}  # Initialize the payload

    daily_db_items = {
        NotionPropertyType.TITLE: ["Name", "Task", "Day"],
        NotionPropertyType.TEXT: ["Sleep Start", "Sleep End", "Sleep Duration", "Activity Duration"],
        NotionPropertyType.SELECT_ID: ["Project"],
        NotionPropertyType.SELECT_NAME: ["Sleep Feedback"],
        NotionPropertyType.DATE: ["Date", "Due"],
        NotionPropertyType.URL: ["gCal Link"],
        NotionPropertyType.NUMBER: ["Steps", "Steps Goal", "Calories", "Sleep Note", "Activity Calories"]
    }

    daily_db_payload = {
        NotionPropertyType.TITLE: {"title": [{"text": {"content": None}}]},
        NotionPropertyType.TEXT: {"rich_text": [{"text": {"content": None}}]},
        NotionPropertyType.SELECT_ID: {"select": {"id": None}},
        NotionPropertyType.SELECT_NAME: {"select": {"name": None}},
        NotionPropertyType.DATE: {"date": {"start": None}},
        NotionPropertyType.URL: {"url": None},
        NotionPropertyType.NUMBER: {"number": None}
    }

    for daily_task_element in db_dict.items():
        key, value = daily_task_element
        for db_item_category_key in list(daily_db_items.keys()):
            if key == "Icon":
                icon_element = {"type": "emoji", "emoji": value}
                daily_task_payload["icon"] = icon_element
                break
            elif key in daily_db_items[db_item_category_key]:
                if db_item_category_key == "Date" and isinstance(value, list) and len(
                        value) == 2:  # Start date and end date
                    start_date = value[0]
                    end_date = value[1]
                    payload_element = replace_none_with_list_or_string(daily_db_payload[db_item_category_key],
                                                                       start_date)
                    payload_element["date"]["end"] = end_date
                else:
                    payload_element = replace_none_with_list_or_string(daily_db_payload[db_item_category_key], value)
                daily_task_payload["properties"][key] = payload_element
                break

    return daily_task_payload


# Children block
def generate_children_block_for_daily_inspirations(note, author, main_content):
    children_block = [
        {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [
                    {"type": "text",
                     "text": {"content": note},
                     "annotations": {"italic": True}
                     },
                    {"type": "text",
                     "text": {"content": f"\n💬 {author}"}
                     }],
                "color": "gray_background"
            }
        },
        {
            "object": "block",
            "type": "divider",
            "divider": {}
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": ""}}]
            }
        },
    ]

    for line in main_content.split(". "):
        children_block.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line + '.'}}]
                }
            })
    return children_block


def generate_simple_page_content(content):
    children_block = {"children": [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }
    ]
    }

    return children_block


# Generic operations
def update_page_with_relation(page_id_add_relation, page_id_data_to_import, relation_name, other_params={}):
    """
    Updates a page with a relation to another page.

    Parameters:
    - page_id_add_relation: The ID of the page where the relation will be added.
    - page_id_data_to_import: The ID of the page that will be linked as a relation.
    """

    # Payload for updating the relation
    relation_payload = {
        "properties": {
            relation_name: {
                "relation": [
                    {
                        "id": page_id_data_to_import  # Add this page as a relation
                    }
                ]
            }
        }
    }
    if other_params:
        relation_payload["properties"].update(other_params)

    response = update_page(page_id_add_relation, relation_payload)

    if response:
        logger.info("Relation added successfully!")
    else:
        logger.error(f"Failed to add relation")


def get_pages_by_date_offset(database_id, offset: DateOffset):
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
    query_payload = generate_payload(filter={
        "property": "Date",
        "date": {
            "equals": target_date_str
        }
    })

    response = get_db_pages(database_id, query_payload)

    # Return the list of page IDs
    if len(response) == 0:
        logger.info(f"No pages found for date {target_date_str} in Notion.")
    elif len(response) > 1:
        logger.info(f"Found multiple pages for date {target_date_str} in Notion.")
    else:
        logger.info(f"Successfully found pages for date {target_date_str} in Notion!")
    return response


def create_daily_summary_pages():
    create_daily_pages_for_db_id(day_summary_db_id)


def create_daily_api_pages():
    create_daily_pages_for_db_id(api_db_id, "💽")


def create_daily_pages_for_db_id(db_id, icon=None, days_range_to_create=10):
    day_summary_payload = generate_payload(next_month_filter, day_summary_sorts)
    response = get_db_pages(db_id, day_summary_payload)

    if not response or 'properties' not in response:
        logger.info(f"No daily tasks found for the next month")
        last_date = str(yesterday.isoformat())
    else:
        last_date = response['properties']['Date']['date']['start']

    days_to_create = create_date_range(last_date, days_range_to_create)

    for day_to_create in days_to_create:
        day_summary_name = create_day_summary_name(day_to_create)
        payload_content = {"Date": day_to_create, "Day": day_summary_name} if not icon else {"Date": day_to_create,
                                                                                             "Day": day_summary_name,
                                                                                             "Icon": icon}
        day_summary_payload = generate_create_page_payload(db_id, payload_content)
        response = create_page(day_summary_payload)
        logger.info(f"Created daily summary for {day_summary_name} with ID {response['id']}")


# Notion API Status operations
def _update_api_status(status, operation, details=None):
    """
    Updates the API status page with the provided status for the specified operation.

    Parameters:
    - status: The new status to set.
    - operation: The operation for which to set the status.
    """
    try:
        # Get the ID of the API status page
        api_status_today_pages = get_pages_by_date_offset(Keys.api_db_id, DateOffset.TODAY)
        if not api_status_today_pages:
            create_daily_api_pages()
            api_status_today_pages = get_pages_by_date_offset(Keys.api_db_id, DateOffset.TODAY)

        api_status_page_id = api_status_today_pages[0].get('id')

        # Prepare the payload to update the status
        update_payload = {
            "properties": {
                operation: {
                    "select": {
                        "name": status
                    }
                }
            }
        }

        # Update the API status page
        update_page(api_status_page_id, update_payload)

        if details:
            update_page(api_status_page_id, generate_simple_page_content(details))
            logger.error(details)

        logger.info(f"Updated API status for {operation} to {status}.")
    except Exception as e:
        logger.error(f"Error while attempting to update API status for {operation} to {status}.: {str(e)}")


def set_start_api_status(operation):
    return _update_api_status(NotionAPIStatus.STARTED, operation)


def set_success_api_status(operation):
    return _update_api_status(NotionAPIStatus.SUCCESS, operation)


def set_error_api_status(operation, details=None):
    if details:
        details = f"Notion API Error detail for {operation}: {details}"
    return _update_api_status(NotionAPIStatus.ERROR, operation, details)


def track_operation(operation):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, should_track=False, **kwargs):
            if should_track:
                set_start_api_status(operation)
                try:
                    result = func(*args, **kwargs)
                    set_success_api_status(operation)
                    return result
                except Exception as e:
                    set_error_api_status(operation, str(e))
                    raise
            else:
                # Run without tracking if should_track is False
                return func(*args, **kwargs)

        return wrapper

    return decorator


# API I/S
def _invoke_notion_api(query_url, query_payload={}, method=Method.GET, print_response=False, print_response_type=''):
    results = []
    start_cursor = None

    while True:
        response_data = _query_notion_api(query_url, query_payload, method, start_cursor=start_cursor, print_response=False)
        if response_data:
            if 'results' not in response_data:  # For not GET requests
                if print_response:
                    logger.info(json.dumps(response_data, indent=4))
                return response_data

            results.extend(response_data.get('results', response_data))
            start_cursor = response_data.get('next_cursor')  # Get the next cursor

            # Break if there's no next cursor
            if not start_cursor:
                break
            logger.info(f"Handling pagination with cursor {start_cursor}...")
        else:
            break

    if print_response or print_response_type:
        print_notion_response(results, print_response_type)

    return results


def _query_notion_api(url, payload={}, method=None, start_cursor=None, print_response=False):
    if start_cursor:
        payload['start_cursor'] = start_cursor
    try:
        if payload:
            if method == Method.GET:
                response = requests.get(url, headers=headers)
            elif method == Method.POST:
                response = requests.post(url, headers=headers, json=payload)
            elif method == Method.PATCH:
                response = requests.patch(url, headers=headers, json=payload)
        else:
            if method == Method.GET:
                response = requests.get(url, headers=headers)
            elif method == Method.POST:
                response = requests.post(url, headers=headers)
            elif method == Method.PATCH:
                response = requests.patch(url, headers=headers)

        response.raise_for_status()  # Raise HTTPError for bad response status codes
        if print_response:
            logger.info(f"{method} Request successful!")
        return response.json()  # Assuming the response is JSON
    except requests.exceptions.RequestException as e:
        error_message = f"Request failed with status code {response.status_code} {response.reason}: {json.loads(response.text).get('message', response.text)}"
        logger.info(error_message)
        raise Exception(error_message)


# Format responses
def get_task_attributes_str(properties):
    notion_task_name = properties['Task']['title'][0]['plain_text']
    notion_state = properties['State']['formula']['string']
    priority = properties['Priority']['select']['name']
    return f"Task name {notion_task_name} - State {notion_state} - Priority {priority}"


def get_recursive_attributes_str(properties):
    notion_task_name = properties['Recurring Task']['title'][0]['plain_text']
    notion_state = properties['State']['formula']['string']
    notion_icon = properties['Icon']['formula']['string']
    return f"Task name {notion_task_name} - State {notion_state} - Icon {notion_icon}"


def get_zahar_nekeva_attributes_str(properties):
    notion_zahar_nekeva_word = properties['Name']['title'][0]['plain_text']
    notion_zahar_nekeva_type = properties['Type']['select']['name']
    return f"Word {notion_zahar_nekeva_word} - Type {notion_zahar_nekeva_type}"


def print_notion_response(response, type=''):
    for result in response:
        properties = result['properties']
        if type == 'tasks':
            logger.info(get_task_attributes_str(properties))
        if type == 'recursive':
            logger.info(get_recursive_attributes_str(properties))
        if type == 'zahar_nekeva':
            logger.info(get_zahar_nekeva_attributes_str(properties))
        else:
            logger.info(json.dumps(properties, indent=4))
