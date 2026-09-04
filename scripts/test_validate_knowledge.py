#!/usr/bin/env python3
"""Regression tests for knowledge validation helpers."""

from __future__ import annotations

import unittest

from validate_knowledge import canonical_url


class CanonicalURLTests(unittest.TestCase):
    def test_content_query_parameters_remain_distinct(self) -> None:
        first = canonical_url("https://www.youtube.com/watch?v=I1oPZO91mtw")
        second = canonical_url("https://www.youtube.com/watch?v=Qw9ZQw9ZQw9")

        self.assertNotEqual(first, second)

    def test_tracking_parameters_do_not_defeat_duplicate_detection(self) -> None:
        clean = canonical_url("https://www.example.com/work?id=42")
        tracked = canonical_url(
            "https://example.com/work/?utm_source=newsletter&id=42&fbclid=abc"
        )

        self.assertEqual(clean, tracked)

    def test_query_order_does_not_change_identity(self) -> None:
        first = canonical_url("https://example.com/search?year=2025&id=42")
        second = canonical_url("https://www.example.com/search?id=42&year=2025")

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
