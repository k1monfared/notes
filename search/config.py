"""Shared configuration for the search engine."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SEARCH_DIR = REPO_ROOT / "search"
RUNTIME_DIR = SEARCH_DIR / "runtime"
CACHE_DIR = SEARCH_DIR / ".cache"
SOURCES_FILE = SEARCH_DIR / "sources.yml"

# Bump when the emitted document/manifest format changes in a breaking way.
SCHEMA_VERSION = 1

# Single embedding model for every source, so one query vector works across all
# of them. Used from Phase 3 onward (build and browser use the same ONNX model).
MODEL_ID = "Xenova/multilingual-e5-small"
MODEL_DIM = 384
MODEL_DTYPE = "q8"
QUERY_PREFIX = "query: "
PASSAGE_PREFIX = "passage: "

# Cloudflare backend: query and document embeddings both come from Workers AI,
# so the model must be one it hosts. bge-m3 is multilingual (100+ languages).
CF_MODEL_ID = "@cf/baai/bge-m3"
CF_QUERY_PREFIX = ""
CF_PASSAGE_PREFIX = ""

# Chunking
MAX_CHUNK_CHARS = 1400
MIN_CHUNK_LETTERS = 15
