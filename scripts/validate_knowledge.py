#!/usr/bin/env python3
"""Validate Photography Coach knowledge records and cross-references."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
REFERENCE_ROOT = ROOT / "references"
SCHEMAS = {
    "sources": {
        "path": REFERENCE_ROOT / "source-registry.jsonl",
        "required": {
            "id", "kind", "tier", "title", "author_org", "url", "language",
            "access", "status", "use_for", "evidence_scope", "limitations", "reviewed_on",
        },
    },
    "masterworks": {
        "path": REFERENCE_ROOT / "masterwork-cards.jsonl",
        "required": {
            "id", "photographer", "title", "year", "direct_url", "source_org",
            "genres", "method_tags", "analysis_notes", "teaching_use", "anti_imitation",
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

    for record in collections["masterworks"]:
        if not str(record.get("direct_url", "")).startswith(("https://", "http://")):
            errors.append(f"masterwork {record.get('id')}: invalid direct URL")
        if not isinstance(record.get("year"), int):
            errors.append(f"masterwork {record.get('id')}: year must be an integer")
        for field in ("genres", "method_tags", "analysis_notes"):
            if not isinstance(record.get(field), list) or not record.get(field):
                errors.append(f"masterwork {record.get('id')}: {field} must be a non-empty list")

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


def main() -> int:
    errors, collections = validate()
    if errors:
        print(f"FAIL: {len(errors)} knowledge-base issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    counts = ", ".join(f"{name}={len(records)}" for name, records in collections.items())
    print(f"PASS: knowledge base is structurally valid ({counts})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
