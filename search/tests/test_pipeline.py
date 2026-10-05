"""Tests for the index pipeline: chunks, artifacts, manifest, backends."""

import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from search import pipeline as P


class TestChunkPost(unittest.TestCase):
    def test_fields_and_ids(self):
        post = {
            "id": "20200101-hello",
            "title": "Hello world",
            "date": "2020-01-01",
            "url": "20200101-hello/",
            "tags": ["test"],
            "lang": "en",
            "content": "# Hello world\n\nFirst paragraph here with enough words.\n\n## Part two\n\nSecond part here with enough words too.",
        }
        docs = P.chunk_post(post)
        self.assertGreaterEqual(len(docs), 2)
        for n, doc in enumerate(docs):
            self.assertEqual(doc["i"], f"20200101-hello#{n}")
            for key in ("p", "u", "t", "d", "g", "l", "h", "a", "x"):
                self.assertIn(key, doc)
        headings = {d["h"] for d in docs}
        self.assertIn("Part two", headings)

    def test_empty_post_falls_back_to_title(self):
        post = {
            "id": "x", "title": "Just a title", "date": "2020-01-01",
            "url": "x/", "tags": [], "lang": "en", "content": "",
        }
        docs = P.chunk_post(post)
        self.assertEqual(len(docs), 1)
        self.assertIn("Just a title", docs[0]["x"])


class TestResolveBackend(unittest.TestCase):
    def test_local(self):
        model, _dtype, qpre, ppre = P.resolve_backend("local")
        self.assertIn("e5-small", model)
        self.assertTrue(qpre.startswith("query:"))

    def test_cloudflare(self):
        model, _dtype, qpre, _ppre = P.resolve_backend("cloudflare")
        self.assertTrue(model.startswith("@cf/"))
        # bge queries carry an instruction; documents stay unprefixed.
        self.assertIn("passages", qpre)


class TestBuildSource(unittest.TestCase):
    def _manifest(self, out):
        return json.loads((Path(out) / "manifest.json").read_text())

    def test_keyword_only_writes_index_without_vectors(self):
        with TemporaryDirectory() as tmp:
            manifest = P.build_source("blog", out_dir=tmp, embed=False,
                                      verbose=False)
            self.assertIsNone(manifest["vectors"])
            docs = json.loads((Path(tmp) / "docs.json").read_text())
            self.assertGreater(len(docs), 100)
            self.assertFalse((Path(tmp) / "vectors.bin").exists())

    def test_no_embed_removes_stale_vectors(self):
        # Regression: a keyword-only rebuild must not ship rows that no
        # longer align with docs.json.
        with TemporaryDirectory() as tmp:
            stale = Path(tmp) / "vectors.bin"
            stale.write_bytes(b"stale-bytes")
            P.build_source("blog", out_dir=tmp, embed=False, verbose=False)
            self.assertFalse(stale.exists())

    def test_content_hash_matches_docs(self):
        with TemporaryDirectory() as tmp:
            manifest = P.build_source("blog", out_dir=tmp, embed=False,
                                      verbose=False)
            docs_bytes = (Path(tmp) / "docs.json").read_bytes()
            digest = hashlib.md5(docs_bytes).hexdigest()
            self.assertEqual(manifest["content"], digest)

    def test_manifest_schema(self):
        with TemporaryDirectory() as tmp:
            manifest = P.build_source("blog", out_dir=tmp, embed=False,
                                      verbose=False)
            for key in ("schema", "source", "generated", "content", "counts",
                        "model", "vectors", "fields"):
                self.assertIn(key, manifest)
            self.assertEqual(manifest["source"], "blog")
            self.assertIn("query_prefix", manifest["model"])


if __name__ == "__main__":
    unittest.main()
