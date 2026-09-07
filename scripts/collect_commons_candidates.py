#!/usr/bin/env python3
"""Collect a reproducible, metadata-rich Commons benchmark candidate pool."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
import urllib.parse
from pathlib import Path
from typing import Any, Callable

from audit_benchmark_sources import query


ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "references" / "benchmark-cases.jsonl"
DEVELOPMENT_CASES_PATH = ROOT / "references" / "benchmark-development-cases.jsonl"
MASTERWORKS_PATH = ROOT / "references" / "masterwork-cards.jsonl"
ASSESSMENT_CATEGORIES = {
    "acclaimed": "Category:Featured pictures on Wikimedia Commons",
    "ordinary": "Category:Quality images",
}
OPEN_LICENSE_PREFIXES = (
    "CC0",
    "CC BY",
    "CC BY-SA",
    "Public domain",
    "PDM",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def plain_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def commons_page(title: str) -> str:
    encoded = urllib.parse.quote(title.replace(" ", "_"), safe=":()_',-.")
    return f"https://commons.wikimedia.org/wiki/{encoded}"


def exclusions() -> tuple[set[str], set[str]]:
    pages: set[str] = set()
    sha1s: set[str] = set()
    for case_path in (CASES_PATH, DEVELOPMENT_CASES_PATH):
        if not case_path.exists():
            continue
        for case in load_jsonl(case_path):
            pages.add(case["source_page"])
            sha1s.add(case["source_sha1"])
    for card in load_jsonl(MASTERWORKS_PATH):
        for field in ("source_page", "source_url", "work_url", "image_page"):
            value = card.get(field)
            if isinstance(value, str) and "commons.wikimedia.org/wiki/" in value:
                pages.add(value)
    return pages, sha1s


def stable_key(title: str, seed: str) -> str:
    return hashlib.sha256(f"{seed}\0{title}".encode("utf-8")).hexdigest()


def acceptable_info(info: dict[str, Any], minimum_side: int) -> bool:
    if info.get("mime") not in {"image/jpeg", "image/png", "image/tiff"}:
        return False
    if min(info.get("width", 0), info.get("height", 0)) < minimum_side:
        return False
    metadata = info.get("extmetadata", {})
    license_name = metadata.get("LicenseShortName", {}).get("value", "")
    return any(license_name.startswith(prefix) for prefix in OPEN_LICENSE_PREFIXES)


def collect_titles(
    assessment: str,
    prefixes: str,
    per_prefix: int,
    source_category: str | None = None,
    query_fn: Callable[[dict[str, str]], dict[str, Any]] = query,
    delay: float = 0.0,
) -> list[str]:
    category = source_category or ASSESSMENT_CATEGORIES[assessment]
    titles: set[str] = set()
    for index, prefix in enumerate(prefixes):
        result = query_fn(
            {
                "list": "categorymembers",
                "cmtitle": category,
                "cmtype": "file",
                "cmlimit": str(per_prefix),
                "cmstartsortkeyprefix": prefix,
            }
        )
        titles.update(
            item["title"]
            for item in result.get("query", {}).get("categorymembers", [])
            if item.get("title", "").startswith("File:")
        )
        if delay and index + 1 < len(prefixes):
            time.sleep(delay)
    return sorted(titles)


def metadata_rows(
    titles: list[str],
    assessment: str,
    batch_size: int,
    minimum_side: int,
    query_fn: Callable[[dict[str, str]], dict[str, Any]] = query,
    delay: float = 0.0,
) -> list[dict[str, Any]]:
    category = ASSESSMENT_CATEGORIES[assessment]
    excluded_pages, excluded_sha1s = exclusions()
    rows: list[dict[str, Any]] = []
    for offset in range(0, len(titles), batch_size):
        batch = titles[offset : offset + batch_size]
        result = query_fn(
            {
                "titles": "|".join(batch),
                "prop": "categories|imageinfo",
                "cllimit": "max",
                "iiprop": "sha1|url|mime|size|extmetadata",
                "iiurlwidth": "1200",
            }
        )
        for page in result.get("query", {}).get("pages", []):
            if page.get("missing") or not page.get("imageinfo"):
                continue
            categories = {item["title"] for item in page.get("categories", [])}
            if category not in categories:
                continue
            info = page["imageinfo"][0]
            if not acceptable_info(info, minimum_side):
                continue
            source_page = commons_page(page["title"])
            if source_page in excluded_pages or info.get("sha1") in excluded_sha1s:
                continue
            metadata = info.get("extmetadata", {})
            rows.append(
                {
                    "assessment": assessment,
                    "title": page["title"].removeprefix("File:"),
                    "source_page": source_page,
                    "image_url": info["url"],
                    "preview_url": info.get("thumburl", info["url"]),
                    "source_sha1": info["sha1"],
                    "width": info["width"],
                    "height": info["height"],
                    "mime": info["mime"],
                    "creator": plain_text(metadata.get("Artist", {}).get("value", "")),
                    "license": metadata.get("LicenseShortName", {}).get("value", ""),
                    "date": plain_text(
                        metadata.get("DateTimeOriginal", metadata.get("DateTime", {})).get("value", "")
                    ),
                    "description": plain_text(metadata.get("ImageDescription", {}).get("value", "")),
                    "assessment_category": category,
                    "categories": sorted(categories - {category}),
                }
            )
        if delay and offset + batch_size < len(titles):
            time.sleep(delay)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assessment", choices=sorted(ASSESSMENT_CATEGORIES), required=True)
    parser.add_argument(
        "--source-category",
        help="Optional content category to sample; assessment membership is still rechecked",
    )
    parser.add_argument("--prefixes", default="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    parser.add_argument("--per-prefix", type=int, default=24)
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--minimum-side", type=int, default=800)
    parser.add_argument("--limit", type=int, default=240)
    parser.add_argument("--seed", default="photography-coach-holdout-v2")
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.prefixes:
        parser.error("prefixes cannot be empty")
    if not 1 <= args.per_prefix <= 500:
        parser.error("per-prefix must be between 1 and 500")
    if not 1 <= args.batch_size <= 50:
        parser.error("batch-size must be between 1 and 50")
    if args.minimum_side < 256 or args.limit < 1 or args.delay < 0:
        parser.error("minimum-side, limit, and delay are out of range")

    titles = collect_titles(
        args.assessment,
        args.prefixes,
        args.per_prefix,
        source_category=args.source_category,
        delay=args.delay,
    )
    rows = metadata_rows(
        titles,
        args.assessment,
        args.batch_size,
        args.minimum_side,
        delay=args.delay,
    )
    rows.sort(key=lambda row: stable_key(row["title"], args.seed))
    rows = rows[: args.limit]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(
        f"Collected {len(rows)} {args.assessment} candidates from "
        f"{len(titles)} category members: {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
