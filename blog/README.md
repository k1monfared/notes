# Blog

[https://k1monfared.github.io/notes/](https://k1monfared.github.io/notes/)

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
| **Draft** | Name the file `YYYYMMDD_slug.draft` — committed to git but excluded from builds |
| **Publish** | Rename `.draft` to `.md`, commit, and push |
| **Unpublish** | Rename `.md` back to `.draft`, commit, and push |

## Mobile Editor (Blog Writer PWA)

A Progressive Web App for writing and publishing posts from your phone. Lives in `blog-writer/` at the repo root.

**Live URL:** [https://k1monfared.github.io/notes/blog-writer/](https://k1monfared.github.io/notes/blog-writer/)

### Setup

1. Open the URL above on your phone
2. Create a [fine-grained Personal Access Token](https://github.com/settings/personal-access-tokens/new):
   - Repository access: select **k1monfared/notes** only
   - Permissions: **Contents** read and write
3. Paste the token into the app
4. Tap "Add to Home Screen" in your browser menu to install it as an app

### Features

- Markdown editor with toolbar (bold, italic, heading, link, image)
- Image insertion from camera or gallery (auto-resized, stored in `files/YYYYMMDD/`)
- Auto-generated filenames following `YYYYMMDD_slug.md` convention
- Tag suggestions based on content keywords
- Live markdown preview
- Draft support (saves as `.draft`, excluded from builds)
- Publishes directly to `main` via the GitHub API (single atomic commit)
- Dark mode (follows system preference)
- Works offline for drafting

### How it works

The app uses the GitHub Contents and Git Trees APIs to create atomic commits containing both the markdown file and any attached images. Pushing to `main` triggers the existing GitHub Actions workflow, which builds the blog and deploys to GitHub Pages. Posts appear live within about 2 minutes.

Images uploaded via the app are stored as regular git blobs (not LFS), which is fine for the build pipeline.

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
