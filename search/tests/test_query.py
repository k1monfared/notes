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
     "d": "2024-01-03", "g": ["math"], "l": "en", "h": "", "a": "",
     "x": "eigenvalues of a matrix"},
]

VECS = array("b", [100, 0, 0, 0, 0, 100, 0, 0, 0, 0, 100, 0])
SCALES = (1.0, 1.0, 1.0)
DIM = 4


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
        hits = Q.vector_search(VECS, SCALES, DIM, [1.0, 0.0, 0.0, 0.0])
        self.assertEqual([idx for idx, _score in hits], [0])

    def test_weak_hits_dropped(self):
        hits = Q.vector_search(VECS, SCALES, DIM, [0.0, 0.0, 0.0, 1.0])
        self.assertEqual(hits, [])


class TestCap(unittest.TestCase):
    def test_results_capped(self):
        docs = [dict(DOCS[0], i=f"x#{i}", p=f"x{i}", t=f"post {i} zzz",
                     x="zzz zzz") for i in range(40)]
        kw = [(i, 1.0) for i in range(40)]
        out = Q.fuse(docs, kw, [], ["zzz"])
        self.assertEqual(len(out), Q.RESULT_CAP)


if __name__ == "__main__":
    unittest.main()
