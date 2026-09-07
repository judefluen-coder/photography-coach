#!/usr/bin/env python3
"""Unit tests for benchmark-source identity parsing."""

from __future__ import annotations

import unittest

from audit_benchmark_sources import assessment_present, commons_title, fetch_pages


class CommonsTitleTests(unittest.TestCase):
    def test_featured_subject_category_counts_as_acclaimed(self) -> None:
        self.assertTrue(
            assessment_present(
                {"Category:Featured pictures of food"},
                "acclaimed",
            )
        )

    def test_featured_candidate_alone_is_not_acclaimed(self) -> None:
        self.assertFalse(
            assessment_present(
                {"Category:Featured picture candidates"},
                "acclaimed",
            )
        )

    def test_quality_images_category_is_required_for_non_acclaimed(self) -> None:
        self.assertTrue(
            assessment_present({"Category:Quality images"}, "ordinary")
        )
        self.assertFalse(
            assessment_present({"Category:Featured pictures of food"}, "ordinary")
        )

    def test_fetch_pages_merges_category_continuation(self) -> None:
        calls = []

        def fake_query(params: dict[str, str]) -> dict:
            calls.append(params)
            if len(calls) == 1:
                return {
                    "continue": {"continue": "||", "clcontinue": "1|x"},
                    "query": {
                        "pages": [{
                            "title": "File:X.jpg",
                            "categories": [{"title": "Category:First"}],
                            "imageinfo": [{"sha1": "abc"}],
                        }]
                    },
                }
            return {
                "query": {
                    "pages": [{
                        "title": "File:X.jpg",
                        "categories": [{"title": "Category:Second"}],
                    }]
                }
            }

        pages = fetch_pages(["File:X.jpg"], query_fn=fake_query)
        self.assertEqual(
            [item["title"] for item in pages["File:X.jpg"]["categories"]],
            ["Category:First", "Category:Second"],
        )
        self.assertEqual(pages["File:X.jpg"]["imageinfo"][0]["sha1"], "abc")
        self.assertEqual(calls[1]["clcontinue"], "1|x")

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
