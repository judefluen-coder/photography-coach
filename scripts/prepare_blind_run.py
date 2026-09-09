#!/usr/bin/env python3
"""Create a shuffled blind-run packet without copying benchmark labels or keys."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
from datetime import datetime, timezone
from pathlib import Path

from materialize_benchmark import (
    CASES_PATH,
    DEFAULT_OUTPUT,
    load_cases,
    materialize,
    write_manifest_atomic,
)
from protocol_fingerprint import protocol_sha256


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RUN_ROOT = ROOT / ".benchmark-runs"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


REUSE_CASE_FIELDS = (
    "source_sha1",
    "source_page",
    "variant_recipe",
    "quality_band",
    "genre",
)


def load_verified_reuse_items(
    manifest_path: Path,
    cases: list[dict[str, object]],
    images_dir: Path,
    *,
    require_all: bool = True,
) -> dict[str, dict[str, object]]:
    """Load reusable outputs only when manifest identity and bytes still match."""
    if not manifest_path.is_file():
        if require_all:
            raise ValueError(f"trusted reuse manifest is missing: {manifest_path}")
        return {}
    existing = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(existing, list):
        raise ValueError(f"reuse manifest must be a JSON array: {manifest_path}")

    case_by_id = {case["id"]: case for case in cases}
    verified: dict[str, dict[str, object]] = {}
    for item in existing:
        if not isinstance(item, dict):
            raise ValueError(f"reuse manifest contains a non-object item: {manifest_path}")
        case_id = item.get("id")
        if case_id not in case_by_id:
            continue
        if case_id in verified:
            raise ValueError(f"{case_id}: duplicate item in reuse manifest")
        case = case_by_id[case_id]
        for field in REUSE_CASE_FIELDS:
            if field not in item:
                raise ValueError(f"{case_id}: reuse manifest is missing {field}")
            if item[field] != case[field]:
                raise ValueError(f"{case_id}: reuse manifest {field} mismatch")
        if "output_sha256" not in item:
            raise ValueError(f"{case_id}: reuse manifest is missing output_sha256")

        image_path = images_dir / f"{case_id}.jpg"
        if not image_path.is_file():
            raise ValueError(f"{case_id}: reusable image is missing: {image_path}")
        actual_hash = file_sha256(image_path)
        if actual_hash != item["output_sha256"]:
            raise ValueError(f"{case_id}: reusable image SHA-256 mismatch")
        verified[case_id] = dict(item)

    if require_all:
        missing = [case["id"] for case in cases if case["id"] not in verified]
        if missing:
            raise ValueError(
                "reuse manifest is missing requested case IDs: " + ", ".join(missing)
            )
    return verified


def reused_materialization_record(
    case: dict[str, object],
    trusted_item: dict[str, object],
    destination: Path,
) -> dict[str, object]:
    """Retarget a verified rich manifest item to its blind-run destination."""
    actual_hash = file_sha256(destination)
    if actual_hash != trusted_item["output_sha256"]:
        raise ValueError(f"{case['id']}: copied image SHA-256 mismatch")
    record = dict(trusted_item)
    record.update(
        {
            "id": case["id"],
            "quality_band": case["quality_band"],
            "genre": case["genre"],
            "source_page": case["source_page"],
            "source_sha1": case["source_sha1"],
            "variant_recipe": case["variant_recipe"],
            "output_path": str(destination),
            "output_sha256": actual_hash,
        }
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    parser.add_argument("--run-id", help="Stable run name; defaults to a UTC timestamp")
    parser.add_argument("--seed", type=int, default=20260904)
    parser.add_argument("--resume", action="store_true", help="Resume an interrupted download")
    parser.add_argument("--original", action="store_true", help="Use full originals and verify SHA-1")
    parser.add_argument(
        "--reuse-cache",
        action="store_true",
        help="Reuse cache only through its verified manifest; fails on missing or stale entries",
    )
    parser.add_argument(
        "--reuse-images-from",
        type=Path,
        help="Copy reviewed images from a directory containing a verified manifest.json",
    )
    args = parser.parse_args()
    if args.reuse_cache and args.reuse_images_from is not None:
        parser.error("--reuse-cache and --reuse-images-from are mutually exclusive")

    run_id = args.run_id or datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    run_dir = DEFAULT_RUN_ROOT / run_id
    if run_dir.exists() and not args.resume:
        parser.error(f"run directory already exists: {run_dir}")
    images_dir = run_dir / "images"
    responses_dir = run_dir / "responses"

    cases = load_cases(args.cases)
    reuse_dir = args.reuse_images_from if args.reuse_images_from is not None else DEFAULT_OUTPUT
    reuse_items: dict[str, dict[str, object]] = {}
    if args.reuse_images_from is not None or args.reuse_cache:
        try:
            reuse_items = load_verified_reuse_items(
                reuse_dir / "manifest.json", cases, reuse_dir
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            parser.error(str(error))

    run_manifest_path = run_dir / "materialization-manifest.json"
    resume_items: dict[str, dict[str, object]] = {}
    if args.resume:
        try:
            resume_items = load_verified_reuse_items(
                run_manifest_path, cases, images_dir, require_all=False
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            parser.error(str(error))
        unrecorded = [
            case["id"]
            for case in cases
            if (images_dir / f"{case['id']}.jpg").exists()
            and case["id"] not in resume_items
        ]
        if unrecorded:
            parser.error(
                "resume images lack verified manifest entries: " + ", ".join(unrecorded)
            )

    images_dir.mkdir(parents=True, exist_ok=args.resume)
    responses_dir.mkdir(exist_ok=args.resume)

    materialized = []
    for case in cases:
        destination = images_dir / f"{case['id']}.jpg"
        if case["id"] in resume_items:
            materialized.append(
                reused_materialization_record(case, resume_items[case["id"]], destination)
            )
            continue
        if args.reuse_images_from is not None:
            source = reuse_dir / f"{case['id']}.jpg"
            shutil.copy2(source, destination)
            item = reused_materialization_record(case, reuse_items[case["id"]], destination)
            materialized.append(item)
        elif args.reuse_cache:
            source = reuse_dir / f"{case['id']}.jpg"
            destination.hardlink_to(source)
            item = reused_materialization_record(case, reuse_items[case["id"]], destination)
            materialized.append(item)
        else:
            item = materialize(case, images_dir, args.original)
            materialized.append(item)
        write_manifest_atomic(run_manifest_path, materialized)

    rng = random.Random(args.seed)
    rng.shuffle(materialized)
    case_prompts = {case["id"]: case["blind_prompt"] for case in cases}
    inputs = [
        {
            "ordinal": index,
            "case_id": item["id"],
            "image_path": item["output_path"],
            "image_sha256": item["output_sha256"],
            "prompt": case_prompts[item["id"]],
            "response_path": str(responses_dir / f"{item['id']}.md"),
        }
        for index, item in enumerate(materialized, 1)
    ]
    (run_dir / "blind-inputs.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in inputs),
        encoding="utf-8",
    )
    write_manifest_atomic(run_manifest_path, materialized)
    run_metadata = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "case_count": len(cases),
        "benchmark_cases_sha256": file_sha256(args.cases),
        "coaching_protocol_sha256": protocol_sha256(),
        "labels_in_blind_packet": False,
        "answers_in_blind_packet": False,
        "annotation_audit_required": True,
        "response_freeze_rule": "Write all response files before opening benchmark-cases.jsonl for grading.",
    }
    (run_dir / "run.json").write_text(
        json.dumps(run_metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Blind run ready: {run_dir}")
    print(f"Cases: {len(inputs)}; seed: {args.seed}")
    print("The packet exposes image, prompt, case ID, and response path only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
