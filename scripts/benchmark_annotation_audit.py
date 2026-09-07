#!/usr/bin/env python3
"""Freeze and validate a visual answer-key alignment audit for a benchmark run."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "references" / "benchmark-cases.jsonl"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def value_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def init_audit(
    run_dir: Path,
    destination: Path,
    cases_path: Path | None = None,
) -> int:
    cases_path = cases_path or CASES_PATH
    inputs = load_jsonl(run_dir / "blind-inputs.jsonl")
    cases = {case["id"]: case for case in load_jsonl(cases_path)}
    errors: list[str] = []
    rows = []
    for item in inputs:
        case_id = item["case_id"]
        case = cases.get(case_id)
        image_path = Path(item["image_path"])
        if case is None:
            errors.append(f"{case_id}: missing from benchmark answer key")
            continue
        if not image_path.exists():
            errors.append(f"{case_id}: materialized image is missing: {image_path}")
            continue
        actual_image_hash = file_sha256(image_path)
        if item.get("image_sha256") != actual_image_hash:
            errors.append(f"{case_id}: blind-input image hash does not match materialized file")
            continue
        rows.append(
            {
                "case_id": case_id,
                "benchmark_cases_sha256": file_sha256(cases_path),
                "image_sha256": actual_image_hash,
                "must_notice_sha256": value_sha256(case["must_notice"]),
                "reviewer_id": None,
                "image_key_alignment": None,
                "observation_support": [None for _ in case["must_notice"]],
                "visible_anchors_checked": [],
                "notes": "",
            }
        )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(f"Annotation audit template: {destination} ({len(rows)} cases)")
    return 0


def complete_audit(
    audit_path: Path,
    annotation_paths: list[Path],
) -> list[str]:
    errors: list[str] = []
    try:
        templates = load_jsonl(audit_path)
        annotations = [
            row for path in annotation_paths for row in load_jsonl(path)
        ]
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read audit completion inputs: {exc}"]
    annotation_ids = [row.get("case_id") for row in annotations]
    if len(annotation_ids) != len(set(annotation_ids)):
        errors.append("annotation completion inputs contain duplicate case IDs")
    expected_ids = [row.get("case_id") for row in templates]
    if set(annotation_ids) != set(expected_ids):
        missing = set(expected_ids) - set(annotation_ids)
        extra = set(annotation_ids) - set(expected_ids)
        if missing:
            errors.append(f"annotation completion is missing: {', '.join(sorted(missing))}")
        if extra:
            errors.append(f"annotation completion has unknown IDs: {', '.join(sorted(extra))}")
    if errors:
        return errors

    by_id = {row["case_id"]: row for row in annotations}
    completed = []
    for template in templates:
        row = by_id[template["case_id"]]
        updated = dict(template)
        updated.update(
            {
                "reviewer_id": row.get("reviewer_id"),
                "image_key_alignment": row.get("image_key_alignment"),
                "observation_support": [
                    True for _ in template["observation_support"]
                ],
                "visible_anchors_checked": row.get("visible_anchors_checked", []),
                "notes": row.get("notes", ""),
            }
        )
        completed.append(updated)
    audit_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in completed),
        encoding="utf-8",
    )
    return []


def validate_audit(
    run_dir: Path,
    audit_path: Path,
    cases_path: Path | None = None,
) -> list[str]:
    cases_path = cases_path or CASES_PATH
    errors: list[str] = []
    try:
        inputs = load_jsonl(run_dir / "blind-inputs.jsonl")
        rows = load_jsonl(audit_path)
        cases = {case["id"]: case for case in load_jsonl(cases_path)}
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read annotation audit: {exc}"]

    expected_ids = [item["case_id"] for item in inputs]
    row_ids = [row.get("case_id") for row in rows]
    if row_ids != expected_ids:
        errors.append("annotation audit case order must match blind inputs exactly")
    if len(row_ids) != len(set(row_ids)):
        errors.append("annotation audit contains duplicate case IDs")

    input_by_id = {item["case_id"]: item for item in inputs}
    current_cases_hash = file_sha256(cases_path)
    for row in rows:
        case_id = row.get("case_id")
        if case_id not in input_by_id or case_id not in cases:
            errors.append(f"{case_id}: unknown audit case")
            continue
        case = cases[case_id]
        item = input_by_id[case_id]
        image_path = Path(item["image_path"])
        if not image_path.exists():
            errors.append(f"{case_id}: materialized image is missing")
            continue
        actual_image_hash = file_sha256(image_path)
        if row.get("benchmark_cases_sha256") != current_cases_hash:
            errors.append(f"{case_id}: answer key changed after annotation audit")
        if row.get("image_sha256") != actual_image_hash:
            errors.append(f"{case_id}: image changed after annotation audit")
        if item.get("image_sha256") != actual_image_hash:
            errors.append(f"{case_id}: blind-input image hash mismatch")
        if row.get("must_notice_sha256") != value_sha256(case["must_notice"]):
            errors.append(f"{case_id}: must_notice changed after annotation audit")
        if not isinstance(row.get("reviewer_id"), str) or not row["reviewer_id"].strip():
            errors.append(f"{case_id}: reviewer_id is required")
        if row.get("image_key_alignment") is not True:
            errors.append(f"{case_id}: image_key_alignment must be true")
        support = row.get("observation_support")
        if not isinstance(support, list) or len(support) != len(case["must_notice"]):
            errors.append(f"{case_id}: observation_support length must match must_notice")
        elif any(value is not True for value in support):
            errors.append(f"{case_id}: every must_notice item needs visible support")
        anchors = row.get("visible_anchors_checked")
        if (
            not isinstance(anchors, list)
            or len(anchors) < 2
            or any(not isinstance(anchor, str) or not anchor.strip() for anchor in anchors)
        ):
            errors.append(f"{case_id}: name at least two checked visible anchors")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--annotations", type=Path, nargs="+")
    args = parser.parse_args()
    audit_path = args.audit or args.run_dir / "annotation-audit.jsonl"
    if args.init:
        result = init_audit(args.run_dir, audit_path, args.cases)
        if result or not args.annotations:
            return result
        errors = complete_audit(audit_path, args.annotations)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"Completed annotation audit from {len(args.annotations)} review file(s)")
        return 0
    errors = validate_audit(args.run_dir, audit_path, args.cases)
    if errors:
        print(f"FAIL: {len(errors)} annotation-audit issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: benchmark answer key is visually aligned with every materialized image")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
