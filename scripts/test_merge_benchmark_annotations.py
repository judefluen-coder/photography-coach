#!/usr/bin/env python3
"""Tests for merging materialized-image benchmark annotations."""

from __future__ import annotations

import unittest

from merge_benchmark_annotations import merge


class MergeBenchmarkAnnotationsTests(unittest.TestCase):
    def test_complete_review_replaces_answer_key(self) -> None:
        cases = [{"id": "v3-001", "must_notice": ["draft"], "must_not_infer": ["draft"]}]
        rows = [
            {
                "case_id": "v3-001",
                "must_notice": ["left anchor visible", "right anchor visible"],
                "must_not_infer": ["do not infer identity"],
                "visible_anchors_checked": ["left anchor", "right anchor"],
                "image_key_alignment": True,
                "reviewer_id": "reviewer-a",
            }
        ]
        merged, errors = merge(cases, rows)
        self.assertEqual(errors, [])
        self.assertEqual(merged[0]["must_notice"], rows[0]["must_notice"])
        self.assertEqual(merged[0]["annotation_status"], "materialized-image-verified")

    def test_missing_annotation_fails(self) -> None:
        _, errors = merge([{"id": "v3-001"}], [])
        self.assertTrue(any("missing annotations" in error for error in errors))

    def test_unaligned_annotation_fails(self) -> None:
        cases = [{"id": "v3-001"}]
        rows = [
            {
                "case_id": "v3-001",
                "must_notice": ["one", "two"],
                "must_not_infer": ["boundary"],
                "visible_anchors_checked": ["one", "two"],
                "image_key_alignment": False,
                "reviewer_id": "reviewer-a",
            }
        ]
        _, errors = merge(cases, rows)
        self.assertTrue(any("image_key_alignment" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
