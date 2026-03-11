# Blog

Markdown posts that auto-build to a static site on push.

## Writing

Create a file named `YYYYMMDD_slug.md` in this folder. The title is taken from the first heading. Date is parsed from the filename.

Optional YAML frontmatter (`---` delimited) can override the title:

```
---
title: Custom Title
---
```

## Building

```bash
pip install -r requirements.txt
python build.py          # production build (for GitHub Pages)
python build.py --local  # local preview (serve _site/ with any HTTP server)
```

## Draft / Publish / Unpublish

| Action | How |
|--------|-----|
| **Draft** | Name the file `YYYYMMDD_slug.draft` — it's gitignored and excluded from builds |
| **Publish** | Rename `.draft` to `.md`, commit, and push |
| **Unpublish** | Rename `.md` back to `.draft`, commit, and push |

## Comments

Comments use a Staticman-like model: form submission creates a PR with a YAML file, owner merges, site rebuilds with comment visible.

Comment files live in `comments/<url_slug>/` as YAML:

```
comments/
  20230414-if-immigration-was-a-baby/
    1741651200_a1b2c3.yml
```

Each `.yml` file:

```yaml
name: Someone
date: 2026-03-11T08:20:00Z
comment: |
  Comment text here.
```

The comment form is hidden until `COMMENT_ENDPOINT` is set in `build.py` to a serverless function URL.

## Pagination

The index page loads 10 posts initially and reveals 10 more as the user scrolls down (infinite scroll via IntersectionObserver).

## Directory Structure

| Path | Purpose |
|------|---------|
| `*.md` | Blog post files |
| `build.py` | Static site builder |
| `templates/` | HTML templates |
| `static/` | CSS, JS, static assets |
| `files/` | Post-referenced assets (images, etc.) |
| `comments/` | Comment YAML files (per post) |
| `tools/` | One-time migration scripts and WordPress export |
| `_site/` | Build output (gitignored) |
