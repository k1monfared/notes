"""Build-time embeddings.

Documents are embedded in Node (Transformers.js) using the same ONNX model the
browser runtime uses, so build-time and query-time vectors share one space.
Vectors are quantized to int8 with a per-vector scale and written into a small
binary file the browser can decode without any libraries.

If Node or the embedder is unavailable, embedding is skipped and the build
degrades cleanly to keyword-only search.
"""

import base64
import hashlib
import json
import math
import os
import shutil
import struct
import subprocess
import urllib.error
import urllib.request
from array import array
from pathlib import Path

from .config import (
    CACHE_DIR,
    CF_MODEL_ID,
    MODEL_DTYPE,
    MODEL_ID,
    SEARCH_DIR,
)

NODE_DIR = SEARCH_DIR / "node"
NODE_SCRIPT = NODE_DIR / "embed.mjs"
MODEL_CACHE = NODE_DIR / ".models"
TRANSFORMERS_PKG = NODE_DIR / "node_modules" / "@huggingface" / "transformers"


class EmbeddingUnavailable(RuntimeError):
    """Raised when the Node embedder cannot be used."""


def embedder_available():
    return (
        shutil.which("node") is not None
        and NODE_SCRIPT.exists()
        and TRANSFORMERS_PKG.is_dir()
    )


def _text_key(prefix, text):
    return hashlib.md5((prefix + text).encode("utf-8")).hexdigest()


def _quantize(vector):
    peak = max((abs(x) for x in vector), default=0.0)
    scale = (peak / 127.0) if peak > 0 else 1.0
    quantized = array("b", (max(-127, min(127, int(round(x / scale)))) for x in vector))
    return quantized, scale


def _cache_path(model, dtype):
    slug = model.replace("/", "_").replace(":", "_")
    return CACHE_DIR / f"embed-{slug}-{dtype}.json"


def _load_embed_cache(model, dtype):
    try:
        return json.loads(_cache_path(model, dtype).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_embed_cache(model, dtype, cache):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(model, dtype).write_text(json.dumps(cache), encoding="utf-8")


def _normalize_rows(vectors):
    """L2-normalize every row so cosine is a plain dot product."""
    out = []
    for row in vectors:
        norm = math.sqrt(sum(x * x for x in row))
        if norm > 0:
            out.append([x / norm for x in row])
        else:
            out.append(list(row))
    return out


def _cf_embed(texts, model):
    """Embed raw texts through the Workers AI REST API.

    Requires CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN in the
    environment. Returns a list of unit-norm float lists.
    """
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if not account_id or not token:
        raise EmbeddingUnavailable(
            "cloudflare backend needs CLOUDFLARE_ACCOUNT_ID and "
            "CLOUDFLARE_API_TOKEN"
        )

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    vectors = []
    for start in range(0, len(texts), 32):
        batch = texts[start:start + 32]
        body = json.dumps({"text": batch}).encode("utf-8")
        req = urllib.request.Request(
            url, data=body,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = json.loads(resp.read())
        except urllib.error.URLError as exc:
            raise EmbeddingUnavailable(f"workers AI request failed: {exc}") from exc
        if not payload.get("success", False):
            errors = payload.get("errors", [{"message": "unknown error"}])
            raise EmbeddingUnavailable(f"workers AI error: {errors[0].get('message')}")
        result = payload["result"]
        data = result["data"]
        shape = result.get("shape", [])
        if shape and len(shape) == 2:
            dim = shape[1]
            rows = [data[i * dim:(i + 1) * dim] for i in range(shape[0])]
        else:
            rows = [data] if data and isinstance(data[0], (int, float)) else data
        vectors.extend(_normalize_rows(rows))
    return vectors


def _run_node_embedder(texts, prefix, model, dtype):
    """Embed raw texts through embed.mjs. Returns a list of float lists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_in = CACHE_DIR / "_embed_in.json"
    tmp_out = CACHE_DIR / "_embed_out.json"
    tmp_in.write_text(json.dumps(texts, ensure_ascii=False), encoding="utf-8")

    cmd = [
        "node", str(NODE_SCRIPT),
        "--model", model,
        "--prefix", prefix,
        "--input", str(tmp_in),
        "--output", str(tmp_out),
        "--dtype", dtype,
        "--cache", str(MODEL_CACHE),
    ]
    try:
        proc = subprocess.run(cmd, cwd=str(NODE_DIR), capture_output=True, text=True)
    except OSError as exc:
        raise EmbeddingUnavailable(str(exc)) from exc
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()[-4:]
        raise EmbeddingUnavailable(" | ".join(tail) or "node embedder failed")

    vectors = json.loads(tmp_out.read_text(encoding="utf-8"))
    for tmp in (tmp_in, tmp_out):
        try:
            tmp.unlink()
        except OSError:
            pass
    return vectors


def embed_with_cache(texts, prefix, model=MODEL_ID, dtype=MODEL_DTYPE,
                     backend="local"):
    """Return [(int8 array, scale), ...] aligned with `texts`, using a cache.

    backend "local" uses the Node/ONNX embedder (works offline once the model
    is cached). backend "cloudflare" uses the Workers AI REST API and needs
    CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN.

    Raises EmbeddingUnavailable if the backend cannot be used.
    """
    if backend == "cloudflare":
        get_vectors = lambda missing: _cf_embed(  # noqa: E731
            [prefix + t for t in missing], model)
    else:
        if not embedder_available():
            raise EmbeddingUnavailable("node embedder not installed")
        get_vectors = lambda missing: _run_node_embedder(  # noqa: E731
            missing, prefix, model, dtype)

    cache = _load_embed_cache(model, dtype)
    results = [None] * len(texts)
    keys = [_text_key(prefix, t) for t in texts]

    missing_texts = []
    missing_positions = []
    for i, (key, text) in enumerate(zip(keys, texts)):
        entry = cache.get(key)
        if entry:
            quantized = array("b")
            quantized.frombytes(base64.b64decode(entry["q"]))
            results[i] = (quantized, entry["s"])
        else:
            missing_texts.append(text)
            missing_positions.append(i)

    if missing_texts:
        vectors = get_vectors(missing_texts)
        for pos, vector in zip(missing_positions, vectors):
            quantized, scale = _quantize(vector)
            cache[keys[pos]] = {
                "q": base64.b64encode(quantized.tobytes()).decode("ascii"),
                "s": scale,
            }
            results[pos] = (quantized, scale)
        _save_embed_cache(model, dtype, cache)

    return results


def write_vectors(path, embedded, dim):
    """Write the int8 vectors plus scales to a compact binary file.

    Layout: magic 'NSEV' (4) | version u32 | count u32 | dim u32 |
            scales float32[count] | vectors int8[count * dim]
    """
    count = len(embedded)
    scales = array("f", (scale for _vec, scale in embedded))
    data = array("b")
    for vec, _scale in embedded:
        data.extend(vec)

    with open(path, "wb") as fh:
        fh.write(b"NSEV")
        fh.write(struct.pack("<III", 1, count, dim))
        fh.write(scales.tobytes())
        fh.write(data.tobytes())
