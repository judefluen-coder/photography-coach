#!/usr/bin/env python3
"""Merge materialized-image reviews into a frozen benchmark answer key."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def merge(
    cases: list[dict[str, Any]], annotations: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    case_ids = [case.get("id") for case in cases]
    annotation_ids = [row.get("case_id") for row in annotations]
    if len(annotation_ids) != len(set(annotation_ids)):
        errors.append("annotation case IDs must be unique")
    missing = set(case_ids) - set(annotation_ids)
    extra = set(annotation_ids) - set(case_ids)
    if missing:
        errors.append(f"missing annotations: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"unknown annotations: {', '.join(sorted(extra))}")

    by_id = {row.get("case_id"): row for row in annotations}
    merged: list[dict[str, Any]] = []
    for case in cases:
        case_id = case["id"]
        row = by_id.get(case_id)
        if row is None:
            continue
        notices = row.get("must_notice")
        boundaries = row.get("must_not_infer")
        anchors = row.get("visible_anchors_checked")
        if not isinstance(notices, list) or not 2 <= len(notices) <= 3:
            errors.append(f"{case_id}: must_notice must contain 2-3 items")
        elif any(not isinstance(item, str) or not item.strip() for item in notices):
            errors.append(f"{case_id}: must_notice items must be non-empty strings")
        if not isinstance(boundaries, list) or not 1 <= len(boundaries) <= 2:
            errors.append(f"{case_id}: must_not_infer must contain 1-2 items")
        elif any(not isinstance(item, str) or not item.strip() for item in boundaries):
            errors.append(f"{case_id}: must_not_infer items must be non-empty strings")
        if not isinstance(anchors, list) or len(anchors) < 2:
            errors.append(f"{case_id}: at least two visible anchors are required")
        elif any(not isinstance(item, str) or not item.strip() for item in anchors):
            errors.append(f"{case_id}: visible anchors must be non-empty strings")
        if row.get("image_key_alignment") is not True:
            errors.append(f"{case_id}: image_key_alignment must be true")
        reviewer = row.get("reviewer_id")
        if not isinstance(reviewer, str) or not reviewer.strip():
            errors.append(f"{case_id}: reviewer_id is required")

        updated = dict(case)
        updated["must_notice"] = notices
        updated["must_not_infer"] = boundaries
        updated["annotation_status"] = "materialized-image-verified"
        merged.append(updated)
    return merged, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cases = load_jsonl(args.cases)
    annotations = [row for path in args.annotations for row in load_jsonl(path)]
    merged, errors = merge(cases, annotations)
    if errors:
        print(f"FAIL: {len(errors)} annotation merge issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in merged),
        encoding="utf-8",
    )
    print(f"PASS: merged {len(merged)} materialized-image annotations -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
