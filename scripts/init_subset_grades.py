#!/usr/bin/env python3
"""Freeze a declared benchmark subset and create a blank grade template."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from report_benchmark import CASES_PATH, load_jsonl, response_files, sha256
from validate_response import integrity_signal_map, validate


def initialize_subset(
    run_dir: Path,
    case_ids: list[str],
    destination: Path,
) -> list[str]:
    errors: list[str] = []
    if not case_ids:
        return ["at least one case ID is required"]
    if len(case_ids) != len(set(case_ids)):
        return ["case IDs must be unique"]

    cases = {case["id"]: case for case in load_jsonl(CASES_PATH)}
    responses = response_files(run_dir)
    inputs = {
        item["case_id"]: item
        for item in load_jsonl(run_dir / "blind-inputs.jsonl")
    }
    unknown = sorted(set(case_ids) - cases.keys())
    outside_packet = sorted(set(case_ids) - responses.keys())
    if unknown:
        errors.append(f"unknown benchmark case IDs: {', '.join(unknown)}")
    if outside_packet:
        errors.append(f"case IDs absent from blind packet: {', '.join(outside_packet)}")

    rows = []
    for case_id in case_ids:
        if case_id not in cases or case_id not in responses:
            continue
        path = responses[case_id]
        if not path.exists() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"{case_id}: response is missing or empty")
            continue
        response_text = path.read_text(encoding="utf-8")
        image_path_value = inputs[case_id].get("image_path")
        integrity_signals = None
        if image_path_value and not Path(image_path_value).exists():
            errors.append(f"{case_id}: benchmark image is missing")
            continue
        if image_path_value:
            integrity_signals = integrity_signal_map(Path(image_path_value))
        response_errors = validate(
            response_text,
            require_integrity_probe=True,
            require_reference=True,
            integrity_signals=integrity_signals,
        )
        if response_errors:
            errors.extend(f"{case_id}: {error}" for error in response_errors)
            continue
        case = cases[case_id]
        rows.append(
            {
                "case_id": case_id,
                "reviewer_id": None,
                "response_sha256": sha256(path),
                "observation_hits": [],
                "priority_hit": None,
                "pattern_fit": None,
                "hallucination_violation": None,
                "action_quality": None,
                "reference_hygiene": None,
                "score_integrity": None,
                "overcorrection": None if case["quality_band"] == "acclaimed" else None,
                "degradation_detected": None if case["quality_band"] == "failed_imitation" else None,
                "notes": "",
            }
        )

    if errors:
        return errors
    destination.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("case_ids", nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    errors = initialize_subset(args.run_dir, args.case_ids, args.output)
    if errors:
        print(f"FAIL: {len(errors)} subset-freeze issue(s)", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"PASS: froze {len(args.case_ids)} responses at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
