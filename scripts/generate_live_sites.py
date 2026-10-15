#!/usr/bin/env python3
"""Generate shared/live-sites.json.

Lists every public, non-fork, non-archived k1monfared repo that has a live
GitHub Pages site, so the notes landing page can show them automatically.
Sites are grouped into the categories defined in live-sites-categories.yml;
anything not listed there lands in "Other".

Detection has no per-repo API calls: the GitHub repo list already carries
``has_pages``. We then drop anything on BLOCKLIST and confirm the site is
actually serving (HTTP 2xx/3xx) before including it.

Run locally:      python scripts/generate_live_sites.py
Run in CI:        GITHUB_TOKEN=<token> python scripts/generate_live_sites.py
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml

OWNER = "k1monfared"
CUSTOM_DOMAIN = "https://k1monfared.com"
ROOT_REPO = "k1monfared.github.io"
OTHER = "Other"

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "shared" / "live-sites.json"
CATEGORIES_FILE = ROOT / "live-sites-categories.yml"
IMAGES_DIR = ROOT / "shared" / "live-sites"
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif")

# Repos that have Pages enabled but should not be listed (docs-only renders,
# shared libraries, meta repos). Add names here to hide a site.
BLOCKLIST = {
    "site_kit",
}

# Words rendered uppercase in the prettified title.
ACRONYMS = {"ltv", "llm", "ai", "ml", "pdf", "api", "rss"}

USER_AGENT = "k1monfared-live-sites-generator"


def _get(url, token=None, timeout=30):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/vnd.github+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def list_repos(token):
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{OWNER}/repos?per_page=100&page={page}"
        try:
            data = _get(url, token)
        except urllib.error.HTTPError as exc:
            if token and exc.code in (401, 403):
                # The scoped CI token cannot read another account's listing;
                # fall back to the unauthenticated public endpoint.
                data = _get(url, None)
            else:
                raise
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def is_live(url):
    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", USER_AGENT)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False


def site_url(name):
    if name == ROOT_REPO:
        return CUSTOM_DOMAIN + "/"
    return f"{CUSTOM_DOMAIN}/{name}/"


def title_for(name):
    if name == ROOT_REPO:
        return "Personal site"
    words = re.split(r"[_\-]+", name)
    return " ".join(w.upper() if w.lower() in ACRONYMS else w.capitalize() for w in words)


def load_categories():
    """Return (ordered category names, repo -> category, image overrides)."""
    if not CATEGORIES_FILE.exists():
        return [], {}, {}
    config = yaml.safe_load(CATEGORIES_FILE.read_text(encoding="utf-8")) or {}

    names = []
    repo_to_cat = {}
    for key, repos in config.items():
        if key == "images":
            continue
        names.append(key)
        for repo in repos or []:
            repo_to_cat.setdefault(repo, key)

    images = config.get("images") or {}
    return names, repo_to_cat, images


def find_image(name, overrides):
    if name in overrides:
        return overrides[name]
    if IMAGES_DIR.is_dir():
        for ext in IMAGE_EXTS:
            candidate = IMAGES_DIR / f"{name}{ext}"
            if candidate.exists():
                return f"shared/live-sites/{candidate.name}"
    return None


def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repos = list_repos(token)
    cat_names, repo_to_cat, image_overrides = load_categories()

    sites = []
    for repo in repos:
        name = repo["name"]
        if repo.get("private") or repo.get("fork") or repo.get("archived"):
            continue
        if not repo.get("has_pages"):
            continue
        if name in BLOCKLIST:
            continue

        url = site_url(name)
        if not is_live(url):
            print(f"skip {name}: {url} not reachable", file=sys.stderr)
            continue

        sites.append({
            "name": name,
            "title": title_for(name),
            "url": url,
            "description": repo.get("description") or "",
            "category": repo_to_cat.get(name, OTHER),
            "image": find_image(name, image_overrides),
        })

    sites.sort(key=lambda s: s["title"].lower())

    # Group in configured order, then "Other" for anything uncategorized.
    ordered = list(cat_names)
    if any(s["category"] == OTHER for s in sites) and OTHER not in ordered:
        ordered.append(OTHER)

    categories = []
    for cat in ordered:
        members = [s for s in sites if s["category"] == cat]
        if members:
            categories.append({"name": cat, "sites": members})

    # Leave the file untouched when nothing changed, so scheduled runs do not
    # create a commit (and a redeploy) just because the clock moved.
    if OUT.exists():
        try:
            existing = json.loads(OUT.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}
        if existing.get("categories") == categories:
            print(f"no change ({len(sites)} sites)")
            return

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(sites),
        "categories": categories,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(sites)} sites in {len(categories)} categories to {OUT}")


if __name__ == "__main__":
    main()
