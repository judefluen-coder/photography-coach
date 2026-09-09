#!/usr/bin/env python3
"""Tests for deterministic benchmark draft assembly."""

from __future__ import annotations

import copy
import json
import unittest
from collections import Counter

from assemble_benchmark_cases import OPERATION_PATTERNS, assemble


class AssembleBenchmarkCasesTests(unittest.TestCase):
    def row(
        self,
        role: str,
        operation: str | None = None,
        serial: int = 0,
    ) -> dict[str, object]:
        return {
            "candidate_id": f"candidate-{role}-{serial}",
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

    def failure_recipe_profiles(self) -> dict[str, list[dict[str, object]]]:
        return {
            "crop_pressure": [
                {
                    "left_pct": round(.04 + index * .006, 3),
                    "right_pct": round(.02 + index * .002, 3),
                    "top_pct": round(.02 + index * .001, 3),
                    "bottom_pct": .03,
                }
                for index in range(10)
            ],
            "shadow_crush": [
                {"black_point": round(.18 + index * .01, 2), "gamma": 1.45}
                for index in range(10)
            ],
            "highlight_clip": [
                {"exposure_stops": round(.75 + index * .07, 2), "clip_point": .96}
                for index in range(10)
            ],
            "color_excess": [
                {
                    "saturation": round(1.55 + index * .05, 2),
                    "red_gain": 1.08,
                    "green_gain": 1.01,
                    "blue_gain": .93,
                }
                for index in range(10)
            ],
            "tilt_and_crop": [
                {
                    "angle_degrees": (1 if index % 2 == 0 else -1) * (4 + index * .25),
                    "resample": "bicubic",
                }
                for index in range(10)
            ],
            "detail_damage": [
                {
                    "downsample_factor": round(.20 + index * .01, 2),
                    "gaussian_blur_radius": .9,
                    "jpeg_quality": 42,
                    "sharpen_amount": 1.4,
                }
                for index in range(10)
            ],
        }

    def v5_plan(self) -> dict[str, object]:
        return {
            "split": "blind_holdout_v5",
            "preregistered_on": "2026-09-09",
            "assembly_seed": 20260909,
            "case_count": 180,
            "blind_prompt": "v5 preregistered blind prompt",
            "failed_operation_counts": {
                operation: 10 for operation in OPERATION_PATTERNS
            },
            "failure_recipe_profiles": self.failure_recipe_profiles(),
        }

    def v5_rows(self) -> list[dict[str, object]]:
        rows = [self.row("acclaimed", serial=index) for index in range(60)]
        rows.extend(self.row("ordinary", serial=index) for index in range(60))
        serial = 0
        for operation in OPERATION_PATTERNS:
            rows.extend(
                self.row("failed_base", operation, serial + index)
                for index in range(10)
            )
            serial += 10
        return rows

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

    def test_v5_plan_assembles_180_cases_with_ten_of_each_failure(self) -> None:
        plan = self.v5_plan()
        cases = assemble(self.v5_rows(), 20260909, plan=plan)

        self.assertEqual(len(cases), 180)
        self.assertEqual(
            Counter(case["quality_band"] for case in cases),
            {"acclaimed": 60, "ordinary": 60, "failed_imitation": 60},
        )
        self.assertEqual(
            Counter(
                case["variant_recipe"]["operation"]
                for case in cases
                if case["variant_recipe"] is not None
            ),
            {operation: 10 for operation in OPERATION_PATTERNS},
        )
        self.assertEqual([case["id"] for case in cases], [
            f"v5-{ordinal:03d}" for ordinal in range(1, 181)
        ])
        self.assertTrue(all(case["split"] == "blind_holdout_v5" for case in cases))
        self.assertTrue(
            all(case["blind_prompt"] == plan["blind_prompt"] for case in cases)
        )

        expected_profiles = plan["failure_recipe_profiles"]
        for operation in OPERATION_PATTERNS:
            actual = {
                json.dumps(case["variant_recipe"]["parameters"], sort_keys=True)
                for case in cases
                if case["variant_recipe"] is not None
                and case["variant_recipe"]["operation"] == operation
            }
            expected = {
                json.dumps(profile, sort_keys=True)
                for profile in expected_profiles[operation]
            }
            self.assertEqual(actual, expected)

    def test_v5_plan_is_deterministic(self) -> None:
        plan = self.v5_plan()
        rows = self.v5_rows()
        self.assertEqual(
            assemble(rows, 20260909, plan=plan),
            assemble(rows, 20260909, plan=plan),
        )

    def test_v5_recipe_shortage_fails_closed(self) -> None:
        plan = self.v5_plan()
        plan["failure_recipe_profiles"]["detail_damage"].pop()
        with self.assertRaisesRegex(ValueError, "expected exactly 10"):
            assemble(self.v5_rows(), 20260909, plan=plan)

    def test_v5_recipe_cannot_add_unregistered_operation_parameters(self) -> None:
        plan = copy.deepcopy(self.v5_plan())
        plan["failure_recipe_profiles"]["crop_pressure"][0]["local_mask"] = "subject"
        with self.assertRaisesRegex(ValueError, "must contain exactly"):
            assemble(self.v5_rows(), 20260909, plan=plan)

    def test_nonlegacy_plan_requires_blind_prompt(self) -> None:
        plan = self.v5_plan()
        del plan["blind_prompt"]
        with self.assertRaisesRegex(ValueError, "blind_prompt"):
            assemble(self.v5_rows(), 20260909, plan=plan)


if __name__ == "__main__":
    unittest.main()
