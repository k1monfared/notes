#!/usr/bin/env python3
"""Import Telegram channel messages as blog posts.

Parses Telegram HTML export and creates one blog post per message.
"""

import html
import re
from datetime import datetime
from pathlib import Path

BLOG_DIR = Path(__file__).parent
SOURCE = Path("/home/k1/backup/telegram_2025-05-29/chats/از لنگرود تا لنگفورد/messages.html")
TAGS = "from Langroud to Langford, از لنگرود تا لنگفورد"


def parse_messages(html_text):
    """Parse Telegram HTML export into list of (date, text) tuples."""
    messages = []

    # Find all message divs with their date and text
    # Date is in: <div class="pull_right date details" title="DD.MM.YYYY HH:MM:SS ...">
    # Text is in: <div class="text">...</div>
    pattern = re.compile(
        r'class="message default clearfix".*?'
        r'title="(\d{2}\.\d{2}\.\d{4})\s+\d{2}:\d{2}:\d{2}[^"]*".*?'
        r'<div class="text">\s*(.*?)\s*</div>',
        re.DOTALL
    )

    for m in pattern.finditer(html_text):
        date_str = m.group(1)  # DD.MM.YYYY
        text_html = m.group(2).strip()

        # Parse date
        dt = datetime.strptime(date_str, "%d.%m.%Y")

        # Convert HTML to markdown
        text = text_html
        text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        text = re.sub(r"<[^>]+>", "", text)  # strip remaining tags
        text = html.unescape(text).strip()

        if text:
            messages.append((dt, text))

    return messages


def slugify(text):
    """Create a short slug from the first few words."""
    words = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE).split()[:5]
    slug = "_".join(words).strip("_")
    return slug[:50] if slug else "post"


def main():
    html_text = SOURCE.read_text(encoding="utf-8")
    messages = parse_messages(html_text)

    print(f"Found {len(messages)} messages\n")

    saved = 0
    for dt, text in messages:
        date_prefix = dt.strftime("%Y%m%d")
        date_dash = dt.strftime("%Y-%m-%d")
        slug = slugify(text)

        filename = f"{date_prefix}_{slug}.md"
        filepath = BLOG_DIR / filename

        # Handle collision
        if filepath.exists():
            n = 2
            while True:
                filename = f"{date_prefix}_{slug}_{n}.md"
                filepath = BLOG_DIR / filename
                if not filepath.exists():
                    break
                n += 1

        # First line as title (truncated), or date
        first_line = text.split("\n")[0].strip()
        if len(first_line) > 80:
            title = first_line[:77] + "..."
        else:
            title = first_line

        lines = [
            "---",
            f"tags: {TAGS}",
            "---",
            "",
            '<div dir="rtl" lang="fa" markdown="1">',
            "",
            f"# {title}",
            "",
            text,
            "",
            "</div>",
            "",
        ]

        filepath.write_text("\n".join(lines), encoding="utf-8")
        print(f"  [{date_dash}] {title[:60]}")
        saved += 1

    print(f"\nSaved {saved} posts")


if __name__ == "__main__":
    main()
