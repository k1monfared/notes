#!/usr/bin/env python3
"""Import photo blog posts from k1-photo.blogspot.com into the local blog.

Fetches all posts via the Blogger JSON feed API, downloads images,
creates markdown post files, and extracts comments.

Usage:
  python import_photoblog.py              # Full import
  python import_photoblog.py --dry-run    # Preview without downloading
  python import_photoblog.py --max 5      # Import only first 5 posts
"""

import argparse
import html
import json
import os
import re
import time
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

BLOG_DIR = Path(__file__).parent
PHOTO_DIR = BLOG_DIR / "files" / "photoblog"
COMMENTS_DIR = BLOG_DIR / "comments"
FEED_BASE = "https://k1-photo.blogspot.com/feeds/posts/default"
BATCH_SIZE = 50
IMAGE_DELAY = 0.1
TAG = "photoblog"

# Titles that are effectively untitled
EMPTY_TITLES = {"", ".", "-", "...", "—"}


def parse_args():
    parser = argparse.ArgumentParser(description="Import photoblog from Blogger")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Preview without downloading")
    parser.add_argument("--max", type=int, default=0, help="Max posts to process (0=all)")
    parser.add_argument("--start", type=int, default=1, help="Start index (for resuming)")
    return parser.parse_args()


def fetch_feed_page(start_index):
    """Fetch one page of the Blogger JSON feed."""
    url = f"{FEED_BASE}?alt=json&max-results={BATCH_SIZE}&start-index={start_index}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data


def get_total_posts(feed_data):
    """Get total post count from feed."""
    return int(feed_data.get("feed", {}).get("openSearch$totalResults", {}).get("$t", "0"))


def extract_images(content_html):
    """Extract all image URLs from post HTML content."""
    urls = []
    # Match img src attributes
    for m in re.finditer(r'<img[^>]*\bsrc="([^"]+)"', content_html, re.IGNORECASE):
        url = m.group(1)
        if "blogger" in url or "blogspot" in url or "googleusercontent" in url or "ggpht" in url:
            urls.append(url)

    # Also check <a href="..."> wrapping images (higher res)
    for m in re.finditer(r'<a[^>]*\bhref="([^"]+)"[^>]*>\s*<img', content_html, re.IGNORECASE):
        url = m.group(1)
        if ("blogger" in url or "blogspot" in url or "googleusercontent" in url or "ggpht" in url) and url not in urls:
            urls.insert(0, url)  # prefer the <a> href (usually higher res)

    # Deduplicate while preserving order, prefer full-res
    seen = set()
    unique = []
    for url in urls:
        # Normalize: get the base path without size parameter
        base = re.sub(r'/s\d+/', '/s0/', url)
        if base not in seen:
            seen.add(base)
            unique.append(base)
    return unique


def slugify(title):
    """Create a filename-safe slug."""
    slug = title.lower().strip()
    # Remove non-alphanumeric (keep unicode letters, digits, spaces, hyphens)
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "_", slug).strip("_")
    return slug[:50] if slug else "photo"


def is_untitled(title):
    """Check if a title is effectively empty."""
    return title.strip() in EMPTY_TITLES


def download_image(url, dest_path):
    """Download an image to the given path."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest_path.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"    FAIL: {e}")
        return False


def get_post_id(entry):
    """Extract numeric post ID from feed entry."""
    id_str = entry.get("id", {}).get("$t", "")
    m = re.search(r"post-(\d+)", id_str)
    return m.group(1) if m else None


def fetch_comments(post_id):
    """Fetch comments for a post via Blogger feed."""
    url = f"https://k1-photo.blogspot.com/feeds/{post_id}/comments/default?alt=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        entries = data.get("feed", {}).get("entry", [])
        comments = []
        for e in entries:
            name = e.get("author", [{}])[0].get("name", {}).get("$t", "Anonymous")
            date_str = e.get("published", {}).get("$t", "")
            # Parse to just date
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                date_val = dt.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                date_val = date_str[:10] if len(date_str) >= 10 else ""
            # Content is HTML, convert to plain text
            content_html = e.get("content", {}).get("$t", "")
            content = html.unescape(re.sub(r"<[^>]+>", "", content_html)).strip()
            if content:
                comments.append({"name": name, "date": date_val, "comment": content})
        return comments
    except Exception:
        return []


def save_comments(url_slug, comments, dry_run=False):
    """Save comments as YAML files."""
    if not comments:
        return 0
    comment_dir = COMMENTS_DIR / url_slug
    if not dry_run:
        comment_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    for i, c in enumerate(comments, 1):
        filepath = comment_dir / f"{i:03d}.yml"
        if filepath.exists():
            continue
        if not dry_run:
            # Simple YAML output (no dependency needed)
            lines = [f"name: {c['name']}", f"date: {c['date']}"]
            text = c["comment"]
            if "\n" in text:
                lines.append("comment: |-")
                for line in text.splitlines():
                    lines.append(f"  {line}")
            else:
                # Escape colons in single-line comments
                lines.append(f"comment: {text}")
            filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
        saved += 1
    return saved


def process_post(entry, dry_run=False):
    """Process a single blog post entry. Returns (saved, images_downloaded, comments_saved)."""
    title = entry.get("title", {}).get("$t", "").strip()
    pub = entry.get("published", {}).get("$t", "")
    content_html = entry.get("content", {}).get("$t", "")
    post_id = get_post_id(entry)

    # Parse date
    try:
        dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        dt = datetime.now()

    date_prefix = dt.strftime("%Y%m%d")
    date_dash = dt.strftime("%Y-%m-%d")

    # Determine slug
    if is_untitled(title):
        slug = "photo"
    else:
        slug = slugify(title)

    # Post filename — append incrementing number for collisions
    post_filename = f"{date_prefix}_{slug}_photo.md"
    post_path = BLOG_DIR / post_filename

    if post_path.exists():
        # Find next available number
        n = 2
        while True:
            post_filename = f"{date_prefix}_{slug}_{n}_photo.md"
            post_path = BLOG_DIR / post_filename
            if not post_path.exists():
                break
            n += 1
        # Also update slug for image naming
        slug = f"{slug}_{n}"

    # Display title
    if is_untitled(title):
        display_title = f"{date_dash} - photo"
    else:
        display_title = f"{title} - photo"

    # Extract images
    image_urls = extract_images(content_html)
    if not image_urls:
        print(f"    No images found, skipping")
        return 0, 0, 0

    # Download images
    image_files = []
    for i, url in enumerate(image_urls, 1):
        # Determine extension from URL
        ext = ".jpg"
        if ".png" in url.lower():
            ext = ".png"
        elif ".gif" in url.lower():
            ext = ".gif"

        img_name = f"{date_dash}_{slug}_{i:02d}{ext}"
        img_path = PHOTO_DIR / img_name

        if not img_path.exists() and not dry_run:
            if download_image(url, img_path):
                time.sleep(IMAGE_DELAY)
            else:
                continue

        image_files.append(img_name)

    if not image_files and not dry_run:
        return 0, 0, 0

    # Get post link
    post_link = ""
    for link in entry.get("link", []):
        if link.get("rel") == "alternate":
            post_link = link.get("href", "")
            break

    # URL slug for comments directory
    url_slug = f"{date_prefix}-{slug.replace('_', '-')}-photo"

    # Fetch and save comments
    comments_saved = 0
    if post_id:
        comment_count = int(entry.get("thr$total", {}).get("$t", "0"))
        if comment_count > 0:
            comments = fetch_comments(post_id)
            if comments:
                comments_saved = save_comments(url_slug, comments, dry_run)
                if comments_saved:
                    print(f"    {comments_saved} comment(s)")

    # Generate markdown
    if not dry_run:
        thumb = f"files/photoblog/{image_files[0]}" if image_files else ""
        lines = [
            "---",
            f"tags: {TAG}",
            f"thumbnail: {thumb}",
            "---",
            "",
            f"# {display_title}",
            "",
        ]
        for img in image_files:
            lines.append(f"![{title}](files/photoblog/{img})")
            lines.append("")

        if post_link:
            lines.append(f"*Originally published on [Daily Photos]({post_link})*")
            lines.append("")

        post_path.write_text("\n".join(lines), encoding="utf-8")

    return 1, len(image_files), comments_saved


def main():
    args = parse_args()

    PHOTO_DIR.mkdir(parents=True, exist_ok=True)

    # Fetch first page to get total
    print("Fetching feed...")
    first_page = fetch_feed_page(args.start)
    total = get_total_posts(first_page)
    print(f"Total posts: {total}")

    if args.dry_run:
        print("(Dry run — no files will be written)\n")

    posts_saved = 0
    images_downloaded = 0
    comments_saved = 0
    processed = 0

    start = args.start
    while start <= total:
        if args.max and processed >= args.max:
            break

        try:
            if start == args.start:
                feed_data = first_page
            else:
                feed_data = fetch_feed_page(start)
        except Exception as e:
            print(f"Feed error at index {start}: {e}")
            break

        entries = feed_data.get("feed", {}).get("entry", [])
        if not entries:
            break

        for entry in entries:
            if args.max and processed >= args.max:
                break

            processed += 1
            title = entry.get("title", {}).get("$t", "").strip()
            pub = entry.get("published", {}).get("$t", "")[:10]
            n_images = len(extract_images(entry.get("content", {}).get("$t", "")))

            print(f"[{processed}/{total}] {pub} — {title or '(untitled)'} ({n_images} img)", end="")

            saved, imgs, cmts = process_post(entry, args.dry_run)
            if saved:
                posts_saved += saved
                images_downloaded += imgs
                comments_saved += cmts
                print(f" ✓")
            else:
                print(f" skip")

        start += BATCH_SIZE

    print(f"\n{'=' * 50}")
    print(f"Posts saved:      {posts_saved}")
    print(f"Images downloaded: {images_downloaded}")
    print(f"Comments saved:   {comments_saved}")
    print(f"Total processed:  {processed}")

    if args.dry_run:
        print("\nDry run complete. Run without --dry-run to import.")


if __name__ == "__main__":
    main()
