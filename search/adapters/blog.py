"""Blog source adapter.

Reads published markdown posts under blog/posts/YYYY/YYYYMMDD_slug.md and
yields search documents. Drafts (`.draft`) are ignored.
"""

import re
from datetime import datetime
from pathlib import Path

from ..config import REPO_ROOT
from ..text import detect_lang

FILENAME_RE = re.compile(r"^(\d{8})_(.+)$")


def parse_frontmatter(text):
    """Parse optional key: value frontmatter delimited by ---."""
    meta = {}
    if not text.startswith("---"):
        return meta, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return meta, text
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip().lower()] = val.strip()
    return meta, parts[2]


def extract_title(text):
    """Extract the title from the first heading and return the rest.

    Mirrors blog/build.py so the search adapter agrees with the rendered page.
    """
    lines = text.strip().splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        atx = re.match(r"^#{1,6}\s+(.+?)(?:\s*#*\s*)?$", stripped)
        if atx:
            title = re.sub(r"\*\*(.+?)\*\*", r"\1", atx.group(1).strip())
            title = re.sub(r"\s*\{#[^}]*\}\s*$", "", title).strip()
            return title, "\n".join(lines[:i] + lines[i + 1:])
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if stripped and re.match(r"^[=-]+$", next_line):
                title = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
                title = re.sub(r"\s*\{#[^}]*\}\s*$", "", title).strip()
                return title, "\n".join(lines[:i] + lines[i + 2:])
    return "Untitled", text


def parse_filename(filename):
    stem = Path(filename).stem
    match = FILENAME_RE.match(stem)
    if not match:
        return None
    date_str, slug = match.group(1), match.group(2).replace("_", "-")
    date = datetime(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
    return date, slug, f"{date_str}-{slug}"


def iter_documents(config):
    posts_dir = REPO_ROOT / config.get("posts_dir", "blog/posts")
    for path in sorted(posts_dir.glob("*/*.md")):
        parsed = parse_filename(path.name)
        if not parsed:
            continue
        date, _slug, url_slug = parsed

        raw = path.read_text(encoding="utf-8")
        # Normalize editor-relative media paths, as build.py does.
        raw = re.sub(r"(?:\.\./)+files/", "files/", raw)
        meta, body = parse_frontmatter(raw)

        title = meta.get("title") or ""
        if title:
            content = body
        else:
            title, content = extract_title(body)

        tags = [t.strip().lower() for t in meta.get("tags", "").split(",") if t.strip()]

        yield {
            "id": url_slug,
            "title": title.strip(),
            "date": date.strftime("%Y-%m-%d"),
            "url": f"{url_slug}/",
            "tags": tags,
            "lang": detect_lang(title + "\n" + content),
            "content": content,
        }
