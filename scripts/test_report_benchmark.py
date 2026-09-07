#!/usr/bin/env python3
"""Unit tests for blind-benchmark grade validation."""

from __future__ import annotations

import json
import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from report_benchmark import init_grades, sha256, validate_grade


class GradeValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.response = Path(self.temp.name) / "bench-001.md"
        self.response.write_text("A frozen critique", encoding="utf-8")
        self.case = {
            "id": "bench-001",
            "quality_band": "acclaimed",
            "must_notice": ["first", "second"],
        }
        self.grade = {
            "case_id": "bench-001",
            "reviewer_id": "independent-reviewer",
            "response_sha256": sha256(self.response),
            "observation_hits": [0, 1],
            "priority_hit": True,
            "pattern_fit": 2,
            "hallucination_violation": False,
            "action_quality": 2,
            "reference_hygiene": 2,
            "score_integrity": 2,
            "overcorrection": False,
            "degradation_detected": None,
            "notes": "",
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_valid_acclaimed_grade_passes(self) -> None:
        errors: list[str] = []
        result = validate_grade(self.grade, self.case, self.response, errors)
        self.assertEqual(errors, [])
        self.assertTrue(result["passed"])
        self.assertEqual(result["recall"], 1)

    def test_response_mutation_is_rejected(self) -> None:
        self.response.write_text("Changed after grading", encoding="utf-8")
        errors: list[str] = []
        result = validate_grade(self.grade, self.case, self.response, errors)
        self.assertIsNone(result)
        self.assertIn("bench-001: response changed after grading", errors)

    def test_boolean_is_not_accepted_as_two_point_score(self) -> None:
        self.grade["pattern_fit"] = True
        errors: list[str] = []
        result = validate_grade(self.grade, self.case, self.response, errors)
        self.assertIsNone(result)
        self.assertIn("bench-001: pattern_fit must be 0, 1, or 2", errors)

    def test_freeze_rejects_response_outside_benchmark_contract(self) -> None:
        run_dir = Path(self.temp.name) / "run"
        run_dir.mkdir()
        (run_dir / "blind-inputs.jsonl").write_text(
            json.dumps(
                {"case_id": "bench-001", "response_path": str(self.response)}
            )
            + "\n",
            encoding="utf-8",
        )
        with redirect_stderr(io.StringIO()):
            result = init_grades(run_dir, run_dir / "grades.jsonl")
        self.assertEqual(result, 1)
        self.assertFalse((run_dir / "grades.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
