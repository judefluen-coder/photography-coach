#!/usr/bin/env python3
"""Tests for frozen benchmark grade merging."""

from __future__ import annotations

import unittest

from merge_benchmark_grades import merge


class MergeBenchmarkGradesTests(unittest.TestCase):
    def test_merge_preserves_template_order(self) -> None:
        template = [
            {"case_id": "b", "response_sha256": "2"},
            {"case_id": "a", "response_sha256": "1"},
        ]
        fragments = [
            {"case_id": "a", "response_sha256": "1", "priority_hit": True},
            {"case_id": "b", "response_sha256": "2", "priority_hit": False},
        ]
        merged, errors = merge(template, fragments)
        self.assertEqual(errors, [])
        self.assertEqual([row["case_id"] for row in merged], ["b", "a"])

    def test_hash_change_fails(self) -> None:
        template = [{"case_id": "a", "response_sha256": "1"}]
        fragments = [{"case_id": "a", "response_sha256": "changed"}]
        _, errors = merge(template, fragments)
        self.assertTrue(any("hash differs" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
