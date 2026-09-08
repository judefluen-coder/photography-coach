#!/usr/bin/env python3
"""Validate a preregistered benchmark candidate selection before case assembly."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PLAN = ROOT / "references" / "benchmark-v4-plan.json"
CASES = ROOT / "references" / "benchmark-cases.jsonl"
DEVELOPMENT = ROOT / "references" / "benchmark-development-cases.jsonl"
V2_ARCHIVE = ROOT / "references" / "benchmark-v2-cases.jsonl"
MASTERWORKS = ROOT / "references" / "masterwork-cards.jsonl"
REQUIRED = {
    "candidate_id", "source_sha1", "source_page", "image_url", "preview_url",
    "title", "creator", "license", "assessment", "quality_role", "genre",
    "visible_observations", "must_not_infer", "selection_rationale",
}


def normalized_commons_title(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    if "/wiki/" not in path:
        return ""
    return urllib.parse.unquote(path.split("/wiki/", 1)[1]).replace("_", " ").casefold()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def validate_selection(
    selection_paths: list[Path],
    plan_path: Path = DEFAULT_PLAN,
) -> tuple[list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    rows = [row for path in selection_paths for row in load_jsonl(path)]
    allowed_roles = set(plan["quality_roles"])
    allowed_genres = set(plan["genre_role_counts"])
    allowed_operations = set(plan["failed_operation_counts"])

    seen_ids: set[str] = set()
    seen_sha1s: set[str] = set()
    seen_pages: set[str] = set()
    seen_images: set[str] = set()
    for index, row in enumerate(rows, 1):
        label = row.get("candidate_id", f"row-{index}")
        missing = REQUIRED - row.keys()
        if missing:
            errors.append(f"{label}: missing fields: {', '.join(sorted(missing))}")
        candidate_id = row.get("candidate_id")
        if candidate_id in seen_ids:
            errors.append(f"{label}: duplicate candidate_id")
        elif isinstance(candidate_id, str):
            seen_ids.add(candidate_id)
        sha1 = row.get("source_sha1")
        if not isinstance(sha1, str) or len(sha1) != 40:
            errors.append(f"{label}: source_sha1 must be 40 characters")
        elif sha1 in seen_sha1s:
            errors.append(f"{label}: duplicate source_sha1")
        else:
            seen_sha1s.add(sha1)
        page = row.get("source_page")
        if not isinstance(page, str) or not page.startswith(("https://", "http://")):
            errors.append(f"{label}: invalid source_page")
        elif page in seen_pages:
            errors.append(f"{label}: duplicate source_page")
        else:
            seen_pages.add(page)
        image_url = row.get("image_url")
        if not isinstance(image_url, str) or not image_url.startswith(("https://", "http://")):
            errors.append(f"{label}: invalid image_url")
        elif image_url in seen_images:
            errors.append(f"{label}: duplicate image_url")
        else:
            seen_images.add(image_url)
        if row.get("quality_role") not in allowed_roles:
            errors.append(f"{label}: invalid quality_role")
        expected_assessment = (
            "acclaimed" if row.get("quality_role") == "acclaimed" else "ordinary"
        )
        if row.get("assessment") != expected_assessment:
            errors.append(
                f"{label}: assessment {row.get('assessment')} does not support "
                f"quality_role {row.get('quality_role')}"
            )
        if row.get("genre") not in allowed_genres:
            errors.append(f"{label}: invalid genre")
        observations = row.get("visible_observations")
        if not isinstance(observations, list) or len(observations) < 2:
            errors.append(f"{label}: at least two visible_observations are required")
        unknowns = row.get("must_not_infer")
        if not isinstance(unknowns, list) or not unknowns:
            errors.append(f"{label}: at least one must_not_infer item is required")
        if row.get("quality_role") == "failed_base":
            if row.get("proposed_operation") not in allowed_operations:
                errors.append(f"{label}: failed_base needs a supported proposed_operation")

    prior_sha1s: set[str] = set()
    prior_pages: set[str] = set()
    prior_paths = {
        CASES,
        DEVELOPMENT,
        V2_ARCHIVE,
        *ROOT.glob("references/benchmark-v*-cases.jsonl"),
    }
    for path in sorted(prior_paths):
        if not path.exists():
            continue
        for row in load_jsonl(path):
            prior_sha1s.add(row.get("source_sha1", ""))
            prior_pages.add(row.get("source_page", ""))
    masterwork_pages = {row.get("direct_url", "") for row in load_jsonl(MASTERWORKS)}
    masterwork_titles = {
        normalized_commons_title(page) for page in masterwork_pages if page
    }
    for row in rows:
        label = row.get("candidate_id", "<unknown>")
        if row.get("source_sha1") in prior_sha1s:
            errors.append(f"{label}: source_sha1 overlaps an earlier benchmark")
        if row.get("source_page") in prior_pages:
            errors.append(f"{label}: source_page overlaps an earlier benchmark")
        if row.get("source_page") in masterwork_pages:
            errors.append(f"{label}: source_page overlaps a teaching masterwork")
        normalized_title = normalized_commons_title(row.get("source_page", ""))
        if normalized_title and normalized_title in masterwork_titles:
            errors.append(f"{label}: normalized Commons file overlaps a teaching masterwork")

    if len(rows) != plan["case_count"]:
        errors.append(f"selection count {len(rows)} != planned {plan['case_count']}")
    role_counts = Counter(row.get("quality_role") for row in rows)
    if dict(role_counts) != plan["quality_roles"]:
        errors.append(f"quality-role counts do not match plan: {dict(role_counts)}")
    for genre, quotas in plan["genre_role_counts"].items():
        actual = Counter(
            row.get("quality_role") for row in rows if row.get("genre") == genre
        )
        if dict(actual) != quotas:
            errors.append(f"{genre}: role counts {dict(actual)} != {quotas}")
    operation_counts = Counter(
        row.get("proposed_operation")
        for row in rows if row.get("quality_role") == "failed_base"
    )
    if dict(operation_counts) != plan["failed_operation_counts"]:
        errors.append(f"failed-operation counts do not match plan: {dict(operation_counts)}")
    return errors, rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selections", nargs="+", type=Path)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    args = parser.parse_args()
    try:
        errors, rows = validate_selection(args.selections, args.plan)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot validate selection: {exc}", file=sys.stderr)
        return 2
    if errors:
        print(f"FAIL: {len(errors)} candidate-selection issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    split = json.loads(args.plan.read_text(encoding="utf-8")).get("split", "benchmark")
    print(f"PASS: {len(rows)} source-disjoint candidates match the preregistered {split} plan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
