import argparse
from epub import read_epub
from garmin import get_garmin_info
from helpers import today, find_state_items, create_tracked_lambda
from notion_py.notion_globals import *
from notion_helpers import *
from variables import Paths


# https://developers.notion.com/reference/property-object


def create_trading_page(name_row, description, large_description, example):
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
    create_page(trading_payload)


def create_daily_stoics(check_date=False):
    if check_date:
        daily_inspirations = get_daily_tasks(daily_filter={"property": "Category",
                                                           "formula": {
                                                               "string": {
                                                                   "contains": "Daily Inspiration"
                                                               }}})
        daily_inspirations_dict = {
            daily_inspiration['properties']['Due']['date']['start']:
                daily_inspiration['properties']['Task']['title'][0]['plain_text'] for daily_inspiration in
            daily_inspirations
        }

    stoic_path = Paths.ebook + 'The Daily Stoic.epub'
    parsed_content = read_epub(stoic_path)
    for page in parsed_content:
        date = page['date']
        name = page['theme'].title()
        note = page['note']
        author = page['source'].title().lstrip("—")
        main_content = page['main_content']

        if check_date and str(date) in daily_inspirations_dict.keys():
            logger.info(f"A daily inspiration page {daily_inspirations_dict[str(date)]} already exists for {str(date)}")
            continue

        if not date or not name or not note:
            logger.info(f"Skipping page {name} without date or name or note object for {page['date_str']}")
            continue

        try:
            stoic_dict = {
                "Task": name,
                "Project": daily_inspiration_project_id,
                "Due": str(date),
                "Icon": "💬"
            }

            stoic_payload = generate_create_page_payload(daily_tasks_db_id, stoic_dict)
            stoic_payload["children"] = generate_children_block_for_daily_inspirations(note, author, main_content)

            response = create_page(stoic_payload)
            logger.info(
                f"Successfully created daily stoic page for {name} with due {str(date)} with ID {response['id']}")

        except Exception as e:
            logger.error(f"Error while creating daily stoic pages: {e}")
            continue


@track_operation(NotionAPIOperation.COPY_BIRTHDAYS)
def copy_birthdays():
    birthday_daily_tasks = get_birthday_tasks()
    daily_tasks_birthday_upcoming_state = [task['properties']['Task']['title'][0]['plain_text'] for task in
                                           birthday_daily_tasks]

    birthday_pages = get_birthdays()
    success_task_count = 0
    error_task_count = 0

    for birthday_page in birthday_pages:
        next_birthday = birthday_page['properties']['Next Birthday']['formula']['date']['start']
        birthday_state = birthday_page['properties']['FullBirthdayState']['formula']['string']

        if birthday_state in daily_tasks_birthday_upcoming_state:
            logger.info(f"Birthday task for {birthday_state} already exists")
            continue

        # if task['properties']['Due']['date']['end'] and '00:00:00' not in \
        #         task['properties']['Due']['date']['end'].split('T')[1].split('+')[0]:
        #     task_due = [task_due_start, task_due_end]
        # else:
        #     task_due = task_due_start

        birthday_task_dict = {
            "Task": birthday_state,
            "Project": Projects.birthdays,
            "Due": next_birthday,
            "Icon": "🎂"
        }

        birthday_task_payload = generate_create_page_payload(daily_tasks_db_id, birthday_task_dict)
        response = create_page(birthday_task_payload)

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


def copy_expenses_and_warranty():
    expense_and_warranties_pages = get_expenses_and_warranties()
    if not expense_and_warranties_pages:
        logger.info("No expenses and warranties to update")
        return

    daily_notion_category = get_daily_tasks(daily_notion_category_filter)
    daily_notion_category_task_names = [task['properties']['Task']['title'][0]['plain_text'] for task in
                                        daily_notion_category]

    success_task_count = 0
    error_task_count = 0

    for expense_and_warranty_page in expense_and_warranties_pages:
        warranty_state = expense_and_warranty_page['properties']['WarrantyState']['formula']['string']
        try:
            # Check for existing pages
            existing_page_in_daily = find_state_items(daily_notion_category_task_names, warranty_state, "end of warranty")
            if existing_page_in_daily:
                logger.info(f"Page for '{warranty_state}' already exists and is named '{existing_page_in_daily}'")
                continue

            # Create the page
            expense_and_warranty_task_dict = {
                "Task": warranty_state,
                "Project": Projects.notion,
                "Due": today.isoformat(),
                "Icon": "📝"
            }

            page_id = expense_and_warranty_page['id']

            expense_and_warranty_task_dict_task_payload = generate_create_page_payload(daily_tasks_db_id, expense_and_warranty_task_dict)
            expense_and_warranty_task_dict_task_payload.update(generate_page_content_page_notion_link(page_id))

            response = create_page(expense_and_warranty_task_dict_task_payload)

            logger.info(f"Successfully created a daily Expense and Warranty task for {warranty_state} with ID {response['id']}")
            success_task_count += 1
        except Exception as e:
            logger.error(
                f"Failed to create a daily Expense and Warranty task for {warranty_state}- error {str(e)}")
            error_task_count += 1
            continue
    logger.info(f"Successfully copied {success_task_count} tasks. Errors: {error_task_count}")


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


def get_birthday_tasks():
    return get_daily_tasks(daily_filter=daily_birthday_category_filter, daily_sorts=[{
        "property": "Due",
        "direction": "ascending"
    }])


def get_expenses_and_warranties():
    expensive_and_warranties_payload = generate_payload(expense_and_warranty_filter)
    return get_db_pages(expense_and_warranty_db_id, expensive_and_warranties_payload)


def get_trading():
    return get_db_pages(trading_db_id)


def get_recursive():
    recursive_payload = generate_payload(recursive_filter, recursive_sorts)
    return get_db_pages(recurring_db_id, recursive_payload)


def get_zahar_nekeva():
    return get_db_pages(zahar_nekeva_db_id, print_response_type='zahar_nekeva')


def get_birthdays():
    birthday_payload = generate_payload(sorts=[{"property": "Next Birthday", "direction": "ascending"}])
    return get_db_pages(birthday_db_id, birthday_payload)


@track_operation(NotionAPIOperation.UNCHECK_DONE)
def uncheck_done_weekly_task_id():
    update_data = {
        "properties": {
            "Done": {
                "checkbox": False  # Set checkbox to False (uncheck)
            },
            "Due": {
                "date": {
                    "start": (today + timedelta(days=1)).isoformat()
                }
            }
        }
    }
    update_page(weekly_task_page_id, update_data)


def check_exercise_according_to_activity_status(activity_status):
    if FieldMap.exercise in activity_status:
        activity = activity_status[FieldMap.exercise]
        if activity and "Nothing" not in activity:
            logger.debug(f"Checking {FieldMap.exercise} to true")
            return {FieldMap.exercise: {
                "checkbox": True
            }}
    return {}


@track_operation(NotionAPIOperation.UNCHECK_DONE)
def create_daily_pages():
    create_daily_summary_pages()
    create_daily_api_pages()


@track_operation(NotionAPIOperation.GARMIN)
def update_garmin_info(update_daily_tasks=True):
    yesterday_date = yesterday.strftime('%d-%m-%Y')
    logger.info(f"Updating Garmin info for {yesterday_date}")

    # Checking if the page exists already
    garmin_pages = []
    # garmin_pages = get_pages_by_date_offset(garmin_db_id, DateOffset.YESTERDAY)
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

        formatted_garmin_data = {
            "Name": yesterday_date,
            "Date": yesterday.isoformat(),
            "Sleep Start": garmin_dict['sleep_start'],
            "Sleep End": garmin_dict['sleep_end'],
            "Sleep Feedback": garmin_dict['sleep_feedback_overall'],
            "Sleep Note": garmin_dict['sleep_feedback_note'],
            "Sleep Duration": garmin_dict['sleep_duration'],
            "Steps": garmin_dict['steps'],
            "Steps Goal": garmin_dict['daily_steps_goal'],
            "Calories": garmin_dict['total_calories'],
            "Activity Duration": garmin_dict['total_activity_duration'],
            "Activity Calories": garmin_dict['total_activity_calories']
        }

        garmin_updated_payload = generate_create_page_payload(garmin_db_id, formatted_garmin_data)
        response = create_page(garmin_updated_payload)

        logger.info(f"Successfully created Garmin info for {yesterday_date}")

    if update_daily_tasks:
        garmin_page_id = response['id']
        activity_status = response["properties"]["Activity Status"]["formula"]["string"]

        daily_tasks = get_pages_by_date_offset(day_summary_db_id, DateOffset.YESTERDAY)
        if daily_tasks:
            daily_task_id = daily_tasks[0]["id"]
            other_fields = check_exercise_according_to_activity_status({FieldMap.exercise: activity_status})
            update_page_with_relation(daily_task_id, garmin_page_id, "Watch Metrics", other_fields)
            logger.info(f"Successfully updated daily task with Garmin info for {yesterday_date}")


def main(selected_tasks):
    try:
        if selected_tasks:
            for task in selected_tasks:
                task_function = task_map.get(task)
                if task_function:
                    task_function(should_track=True)
        else:
            # Manually call the functions here
            copy_expenses_and_warranty()
            logger.info("End of manual run")

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
        'add_trading': create_tracked_lambda(
            create_trading_page,
            "ariel row",
            "ariel description",
            "ariel large description",
            "ariel example"
        ),
        'uncheck_done': uncheck_done_weekly_task_id,
        'garmin': update_garmin_info,
        'create_daily_pages': create_daily_pages,
        'copy_birthdays': copy_birthdays,
    }

    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Run specified tasks.")
    for task in task_map.keys():
        parser.add_argument(f'--{task}', action='store_true', help=f"Run the task to {task.replace('_', ' ')}")

    args = parser.parse_args()

    # Gather selected tasks based on command-line arguments
    selected_tasks = [task for task in task_map.keys() if getattr(args, task)]
    # selected_tasks = ['copy_birthdays']

    # Call the main logic with the selected tasks
    main(selected_tasks)
