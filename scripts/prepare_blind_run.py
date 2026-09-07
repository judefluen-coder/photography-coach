#!/usr/bin/env python3
"""Create a shuffled blind-run packet without copying benchmark labels or keys."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from materialize_benchmark import CASES_PATH, DEFAULT_OUTPUT, load_cases, materialize
from protocol_fingerprint import protocol_sha256


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RUN_ROOT = ROOT / ".benchmark-runs"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", help="Stable run name; defaults to a UTC timestamp")
    parser.add_argument("--seed", type=int, default=20260904)
    parser.add_argument("--resume", action="store_true", help="Resume an interrupted download")
    parser.add_argument("--original", action="store_true", help="Use full originals and verify SHA-1")
    parser.add_argument(
        "--reuse-cache",
        action="store_true",
        help="Reuse already materialized case images; fails when any are missing",
    )
    args = parser.parse_args()

    run_id = args.run_id or datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    run_dir = DEFAULT_RUN_ROOT / run_id
    if run_dir.exists() and not args.resume:
        parser.error(f"run directory already exists: {run_dir}")
    images_dir = run_dir / "images"
    responses_dir = run_dir / "responses"
    images_dir.mkdir(parents=True, exist_ok=args.resume)
    responses_dir.mkdir(exist_ok=args.resume)

    cases = load_cases()
    materialized = []
    for case in cases:
        cached = DEFAULT_OUTPUT / f"{case['id']}.jpg"
        destination = images_dir / f"{case['id']}.jpg"
        if args.resume and destination.exists():
            materialized.append(
                {
                    "id": case["id"],
                    "output_path": str(destination),
                    "output_sha256": file_sha256(destination),
                }
            )
            continue
        if args.reuse_cache:
            if not cached.exists():
                parser.error(f"missing cached image: {cached}")
            destination = images_dir / cached.name
            destination.hardlink_to(cached)
            materialized.append(
                {
                    "id": case["id"],
                    "output_path": str(destination),
                    "output_sha256": file_sha256(destination),
                }
            )
        else:
            item = materialize(case, images_dir, args.original)
            materialized.append(item)

    rng = random.Random(args.seed)
    materialized = [
        {
            "id": item["id"],
            "output_path": item["output_path"],
            "output_sha256": item["output_sha256"],
        }
        for item in materialized
    ]
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
    (run_dir / "materialization-manifest.json").write_text(
        json.dumps(materialized, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    run_metadata = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "case_count": len(cases),
        "benchmark_cases_sha256": file_sha256(CASES_PATH),
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
