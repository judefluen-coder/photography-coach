#!/usr/bin/env python3
"""Download candidate previews and build labeled contact sheets for curation."""

from __future__ import annotations

import argparse
import io
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps


USER_AGENT = "PhotographyCoachHoldoutReview/0.1"
GENRE_SLUGS = {
    "people": "peo",
    "landscapes": "lan",
    "architecture": "arc",
    "food": "foo",
    "sports": "spo",
    "sculptures": "scu",
}


def pool_identity(path: Path) -> tuple[str, str]:
    stem = path.stem
    band = "A" if "featured" in stem else "O" if "target" in stem else ""
    genre = next((name for name in GENRE_SLUGS if stem.endswith(name)), "")
    if not band or not genre:
        raise ValueError(f"cannot infer band/genre from pool name: {path.name}")
    return band, genre


def load_review_rows(pools: list[Path], limit_per_pool: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for pool in pools:
        band, genre = pool_identity(pool)
        candidates = [
            json.loads(line)
            for line in pool.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ][:limit_per_pool]
        for index, candidate in enumerate(candidates, 1):
            if candidate["source_sha1"] in seen:
                continue
            seen.add(candidate["source_sha1"])
            rows.append(
                {
                    **candidate,
                    "candidate_id": f"{band}-{GENRE_SLUGS[genre]}-{index:03d}",
                    "review_genre": genre,
                }
            )
    return rows


def download_preview(row: dict[str, Any], destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        return
    request = urllib.request.Request(row["preview_url"], headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read()
    with Image.open(io.BytesIO(payload)) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
        image.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
        image.save(destination, quality=90, optimize=True)


def build_sheets(rows: list[dict[str, Any]], images: Path, sheets: Path) -> int:
    sheets.mkdir(parents=True, exist_ok=True)
    count = 0
    groups = sorted({(row["candidate_id"][0], row["review_genre"]) for row in rows})
    for band, genre in groups:
        group = [
            row for row in rows
            if row["candidate_id"].startswith(f"{band}-") and row["review_genre"] == genre
        ]
        for page_start in range(0, len(group), 12):
            canvas = Image.new("RGB", (1200, 900), "white")
            draw = ImageDraw.Draw(canvas)
            for slot, row in enumerate(group[page_start : page_start + 12]):
                x = (slot % 4) * 300
                y = (slot // 4) * 300
                with Image.open(images / f"{row['candidate_id']}.jpg") as opened:
                    thumbnail = ImageOps.contain(
                        opened.convert("RGB"), (286, 252), Image.Resampling.LANCZOS
                    )
                paste_x = x + (300 - thumbnail.width) // 2
                paste_y = y + 6 + (252 - thumbnail.height) // 2
                canvas.paste(thumbnail, (paste_x, paste_y))
                draw.text((x + 8, y + 264), row["candidate_id"], fill="black")
                draw.text((x + 8, y + 280), row["title"][:43], fill="black")
            page = page_start // 12 + 1
            canvas.save(sheets / f"{band}-{genre}-{page}.jpg", quality=92)
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pools", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit-per-pool", type=int, default=30)
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()
    if args.limit_per_pool < 1 or args.workers < 1:
        parser.error("limit-per-pool and workers must be positive")

    rows = load_review_rows(args.pools, args.limit_per_pool)
    images = args.output / "images"
    sheets = args.output / "sheets"
    images.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(download_preview, row, images / f"{row['candidate_id']}.jpg"): row
            for row in rows
        }
        for completed, future in enumerate(as_completed(futures), 1):
            try:
                future.result()
            except Exception as exc:  # network and decoder failures are reported per candidate
                errors.append(f"{futures[future]['candidate_id']}: {exc}")
            if completed % 40 == 0:
                print(f"downloaded {completed}/{len(rows)}; errors={len(errors)}", flush=True)

    valid = [row for row in rows if (images / f"{row['candidate_id']}.jpg").exists()]
    (args.output / "manifest.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in valid),
        encoding="utf-8",
    )
    sheet_count = build_sheets(valid, images, sheets)
    print(
        f"Review set: {len(valid)}/{len(rows)} previews, {sheet_count} sheets, "
        f"{len(errors)} error(s)"
    )
    for error in errors[:20]:
        print(f"- {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
