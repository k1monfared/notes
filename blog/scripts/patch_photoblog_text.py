#!/usr/bin/env python3
"""Patch photoblog posts to include text content from original Blogger posts.

Re-fetches the Blogger feed and extracts any non-image text content,
then adds it to existing posts that are missing the text.
"""

import html
import json
import re
import time
import urllib.request
from pathlib import Path

BLOG_DIR = Path(__file__).parent.parent
FEED_BASE = "https://k1-photo.blogspot.com/feeds/posts/default"
BATCH_SIZE = 50


def fetch_feed_page(start_index):
    url = f"{FEED_BASE}?alt=json&max-results={BATCH_SIZE}&start-index={start_index}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def extract_text(content_html):
    """Extract non-image text from post HTML."""
    text = content_html

    # Remove image-related tags entirely
    text = re.sub(r'<a[^>]*>\s*<img[^>]*/?\s*>\s*</a>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<img[^>]*/?\s*>', '', text, flags=re.IGNORECASE)

    # Remove separator divs that are now empty
    text = re.sub(r'<div[^>]*class="separator"[^>]*>\s*</div>', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Convert HTML to plain text
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r'<div[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text).strip()

    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    return text if text else None


def slugify(title):
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "_", slug).strip("_")
    return slug[:50] if slug else "photo"


EMPTY_TITLES = {"", ".", "-", "...", "—"}


def find_post_file(date_prefix, title):
    """Find the matching post file for a Blogger entry."""
    if title.strip() in EMPTY_TITLES:
        slug = "photo"
    else:
        slug = slugify(title)

    # Try exact match first
    pattern = f"{date_prefix}_{slug}_photo.md"
    path = BLOG_DIR / pattern
    if path.exists():
        return path

    # Try numbered variants
    for n in range(2, 100):
        pattern = f"{date_prefix}_{slug}_{n}_photo.md"
        path = BLOG_DIR / pattern
        if path.exists():
            return path

    return None


def main():
    from datetime import datetime

    print("Fetching posts and extracting text...\n")

    patched = 0
    total = 0
    start = 1

    while True:
        try:
            feed_data = fetch_feed_page(start)
        except Exception as e:
            print(f"Feed error at {start}: {e}")
            break

        entries = feed_data.get("feed", {}).get("entry", [])
        if not entries:
            break

        for entry in entries:
            title = entry.get("title", {}).get("$t", "").strip()
            pub = entry.get("published", {}).get("$t", "")
            content_html = entry.get("content", {}).get("$t", "")

            try:
                dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue

            date_prefix = dt.strftime("%Y%m%d")

            # Extract text from HTML
            text = extract_text(content_html)
            if not text:
                total += 1
                continue

            # Find the post file
            post_file = find_post_file(date_prefix, title)
            if not post_file:
                total += 1
                continue

            # Check if text is already in the post
            existing = post_file.read_text(encoding="utf-8")
            if text in existing:
                total += 1
                continue

            # Add text before the closing of the post (before the last empty line)
            # Insert after the last image line
            lines = existing.splitlines(keepends=True)
            insert_idx = len(lines)
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i].strip()
                if line.startswith("![") or line.startswith("**Camera") or line.startswith("**Lens") or line.startswith("**Settings"):
                    insert_idx = i + 1
                    break

            lines.insert(insert_idx, f"\n{text}\n")
            post_file.write_text("".join(lines), encoding="utf-8")
            print(f"  [{date_prefix}] {title[:50]} — added text: {text[:60]}...")
            patched += 1
            total += 1

        total_posts = int(feed_data.get("feed", {}).get("openSearch$totalResults", {}).get("$t", "0"))
        start += BATCH_SIZE
        if start > total_posts:
            break

    print(f"\nPatched {patched} posts with text content (of {total} checked)")


if __name__ == "__main__":
    main()
