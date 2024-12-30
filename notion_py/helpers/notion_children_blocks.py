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
    return {"children": children_block}


def generate_simple_page_content(content, add_separator=False):
    children_list = []
    for sentence in content:
        sentence_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": sentence}}]
            }
        }
        children_list.append(sentence_block)
    if add_separator:
        children_list.append(create_separator_block())
    return {"children": children_list}


def generate_page_content_page_notion_link(page_link):
    children_block = {"children": [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "mention",
                        "mention": {
                            "type": "page",
                            "page": {
                                "id": page_link
                            }
                        }
                    }
                ]
            }
        }
    ]
    }
    return children_block


def create_rich_text(content, link_url=None):
    """Create a rich text object with optional link"""
    text_object = {
        "type": "text",
        "text": {
            "content": content
        }
    }
    if link_url:
        text_object["text"]["link"] = {"url": link_url}
    return text_object


def create_paragraph_block(content, bold_word=None):
    """
    Create a paragraph block with optional bold text.

    Parameters:
        content (str): The paragraph content.
        bold_word (str, optional): A word to format as bold in the paragraph.

    Returns:
        dict: The Notion paragraph block.
    """
    rich_text = []

    if bold_word and bold_word in content:
        # Split content into parts: before, the bold word, and after
        before, _, after = content.partition(bold_word)
        if before:
            rich_text.append({"type": "text", "text": {"content": before}})
        rich_text.append({
            "type": "text",
            "text": {"content": bold_word},
            "annotations": {"bold": True},
        })
        if after:
            rich_text.append({"type": "text", "text": {"content": after}})
    else:
        # No bold word, default to plain text
        rich_text.append({"type": "text", "text": {"content": content}})

    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": rich_text}
    }


def create_number_block(numbered_list_items):
    """Create a paragraph block"""
    return [{
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {
            "rich_text": [{
                "type": "text",
                "text": {"content": step}
            }]
        }
    } for step in numbered_list_items]


def create_heading_3_block(content):
    """Create a heading 3 block"""
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [create_rich_text(content)]
        }
    }


def create_toggle_block(content, children_blocks):
    """Create a toggle block with children"""
    return {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": [create_rich_text(content)],
            "children": children_blocks
        }
    }


def create_toggle_heading_block(content, children_blocks, heading_number=3, color_background=""):
    """Create a toggle heading block."""
    heading_number_str = f"heading_{heading_number}"
    block = {
        "object": "block",
        "type": heading_number_str,
        heading_number_str: {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": content},
                    "annotations": {"color": f"{color_background}_background"} if color_background else {}
                }
            ],
            "is_toggleable": True,
            "children": children_blocks
        }
    }
    return block


def create_code_block(content, language="python"):
    """Create a code block"""
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [create_rich_text(content)],
            "language": language
        }
    }


def create_separator_block():
    """Create a separator block"""
    return {
        "object": "block",
        "type": "divider",
        "divider": {}
    }


def create_columns(column_blocks):
    """Create a column list with multiple columns"""
    return {
        "object": "block",
        "type": "column_list",
        "column_list": {
            "children": [
                {
                    "object": "block",
                    "type": "column",
                    "column": {
                        "children": [block] if not isinstance(block, list) else block
                    }
                }
                for block in column_blocks
            ]
        }
    }


def create_notion_link(page_id, text):
    """Create a link to another Notion page"""
    return {
        "type": "text",
        "text": {
            "content": text,
            "link": {
                "type": "page_id",
                "page_id": page_id
            }
        }
    }


def generate_children_block_for_crossfit_workout(title: str, exercises: list, additional_info: list,
                                                 original_program: str = "", add_score: bool = False,
                                                 add_original_program: bool = True) -> dict:
    """Generate workout block with optional score table."""

    try:
        columns = [{"name": "Exercise", "type": "mention", "field": "id"}]
        other_fields = [k for k in exercises[0].keys() if k != "id"]
        columns.extend([{
            "name": key.capitalize(),
            "type": "text",
            "field": key
        } for key in other_fields if isinstance(key, str)])

        workout_table = {
            "object": "block",
            "type": "table",
            "table": {
                "table_width": len(columns),
                "has_column_header": True,
                "has_row_header": False,
                "children": [
                                {
                                    "type": "table_row",
                                    "table_row": {
                                        "cells": [[{
                                            "type": "text",
                                            "text": {"content": col["name"]},
                                        }] for col in columns]
                                    }
                                }
                            ] + [
                                {
                                    "type": "table_row",
                                    "table_row": {
                                        "cells": [
                                            [{
                                                "type": "mention",
                                                "mention": {"page": {"id": exercise[col["field"]]}}
                                            }] if col["type"] == "mention" else
                                            [{"type": "text", "text": {"content": str(exercise.get(col["field"], ""))}}]
                                            for col in columns
                                        ]
                                    }
                                }
                                for exercise in exercises
                            ]
            }
        }

        children_block = [create_heading_3_block(title), workout_table]
        if additional_info:
            for info in additional_info:
                children_block.append(create_paragraph_block(info, bold_word=info.split(" - ")[0]))
            children_block.append(create_paragraph_block(""))
        if add_original_program and original_program:
            children_block.append(create_toggle_block("Original Exercise", [create_paragraph_block(original_program)]))
        children_block.append(create_separator_block())

        if add_score:
            score_table = {
                "object": "block",
                "type": "table",
                "table": {
                    "table_width": 2,
                    "has_column_header": True,
                    "has_row_header": False,
                    "children": [
                                    {
                                        "type": "table_row",
                                        "table_row": {
                                            "cells": [[{
                                                "type": "text",
                                                "text": {"content": header},
                                                "annotations": {"color": "green"}  # Added color to header
                                            }] for header in ["Date", "Score"]]
                                        }
                                    }
                                ] + [
                                    {
                                        "type": "table_row",
                                        "table_row": {
                                            "cells": [[{"type": "text", "text": {"content": ""}}] for _ in range(2)]
                                        }
                                    } for _ in range(2)  # Two empty rows
                                ]
                }
            }

            children_block.append(create_toggle_heading_block("My Score 💪", [score_table], color_background="green"))

        return {"children": children_block}
    except Exception as e:
        error_message = f"Error in generate_children_block_for_crossfit_workout: {e}"
        raise Exception(error_message)


def generate_children_block_for_crossfit_exercise(description_steps, tips):
    return {
        "children": [
            {
                "object": "block",
                "type": "column_list",
                "column_list": {
                    "children": [
                        {
                            "object": "block",
                            "type": "column",
                            "column": {
                                "children": [
                                    {
                                        "object": "block",
                                        "type": "heading_2",
                                        "heading_2": {
                                            "rich_text": [{"text": {"content": "Description 📑"}}],
                                            "color": "gray_background"
                                        }
                                    },
                                    {
                                        "object": "block",
                                        "type": "divider",
                                        "divider": {}
                                    },
                                    *[{
                                        "object": "block",
                                        "type": "bulleted_list_item",
                                        "bulleted_list_item": {
                                            "rich_text": [{"text": {"content": step}}]
                                        }
                                    } for step in description_steps]
                                ]
                            }
                        },
                        {
                            "object": "block",
                            "type": "column",
                            "column": {
                                "children": [
                                    {
                                        "object": "block",
                                        "type": "heading_2",
                                        "heading_2": {
                                            "rich_text": [{"text": {"content": "Tips 👌"}}],
                                            "color": "brown_background"
                                        }
                                    },
                                    {
                                        "object": "block",
                                        "type": "divider",
                                        "divider": {}
                                    },
                                    *[{
                                        "object": "block",
                                        "type": "bulleted_list_item",
                                        "bulleted_list_item": {
                                            "rich_text": [{"text": {"content": tip}}]
                                        }
                                    } for tip in tips]
                                ]
                            }
                        }
                    ]
                }
            }
        ]
    }


def generate_children_block_for_shabbat(shabat_cities, parasha_summary, parasha_link_name, parasha_link):
    # Create sentence blocks
    summary_blocks = [
        create_paragraph_block(f"{sentence}.")
        for sentence in parasha_summary.split('. ')
        if sentence.strip()
    ]

    # Create city blocks
    cities_blocks = [
        create_paragraph_block(city)
        for city in shabat_cities
    ]

    # Create toggle block with cities
    toggle_block = create_toggle_heading_block("🕊️ זמני שבת", cities_blocks)

    # Create link block
    link_block = create_paragraph_block(f"🔗 {parasha_link_name}", parasha_link)

    # Combine everything
    children_blocks = [toggle_block] + summary_blocks + [link_block]

    return {"children": children_blocks}
