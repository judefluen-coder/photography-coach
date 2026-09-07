#!/usr/bin/env python3
"""Download blind-benchmark inputs and deterministically build degraded variants."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageStat


ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "references" / "benchmark-cases.jsonl"
DEFAULT_OUTPUT = ROOT / ".benchmark-cache"
USER_AGENT = "PhotographyCoachBenchmark/0.1 (+https://github.com/judefluen-coder/photography-coach)"


def load_cases(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def apply_recipe(image: Image.Image, recipe: dict[str, Any]) -> Image.Image:
    operation = recipe["operation"]
    params = recipe["parameters"]
    source = image.convert("RGB")
    width, height = source.size

    if operation == "crop_pressure":
        left = round(width * params["left_pct"])
        right = round(width * (1 - params["right_pct"]))
        top = round(height * params["top_pct"])
        bottom = round(height * (1 - params["bottom_pct"]))
        return source.crop((left, top, right, bottom)).resize(
            (width, height), Image.Resampling.LANCZOS
        )

    if operation == "shadow_crush":
        black_point = params["black_point"]
        gamma = params["gamma"]

        def crush(value: int) -> int:
            normalized = max(value / 255 - black_point, 0) / (1 - black_point)
            return round(255 * normalized**gamma)

        return source.point([crush(value) for value in range(256)] * 3)

    if operation == "highlight_clip":
        factor = 2 ** params["exposure_stops"]
        clip_point = params["clip_point"] * 255

        def clip(value: int) -> int:
            return round(255 * min(value * factor, clip_point) / clip_point)

        return source.point([clip(value) for value in range(256)] * 3)

    if operation == "color_excess":
        saturated = ImageEnhance.Color(source).enhance(params["saturation"])
        red, green, blue = saturated.split()
        red = red.point(lambda value: min(255, round(value * params["red_gain"])))
        green = green.point(lambda value: min(255, round(value * params["green_gain"])))
        blue = blue.point(lambda value: min(255, round(value * params["blue_gain"])))
        return Image.merge("RGB", (red, green, blue))

    if operation == "tilt_and_crop":
        angle = params["angle_degrees"]
        rotated = source.rotate(
            angle,
            resample=Image.Resampling.BICUBIC,
            expand=False,
            fillcolor=(0, 0, 0),
        )
        radians = abs(math.radians(angle))
        margin_x = min(round(math.sin(radians) * height), width // 4)
        margin_y = min(round(math.sin(radians) * width), height // 4)
        cropped = rotated.crop((margin_x, margin_y, width - margin_x, height - margin_y))
        return cropped.resize((width, height), Image.Resampling.LANCZOS)

    if operation == "detail_damage":
        factor = params["downsample_factor"]
        reduced = source.resize(
            (max(16, round(width * factor)), max(16, round(height * factor))),
            Image.Resampling.BILINEAR,
        )
        reduced = reduced.filter(ImageFilter.GaussianBlur(params["gaussian_blur_radius"]))
        restored = reduced.resize((width, height), Image.Resampling.BILINEAR)
        return restored.filter(
            ImageFilter.UnsharpMask(radius=1.2, percent=round(params["sharpen_amount"] * 100))
        )

    raise ValueError(f"unsupported operation: {operation}")


def mean_absolute_difference(first: Image.Image, second: Image.Image) -> float:
    difference = ImageChops.difference(first.convert("RGB"), second.convert("RGB"))
    return sum(ImageStat.Stat(difference).mean) / 3


def materialize(case: dict[str, Any], output: Path, use_original: bool) -> dict[str, Any]:
    url = case["image_url"] if use_original else case["preview_url"]
    payload = download(url)
    if use_original:
        actual_sha1 = hashlib.sha1(payload).hexdigest()
        if actual_sha1 != case["source_sha1"]:
            raise ValueError(
                f"{case['id']}: source SHA-1 mismatch ({actual_sha1} != {case['source_sha1']})"
            )

    with Image.open(io.BytesIO(payload)) as opened:
        source = opened.convert("RGB")
    result = source
    difference = 0.0
    if case["variant_recipe"] is not None:
        result = apply_recipe(source, case["variant_recipe"])
        difference = mean_absolute_difference(source, result)
        minimum_difference = (
            2 if case["variant_recipe"]["operation"] == "detail_damage" else 4
        )
        if difference < minimum_difference:
            raise ValueError(f"{case['id']}: variant is visually too close to source ({difference:.2f})")

    output.mkdir(parents=True, exist_ok=True)
    destination = output / f"{case['id']}.jpg"
    save_options = {"format": "JPEG", "quality": 95, "optimize": True}
    if case["variant_recipe"] and case["variant_recipe"]["operation"] == "detail_damage":
        save_options["quality"] = case["variant_recipe"]["parameters"]["jpeg_quality"]
    result.save(destination, **save_options)
    output_bytes = destination.read_bytes()
    return {
        "id": case["id"],
        "quality_band": case["quality_band"],
        "genre": case["genre"],
        "source_page": case["source_page"],
        "download_url": url,
        "source_sha1": case["source_sha1"],
        "output_path": str(destination),
        "output_sha256": hashlib.sha256(output_bytes).hexdigest(),
        "output_width": result.width,
        "output_height": result.height,
        "mean_absolute_difference": round(difference, 3),
        "variant_recipe": case["variant_recipe"],
        "license": case["license"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--case", action="append", dest="case_ids", help="Materialize one case ID")
    parser.add_argument(
        "--band",
        choices=("acclaimed", "ordinary", "failed_imitation"),
        help="Materialize only one quality band",
    )
    parser.add_argument("--limit", type=int, help="Limit cases after filtering")
    parser.add_argument(
        "--original",
        action="store_true",
        help="Download originals and verify source SHA-1; previews are the default",
    )
    args = parser.parse_args()

    cases = load_cases(args.cases)
    if args.case_ids:
        requested = set(args.case_ids)
        cases = [case for case in cases if case["id"] in requested]
        missing = requested - {case["id"] for case in cases}
        if missing:
            parser.error(f"unknown case IDs: {', '.join(sorted(missing))}")
    if args.band:
        cases = [case for case in cases if case["quality_band"] == args.band]
    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be positive")
        cases = cases[: args.limit]

    manifest = []
    for case in cases:
        item = materialize(case, args.output, args.original)
        manifest.append(item)
        print(
            f"{item['id']}: {item['output_width']}x{item['output_height']} "
            f"diff={item['mean_absolute_difference']:.3f}"
        )
    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
