from datetime import timedelta

from common import replace_none_with_list_or_string, today, get_next_sunday
from notion_py.notion_globals import NotionPropertyType


def generate_payload(filter=None, sorts=None):
    new_payload = {}
    if filter:
        new_payload['filter'] = filter
    if sorts:
        new_payload['sorts'] = sorts
    return new_payload


def generate_create_page_payload(db_id, db_dict, property_overrides=None):
    """
    Generate Notion page creation payload with flexible property types.
    Handles predefined mappings and automatic type detection.

    Args:
        db_id (str): Database ID
        db_dict (dict): Dictionary of values to set
        property_overrides (dict, optional): Dictionary to override default property types

    Returns:
        dict: Notion API payload
    """
    daily_task_payload = {"parent": {"database_id": db_id}, "properties": {}}
    property_overrides = property_overrides or {}

    # Default property type mappings
    daily_db_items = {
        NotionPropertyType.TITLE: ["Name", "Task", "Day", "Expense", 'Month'],
        NotionPropertyType.TEXT: ["Sleep Start", "Sleep End", "Sleep Duration", "Activity Duration", "Memo",
                                  "Original Name", "Year"],
        NotionPropertyType.SELECT_ID: ["Project"],
        NotionPropertyType.SELECT_NAME: ["Sleep Feedback", "Person Card", "Status", "Type", "Original Currency",
                                         "Charged Currency", "Category"],
        NotionPropertyType.MULTI_SELECT: ["Activities", "Body Parts", "Equipment"],
        NotionPropertyType.DATE: ["Date", "Due", "Processed Date"],
        NotionPropertyType.URL: ["gCal Link"],
        NotionPropertyType.NUMBER: ["Steps", "Steps Goal", "Calories", "Sleep Note", "Activity Calories",
                                    "Charged Amount", "Original Amount", "Remaining Amount", "4 Months Average",
                                    "Target"],
        NotionPropertyType.RELATION: ["Exercises"]
    }

    def detect_property_type(key, value):
        """
        Detect property type based on predefined mappings and value analysis.
        """
        # First check predefined mappings
        for prop_type, keys in daily_db_items.items():
            if key in keys:
                return prop_type

        # Then check if it's a relation
        if isinstance(value, (list, tuple)):
            if all(isinstance(x, str) and len(x) >= 32 for x in value):
                return NotionPropertyType.RELATION
        elif isinstance(value, str) and len(value) >= 32:
            return NotionPropertyType.RELATION

        # Otherwise detect based on value type
        if isinstance(value, bool):
            return NotionPropertyType.CHECKBOX
        elif isinstance(value, (int, float)):
            return NotionPropertyType.NUMBER
        elif isinstance(value, (list, tuple)):
            return NotionPropertyType.MULTI_SELECT
        elif isinstance(value, str):
            if value.startswith(('http://', 'https://')):
                return NotionPropertyType.URL
            elif '@' in value and '.' in value.split('@')[1]:
                return NotionPropertyType.EMAIL
            else:
                return NotionPropertyType.TEXT

        return NotionPropertyType.TEXT

    def format_property_value(prop_type, value):
        """
        Format value according to Notion API requirements for each property type.
        """
        if value in (None, "", [], {}):
            return None

        if prop_type == NotionPropertyType.TITLE:
            return {"title": [{"text": {"content": str(value)}}]}

        elif prop_type == NotionPropertyType.TEXT:
            return {"rich_text": [{"text": {"content": str(value)}}]}

        elif prop_type == NotionPropertyType.NUMBER:
            return {"number": float(value)}

        elif prop_type == NotionPropertyType.CHECKBOX:
            return {"checkbox": bool(value)}

        elif prop_type == NotionPropertyType.SELECT_NAME:
            return {"select": {"name": str(value)}}

        elif prop_type == NotionPropertyType.SELECT_ID:
            return {"select": {"id": str(value)}}

        elif prop_type == NotionPropertyType.MULTI_SELECT:
            if isinstance(value, str):
                value = [value]
            return {"multi_select": [{"name": str(v)} for v in value]}

        elif prop_type == NotionPropertyType.DATE:
            if isinstance(value, list) and len(value) == 2:
                return {"date": {"start": value[0], "end": value[1]}}
            return {"date": {"start": value}}

        elif prop_type == NotionPropertyType.URL:
            return {"url": value}

        elif prop_type == NotionPropertyType.EMAIL:
            return {"email": value}

        elif prop_type == NotionPropertyType.RELATION:
            if isinstance(value, (list, tuple)):
                return {"relation": [{"id": str(id_)} for id_ in value]}
            return {"relation": [{"id": str(value)}]}

        elif prop_type == NotionPropertyType.PEOPLE:
            if isinstance(value, (list, tuple)):
                return {"people": [{"id": str(id_)} for id_ in value]}
            return {"people": [{"id": str(value)}]}

        # Default case
        return {"rich_text": [{"text": {"content": str(value)}}]}

    # Process each property
    for key, value in db_dict.items():
        if value in (None, "", [], {}):
            continue

        # Handle Icon specially
        if key == "Icon":
            if len(value) == 1:
                daily_task_payload["icon"] = {"type": "emoji", "emoji": value}
            else:
                daily_task_payload["icon"] = {"type": "external", "external": {"url": value}}
            continue

        # Get property type (from override, predefined mapping, or detect it)
        prop_type = (property_overrides.get(key) or  # First check overrides
                     next((t for t, keys in daily_db_items.items() if key in keys),
                          None) or  # Then check predefined mappings
                     detect_property_type(key, value))  # Finally auto-detect

        # Format and add the property value
        formatted_value = format_property_value(prop_type, value)
        if formatted_value is not None:
            daily_task_payload["properties"][key] = formatted_value

    return daily_task_payload

def get_relation_payload(page_id_data_to_import, relation_name, other_params={}):
    """
    Updates a page with a relation to another page.

    Parameters:
    - page_id_add_relation: The ID of the page where the relation will be added.
    - page_id_data_to_import: The ID of the page that will be linked as a relation.
    """

    if isinstance(page_id_data_to_import, list):
        relation_objects = [{"id": rel_id} for rel_id in page_id_data_to_import]
    else:
        relation_objects = [{"id": page_id_data_to_import}]

    # Payload for updating the relation
    relation_payload = {
        "properties": {
            relation_name: {
                "relation": relation_objects
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


uncheck_copied_to_daily_payload = {
    "properties": {
        "Copied to Daily": {
            "checkbox": False
        }
    }
}

check_copied_to_daily_payload = {
    "properties": {
        "Copied to Daily": {
            "checkbox": True
        }
    }
}

uncheck_done_set_today_payload = {
    "properties": {
        "Done": {
            "checkbox": False  # Set checkbox to False (uncheck)
        },
        "Due": {
            "date": {
                "start": get_next_sunday().isoformat()
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
