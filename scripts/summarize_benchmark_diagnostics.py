#!/usr/bin/env python3
"""Create a reproducible case-level diagnostic from frozen benchmark grades."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def failed_checks(case: dict[str, Any], grade: dict[str, Any]) -> list[str]:
    checks: list[str] = []
    recall = len(grade["observation_hits"]) / len(case["must_notice"])
    if recall < .5:
        checks.append("observation_recall")
    if not grade["priority_hit"]:
        checks.append("priority")
    if grade["pattern_fit"] < 1:
        checks.append("pattern_fit")
    if grade["hallucination_violation"]:
        checks.append("hallucination")
    if grade["action_quality"] < 1:
        checks.append("action_quality")
    if grade["reference_hygiene"] < 1:
        checks.append("reference_hygiene")
    if grade["score_integrity"] < 1:
        checks.append("score_integrity")
    if case["quality_band"] == "acclaimed" and grade["overcorrection"]:
        checks.append("overcorrection")
    if case["quality_band"] == "failed_imitation" and not grade["degradation_detected"]:
        checks.append("degradation_miss")
    return checks


def summarize(
    cases: list[dict[str, Any]], grades: list[dict[str, Any]], report: dict[str, Any]
) -> dict[str, Any]:
    by_case = {case["id"]: case for case in cases}
    reason_counts: Counter[str] = Counter()
    operations: dict[str, Counter[str]] = defaultdict(Counter)
    failures = []
    for grade in grades:
        case = by_case[grade["case_id"]]
        checks = failed_checks(case, grade)
        reason_counts.update(checks)
        operation = (
            case["variant_recipe"]["operation"]
            if case.get("variant_recipe") is not None
            else None
        )
        if operation:
            operations[operation]["total"] += 1
            operations[operation]["detected"] += bool(grade["degradation_detected"])
            operations[operation]["case_passed"] += not checks
        if checks:
            failures.append(
                {
                    "case_id": case["id"],
                    "quality_band": case["quality_band"],
                    "genre": case["genre"],
                    "operation": operation,
                    "failed_checks": checks,
                    "grader_notes": grade["notes"],
                }
            )
    return {
        "run_id": report["run_id"],
        "benchmark_cases_sha256": report["benchmark_cases_sha256"],
        "coaching_protocol_sha256": report.get("coaching_protocol_sha256"),
        "passed": report["passed"],
        "metrics": report["metrics"],
        "failure_reason_counts": dict(reason_counts.most_common()),
        "operation_results": {
            name: dict(counts) for name, counts in sorted(operations.items())
        },
        "failed_cases": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--grades", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(
        load_jsonl(args.cases),
        load_jsonl(args.grades),
        json.loads(args.report.read_text(encoding="utf-8")),
    )
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Diagnostic: {len(result['failed_cases'])} failed cases -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
