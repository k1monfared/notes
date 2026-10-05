"""Adapter registry.

An adapter is a module exposing `iter_documents(config) -> Iterator[dict]`.
Each yielded document is:

    {
        "id": str,       # stable id, unique within the source
        "title": str,
        "date": str,     # ISO YYYY-MM-DD
        "url": str,      # relative URL (resolved against the page <base href>)
        "tags": [str],
        "lang": str,     # "en" | "fa" | ...
        "content": str,  # markdown or plain text, title heading removed
    }
"""

from . import blog

_ADAPTERS = {
    "blog": blog,
}


def get_adapter(name):
    if name not in _ADAPTERS:
        raise KeyError(f"Unknown adapter: {name}")
    return _ADAPTERS[name]
