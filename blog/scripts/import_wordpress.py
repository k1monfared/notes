#!/usr/bin/env python3
"""Import posts from thesouthernhills.wordpress.com into the local blog.

Fetches all posts from the WordPress RSS feed, converts HTML to markdown,
wraps in RTL div, adds appropriate tags, and saves as blog post files.
"""

import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

FEED_URLS = [
    "https://thesouthernhills.wordpress.com/feed/",
    "https://thesouthernhills.wordpress.com/feed/?paged=2",
    "https://thesouthernhills.wordpress.com/feed/?paged=3",
]

BLOG_DIR = Path(__file__).parent
TAGS = "the_southern_hills, تپه‌های‌جنوبی"

# WordPress content namespace
NAMESPACES = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "wp": "http://wordpress.org/export/1.2/",
}


def fetch_feed(url):
    """Fetch and parse an RSS feed, return list of post dicts."""
    print(f"Fetching {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml_text = resp.read()

    root = ET.fromstring(xml_text)
    posts = []

    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "").strip()

        # Try content:encoded first, fall back to description
        content_el = item.find("content:encoded", NAMESPACES)
        if content_el is not None and content_el.text:
            content_html = content_el.text.strip()
        else:
            content_html = item.findtext("description", "").strip()

        # Parse date
        # Format: "Wed, 24 Sep 2014 05:30:55 +0000"
        try:
            dt = datetime.strptime(pub_date.rsplit(" ", 1)[0], "%a, %d %b %Y %H:%M:%S")
        except (ValueError, IndexError):
            dt = datetime.now()

        posts.append({
            "title": title,
            "link": link,
            "date": dt,
            "content_html": content_html,
        })

    return posts


def html_to_markdown(html_text):
    """Basic HTML to markdown conversion for WordPress content."""
    text = html_text

    # Handle common HTML entities
    text = html.unescape(text)

    # Convert <br> and <br/> to newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

    # Convert paragraphs
    text = re.sub(r"<p[^>]*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "", text, flags=re.IGNORECASE)

    # Convert headings
    for level in range(1, 7):
        text = re.sub(
            rf"<h{level}[^>]*>(.*?)</h{level}>",
            lambda m, l=level: f"\n\n{'#' * l} {m.group(1).strip()}\n\n",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

    # Convert bold
    text = re.sub(r"<(?:strong|b)>(.*?)</(?:strong|b)>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)

    # Convert italic
    text = re.sub(r"<(?:em|i)>(.*?)</(?:em|i)>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)

    # Convert links
    text = re.sub(
        r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        r"[\2](\1)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Convert images
    text = re.sub(
        r'<img[^>]*src="([^"]*)"[^>]*(?:alt="([^"]*)")?[^>]*/?>',
        lambda m: f'![{m.group(2) or ""}]({m.group(1)})',
        text,
        flags=re.IGNORECASE,
    )

    # Convert blockquotes
    text = re.sub(
        r"<blockquote[^>]*>(.*?)</blockquote>",
        lambda m: "\n" + "\n".join("> " + line for line in m.group(1).strip().splitlines()) + "\n",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Convert lists
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?[ou]l[^>]*>", "\n", text, flags=re.IGNORECASE)

    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def slugify(title):
    """Create a filename-safe slug from a Farsi title."""
    # Transliterate common words or just use a simple approach
    # For Farsi titles, we'll use the date-based naming
    slug = re.sub(r"[^\w\s-]", "", title, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "_", slug).strip("_")
    return slug[:60] if slug else "post"


def save_post(post):
    """Save a post as a markdown file in the blog directory."""
    dt = post["date"]
    date_prefix = dt.strftime("%Y%m%d")
    slug = slugify(post["title"])
    filename = f"{date_prefix}_{slug}.md"
    filepath = BLOG_DIR / filename

    if filepath.exists():
        print(f"  SKIP (exists): {filename}")
        return False

    content_md = html_to_markdown(post["content_html"])

    # Build the post
    lines = [
        "---",
        f"tags: {TAGS}",
        "---",
        "",
        f'<div dir="rtl" lang="fa" markdown="1">',
        "",
        f"# {post['title']}",
        "",
        content_md,
        "",
        "</div>",
        "",
        f'*Originally published on [تپه‌های جنوبی]({post["link"]})*',
        "",
    ]

    filepath.write_text("\n".join(lines), encoding="utf-8")
    print(f"  SAVED: {filename}")
    return True


def main():
    all_posts = []
    for url in FEED_URLS:
        try:
            posts = fetch_feed(url)
            if not posts:
                break
            all_posts.extend(posts)
        except Exception as e:
            print(f"  Feed error: {e}")
            break

    print(f"\nFound {len(all_posts)} posts total\n")

    # Sort by date (oldest first)
    all_posts.sort(key=lambda p: p["date"])

    saved = 0
    for post in all_posts:
        date_str = post["date"].strftime("%Y-%m-%d")
        print(f"[{date_str}] {post['title']}")
        if save_post(post):
            saved += 1

    print(f"\nDone: {saved} new posts saved, {len(all_posts) - saved} skipped")


if __name__ == "__main__":
    main()
