#!/usr/bin/env python3
"""Auto-tag blog posts based on content keyword matching.

Usage:
    python auto_tag.py [file.md ...]    # tag specific files
    python auto_tag.py --check [file.md ...]  # check only, exit 1 if untagged
    python auto_tag.py --all            # re-tag all posts

Called by the pre-commit hook when blog posts are staged.
"""

import argparse
import re
import sys
from pathlib import Path

BLOG_DIR = Path(__file__).resolve().parent.parent

# Keywords → tags mapping. Each entry is (min_hits, [keywords]).
# min_hits: how many keywords must match to assign this tag.
# Use higher thresholds for broad/ambiguous tags.
TAG_KEYWORDS = {
    # Math subtopics (specific terms, 1 hit enough)
    "linear algebra": (1, ["linear algebra", "matrices", "vector space", "row reduction"]),
    "eigenvalue": (1, ["eigenvalue", "eigenvector", "eigenspace"]),
    "statistics": (1, ["statistics", "statistical", "hypothesis test", "p-value", "confidence interval"]),
    "probability": (1, ["probability", "probabilistic", "expected value", "random variable"]),
    "combinatorics": (1, ["combinatorics", "combinatorial", "binomial coefficient"]),
    "geometry": (1, ["geometry", "geometric", "polygon", "fractal", "tesselation"]),
    "number theory": (1, ["number theory", "prime number", "modular arithmetic"]),
    "dynamical systems": (1, ["dynamical system", "differential equation", "attractor"]),
    "calculus": (1, ["calculus", "derivative", "integral", "taylor series"]),
    "graph": (1, ["graph theory", "adjacency matrix", "vertex", "vertices"]),
    "math": (2, ["mathematic", "theorem", "proof", "lemma", "conjecture", "equation"]),

    # Music (specific terms)
    "music": (1, ["music", "album", "musician", "composer", "melody", "symphony"]),
    "concert": (1, ["concert", "live performance", "recital"]),
    "piano": (1, ["piano", "pianist"]),
    "cello": (1, ["cello", "cellist"]),
    "classical": (1, ["classical music", "baroque", "vivaldi", "beethoven", "mozart"]),

    # Tech (specific terms)
    "linux": (1, ["linux", "ubuntu", "gnome", "sudo apt"]),
    "bash": (1, ["#!/bin/bash", "bash script", "bash command"]),
    "python": (1, ["python3", "import numpy", "import pandas", ".py ", "pip install"]),
    "sage": (1, ["sagemath", "sage("]),

    # Teaching (2 hits to avoid false positives)
    "teaching": (2, ["teaching", "classroom", "students", "instructor", "syllabus", "lecture", "course"]),
    "education": (1, ["education", "curriculum", "pedagogy"]),

    # Life (2 hits — very broad)
    "life": (2, ["my life", "i've been", "personal", "recently"]),
    "philosophy": (1, ["philosophy", "philosophical", "epistemolog"]),
    "observation": (1, ["observation", "i noticed", "interesting pattern"]),
    "depression": (1, ["depression", "depressed", "mental health"]),
    "movie": (1, ["movie", "film", "cinema", "director"]),
    "book": (1, ["book review", "i read a book", "this book"]),
    "poetry": (1, ["poem", "poetry", "stanza"]),

    # Politics
    "politics": (1, ["politics", "political", "government", "democracy"]),
    "immigration": (1, ["immigration", "immigrant", "visa", "citizenship", "refugee"]),
    "racism": (1, ["racism", "racist", "racial discrimination"]),

    # Academic (2 hits — common words)
    "publication": (2, ["published", "journal", "accepted", "peer review"]),
    "paper": (1, ["our paper", "this paper", "the paper", "manuscript"]),
    "talk": (1, ["gave a talk", "seminar talk", "my talk", "invited talk"]),
    "conference": (1, ["conference", "workshop", "symposium"]),
    "academia": (2, ["academia", "academic", "university", "professor", "faculty", "department"]),

    # Finance
    "finance": (1, ["finance", "financial", "tax", "budget", "investment"]),

    # Other
    "health": (1, ["bpa", "bisphenol", "endocrine disruptor"]),
    "privacy": (1, ["privacy", "end-to-end encryption", "e2ee", "surveillance"]),
}


def get_existing_tags():
    """Get frequency map of all tags currently used across posts."""
    tag_freq = {}
    for f in BLOG_DIR.glob("*.md"):
        if not re.match(r"^\d{8}_", f.name):
            continue
        raw = f.read_text(encoding="utf-8")
        if not raw.startswith("---"):
            continue
        parts = raw.split("---", 2)
        if len(parts) < 3:
            continue
        for line in parts[1].strip().splitlines():
            if line.startswith("tags:"):
                tags = [t.strip().lower() for t in line.split(":", 1)[1].split(",") if t.strip()]
                for t in tags:
                    tag_freq[t] = tag_freq.get(t, 0) + 1
    return tag_freq


def suggest_tags(filepath):
    """Suggest tags for a post based on keyword matching."""
    raw = filepath.read_text(encoding="utf-8")
    content = raw.lower()

    # Parse existing tags
    existing = []
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if line.startswith("tags:"):
                    existing = [t.strip().lower() for t in line.split(":", 1)[1].split(",") if t.strip()]

    # Score each tag by keyword hits
    scores = {}
    for tag, (min_hits, keywords) in TAG_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw.lower() in content)
        if hits >= min_hits:
            scores[tag] = hits

    # Sort by score, take top tags
    suggested = sorted(scores, key=lambda t: -scores[t])

    # Limit to reasonable number (keep it to ~2-6 tags)
    if len(suggested) > 6:
        suggested = suggested[:6]

    # Ensure at least one broad category
    broad = {"math", "music", "linux", "teaching", "life", "politics", "publication", "finance"}
    if not any(t in broad for t in suggested) and not any(t in broad for t in existing):
        # Default to "life" for uncategorizable posts
        suggested.append("life")

    return existing, suggested


def has_tags(filepath):
    """Check if a post has tags in frontmatter."""
    raw = filepath.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return False
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return False
    return any(line.startswith("tags:") for line in parts[1].strip().splitlines())


def apply_tags(filepath, tags):
    """Write tags to post frontmatter."""
    raw = filepath.read_text(encoding="utf-8")
    tags_line = "tags: " + ", ".join(tags)

    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            lines = parts[1].strip().splitlines()
            new_lines = [l for l in lines if not l.startswith("tags:")]
            new_lines.append(tags_line)
            parts[1] = "\n" + "\n".join(new_lines) + "\n"
            filepath.write_text("---".join(parts), encoding="utf-8")
            return
    # No frontmatter
    filepath.write_text(f"---\n{tags_line}\n---\n{raw}", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Auto-tag blog posts")
    parser.add_argument("files", nargs="*", help="Specific .md files to tag")
    parser.add_argument("--check", action="store_true", help="Check only, exit 1 if untagged")
    parser.add_argument("--all", action="store_true", help="Re-tag all posts")
    parser.add_argument("--dry-run", action="store_true", help="Show suggestions without applying")
    args = parser.parse_args()

    if args.all:
        files = sorted(f for f in BLOG_DIR.glob("*.md") if re.match(r"^\d{8}_", f.name))
    elif args.files:
        files = [Path(f) for f in args.files if Path(f).exists()]
    else:
        # Default: find untagged posts
        files = [
            f for f in sorted(BLOG_DIR.glob("*.md"))
            if re.match(r"^\d{8}_", f.name) and not has_tags(f)
        ]

    if args.check:
        untagged = [f for f in files if not has_tags(f)]
        if untagged:
            print("Untagged blog posts:")
            for f in untagged:
                print(f"  {f.name}")
            print(f"\nRun: python {__file__} {' '.join(str(f) for f in untagged)}")
            sys.exit(1)
        sys.exit(0)

    if not files:
        print("No posts to tag.")
        return

    for f in files:
        existing, suggested = suggest_tags(f)
        # Merge: keep existing, add new suggestions
        merged = list(existing)
        for t in suggested:
            if t not in merged:
                merged.append(t)

        if merged == existing:
            continue

        if args.dry_run:
            added = [t for t in merged if t not in existing]
            print(f"{f.name}: +{', '.join(added)}" if added else f"{f.name}: no changes")
        else:
            apply_tags(f, merged)
            added = [t for t in merged if t not in existing]
            if added:
                print(f"{f.name}: added {', '.join(added)}")


if __name__ == "__main__":
    main()
