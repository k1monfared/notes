"""Tests for the offline query path: AND fallback, vector floor, result cap."""

import unittest
from array import array

from search import query as Q

DOCS = [
    {"i": "a#0", "p": "a", "u": "a/", "t": "matrix tree theorem guide",
     "d": "2024-01-01", "g": ["math"], "l": "en", "h": "", "a": "",
     "x": "spanning trees and the matrix tree theorem proof"},
    {"i": "b#0", "p": "b", "u": "b/", "t": "cooking pasta",
     "d": "2024-01-02", "g": ["food"], "l": "en", "h": "", "a": "",
     "x": "boil water add salt"},
    {"i": "c#0", "p": "c", "u": "c/", "t": "linear algebra notes",
     "d": "2024-01-03", "g": ["math", "linear algebra"], "l": "en", "h": "", "a": "",
     "x": "eigenvalues of a matrix"},
    {"i": "d#0", "p": "d", "u": "d/", "t": "یک غزل بهاری",
     "d": "2023-05-05", "g": ["poem"], "l": "fa", "h": "", "a": "",
     "x": "شعر درباره بهار و شکوفه"},
]

VECS = array("b", [100, 0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 100, 0])
SCALES = (1.0, 1.0, 1.0, 1.0)
DIM = 5


class TestKeywordAnd(unittest.TestCase):
    def test_strict_and_keeps_only_full_matches(self):
        hits = Q.keyword_search(DOCS, ["matrix", "theorem"], min_and=1)
        self.assertEqual([idx for idx, _score in hits], [0])

    def test_fallback_to_or_when_and_is_thin(self):
        hits = Q.keyword_search(DOCS, ["matrix", "theorem"])
        idxs = [idx for idx, _score in hits]
        self.assertIn(0, idxs)
        self.assertIn(2, idxs)  # partial match rescued by OR fallback
        self.assertEqual(idxs[0], 0)

    def test_single_term_behaves(self):
        hits = Q.keyword_search(DOCS, ["pasta"])
        self.assertEqual([idx for idx, _score in hits], [1])


class TestVectorFloor(unittest.TestCase):
    def test_strong_hit_survives(self):
        hits = Q.vector_search(VECS, SCALES, DIM, [1.0, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual([idx for idx, _score in hits], [0])

    def test_weak_hits_dropped(self):
        hits = Q.vector_search(VECS, SCALES, DIM, [0.0, 0.0, 0.0, 0.0, 1.0])
        self.assertEqual(hits, [])


class TestOperators(unittest.TestCase):
    def test_parse(self):
        ops = Q.parse_query('+latex -book "tex editor" cooking')
        self.assertEqual(ops["must"], ["latex"])
        self.assertEqual(ops["not"], ["book"])
        self.assertEqual(ops["phrases"], ["tex editor"])
        self.assertIn("cooking", ops["engine_terms"])
        self.assertNotIn("book", ops["vector_text"])

    def test_must_excludes(self):
        ops = Q.parse_query("+matrix -theorem")
        kw = Q.keyword_search(DOCS, ops["engine_terms"], min_and=1)
        out = Q.fuse(DOCS, kw, [], ops["positives"], ops)
        self.assertEqual([DOCS[i]["p"] for i, _e in out], ["c"])

    def test_phrase_requires_adjacency(self):
        ops = Q.parse_query('"trees theorem"')
        kw = Q.keyword_search(DOCS, ops["engine_terms"], min_and=1)
        out = Q.fuse(DOCS, kw, [], ops["positives"], ops)
        self.assertEqual(out, [])
        ops2 = Q.parse_query('"tree theorem"')
        kw2 = Q.keyword_search(DOCS, ops2["engine_terms"], min_and=1)
        out2 = Q.fuse(DOCS, kw2, [], ops2["positives"], ops2)
        self.assertEqual([DOCS[i]["p"] for i, _e in out2], ["a"])


class TestFacets(unittest.TestCase):
    def test_parse_facets(self):
        ops = Q.parse_query("tag:math lang:FA after:2024 before:2025")
        self.assertEqual(ops["tags"], ["math"])
        self.assertEqual(ops["langs"], ["fa"])
        self.assertEqual(ops["after"], "2024-01-01")
        self.assertEqual(ops["before"], "2025-01-01")
        self.assertEqual(ops["engine_terms"], [])

    def test_parse_quoted_tag_and_negation(self):
        ops = Q.parse_query('tag:"linear algebra" -tag:food after:soon')
        self.assertEqual(ops["tags"], ["linear algebra"])
        self.assertEqual(ops["not_tags"], ["food"])
        self.assertIsNone(ops["after"])
        self.assertIn("after", ops["engine_terms"])

    def _titles(self, query):
        ops = Q.parse_query(query)
        kw = Q.keyword_search(DOCS, ops["engine_terms"], min_and=1)
        out = Q.fuse(DOCS, kw, [], ops["positives"], ops)
        return sorted(DOCS[i]["t"] for i, _e in out)

    def _browse(self, query):
        ops = Q.parse_query(query)
        out = Q.fuse(DOCS, [], [], ops["positives"], ops)
        return sorted(DOCS[i]["t"] for i, _e in out)

    def test_tag_scopes(self):
        self.assertEqual(self._titles("tag:math"),
                         ["linear algebra notes", "matrix tree theorem guide"])

    def test_quoted_tag(self):
        self.assertEqual(self._titles('tag:"linear algebra"'),
                         ["linear algebra notes"])

    def test_lang_scopes(self):
        self.assertEqual(self._titles("lang:fa"), ["یک غزل بهاری"])

    def test_dates(self):
        self.assertEqual(len(self._browse("after:2024")), 3)
        self.assertEqual(self._browse("before:2024"), ["یک غزل بهاری"])

    def test_facet_with_terms(self):
        self.assertEqual(self._titles("matrix tag:math"),
                         ["linear algebra notes", "matrix tree theorem guide"])


class TestCap(unittest.TestCase):
    def test_results_capped(self):
        docs = [dict(DOCS[0], i=f"x#{i}", p=f"x{i}", t=f"post {i} zzz",
                     x="zzz zzz") for i in range(40)]
        kw = [(i, 1.0) for i in range(40)]
        out = Q.fuse(docs, kw, [], ["zzz"])
        self.assertEqual(len(out), Q.RESULT_CAP)


if __name__ == "__main__":
    unittest.main()
