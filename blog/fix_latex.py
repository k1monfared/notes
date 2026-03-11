#!/usr/bin/env python3
"""Fix leftover WordPress LaTeX and HTML entity issues in blog markdown files.

Issues fixed:
1. Multiline $latex ...$ blocks → $...$ (WordPress LaTeX shortcode)
2. HTML entities in markdown (e.g. &amp; → &)

Usage: python fix_latex.py
"""

import html
import re
from pathlib import Path

BLOG_DIR = Path(__file__).parent


def fix_multiline_latex(content):
    """Convert multiline $latex ...$ blocks to $...$."""
    # Match $latex ... $ spanning multiple lines
    return re.sub(r"\$latex\s+(.+?)\$", r"$\1$", content, flags=re.DOTALL)


def fix_html_entities(content):
    """Decode HTML entities that survived the import."""
    # Only fix known HTML entities, not dollar signs or other markdown-meaningful chars
    content = content.replace("&amp;", "&")
    content = content.replace("&lt;", "<")
    content = content.replace("&gt;", ">")
    content = content.replace("&quot;", '"')
    content = content.replace("&#8211;", "–")
    content = content.replace("&#8212;", "—")
    content = content.replace("&#8216;", "'")
    content = content.replace("&#8217;", "'")
    content = content.replace("&#8220;", "\u201c")
    content = content.replace("&#8221;", "\u201d")
    content = content.replace("&#8230;", "…")
    return content


def main():
    fixed_files = 0
    for md_file in sorted(BLOG_DIR.glob("*.md")):
        if md_file.name == "README.md":
            continue
        original = md_file.read_text(encoding="utf-8")
        content = original

        content = fix_multiline_latex(content)
        content = fix_html_entities(content)

        if content != original:
            md_file.write_text(content, encoding="utf-8")
            # Report what changed
            changes = []
            if "$latex" in original and "$latex" not in content:
                changes.append("fixed $latex blocks")
            if "&amp;" in original and "&amp;" not in content:
                changes.append("fixed &amp; entities")
            print(f"  FIXED: {md_file.name} ({', '.join(changes)})")
            fixed_files += 1

    print(f"\nDone: {fixed_files} files fixed")


if __name__ == "__main__":
    main()
