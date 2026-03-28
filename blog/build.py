#!/usr/bin/env python3
"""Static blog builder. Converts markdown posts to HTML with index and RSS."""

import argparse
import re
import shutil
import html
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import yaml
import markdown
from pygments.formatters import HtmlFormatter

# --- Config ---
BLOG_DIR = Path(__file__).parent
SITE_DIR = BLOG_DIR / "_site"
TEMPLATE_DIR = BLOG_DIR / "templates"
STATIC_DIR = BLOG_DIR / "static"
FILES_DIR = BLOG_DIR / "files"
COMMENTS_DIR = BLOG_DIR / "comments"
SITE_URL = "https://k1monfared.github.io/notes/blog"
COMMENT_ENDPOINT = ""  # Set to serverless function URL when ready

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


EMBED_RE = re.compile(r'\[embed\](.*?)\[/embed\]', re.IGNORECASE)
YOUTUBE_RE = re.compile(r'https?://(?:www\.)?youtube\.com/watch\?v=([\w-]+)')
YOUTU_BE_RE = re.compile(r'https?://youtu\.be/([\w-]+)')


def convert_embeds(text):
    """Convert WordPress [embed]URL[/embed] to iframes (YouTube) or links."""
    def replace_embed(match):
        url = match.group(1).strip()
        yt = YOUTUBE_RE.match(url) or YOUTU_BE_RE.match(url)
        if yt:
            vid = yt.group(1)
            return (
                f'<div class="video-embed">'
                f'<iframe src="https://www.youtube.com/embed/{vid}" '
                f'frameborder="0" allowfullscreen loading="lazy"></iframe>'
                f'</div>'
            )
        return f'<a href="{url}">{url}</a>'
    return EMBED_RE.sub(replace_embed, text)


def render_markdown(text):
    """Convert markdown to HTML."""
    md = markdown.Markdown(extensions=MD_EXTENSIONS, extension_configs=MD_EXTENSION_CONFIGS)
    return md.convert(text)


def add_target_blank(html_text):
    """Add target='_blank' rel='noopener' to <a> tags that don't already have a target."""
    return re.sub(
        r'<a\s+((?:(?!target=)[^>])*)>',
        r'<a \1 target="_blank" rel="noopener">',
        html_text,
    )


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


def load_comments(url_slug):
    """Load and render comments for a post from comments/<url_slug>/*.yml."""
    comment_dir = COMMENTS_DIR / url_slug
    if not comment_dir.is_dir():
        return ""
    comments = []
    for yml_file in sorted(comment_dir.glob("*.yml")):
        try:
            data = yaml.safe_load(yml_file.read_text(encoding="utf-8"))
            if not data or "comment" not in data:
                continue
            comments.append(data)
        except Exception:
            continue
    if not comments:
        return ""
    parts = []
    for c in comments:
        name = html.escape(str(c.get("name", "Anonymous")))
        date_val = c.get("date", "")
        if hasattr(date_val, "strftime"):
            date_str = date_val.strftime("%B %d, %Y")
        else:
            date_str = html.escape(str(date_val))
        comment_text = html.escape(str(c["comment"])).replace("\n", "<br>")
        parts.append(
            f'<div class="comment">'
            f'<div class="comment-header">'
            f'<strong>{name}</strong> <span class="comment-date">{date_str}</span>'
            f'</div>'
            f'<div class="comment-body">{comment_text}</div>'
            f'</div>'
        )
    return "\n".join(parts)


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
        base_tmpl = base_tmpl.replace('<base href="/notes/blog/">', '<base href="/">')
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

        # Convert WordPress embeds
        content = convert_embeds(content)

        # Rewrite GitHub cross-links
        content = rewrite_github_links(content, slug_map)

        # Find referenced assets (before markdown rendering)
        for match in re.finditer(r'(?<![a-z/])files/([^"\')\s]+)', content):
            all_assets.add(f"files/{match.group(1)}")

        # Render markdown
        body_html = add_target_blank(render_markdown(content))

        # Load comments
        comments_html = load_comments(url_slug)

        # Parse tags from frontmatter
        tags = []
        raw_tags = meta.get("tags", "")
        if raw_tags:
            tags = [t.strip().lower() for t in raw_tags.split(",") if t.strip()]

        # Build tag chips for post page
        tag_chips_html = ""
        if tags:
            chips = " ".join(
                f'<a href="tag/{t}/" class="tag">{html.escape(t)}</a>' for t in tags
            )
            tag_chips_html = f'<span class="tag-chips">{chips}</span>'

        # Render post content (final page written after sidebar is built)
        date_str = date.strftime("%B %d, %Y")
        post_html = render_template(
            post_tmpl, title=title, date=date_str, body=body_html,
            comments=comments_html, comment_endpoint=COMMENT_ENDPOINT,
            post_slug=url_slug, tag_chips=tag_chips_html,
        )

        thumbnail = meta.get("thumbnail", "")

        posts_data.append({
            "title": title,
            "date": date,
            "date_str": date_str,
            "url_slug": url_slug,
            "excerpt": excerpt,
            "tags": tags,
            "thumbnail": thumbnail,
            "post_html": post_html,
        })

    # Build tag map
    tag_map = {}
    for p in posts_data:
        for tag in p["tags"]:
            tag_map.setdefault(tag, []).append(p)

    # --- Tag hierarchy helpers ---
    def collect_tree_tags(children):
        """Collect all tag names from a recursive tree of children."""
        tags = set()
        for item in children:
            if isinstance(item, str):
                tags.add(item)
            elif isinstance(item, dict):
                for parent, sub in item.items():
                    tags.add(parent)
                    if sub:
                        tags.update(collect_tree_tags(sub))
        return tags

    def render_tag_tree(items, tm):
        """Render a list of tree items as nested HTML (details/summary)."""
        parts = []
        for item in items:
            if isinstance(item, str):
                if item not in tm:
                    continue
                parts.append(
                    f'<a href="tag/{item}/" class="tag-sidebar-link">'
                    f'{html.escape(item)}'
                    f' <span class="tag-count">{len(tm[item])}</span></a>'
                )
            elif isinstance(item, dict):
                for parent, sub_children in item.items():
                    all_tags = {parent} | (collect_tree_tags(sub_children) if sub_children else set())
                    existing = {t for t in all_tags if t in tm}
                    if not existing:
                        continue
                    group_count = sum(len(tm[t]) for t in existing)
                    child_html = render_tag_tree(sub_children, tm) if sub_children else ""
                    if parent in tm:
                        parent_link = (
                            f'<a href="tag/{parent}/" class="tag-sidebar-link">'
                            f'{html.escape(parent)}'
                            f' <span class="tag-count">{group_count}</span></a>'
                        )
                    else:
                        parent_link = (
                            f'<span class="tag-sidebar-label">{html.escape(parent)}'
                            f' <span class="tag-count">{group_count}</span></span>'
                        )
                    parts.append(
                        f'<details>\n'
                        f'<summary>{parent_link}</summary>\n'
                        f'{child_html}\n'
                        f'</details>'
                    )
        return "\n".join(parts)

    # Load tag hierarchy from tags.yml
    tags_yml_path = BLOG_DIR / "tags.yml"
    grouped_tags = set()
    tag_sidebar_html = ""

    if tag_map:
        hierarchy = {}
        if tags_yml_path.exists():
            hierarchy = yaml.safe_load(tags_yml_path.read_text(encoding="utf-8")) or {}

        # Collect all tags claimed by the hierarchy
        for parent, children in hierarchy.items():
            grouped_tags.add(parent)
            if children:
                grouped_tags.update(collect_tree_tags(children))

        # Render grouped tags as nested details
        top_items = [{k: v} for k, v in hierarchy.items()]
        sidebar_parts = [render_tag_tree(top_items, tag_map)]

        # Collect ungrouped tags into "Other"
        other_tags = sorted(
            (t for t in tag_map if t not in grouped_tags),
            key=lambda t: (-len(tag_map[t]), t),
        )
        if other_tags:
            other_count = sum(len(tag_map[t]) for t in other_tags)
            other_links = "\n".join(
                f'<a href="tag/{t}/" class="tag-sidebar-link">{html.escape(t)}'
                f' <span class="tag-count">{len(tag_map[t])}</span></a>'
                for t in other_tags
            )
            sidebar_parts.append(
                f'<details>\n'
                f'<summary><span class="tag-sidebar-label">Other'
                f' <span class="tag-count">{other_count}</span></span></summary>\n'
                f'{other_links}\n'
                f'</details>'
            )

        inner = "\n".join(sidebar_parts)
        tag_sidebar_html = (
            '<aside class="tag-sidebar" id="tag-sidebar">\n'
            '  <div class="tag-sidebar-header">'
            '<h3>Tags</h3>'
            '<button id="tag-sort" class="tag-sort-btn" title="Sort alphabetically">A-Z</button>'
            '</div>\n'
            f'  {inner}\n'
            '</aside>'
        )

    # --- Timeline sidebar ---
    MONTH_NAMES = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    from collections import defaultdict as _dd
    year_month = _dd(lambda: _dd(list))
    for p in posts_data:
        y = p["date"].year
        m = p["date"].month
        year_month[y][m].append(p)

    timeline_parts = []
    for year in sorted(year_month.keys(), reverse=True):
        months = year_month[year]
        year_count = sum(len(posts) for posts in months.values())
        month_parts = []
        for month in sorted(months.keys(), reverse=True):
            month_posts = months[month]
            post_links = "\n".join(
                f'<a href="{p["url_slug"]}/" class="timeline-link" target="_blank" rel="noopener">'
                f'{html.escape(p["title"])}'
                f'<span class="timeline-date">{p["date"].day}</span></a>'
                for p in month_posts
            )
            month_parts.append(
                f'<details>\n'
                f'<summary><span class="timeline-label" data-scroll="date-{year}-{month:02d}">{MONTH_NAMES[month]}'
                f' <span class="tag-count">{len(month_posts)}</span></span></summary>\n'
                f'{post_links}\n'
                f'</details>'
            )
        timeline_parts.append(
            f'<details>\n'
            f'<summary><span class="timeline-label" data-scroll="date-{year}">{year}'
            f' <span class="tag-count">{year_count}</span></span></summary>\n'
            f'{"".join(month_parts)}\n'
            f'</details>'
        )

    timeline_sidebar_html = (
        '<aside class="timeline-sidebar" id="timeline-sidebar">\n'
        '  <div class="timeline-sidebar-header"><h3>Timeline</h3></div>\n'
        f'  {"".join(timeline_parts)}\n'
        '</aside>'
    ) if timeline_parts else ""

    # Write post pages (deferred so sidebar is available)
    for p in posts_data:
        page_html = render_template(base_tmpl, title=p["title"], content=p["post_html"], sidebar=tag_sidebar_html, timeline_sidebar=timeline_sidebar_html)
        post_dir = SITE_DIR / p["url_slug"]
        post_dir.mkdir(parents=True, exist_ok=True)
        (post_dir / "index.html").write_text(page_html, encoding="utf-8")

    def make_tag_chips(tags):
        """Generate tag chip HTML for a post listing."""
        if not tags:
            return ""
        chips = " ".join(
            f'<a href="tag/{t}/" class="tag">{html.escape(t)}</a>' for t in tags
        )
        return f'<span class="tag-chips">{chips}</span>'

    def make_post_list(post_list, page_size=None):
        """Generate <li> items for a list of posts."""
        items = []
        for i, p in enumerate(post_list):
            excerpt_html = f'<p class="post-excerpt">{html.escape(p["excerpt"])}</p>' if p["excerpt"] else ""
            chips_html = make_tag_chips(p["tags"])
            thumb = p.get("thumbnail", "")
            thumb_html = f'<img class="post-thumbnail" src="{html.escape(thumb)}" alt="" loading="lazy">' if thumb else ""
            hidden = ' hidden' if page_size and i >= page_size else ''
            date_y = p["date"].strftime("%Y")
            date_ym = p["date"].strftime("%Y-%m")
            items.append(
                f'  <li{hidden} data-year="date-{date_y}" data-month="date-{date_ym}">\n'
                f'    <a href="{p["url_slug"]}/" target="_blank" rel="noopener">\n'
                f'      {thumb_html}\n'
                f'      <span class="post-title">{html.escape(p["title"])}</span>\n'
                f'      <span class="post-date">{p["date_str"]}</span>\n'
                f'      {excerpt_html}\n'
                f'    </a>\n'
                f'    <div class="post-meta-line">{chips_html}</div>\n'
                f'  </li>'
            )
        return "\n".join(items)

    # Generate index page
    PAGE_SIZE = 10
    index_content = render_template(
        index_tmpl,
        posts=make_post_list(posts_data, page_size=PAGE_SIZE),
    )
    index_html = render_template(base_tmpl, title="Blog", content=index_content, sidebar=tag_sidebar_html, timeline_sidebar=timeline_sidebar_html)
    (SITE_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # Generate tag pages
    if tag_map:
        tag_tmpl = load_template("tag.html")
        for tag, tag_posts in tag_map.items():
            tag_content = render_template(
                tag_tmpl,
                tag=html.escape(tag),
                posts=make_post_list(tag_posts),
            )
            tag_html = render_template(
                base_tmpl, title=f"Posts tagged: {tag}", content=tag_content, sidebar=tag_sidebar_html, timeline_sidebar=timeline_sidebar_html
            )
            tag_dir = SITE_DIR / "tag" / tag
            tag_dir.mkdir(parents=True, exist_ok=True)
            (tag_dir / "index.html").write_text(tag_html, encoding="utf-8")
        print(f"Generated {len(tag_map)} tag pages")

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
