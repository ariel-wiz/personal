import argparse
from epub import read_epub
from garmin import get_garmin_info
from common import create_tracked_lambda, create_shabbat_dates, yesterday, \
    DateOffset
from jewish_calendar import JewishCalendarAPI
from logger import logger
from notion_py.helpers.notion_children_blocks import generate_children_block_for_daily_inspirations, \
    generate_children_block_for_shabbat
from notion_py.notion_globals import *
from notion_py.helpers.notion_payload import generate_payload, get_trading_payload, uncheck_done_set_today_payload, \
    check_done_payload
from notion_py.helpers.notion_common import create_page_with_db_dict, create_page_with_db_dict_and_children_block, \
    update_page_with_relation, get_db_pages, track_operation, create_daily_summary_pages, create_daily_api_pages, \
    update_page, create_page, get_pages_by_date_offset, recurring_tasks_to_daily, get_daily_tasks, \
    get_daily_tasks_by_date_str, get_tasks, get_page
from variables import Paths


# https://developers.notion.com/reference/property-object


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
                "Icon": "💬"
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
        icon="🎂",
        project=Projects.birthdays,
        children_block=False
    )

    recurring_tasks_to_daily(birthday_config)


def get_birthday_daily_tasks():
    return get_daily_tasks(daily_filter=daily_birthday_category_filter, daily_sorts=[{
        "property": "Due",
        "direction": "ascending"
    }])


def get_expenses_and_warranties():
    expensive_and_warranties_payload = generate_payload(expense_and_warranty_filter)
    return get_db_pages(expense_and_warranty_db_id, expensive_and_warranties_payload)


def get_insurances():
    insurances_payload = generate_payload(insurances_filter)
    return get_db_pages(insurance_db_id, insurances_payload)


def copy_expenses_and_warranty():
    expense_warranty_config = TaskConfig(
        name="Expense and Warranty",
        get_pages_func=get_expenses_and_warranties,
        state_property_name="WarrantyState",
        daily_filter=daily_notion_category_filter,
        state_suffix="end of warranty",
        icon="📝",
        project=Projects.notion
    )

    recurring_tasks_to_daily(expense_warranty_config)


def copy_insurance():
    insurance_config = TaskConfig(
        name="Insurance",
        get_pages_func=get_insurances,
        state_property_name="InsuranceState",
        daily_filter=daily_notion_category_filter,
        state_suffix="end of insurance",
        icon="🤑",
        project=Projects.notion
    )

    recurring_tasks_to_daily(insurance_config)


def copy_recurring_tasks():
    insurance_config = TaskConfig(
        name="Recurring Tasks",
        get_pages_func=get_dailystate_recurring,
        state_property_name="DailyState",
        daily_filter=daily_notion_category_filter,
        state_suffix="",
        icon="🔁",
        project=Projects.notion
    )

    recurring_tasks_to_daily(insurance_config)


def copy_normal_tasks():
    insurance_config = TaskConfig(
        name="Normal Tasks",
        get_pages_func=get_dailystate_tasks,
        state_property_name="DailyState",
        daily_filter=daily_notion_category_filter,
        state_suffix="",
        icon="✔️",
        project=Projects.notion
    )

    recurring_tasks_to_daily(insurance_config)


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


def check_exercise_according_to_activity_status(activity_status):
    if FieldMap.exercise in activity_status:
        activity = activity_status[FieldMap.exercise]
        if activity and "Nothing" not in activity:
            logger.debug(f"Checking {FieldMap.exercise} to true")
            return {FieldMap.exercise: {
                "checkbox": True
            }}
    return {}


def create_parashat_hashavua():
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
            "Icon": "🕯️"
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


@track_operation(NotionAPIOperation.GARMIN)
def update_garmin_info(update_daily_tasks=True):
    yesterday_date = yesterday.strftime('%d-%m-%Y')
    logger.info(f"Updating Garmin info for {yesterday_date}")

    # Checking if the page exists already
    garmin_pages = get_pages_by_date_offset(garmin_db_id, DateOffset.YESTERDAY)
    if garmin_pages:
        garmin_page_id = garmin_pages[0]["id"]
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
            "Activity Calories": garmin_dict['total_activity_calories'],
            "Icon": "⌚"
        }

        response = create_page_with_db_dict(garmin_db_id, formatted_garmin_data)

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


@track_operation(NotionAPIOperation.UNCHECK_DONE)
def uncheck_done_weekly_task_id():
    update_page_payload = uncheck_done_set_today_payload
    update_page(weekly_task_page_id, update_page_payload)


@track_operation(NotionAPIOperation.CREATE_DAILY_PAGES)
def create_daily_pages():
    create_daily_summary_pages()
    create_daily_api_pages()
    create_parashat_hashavua()
    copy_recurring_tasks()
    copy_normal_tasks()


@track_operation(NotionAPIOperation.COPY_PAGES)
def copy_pages_from_other_db_if_needed():
    copy_birthdays()
    copy_expenses_and_warranty()
    copy_insurance()


def main(selected_tasks):
    try:
        if selected_tasks:
            for task in selected_tasks:
                task_function = task_map.get(task)
                if task_function:
                    task_function(should_track=True)
        else:
            # Manually call the functions here
            copy_done_from_daily_to_copied_tasks()
            logger.info("End of manual run")

    except Exception as e:
        logger.error(f"Error: {e}")

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
