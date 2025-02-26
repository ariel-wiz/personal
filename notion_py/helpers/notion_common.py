import functools
import json
from datetime import datetime, timedelta
from typing import List, Dict

import requests

from common import DateOffset, yesterday, create_date_range, create_day_summary_name, get_date_offset, find_state_items, \
    today
from logger import logger, collect_handler
from notion_py.helpers.notion_children_blocks import generate_simple_page_content, \
    generate_page_content_page_notion_link
from notion_py.notion_globals import date_descending_sort, api_db_id, day_summary_db_id, \
    Method, NotionAPIStatus, TaskConfig, daily_tasks_db_id, tasks_db_id, next_filter, first_created_sorts, \
    default_tasks_filter, default_tasks_sorts, on_or_after_today_filter, IconType, IconColor, NotionAPIOperation, \
    recurring_db_id
from notion_py.helpers.notion_payload import generate_payload, generate_create_page_payload, get_relation_payload, \
    get_api_status_payload
from variables import Keys

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {Keys.notion_api_key}",
    "Notion-Version": "2022-06-28"
}


def create_notion_id_mapping():
    """Create mapping of Notion IDs to their descriptive names from Keys class"""
    id_mapping = {}

    # Get all attributes from Keys class
    for attr_name, attr_value in vars(Keys).items():
        # Skip private attributes
        if attr_name.startswith('_'):
            continue

        # Only process string values (IDs)
        if not isinstance(attr_value, str):
            continue

        # Format the name based on the attribute name
        if attr_name.endswith('_db_id'):
            # Convert tasks_db_id -> Tasks DB
            name = attr_name[:-6].replace('_', ' ').title() + ' DB'
        elif attr_name.endswith('_page_id'):
            # Convert day_summary_page_id -> Day Summary Page
            name = attr_name[:-8].replace('_', ' ').title() + ' Page'
        else:
            continue

        id_mapping[attr_value] = name

    return id_mapping


_notion_id_mapping = create_notion_id_mapping()


# Fundamental operations
def create_page(create_payload, print_response=False):
    create_url = f"https://api.notion.com/v1/pages"
    return _invoke_notion_api(create_url, create_payload, method=Method.POST, print_response=print_response)


def get_page_children(page_id, print_response=False):
    return get_page(page_id, get_children=True, print_response=print_response)


def get_page(page_id, get_children=False, print_response=False):
    page_id = page_id.strip().replace("-", "")
    get_url = f"https://api.notion.com/v1/pages/{page_id}"
    if get_children:
        get_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    return _invoke_notion_api(get_url, method=Method.GET, print_response=print_response)


def get_db_info(db_id, print_response=False, print_response_type=''):
    get_db_url = f"https://api.notion.com/v1/databases/{db_id}"
    return _invoke_notion_api(get_db_url, method=Method.GET, print_response=print_response,
                              print_response_type=print_response_type)


def get_db_pages(db_id, get_db_payload=None, print_response=False, print_response_type=''):
    get_db_url = f"https://api.notion.com/v1/databases/{db_id}/query"
    if get_db_payload is None:
        get_db_payload = {}
    return _invoke_notion_api(get_db_url, get_db_payload, method=Method.POST, print_response=print_response,
                              print_response_type=print_response_type)


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


def delete_page(page_id):
    page_id = page_id.strip().replace("-", "")
    archived_payload = {"archived": True}
    return update_page(page_id, archived_payload)


def create_db(page_id_to_create_the_db_in, db_title, properties_payload={}, print_response=False):
    """
    Creates a new database in Notion.

    Args:
        page_id_to_create_the_db_in: Parent page ID where the DB will be created
        db_title: Title of the database
        properties_payload: Dictionary containing database properties configuration
        print_response: Whether to print the API response

    Returns:
        Response from Notion API containing the new database ID
    """
    create_db_url = "https://api.notion.com/v1/databases"

    # Create base payload with parent and title
    database_payload = {
        "parent": {
            "type": "page_id",
            "page_id": page_id_to_create_the_db_in
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": db_title
                }
            }
        ]
    }

    # Generate properties payload if db_dict is provided
    if properties_payload:
        database_payload["properties"] = properties_payload

    return _invoke_notion_api(create_db_url, database_payload, Method.POST, print_response=print_response)


def duplicate_db(db_id_to_copy: str, new_db_name: str, page_id_to_copy: str, print_response: bool = False) -> str:
    """
    Duplicates a Notion database with its properties structure and all its pages.

    Args:
        db_id_to_copy: ID of the source database to copy
        new_db_name: Name for the new database
        page_id_to_copy: Parent page ID where the new DB will be created
        print_response: Whether to print API responses

    Returns:
        str: ID of the newly created database
    """
    try:
        # Get source database schema
        source_db = get_db_info(db_id_to_copy, print_response=print_response)

        # Create new database with same properties
        new_db_response = create_db(
            page_id_to_create_the_db_in=page_id_to_copy,
            db_title=new_db_name,
            properties_payload=source_db["properties"],
            print_response=print_response
        )

        new_db_id = new_db_response['id']
        logger.info(f"Created new database with ID: {new_db_id}")

        # Get all pages from source database
        source_pages = get_db_pages(db_id_to_copy, print_response=print_response)

        # Copy each page to the new database
        for page in source_pages:
            try:
                # Extract properties from source page
                properties = page['properties']

                # Create new page payload
                new_page_payload = {
                    "parent": {"database_id": new_db_id},
                    "properties": properties
                }

                # Copy icon if exists
                if "icon" in page:
                    new_page_payload["icon"] = page["icon"]

                # Create the new page
                create_page(new_page_payload, print_response=print_response)
                logger.debug(f"Duplicated page with title: {_get_page_title(properties)}")

            except Exception as e:
                logger.error(f"Error duplicating page: {str(e)}")
                continue

        logger.info(f"Successfully duplicated database with {len(source_pages)} pages")
        return new_db_id

    except Exception as e:
        logger.error(f"Error duplicating database: {str(e)}")
        raise


def _get_page_title(properties: dict) -> str:
    """Helper function to extract page title from properties"""
    for prop in properties.values():
        if prop.get('type') == 'title':
            title_content = prop.get('title', [])
            if title_content and len(title_content) > 0:
                return title_content[0].get('plain_text', 'Untitled')
    return 'Untitled'


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
        logger.debug(f"No pages found for date {target_date_str} in Notion.")
    elif len(response) > 1:
        logger.debug(f"Found multiple pages for date {target_date_str} in Notion.")
    else:
        logger.debug(f"Successfully found pages for date {target_date_str} in Notion!")
    return response


# Daily and tasks functions
def create_daily_summary_pages():
    logger.info('Creating daily summary pages')
    create_daily_pages_for_db_id(day_summary_db_id, icon=generate_icon_url(IconType.SUN, IconColor.YELLOW))


def create_daily_api_pages():
    logger.info('Creating daily API pages')
    create_daily_pages_for_db_id(api_db_id, icon=generate_icon_url(IconType.SERVER, IconColor.BLUE),
                                 link_to_day_summary_tasks=True, name='daily API page')


def create_daily_pages_for_db_id(db_id, icon=None, link_to_day_summary_tasks=False, days_range_to_create=10, name=""):
    day_summary_payload = generate_payload(on_or_after_today_filter, date_descending_sort)
    response = get_db_pages(db_id, day_summary_payload)

    if not response:
        logger.info(f"No daily tasks found for the future")
        last_date = str(yesterday.isoformat())
    else:
        last_date = response[0]['properties']['Date']['date']['start']

    days_to_create = create_date_range(last_date, days_range_to_create + 1)

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

        logger.info(f"Created {name if name else 'daily summary'} for {day_summary_name} with ID {response['id']}")


def get_tasks(tasks_filter=None, tasks_sort=None, is_daily=False, print_response=False):
    get_tasks_payload = generate_payload(tasks_filter if tasks_filter else default_tasks_filter,
                                         tasks_sort if tasks_sort else default_tasks_sorts)
    if is_daily:
        return get_db_pages(daily_tasks_db_id, get_tasks_payload, print_response)
    else:
        return get_db_pages(tasks_db_id, get_tasks_payload, print_response, 'tasks')


def get_daily_tasks(daily_filter=None, daily_sorts=None, print_response=False, get_only_properties=False):
    tasks = get_tasks(daily_filter if daily_filter else next_filter,
                      daily_sorts if daily_sorts else first_created_sorts,
                      is_daily=True, print_response=print_response)
    if get_only_properties:
        return [task['properties'] for task in tasks]
    return tasks


def get_daily_tasks_by_date_str(date_str, filter_to_add=None):
    date_offset = get_date_offset(date_str)
    return get_pages_by_date_offset(daily_tasks_db_id, date_offset, date_name="Due", filter_to_add=filter_to_add)


def get_recurring_tasks(custom_filter=None):
    try:
        if custom_filter is None:
            custom_filter = {}

        recurring_payload = generate_payload(custom_filter)
        recurring_tasks = get_db_pages(recurring_db_id, recurring_payload)

        logger.debug(f"Found {len(recurring_tasks)} recurring tasks matching filter")
        return recurring_tasks

    except Exception as e:
        logger.error(f"Error getting recurring tasks: {str(e)}")
        return []


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
        update_page(api_status_page_id, update_payload)

        if details:
            update_page(api_status_page_id, generate_simple_page_content(details, add_separator=True))

        logger.debug(f"Updated API status for {operation} to {status}.")
    except Exception as e:
        logger.error(f"Error while attempting to update API status for {operation} to {status}.: {str(e)}")


def set_start_api_status(operation):
    message_logs = collect_handler.get_all_message_logs_and_clear(get_only_info_or_error=True)
    return _update_api_status(NotionAPIStatus.STARTED, operation, message_logs)


def set_success_api_status(operation):
    message_logs = collect_handler.get_all_message_logs_and_clear(get_only_info_or_error=True)
    return _update_api_status(NotionAPIStatus.SUCCESS, operation, message_logs)

def clear_api_status(operation):
    """Clears the API status for the specified operation by setting it to empty."""
    try:
        # Get the ID of the API status page
        api_status_today_pages = get_pages_by_date_offset(Keys.api_db_id, DateOffset.TODAY)
        if not api_status_today_pages:
            return

        api_status_page_id = api_status_today_pages[0].get('id')

        # Prepare the payload to clear the status
        update_payload = {
            "properties": {
                operation: {
                    "select": None
                }
            }
        }
        update_page(api_status_page_id, update_payload)
        logger.debug(f"Cleared API status for {operation}.")
    except Exception as e:
        logger.error(f"Error while attempting to clear API status for {operation}: {str(e)}")


def set_error_api_status(operation, details=None):
    message_logs = collect_handler.get_all_message_logs_and_clear()
    if details:
        details = f"Notion API Error detail for {operation}: {details}"
        message_logs.append(details)
    return _update_api_status(NotionAPIStatus.ERROR, operation, message_logs)


# Current track_operation decorator in notion_common.py
def track_operation(operation):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, should_track=False, **kwargs):
            if should_track:
                set_start_api_status(operation)
                try:
                    result = func(*args, **kwargs)
                    if not result and operation == NotionAPIOperation.SCHEDULED_TASKS:
                        clear_api_status(operation)
                    elif result is not False:  # This allows None (no return) and True to set success
                        set_success_api_status(operation)
                    return result
                except Exception as e:
                    set_error_api_status(operation, str(e))
                    raise
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator


# API I/S
def _invoke_notion_api(query_url, query_payload={}, method=Method.GET, print_response=False, print_response_type=''):
    results = []
    start_cursor = None

    resource_name = _get_notion_resource_name_from_id(query_url, query_payload)
    logger.debug(f"Invoking {method.capitalize() if query_url.split('/')[-1] != 'query' else Method.GET.capitalize()} "
                 f"API {f'for {resource_name}' if resource_name else ''}")

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
            if resource_name:
                logger.debug(f"Handling pagination for {resource_name} with cursor {start_cursor}...")
            else:
                logger.debug(f"Handling pagination with cursor {start_cursor}...")
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
            if method == Method.DELETE:
                response = requests.delete(url, headers=headers)
            elif method == Method.POST:
                response = requests.post(url, headers=headers, json=payload)
            elif method == Method.PATCH:
                response = requests.patch(url, headers=headers, json=payload)
        else:
            if method == Method.GET:
                response = requests.get(url, headers=headers)
            if method == Method.DELETE:
                response = requests.delete(url, headers=headers)
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


def create_page_with_db_dict(db_id, db_dict, property_overrides=None):
    generated_payload = generate_create_page_payload(db_id, db_dict, property_overrides)
    return create_page(generated_payload)


def create_page_with_db_dict_and_children_block(db_id, db_dict, children_block, property_overrides=None):
    generated_payload = generate_create_page_payload(db_id, db_dict, property_overrides)
    generated_payload.update(children_block)

    return create_page(generated_payload)


def update_page_with_relation(page_id_add_relation, page_id_data_to_import, relation_name, other_params={}, name=""):
    relation_payload = get_relation_payload(page_id_data_to_import, relation_name, other_params)
    update_page(page_id_add_relation, relation_payload)

    if name:
        logger.debug(f"Relation added successfully for {name}")
    else:
        logger.debug("Relation added successfully!")


def copy_pages_to_daily(config: TaskConfig) -> None:
    """
    Copy tasks from source database or specific page to daily tasks.
    Handles both single page copying and bulk copying scenarios.

    Args:
        config: TaskConfig object containing copying configuration
    """
    if config.page_id:
        _copy_single_page(config)
        return

    if not config.get_pages_func:
        logger.info(f"No get_pages_func provided and no page_id specified for {config.name}")
        return

    _copy_multiple_pages(config)


def _copy_single_page(config: TaskConfig) -> None:
    """Handle copying a single page based on page_id"""
    try:
        task_dict = {
            "Task": config.name,
            "Project": config.project,
            "Due": today.isoformat(),
            "Icon": config.icon
        }

        response = _create_page_with_config(task_dict, config)
        logger.info(f"Successfully created a daily {config.name} task with ID {response['id']}")

    except Exception as e:
        logger.error(f"Failed to create a daily {config.name} task - error {str(e)}")


def _copy_multiple_pages(config: TaskConfig) -> None:
    """Handle copying multiple pages from source database"""
    source_pages = config.get_pages_func()
    if not source_pages:
        logger.info(f"No {config.name} to update")
        return

    existing_task_names = _get_existing_task_names(config.daily_filter)
    success_count, error_count = 0, 0

    for source_page in source_pages:
        state = source_page['properties'][config.state_property_name]['formula']['string']

        if _is_page_exists(state, existing_task_names, config.state_suffix):
            logger.debug(f"Page for '{state}' already exists")
            continue

        try:
            task_dict = {
                "Task": state,
                "Project": config.project,
                "Due": _get_due_date(source_page, config),
                "Icon": config.icon
            }

            response = _create_page_with_config(task_dict, config, source_page.get('id'))
            logger.info(f"Successfully created a daily {config.name} task for {state} with ID {response['id']}")
            success_count += 1

        except Exception as e:
            logger.error(f"Failed to create a daily {config.name} task for {state} - error {str(e)}")
            error_count += 1

    _log_copy_results(config.name, success_count, error_count)


def _create_page_with_config(task_dict: dict, config: TaskConfig, page_id: str = None) -> dict:
    """Create a page with or without children block based on config"""
    if config.children_block:
        children_block = generate_page_content_page_notion_link(page_id or config.page_id)
        return create_page_with_db_dict_and_children_block(daily_tasks_db_id, task_dict, children_block)
    return create_page_with_db_dict(daily_tasks_db_id, task_dict)


def _get_existing_task_names(daily_filter: dict) -> list:
    """Get list of existing task names"""
    daily_tasks = get_daily_tasks(daily_filter)
    return [task['properties']['Task']['title'][0]['plain_text'] for task in daily_tasks]


def _is_page_exists(state: str, existing_names: list, suffix: str) -> bool:
    """Check if page already exists"""
    if suffix:
        return bool(find_state_items(existing_names, state, suffix))
    return state in existing_names


def _get_due_date(source_page: dict, config: TaskConfig) -> str:
    """Get due date from source page or default to today"""
    if config.date_property_name:
        return source_page['properties'][config.date_property_name]['formula']['date']['start']
    return today.isoformat()


def _log_copy_results(name: str, success_count: int, error_count: int) -> None:
    """Log results of copy operation"""
    if success_count > 0 and error_count > 0:
        logger.info(f"Successfully copied {success_count} tasks. Errors: {error_count}")
    elif success_count > 0:
        logger.info(f"Successfully copied {success_count} tasks")
    elif error_count > 0:
        logger.info(f"Failed to create daily {name} tasks - Errors: {error_count}")


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


def generate_icon_url(icon_type, icon_color=IconColor.LIGHT_GRAY):
    return f'https://www.notion.so/icons/{icon_type}_{icon_color}.svg'


def _get_notion_resource_name_from_id(url: str, payload: dict = {}) -> str:
    """
    Extract Notion ID from either URL or payload.

    Args:
        url: Notion API URL
        payload: Optional API payload that may contain database/page ID

    Returns:
        Optional[str]: Extracted Notion ID or None
    """
    id = ''
    # First try to get ID from URL
    url_parts = url.split('/')
    for part in url_parts:
        cleaned_part = part.strip().replace("-", "")
        if len(cleaned_part) == 32:
            id = cleaned_part

    # If not found in URL, check payload
    if not id and payload:
        # Check parent database_id if exists
        if 'parent' in payload and 'database_id' in payload['parent']:
            id = payload['parent']['database_id'].strip().replace("-", "")

        # Check direct database_id if exists
        if not id and 'database_id' in payload:
            id = payload['database_id'].strip().replace("-", "")

    return _notion_id_mapping.get(id, "")


def manage_daily_summary_pages():
    """Main function to manage daily summary pages"""
    try:
        daily_pages = get_db_pages(day_summary_db_id)
        api_pages = get_db_pages(api_db_id)

        if not daily_pages:
            logger.info("No daily summary pages found")
            return

        # First handle duplicates
        remove_duplicate_daily_pages(daily_pages)

        # Then handle missing relations
        if api_pages:
            add_missing_api_relations(daily_pages, api_pages)

    except Exception as e:
        logger.error(f"Error managing daily summary pages: {str(e)}")


def remove_duplicate_daily_pages(daily_pages: List[Dict]):
    """Process and remove duplicate daily summary pages"""
    try:
        # Group pages by date
        date_groups = group_pages_by_date(daily_pages)

        # Process each group of pages with the same date
        duplicates_removed = 0
        for date, pages in date_groups.items():
            if len(pages) > 1:
                duplicates_removed += remove_duplicates_for_date(pages)

        if duplicates_removed:
            logger.info(f"Removed {duplicates_removed} duplicate daily summary pages")
        else:
            logger.info("No duplicate daily summary pages found")

    except Exception as e:
        logger.error(f"Error removing duplicate daily pages: {str(e)}")


def group_pages_by_date(pages: List[Dict]) -> Dict[str, List[Dict]]:
    """Group pages by their date"""
    date_groups = {}
    for page in pages:
        try:
            try:
                date = page['properties']['Date']['date']['start']
            except TypeError:
                date = 'No Date'

            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(page)
        except KeyError:
            logger.warning(f"Page {page.get('id')} has no date property")
            continue
    return date_groups


def remove_duplicates_for_date(pages: List[Dict]) -> int:
    """Remove duplicate pages for a specific date"""
    if len(pages) <= 1:
        return 0

    if should_delete_no_date_pages(pages):
        return delete_pages_with_no_date(pages)

    pages_by_relation = separate_pages_by_relation(pages)
    return remove_duplicate_pages(pages_by_relation)


def should_delete_no_date_pages(pages: List[Dict]) -> bool:
    """Check if these are pages with no date"""
    try:
        return any(
            page['properties']['Date']['date'] is None
            for page in pages
        )
    except KeyError:
        return False


def delete_pages_with_no_date(pages: List[Dict]) -> int:
    """Delete all pages that have no date"""
    deleted_count = 0
    for page in pages:
        try:
            delete_page(page['id'])
            logger.debug(f"Removed page with no date {page['id']}")
            deleted_count += 1
        except Exception as e:
            logger.error(f"Error deleting page with no date {page['id']}: {str(e)}")
    return deleted_count


def has_api_relation(page: Dict) -> bool:
    """Check if page has API Status Page relation"""
    try:
        api_relation = page.get('properties', {}).get('API Status Page', {}).get('relation', [])
        return len(api_relation) > 0
    except Exception:
        return False


def separate_pages_by_relation(pages: List[Dict]) -> Dict[str, List[Dict]]:
    """Separate pages into those with and without API relations"""
    pages_by_relation = {
        'with_relations': [],
        'without_relations': []
    }

    for page in pages:
        if has_api_relation(page):
            pages_by_relation['with_relations'].append(page)
        else:
            pages_by_relation['without_relations'].append(page)

    return pages_by_relation


def remove_duplicate_pages(pages_by_relation: Dict[str, List[Dict]]) -> int:
    """Remove duplicate pages while preserving those with relations"""
    if pages_by_relation['with_relations']:
        logger.debug(
            f"Found {len(pages_by_relation['with_relations'])} pages with API relations - these will be preserved"
        )

    pages_to_remove = get_pages_to_remove(
        pages_by_relation['without_relations'] if len(pages_by_relation['without_relations']) > 0 else
        pages_by_relation['with_relations'])
    return delete_duplicate_pages(pages_to_remove)


def get_pages_to_remove(pages: List[Dict]) -> List[Dict]:
    """Get list of pages that should be removed"""
    if not pages:
        return []

    # Sort by last edited time, most recent first
    sorted_pages = sorted(
        pages,
        key=lambda x: x.get('last_edited_time', ''),
        reverse=True
    )

    # Keep the most recent, remove others
    return sorted_pages[1:]


def delete_duplicate_pages(pages: List[Dict]) -> int:
    """Delete the specified duplicate pages"""
    deleted_count = 0
    for page in pages:
        try:
            delete_page(page['id'])
            logger.debug(f"Removed duplicate page {page['id']}")
            deleted_count += 1
        except Exception as e:
            logger.error(f"Error deleting page {page['id']}: {str(e)}")
    return deleted_count


def add_missing_api_relations(daily_pages: List[Dict], api_pages: List[Dict]):
    """Add missing API page relations to daily summary pages"""
    try:
        # Create lookup dictionary for API pages by date
        api_pages_by_date = {
            page['properties']['Date']['date']['start']: page
            for page in api_pages
            if 'Date' in page['properties']
               and page['properties']['Date'].get('date')
        }

        relations_added = 0
        for daily_page in daily_pages:
            if add_api_relation_if_missing(daily_page, api_pages_by_date):
                relations_added += 1

        if relations_added:
            logger.info(f"Added {relations_added} missing API page relations")
        else:
            logger.info("No missing API page relations found")

    except Exception as e:
        logger.error(f"Error adding API relations: {str(e)}")


def add_api_relation_if_missing(daily_page: Dict, api_pages_by_date: Dict[str, Dict]) -> bool:
    """Add API relation to a daily page if missing and API page exists"""
    try:
        # Check if page already has API relation
        api_status_relation = daily_page['properties'].get('API Status Page', {}).get('relation', [])
        if api_status_relation:
            return False

        # Get date and find matching API page
        daily_date = daily_page['properties']['Date']['date']['start']
        api_page = api_pages_by_date.get(daily_date)

        if not api_page:
            return False

        # Add relation
        update_page_with_relation(
            daily_page['id'],
            api_page['id'],
            "API Status Page"
        )

        logger.debug(f"Added API relation to daily page {daily_page['id']}")
        return True

    except Exception as e:
        logger.error(f"Error processing relation for page {daily_page.get('id')}: {str(e)}")
        return False


def get_today_recurring_tasks():
    """Get all recurring tasks with Next Due = today"""
    today_date = today.isoformat()

    # Create filter for tasks due today
    today_filter = {
        "property": "Next Due",
        "formula": {
            "date": {
                "equals": today_date
            }
        }
    }

    recurring_tasks = get_recurring_tasks(today_filter)
    logger.debug(f"Found {len(recurring_tasks)} recurring tasks due today")

    return recurring_tasks


def create_recurring_combined_task_name(tasks, task_name_prefix):
    """
    Creates a combined task name from a list of task objects,
    sorted by priority (highest first).
    """
    if not tasks:
        return ""

    sorted_tasks = sorted(
        tasks,
        key=lambda task: task['properties'].get('Priority', {}).get('formula', {}).get('number', 0) or 0,
        reverse=True
    )

    task_names = [task_name_prefix]
    for task in sorted_tasks:
        try:
            task_name = task['properties']['Recurring Task']['title'][0]['plain_text']
            task_names.append(task_name)
        except (KeyError, IndexError) as e:
            logger.error(f"Error extracting task name: {str(e)}")
            continue

    return "\n".join(task_names)
