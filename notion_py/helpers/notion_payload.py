from datetime import timedelta

from common import replace_none_with_list_or_string, today
from notion_py.notion_globals import NotionPropertyType


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
        NotionPropertyType.TEXT: ["Sleep Start", "Sleep End", "Sleep Duration", "Activity Duration", "Memo"],
        NotionPropertyType.SELECT_ID: ["Project"],
        NotionPropertyType.SELECT_NAME: ["Sleep Feedback", "Person Card", "Status", "Type", "Original Currency",
                                         "Charged Currency"],
        NotionPropertyType.MULTI_SELECT: ["Category"],
        NotionPropertyType.DATE: ["Date", "Due", "Processed Date"],
        NotionPropertyType.URL: ["gCal Link"],
        NotionPropertyType.NUMBER: ["Steps", "Steps Goal", "Calories", "Sleep Note", "Activity Calories",
                                    "Charged Amount", "Original Amount"]
    }

    daily_db_payload = {
        NotionPropertyType.TITLE: {"title": [{"text": {"content": None}}]},
        NotionPropertyType.TEXT: {"rich_text": [{"text": {"content": None}}]},
        NotionPropertyType.SELECT_ID: {"select": {"id": None}},
        NotionPropertyType.MULTI_SELECT: {"multi_select": []},
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
                if db_item_category_key == NotionPropertyType.DATE and isinstance(value, list) and len(
                        value) == 2:  # Start date and end date
                    start_date = value[0]
                    end_date = value[1]
                    payload_element = replace_none_with_list_or_string(daily_db_payload[db_item_category_key],
                                                                       start_date)
                    payload_element["date"]["end"] = end_date
                elif db_item_category_key == NotionPropertyType.MULTI_SELECT:
                    if isinstance(value, str):
                        value = [value]
                    payload_element = {"multi_select": [{"name": v} for v in value]}
                else:
                    payload_element = replace_none_with_list_or_string(daily_db_payload[db_item_category_key], value)
                daily_task_payload["properties"][key] = payload_element
                break

    return daily_task_payload


def get_relation_payload(page_id_data_to_import, relation_name, other_params={}):
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

    return relation_payload


def get_api_status_payload(status, operation):
    return {
        "properties": {
            operation: {
                "select": {
                    "name": status
                }
            }
        }
    }


def get_trading_payload(db_id, name_row, description, large_description, example):
    trading_payload = {
        "parent": {"database_id": db_id},
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
    return trading_payload


uncheck_done_set_today_payload = {
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
check_done_payload = {
    "properties": {
        "Done": {
            "checkbox": True
        }
    }
}

