#!/usr/bin/env python3
"""Tests for preregistered candidate-selection validation."""

from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

import validate_candidate_selection as validator


class CandidateSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan = self.root / "plan.json"
        self.snapshot = self.root / "historical-source-exclusions.json"
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
        self.plan_payload = {
            "split": "blind_holdout_v5",
            "blind_prompt": "Critique only the supplied image.",
            "case_count": 1,
            "quality_roles": {"failed_base": 1},
            "assessment_by_quality_role": {"failed_base": "ordinary"},
            "genre_role_counts": {"wildlife/action": {"failed_base": 1}},
            "failed_operation_counts": {"crop_pressure": 1},
            "failure_recipe_profiles": {"crop_pressure": [{"left_pct": 0.1}]},
            "candidate_review_genre_map": {"sports": "wildlife/action"},
        }
        self.write_exclusion_snapshot([])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_exclusion_snapshot(self, sources: list[dict[str, object]]) -> None:
        source_sha1s = sorted(
            {item for source in sources for item in source["source_sha1s"]}
        )
        source_pages = sorted(
            {item for source in sources for item in source["source_pages"]}
        )
        image_urls = sorted(
            {item for source in sources for item in source["image_urls"]}
        )
        canonical_payload = {
            "schema_version": 1,
            "source_files": sorted(
                {item for source in sources for item in source["source_files"]}
            ),
            "source_sha1s": source_sha1s,
            "source_pages": source_pages,
            "image_urls": image_urls,
            "sources": sources,
        }
        overall_hash = hashlib.sha256(
            json.dumps(
                canonical_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        snapshot_payload = {
            **canonical_payload,
            "source_count": len(sources),
            "overall_sha256": overall_hash,
            "snapshot_sha256": overall_hash,
        }
        self.snapshot.write_text(json.dumps(snapshot_payload), encoding="utf-8")
        self.plan_payload["exclusion_snapshot"] = {
            "path": str(self.snapshot),
            "sha256": hashlib.sha256(self.snapshot.read_bytes()).hexdigest(),
            "source_count": len(sources),
            "overall_sha256": overall_hash,
        }
        self.plan.write_text(json.dumps(self.plan_payload), encoding="utf-8")

    def validate(self) -> list[str]:
        self.selection.write_text(json.dumps(self.row) + "\n", encoding="utf-8")
        errors, _ = validator.validate_selection([self.selection], self.plan)
        return errors

    def test_valid_selection_passes(self) -> None:
        self.assertEqual(self.validate(), [])

    def test_prior_sha1_overlap_fails(self) -> None:
        self.write_exclusion_snapshot(
            [{
                "source_files": ["references/benchmark-v4-cases.jsonl"],
                "source_sha1s": ["a" * 40],
                "source_pages": ["https://old"],
                "image_urls": [],
            }]
        )
        self.assertTrue(any("overlaps an earlier benchmark" in error for error in self.validate()))

    def test_tracking_query_cannot_hide_image_url_overlap(self) -> None:
        self.write_exclusion_snapshot(
            [{
                "source_files": ["old/materialization-manifest.json"],
                "source_sha1s": [],
                "source_pages": [],
                "image_urls": [
                    "https://upload.wikimedia.org/example.jpg"
                ],
            }]
        )
        self.row["image_url"] = (
            "https://upload.wikimedia.org/example.jpg?utm_source=commons"
        )
        self.assertTrue(
            any("image_url overlaps" in error for error in self.validate())
        )

    def test_same_split_history_is_still_excluded(self) -> None:
        self.write_exclusion_snapshot(
            [{
                "source_files": ["same-split/blind_holdout_v5.jsonl"],
                "source_sha1s": ["a" * 40],
                "source_pages": [
                    "https://commons.wikimedia.org/wiki/File:Fresh.jpg"
                ],
                "image_urls": [],
            }]
        )
        self.assertTrue(any("overlaps an earlier benchmark" in error for error in self.validate()))

    def test_exclusion_snapshot_hash_mismatch_fails(self) -> None:
        self.snapshot.write_text(self.snapshot.read_text() + " ", encoding="utf-8")
        self.assertTrue(any("exclusion snapshot sha256" in error for error in self.validate()))

    def test_wrong_operation_fails(self) -> None:
        self.row["proposed_operation"] = "tilt_and_crop"
        errors = self.validate()
        self.assertTrue(
            any("failed-operation counts do not match plan" in error for error in errors)
        )

    def test_assessment_must_support_quality_role(self) -> None:
        self.row["assessment"] = "acclaimed"
        self.assertTrue(any("does not support quality_role" in error for error in self.validate()))

    def test_normalized_masterwork_file_overlap_fails(self) -> None:
        self.write_exclusion_snapshot(
            [{
                "source_files": ["references/masterwork-cards.jsonl"],
                "source_sha1s": [],
                "source_pages": [
                    "https://commons.wikimedia.org/wiki/File%3AFresh.jpg"
                ],
                "image_urls": [],
            }]
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
        plan["failure_recipe_profiles"] = {
            "crop_pressure": [{"left_pct": 0.1}, {"right_pct": 0.1}]
        }
        self.plan.write_text(json.dumps(plan))
        other = {**self.row, "candidate_id": "O-spo-002", "source_sha1": "b" * 40,
                 "source_page": "https://commons.wikimedia.org/wiki/File:Other.jpg"}
        self.selection.write_text(
            json.dumps(self.row) + "\n" + json.dumps(other) + "\n",
            encoding="utf-8",
        )
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
            "status": "frozen",
            "manifest_path": str(manifest),
            "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "candidate_count": 1,
        }
        self.plan.write_text(json.dumps(plan), encoding="utf-8")
        return manifest, frozen

    def test_frozen_manifest_membership_passes(self) -> None:
        self.with_frozen_manifest()
        self.selection.write_text(json.dumps(self.row) + "\n", encoding="utf-8")
        errors, _ = validator.validate_selection(
            [self.selection], self.plan,
        )
        self.assertEqual(errors, [])

    def test_candidate_manifest_path_must_match_plan(self) -> None:
        manifest, _ = self.with_frozen_manifest()
        alternate = self.root / "alternate-manifest.jsonl"
        alternate.write_bytes(manifest.read_bytes())
        self.selection.write_text(json.dumps(self.row) + "\n", encoding="utf-8")
        errors, _ = validator.validate_selection(
            [self.selection], self.plan, alternate,
        )
        self.assertIn(
            "candidate manifest path differs from the preregistered plan",
            errors,
        )

    def test_frozen_manifest_hash_mismatch_fails(self) -> None:
        manifest, _ = self.with_frozen_manifest()
        manifest.write_text(manifest.read_text() + "\n", encoding="utf-8")
        self.selection.write_text(json.dumps(self.row) + "\n", encoding="utf-8")
        errors, _ = validator.validate_selection(
            [self.selection], self.plan, manifest,
        )
        self.assertTrue(any("candidate manifest sha256" in error for error in errors))

    def test_selection_cannot_mutate_frozen_identity(self) -> None:
        manifest, _ = self.with_frozen_manifest()
        self.row["creator"] = "Changed after preregistration"
        self.selection.write_text(json.dumps(self.row) + "\n", encoding="utf-8")
        errors, _ = validator.validate_selection(
            [self.selection], self.plan, manifest,
        )
        self.assertTrue(any("creator differs from the frozen" in error for error in errors))


class V5PlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parent.parent
        self.plan_path = self.root / "references" / "benchmark-v5-plan.json"
        self.plan = json.loads(self.plan_path.read_text(encoding="utf-8"))

    def test_v5_plan_quotas_and_recipe_profiles_are_consistent(self) -> None:
        errors: list[str] = []
        validator.validate_plan(self.plan, errors)
        self.assertEqual(errors, [])
        self.assertEqual(self.plan["case_count"], 180)
        self.assertEqual(
            self.plan["quality_roles"],
            {"acclaimed": 60, "ordinary": 60, "failed_base": 60},
        )
        for quotas in self.plan["genre_role_counts"].values():
            self.assertEqual(
                quotas, {"acclaimed": 10, "ordinary": 10, "failed_base": 10}
            )
        for operation, count in self.plan["failed_operation_counts"].items():
            self.assertEqual(count, 10)
            self.assertEqual(len(self.plan["failure_recipe_profiles"][operation]), 10)

    def test_v5_exclusion_snapshot_and_candidate_pool_are_frozen(self) -> None:
        errors: list[str] = []
        excluded = validator.load_exclusion_snapshot(
            self.plan, self.plan_path, errors
        )
        self.assertEqual(errors, [])
        self.assertEqual(self.plan["exclusion_snapshot"]["source_count"], 550)
        self.assertTrue(all(excluded))

        pool = self.plan["candidate_pool"]
        manifest_path = validator.resolve_plan_path(
            self.plan_path, pool["manifest_path"]
        )
        self.assertEqual(
            hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            pool["manifest_sha256"],
        )
        self.assertEqual(
            sum(1 for line in manifest_path.read_text().splitlines() if line.strip()),
            pool["candidate_count"],
        )

    def test_real_stress_set_is_separate_from_release_score(self) -> None:
        stress = self.plan["real_stress_set"]
        self.assertEqual(stress["case_count"], 40)
        self.assertTrue(stress["scored_separately"])
        self.assertFalse(stress["counts_toward_release_score"])

    def test_release_thresholds_match_frozen_status_snapshot(self) -> None:
        snapshot = self.plan["threshold_snapshot"]
        status_path = validator.resolve_plan_path(self.plan_path, snapshot["path"])
        self.assertEqual(
            hashlib.sha256(status_path.read_bytes()).hexdigest(),
            snapshot["sha256"],
        )
        status = json.loads(status_path.read_text(encoding="utf-8"))
        self.assertEqual(
            self.plan["release_acceptance_thresholds"],
            status["coverage_floors"]["benchmark_acceptance"],
        )


if __name__ == "__main__":
    unittest.main()
