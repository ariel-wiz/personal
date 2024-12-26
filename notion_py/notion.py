import argparse
import random

from crossfit.crossfit_notion_manager import CrossfitManager
from epub import read_epub
from common import create_tracked_lambda, create_shabbat_dates
from expense.notion_expense_service import NotionExpenseService
from garmin.garmin_manager import GarminManager
from jewish_calendar import JewishCalendarAPI
from logger import logger
from notion_py.helpers.notion_children_blocks import generate_children_block_for_daily_inspirations, \
    generate_children_block_for_shabbat
from notion_py.notion_globals import *
from notion_py.helpers.notion_payload import generate_payload, get_trading_payload, uncheck_done_set_today_payload, \
    check_done_payload, uncheck_copied_to_daily_payload, check_copied_to_daily_payload
from notion_py.helpers.notion_common import create_page_with_db_dict_and_children_block, \
    get_db_pages, track_operation, create_daily_summary_pages, create_daily_api_pages, \
    update_page, create_page, copy_pages_to_daily, get_daily_tasks, \
    get_daily_tasks_by_date_str, get_tasks, get_page, generate_icon_url, manage_daily_summary_pages
from variables import Paths


def create_trading_page(name_row, description, large_description, example):
    trading_payload = get_trading_payload(trading_db_id, name_row, description, large_description, example)
    create_page(trading_payload)


def create_daily_stoics(check_date=False):
    if check_date:
        daily_inspirations = get_daily_tasks(daily_filter=daily_inspiration_filter)
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
                "Icon": generate_icon_url(IconType.CHAT, IconColor.LIGHT_GRAY)
            }

            children_block = generate_children_block_for_daily_inspirations(note, author, main_content)
            response = create_page_with_db_dict_and_children_block(daily_tasks_db_id, stoic_dict, children_block)
            logger.info(
                f"Successfully created daily stoic page for {name} with due {str(date)} with ID {response['id']}")

        except Exception as e:
            logger.error(f"Error while creating daily stoic pages: {e}")
            continue


def copy_birthdays():
    birthday_config = TaskConfig(
        name="Birthday",
        get_pages_func=get_birthdays,
        state_property_name="FullBirthdayState",
        daily_filter=daily_birthday_category_filter,
        date_property_name="Next Birthday",
        icon=generate_icon_url(IconType.CAKE, IconColor.LIGHT_GRAY),
        project=Projects.birthdays,
        children_block=False
    )

    copy_pages_to_daily(birthday_config)


def get_birthday_daily_tasks():
    return get_daily_tasks(daily_filter=daily_birthday_category_filter, daily_sorts=[{
        "property": "Due",
        "direction": "ascending"
    }])


def get_book_summaries(get_books_not_copied=True):
    if get_books_not_copied:
        book_summaries_payload = generate_payload(book_summaries_not_copied_to_daily_filter)
    else:
        book_summaries_payload = {}
    return get_db_pages(book_summaries_db_id, book_summaries_payload)


def get_expenses_and_warranties():
    expensive_and_warranties_payload = generate_payload(expense_and_warranty_filter)
    return get_db_pages(expense_and_warranty_db_id, expensive_and_warranties_payload)


def get_insurances():
    insurances_payload = generate_payload(insurances_filter)
    return get_db_pages(insurance_db_id, insurances_payload)


@track_operation(NotionAPIOperation.COPY_PAGES)
def copy_book_summary():
    book_summaries = get_book_summaries(get_books_not_copied=True)
    if not book_summaries:
        logger.info("All the books were copied - Resetting 'Copied to Daily' property to False")
        uncheck_copied_to_daily_book_summaries()
        book_summaries = get_book_summaries(get_books_not_copied=True)

    book_summary_to_copy = random.choice(book_summaries)
    book_summary_to_copy_page_id = book_summary_to_copy["id"]
    book_summary_to_copy_state_name = book_summary_to_copy["properties"]["State"]["formula"]["string"]

    book_summary_config = TaskConfig(
        name=book_summary_to_copy_state_name,
        get_pages_func=None,
        state_property_name="State",
        daily_filter=daily_notion_category_filter,
        state_suffix="",
        icon=generate_icon_url(IconType.BOOK),
        project=Projects.notion,
        page_id=book_summary_to_copy_page_id
    )

    copy_pages_to_daily(book_summary_config)
    check_copied_to_daily_book_summaries(book_summary_to_copy_page_id)


def copy_expenses_and_warranty():
    expense_warranty_config = TaskConfig(
        name="Expense and Warranty",
        get_pages_func=get_expenses_and_warranties,
        state_property_name="WarrantyState",
        daily_filter=daily_notion_category_filter,
        state_suffix="end of warranty",
        icon=generate_icon_url(IconType.SIGNATURE, IconColor.LIGHT_GRAY),
        project=Projects.notion
    )

    copy_pages_to_daily(expense_warranty_config)


def copy_insurance():
    insurance_config = TaskConfig(
        name="Insurance",
        get_pages_func=get_insurances,
        state_property_name="InsuranceState",
        daily_filter=daily_notion_category_filter,
        state_suffix="end of insurance",
        icon=generate_icon_url(IconType.CURRENCY, IconColor.LIGHT_GRAY),
        project=Projects.notion
    )

    copy_pages_to_daily(insurance_config)


def copy_recurring_tasks():
    insurance_config = TaskConfig(
        name="Recurring Tasks",
        get_pages_func=get_dailystate_recurring,
        state_property_name="DailyState",
        daily_filter=daily_notion_category_filter,
        state_suffix="",
        icon=generate_icon_url(IconType.SYNC, IconColor.LIGHT_GRAY),
        project=Projects.notion
    )

    copy_pages_to_daily(insurance_config)


def copy_normal_tasks():
    insurance_config = TaskConfig(
        name="Normal Tasks",
        get_pages_func=get_dailystate_tasks,
        state_property_name="DailyState",
        daily_filter=daily_notion_category_filter,
        state_suffix="",
        icon=generate_icon_url(IconType.CHECKLIST, IconColor.LIGHT_GRAY),
        project=Projects.notion
    )

    copy_pages_to_daily(insurance_config)


def get_trading():
    return get_db_pages(trading_db_id)


def get_recurring():
    recurring_payload = generate_payload(recursive_filter, recursive_sorts)
    return get_db_pages(recurring_db_id, recurring_payload)


def get_dailystate_recurring():
    recurring_payload = generate_payload(daily_recurring_filter, recursive_sorts)
    return get_db_pages(recurring_db_id, recurring_payload)


def get_dailystate_tasks():
    tasks_payload = generate_payload(daily_recurring_filter)
    return get_db_pages(tasks_db_id, tasks_payload)


def get_zahar_nekeva():
    return get_db_pages(zahar_nekeva_db_id, print_response_type='zahar_nekeva')


def get_birthdays():
    birthday_payload = generate_payload(sorts=[{"property": "Next Birthday", "direction": "ascending"}])
    return get_db_pages(birthday_db_id, birthday_payload)


def create_parashat_hashavua():
    logger.info(f"Starting creating parashat hashavua")
    jewish_api = JewishCalendarAPI()
    shabbat_list = jewish_api.get_shabbat_times()

    for shabbat in shabbat_list:
        shabbat_dict = shabbat.to_dict()

        city_list = []
        for city in shabbat_dict["cities"]:
            city_name = city["city"]
            city_candle_lighting = city["candle_lighting"]
            city_candle_havdalah = city["havdalah"]
            city_str = f"{city_name} • 🌅{city_candle_lighting} -  🌠{city_candle_havdalah}"
            city_list.append(city_str)

        parasha_en_name = shabbat.parasha_name
        parasha_hebrew_name = shabbat.parasha_hebrew
        parasha_date = shabbat.date
        parasha_hebrew_date = shabbat.hebrew_date
        parasha_link = shabbat.link
        parasha_summary = shabbat.summary

        # variables to use in Notion
        notion_parasha_task_name = f"{parasha_hebrew_name}\n{city_list[0].split(' • ')[1]}"
        notion_link_name = f"{parasha_en_name} - {parasha_hebrew_date}"

        shabat_daily_tasks = get_daily_tasks_by_date_str(parasha_date, filter_to_add={"property": "Category",
                                                                                      "formula": {
                                                                                          "string": {
                                                                                              "contains": "Jewish"
                                                                                          }}})
        shabat_daily_page_exists = False
        if shabat_daily_tasks:
            for shabat_task in shabat_daily_tasks:
                if "פרשת" in shabat_task['properties']['Task']['title'][0]['plain_text']:
                    logger.info(f"Shabbat page for {parasha_date} already exists")
                    shabat_daily_page_exists = True
                    break

        if shabat_daily_page_exists:  # Get the next element in the main loop
            break

        shabbat_dates = create_shabbat_dates(parasha_date, shabbat.city_times[0].candle_lighting,
                                             shabbat.city_times[0].havdalah)

        formatted_shabat_data = {
            "Task": notion_parasha_task_name,
            "Project": Projects.jewish_holidays,
            "Due": shabbat_dates,
            "Icon": generate_icon_url(IconType.MENORAH, IconColor.LIGHT_GRAY)
        }

        shabat_children_block = generate_children_block_for_shabbat(city_list, parasha_summary,
                                                                    notion_link_name, parasha_link)
        create_page_with_db_dict_and_children_block(daily_tasks_db_id, formatted_shabat_data,
                                                    shabat_children_block)
        logger.info(f"Successfully created a Parasha page for {parasha_en_name}")


@track_operation(NotionAPIOperation.HANDLE_DONE_TASKS)
def copy_done_from_daily_to_copied_tasks():
    daily_tasks = get_daily_tasks(daily_filter=daily_notion_category_filter_with_done_last_week)
    for daily_task in daily_tasks:
        daily_page_id = daily_task['id']
        daily_page_name = daily_task['properties']['Task']['title'][0]['plain_text']
        daily_children = get_page(daily_page_id, get_children=True)
        if not daily_children:
            logger.debug(f"No children found for the daily task {daily_page_name}")
            continue

        try:
            daily_children_page_id = \
                (daily_children[0]['paragraph']['rich_text'][0]['mention']["page"]["id"]).replace("-", "")

        except KeyError as ke:
            logger.error(f"Could not get the children's page_id for {daily_page_name}: {ke}")
            continue

        try:
            update_page(daily_children_page_id, check_done_payload)
            logger.info(f"Successfully updated the status to done for the children of {daily_page_name}")
        except Exception as e:
            logger.error(f"Could not Update the status to done for the children of {daily_page_name}: {e}")
            continue


def uncheck_copied_to_daily_book_summaries():
    book_summaries = get_book_summaries(get_books_not_copied=False)
    if not book_summaries:
        logger.info("No book summaries were found to uncheck")
        return

    for book_summary in book_summaries:
        book_summary_id = book_summary["id"]
        update_page(book_summary_id, uncheck_copied_to_daily_payload)


def check_copied_to_daily_book_summaries(book_summary_page_id):
    update_page(book_summary_page_id, check_copied_to_daily_payload)


@track_operation(NotionAPIOperation.GARMIN)
def update_garmin_info(update_daily_tasks=True):
    garmin_manager = GarminManager(garmin_db_id, day_summary_db_id)
    garmin_manager.update_garmin_info(update_daily_tasks, fill_history=True)


@track_operation(NotionAPIOperation.UNCHECK_DONE)
def uncheck_done_weekly_task_id():
    update_page_payload = uncheck_done_set_today_payload
    update_page(weekly_task_page_id, update_page_payload)
    update_page(weight_page_id, update_page_payload)


@track_operation(NotionAPIOperation.CREATE_DAILY_PAGES)
def create_daily_pages():
    functions = [
        create_daily_summary_pages,
        create_daily_api_pages,
        create_parashat_hashavua,
        copy_recurring_tasks,
        copy_normal_tasks,
        manage_daily_summary_pages
    ]
    run_functions(functions)


@track_operation(NotionAPIOperation.COPY_PAGES)
def copy_pages_from_other_db_if_needed():
    functions = [
        copy_birthdays,
        copy_expenses_and_warranty,
        copy_insurance
    ]
    run_functions(functions)


def get_expenses_to_notion():
    expense_service = NotionExpenseService(expense_tracker_db_id, monthly_category_expense_db)
    expense_service.add_all_expenses_to_notion()


def run_functions(functions):
    # Loop through each function
    for func in functions:
        try:
            func()  # Call the function
        except Exception as e:
            print(f"Error in {func.__name__}: {e}")  # Print error with function name


def main(selected_tasks):
    try:
        if selected_tasks:
            for task in selected_tasks:
                task_function = task_map.get(task)
                if task_function != get_expenses_to_notion:
                    task_function(should_track=True)
                else:
                    task_function()
        else:
            # Manually call the functions here
            crossfit_manager = CrossfitManager(crossfit_exercises_db_id=Keys.crossfit_exercises_db_id,
                                               crossfit_workout_db_id=Keys.crossfit_workouts_db_id)
            # crossfit_manager.add_crossfit_exercises_to_notion()
            crossfit_manager.add_crossfit_workouts_to_notion()

            # get_expenses_to_notion()
            logger.info("End of manual run")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

    logger.info("Script completed successfully.")


if __name__ == '__main__':
    # Define the task mapping
    task_map = {
        'tasks': get_tasks,
        'trading': get_trading,
        'recursive': get_recurring,
        'zahar_nekeva': get_zahar_nekeva,
        'add_trading': create_tracked_lambda(
            create_trading_page,
            "ariel row",
            "ariel description",
            "ariel large description",
            "ariel example"
        ),
        'uncheck_done': uncheck_done_weekly_task_id,
        'handle_done_tasks': copy_done_from_daily_to_copied_tasks,
        'garmin': update_garmin_info,
        'create_daily_pages': create_daily_pages,
        'copy_pages': copy_pages_from_other_db_if_needed,
        'get_expenses': get_expenses_to_notion,
        'copy_book_summary': copy_book_summary,
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
