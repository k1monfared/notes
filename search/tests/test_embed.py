"""Tests for embedding helpers: API parsing, quantization, binary layout."""

import base64
import json
import math
import struct
import unittest
from array import array
from pathlib import Path
from tempfile import TemporaryDirectory

from search import embed as E


class FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self._payload).encode()


def fake_urlopen(payload):
    return lambda req, timeout=None: FakeResp(payload)


class TestCfParsing(unittest.TestCase):
    def setUp(self):
        import os
        import urllib.request
        self._real = urllib.request.urlopen
        os.environ["CLOUDFLARE_ACCOUNT_ID"] = "test"
        os.environ["CLOUDFLARE_API_TOKEN"] = "test"

    def tearDown(self):
        import os
        import urllib.request
        urllib.request.urlopen = self._real
        os.environ.pop("CLOUDFLARE_ACCOUNT_ID", None)
        os.environ.pop("CLOUDFLARE_API_TOKEN", None)

    def _patch(self, payload):
        import urllib.request
        urllib.request.urlopen = fake_urlopen(payload)

    def test_nested_rows(self):
        # Regression: Workers AI returns data as nested rows, not flat.
        self._patch({"success": True,
                     "result": {"shape": [2, 3],
                                "data": [[0.1, 0.2, 0.2], [0.5, 0.1, 0.1]]}})
        vecs = E._cf_embed(["a", "b"], "m")
        self.assertEqual(len(vecs), 2)
        for row in vecs:
            self.assertAlmostEqual(math.sqrt(sum(x * x for x in row)), 1.0)

    def test_flat_row(self):
        self._patch({"success": True,
                     "result": {"shape": [1, 2], "data": [0.6, 0.8]}})
        vecs = E._cf_embed(["a"], "m")
        self.assertEqual(len(vecs), 1)
        self.assertAlmostEqual(vecs[0][0], 0.6, places=4)
        self.assertAlmostEqual(vecs[0][1], 0.8, places=4)

    def test_error_raises(self):
        self._patch({"success": False, "errors": [{"message": "boom"}]})
        with self.assertRaises(E.EmbeddingUnavailable):
            E._cf_embed(["a"], "m")


class TestQuantize(unittest.TestCase):
    def test_roundtrip_error_small(self):
        import random
        random.seed(7)
        vec = [random.uniform(-1, 1) for _ in range(64)]
        norm = math.sqrt(sum(x * x for x in vec))
        vec = [x / norm for x in vec]
        q, scale = E._quantize(vec)
        recon = [x * scale for x in q]
        err = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec, recon)))
        self.assertLess(err, 0.05)

    def test_cache_base64_roundtrip(self):
        q = array("b", [1, -2, 127, -127])
        blob = base64.b64encode(q.tobytes()).decode("ascii")
        back = array("b")
        back.frombytes(base64.b64decode(blob))
        self.assertEqual(list(back), [1, -2, 127, -127])


class TestVectorsFile(unittest.TestCase):
    def test_write_and_parse_layout(self):
        vecs = [(array("b", [10, -20, 30]), 0.5),
                (array("b", [1, 2, 3]), 0.25)]
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "vectors.bin"
            E.write_vectors(path, vecs, 3)
            raw = path.read_bytes()
        self.assertEqual(raw[:4], b"NSEV")
        _ver, count, dim = struct.unpack("<III", raw[4:16])
        self.assertEqual((count, dim), (2, 3))
        off = 16
        scales = struct.unpack("<2f", raw[off:off + 8])
        self.assertAlmostEqual(scales[0], 0.5)
        self.assertAlmostEqual(scales[1], 0.25)
        data = array("b")
        data.frombytes(raw[off + 8:off + 8 + 6])
        self.assertEqual(list(data), [10, -20, 30, 1, 2, 3])


if __name__ == "__main__":
    unittest.main()
