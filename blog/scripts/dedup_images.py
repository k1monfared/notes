#!/usr/bin/env python3
"""Find duplicate photoblog posts by comparing actual image file hashes.

If two posts reference images with identical content (same MD5), the
second post is considered a duplicate and removed.
"""

import hashlib
import re
from pathlib import Path

BLOG_DIR = Path(__file__).parent.parent
PHOTO_DIR = BLOG_DIR / "files" / "photoblog"


def file_hash(path):
    """Get MD5 hash of a file."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_images(post_path):
    """Extract image filenames from a post."""
    text = post_path.read_text(encoding="utf-8")
    return re.findall(r'!\[.*?\]\(files/photoblog/([^)]+)\)', text)


def main():
    photo_posts = sorted(BLOG_DIR.glob("*_photo.md"))
    print(f"Checking {len(photo_posts)} photoblog posts for image duplicates...\n")

    # Build hash -> first post mapping
    hash_to_post = {}  # image_hash -> (post_path, image_name)
    to_delete_posts = []
    to_delete_images = []

    for p in photo_posts:
        images = get_images(p)
        if not images:
            continue

        # Hash the first image (main photo)
        img_path = PHOTO_DIR / images[0]
        if not img_path.exists():
            continue

        h = file_hash(img_path)

        if h in hash_to_post:
            orig_post, orig_img = hash_to_post[h]
            print(f"  DUP: {p.name} (same image as {orig_post.name})")
            to_delete_posts.append(p)
            # Delete images unique to this post
            for img in images:
                img_p = PHOTO_DIR / img
                if img_p.exists() and img not in get_images(orig_post):
                    to_delete_images.append(img_p)
        else:
            hash_to_post[h] = (p, images[0])

    if not to_delete_posts:
        print("No image-based duplicates found.")
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
