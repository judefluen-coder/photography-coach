#!/usr/bin/env python3
"""Validate Photography Coach knowledge records and cross-references."""

from __future__ import annotations

import json
import sys
import argparse
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
REFERENCE_ROOT = ROOT / "references"
STATUS_PATH = REFERENCE_ROOT / "knowledge-status.json"
TEST_CASES_PATH = REFERENCE_ROOT / "benchmark-cases.jsonl"
SCHEMAS = {
    "sources": {
        "path": REFERENCE_ROOT / "source-registry.jsonl",
        "required": {
            "id", "kind", "tier", "title", "author_org", "url", "language",
            "access", "status", "use_for", "source_lanes", "evidence_scope",
            "limitations", "reviewed_on",
        },
    },
    "masterworks": {
        "path": REFERENCE_ROOT / "masterwork-cards.jsonl",
        "required": {
            "id", "photographer", "title", "year", "direct_url", "source_org",
            "genres", "method_tags", "analysis_notes", "teaching_use", "anti_imitation",
            "coverage_genres", "creator_regions", "historical_period", "tradition_tags",
            "rights", "verification_status", "reviewed_on",
        },
    },
    "patterns": {
        "path": REFERENCE_ROOT / "critique-patterns.jsonl",
        "required": {
            "id", "method_tags", "condition", "visible_tests", "likely_effect", "counter_conditions",
            "actions", "exercise", "source_ids", "masterwork_ids", "score_dimensions",
            "scope", "confidence", "status",
        },
    },
}


def load(name: str, path: Path, required: set[str], errors: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        errors.append(f"{name}: cannot read {path}: {exc}")
        return records

    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_number}: invalid JSON: {exc}")
            continue
        if not isinstance(record, dict):
            errors.append(f"{path}:{line_number}: record must be an object")
            continue
        missing = sorted(required - record.keys())
        if missing:
            errors.append(f"{path}:{line_number}: missing fields: {', '.join(missing)}")
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            errors.append(f"{path}:{line_number}: id must be a non-empty string")
        elif record_id in seen:
            errors.append(f"{path}:{line_number}: duplicate id: {record_id}")
        else:
            seen.add(record_id)
        records.append(record)
    return records


def validate() -> tuple[list[str], dict[str, list[dict[str, Any]]]]:
    errors: list[str] = []
    collections = {
        name: load(name, spec["path"], spec["required"], errors)
        for name, spec in SCHEMAS.items()
    }

    for record in collections["sources"]:
        if record.get("tier") not in {1, 2, 3, 4}:
            errors.append(f"source {record.get('id')}: tier must be 1–4")
        if record.get("status") not in {"verified", "partial", "discovery_only"}:
            errors.append(f"source {record.get('id')}: invalid status")
        if not str(record.get("url", "")).startswith(("https://", "http://")):
            errors.append(f"source {record.get('id')}: invalid URL")
        if not isinstance(record.get("source_lanes"), list) or not record.get("source_lanes"):
            errors.append(f"source {record.get('id')}: source_lanes must be a non-empty list")

    for record in collections["masterworks"]:
        if not str(record.get("direct_url", "")).startswith(("https://", "http://")):
            errors.append(f"masterwork {record.get('id')}: invalid direct URL")
        if not isinstance(record.get("year"), int):
            errors.append(f"masterwork {record.get('id')}: year must be an integer")
        for field in (
            "genres", "method_tags", "analysis_notes", "coverage_genres",
            "creator_regions", "tradition_tags",
        ):
            if not isinstance(record.get(field), list) or not record.get(field):
                errors.append(f"masterwork {record.get('id')}: {field} must be a non-empty list")
        if record.get("historical_period") not in {"historical", "contemporary"}:
            errors.append(
                f"masterwork {record.get('id')}: historical_period must be historical or contemporary"
            )

    source_ids = {record.get("id") for record in collections["sources"]}
    masterwork_ids = {record.get("id") for record in collections["masterworks"]}
    for record in collections["patterns"]:
        if record.get("status") not in {"candidate", "provisional", "admitted", "retired"}:
            errors.append(f"pattern {record.get('id')}: invalid status")
        if record.get("confidence") not in {"low", "medium", "high"}:
            errors.append(f"pattern {record.get('id')}: invalid confidence")
        if not isinstance(record.get("method_tags"), list) or not record.get("method_tags"):
            errors.append(f"pattern {record.get('id')}: method_tags must be a non-empty list")
        missing_sources = sorted(set(record.get("source_ids", [])) - source_ids)
        missing_works = sorted(set(record.get("masterwork_ids", [])) - masterwork_ids)
        if missing_sources:
            errors.append(f"pattern {record.get('id')}: unknown source ids: {', '.join(missing_sources)}")
        if missing_works:
            errors.append(f"pattern {record.get('id')}: unknown masterwork ids: {', '.join(missing_works)}")
        if not record.get("counter_conditions"):
            errors.append(f"pattern {record.get('id')}: at least one counter-condition is required")
        if not record.get("actions") or not record.get("exercise"):
            errors.append(f"pattern {record.get('id')}: action and exercise are required")

    return errors, collections


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def count_values(records: list[dict[str, Any]], field: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for record in records:
        values = record.get(field, [])
        if isinstance(values, list):
            counts.update(value for value in values if isinstance(value, str) and value)
    return counts


def format_floor_progress(actual: Counter[str], floors: dict[str, int]) -> str:
    return ", ".join(
        f"{name}={actual.get(name, 0)}/{minimum}" for name, minimum in floors.items()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release",
        action="store_true",
        help="Fail unless all numerical release thresholds are met",
    )
    args = parser.parse_args()

    errors, collections = validate()
    try:
        status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read knowledge status: {exc}")
        status = {"release_thresholds": {}}

    actual = {
        "sources": len(collections["sources"]),
        "verified_sources": sum(
            record.get("status") == "verified" for record in collections["sources"]
        ),
        "masterworks": len(collections["masterworks"]),
        "patterns": len(collections["patterns"]),
        "admitted_patterns": sum(
            record.get("status") == "admitted" for record in collections["patterns"]
        ),
        "test_cases": count_jsonl(TEST_CASES_PATH),
    }
    thresholds = status.get("release_thresholds", {})
    coverage_floors = status.get("coverage_floors", {})
    lane_floors = coverage_floors.get("source_lanes", {})
    genre_floors = coverage_floors.get("genres", {})
    lane_counts = count_values(collections["sources"], "source_lanes")
    genre_counts = count_values(collections["masterworks"], "coverage_genres")
    region_counts = count_values(collections["masterworks"], "creator_regions")
    tradition_counts = count_values(collections["masterworks"], "tradition_tags")
    period_counts = Counter(
        record.get("historical_period") for record in collections["masterworks"]
        if record.get("historical_period")
    )

    allowed_lanes = set(status.get("coverage_requirements", {}).get("source_lanes", []))
    allowed_genres = set(status.get("coverage_requirements", {}).get("genres", []))
    for record in collections["sources"]:
        unknown = sorted(set(record.get("source_lanes", [])) - allowed_lanes)
        if unknown:
            errors.append(f"source {record.get('id')}: unknown source lanes: {', '.join(unknown)}")
    for record in collections["masterworks"]:
        unknown = sorted(set(record.get("coverage_genres", [])) - allowed_genres)
        if unknown:
            errors.append(f"masterwork {record.get('id')}: unknown coverage genres: {', '.join(unknown)}")

    if args.release:
        for metric, minimum in thresholds.items():
            if actual.get(metric, 0) < minimum:
                errors.append(
                    f"release threshold not met: {metric}={actual.get(metric, 0)} < {minimum}"
                )
        for lane, minimum in lane_floors.items():
            if lane_counts[lane] < minimum:
                errors.append(
                    f"source-lane floor not met: {lane}={lane_counts[lane]} < {minimum}"
                )
        for genre, minimum in genre_floors.items():
            if genre_counts[genre] < minimum:
                errors.append(
                    f"genre floor not met: {genre}={genre_counts[genre]} < {minimum}"
                )
        distinct_regions = len(region_counts)
        minimum_regions = coverage_floors.get("minimum_creator_regions", 0)
        if distinct_regions < minimum_regions:
            errors.append(
                f"creator-region floor not met: {distinct_regions} < {minimum_regions}"
            )
        distinct_traditions = len(tradition_counts)
        minimum_traditions = coverage_floors.get("minimum_photographic_traditions", 0)
        if distinct_traditions < minimum_traditions:
            errors.append(
                f"photographic-tradition floor not met: {distinct_traditions} < {minimum_traditions}"
            )
        for period, key in (("historical", "historical_works"), ("contemporary", "contemporary_works")):
            minimum = coverage_floors.get(key, 0)
            if period_counts[period] < minimum:
                errors.append(
                    f"period floor not met: {period}={period_counts[period]} < {minimum}"
                )

    if errors:
        print(f"FAIL: {len(errors)} knowledge-base issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    counts = ", ".join(f"{name}={len(records)}" for name, records in collections.items())
    progress = ", ".join(
        f"{metric}={value}/{thresholds.get(metric, '?')}" for metric, value in actual.items()
    )
    print(f"PASS: knowledge base is structurally valid ({counts})")
    print(f"Stage: {status.get('stage', 'unknown')} ({status.get('label', 'unlabeled')})")
    print(f"Release progress: {progress}")
    print(f"Source-lane coverage: {format_floor_progress(lane_counts, lane_floors)}")
    print(f"Genre coverage: {format_floor_progress(genre_counts, genre_floors)}")
    print(
        "Diversity coverage: "
        f"regions={len(region_counts)}/{coverage_floors.get('minimum_creator_regions', '?')}, "
        f"traditions={len(tradition_counts)}/{coverage_floors.get('minimum_photographic_traditions', '?')}, "
        f"historical={period_counts['historical']}/{coverage_floors.get('historical_works', '?')}, "
        f"contemporary={period_counts['contemporary']}/{coverage_floors.get('contemporary_works', '?')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
