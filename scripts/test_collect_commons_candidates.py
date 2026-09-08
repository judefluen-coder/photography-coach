#!/usr/bin/env python3
"""Tests for deterministic Commons candidate collection helpers."""

from __future__ import annotations

import unittest

from collect_commons_candidates import (
    acceptable_info,
    collect_titles,
    commons_page,
    masterwork_pages,
    plain_text,
    stable_key,
)


class CommonsCandidateTests(unittest.TestCase):
    def test_plain_text_removes_markup(self) -> None:
        self.assertEqual(plain_text("<b>Ada</b>&nbsp;Lovelace"), "Ada Lovelace")

    def test_commons_page_encodes_title(self) -> None:
        self.assertEqual(
            commons_page("File:A B.jpg"),
            "https://commons.wikimedia.org/wiki/File:A_B.jpg",
        )

    def test_stable_key_depends_on_seed(self) -> None:
        self.assertEqual(stable_key("x", "a"), stable_key("x", "a"))
        self.assertNotEqual(stable_key("x", "a"), stable_key("x", "b"))

    def test_accepts_only_large_open_still_images(self) -> None:
        info = {
            "mime": "image/jpeg",
            "width": 1600,
            "height": 1000,
            "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 4.0"}},
        }
        self.assertTrue(acceptable_info(info, 800))
        info["mime"] = "video/webm"
        self.assertFalse(acceptable_info(info, 800))

    def test_collect_titles_deduplicates_prefix_results(self) -> None:
        def fake_query(params: dict[str, str]) -> dict:
            return {
                "query": {
                    "categorymembers": [
                        {"title": "File:A.jpg"},
                        {"title": "File:Shared.jpg"},
                    ]
                }
            }

        self.assertEqual(
            collect_titles("ordinary", "AB", 2, query_fn=fake_query),
            ["File:A.jpg", "File:Shared.jpg"],
        )

    def test_masterwork_direct_url_is_excluded(self) -> None:
        url = "https://commons.wikimedia.org/wiki/File:Teaching_example.jpg"
        self.assertEqual(
            masterwork_pages([{"direct_url": url}]),
            {url},
        )


if __name__ == "__main__":
    unittest.main()
