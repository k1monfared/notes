#!/usr/bin/env python3
"""Import WordPress XML export into blog markdown files.

Usage: python import_wordpress.py /path/to/export.xml [--drafts]
"""

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BLOG_DIR = Path(__file__).parent

NAMESPACES = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wp": "http://wordpress.org/export/1.2/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
}


def html_to_markdown(text):
    """Convert WordPress HTML content to markdown."""
    if not text:
        return ""

    s = text

    # Normalize line endings
    s = s.replace("\r\n", "\n")

    # WordPress block editor comments
    s = re.sub(r"<!-- /?wp:\w+[^>]*?-->", "", s)

    # WordPress shortcodes — remove them
    s = re.sub(r"\[/?caption[^\]]*\]", "", s)
    s = re.sub(r"\[/?gallery[^\]]*\]", "", s)
    s = re.sub(r"\[googleapps[^\]]*/?]", "", s)
    s = re.sub(r"\[/?wordpress[^\]]*\]", "", s)

    # WordPress latex shortcodes: $latex expression$ -> $expression$
    s = re.sub(r"\$latex\s+(.+?)\$", r"$\1$", s)

    # Images: <img src="..." alt="..." /> -> ![alt](src)
    def img_replace(m):
        attrs = m.group(0)
        src = re.search(r'src="([^"]*)"', attrs)
        alt = re.search(r'alt="([^"]*)"', attrs)
        if src:
            alt_text = alt.group(1) if alt else ""
            return f"![{alt_text}]({src.group(1)})"
        return ""
    s = re.sub(r"<img\s[^>]*?>", img_replace, s)

    # Links: <a href="...">text</a> -> [text](href)
    s = re.sub(r'<a\s[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", s, flags=re.DOTALL)

    # Bold
    s = re.sub(r"<strong>(.*?)</strong>", r"**\1**", s, flags=re.DOTALL)
    s = re.sub(r"<b>(.*?)</b>", r"**\1**", s, flags=re.DOTALL)

    # Italic
    s = re.sub(r"<em>(.*?)</em>", r"*\1*", s, flags=re.DOTALL)
    s = re.sub(r"<i>(.*?)</i>", r"*\1*", s, flags=re.DOTALL)

    # Strikethrough
    s = re.sub(r"<del>(.*?)</del>", r"~~\1~~", s, flags=re.DOTALL)
    s = re.sub(r"<s>(.*?)</s>", r"~~\1~~", s, flags=re.DOTALL)

    # Code
    s = re.sub(r"<code>(.*?)</code>", r"`\1`", s, flags=re.DOTALL)
    s = re.sub(r"<pre>(.*?)</pre>", r"```\n\1\n```", s, flags=re.DOTALL)

    # Blockquote
    def blockquote_replace(m):
        inner = m.group(1).strip()
        inner = re.sub(r"</?p>", "", inner)
        lines = inner.split("\n")
        return "\n".join(f"> {line}" for line in lines)
    s = re.sub(r"<blockquote>(.*?)</blockquote>", blockquote_replace, s, flags=re.DOTALL)

    # Headings
    for i in range(6, 0, -1):
        s = re.sub(rf"<h{i}[^>]*>(.*?)</h{i}>", rf"{'#' * i} \1", s, flags=re.DOTALL)

    # Lists — handle nested
    s = re.sub(r"<ul[^>]*>", "", s)
    s = re.sub(r"</ul>", "", s)
    s = re.sub(r"<ol[^>]*>", "", s)
    s = re.sub(r"</ol>", "", s)
    s = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1", s, flags=re.DOTALL)

    # Horizontal rule
    s = re.sub(r"<hr\s*/?>", "\n---\n", s)

    # Paragraphs
    s = re.sub(r"<p[^>]*>", "\n", s)
    s = re.sub(r"</p>", "\n", s)

    # Line breaks
    s = re.sub(r"<br\s*/?>", "\n", s)

    # Remove remaining HTML tags
    s = re.sub(r"</?(?:div|span|figure|figcaption|iframe|table|tr|td|th|thead|tbody)[^>]*>", "", s)

    # Decode HTML entities
    s = html.unescape(s)

    # Clean up excessive blank lines
    s = re.sub(r"\n{3,}", "\n\n", s)

    return s.strip()


def slugify(title):
    """Create a slug from a title."""
    s = title.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s]+", "_", s).strip("_")
    return s[:60].rstrip("_")


def parse_export(xml_path, include_drafts=False):
    """Parse WordPress XML export and return list of posts."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    channel = root.find("channel")

    posts = []
    for item in channel.findall("item"):
        post_type = item.find("wp:post_type", NAMESPACES)
        if post_type is None or post_type.text != "post":
            continue

        status = item.find("wp:status", NAMESPACES)
        if status is None:
            continue
        status_text = status.text

        if status_text == "draft" and not include_drafts:
            continue
        if status_text not in ("publish", "draft", "private"):
            continue

        title_el = item.find("title")
        title = title_el.text if title_el is not None and title_el.text else ""

        content_el = item.find("content:encoded", NAMESPACES)
        content = content_el.text if content_el is not None and content_el.text else ""

        date_el = item.find("wp:post_date", NAMESPACES)
        date_str = date_el.text if date_el is not None and date_el.text else ""

        post_name_el = item.find("wp:post_name", NAMESPACES)
        post_name = post_name_el.text if post_name_el is not None and post_name_el.text else ""

        # Skip empty posts
        if not content.strip():
            continue
        if not title.strip():
            continue

        posts.append({
            "title": title.strip(),
            "content": content,
            "date": date_str,
            "slug": post_name,
            "status": status_text,
        })

    return posts


def main():
    parser = argparse.ArgumentParser(description="Import WordPress XML export")
    parser.add_argument("xml_file", help="Path to WordPress XML export file")
    parser.add_argument("--drafts", action="store_true", help="Also import drafts (as .draft files)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be created without writing")
    args = parser.parse_args()

    posts = parse_export(args.xml_file, include_drafts=args.drafts)

    print(f"Found {len(posts)} posts to import")

    created = 0
    skipped = 0
    for post in posts:
        # Parse date
        if not post["date"] or post["date"].startswith("0000"):
            print(f"  SKIP (no date): {post['title']}")
            skipped += 1
            continue

        date_parts = post["date"].split(" ")[0].split("-")
        date_prefix = "".join(date_parts)  # YYYYMMDD

        # Build slug
        slug = post["slug"] if post["slug"] else slugify(post["title"])
        slug = slug.replace("-", "_")

        # Extension based on status
        ext = ".draft" if post["status"] == "draft" else ".md"

        filename = f"{date_prefix}_{slug}{ext}"
        filepath = BLOG_DIR / filename

        # Check for existing file
        if filepath.exists():
            print(f"  SKIP (exists): {filename}")
            skipped += 1
            continue

        # Convert content
        markdown_content = html_to_markdown(post["content"])
        full_content = f"# {post['title']}\n\n{markdown_content}\n"

        if args.dry_run:
            print(f"  WOULD CREATE: {filename} ({len(full_content)} chars)")
        else:
            filepath.write_text(full_content, encoding="utf-8")
            print(f"  CREATED: {filename}")
        created += 1

    print(f"\nDone: {created} created, {skipped} skipped")


if __name__ == "__main__":
    main()
