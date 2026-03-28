#!/usr/bin/env python3
"""Import original photos from /home/k1/public/blogs/photoblog/originals/.

Reads EXIF data for date/time and camera settings, copies photos to
blog/files/photoblog/ with proper naming, and creates blog post files
with camera info as content.
"""

import shutil
from collections import defaultdict
from datetime import datetime
from fractions import Fraction
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS

SOURCE_DIR = Path("/home/k1/public/blogs/photoblog/originals")
BLOG_DIR = Path(__file__).parent
PHOTO_DIR = BLOG_DIR / "files" / "photoblog"
TAG = "photoblog"


def get_exif(filepath):
    """Extract relevant EXIF data from a photo."""
    try:
        img = Image.open(filepath)
        exif_raw = img._getexif()
        if not exif_raw:
            return {}
        exif = {}
        for tag_id, val in exif_raw.items():
            tag = TAGS.get(tag_id, tag_id)
            exif[tag] = val
        return exif
    except Exception:
        return {}


def to_float(val):
    """Convert EXIF value (IFDRational, tuple, etc.) to float."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        pass
    if isinstance(val, tuple) and len(val) == 2:
        return val[0] / val[1] if val[1] else float(val[0])
    return None


def format_exposure(val):
    """Format exposure time as a fraction like 1/320."""
    val = to_float(val)
    if val is None or val == 0:
        return None
    if val >= 1:
        return f"{val:.1f}s"
    frac = Fraction(val).limit_denominator(10000)
    return f"{frac.numerator}/{frac.denominator}s"


def format_focal(val):
    """Format focal length."""
    val = to_float(val)
    if val is None:
        return None
    return f"{val:.0f}mm" if val == int(val) else f"{val:.1f}mm"


def format_aperture(val):
    """Format f-number."""
    val = to_float(val)
    if val is None:
        return None
    return f"f/{val:.1f}"


def build_camera_info(exif):
    """Build camera settings text from EXIF data."""
    lines = []

    camera = exif.get("Model", "")
    make = exif.get("Make", "")
    if camera:
        # Remove redundant make from model (e.g. "Canon Canon EOS M50")
        if make and camera.startswith(make):
            camera_display = camera
        elif make:
            camera_display = f"{make} {camera}"
        else:
            camera_display = camera
        lines.append(f"**Camera:** {camera_display}")

    lens = exif.get("LensModel")
    if lens:
        lines.append(f"**Lens:** {lens}")

    settings = []
    focal = format_focal(exif.get("FocalLength"))
    if focal:
        settings.append(focal)

    aperture = format_aperture(exif.get("FNumber"))
    if aperture:
        settings.append(aperture)

    shutter = format_exposure(exif.get("ExposureTime"))
    if shutter:
        settings.append(shutter)

    iso = exif.get("ISOSpeedRatings")
    if iso:
        settings.append(f"ISO {iso}")

    if settings:
        lines.append(f"**Settings:** {' | '.join(settings)}")

    return "\n\n".join(lines)


def main():
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)

    # Read all photos and sort by datetime
    photos = []
    for f in sorted(SOURCE_DIR.glob("*.jpg")) + sorted(SOURCE_DIR.glob("*.JPG")):
        exif = get_exif(f)
        dt_str = exif.get("DateTimeOriginal") or exif.get("DateTime")
        if dt_str:
            try:
                dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
            except ValueError:
                dt = None
        else:
            dt = None

        if dt is None:
            print(f"  SKIP (no date): {f.name}")
            continue

        photos.append((dt, f, exif))

    # Sort by datetime
    photos.sort(key=lambda x: x[0])

    print(f"Found {len(photos)} photos with EXIF dates\n")

    # Group by date and assign numbers
    by_date = defaultdict(list)
    for dt, f, exif in photos:
        by_date[dt.strftime("%Y-%m-%d")].append((dt, f, exif))

    saved = 0
    for date_dash in sorted(by_date.keys()):
        group = by_date[date_dash]
        date_prefix = date_dash.replace("-", "")

        for i, (dt, src_file, exif) in enumerate(group, 1):
            img_name = f"{date_dash}_photo_{i:02d}.jpg"
            img_dest = PHOTO_DIR / img_name

            # Copy image
            if not img_dest.exists():
                shutil.copy2(src_file, img_dest)

            # Create post
            post_filename = f"{date_prefix}_photo_{i}_photo.md"
            post_path = BLOG_DIR / post_filename

            # Handle collision with existing photoblog posts
            if post_path.exists():
                n = i + len(group)
                while True:
                    img_name = f"{date_dash}_photo_{n:02d}.jpg"
                    img_dest = PHOTO_DIR / img_name
                    post_filename = f"{date_prefix}_photo_{n}_photo.md"
                    post_path = BLOG_DIR / post_filename
                    if not post_path.exists():
                        if not img_dest.exists():
                            shutil.copy2(src_file, img_dest)
                        break
                    n += 1

            if post_path.exists():
                continue

            title = f"{date_dash} - photo"
            camera_info = build_camera_info(exif)

            lines = [
                "---",
                f"tags: {TAG}",
                f"thumbnail: files/photoblog/{img_name}",
                "---",
                "",
                f"# {title}",
                "",
                f"![{title}](files/photoblog/{img_name})",
                "",
            ]

            if camera_info:
                lines.append(camera_info)
                lines.append("")

            post_path.write_text("\n".join(lines), encoding="utf-8")
            print(f"  [{date_dash}] {src_file.name} -> {img_name}")
            saved += 1

    print(f"\nSaved {saved} posts with {saved} images")


if __name__ == "__main__":
    main()
