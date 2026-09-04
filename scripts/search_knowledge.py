#!/usr/bin/env python3
"""Search Photography Coach JSONL knowledge records by tags and text."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parent.parent
COLLECTIONS = {
    "sources": SKILL_ROOT / "references" / "source-registry.jsonl",
    "masterworks": SKILL_ROOT / "references" / "masterwork-cards.jsonl",
    "patterns": SKILL_ROOT / "references" / "critique-patterns.jsonl",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
            record["_collection"] = path.stem
            records.append(record)
    return records


def searchable_text(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False).lower()


def tokenize(query: str) -> list[str]:
    return [token for token in re.split(r"[\s,;/]+", query.lower()) if token]


def score(record: dict[str, Any], tokens: list[str]) -> int:
    haystack = searchable_text(record)
    record_id = str(record.get("id", "")).lower()
    tag_text = " ".join(
        str(item).lower()
        for field in ("method_tags", "use_for", "genres", "score_dimensions")
        for item in record.get(field, [])
    )
    total = 0
    for token in tokens:
        if token in record_id:
            total += 5
        if token in tag_text:
            total += 4
        if token in haystack:
            total += 1
    return total


def compact_record(record: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "title",
        "photographer",
        "author_org",
        "year",
        "kind",
        "tier",
        "status",
        "verification_status",
        "genres",
        "method_tags",
        "use_for",
        "condition",
        "teaching_use",
        "anti_imitation",
        "direct_url",
        "url",
    )
    return {"collection": record.get("_collection"), **{key: record[key] for key in keys if key in record}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Space- or comma-separated method tags or words")
    parser.add_argument(
        "--collection",
        choices=("all", *COLLECTIONS),
        default="all",
        help="Knowledge collection to search",
    )
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of compact text")
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be positive")

    selected = COLLECTIONS.values() if args.collection == "all" else (COLLECTIONS[args.collection],)
    try:
        records = [record for path in selected for record in load_jsonl(path)]
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    tokens = tokenize(args.query)
    if not tokens:
        parser.error("query must contain at least one word")

    ranked = sorted(
        ((score(record, tokens), record) for record in records),
        key=lambda pair: (-pair[0], str(pair[1].get("id", ""))),
    )
    matches = [compact_record(record) for points, record in ranked if points > 0][: args.limit]

    if args.json:
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        for record in matches:
            label = record.get("title") or record.get("condition") or record.get("id")
            creator = record.get("photographer") or record.get("author_org") or ""
            url = record.get("direct_url") or record.get("url") or ""
            print(f"[{record['collection']}] {record['id']}: {label}")
            if creator:
                print(f"  creator/source: {creator}")
            if url:
                print(f"  url: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
