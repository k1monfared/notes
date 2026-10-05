"""Tests for cleaning, normalization, sectioning, and chunking."""

import unittest

from search.text import (
    detect_lang,
    normalize_persian,
    normalize_text,
    sectionize,
    slugify,
    split_long,
    strip_markdown,
)


class TestNormalize(unittest.TestCase):
    def test_persian_kaf_yeh(self):
        self.assertEqual(normalize_persian("كتاب يكي"), "کتاب یکی")

    def test_strips_diacritics_and_tatweel(self):
        self.assertEqual(normalize_text("كِتابـ"), "کتاب")

    def test_nfkc(self):
        self.assertEqual(normalize_text("ﬁ"), "fi")


class TestStripMarkdown(unittest.TestCase):
    def test_links_and_images(self):
        text = strip_markdown("See [the docs](http://x) ![alt](img.png) now")
        self.assertIn("the docs", text)
        self.assertIn("alt", text)
        self.assertNotIn("http", text)

    def test_latex_keeps_words(self):
        text = strip_markdown(r"Let $\alpha + \beta$ be numbers")
        self.assertIn("alpha", text)
        self.assertIn("beta", text)
        self.assertNotIn("$", text)

    def test_code_fences_keep_code(self):
        text = strip_markdown("```python\nprint(1)\n```")
        self.assertIn("print(1)", text)
        self.assertNotIn("```", text)

    def test_setext_underline_removed(self):
        text = strip_markdown("Title\n--\nBody here")
        self.assertNotIn("--", text)
        self.assertIn("Body here", text)


class TestSectionize(unittest.TestCase):
    def test_heading_split_and_anchors(self):
        sections = sectionize("# Title\n\nIntro\n\n## Sub part\n\nBody")
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0][0], "Title")
        self.assertIn("Intro", sections[0][2])
        self.assertEqual(sections[1][0], "Sub part")
        self.assertEqual(sections[1][1], "sub-part")

    def test_custom_anchor(self):
        sections = sectionize("## Head {#custom}\n\nText")
        self.assertEqual(sections[0][1], "custom")


class TestSplitLong(unittest.TestCase):
    def test_short_passthrough(self):
        self.assertEqual(split_long("abc", 100), ["abc"])

    def test_paragraph_packing(self):
        paras = "\n\n".join(f"paragraph {i} " + "x" * 50 for i in range(5))
        pieces = split_long(paras, 150)
        self.assertTrue(all(len(p) <= 150 for p in pieces))
        self.assertGreater(len(pieces), 1)


class TestLang(unittest.TestCase):
    def test_persian(self):
        self.assertEqual(detect_lang("این یک متن فارسی است"), "fa")

    def test_english(self):
        self.assertEqual(detect_lang("This is an English sentence"), "en")


class TestSlugify(unittest.TestCase):
    def test_unicode_preserved(self):
        self.assertEqual(slugify("جهان امید"), "جهان-امید")


if __name__ == "__main__":
    unittest.main()
