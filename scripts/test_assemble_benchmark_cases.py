#!/usr/bin/env python3
"""Tests for deterministic benchmark draft assembly."""

from __future__ import annotations

import unittest

from assemble_benchmark_cases import assemble


class AssembleBenchmarkCasesTests(unittest.TestCase):
    def row(self, role: str, operation: str | None = None) -> dict[str, object]:
        return {
            "candidate_id": f"candidate-{role}",
            "quality_role": role,
            "genre": "wildlife/action",
            "title": "Runner",
            "creator": "Example",
            "source_page": f"https://commons.wikimedia.org/{role}",
            "image_url": f"https://upload.wikimedia.org/{role}.jpg",
            "preview_url": f"https://upload.wikimedia.org/{role}-preview.jpg",
            "source_sha1": ("a" if role == "acclaimed" else "b") * 40,
            "license": "CC BY-SA 4.0",
            "visible_observations": ["runner clears rail", "crowd remains behind"],
            "must_not_infer": ["result unknown"],
            "selection_rationale": "visible action relationship",
            **({"proposed_operation": operation} if operation else {}),
        }

    def test_failed_base_becomes_draft_variant(self) -> None:
        case = assemble([self.row("failed_base", "tilt_and_crop")], 7)[0]
        self.assertEqual(case["id"], "v4-001")
        self.assertEqual(case["split"], "blind_holdout_v4")
        self.assertEqual(case["quality_band"], "failed_imitation")
        self.assertEqual(case["variant_recipe"]["operation"], "tilt_and_crop")
        self.assertEqual(case["annotation_status"], "draft_requires_materialized_review")

    def test_seed_is_deterministic(self) -> None:
        rows = [self.row("acclaimed"), self.row("failed_base", "crop_pressure")]
        self.assertEqual(assemble(rows, 9), assemble(rows, 9))

    def test_split_controls_case_prefix(self) -> None:
        case = assemble(
            [self.row("acclaimed")],
            1,
            split="blind_holdout_v9",
            reviewed_on="2030-01-02",
        )[0]
        self.assertEqual(case["id"], "v9-001")
        self.assertEqual(case["reviewed_on"], "2030-01-02")


if __name__ == "__main__":
    unittest.main()
