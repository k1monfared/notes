#!/usr/bin/env python3
"""Batch-enrich all movies missing IMDb data in movies.log.

OMDb free tier: 1000 calls/day, no per-second limit.
Each movie needs 2 calls (search + details) = ~500 movies per run.
We add a small delay (0.2s) between movies to be respectful.
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

MOVIES_FILE = Path(__file__).parent / "movies.log"
OMDB_URL = "http://www.omdbapi.com/"
TODO_RE = re.compile(r"^(\s*)\[([x\-? ]?)\]\s*(.+?)\s*$", re.IGNORECASE)
DELAY = 0.2  # seconds between movies


def omdb_search(api_key, title):
    params = urllib.parse.urlencode({"apikey": api_key, "s": title, "type": "movie"})
    with urllib.request.urlopen(f"{OMDB_URL}?{params}", timeout=10) as resp:
        data = json.loads(resp.read())
    if data.get("Response") == "False":
        return []
    return data.get("Search", [])


def omdb_details(api_key, imdb_id):
    params = urllib.parse.urlencode({"apikey": api_key, "i": imdb_id, "plot": "short"})
    with urllib.request.urlopen(f"{OMDB_URL}?{params}", timeout=10) as resp:
        data = json.loads(resp.read())
    if data.get("Response") == "False":
        return None
    return data


def find_insert_after(lines, movie_idx, movie_indent):
    idx = movie_idx + 1
    while idx < len(lines):
        stripped = lines[idx].rstrip("\n")
        if not stripped.strip():
            idx += 1
            continue
        line_indent = len(stripped) - len(stripped.lstrip())
        if line_indent > movie_indent:
            idx += 1
        else:
            break
    return idx


def has_imdb_data(lines, movie_idx, movie_indent):
    """Check if a movie already has IMDB link/marker, rating, or genres."""
    idx = movie_idx + 1
    while idx < len(lines):
        stripped = lines[idx].rstrip("\n")
        if not stripped.strip():
            idx += 1
            continue
        line_indent = len(stripped) - len(stripped.lstrip())
        if line_indent <= movie_indent:
            break
        lower = stripped.strip().lower()
        if lower.startswith("- imdb:") or lower.startswith("- imdb rating:") or \
           lower.startswith("- rating:") or lower.startswith("- genres:"):
            return True
        idx += 1
    return False


def build_imdb_lines(d, indent):
    na = lambda v: v if v and v != "N/A" else None
    pad = " " * (indent + 4)
    new_lines = []

    fields = [
        ("Year", na(d.get("Year"))),
        ("IMDB Rating", na(d.get("imdbRating")) and d["imdbRating"] + "/10"),
        ("Genres", na(d.get("Genre"))),
        ("Country", na(d.get("Country"))),
        ("Duration", na(d.get("Runtime"))),
        ("Released", na(d.get("Released"))),
        ("Director", na(d.get("Director"))),
        ("Synopsis", na(d.get("Plot"))),
    ]

    for key, val in fields:
        if val:
            new_lines.append(f"{pad}- {key}: {val} (IMDb)\n")

    actors = na(d.get("Actors"))
    if actors:
        new_lines.append(f"{pad}- Cast (IMDb):\n")
        cast_pad = " " * (indent + 8)
        for actor in actors.split(",")[:5]:
            new_lines.append(f"{cast_pad}- {actor.strip()}\n")

    if d.get("imdbID"):
        new_lines.append(f"{pad}- IMDB: https://www.imdb.com/title/{d['imdbID']}/\n")

    return new_lines


def find_all_unenriched(lines):
    """Find all movie entries that lack IMDb data. Returns [(idx, indent, title), ...]."""
    movies = []
    for i, line in enumerate(lines):
        m = TODO_RE.match(line.rstrip("\n"))
        if m:
            indent = len(m.group(1))
            title = m.group(3).strip()
            if not has_imdb_data(lines, i, indent):
                movies.append((i, indent, title))
    return movies


def main():
    api_key = os.environ.get("OMDB_API_KEY")
    if not api_key:
        print("OMDB_API_KEY environment variable not set")
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv

    lines = MOVIES_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    unenriched = find_all_unenriched(lines)

    print(f"Found {len(unenriched)} movies without IMDb data")
    if dry_run:
        print("(Dry run — no changes will be written)\n")
    print(f"API budget: ~{len(unenriched) * 2} calls needed, 1000/day limit\n")

    if len(unenriched) * 2 > 1000:
        print(f"WARNING: This needs {len(unenriched) * 2} API calls but limit is 1000/day.")
        print(f"Will process first 500 movies and stop.\n")

    enriched = 0
    skipped = 0
    failed = 0
    api_calls = 0
    offset = 0  # tracks line offset from insertions

    for i, (orig_idx, indent, title) in enumerate(unenriched):
        if api_calls >= 990:  # leave some buffer
            print(f"\nStopping: approaching daily API limit ({api_calls} calls used)")
            break

        idx = orig_idx + offset
        print(f"[{i+1}/{len(unenriched)}] {title}", end=" ", flush=True)

        try:
            results = omdb_search(api_key, title)
            api_calls += 1
        except Exception as e:
            err_str = str(e)
            if "401" in err_str or "limit" in err_str.lower():
                print(f"— rate limited, stopping")
                print(f"\nStopping: API rate limit reached ({api_calls} calls used)")
                break
            print(f"— search error: {e}")
            failed += 1
            time.sleep(DELAY)
            continue

        if not results:
            # Mark as N/A so we don't retry this movie
            pad = " " * (indent + 4)
            na_line = f"{pad}- IMDB: N/A\n"
            insert_at = find_insert_after(lines, idx, indent)
            if not dry_run:
                lines[insert_at:insert_at] = [na_line]
                offset += 1
            print("— not found (marked N/A)")
            skipped += 1
            time.sleep(DELAY)
            continue

        # Auto-match: exact title > first result
        match = results[0]
        exact = [r for r in results if r["Title"].lower() == title.lower()]
        if exact:
            match = exact[0]

        try:
            d = omdb_details(api_key, match["imdbID"])
            api_calls += 1
        except Exception as e:
            err_str = str(e)
            if "401" in err_str or "limit" in err_str.lower():
                print(f"— rate limited, stopping")
                print(f"\nStopping: API rate limit reached ({api_calls} calls used)")
                break
            print(f"— details error: {e}")
            failed += 1
            time.sleep(DELAY)
            continue

        if not d:
            print("— no details")
            skipped += 1
            time.sleep(DELAY)
            continue

        new_lines = build_imdb_lines(d, indent)
        if not new_lines:
            print("— no data")
            skipped += 1
            time.sleep(DELAY)
            continue

        insert_at = find_insert_after(lines, idx, indent)

        if not dry_run:
            lines[insert_at:insert_at] = new_lines
            offset += len(new_lines)

        enriched += 1
        na = lambda v: v if v and v != "N/A" else None
        year = na(d.get("Year")) or "?"
        rating = na(d.get("imdbRating")) or "?"
        print(f"— {d.get('Title')} ({year}) ★{rating} [+{len(new_lines)} lines]")

        time.sleep(DELAY)

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Enriched:  {enriched}")
    print(f"Skipped:   {skipped}")
    print(f"Failed:    {failed}")
    print(f"API calls: {api_calls}")

    if not dry_run and enriched > 0:
        MOVIES_FILE.write_text("".join(lines), encoding="utf-8")
        print(f"\nChanges written to {MOVIES_FILE}")
    elif dry_run:
        print(f"\nDry run complete. Run without --dry-run to apply.")


if __name__ == "__main__":
    main()
