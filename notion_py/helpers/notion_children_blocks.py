

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


def create_paragraph_block(content, link_url=None):
    """Create a paragraph block"""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [create_rich_text(content, link_url)]
        }
    }


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


def create_toggle_heading_3_block(content, children_blocks):
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [
                {
                    "text": {
                        "content": content
                    }
                }
            ],
            "is_toggleable": True,
            "children": children_blocks
        }
    }


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
    toggle_block = create_toggle_heading_3_block("🕊️ זמני שבת", cities_blocks)

    # Create link block
    link_block = create_paragraph_block(f"🔗 {parasha_link_name}", parasha_link)

    # # Create columns with toggle and link
    # columns_block = create_columns([
    #     [toggle_block],  # First column
    #     [link_block]  # Second column
    # ])

    # Combine everything
    children_blocks = [toggle_block] + summary_blocks + [link_block]

    return {"children": children_blocks}
