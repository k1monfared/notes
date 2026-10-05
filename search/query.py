"""Offline search tester. Mimics the Worker/browser hybrid on this machine.

Loads a built source (docs.json + vectors.bin), embeds the query with the
local ONNX backend, scores keyword and vector arms, fuses with RRF, and prints
ranked posts. Needs no internet once the embedding model is cached, and talks
to neither GitHub nor Cloudflare.

Keyword scoring here is a close approximation of the browser MiniSearch setup
(same fields, boosts, prefix matching), not bit-identical. The fusion math
(RRF weights, title and recency boosts) matches search.js and the Worker.

Only sources built with the local backend can be queried this way; cloudflare
vectors live in a different space.
"""

import argparse
import json
import math
import re
import struct
import sys
import unicodedata
from array import array
from datetime import datetime, timezone
from pathlib import Path

from .config import (
    MODEL_DTYPE,
    MODEL_ID,
    QUERY_PREFIX,
    REPO_ROOT,
)
from .embed import _run_node_embedder, embedder_available
from .text import normalize_persian

RRF_K = 60
KW_WEIGHT = 1.0
VEC_WEIGHT = 1.15
FIELD_BOOSTS = (("t", 3.0), ("h", 2.0), ("g", 2.0), ("x", 1.0))
MIN_AND_RESULTS = 5
VECTOR_FLOOR = 0.7
RESULT_CAP = 30


def split_terms(text):
    """Split roughly like the browser tokenizer: separators, punctuation,
    symbols are boundaries."""
    text = normalize_persian(unicodedata.normalize("NFKC", text)).lower()
    terms, current = [], []
    for ch in text:
        if unicodedata.category(ch)[0] in ("Z", "P", "S") or ch.isspace():
            if current:
                terms.append("".join(current))
                current = []
        else:
            current.append(ch)
    if current:
        terms.append("".join(current))
    return [t for t in terms if t]


def load_index(index_dir):
    index_dir = Path(index_dir)
    manifest = json.loads((index_dir / "manifest.json").read_text(encoding="utf-8"))
    vectors_meta = manifest.get("vectors") or {}
    if vectors_meta.get("backend", "local") != "local":
        raise SystemExit(
            f"index was built with backend '{vectors_meta.get('backend')}', "
            "this tool only reads local-backend vectors"
        )
    docs = json.loads((index_dir / "docs.json").read_text(encoding="utf-8"))

    raw = (index_dir / vectors_meta["file"]).read_bytes()
    if raw[:4] != b"NSEV":
        raise SystemExit("bad vectors file")
    _version, count, dim = struct.unpack("<III", raw[4:16])
    off = 16
    scales = struct.unpack(f"<{count}f", raw[off:off + 4 * count])
    off += 4 * count
    vecs = array("b")
    vecs.frombytes(raw[off:off + count * dim])
    return docs, vecs, scales, dim


def keyword_search(docs, terms, limit=50, min_and=MIN_AND_RESULTS):
    scored = []
    for idx, doc in enumerate(docs):
        score = 0.0
        matched = set()
        fields = {
            "t": doc.get("t", ""),
            "h": doc.get("h", ""),
            "g": " ".join(doc.get("g", [])),
            "x": doc.get("x", ""),
        }
        for field, boost in FIELD_BOOSTS:
            tokens = split_terms(fields[field])
            for term in terms:
                if term in tokens:
                    score += boost
                    matched.add(term)
                elif any(tok.startswith(term) for tok in tokens):
                    score += boost * 0.5
                    matched.add(term)
        if score > 0:
            scored.append((idx, score, matched))
    pool = scored
    if terms:
        anded = [item for item in scored if len(item[2]) >= len(terms)]
        if len(anded) >= min_and:
            pool = anded
    else:
        pool = []
    pool.sort(key=lambda item: item[1], reverse=True)
    return [(idx, score) for idx, score, _matched in pool[:limit]]


def vector_search(vecs, scales, dim, query_vec, limit=50,
                  floor=VECTOR_FLOOR):
    scores = []
    for row in range(len(scales)):
        base = row * dim
        dot = sum(vecs[base + i] * query_vec[i] for i in range(dim))
        sim = scales[row] * dot
        if sim >= floor:
            scores.append((row, sim))
    scores.sort(key=lambda item: item[1], reverse=True)
    return scores[:limit]


def fuse(docs, keyword, vector, terms, ops=None):
    fused = {}

    def add(idx, rank, arm, weight):
        entry = fused.setdefault(idx, {"score": 0.0, "arms": set()})
        entry["score"] += weight / (RRF_K + rank + 1)
        entry["arms"].add(arm)

    for rank, (idx, _score) in enumerate(keyword):
        add(idx, rank, "kw", KW_WEIGHT)
    for rank, (idx, _score) in enumerate(vector):
        add(idx, rank, "vec", VEC_WEIGHT)

    now = datetime.now(timezone.utc).timestamp()
    ranked = []
    for idx, entry in fused.items():
        doc = docs[idx]
        title = " ".join(split_terms(doc.get("t", "")))
        hits = sum(1 for t in terms if t in title)
        if terms and hits == len(terms):
            entry["score"] *= 3.0
        elif hits:
            entry["score"] *= 1.2
        try:
            when = datetime.strptime(doc["d"], "%Y-%m-%d").replace(
                tzinfo=timezone.utc).timestamp()
            years = max(0.0, (now - when) / (365.25 * 24 * 3600))
            entry["score"] *= 1.0 / (1.0 + 0.03 * years)
        except (KeyError, ValueError):
            pass
        ranked.append((idx, entry))

    ranked.sort(key=lambda item: item[1]["score"], reverse=True)
    if ops is not None:
        ranked = [(idx, entry) for idx, entry in ranked
                  if chunk_matches_ops(docs[idx], ops)]

    seen, out = set(), []
    for idx, entry in ranked:
        post = docs[idx]["p"]
        if post in seen:
            continue
        seen.add(post)
        entry["semantic"] = "vec" in entry["arms"] and "kw" not in entry["arms"]
        out.append((idx, entry))
        if len(out) >= RESULT_CAP:
            break
    return out


def parse_query(text):
    """Split a query into +must / -not / "exact phrase" / optional words.

    Mirrors parseSearchQuery in search.js and the Worker.
    """
    must, not_, phrases, not_phrases, optional = [], [], [], [], []

    def push_word(word, target):
        target.extend(split_terms(word))

    pattern = re.compile(r'([+-]?)"([^"]+)"|([+-]?)(\S+)')
    for match in pattern.finditer(text):
        if match.group(2) is not None:
            joined = " ".join(split_terms(match.group(2)))
            if not joined:
                continue
            if match.group(1) == "-":
                if " " in joined:
                    not_phrases.append(joined)
                else:
                    push_word(joined, not_)
            elif " " in joined:
                phrases.append(joined)
            else:
                push_word(joined, must)
        elif match.group(3) == "+":
            push_word(match.group(4), must)
        elif match.group(3) == "-":
            push_word(match.group(4), not_)
        else:
            push_word(match.group(4), optional)

    def dedup(words):
        return list(dict.fromkeys(words))

    phrase_words = [w for p in phrases for w in p.split(" ")]
    engine_terms = dedup(must + optional + phrase_words)
    return {
        "must": dedup(must),
        "not": dedup(not_),
        "phrases": dedup(phrases),
        "not_phrases": dedup(not_phrases),
        "positives": [t for t in engine_terms if len(t) > 1],
        "engine_terms": engine_terms,
        "vector_text": " ".join(dedup(must + optional + phrases)),
    }


def chunk_matches_ops(doc, ops):
    fields = [doc.get("t", ""), doc.get("h", ""),
              " ".join(doc.get("g", [])), doc.get("x", "")]
    tokens = set()
    parts = []
    for field in fields:
        tks = split_terms(field)
        tokens.update(tks)
        parts.append(" ".join(tks))
    joined = " ".join(parts)
    if any(m not in tokens for m in ops["must"]):
        return False
    if any(n in tokens for n in ops["not"]):
        return False
    if any(p not in joined for p in ops["phrases"]):
        return False
    if any(p in joined for p in ops["not_phrases"]):
        return False
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline search tester")
    parser.add_argument("--index-dir", default=None,
                        help="Directory with docs.json/vectors.bin "
                             "(default: blog/_site/search)")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--mode", default="hybrid",
                        choices=("hybrid", "keyword", "vector"))
    args = parser.parse_args(argv)

    index_dir = Path(args.index_dir) if args.index_dir else (
        REPO_ROOT / "blog" / "_site" / "search")
    docs, vecs, scales, dim = load_index(index_dir)

    ops = parse_query(args.query)
    terms = ops["positives"]
    keyword = keyword_search(docs, ops["engine_terms"]) \
        if args.mode != "vector" else []

    vector = []
    if args.mode != "keyword" and ops["vector_text"]:
        if not embedder_available():
            print("local embedder unavailable; falling back to keyword",
                  file=sys.stderr)
        else:
            query_vec = _run_node_embedder(
                [ops["vector_text"]], QUERY_PREFIX, MODEL_ID, MODEL_DTYPE)[0]
            vector = vector_search(vecs, scales, dim, query_vec)

    if args.mode == "hybrid":
        results = fuse(docs, keyword, vector, terms, ops)
    elif args.mode == "vector":
        results = fuse(docs, [], vector, terms, ops)
    else:
        results = fuse(docs, keyword, [], terms, ops)

    for n, (idx, entry) in enumerate(results[:args.top], 1):
        doc = docs[idx]
        arms = "+".join(sorted(entry["arms"]))
        tag = " [AI]" if entry["semantic"] else ""
        print(f"{n}. [{doc['d']}] {doc['t']}{tag}")
        print(f"   {doc['u']}  score={entry['score']:.4f} arms={arms}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
