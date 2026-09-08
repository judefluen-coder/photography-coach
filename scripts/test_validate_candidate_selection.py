#!/usr/bin/env python3
"""Tests for preregistered candidate-selection validation."""

from __future__ import annotations

import json
import hashlib
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
                    "split": "blind_holdout_v4",
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
            "assessment": "ordinary",
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

    def test_promoted_target_split_is_not_treated_as_earlier(self) -> None:
        self.cases.write_text(
            json.dumps(
                {
                    "split": "blind_holdout_v4",
                    "source_sha1": "a" * 40,
                    "source_page": "https://commons.wikimedia.org/wiki/File:Fresh.jpg",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.assertEqual(self.validate(), [])

    def test_wrong_operation_fails(self) -> None:
        self.row["proposed_operation"] = "tilt_and_crop"
        errors = self.validate()
        self.assertTrue(any("failed-operation counts do not match plan" in error for error in errors))

    def test_assessment_must_support_quality_role(self) -> None:
        self.row["assessment"] = "acclaimed"
        self.assertTrue(any("does not support quality_role" in error for error in self.validate()))

    def test_normalized_masterwork_file_overlap_fails(self) -> None:
        self.masterworks.write_text(
            json.dumps(
                {"direct_url": "https://commons.wikimedia.org/wiki/File%3AFresh.jpg"}
            )
            + "\n",
            encoding="utf-8",
        )
        self.assertTrue(
            any("normalized Commons file overlaps" in error for error in self.validate())
        )

    def test_duplicate_image_url_fails(self) -> None:
        plan = json.loads(self.plan.read_text())
        plan["case_count"] = 2
        plan["quality_roles"] = {"failed_base": 2}
        plan["genre_role_counts"] = {"wildlife/action": {"failed_base": 2}}
        plan["failed_operation_counts"] = {"crop_pressure": 2}
        self.plan.write_text(json.dumps(plan))
        other = {**self.row, "candidate_id": "O-spo-002", "source_sha1": "b" * 40,
                 "source_page": "https://commons.wikimedia.org/wiki/File:Other.jpg"}
        self.selection.write_text(
            json.dumps(self.row) + "\n" + json.dumps(other) + "\n",
            encoding="utf-8",
        )
        with (
            patch.object(validator, "CASES", self.cases),
            patch.object(validator, "DEVELOPMENT", self.development),
            patch.object(validator, "V2_ARCHIVE", self.v2_archive),
            patch.object(validator, "MASTERWORKS", self.masterworks),
            patch.object(validator, "ROOT", self.root),
        ):
            errors, _ = validator.validate_selection([self.selection], self.plan)
        self.assertTrue(any("duplicate image_url" in error for error in errors))

    def with_frozen_manifest(self) -> tuple[Path, dict]:
        manifest = self.root / "candidate-manifest.jsonl"
        frozen = {
            key: self.row[key]
            for key in (
                "candidate_id", "source_sha1", "source_page", "image_url", "preview_url",
                "title", "creator", "license", "assessment",
            )
        }
        frozen["review_genre"] = "sports"
        manifest.write_text(json.dumps(frozen) + "\n", encoding="utf-8")
        plan = json.loads(self.plan.read_text())
        plan["candidate_pool"] = {
            "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "candidate_count": 1,
        }
        self.plan.write_text(json.dumps(plan), encoding="utf-8")
        return manifest, frozen

    def test_frozen_manifest_membership_passes(self) -> None:
        manifest, _ = self.with_frozen_manifest()
        self.selection.write_text(json.dumps(self.row) + "\n", encoding="utf-8")
        with (
            patch.object(validator, "CASES", self.cases),
            patch.object(validator, "DEVELOPMENT", self.development),
            patch.object(validator, "V2_ARCHIVE", self.v2_archive),
            patch.object(validator, "MASTERWORKS", self.masterworks),
        ):
            errors, _ = validator.validate_selection(
                [self.selection], self.plan, manifest,
            )
        self.assertEqual(errors, [])

    def test_frozen_manifest_hash_mismatch_fails(self) -> None:
        manifest, _ = self.with_frozen_manifest()
        manifest.write_text(manifest.read_text() + "\n", encoding="utf-8")
        self.selection.write_text(json.dumps(self.row) + "\n", encoding="utf-8")
        with (
            patch.object(validator, "CASES", self.cases),
            patch.object(validator, "DEVELOPMENT", self.development),
            patch.object(validator, "V2_ARCHIVE", self.v2_archive),
            patch.object(validator, "MASTERWORKS", self.masterworks),
        ):
            errors, _ = validator.validate_selection(
                [self.selection], self.plan, manifest,
            )
        self.assertTrue(any("candidate manifest sha256" in error for error in errors))

    def test_selection_cannot_mutate_frozen_identity(self) -> None:
        manifest, _ = self.with_frozen_manifest()
        self.row["creator"] = "Changed after preregistration"
        self.selection.write_text(json.dumps(self.row) + "\n", encoding="utf-8")
        with (
            patch.object(validator, "CASES", self.cases),
            patch.object(validator, "DEVELOPMENT", self.development),
            patch.object(validator, "V2_ARCHIVE", self.v2_archive),
            patch.object(validator, "MASTERWORKS", self.masterworks),
        ):
            errors, _ = validator.validate_selection(
                [self.selection], self.plan, manifest,
            )
        self.assertTrue(any("creator differs from the frozen" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
