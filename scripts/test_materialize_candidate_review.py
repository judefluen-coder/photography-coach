#!/usr/bin/env python3
"""Tests for candidate-review packet helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from materialize_candidate_review import load_review_rows, pool_identity


class CandidateReviewTests(unittest.TestCase):
    def test_pool_identity(self) -> None:
        self.assertEqual(
            pool_identity(Path("v2-featured-landscapes.jsonl")),
            ("A", "landscapes"),
        )

    def test_unknown_pool_name_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            pool_identity(Path("candidates.jsonl"))

    def test_duplicate_sha1_is_removed_across_pools(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "v2-featured-people.jsonl"
            second = root / "v2-target-food.jsonl"
            row = {"source_sha1": "same", "title": "x"}
            first.write_text(json.dumps(row) + "\n", encoding="utf-8")
            second.write_text(json.dumps(row) + "\n", encoding="utf-8")
            rows = load_review_rows([first, second], 1)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["candidate_id"], "A-peo-001")


if __name__ == "__main__":
    unittest.main()
