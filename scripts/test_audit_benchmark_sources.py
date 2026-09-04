#!/usr/bin/env python3
"""Unit tests for benchmark-source identity parsing."""

from __future__ import annotations

import unittest

from audit_benchmark_sources import commons_title


class CommonsTitleTests(unittest.TestCase):
    def test_decodes_exact_file_title(self) -> None:
        self.assertEqual(
            commons_title(
                "https://commons.wikimedia.org/wiki/File:Quiraing%2C_Isle_of_Skye%2C_Scotland_-_Diliff.jpg"
            ),
            "File:Quiraing, Isle of Skye, Scotland - Diliff.jpg",
        )

    def test_rejects_non_wiki_url(self) -> None:
        with self.assertRaises(ValueError):
            commons_title("https://upload.wikimedia.org/image.jpg")


if __name__ == "__main__":
    unittest.main()
