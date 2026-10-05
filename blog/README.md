# Blog

[https://k1monfared.com/notes/](https://k1monfared.com/notes/)

Markdown posts that auto-build to a static site on push.

## Writing

Create a file named `posts/YYYY/YYYYMMDD_slug.md` (YYYY is the post's year) in this folder. The title is taken from the first heading. Date is parsed from the filename.

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

**Live URL:** [https://k1monfared.com/notes/blog-writer/](https://k1monfared.com/notes/blog-writer/)

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

## Audio and Video

Self-hosted media uses the same syntax as images. The build detects the file extension and renders the right HTML5 element:

```markdown
![Caption here](files/20260514/song.mp3)
![](files/20260514/demo.mp4)
```

Renders as:

- `<audio controls>` for `mp3`, `m4a`, `wav`, `oga`, `ogg`, `flac`, `opus`, `aac`
- `<video controls>` for `mp4`, `mov`, `webm`, `m4v`, `ogv`
- regular `<img>` for everything else

The reference must sit on its own line for the conversion to trigger. Captions become `<figcaption>` text.

GitHub Pages supports HTTP byte-range requests, so the browser streams and seeks natively. For files larger than ~25 MB consider uploading to a GitHub Release and linking to that URL instead, so the repo doesn't grow per post.

The mobile editor has a separate audio/video button (musical note icon) in the toolbar that picks the file from the device and uploads it under `files/YYYYMMDD/` in the same atomic commit as the post.

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

## Search

Static, serverless search over all published posts. Press `Ctrl+K` (or `Cmd+K`) or the magnifier in the nav. No query ever leaves the browser.

Two retrieval arms are fused with Reciprocal Rank Fusion, plus light title/tag/recency boosts:

- **Keyword (BM25-ish):** MiniSearch, built in the browser from `docs.json`. Works instantly, no download.
- **Semantic:** int8 document vectors from `vectors.bin`, compared against a query embedding computed in the browser with Transformers.js running the same model the build used (`Xenova/multilingual-e5-small`). This is cross-lingual, so an English query can surface Persian posts.

Two serving modes share one engine. Local previews embed on-device and are fully private. Production serves hybrid search through a Cloudflare Worker so visitors download nothing.

Queries support operators, enforced as hard constraints over both arms. `+word` must be present as an exact word, `-word` drops any hit containing it, and `"some words"` must appear adjacently (single-word quotes behave like `+word`). Facets scope the search: `tag:math` (use quotes for multi-word tags, as in `tag:"linear algebra"`), `-tag:food` to exclude one, `lang:fa` or `lang:en`, and `after:2024` / `before:2020-05` (year, year-month, or full date). A query of only facets, like `tag:math after:2024`, browses the matching posts newest-first. Plain words use AND-first matching with OR fallback, and semantic candidates under 0.70 similarity are dropped. The list caps at 30.

- **Engine:** the source-agnostic package at the repo root, `search/`. Each content type is an adapter that yields documents. The blog adapter reads `posts/`. The same engine is meant to serve movies, books, and the rest later, either per source or combined with a scope filter.
- **Pipeline:** `search/pipeline.py` extracts, cleans, normalizes (including Persian/Arabic variants), chunks by heading, embeds, and emits `docs.json`, `manifest.json`, and `vectors.bin` under `blog/_site/search/`. `blog/build.py` invokes it after each build and copies the browser runtime. Backends: `local` (default, e5-small via `search/node/embed.mjs`, works offline once the model is cached) and `cloudflare` (bge-m3 via the Workers AI REST API, needs `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN`). Select with `--backend` or `SEARCH_BACKEND`. `SEARCH_NO_EMBED=1` builds keyword-only.
- **Incremental:** chunks are cached in `search/.cache/blog.json` and embeddings in `search/.cache/embed-*.json`, keyed by content hash and the pipeline fingerprint. Only new or changed posts are reprocessed, so a new post never waits on old ones.
- **Two-step publishing:** pushing a post triggers `deploy-blog.yml`, which goes live fast with keyword-only search. On success, `update-search-index.yml` embeds the new chunks through Workers AI and redeploys, upgrading search to full hybrid a few minutes later. No local computer needed; phone-published posts work the same.
- **Worker API:** `search/worker/` is a thin Cloudflare Worker (same account and CORS pattern as news_reader's subscribe-proxy). It reads the public `docs.json`/`vectors.bin`, embeds the query with Workers AI, fuses keyword plus vector results, and returns JSON. The browser calls it when the manifest says `backend: cloudflare`, renders local keyword results instantly, then upgrades to the server hybrid. Offline or on error, keyword results stay. Deploy with `wrangler deploy` from `search/worker/`, then put the printed URL into `search/sources.yml` under `api.search`.
- **Offline testing:** `python -m search.query --query "..."` runs the same fusion on this machine with no internet and no Cloudflare, for local previews and debugging.
- **Pre-deploy gate:** `python -m unittest discover -s search/tests` (34 tests: cleaning, API parsing, quantization, artifacts, manifest schema, AND fallback, vector floor, result cap) and `node search/worker/test/run_tests.mjs` (22 tests: ranking, AND fallback, vector floor, result cap, CORS, error paths, prefix threading, config consistency against `wrangler.toml`). Both workflows run them before building, so a regression fails the run before anything ships.
- **Manual build:** `python -m search.pipeline --source blog` (`--force` to ignore the cache, `--no-embed` to skip embeddings). First local embedder run needs `npm install` in `search/node/`.

## Directory Structure

| Path | Purpose |
|------|---------|
| `posts/` | Blog post files, organized by year (`posts/YYYY/YYYYMMDD_slug.md`) |
| `build.py` | Static site builder |
| `templates/` | HTML templates |
| `static/` | CSS, JS, static assets |
| `files/` | Post-referenced assets (images, etc.) |
| `comments/` | Comment YAML files (per post) |
| `tools/` | One-time migration scripts and WordPress export |
| `_site/` | Build output (gitignored) |
| `_site/search/` | Generated search index and browser runtime |
| `../search/` | Shared search engine (adapters, pipeline, runtime) |
