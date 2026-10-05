"""Notes search engine.

A source-agnostic, fully static (no server) hybrid search engine. Each content
type (blog, movies, books, ...) contributes an adapter that yields documents.
The pipeline cleans, chunks, and indexes those documents into compact artifacts
that the browser runtime consumes.
"""

__version__ = "0.1.0"
