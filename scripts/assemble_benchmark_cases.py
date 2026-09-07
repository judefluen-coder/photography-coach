#!/usr/bin/env python3
"""Assemble a deterministic benchmark-case draft from a validated selection."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from validate_candidate_selection import DEFAULT_PLAN, validate_selection


BLIND_PROMPT = (
    "仅根据图像完成摄影教练盲评；不要使用文件名、作者、来源、平台评级或答案标签。"
    "运行完整性量化与六检，先做全画面扫描，再给唯一优先级、八维区间、可执行方案、"
    "事实边界，以及一张经核验的精确作品参考。"
)
GENRE_PATTERNS = {
    "architecture/cityscape": [
        "pattern-architectural-axis-with-lived-detail",
        "pattern-perspective-convergence-has-destination",
    ],
    "landscape/nature": [
        "pattern-horizon-controls-stability-and-scale",
        "pattern-depth-by-overlap-and-value",
    ],
    "people/documentary": [
        "pattern-moment-relational",
        "pattern-documentary-context-gate",
    ],
    "wildlife/action": [
        "pattern-action-phase-explains-force",
        "pattern-frame-edge-needs-intent",
    ],
    "still-life/food/macro": [
        "pattern-found-still-life-place-specific",
        "pattern-repetition-needs-interval-and-variation",
    ],
    "abstract/concept": [
        "pattern-reduction-retains-differences",
        "pattern-pattern-interruption-earns-emphasis",
    ],
}
OPERATION_PATTERNS = {
    "crop_pressure": "pattern-crop-pressure-compares-opposite-edges",
    "shadow_crush": "pattern-global-shadow-compression-needs-multiple-boundaries",
    "highlight_clip": "pattern-highlight-hierarchy-before-recovery",
    "color_excess": "pattern-color-excess-preserves-material-differences",
    "tilt_and_crop": "pattern-roll-and-crop-require-independent-references",
    "detail_damage": "pattern-noise-sharpening-protects-material",
}
RECIPES = {
    "crop_pressure": [
        {"left_pct": .10, "right_pct": .02, "top_pct": .04, "bottom_pct": .03},
        {"left_pct": .02, "right_pct": .11, "top_pct": .03, "bottom_pct": .04},
        {"left_pct": .04, "right_pct": .03, "top_pct": .10, "bottom_pct": .02},
        {"left_pct": .03, "right_pct": .05, "top_pct": .02, "bottom_pct": .10},
        {"left_pct": .07, "right_pct": .06, "top_pct": .04, "bottom_pct": .03},
    ],
    "shadow_crush": [
        {"black_point": .20, "gamma": 1.45},
        {"black_point": .22, "gamma": 1.50},
        {"black_point": .24, "gamma": 1.55},
        {"black_point": .25, "gamma": 1.60},
    ],
    "highlight_clip": [
        {"exposure_stops": .80, "clip_point": .97},
        {"exposure_stops": .95, "clip_point": .96},
        {"exposure_stops": 1.10, "clip_point": .95},
        {"exposure_stops": 1.20, "clip_point": .94},
    ],
    "color_excess": [
        {"saturation": 1.65, "red_gain": 1.08, "green_gain": 1.02, "blue_gain": .94},
        {"saturation": 1.75, "red_gain": 1.10, "green_gain": 1.00, "blue_gain": .92},
        {"saturation": 1.85, "red_gain": 1.06, "green_gain": 1.04, "blue_gain": .90},
        {"saturation": 1.90, "red_gain": 1.12, "green_gain": 1.00, "blue_gain": .91},
    ],
    "tilt_and_crop": [
        {"angle_degrees": 4.2, "resample": "bicubic"},
        {"angle_degrees": -4.8, "resample": "bicubic"},
        {"angle_degrees": 5.4, "resample": "bicubic"},
        {"angle_degrees": -5.8, "resample": "bicubic"},
    ],
    "detail_damage": [
        {"downsample_factor": .28, "gaussian_blur_radius": .7, "jpeg_quality": 52, "sharpen_amount": 1.2},
        {"downsample_factor": .24, "gaussian_blur_radius": .9, "jpeg_quality": 45, "sharpen_amount": 1.4},
        {"downsample_factor": .21, "gaussian_blur_radius": 1.0, "jpeg_quality": 38, "sharpen_amount": 1.6},
        {"downsample_factor": .18, "gaussian_blur_radius": 1.1, "jpeg_quality": 32, "sharpen_amount": 1.8},
    ],
}


def assemble(rows: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows = [dict(row) for row in rows]
    rng.shuffle(rows)
    recipe_offsets: dict[str, int] = defaultdict(int)
    cases = []
    for ordinal, row in enumerate(rows, 1):
        role = row["quality_role"]
        operation = row.get("proposed_operation") if role == "failed_base" else None
        variant_recipe = None
        expected_patterns = list(GENRE_PATTERNS[row["genre"]])
        if operation:
            recipe_index = recipe_offsets[operation]
            recipe_offsets[operation] += 1
            variant_recipe = {
                "operation": operation,
                "parameters": RECIPES[operation][recipe_index],
                "source_role": "open-license quality-image base",
                "disclosure": "deterministic derived test variant; not the creator original",
            }
            expected_patterns.insert(0, OPERATION_PATTERNS[operation])
        cases.append(
            {
                "id": f"v3-{ordinal:03d}",
                "quality_band": "failed_imitation" if role == "failed_base" else role,
                "genre": row["genre"],
                "title": row["title"],
                "creator": row["creator"],
                "source_page": row["source_page"],
                "image_url": row["image_url"],
                "preview_url": row["preview_url"],
                "source_sha1": row["source_sha1"],
                "license": row["license"],
                "provenance_status": "official-page-verified",
                "reviewed_on": "2026-09-07",
                "split": "blind_holdout_v3",
                "blind_prompt": BLIND_PROMPT,
                "expected_pattern_ids": expected_patterns,
                "must_notice": row["visible_observations"],
                "must_not_infer": row["must_not_infer"],
                "difficulty": "high" if role in {"acclaimed", "failed_base"} else "medium",
                "selection_rationale": row["selection_rationale"],
                "variant_recipe": variant_recipe,
                "annotation_status": "draft_requires_materialized_review",
                "selection_candidate_id": row["candidate_id"],
            }
        )
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selections", nargs="+", type=Path)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--seed", type=int, default=20260907)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    errors, rows = validate_selection(args.selections, args.plan)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    cases = assemble(rows, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases),
        encoding="utf-8",
    )
    print(f"Draft cases: {len(cases)} -> {args.output}")
    print("Every case remains draft_requires_materialized_review until the image-key audit passes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
