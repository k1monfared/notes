#!/usr/bin/env python3
"""Auto-add recommender property to movies under 'Recommended by' subsections.

Movies under a subsection like "- Anton K" within "- Recommended by" should
have a "- Recommender: Anton K" property. This script adds it if missing.
"""

import re
from pathlib import Path

MOVIES_FILE = Path(__file__).parent / "movies.log"
TODO_RE = re.compile(r"^(\s*)\[([x\-? ]?)\]\s*(.+?)\s*$", re.IGNORECASE)


def main():
    lines = MOVIES_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    fixed = 0
    offset = 0

    in_recommended = False
    current_recommender = None
    rec_cat_indent = None

    for i in range(len(lines)):
        idx = i + offset
        if idx >= len(lines):
            break

        raw = lines[idx].rstrip("\n")
        stripped = raw.strip()
        if not stripped:
            continue

        indent = len(raw) - len(raw.lstrip())

        # Detect "Recommended by" category (indent 4)
        if indent == 4 and stripped.startswith("- "):
            name = stripped[2:].rstrip(":").strip()
            if "recommended by" in name.lower():
                in_recommended = True
                rec_cat_indent = indent
                current_recommender = None
                continue
            else:
                if in_recommended:
                    in_recommended = False
                    current_recommender = None
                continue

        if not in_recommended:
            continue

        # Root section resets
        if indent == 0:
            in_recommended = False
            current_recommender = None
            continue

        # Subsection (indent 8) = recommender name
        if indent == 8 and stripped.startswith("- "):
            current_recommender = stripped[2:].rstrip(":").strip()
            continue

        # Movie entry under a recommender
        if current_recommender and TODO_RE.match(raw):
            movie_indent = indent
            # Check if this movie already has a recommender property
            has_rec = False
            j = idx + 1
            while j < len(lines):
                child = lines[j].rstrip("\n")
                if not child.strip():
                    j += 1
                    continue
                child_indent = len(child) - len(child.lstrip())
                if child_indent <= movie_indent:
                    break
                lower = child.strip().lower()
                if lower.startswith("- recommender:") or lower.startswith("- recommended by:") or \
                   lower.startswith("- recommmender:") or lower.startswith("- receommender:"):
                    has_rec = True
                    break
                j += 1

            if not has_rec:
                # Insert recommender property right after the movie line
                pad = " " * (movie_indent + 4)
                new_line = f"{pad}- Recommender: {current_recommender}\n"
                lines.insert(idx + 1, new_line)
                offset += 1
                fixed += 1
                title = TODO_RE.match(raw).group(3).strip()
                print(f"  + {title} → Recommender: {current_recommender}")

    if fixed > 0:
        MOVIES_FILE.write_text("".join(lines), encoding="utf-8")
        print(f"\nAdded recommender to {fixed} movie(s)")
    else:
        print("All movies in 'Recommended by' already have recommender set")

    return 0


if __name__ == "__main__":
    main()
