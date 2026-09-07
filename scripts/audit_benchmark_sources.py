#!/usr/bin/env python3
"""Recheck benchmark file identity, assessment category, and licence metadata."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "references" / "benchmark-cases.jsonl"
API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "PhotographyCoachBenchmarkAudit/0.1 (+https://github.com/judefluen-coder/photography-coach)"


def assessment_present(categories: set[str], quality_band: str) -> bool:
    if quality_band == "acclaimed":
        return any(
            category.startswith("Category:Featured pictures ")
            and "candidate" not in category.lower()
            for category in categories
        )
    return "Category:Quality images" in categories


def load_cases() -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in CASES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def commons_title(source_page: str) -> str:
    path = urllib.parse.urlparse(source_page).path
    if "/wiki/" not in path:
        raise ValueError(f"not a Commons wiki page: {source_page}")
    return urllib.parse.unquote(path.split("/wiki/", 1)[1]).replace("_", " ")


def query(params: dict[str, str], retries: int = 3) -> dict[str, Any]:
    request = urllib.request.Request(
        API
        + "?"
        + urllib.parse.urlencode(
            {"action": "query", "format": "json", "formatversion": "2", **params}
        ),
        headers={"User-Agent": USER_AGENT},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == retries - 1:
                raise
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError("unreachable")


def fetch_pages(
    titles: list[str],
    query_fn: Callable[[dict[str, str]], dict[str, Any]] = query,
) -> dict[str, dict[str, Any]]:
    """Merge category-continuation pages without losing first-page image info."""
    params = {
        "titles": "|".join(titles),
        "prop": "categories|imageinfo",
        "cllimit": "max",
        "iiprop": "sha1|url|extmetadata",
    }
    continuation: dict[str, str] = {}
    pages: dict[str, dict[str, Any]] = {}
    while True:
        result = query_fn({**params, **continuation})
        for page in result.get("query", {}).get("pages", []):
            title = page["title"]
            current = pages.setdefault(title, {**page, "categories": []})
            current["categories"].extend(page.get("categories", []))
            if page.get("imageinfo"):
                current["imageinfo"] = page["imageinfo"]
        raw_continuation = result.get("continue")
        if not raw_continuation:
            return pages
        continuation = {
            str(name): str(value) for name, value in raw_continuation.items()
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--delay", type=float, default=.6)
    args = parser.parse_args()
    if args.batch_size < 1 or args.batch_size > 50:
        parser.error("--batch-size must be between 1 and 50")
    if args.delay < 0:
        parser.error("--delay cannot be negative")

    cases = load_cases()
    errors: list[str] = []
    checked = 0
    for offset in range(0, len(cases), args.batch_size):
        batch = cases[offset : offset + args.batch_size]
        titles = [commons_title(case["source_page"]) for case in batch]
        pages = fetch_pages(titles)
        for case, title in zip(batch, titles):
            page = pages.get(title)
            if not page or page.get("missing"):
                errors.append(f"{case['id']}: missing source page")
                continue
            info = (page.get("imageinfo") or [{}])[0]
            if info.get("sha1") != case["source_sha1"]:
                errors.append(f"{case['id']}: source SHA-1 changed")
            categories = {item["title"] for item in page.get("categories", [])}
            if not assessment_present(categories, case["quality_band"]):
                errors.append(f"{case['id']}: assessment category changed")
            licence = (
                info.get("extmetadata", {})
                .get("LicenseShortName", {})
                .get("value", "")
            )
            if licence != case["license"]:
                errors.append(
                    f"{case['id']}: licence changed from {case['license']!r} to {licence!r}"
                )
            checked += 1
        if offset + args.batch_size < len(cases):
            time.sleep(args.delay)

    if errors:
        print(f"FAIL: checked {checked}/{len(cases)} benchmark sources; {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"PASS: {checked}/{len(cases)} benchmark sources retain exact SHA-1, "
        "assessment category, and licence metadata"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
