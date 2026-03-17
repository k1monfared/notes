#!/usr/bin/env python3
"""Add tags from WordPress XML export to existing blog post frontmatter.

Usage: python add_tags_from_wp.py /path/to/export.xml [--dry-run]
"""

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

BLOG_DIR = Path(__file__).parent.parent

NAMESPACES = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wp": "http://wordpress.org/export/1.2/",
}


def parse_tags_from_export(xml_path):
    """Parse WordPress XML and return a map of (date_prefix, slug) -> [tags]."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    channel = root.find("channel")

    post_tags = {}
    for item in channel.findall("item"):
        post_type = item.find("wp:post_type", NAMESPACES)
        if post_type is None or post_type.text != "post":
            continue

        status = item.find("wp:status", NAMESPACES)
        if status is None or status.text not in ("publish", "draft", "private"):
            continue

        # Get date prefix
        date_el = item.find("wp:post_date", NAMESPACES)
        date_str = date_el.text if date_el is not None and date_el.text else ""
        if not date_str or date_str.startswith("0000"):
            continue
        date_prefix = date_str.split(" ")[0].replace("-", "")  # YYYYMMDD

        # Get slug
        post_name_el = item.find("wp:post_name", NAMESPACES)
        slug = post_name_el.text if post_name_el is not None and post_name_el.text else ""
        if not slug:
            continue
        slug = slug.replace("-", "_")

        # Get tags
        tags = []
        for cat in item.findall("category"):
            if cat.get("domain") == "post_tag":
                tag_name = cat.text
                if tag_name:
                    tags.append(tag_name.strip().lower())

        if tags:
            filename_stem = f"{date_prefix}_{slug}"
            post_tags[filename_stem] = sorted(set(tags))

    return post_tags


def add_frontmatter_tags(filepath, tags):
    """Add tags to a post's frontmatter. Returns True if modified."""
    text = filepath.read_text(encoding="utf-8")

    tags_line = f"tags: {', '.join(tags)}"

    if text.startswith("---"):
        # Has existing frontmatter — add tags if not already present
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            if re.search(r"^tags:", frontmatter, re.MULTILINE):
                return False  # already has tags
            new_frontmatter = f"{frontmatter}\n{tags_line}"
            text = f"---\n{new_frontmatter}\n---{parts[2]}"
        else:
            return False
    else:
        # No frontmatter — add one
        text = f"---\n{tags_line}\n---\n\n{text}"

    filepath.write_text(text, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="Add WordPress tags to blog posts")
    parser.add_argument("xml_file", help="Path to WordPress XML export file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed")
    args = parser.parse_args()

    post_tags = parse_tags_from_export(args.xml_file)
    print(f"Found tags for {len(post_tags)} posts in XML")

    md_files = sorted(BLOG_DIR.glob("*.md"))
    updated = 0
    no_tags = 0

    for f in md_files:
        stem = f.stem
        if stem in post_tags:
            tags = post_tags[stem]
            if args.dry_run:
                print(f"  WOULD TAG: {f.name} -> {', '.join(tags)}")
                updated += 1
            else:
                if add_frontmatter_tags(f, tags):
                    print(f"  TAGGED: {f.name} -> {', '.join(tags)}")
                    updated += 1
                else:
                    print(f"  SKIP (already tagged): {f.name}")
        else:
            no_tags += 1

    print(f"\nDone: {updated} tagged, {no_tags} without tags in XML")


if __name__ == "__main__":
    main()
