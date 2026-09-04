#!/usr/bin/env python3
"""Validate blind-run grades and calculate preregistered acceptance metrics."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "references" / "benchmark-cases.jsonl"
STATUS_PATH = ROOT / "references" / "knowledge-status.json"
GRADE_FIELDS = {
    "case_id",
    "reviewer_id",
    "response_sha256",
    "observation_hits",
    "priority_hit",
    "pattern_fit",
    "hallucination_violation",
    "action_quality",
    "reference_hygiene",
    "score_integrity",
    "overcorrection",
    "degradation_detected",
    "notes",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def response_files(run_dir: Path) -> dict[str, Path]:
    inputs = load_jsonl(run_dir / "blind-inputs.jsonl")
    return {item["case_id"]: Path(item["response_path"]) for item in inputs}


def init_grades(run_dir: Path, destination: Path) -> int:
    cases = {case["id"]: case for case in load_jsonl(CASES_PATH)}
    responses = response_files(run_dir)
    missing = [case_id for case_id, path in responses.items() if not path.exists() or not path.read_text(encoding="utf-8").strip()]
    if missing:
        print(
            f"ERROR: freeze all responses before grading; {len(missing)} missing or empty",
            file=sys.stderr,
        )
        return 2
    rows = []
    for case_id, path in responses.items():
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
                "overcorrection": None if case["quality_band"] != "acclaimed" else None,
                "degradation_detected": None if case["quality_band"] != "failed_imitation" else None,
                "notes": "",
            }
        )
    destination.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(f"Grade template: {destination}")
    return 0


def validate_grade(
    grade: dict[str, Any],
    case: dict[str, Any],
    response: Path,
    errors: list[str],
) -> dict[str, Any] | None:
    case_id = case["id"]
    missing = GRADE_FIELDS - grade.keys()
    if missing:
        errors.append(f"{case_id}: missing grade fields: {', '.join(sorted(missing))}")
        return None
    if not isinstance(grade["reviewer_id"], str) or not grade["reviewer_id"].strip():
        errors.append(f"{case_id}: reviewer_id is required")
    if grade["response_sha256"] != sha256(response):
        errors.append(f"{case_id}: response changed after grading")
    hits = grade["observation_hits"]
    maximum = len(case["must_notice"])
    if (
        not isinstance(hits, list)
        or any(not isinstance(index, int) or index < 0 or index >= maximum for index in hits)
        or len(hits) != len(set(hits))
    ):
        errors.append(f"{case_id}: observation_hits must be unique zero-based key indexes")
        hits = []
    for field in ("priority_hit", "hallucination_violation"):
        if not isinstance(grade[field], bool):
            errors.append(f"{case_id}: {field} must be boolean")
    for field in ("pattern_fit", "action_quality", "reference_hygiene", "score_integrity"):
        if isinstance(grade[field], bool) or not isinstance(grade[field], int) or grade[field] not in {0, 1, 2}:
            errors.append(f"{case_id}: {field} must be 0, 1, or 2")
    for field, band in (("overcorrection", "acclaimed"), ("degradation_detected", "failed_imitation")):
        if case["quality_band"] == band:
            if not isinstance(grade[field], bool):
                errors.append(f"{case_id}: {field} must be boolean for {band}")
        elif grade[field] is not None:
            errors.append(f"{case_id}: {field} must be null outside {band}")
    if errors and errors[-1].startswith(f"{case_id}:"):
        return None

    recall = len(hits) / maximum
    passed = (
        recall >= .5
        and grade["priority_hit"]
        and grade["pattern_fit"] >= 1
        and not grade["hallucination_violation"]
        and grade["action_quality"] >= 1
        and grade["reference_hygiene"] >= 1
        and grade["score_integrity"] >= 1
        and (case["quality_band"] != "acclaimed" or not grade["overcorrection"])
        and (case["quality_band"] != "failed_imitation" or grade["degradation_detected"])
    )
    return {"passed": passed, "recall": recall, **grade, **case}


def rate(numerator: int | float, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--grades", type=Path)
    parser.add_argument("--init", action="store_true", help="Create a grade template after responses are frozen")
    parser.add_argument("--output", type=Path, help="Report path; defaults to RUN_DIR/report.json")
    args = parser.parse_args()
    grades_path = args.grades or args.run_dir / "grades.jsonl"
    if args.init:
        return init_grades(args.run_dir, grades_path)

    cases = {case["id"]: case for case in load_jsonl(CASES_PATH)}
    responses = response_files(args.run_dir)
    run = json.loads((args.run_dir / "run.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    if run.get("benchmark_cases_sha256") != sha256(CASES_PATH):
        errors.append("benchmark answer key changed after the run was prepared")
    if set(responses) != set(cases):
        errors.append("blind packet case IDs do not match the current benchmark")
    for case_id, path in responses.items():
        if not path.exists() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"{case_id}: response is missing or empty")

    try:
        grades = load_jsonl(grades_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read grades: {exc}", file=sys.stderr)
        return 2
    grade_ids = [grade.get("case_id") for grade in grades]
    duplicates = [case_id for case_id, count in Counter(grade_ids).items() if count > 1]
    if duplicates:
        errors.append(f"duplicate grade case IDs: {', '.join(sorted(duplicates))}")
    if set(grade_ids) != set(cases):
        errors.append("grades must contain exactly one row for every benchmark case")

    evaluated = []
    by_id = {grade.get("case_id"): grade for grade in grades}
    if not errors:
        for case_id, case in cases.items():
            item = validate_grade(by_id[case_id], case, responses[case_id], errors)
            if item is not None:
                evaluated.append(item)
    if errors:
        print(f"FAIL: {len(errors)} benchmark-run issue(s)", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    thresholds = status["coverage_floors"]["benchmark_acceptance"]
    band_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    genre_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in evaluated:
        band_groups[item["quality_band"]].append(item)
        genre_groups[item["genre"]].append(item)
    band_rates = {name: rate(sum(item["passed"] for item in items), len(items)) for name, items in band_groups.items()}
    genre_rates = {name: rate(sum(item["passed"] for item in items), len(items)) for name, items in genre_groups.items()}
    acclaimed = band_groups["acclaimed"]
    failed = band_groups["failed_imitation"]
    metrics = {
        "evaluated_cases": len(evaluated),
        "overall_pass_rate": rate(sum(item["passed"] for item in evaluated), len(evaluated)),
        "observation_recall": rate(sum(item["recall"] for item in evaluated), len(evaluated)),
        "failed_variant_detection_rate": rate(sum(item["degradation_detected"] for item in failed), len(failed)),
        "acclaimed_overcorrection_rate": rate(sum(item["overcorrection"] for item in acclaimed), len(acclaimed)),
        "hallucination_violation_rate": rate(sum(item["hallucination_violation"] for item in evaluated), len(evaluated)),
        "band_pass_rates": dict(sorted(band_rates.items())),
        "genre_pass_rates": dict(sorted(genre_rates.items())),
    }
    checks = {
        "all_cases_evaluated": metrics["evaluated_cases"] == len(cases),
        "overall_pass_rate": metrics["overall_pass_rate"] >= thresholds["minimum_overall_pass_rate"],
        "every_band_pass_rate": min(band_rates.values()) >= thresholds["minimum_band_pass_rate"],
        "every_genre_pass_rate": min(genre_rates.values()) >= thresholds["minimum_genre_pass_rate"],
        "observation_recall": metrics["observation_recall"] >= thresholds["minimum_observation_recall"],
        "failed_variant_detection_rate": metrics["failed_variant_detection_rate"] >= thresholds["minimum_failed_variant_detection_rate"],
        "acclaimed_overcorrection_rate": metrics["acclaimed_overcorrection_rate"] <= thresholds["maximum_acclaimed_overcorrection_rate"],
        "hallucination_violation_rate": metrics["hallucination_violation_rate"] <= thresholds["maximum_hallucination_violation_rate"],
    }
    report = {
        "run_id": run["run_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_cases_sha256": run["benchmark_cases_sha256"],
        "blind_integrity": {
            "labels_in_blind_packet": run["labels_in_blind_packet"],
            "answers_in_blind_packet": run["answers_in_blind_packet"],
            "response_freeze_enforced": True,
        },
        "thresholds": thresholds,
        "metrics": metrics,
        "checks": checks,
        "passed": all(checks.values()),
        "failed_case_ids": [item["id"] for item in evaluated if not item["passed"]],
    }
    output = args.output or args.run_dir / "report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
