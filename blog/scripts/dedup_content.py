#!/usr/bin/env python3
"""Find and remove duplicate posts by comparing content.

Catches duplicates that have different filenames but identical images
or identical original URLs (e.g. from Blogger feed pagination overlap).
"""

import re
from pathlib import Path

BLOG_DIR = Path(__file__).parent
PHOTO_DIR = BLOG_DIR / "files" / "photoblog"


def get_original_url(path):
    """Extract the 'Originally published on' URL from a post."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r'Originally published on.*?\((https?://[^)]+)\)', text)
    return m.group(1) if m else None


def get_images(path):
    """Extract image filenames referenced in a post."""
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r'!\[.*?\]\(files/photoblog/([^)]+)\)', text))


def main():
    photo_posts = sorted(BLOG_DIR.glob("*_photo.md"))
    print(f"Checking {len(photo_posts)} photoblog posts for duplicates...\n")

    # Group by original URL
    by_url = {}
    no_url = []
    for p in photo_posts:
        url = get_original_url(p)
        if url:
            by_url.setdefault(url, []).append(p)
        else:
            no_url.append(p)

    to_delete_posts = []
    to_delete_images = []

    # Find URL-based duplicates
    for url, posts in sorted(by_url.items()):
        if len(posts) <= 1:
            continue
        # Keep the one with the shortest filename (original), delete the rest
        posts.sort(key=lambda p: (len(p.name), p.name))
        keeper = posts[0]
        for dup in posts[1:]:
            print(f"  DUP: {dup.name} (same URL as {keeper.name})")
            to_delete_posts.append(dup)
            for img in get_images(dup):
                img_path = PHOTO_DIR / img
                # Only delete if not referenced by the keeper
                if img not in get_images(keeper) and img_path.exists():
                    to_delete_images.append(img_path)

    # Also check no-URL posts for image-based duplicates
    # (same images = same content)
    by_images = {}
    for p in no_url:
        imgs = frozenset(get_images(p))
        if imgs:
            by_images.setdefault(imgs, []).append(p)

    for imgs, posts in by_images.items():
        if len(posts) <= 1:
            continue
        posts.sort(key=lambda p: (len(p.name), p.name))
        keeper = posts[0]
        for dup in posts[1:]:
            print(f"  DUP: {dup.name} (same images as {keeper.name})")
            to_delete_posts.append(dup)

    if not to_delete_posts:
        print("No duplicates found.")
        return

    print(f"\nFound {len(to_delete_posts)} duplicate posts, {len(to_delete_images)} orphaned images")
    print("Deleting...")

    for p in to_delete_posts:
        p.unlink()
    for p in to_delete_images:
        if p.exists():
            p.unlink()

    print(f"Deleted {len(to_delete_posts)} posts and {len(to_delete_images)} images")


if __name__ == "__main__":
    main()
