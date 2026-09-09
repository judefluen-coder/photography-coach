#!/usr/bin/env python3
"""Freeze a source-disjoint candidate pool from a reviewed candidate manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from build_historical_source_exclusions import normalized_sha1, normalized_url


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = (
    ROOT / ".benchmark-runs" / "v4-review" / "candidate-manifest.jsonl"
)
DEFAULT_EXCLUSIONS = (
    ROOT / ".benchmark-runs" / "v5-draft" / "historical-source-exclusions.json"
)
DEFAULT_OUTPUT = (
    ROOT / ".benchmark-runs" / "v5-review" / "candidate-manifest.jsonl"
)
REQUIRED_LANES = {
    "architecture": {"acclaimed": 10, "ordinary": 20},
    "landscapes": {"acclaimed": 10, "ordinary": 20},
    "people": {"acclaimed": 10, "ordinary": 20},
    "sports": {"acclaimed": 10, "ordinary": 20},
    "food": {"acclaimed": 10, "ordinary": 20},
    "sculptures": {"acclaimed": 10, "ordinary": 20},
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_number}: row must be an object")
        rows.append(row)
    return rows


def exclusion_sets(snapshot: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    return (
        {normalized_sha1(value) for value in snapshot.get("source_sha1s", [])} - {""},
        {normalized_url(value) for value in snapshot.get("source_pages", [])} - {""},
        {normalized_url(value) for value in snapshot.get("image_urls", [])} - {""},
    )


def freeze_pool(
    rows: list[dict[str, Any]], snapshot: dict[str, Any]
) -> list[dict[str, Any]]:
    excluded_sha1s, excluded_pages, excluded_images = exclusion_sets(snapshot)
    kept: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_sha1s: set[str] = set()
    seen_pages: set[str] = set()
    seen_images: set[str] = set()
    for row in rows:
        candidate_id = row.get("candidate_id")
        sha1 = normalized_sha1(row.get("source_sha1"))
        page = normalized_url(row.get("source_page"))
        image = normalized_url(row.get("image_url"))
        if sha1 in excluded_sha1s or page in excluded_pages or image in excluded_images:
            continue
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ValueError("candidate_id must be a non-empty string")
        if not sha1 or not page or not image:
            raise ValueError(f"{candidate_id}: incomplete source identity")
        if candidate_id in seen_ids:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        if sha1 in seen_sha1s or page in seen_pages or image in seen_images:
            raise ValueError(f"duplicate source identity in candidate pool: {candidate_id}")
        seen_ids.add(candidate_id)
        seen_sha1s.add(sha1)
        seen_pages.add(page)
        seen_images.add(image)
        kept.append(dict(row))

    counts = Counter((row.get("review_genre"), row.get("assessment")) for row in kept)
    for genre, assessment_counts in REQUIRED_LANES.items():
        for assessment, minimum in assessment_counts.items():
            actual = counts[(genre, assessment)]
            if actual < minimum:
                raise ValueError(
                    f"candidate lane {genre}/{assessment} has {actual}; needs at least {minimum}"
                )
    return kept


def serialized_jsonl(rows: list[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--exclusions", type=Path, default=DEFAULT_EXCLUSIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    snapshot_bytes = args.exclusions.read_bytes()
    snapshot = json.loads(snapshot_bytes)
    expected_snapshot_hash = snapshot.get("snapshot_sha256")
    if expected_snapshot_hash != snapshot.get("overall_sha256"):
        raise ValueError("exclusion snapshot self-hash fields disagree")
    rows = freeze_pool(load_jsonl(args.source), snapshot)
    payload = serialized_jsonl(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    counts = Counter((row["review_genre"], row["assessment"]) for row in rows)
    print(
        json.dumps(
            {
                "candidate_count": len(rows),
                "manifest_sha256": hashlib.sha256(payload).hexdigest(),
                "exclusion_snapshot_file_sha256": hashlib.sha256(snapshot_bytes).hexdigest(),
                "exclusion_snapshot_overall_sha256": expected_snapshot_hash,
                "lane_counts": {
                    f"{genre}/{assessment}": count
                    for (genre, assessment), count in sorted(counts.items())
                },
                "output": str(args.output),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
