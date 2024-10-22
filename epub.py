from datetime import datetime

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re

from variables import Paths

stoic_path = Paths.ebook + 'The Daily Stoic.epub'


def create_notion_page_content(page_data):
    # Add a space after each period in the main content
    main_content = re.sub(r'\.(?![\s\n])', '. ', page_data['main_content'])

    notion_content = f"""# {page_data['date'].strftime('%B %d, %Y')} - {page_data['theme']}

> *"{page_data['note']}"*
> 
> {page_data['source']}

{main_content}
"""
    return notion_content


def parse_daily_stoic_page(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract the title (date and theme)
    title_element = soup.find('h3', class_='x05-Head-A')
    title = title_element.text.strip() if title_element else None

    # Extract the date and theme
    date_str = None
    theme = None
    if title:
        match = re.match(
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+)(?:st|nd|rd|th)?\s*(.+)',
            title)
        if match:
            month, day, theme = match.groups()
            date_str = f"{month} {day}"
            theme = theme.strip()

    # Convert date string to Python date object and adjust to future date
    date_obj = None
    if date_str:
        try:
            current_date = datetime.now().date()
            # Attempt to parse the date string
            parsed_date = datetime.strptime(f"{date_str} {current_date.year}", "%B %d %Y").date()

            if not parsed_date:
                parsed_date = datetime.strptime(f"{date_str} {current_date.year + 1}", "%B %d %Y").date()

            # Ensure the date is on or after today's date
            target_date = current_date
            while parsed_date < target_date:
                parsed_date = parsed_date.replace(year=parsed_date.year + 1)

            # Finally, ensure that parsed_date is still valid and not None
            date_obj = parsed_date

        except ValueError:
            pass

    # Extract the note (quote and author)
    note_element = soup.find('p', class_='x03-Chapter-Epigraph')
    note = note_element.text.strip() if note_element else None

    # Extract the source
    source_element = soup.find('p', class_='x03-Chapter-Epigraph-Source')
    source = source_element.text.strip() if source_element else None

    # Extract the main content
    main_content_elements = soup.find_all('p', class_=['x03-CO-Body-Text', 'x04-Body-Text'])
    main_content = ' '.join([p.text.strip() for p in main_content_elements])

    return {
        'title': title,
        'date_str': date_str,
        'date': date_obj,
        'theme': theme,
        'note': note,
        'source': source,
        'main_content': main_content
    }


def read_epub(epub_path):
    book = epub.read_epub(epub_path)
    results = []

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            html_content = item.get_content().decode('utf-8')
            page_data = parse_daily_stoic_page(html_content)
            if page_data['title']:  # Only append if we found a title (to filter out non-content pages)
                results.append(page_data)

    return results



# parsed_content = read_epub(stoic_path)
#
# # Print the first entry as an example
# if parsed_content:
#     entry = parsed_content[0]
#     print("Title:", entry['title'])
#     print("Date:", entry['date_str'])
#     print("Python Date Object:", entry['date'])
#     print("Theme:", entry['theme'])
#     print("Note:", entry['note'])
#     print("Main Content:", entry['main_content'][:100] + "...")  # First 100 characters
