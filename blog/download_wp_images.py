#!/usr/bin/env python3
"""Download WordPress images and update markdown references.

Finds all k1monfared.wordpress.com image URLs in blog posts,
downloads them to files/YYYYMMDD/ directories, and rewrites
the markdown to use local paths.
"""

import os
import re
import urllib.request
import urllib.parse
from pathlib import Path

BLOG_DIR = Path(__file__).parent
WP_URL_RE = re.compile(
    r'https?://k1monfared\.wordpress\.com/wp-content/uploads/(\d{4})/(\d{2})/([^\s)"\]?]+?)(\?[^\s)"\]]*)?(?=[)\s"\]])'
)


def download_image(url, dest):
    """Download a URL to a local file path."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"    FAILED: {url} -> {e}")
        return False


def process_post(filepath):
    """Process a single markdown file: download images, rewrite paths."""
    text = filepath.read_text(encoding="utf-8")
    matches = list(WP_URL_RE.finditer(text))
    if not matches:
        return 0

    # Determine the post date prefix from filename
    stem = filepath.stem
    date_match = re.match(r"^(\d{8})_", stem)
    if not date_match:
        return 0
    date_prefix = date_match.group(1)

    downloaded = 0
    new_text = text

    # Deduplicate URLs
    seen = {}
    for m in matches:
        year, month, filename = m.group(1), m.group(2), m.group(3)
        # Decode URL-encoded filenames
        filename_decoded = urllib.parse.unquote(filename)
        full_url = f"https://k1monfared.wordpress.com/wp-content/uploads/{year}/{month}/{filename}"
        original_match = m.group(0)

        if full_url in seen:
            local_path = seen[full_url]
        else:
            local_path = f"files/{date_prefix}/{filename_decoded}"
            dest = BLOG_DIR / local_path

            if download_image(full_url, dest):
                downloaded += 1
                print(f"    {filename_decoded}")
            else:
                continue
            seen[full_url] = local_path

        # Replace the full WordPress URL (with optional query params) with local path
        new_text = new_text.replace(original_match, local_path)

    if new_text != text:
        filepath.write_text(new_text, encoding="utf-8")

    return downloaded


def main():
    md_files = sorted(BLOG_DIR.glob("*.md"))
    total = 0
    for f in md_files:
        text = f.read_text(encoding="utf-8")
        if "k1monfared.wordpress.com/wp-content/uploads/" not in text:
            continue
        print(f"  {f.name}:")
        count = process_post(f)
        total += count

    print(f"\nDone: {total} images downloaded")


if __name__ == "__main__":
    main()
