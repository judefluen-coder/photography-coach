#!/usr/bin/env python3
"""Tests for preregistered candidate-selection validation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import validate_candidate_selection as validator


class CandidateSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan = self.root / "plan.json"
        self.plan.write_text(
            json.dumps(
                {
                    "case_count": 1,
                    "quality_roles": {"failed_base": 1},
                    "genre_role_counts": {"wildlife/action": {"failed_base": 1}},
                    "failed_operation_counts": {"crop_pressure": 1},
                }
            ),
            encoding="utf-8",
        )
        self.selection = self.root / "selection.jsonl"
        self.row = {
            "candidate_id": "O-spo-001",
            "source_sha1": "a" * 40,
            "source_page": "https://commons.wikimedia.org/wiki/File:Fresh.jpg",
            "image_url": "https://upload.wikimedia.org/fresh.jpg",
            "preview_url": "https://upload.wikimedia.org/fresh-preview.jpg",
            "title": "Fresh",
            "creator": "Example",
            "license": "CC BY-SA 4.0",
            "quality_role": "failed_base",
            "genre": "wildlife/action",
            "visible_observations": ["runner clears rail", "crowd remains behind"],
            "must_not_infer": ["identity and result are unknown"],
            "selection_rationale": "clear action interfaces",
            "proposed_operation": "crop_pressure",
        }
        self.cases = self.root / "cases.jsonl"
        self.development = self.root / "development.jsonl"
        self.v2_archive = self.root / "v2.jsonl"
        self.masterworks = self.root / "masterworks.jsonl"
        for path in (self.cases, self.development, self.v2_archive, self.masterworks):
            path.write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def validate(self) -> list[str]:
        self.selection.write_text(json.dumps(self.row) + "\n", encoding="utf-8")
        with (
            patch.object(validator, "CASES", self.cases),
            patch.object(validator, "DEVELOPMENT", self.development),
            patch.object(validator, "V2_ARCHIVE", self.v2_archive),
            patch.object(validator, "MASTERWORKS", self.masterworks),
        ):
            errors, _ = validator.validate_selection([self.selection], self.plan)
        return errors

    def test_valid_selection_passes(self) -> None:
        self.assertEqual(self.validate(), [])

    def test_prior_sha1_overlap_fails(self) -> None:
        self.cases.write_text(
            json.dumps({"source_sha1": "a" * 40, "source_page": "https://old"}) + "\n",
            encoding="utf-8",
        )
        self.assertTrue(any("overlaps an earlier benchmark" in error for error in self.validate()))

    def test_wrong_operation_fails(self) -> None:
        self.row["proposed_operation"] = "tilt_and_crop"
        errors = self.validate()
        self.assertTrue(any("failed-operation counts do not match plan" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
