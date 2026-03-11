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
