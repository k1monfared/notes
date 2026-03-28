#!/usr/bin/env python3
"""Find and remove duplicate photoblog posts.

Posts like `20140518_special_blessings_photo.md` and
`20140518_special_blessings_2_photo.md` are duplicates — the `_2_` suffix
was added by the collision handler. This script keeps the original (no number)
and deletes the numbered duplicates, along with their duplicate images.
"""

import re
from pathlib import Path

BLOG_DIR = Path(__file__).parent
PHOTO_DIR = BLOG_DIR / "files" / "photoblog"


def get_post_content(path):
    """Read post and return the image filenames and text content (minus frontmatter)."""
    text = path.read_text(encoding="utf-8")
    # Strip frontmatter
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2]
    # Extract image references
    images = re.findall(r'!\[.*?\]\(files/photoblog/([^)]+)\)', text)
    # Get text without images and whitespace for comparison
    body = re.sub(r'!\[.*?\]\([^)]+\)', '', text).strip()
    body = re.sub(r'\s+', ' ', body)
    return set(images), body


def main():
    # Find all photoblog posts
    photo_posts = sorted(BLOG_DIR.glob("*_photo.md"))

    # Group by date prefix (YYYYMMDD) + base slug
    # Pattern: YYYYMMDD_slug_photo.md vs YYYYMMDD_slug_N_photo.md
    groups = {}
    numbered_re = re.compile(r'^(\d{8}_.*?)_(\d+)_photo\.md$')
    base_re = re.compile(r'^(\d{8}_.*?)_photo\.md$')

    for p in photo_posts:
        name = p.name
        m_num = numbered_re.match(name)
        m_base = base_re.match(name)

        if m_num:
            key = m_num.group(1)
            num = int(m_num.group(2))
            if key not in groups:
                groups[key] = {"base": None, "numbered": []}
            groups[key]["numbered"].append((num, p))
        elif m_base:
            key = m_base.group(1)
            if key not in groups:
                groups[key] = {"base": None, "numbered": []}
            groups[key]["base"] = p

    # Find duplicates
    to_delete_posts = []
    to_delete_images = []
    kept = 0

    for key, group in sorted(groups.items()):
        if not group["base"] or not group["numbered"]:
            continue

        base_path = group["base"]
        base_images, base_body = get_post_content(base_path)

        for num, dup_path in sorted(group["numbered"]):
            dup_images, dup_body = get_post_content(dup_path)

            # Check if content is similar (same original link or same body)
            is_dup = False

            # Same images referenced (different filenames but same content pattern)
            if base_body and dup_body:
                # Compare without the image refs and minor differences
                base_clean = re.sub(r'files/photoblog/[^\s)]+', '', base_body)
                dup_clean = re.sub(r'files/photoblog/[^\s)]+', '', dup_body)
                if base_clean == dup_clean:
                    is_dup = True

            # Same original link
            base_text = base_path.read_text(encoding="utf-8")
            dup_text = dup_path.read_text(encoding="utf-8")
            base_links = re.findall(r'Originally published on.*?\((https?://[^)]+)\)', base_text)
            dup_links = re.findall(r'Originally published on.*?\((https?://[^)]+)\)', dup_text)
            if base_links and dup_links and base_links[0] == dup_links[0]:
                is_dup = True

            if is_dup:
                to_delete_posts.append(dup_path)
                # Also delete the duplicate images
                for img in dup_images:
                    img_path = PHOTO_DIR / img
                    if img_path.exists():
                        to_delete_images.append(img_path)
                print(f"  DUP: {dup_path.name} (duplicate of {base_path.name})")
                kept += 1

    if not to_delete_posts:
        print("No duplicates found.")
        return

    print(f"\nFound {len(to_delete_posts)} duplicate posts and {len(to_delete_images)} duplicate images")
    print(f"\nDeleting...")

    for p in to_delete_posts:
        p.unlink()
    for p in to_delete_images:
        p.unlink()

    print(f"Deleted {len(to_delete_posts)} posts and {len(to_delete_images)} images")


if __name__ == "__main__":
    main()
