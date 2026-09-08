#!/usr/bin/env python3
"""Merge disjoint grade fragments while preserving the frozen template order."""

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
    template: list[dict[str, Any]], fragments: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    template_ids = [row.get("case_id") for row in template]
    fragment_ids = [row.get("case_id") for row in fragments]
    if len(fragment_ids) != len(set(fragment_ids)):
        errors.append("grade fragments contain duplicate case IDs")
    missing = set(template_ids) - set(fragment_ids)
    extra = set(fragment_ids) - set(template_ids)
    if missing:
        errors.append(f"grade fragments are missing: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"grade fragments contain unknown IDs: {', '.join(sorted(extra))}")
    by_id = {row.get("case_id"): row for row in fragments}
    merged: list[dict[str, Any]] = []
    for frozen in template:
        case_id = frozen["case_id"]
        row = by_id.get(case_id)
        if row is None:
            continue
        if row.get("response_sha256") != frozen.get("response_sha256"):
            errors.append(f"{case_id}: response hash differs from frozen template")
        merged.append(row)
    return merged, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--fragments", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    template = load_jsonl(args.template)
    fragments = [row for path in args.fragments for row in load_jsonl(path)]
    merged, errors = merge(template, fragments)
    if errors:
        print(f"FAIL: {len(errors)} grade-merge issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in merged),
        encoding="utf-8",
    )
    print(f"PASS: merged {len(merged)} frozen grades -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
