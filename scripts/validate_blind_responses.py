#!/usr/bin/env python3
"""Validate that every blind-run response exists, is unique, and meets the response contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from validate_response import validate


def validate_run(run_dir: Path) -> tuple[list[str], int, int]:
    inputs_path = run_dir / "blind-inputs.jsonl"
    try:
        inputs = [
            json.loads(line)
            for line in inputs_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read blind inputs: {exc}"], 0, 0

    errors: list[str] = []
    ids = [item.get("case_id") for item in inputs]
    duplicates = [case_id for case_id, count in Counter(ids).items() if count > 1]
    if duplicates:
        errors.append(f"duplicate case IDs: {', '.join(sorted(duplicates))}")
    ordinals = [item.get("ordinal") for item in inputs]
    if sorted(ordinals) != list(range(1, len(inputs) + 1)):
        errors.append("ordinals must be consecutive and unique")

    response_hashes: dict[str, str] = {}
    valid = 0
    for item in inputs:
        case_id = item.get("case_id", "<missing>")
        path = Path(item.get("response_path", ""))
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{case_id}: cannot read response: {exc}")
            continue
        if not text.strip():
            errors.append(f"{case_id}: response is empty")
            continue
        response_errors = validate(
            text,
            require_integrity_probe=True,
            require_reference=True,
        )
        if response_errors:
            errors.extend(f"{case_id}: {error}" for error in response_errors)
            continue
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest in response_hashes:
            errors.append(
                f"{case_id}: byte-identical response duplicates {response_hashes[digest]}"
            )
            continue
        response_hashes[digest] = case_id
        valid += 1

    return errors, valid, len(inputs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    errors, valid, total = validate_run(args.run_dir)
    if errors:
        print(f"FAIL: {valid}/{total} responses valid; {len(errors)} issue(s)")
        for error in errors[:30]:
            print(f"- {error}")
        if len(errors) > 30:
            print(f"- ... {len(errors) - 30} additional issue(s) omitted")
        return 1
    print(f"PASS: {valid}/{total} frozen responses are present, unique, and structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
