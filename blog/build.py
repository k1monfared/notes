#!/usr/bin/env python3
"""Static blog builder. Converts markdown posts to HTML with index and RSS."""

import argparse
import os
import re
import shutil
import html
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import markdown
from pygments.formatters import HtmlFormatter

# --- Config ---
BLOG_DIR = Path(__file__).parent
SITE_DIR = BLOG_DIR / "_site"
TEMPLATE_DIR = BLOG_DIR / "templates"
STATIC_DIR = BLOG_DIR / "static"
FILES_DIR = BLOG_DIR / "files"
SITE_URL = "https://k1monfared.github.io/notes"

MD_EXTENSIONS = ["extra", "codehilite", "toc", "smarty", "md_in_html"]
def unicode_slugify(value, separator='-'):
    """Slugify that preserves Unicode characters (for Persian/Arabic headings)."""
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[\s]+', separator, value)

MD_EXTENSION_CONFIGS = {
    "codehilite": {"css_class": "highlight", "guess_lang": False},
    "toc": {"slugify": unicode_slugify},
}

GITHUB_LINK_RE = re.compile(
    r"https://github\.com/k1monfared/notes/blob/main/blog/(\d{8}_[^)\"'\s]+\.md)"
)


def parse_filename(filename):
    """Extract date and slug from YYYYMMDD_slug.md filename."""
    stem = Path(filename).stem
    match = re.match(r"^(\d{8})_(.+)$", stem)
    if not match:
        return None, None, None
    date_str, slug = match.group(1), match.group(2)
    slug = slug.replace("_", "-")
    date = datetime(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
    return date, slug, f"{date_str[:8]}-{slug}"


def parse_frontmatter(text):
    """Parse optional key: value frontmatter delimited by ---. Returns (meta, body)."""
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
    """Extract title from first heading (ATX or Setext). Strips bold markers."""
    lines = text.strip().splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        # ATX heading
        atx = re.match(r"^#{1,6}\s+(.+?)(?:\s*#*\s*)?$", stripped)
        if atx:
            title = atx.group(1).strip()
            title = re.sub(r"\*\*(.+?)\*\*", r"\1", title)
            remaining = "\n".join(lines[:i] + lines[i + 1 :])
            return title, remaining
        # Setext heading (next line is -- or ==)
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if stripped and re.match(r"^[=-]+$", next_line):
                title = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
                remaining = "\n".join(lines[:i] + lines[i + 2 :])
                return title, remaining
    return "Untitled", text


def extract_excerpt(text, max_len=200):
    """Extract first paragraph of plain text as excerpt."""
    # Remove headings, images, links-as-images
    clean = re.sub(r"^#{1,6}\s+.*$", "", text, flags=re.MULTILINE)
    clean = re.sub(r"!\[.*?\]\(.*?\)", "", clean)
    clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
    clean = re.sub(r"[*_`~]", "", clean)
    clean = re.sub(r"<[^>]+>", "", clean)
    for para in clean.split("\n\n"):
        para = para.strip()
        if para and not para.startswith("[") and len(para) > 20:
            if len(para) > max_len:
                return para[:max_len].rsplit(" ", 1)[0] + "..."
            return para
    return ""


def find_referenced_assets(text):
    """Find all files/ references in the post content."""
    refs = set()
    for match in re.finditer(r'(?:src|href)=["\']?(files/[^"\')\s]+)', text):
        refs.add(match.group(1))
    for match in re.finditer(r'\(files/([^)]+)\)', text):
        refs.add(f"files/{match.group(1)}")
    for match in re.finditer(r'\[.*?\]\(files/([^)]+)\)', text):
        refs.add(f"files/{match.group(1)}")
    return refs


def build_slug_map(posts):
    """Build a map of original markdown filenames to blog URL slugs."""
    slug_map = {}
    for filename, _date, _slug, url_slug in posts:
        slug_map[filename] = url_slug
    return slug_map


def rewrite_github_links(text, slug_map):
    """Convert github.com/.../blog/FILENAME.md links to blog URLs."""
    def replace_link(match):
        filename = match.group(1)
        if filename in slug_map:
            return f"{slug_map[filename]}/"
        return match.group(0)
    return GITHUB_LINK_RE.sub(replace_link, text)


def render_markdown(text):
    """Convert markdown to HTML."""
    md = markdown.Markdown(extensions=MD_EXTENSIONS, extension_configs=MD_EXTENSION_CONFIGS)
    return md.convert(text)


def generate_pygments_css():
    """Generate Pygments CSS for light and dark themes."""
    light = HtmlFormatter(style="default").get_style_defs(".highlight")
    dark = HtmlFormatter(style="monokai").get_style_defs('[data-theme="dark"] .highlight')
    return f"/* Pygments - light */\n{light}\n\n/* Pygments - dark */\n{dark}\n"


def load_template(name):
    """Load a template file."""
    return (TEMPLATE_DIR / name).read_text()


def render_template(template, **kwargs):
    """Simple {{var}} template substitution."""
    result = template
    for key, val in kwargs.items():
        result = result.replace(f"{{{{{key}}}}}", str(val))
    return result


def generate_rss(posts_data):
    """Generate RSS 2.0 XML feed."""
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Blog"
    ET.SubElement(channel, "link").text = f"{SITE_URL}/"
    atom_link = ET.SubElement(channel, "atom:link")
    atom_link.set("href", f"{SITE_URL}/feed.xml")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")
    ET.SubElement(channel, "description").text = "Blog posts"
    ET.SubElement(channel, "language").text = "en-us"

    for post in posts_data[:20]:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = post["title"]
        ET.SubElement(item, "link").text = f"{SITE_URL}/{post['url_slug']}/"
        ET.SubElement(item, "guid").text = f"{SITE_URL}/{post['url_slug']}/"
        ET.SubElement(item, "pubDate").text = post["date"].strftime(
            "%a, %d %b %Y 00:00:00 +0000"
        )
        ET.SubElement(item, "description").text = post["excerpt"]

    tree = ET.ElementTree(rss)
    ET.indent(tree)
    return ET.tostring(rss, encoding="unicode", xml_declaration=True)


def build(local=False):
    """Main build function."""
    # Clean output
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)

    # Collect all post files
    md_files = sorted(BLOG_DIR.glob("*.md"))
    posts = []
    for f in md_files:
        date, slug, url_slug = parse_filename(f.name)
        if date is None:
            continue
        posts.append((f.name, date, slug, url_slug))

    # Sort newest first
    posts.sort(key=lambda p: p[1], reverse=True)

    # Build slug map for cross-references
    slug_map = build_slug_map(posts)

    # Load templates
    base_tmpl = load_template("base.html")
    if local:
        base_tmpl = base_tmpl.replace('<base href="/notes/">', '<base href="/">')
    post_tmpl = load_template("post.html")
    index_tmpl = load_template("index.html")

    # Generate Pygments CSS
    pygments_css = generate_pygments_css()

    # Copy static files and append Pygments CSS to style.css
    static_out = SITE_DIR / "static"
    shutil.copytree(STATIC_DIR, static_out)
    with open(static_out / "style.css", "a") as f:
        f.write(f"\n{pygments_css}")

    # Process posts
    all_assets = set()
    posts_data = []

    for filename, date, slug, url_slug in posts:
        filepath = BLOG_DIR / filename
        raw = filepath.read_text(encoding="utf-8")

        # Parse frontmatter
        meta, body = parse_frontmatter(raw)

        # Extract title
        title = meta.get("title")
        if title:
            content = body
        else:
            title, content = extract_title(body)

        # Extract excerpt before processing
        excerpt = extract_excerpt(content)

        # Rewrite GitHub cross-links
        content = rewrite_github_links(content, slug_map)

        # Find referenced assets (before markdown rendering)
        for match in re.finditer(r'(?<![a-z/])files/([^"\')\s]+)', content):
            all_assets.add(f"files/{match.group(1)}")

        # Render markdown
        body_html = render_markdown(content)

        # Render post page
        date_str = date.strftime("%B %d, %Y")
        post_html = render_template(post_tmpl, title=title, date=date_str, body=body_html)
        page_html = render_template(base_tmpl, title=title, content=post_html)

        # Write post
        post_dir = SITE_DIR / url_slug
        post_dir.mkdir(parents=True)
        (post_dir / "index.html").write_text(page_html, encoding="utf-8")

        posts_data.append({
            "title": title,
            "date": date,
            "date_str": date_str,
            "url_slug": url_slug,
            "excerpt": excerpt,
        })

    # Generate index page
    post_items = []
    for p in posts_data:
        excerpt_html = f'<p class="post-excerpt">{html.escape(p["excerpt"])}</p>' if p["excerpt"] else ""
        post_items.append(
            f'  <li>\n'
            f'    <a href="{p["url_slug"]}/">\n'
            f'      <span class="post-title">{html.escape(p["title"])}</span>\n'
            f'      <span class="post-date">{p["date_str"]}</span>\n'
            f'      {excerpt_html}\n'
            f'    </a>\n'
            f'  </li>'
        )

    index_content = render_template(index_tmpl, posts="\n".join(post_items))
    index_html = render_template(base_tmpl, title="Blog", content=index_content)
    (SITE_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # Generate RSS feed
    rss_xml = generate_rss(posts_data)
    (SITE_DIR / "feed.xml").write_text(rss_xml, encoding="utf-8")

    # Copy only referenced assets
    copied_assets = 0
    for asset in all_assets:
        src = BLOG_DIR / asset
        if src.exists():
            dst = SITE_DIR / asset
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied_assets += 1

    print(f"Built {len(posts_data)} posts to {SITE_DIR.relative_to(BLOG_DIR)}")
    print(f"Copied {copied_assets} referenced assets")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the blog")
    parser.add_argument("--local", action="store_true", help="Build for local preview (no base href)")
    args = parser.parse_args()
    build(local=args.local)
