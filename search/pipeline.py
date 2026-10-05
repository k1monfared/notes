"""Build search artifacts for a source.

    extract -> clean -> chunk -> emit (docs.json, manifest.json)

Embeddings (Phase 3) will slot in after chunking, keyed by the same content
hash so only new or changed posts are re-embedded. For now the emitted
docs.json is the full keyword index payload; the browser builds MiniSearch
from it.
"""

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .adapters import get_adapter
from .config import (
    CACHE_DIR,
    CF_MODEL_ID,
    CF_PASSAGE_PREFIX,
    CF_QUERY_PREFIX,
    MAX_CHUNK_CHARS,
    MIN_CHUNK_LETTERS,
    MODEL_DIM,
    MODEL_DTYPE,
    MODEL_ID,
    PASSAGE_PREFIX,
    QUERY_PREFIX,
    REPO_ROOT,
    RUNTIME_DIR,
    SCHEMA_VERSION,
    SOURCES_FILE,
)
from .embed import EmbeddingUnavailable, embed_with_cache, write_vectors
from .text import normalize_text, sectionize, split_long, strip_markdown

INDEXED_FIELDS = ["t", "h", "g", "x"]
STORED_FIELDS = ["p", "u", "t", "d", "g", "l", "h", "a", "x"]


def _load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8")


def load_sources():
    return yaml.safe_load(SOURCES_FILE.read_text(encoding="utf-8")) or {}


def _count_letters(text):
    return sum(1 for c in text if c.isalnum())


def chunk_post(post):
    """Turn one source document into a list of chunk documents."""
    sections = sectionize(post["content"])
    chunks = []
    for heading, anchor, body in sections:
        clean = normalize_text(strip_markdown(body))
        if _count_letters(clean) < MIN_CHUNK_LETTERS:
            continue
        for piece in split_long(clean, MAX_CHUNK_CHARS):
            chunks.append((heading, anchor, piece))

    if not chunks:
        chunks.append(("", "", normalize_text(post["title"])))

    docs = []
    for n, (heading, anchor, text) in enumerate(chunks):
        docs.append({
            "i": f'{post["id"]}#{n}',
            "p": post["id"],
            "u": post["url"],
            "t": post["title"],
            "d": post["date"],
            "g": post["tags"],
            "l": post["lang"],
            "h": heading,
            "a": anchor,
            "x": text,
        })
    return docs


def _post_hash(post):
    h = hashlib.md5()
    for part in (post["title"], post["date"], ",".join(post["tags"]), post["content"]):
        h.update(part.encode("utf-8"))
    return h.hexdigest()


def _pipeline_fingerprint():
    """Hash of the pipeline source, so cached chunks are dropped when the
    cleaning/chunking logic changes."""
    h = hashlib.md5()
    for path in sorted(Path(__file__).parent.rglob("*.py")):
        h.update(path.read_bytes())
    return h.hexdigest()


def resolve_backend(backend):
    """Map a backend name to (model, dtype, query_prefix, passage_prefix)."""
    if backend == "cloudflare":
        return CF_MODEL_ID, "api", CF_QUERY_PREFIX, CF_PASSAGE_PREFIX
    return MODEL_ID, MODEL_DTYPE, QUERY_PREFIX, PASSAGE_PREFIX


def build_source(name, out_dir=None, force=False, verbose=True, embed=True,
                 backend="local"):
    """Build search artifacts for one source. Returns the manifest dict."""
    sources = load_sources().get("sources", {})
    if name not in sources:
        raise KeyError(f"Source '{name}' not found in {SOURCES_FILE}")
    spec = sources[name]

    adapter = get_adapter(spec["adapter"])
    config = spec.get("config", {})
    out = Path(out_dir) if out_dir else (REPO_ROOT / spec["out"])
    out.mkdir(parents=True, exist_ok=True)

    cache_path = CACHE_DIR / f"{name}.json"
    fingerprint = _pipeline_fingerprint()
    cache = {} if force else _load_json(cache_path, {})
    if cache.get("_fingerprint") not in (None, fingerprint):
        cache = {}

    new_cache = {"_fingerprint": fingerprint, "posts": {}}
    docs = []
    post_count = 0
    reused = 0

    cached_posts = cache.get("posts", {})
    for post in adapter.iter_documents(config):
        post_count += 1
        ph = _post_hash(post)
        cached = cached_posts.get(post["id"])
        if cached and cached.get("hash") == ph and cached.get("docs"):
            post_docs = cached["docs"]
            reused += 1
        else:
            post_docs = chunk_post(post)
        new_cache["posts"][post["id"]] = {"hash": ph, "docs": post_docs}
        docs.extend(post_docs)

    docs.sort(key=lambda d: (d["d"], d["i"]), reverse=True)

    model, dtype, query_prefix, passage_prefix = resolve_backend(backend)
    api_url = (load_sources().get("api", {}) or {}).get("search", "")

    vectors_meta = None
    if embed and docs:
        try:
            embedded = embed_with_cache(
                [d["x"] for d in docs], passage_prefix, model, dtype,
                backend=backend,
            )
            dim = len(embedded[0][0])
            vectors_meta = {"file": "vectors.bin", "dtype": "int8",
                            "dim": dim, "count": len(embedded),
                            "model": model, "backend": backend,
                            "api": api_url if backend == "cloudflare" else ""}
            # Write vectors before docs so a partial run never leaves docs
            # pointing at a stale/missing vector file.
            write_vectors(out / "vectors.bin", embedded, dim)
            if verbose:
                print(f"Embedded {len(embedded)} chunks with {model}")
        except Exception as exc:  # noqa: BLE001
            # Never let an embedding failure take down the keyword index:
            # docs.json and the manifest below are still written.
            vectors_meta = None
            if verbose:
                print(f"Embeddings skipped: {exc}")
    elif not embed:
        # Keyword-only builds must not ship a stale vector file whose rows no
        # longer align with docs.json.
        stale = out / "vectors.bin"
        if stale.exists():
            stale.unlink()

    docs_text = json.dumps(docs, ensure_ascii=False, separators=(",", ":"))
    (out / "docs.json").write_text(docs_text, encoding="utf-8")

    manifest = {
        "schema": SCHEMA_VERSION,
        "source": name,
        "title": spec.get("title", name),
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "content": hashlib.md5(docs_text.encode("utf-8")).hexdigest(),
        "counts": {"posts": post_count, "chunks": len(docs)},
        "model": {
            "id": model,
            "dim": vectors_meta["dim"] if vectors_meta else MODEL_DIM,
            "query_prefix": query_prefix,
            "passage_prefix": passage_prefix,
        },
        "vectors": vectors_meta,
        "fields": {"indexed": INDEXED_FIELDS, "stored": STORED_FIELDS},
    }
    _write_json(out / "manifest.json", manifest)

    _write_json(cache_path, new_cache)

    if verbose:
        print(f"Search index [{name}]: {post_count} posts, {len(docs)} chunks "
              f"({reused} reused from cache) -> {out}")

    return manifest


def copy_runtime(dest):
    """Copy the shared browser runtime into a site's search directory."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for src in RUNTIME_DIR.iterdir():
        if src.is_file():
            shutil.copy2(src, dest / src.name)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build search artifacts")
    parser.add_argument("--source", required=True, help="Source name from sources.yml")
    parser.add_argument("--out", default=None, help="Override output directory")
    parser.add_argument("--force", action="store_true", help="Ignore the cache")
    parser.add_argument("--no-embed", action="store_true", help="Skip embeddings")
    parser.add_argument("--backend", default="local",
                        choices=("local", "cloudflare"),
                        help="Embedding backend (default: local)")
    args = parser.parse_args(argv)

    try:
        sys.path.insert(0, str(REPO_ROOT))
        build_source(args.source, out_dir=args.out, force=args.force,
                     embed=not args.no_embed, backend=args.backend)
    except Exception as exc:  # noqa: BLE001
        print(f"Search build failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
