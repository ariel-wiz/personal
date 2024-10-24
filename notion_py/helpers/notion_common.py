import functools
import json
from datetime import datetime, timedelta

import requests

from common import DateOffset, yesterday, create_date_range, create_day_summary_name, get_date_offset, find_state_items, \
    today
from logger import logger
from notion_py.helpers.notion_children_blocks import generate_simple_page_content, \
    generate_page_content_page_notion_link
from notion_py.notion_globals import next_month_filter, date_descending_sort, api_db_id, day_summary_db_id, \
    Method, NotionAPIStatus, TaskConfig, daily_tasks_db_id, tasks_db_id, next_filter, first_created_sorts, \
    default_tasks_filter, default_tasks_sorts, daily_notion_category_filter, on_or_after_today_filter
from notion_py.helpers.notion_payload import generate_payload, generate_create_page_payload, get_relation_payload, \
    get_api_status_payload
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


def get_pages_by_date_offset(database_id, offset: int, date_name="Date", filter_to_add={}):
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
    target_date = datetime.now().date() - timedelta(days=offset)

    # Get the target date in YYYY-MM-DD format
    target_date_str = target_date.isoformat()

    query_filter = {
        "property": date_name,
        "date": {
            "equals": target_date_str
        }
    }
    if filter_to_add:
        query_filter = {"and": [query_filter, filter_to_add]}

    # Prepare the query payload
    query_payload = generate_payload(filter=query_filter)

    response = get_db_pages(database_id, query_payload)

    # Return the list of page IDs
    if len(response) == 0:
        logger.info(f"No pages found for date {target_date_str} in Notion.")
    elif len(response) > 1:
        logger.info(f"Found multiple pages for date {target_date_str} in Notion.")
    else:
        logger.info(f"Successfully found pages for date {target_date_str} in Notion!")
    return response


# Daily and tasks functions
def create_daily_summary_pages():
    create_daily_pages_for_db_id(day_summary_db_id)


def create_daily_api_pages():
    create_daily_pages_for_db_id(api_db_id, "🌐", link_to_day_summary_tasks=True)


def create_daily_pages_for_db_id(db_id, icon=None, link_to_day_summary_tasks=False, days_range_to_create=10):
    day_summary_payload = generate_payload(on_or_after_today_filter, date_descending_sort)
    response = get_db_pages(db_id, day_summary_payload)

    if not response:
        logger.info(f"No daily tasks found for the future")
        last_date = str(yesterday.isoformat())
    else:
        last_date = response[0]['properties']['Date']['date']['start']

    days_to_create = create_date_range(last_date, days_range_to_create+1)

    for day_to_create in days_to_create:
        day_summary_name = create_day_summary_name(day_to_create)
        payload_content = {"Date": day_to_create, "Day": day_summary_name} if not icon else {"Date": day_to_create,
                                                                                             "Day": day_summary_name,
                                                                                             "Icon": icon}
        response = create_page_with_db_dict(db_id, payload_content)

        if link_to_day_summary_tasks:
            day_summary_pages = get_day_summary_by_date_str(day_to_create)
            if day_summary_pages:
                daily_summary_page_id = day_summary_pages[0]['id']
                created_page_id = response['id']
                update_page_with_relation(daily_summary_page_id, created_page_id, "API Status Page")

        logger.info(f"Created daily summary for {day_summary_name} with ID {response['id']}")


def get_tasks(tasks_filter=None, tasks_sort=None, is_daily=False, print_response=False):
    get_tasks_payload = generate_payload(tasks_filter if tasks_filter else default_tasks_filter,
                                         tasks_sort if tasks_sort else default_tasks_sorts)
    if is_daily:
        return get_db_pages(daily_tasks_db_id, get_tasks_payload, print_response)
    else:
        return get_db_pages(tasks_db_id, get_tasks_payload, print_response, 'tasks')


def get_daily_tasks(daily_filter=None, daily_sorts=None, print_response=False):
    return get_tasks(daily_filter if daily_filter else next_filter, daily_sorts if daily_sorts else first_created_sorts,
                     is_daily=True, print_response=print_response)


def get_daily_tasks_by_date_str(date_str, filter_to_add=None):
    date_offset = get_date_offset(date_str)
    return get_pages_by_date_offset(daily_tasks_db_id, date_offset, date_name="Due", filter_to_add=filter_to_add)


def get_day_summary_by_date_str(date_str, filter_to_add=None):
    date_offset = get_date_offset(date_str)
    return get_pages_by_date_offset(day_summary_db_id, date_offset, date_name="Date", filter_to_add=filter_to_add)


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
        update_payload = get_api_status_payload(status, operation)

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
        response_data = _query_notion_api(query_url, query_payload, method, start_cursor=start_cursor,
                                          print_response=False)
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


def create_page_with_db_dict(db_id, db_dict):
    generated_payload = generate_create_page_payload(db_id, db_dict)
    return create_page(generated_payload)


def create_page_with_db_dict_and_children_block(db_id, db_dict, children_block):
    generated_payload = generate_create_page_payload(db_id, db_dict)
    generated_payload.update(children_block)

    return create_page(generated_payload)


def update_page_with_relation(page_id_add_relation, page_id_data_to_import, relation_name, other_params={}):
    relation_payload = get_relation_payload(page_id_data_to_import, relation_name, other_params)
    update_page(page_id_add_relation, relation_payload)

    logger.info("Relation added successfully!")


def recurring_tasks_to_daily(config: TaskConfig) -> None:
    """
    Generic function to copy tasks from a source database to daily tasks.

    Args:
        config: TaskConfig object containing all necessary configuration
    """
    # Get source pages
    source_pages = config.get_pages_func()
    if not source_pages:
        logger.info(f"No {config.name} to update")
        return

    # Get existing daily tasks using the filter
    daily_tasks = get_daily_tasks(config.daily_filter)
    existing_task_names = [
        task['properties']['Task']['title'][0]['plain_text']
        for task in daily_tasks
    ]

    success_task_count = 0
    error_task_count = 0

    for source_page in source_pages:
        state = source_page['properties'][config.state_property_name]['formula']['string']

        try:
            # Check for existing pages
            if config.state_suffix:
                existing_page = find_state_items(
                    existing_task_names,
                    state,
                    config.state_suffix
                )
            else:
                existing_page = state in existing_task_names

            if existing_page:
                logger.info(f"Page for '{state}' already exists")
                continue

            # Get due date if configured
            due_date = (
                source_page['properties'][config.date_property_name]['formula']['date']['start']
                if config.date_property_name
                else today.isoformat()
            )

            # Create the task
            task_dict = {
                "Task": state,
                "Project": config.project,
                "Due": due_date,
                "Icon": config.icon
            }

            # Create page with or without children block
            if config.children_block:
                children_block = generate_page_content_page_notion_link(source_page['id'])
                response = create_page_with_db_dict_and_children_block(
                    daily_tasks_db_id,
                    task_dict,
                    children_block
                )
            else:
                response = create_page_with_db_dict(daily_tasks_db_id, task_dict)

            logger.info(f"Successfully created a daily {config.name} task for {state} with ID {response['id']}")
            success_task_count += 1

        except Exception as e:
            logger.error(f"Failed to create a daily {config.name} task for {state} - error {str(e)}")
            error_task_count += 1
            continue

    if success_task_count > 0 and error_task_count > 0:
        logger.info(f"Successfully copied {success_task_count} tasks. Errors: {error_task_count}")
    elif success_task_count > 0:
        logger.info(f"Successfully copied {success_task_count} tasks")
    elif error_task_count > 0:
        logger.info(f"Failed to create daily {config.name} tasks - Errors: {error_task_count}")


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
