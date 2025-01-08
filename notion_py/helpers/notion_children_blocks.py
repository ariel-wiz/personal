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


def create_paragraph_block(content, bold_word=None, color_list=None, code_words=None):
    """
    Create a paragraph block with optional bold text, color, and code formatting.

    Parameters:
        content (str): The paragraph content.
        bold_word (str, optional): A word to format as bold in the paragraph.
        color_list (list, optional): A list of dictionaries with color mappings,
                                     e.g., [{"color": "red", "words": "error"}]
        code_words (list, optional): A list of words to format as inline code.

    Returns:
        dict: The Notion paragraph block.
    """
    rich_text = []

    def apply_color(text):
        """Finds the corresponding color for a given text if it exists."""
        for color_dict in color_list or []:
            if text in color_dict.get("words", []):
                return color_dict["color"]
        return "default"

    words = content.split()
    for i, word in enumerate(words):
        # Prepare annotations dictionary
        annotations = {}

        # Apply color
        word_color = apply_color(word)
        if word_color != "default":
            annotations["color"] = word_color

        # Apply bold formatting
        if bold_word and word in bold_word:
            annotations["bold"] = True

        # Apply code formatting
        is_code_word = code_words and word in code_words
        if is_code_word:
            annotations["code"] = True

        # Create rich text entry for the word
        rich_text.append({
            "type": "text",
            "text": {"content": word},
            "annotations": annotations
        })

        # Always add a normal space after the word (except for the last word)
        if i < len(words) - 1:
            rich_text.append({
                "type": "text",
                "text": {"content": " "},
                "annotations": {}
            })

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


def create_table_row(cells: list) -> dict:
    """Create a table row with the given cells"""
    return {
        "type": "table_row",
        "table_row": {
            "cells": [[{"type": "text", "text": {"content": str(cell)}}] for cell in cells]
        }
    }


def create_table_block(headers: list, rows: list) -> dict:
    """Create a table block with the given headers and rows"""
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": len(headers),
            "has_column_header": True,
            "has_row_header": False,
            "children": [create_table_row(headers)] + [create_table_row(row) for row in rows]

        }
    }


def create_heading_1_block(content):
    """Create a heading 3 block"""
    return _create_heading_block(content, heading_number=1)


def create_heading_2_block(content, color="default"):
    """Create a heading 3 block"""
    return _create_heading_block(content, heading_number=2, color=color)


def create_heading_3_block(content, color="default"):
    """Create a heading 3 block"""
    return _create_heading_block(content, heading_number=3, color=color)


def _create_heading_block(content, heading_number=3, color="default"):
    """Create a heading block with an optional color."""
    heading = f"heading_{heading_number}"
    return {
        "object": "block",
        "type": heading,
        heading: {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": content},
                    "annotations": {"color": color} if color != "default" else {}
                }
            ]
        }
    }



def create_section_text_with_bullet(title: str, bullet_points: list) -> list:
    """Create a section with title and bullet points"""
    blocks = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": f"{title}"}}]
            }
        }
    ]
    blocks.extend(create_bullet_list(bullet_points))
    return blocks


def create_bullet_list(items: list) -> list:
    """Create a list of bullet points"""
    return [
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": item}}]
            }
        }
        for item in items
    ]


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


def create_toggle_heading_block(content, children_blocks: list, heading_number=3, color_background="", link_url=None):
    """
    Create a toggle heading block with an optional hyperlink on a subpart of the text.

    :param content: Full text of the heading
    :param children_blocks: Blocks to be nested under the toggle
    :param heading_number: Level of heading (default is 3)
    :param color_background: Optional background color
    :param link_url: Dictionary with 'url' and optional 'subword' keys
    """
    heading_number_str = f"heading_{heading_number}"

    # Create rich text elements
    rich_text = []

    # Process link if provided
    if link_url and isinstance(link_url, dict) and 'url' in link_url:
        url = link_url['url']
        subword = link_url.get('subword', '')

        # Calculate start and end indices for linking
        if subword:
            start_index = content.find(subword)
            if start_index != -1:
                end_index = start_index + len(subword)

                # Text before the link
                if start_index > 0:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": content[:start_index]}
                    })

                # Linked text
                rich_text.append({
                    "type": "text",
                    "text": {
                        "content": content[start_index:end_index],
                        "link": {"url": url}
                    }
                })

                # Text after the link
                if end_index < len(content):
                    rich_text.append({
                        "type": "text",
                        "text": {"content": content[end_index:]}
                    })
            else:
                # If subword not found, create a single text element with link
                rich_text = [{
                    "type": "text",
                    "text": {
                        "content": content,
                        "link": {"url": url}
                    }
                }]
        else:
            # If no subword, link the entire content
            rich_text = [{
                "type": "text",
                "text": {
                    "content": content,
                    "link": {"url": url}
                }
            }]
    else:
        # No link
        rich_text = [{
            "type": "text",
            "text": {"content": content}
        }]

    block = {
        "object": "block",
        "type": heading_number_str,
        heading_number_str: {
            "color": f"{color_background}_background" if color_background else "default",
            "rich_text": rich_text,
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


def create_db_block(db_id: str) -> dict:
    """Create a block with a link to a Notion database"""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "mention",
                "mention": {
                    "type": "database",
                    "database": {
                        "id": db_id
                    }
                }
            }]
        }
    }


def create_column_block(title: str, content_blocks: list) -> dict:
    """Create a column block with a title and content blocks"""
    return {
        "object": "block",
        "type": "column",
        "column": {
            "children": [
                create_heading_2_block(title),
                *content_blocks
            ]
        }
    }


def create_metrics_single_paragraph(metrics_list: list) -> dict:
    """Create a paragraph block with metrics data"""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"type": "text", "text": {"content": line}}
                for line in metrics_list
            ]
        }
    }


def create_metrics_paragraph(metric: str) -> dict:
    """Create a single paragraph block for a metric"""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"type": "text", "text": {"content": metric}}
            ]
        }
    }


def create_stats_list(stats_list: list) -> list:
    """Create a list of bullet points from stats data"""
    return [
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {"type": "text", "text": {"content": stat}}
                ]
            }
        }
        for stat in stats_list
    ]


def create_two_column_section(left_column: dict, right_column: dict) -> dict:
    """Create a two-column section with provided column data"""
    return {
        "object": "block",
        "type": "column_list",
        "column_list": {
            "children": [left_column, right_column]
        }
    }


def create_toggle_stats_block(title: str, stats_list: list) -> dict:
    """Create a toggle block with stats list"""
    return {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": title}
                }
            ],
            "children": create_stats_list(stats_list)
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


def create_three_column_layout(left_content: dict, middle_content: dict, right_content: dict) -> dict:
    """Creates a three column layout with equal width columns"""
    return {
        "object": "block",
        "type": "column_list",
        "column_list": {
            "children": [
                {
                    "object": "block",
                    "type": "column",
                    "column": {
                        "children": [left_content]
                    }
                },
                {
                    "object": "block",
                    "type": "column",
                    "column": {
                        "children": [middle_content]
                    }
                },
                {
                    "object": "block",
                    "type": "column",
                    "column": {
                        "children": [right_content]
                    }
                }
            ]
        }
    }


def create_callout_block(children: list = None,
                         title: str = None,
                         background: str = "default",
                         emoji: str = "⭐",
                         link: str = None,
                         bold_title: bool = False,
                         color_background="") -> dict:
    """
    Creates a callout block with customizable properties

    Args:
        children (list): List of child blocks to include in the callout
        title (str): The main text content of the callout
        background (str): Color of the callout background (e.g., "blue_background", "default")
        emoji (str): Emoji to use as the callout icon
        link (str): Optional URL to make the text a hyperlink
        bold_title (bool): Whether the title should be bold

    Returns:
        dict: Notion API compatible callout block structure
    """
    # Initialize rich_text content with optional bold formatting
    rich_text_content = {
        "type": "text",
        "text": {
            "content": title,
            "link": {"url": link} if link else None
        },
        "annotations": {"bold": bold_title} if bold_title else {}
    }

    # Initialize the base callout structure
    callout_block = {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [rich_text_content],
            "color": f"{color_background}_background" if color_background else "default",
            "icon": {
                "type": "emoji",
                "emoji": emoji
            }
        }
    }

    # Add children blocks if provided
    if children:
        callout_block["callout"]["children"] = children

    return callout_block
