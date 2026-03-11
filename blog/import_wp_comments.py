#!/usr/bin/env python3
"""Import WordPress comments from XML export into existing blog markdown files.

Appends approved comments as a static "Old Comments" section at the bottom
of each affected post's markdown file.

Usage: python import_wp_comments.py k1monfared.WordPress.2026-03-11.xml
"""

import html
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

BLOG_DIR = Path(__file__).parent

NAMESPACES = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wp": "http://wordpress.org/export/1.2/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
}


def format_date(date_str):
    """Format '2014-05-02 08:11:26' as 'May 2, 2014'."""
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%B %-d, %Y")


def clean_comment_content(text):
    """Clean comment content: decode entities, strip HTML, normalize whitespace."""
    if not text:
        return ""
    s = html.unescape(text)
    # Remove HTML tags (some comments have <a> tags)
    s = re.sub(r"<[^>]+>", "", s)
    # Normalize whitespace but preserve paragraph breaks
    s = s.strip()
    return s


def build_comment_markdown(comments, prefix="> "):
    """Build markdown for a list of comments with nested replies."""
    lines = []
    for comment in comments:
        author = html.unescape(comment["author"])
        date = format_date(comment["date"])
        content = clean_comment_content(comment["content"])

        # Split content into lines for blockquote formatting
        content_lines = content.split("\n")

        lines.append(f"{prefix}**{author}** — {date}")
        lines.append(f"{prefix}")
        for cl in content_lines:
            cl = cl.strip()
            if cl:
                lines.append(f"{prefix}{cl}")
            else:
                lines.append(f"{prefix}")

        # Add nested replies
        if comment["replies"]:
            lines.append(f"{prefix}")
            reply_prefix = prefix + "> "
            reply_lines = build_comment_markdown(comment["replies"], prefix=reply_prefix)
            lines.extend(reply_lines)

        lines.append("")  # blank line between top-level comments

    return lines


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_wp_comments.py <wordpress-export.xml>")
        sys.exit(1)

    xml_path = sys.argv[1]
    tree = ET.parse(xml_path)
    root = tree.getroot()
    channel = root.find("channel")

    posts_with_comments = 0
    comments_added = 0

    for item in channel.findall("item"):
        post_type = item.find("wp:post_type", NAMESPACES)
        if post_type is None or post_type.text != "post":
            continue

        status = item.find("wp:status", NAMESPACES)
        if status is None or status.text not in ("publish", "draft", "private"):
            continue

        # Collect approved comments
        wp_comments = item.findall("wp:comment", NAMESPACES)
        approved = []
        for c in wp_comments:
            if c.find("wp:comment_approved", NAMESPACES).text != "1":
                continue
            approved.append({
                "id": c.find("wp:comment_id", NAMESPACES).text,
                "author": c.find("wp:comment_author", NAMESPACES).text or "Anonymous",
                "date": c.find("wp:comment_date", NAMESPACES).text,
                "content": c.find("wp:comment_content", NAMESPACES).text or "",
                "parent": c.find("wp:comment_parent", NAMESPACES).text,
            })

        if not approved:
            continue

        # Find the local markdown file
        date_el = item.find("wp:post_date", NAMESPACES)
        date_str = date_el.text if date_el is not None and date_el.text else ""
        if not date_str or date_str.startswith("0000"):
            continue

        post_name_el = item.find("wp:post_name", NAMESPACES)
        slug = post_name_el.text if post_name_el is not None and post_name_el.text else ""
        if not slug:
            title_el = item.find("title")
            title = title_el.text if title_el is not None and title_el.text else ""
            s = title.lower()
            s = re.sub(r"[^\w\s-]", "", s)
            s = re.sub(r"[\s]+", "_", s).strip("_")
            slug = s[:60].rstrip("_")

        date_prefix = date_str.split(" ")[0].replace("-", "")
        file_slug = slug.replace("-", "_")
        filepath = BLOG_DIR / f"{date_prefix}_{file_slug}.md"

        if not filepath.exists():
            print(f"  SKIP (file not found): {filepath.name}")
            continue

        # Check idempotency
        existing = filepath.read_text(encoding="utf-8")
        if "## Old Comments" in existing:
            print(f"  SKIP (already has comments): {filepath.name}")
            continue

        # Build comment tree
        by_id = {c["id"]: c for c in approved}
        for c in approved:
            c["replies"] = []
        top_level = []
        for c in approved:
            if c["parent"] == "0" or c["parent"] not in by_id:
                top_level.append(c)
            else:
                by_id[c["parent"]]["replies"].append(c)

        # Sort by date
        top_level.sort(key=lambda c: c["date"])
        for c in approved:
            c["replies"].sort(key=lambda r: r["date"])

        # Build markdown
        comment_lines = build_comment_markdown(top_level)
        section = "\n---\n\n## Old Comments\n\n" + "\n".join(comment_lines)

        # Append to file
        # Ensure file ends with single newline before appending
        content = existing.rstrip("\n") + "\n" + section

        filepath.write_text(content, encoding="utf-8")
        n = len(approved)
        posts_with_comments += 1
        comments_added += n
        print(f"  ADDED {n} comment(s): {filepath.name}")

    print(f"\nDone: {comments_added} comments added to {posts_with_comments} posts")


if __name__ == "__main__":
    main()
