#!/usr/bin/env python3
"""Tests for declared benchmark-subset freezing."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from init_subset_grades import initialize_subset
from test_validate_blind_responses import valid_response


class SubsetFreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.response = self.root / "bench-001.md"
        self.response.write_text(valid_response("测试主体"), encoding="utf-8")
        (self.root / "blind-inputs.jsonl").write_text(
            json.dumps(
                {"case_id": "bench-001", "response_path": str(self.response)}
            )
            + "\n",
            encoding="utf-8",
        )
        self.cases = self.root / "cases.jsonl"
        self.cases.write_text(
            json.dumps({"id": "bench-001", "quality_band": "acclaimed"}) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_freezes_only_declared_response(self) -> None:
        output = self.root / "grades.jsonl"
        with patch("init_subset_grades.CASES_PATH", self.cases):
            errors = initialize_subset(self.root, ["bench-001"], output)
        self.assertEqual(errors, [])
        row = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(row["case_id"], "bench-001")
        self.assertEqual(len(row["response_sha256"]), 64)
        self.assertIsNone(row["reviewer_id"])

    def test_missing_response_is_rejected(self) -> None:
        self.response.unlink()
        with patch("init_subset_grades.CASES_PATH", self.cases):
            errors = initialize_subset(
                self.root,
                ["bench-001"],
                self.root / "grades.jsonl",
            )
        self.assertIn("bench-001: response is missing or empty", errors)

    def test_structurally_invalid_response_is_not_frozen(self) -> None:
        self.response.write_text("not a critique", encoding="utf-8")
        with patch("init_subset_grades.CASES_PATH", self.cases):
            errors = initialize_subset(
                self.root,
                ["bench-001"],
                self.root / "grades.jsonl",
            )
        self.assertTrue(any("missing heading" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
