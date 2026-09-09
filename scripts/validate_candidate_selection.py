#!/usr/bin/env python3
"""Validate a preregistered benchmark candidate selection before case assembly."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.parse
from collections import Counter
from pathlib import Path
from typing import Any

from build_historical_source_exclusions import normalized_url


ROOT = Path(__file__).resolve().parent.parent
# Compatibility exports for the case assembler. The validator CLI itself requires
# an explicit plan and takes its candidate-manifest path from that plan or the CLI.
DEFAULT_PLAN = ROOT / "references" / "benchmark-v5-plan.json"
DEFAULT_CANDIDATE_MANIFEST = (
    ROOT / ".benchmark-runs" / "v5-review" / "candidate-manifest.jsonl"
)
REQUIRED = {
    "candidate_id", "source_sha1", "source_page", "image_url", "preview_url",
    "title", "creator", "license", "assessment", "quality_role", "genre",
    "visible_observations", "must_not_infer", "selection_rationale",
}
MANIFEST_IDENTITY_FIELDS = (
    "source_sha1", "source_page", "image_url", "preview_url", "title", "creator",
    "license", "assessment",
)


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


def resolve_plan_path(plan_path: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else plan_path.parent / path


def validate_plan(plan: dict[str, Any], errors: list[str]) -> None:
    split = plan.get("split")
    if not isinstance(split, str) or not split.startswith("blind_holdout_v"):
        errors.append("plan split must be a versioned blind_holdout_vN")
    if not isinstance(plan.get("blind_prompt"), str) or not plan["blind_prompt"].strip():
        errors.append("plan requires a non-empty blind_prompt")

    case_count = plan.get("case_count")
    quality_roles = plan.get("quality_roles", {})
    genre_role_counts = plan.get("genre_role_counts", {})
    operation_counts = plan.get("failed_operation_counts", {})
    recipe_profiles = plan.get("failure_recipe_profiles", {})
    if not isinstance(case_count, int) or isinstance(case_count, bool) or case_count < 1:
        errors.append("plan case_count must be a positive integer")
    if not isinstance(quality_roles, dict) or not quality_roles:
        errors.append("plan quality_roles must be a non-empty object")
    elif sum(quality_roles.values()) != case_count:
        errors.append("plan quality-role counts do not sum to case_count")
    if not isinstance(genre_role_counts, dict) or not genre_role_counts:
        errors.append("plan genre_role_counts must be a non-empty object")
    elif isinstance(quality_roles, dict):
        totals: Counter[str] = Counter()
        for genre, quotas in genre_role_counts.items():
            if not isinstance(quotas, dict) or set(quotas) != set(quality_roles):
                errors.append(f"plan {genre}: role quota keys do not match quality_roles")
                continue
            totals.update(quotas)
        if dict(totals) != quality_roles:
            errors.append("plan genre-role quotas do not sum to quality_roles")
    if not isinstance(operation_counts, dict) or not operation_counts:
        errors.append("plan failed_operation_counts must be a non-empty object")
    elif sum(operation_counts.values()) != quality_roles.get("failed_base"):
        errors.append("plan failed-operation counts do not sum to failed_base")
    if not isinstance(recipe_profiles, dict) or set(recipe_profiles) != set(operation_counts):
        errors.append("plan failure_recipe_profiles keys do not match failed operations")
    else:
        for operation, count in operation_counts.items():
            profiles = recipe_profiles.get(operation)
            if not isinstance(profiles, list) or len(profiles) != count:
                errors.append(
                    f"plan {operation}: recipe profile count must equal operation count {count}"
                )

    assessment_map = plan.get("assessment_by_quality_role")
    if not isinstance(assessment_map, dict) or set(assessment_map) != set(quality_roles):
        errors.append("plan assessment_by_quality_role keys do not match quality_roles")
    review_genre_map = plan.get("candidate_review_genre_map")
    if not isinstance(review_genre_map, dict) or not review_genre_map:
        errors.append("plan requires candidate_review_genre_map")


def load_exclusion_snapshot(
    plan: dict[str, Any],
    plan_path: Path,
    errors: list[str],
) -> tuple[set[str], set[str], set[str], set[str]]:
    snapshot = plan.get("exclusion_snapshot")
    if not isinstance(snapshot, dict):
        errors.append("plan requires an exclusion_snapshot object")
        return set(), set(), set(), set()
    value = snapshot.get("path")
    expected_hash = snapshot.get("sha256")
    expected_count = snapshot.get("source_count")
    if not isinstance(value, str) or not value:
        errors.append("exclusion_snapshot requires a path")
        return set(), set(), set(), set()
    path = resolve_plan_path(plan_path, value)
    try:
        payload_bytes = path.read_bytes()
    except OSError as exc:
        errors.append(f"cannot read exclusion snapshot {value}: {exc}")
        return set(), set(), set(), set()
    actual_hash = hashlib.sha256(payload_bytes).hexdigest()
    if actual_hash != expected_hash:
        errors.append(f"exclusion snapshot sha256 {actual_hash} != {expected_hash}")
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError as exc:
        errors.append(f"invalid exclusion snapshot JSON {value}: {exc}")
        return set(), set(), set(), set()
    sources = payload.get("sources") if isinstance(payload, dict) else None
    if not isinstance(sources, list):
        errors.append("exclusion snapshot requires a sources list")
        return set(), set(), set(), set()
    if payload.get("source_count") != len(sources):
        errors.append("exclusion snapshot source_count does not match its sources")
    if payload.get("source_count") != expected_count:
        errors.append(
            f"exclusion snapshot source count {payload.get('source_count')} "
            f"!= preregistered {expected_count}"
        )
    hash_fields = (
        "schema_version",
        "source_files",
        "source_sha1s",
        "source_pages",
        "image_urls",
        "sources",
    )
    canonical_payload = {field: payload.get(field) for field in hash_fields}
    canonical_bytes = json.dumps(
        canonical_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    actual_overall_hash = hashlib.sha256(canonical_bytes).hexdigest()
    expected_overall_hash = snapshot.get("overall_sha256")
    if expected_overall_hash and expected_overall_hash != actual_overall_hash:
        errors.append(
            "exclusion snapshot canonical hash differs from the preregistered plan"
        )
    for field in ("overall_sha256", "snapshot_sha256"):
        if payload.get(field) != actual_overall_hash:
            errors.append(f"exclusion snapshot {field} does not match its canonical payload")

    prior_sha1s: set[str] = set()
    prior_pages: set[str] = set()
    prior_images: set[str] = set()
    normalized_pages: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            errors.append("exclusion snapshot sources must be objects")
            continue
        for field, target in (
            ("source_sha1s", prior_sha1s),
            ("source_pages", prior_pages),
            ("image_urls", prior_images),
        ):
            values = source.get(field)
            if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
                errors.append(f"exclusion snapshot source requires string list {field}")
                continue
            target.update(values)
        normalized_pages.update(
            title for title in map(normalized_commons_title, source.get("source_pages", []))
            if title
        )
    for field, derived in (
        ("source_sha1s", prior_sha1s),
        ("source_pages", prior_pages),
        ("image_urls", prior_images),
    ):
        declared = payload.get(field)
        if not isinstance(declared, list) or set(declared) != derived:
            errors.append(f"exclusion snapshot top-level {field} differs from sources")
    return (
        prior_sha1s - {""},
        prior_pages - {""},
        prior_images - {""},
        normalized_pages,
    )


def validate_selection(
    selection_paths: list[Path],
    plan_path: Path,
    candidate_manifest_path: Path | None = None,
) -> tuple[list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    validate_plan(plan, errors)
    rows = [row for path in selection_paths for row in load_jsonl(path)]
    allowed_roles = set(plan["quality_roles"])
    allowed_genres = set(plan["genre_role_counts"])
    allowed_operations = set(plan["failed_operation_counts"])

    manifest_by_id: dict[str, dict[str, Any]] = {}
    candidate_pool = plan.get("candidate_pool")
    if candidate_pool:
        if candidate_pool.get("status") != "frozen":
            errors.append("candidate pool status must be frozen before selection")
        planned_manifest = candidate_pool.get("manifest_path")
        if not isinstance(planned_manifest, str) or not planned_manifest:
            errors.append("candidate pool requires a preregistered manifest_path")
        if candidate_manifest_path is None and isinstance(planned_manifest, str):
            candidate_manifest_path = resolve_plan_path(plan_path, planned_manifest)
        elif candidate_manifest_path is not None and isinstance(planned_manifest, str):
            expected_path = resolve_plan_path(plan_path, planned_manifest)
            if candidate_manifest_path.resolve() != expected_path.resolve():
                errors.append("candidate manifest path differs from the preregistered plan")
        expected_hash = candidate_pool.get("manifest_sha256")
        expected_count = candidate_pool.get("candidate_count")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            errors.append("candidate pool is not frozen: manifest_sha256 is required")
        if (
            not isinstance(expected_count, int)
            or isinstance(expected_count, bool)
            or expected_count < 1
        ):
            errors.append("candidate pool is not frozen: candidate_count is required")
        if candidate_manifest_path is None:
            errors.append("candidate manifest is required by the preregistered plan")
        elif not isinstance(expected_hash, str) or len(expected_hash) != 64:
            pass
        elif (
            not isinstance(expected_count, int)
            or isinstance(expected_count, bool)
            or expected_count < 1
        ):
            pass
        else:
            manifest_bytes = candidate_manifest_path.read_bytes()
            actual_hash = hashlib.sha256(manifest_bytes).hexdigest()
            if actual_hash != expected_hash:
                errors.append(
                    f"candidate manifest sha256 {actual_hash} != preregistered {expected_hash}"
                )
            manifest_rows = load_jsonl(candidate_manifest_path)
            if len(manifest_rows) != expected_count:
                errors.append(
                    f"candidate manifest count {len(manifest_rows)} != preregistered "
                    f"{expected_count}"
                )
            for manifest_row in manifest_rows:
                manifest_id = manifest_row.get("candidate_id")
                if not isinstance(manifest_id, str):
                    errors.append("candidate manifest contains a row without candidate_id")
                elif manifest_id in manifest_by_id:
                    errors.append(f"candidate manifest has duplicate candidate_id {manifest_id}")
                else:
                    manifest_by_id[manifest_id] = manifest_row
    elif candidate_manifest_path is not None:
        errors.append("candidate manifest was supplied but the plan has no candidate_pool")

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
        expected_assessment = plan["assessment_by_quality_role"].get(row.get("quality_role"))
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
        if candidate_pool and manifest_by_id:
            frozen = manifest_by_id.get(candidate_id)
            if frozen is None:
                errors.append(f"{label}: candidate_id is not in the frozen candidate manifest")
            else:
                for field in MANIFEST_IDENTITY_FIELDS:
                    if row.get(field) != frozen.get(field):
                        errors.append(
                            f"{label}: {field} differs from the frozen candidate manifest"
                        )
                expected_genre = plan["candidate_review_genre_map"].get(
                    frozen.get("review_genre")
                )
                if expected_genre is None:
                    errors.append(f"{label}: frozen candidate has invalid review_genre")
                elif row.get("genre") != expected_genre:
                    errors.append(
                        f"{label}: genre {row.get('genre')} differs from frozen pool lane "
                        f"{expected_genre}"
                    )

    prior_sha1s, prior_pages, prior_images, excluded_titles = load_exclusion_snapshot(
        plan, plan_path, errors
    )
    for row in rows:
        label = row.get("candidate_id", "<unknown>")
        if row.get("source_sha1") in prior_sha1s:
            errors.append(f"{label}: source_sha1 overlaps an earlier benchmark")
        if normalized_url(row.get("source_page")) in prior_pages:
            errors.append(f"{label}: source_page overlaps an earlier benchmark")
        if normalized_url(row.get("image_url")) in prior_images:
            errors.append(f"{label}: image_url overlaps an earlier benchmark")
        normalized_title = normalized_commons_title(row.get("source_page", ""))
        if normalized_title and normalized_title in excluded_titles:
            errors.append(f"{label}: normalized Commons file overlaps the exclusion snapshot")

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
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument(
        "--candidate-manifest", type=Path,
    )
    args = parser.parse_args()
    try:
        errors, rows = validate_selection(
            args.selections, args.plan, args.candidate_manifest,
        )
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
