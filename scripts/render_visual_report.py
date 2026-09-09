#!/usr/bin/env python3
"""Render a self-contained local Photography Coach report from validated JSON."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SCORE_DIMENSIONS = [
    "技术可读性",
    "取景与边缘控制",
    "注意力与形式组织",
    "光线影调色彩",
    "空间与层次",
    "时机与关键关系",
    "信息叙事情绪",
    "表达一致性与完成度",
]

REQUIRED_TOP_LEVEL = {
    "title",
    "source_image",
    "summary",
    "priority",
    "strength",
    "observations",
    "scores",
    "reshoot",
    "edit",
    "reference",
    "exercise",
    "boundary_note",
    "research_status",
}

NESTED_FIELDS = {
    "priority": {"title", "body"},
    "strength": {"title", "body"},
    "reshoot": {"action", "effect", "cost", "availability"},
    "edit": {"summary", "crop", "tone_color", "limit"},
    "reference": {
        "photographer",
        "title",
        "year",
        "url",
        "looking_task",
        "match",
        "difference",
    },
    "exercise": {"title", "instructions"},
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}


class ReportError(ValueError):
    """Raised when the visual report payload cannot be rendered safely."""


def nonempty_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReportError(f"{field} must be a non-empty string")
    if "—" in value or "–" in value:
        raise ReportError(f"{field} contains a forbidden dash character; use punctuation or '-'")
    return value.strip()


def resolve_image(value: Any, field: str, base_dir: Path) -> Path:
    raw = nonempty_text(value, field)
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    path = path.resolve()
    if not path.is_file():
        raise ReportError(f"{field} does not exist: {path}")
    if path.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ReportError(f"{field} must use a supported image extension")
    return path


def validate_url(value: Any, field: str) -> str:
    url = nonempty_text(value, field)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ReportError(f"{field} must be a direct http(s) URL")
    return url


def validate_report(data: Any, base_dir: Path) -> tuple[dict[str, Any], Path, Path | None]:
    if not isinstance(data, dict):
        raise ReportError("report root must be an object")

    missing = sorted(REQUIRED_TOP_LEVEL - data.keys())
    if missing:
        raise ReportError(f"missing top-level fields: {', '.join(missing)}")

    for field in ["title", "summary", "boundary_note", "research_status"]:
        data[field] = nonempty_text(data[field], field)

    for section, required in NESTED_FIELDS.items():
        value = data.get(section)
        if not isinstance(value, dict):
            raise ReportError(f"{section} must be an object")
        section_missing = sorted(required - value.keys())
        if section_missing:
            raise ReportError(f"{section} is missing: {', '.join(section_missing)}")
        for field in required:
            value[field] = nonempty_text(value[field], f"{section}.{field}")

    data["reference"]["url"] = validate_url(data["reference"]["url"], "reference.url")

    observations = data.get("observations")
    if not isinstance(observations, list) or not 6 <= len(observations) <= 9:
        raise ReportError("observations must contain 6 to 9 items")
    allowed_priorities = {"首要", "次要", "要保护", "无明显问题"}
    priority_counts = {name: 0 for name in allowed_priorities}
    for index, item in enumerate(observations):
        if not isinstance(item, dict):
            raise ReportError(f"observations[{index}] must be an object")
        for field in ["label", "priority", "text"]:
            item[field] = nonempty_text(item.get(field), f"observations[{index}].{field}")
        if item["priority"] not in allowed_priorities:
            raise ReportError(f"observations[{index}].priority is invalid")
        priority_counts[item["priority"]] += 1
    if priority_counts["首要"] != 1:
        raise ReportError("observations must contain exactly one 首要")
    if not 2 <= priority_counts["次要"] <= 5:
        raise ReportError("observations must contain 2 to 5 次要 items")
    if priority_counts["要保护"] < 1:
        raise ReportError("observations must contain at least one 要保护")

    scores = data.get("scores")
    if not isinstance(scores, list) or len(scores) != 8:
        raise ReportError("scores must contain exactly eight items")
    dimensions: list[str] = []
    for index, item in enumerate(scores):
        if not isinstance(item, dict):
            raise ReportError(f"scores[{index}] must be an object")
        for field in ["dimension", "interval", "reason"]:
            item[field] = nonempty_text(item.get(field), f"scores[{index}].{field}")
        dimensions.append(item["dimension"])
    if dimensions != SCORE_DIMENSIONS:
        raise ReportError("scores must use all eight stable dimensions in the documented order")

    source_path = resolve_image(data["source_image"], "source_image", base_dir)
    treatment_path: Path | None = None
    if data.get("treatment_image") not in (None, ""):
        treatment_path = resolve_image(data["treatment_image"], "treatment_image", base_dir)

    return data, source_path, treatment_path


def safe_embedded_json(data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return (
        payload.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def render_report(input_path: Path, output_dir: Path, force: bool = False) -> Path:
    input_path = input_path.expanduser().resolve()
    if not input_path.is_file():
        raise ReportError(f"input file does not exist: {input_path}")

    skill_root = Path(__file__).resolve().parents[1]
    output_dir = output_dir.expanduser().resolve()
    if output_dir == skill_root or skill_root in output_dir.parents:
        raise ReportError("output must be outside the skill repository to protect user media")
    if output_dir.exists() and any(output_dir.iterdir()) and not force:
        raise ReportError(f"output directory is not empty: {output_dir}; pass --force to replace report files")

    try:
        raw = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReportError(f"cannot read report JSON: {exc}") from exc

    data, source_path, treatment_path = validate_report(raw, input_path.parent)
    output_dir.mkdir(parents=True, exist_ok=True)
    asset_dir = output_dir / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)

    source_name = f"source{source_path.suffix.lower()}"
    source_output = asset_dir / source_name
    shutil.copy2(source_path, source_output)
    data["source_asset"] = f"assets/{source_name}"
    data["source_extension"] = source_path.suffix.lower().lstrip(".")

    if treatment_path:
        treatment_name = f"treatment{treatment_path.suffix.lower()}"
        treatment_output = asset_dir / treatment_name
        shutil.copy2(treatment_path, treatment_output)
        data["treatment_asset"] = f"assets/{treatment_name}"
        data["treatment_extension"] = treatment_path.suffix.lower().lstrip(".")
    else:
        data["treatment_asset"] = None
        data["treatment_extension"] = None

    data.pop("source_image", None)
    data.pop("treatment_image", None)

    template_path = skill_root / "assets" / "visual-report-template.html"
    try:
        template = template_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReportError(f"cannot read visual template: {exc}") from exc
    if template.count("__REPORT_JSON__") != 1:
        raise ReportError("visual template must contain exactly one report placeholder")

    html = template.replace("__REPORT_JSON__", safe_embedded_json(data))
    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Path to visual report JSON")
    parser.add_argument("--output", required=True, type=Path, help="Task-specific output directory")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite index.html and copied report assets in an existing output directory",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        index_path = render_report(args.input, args.output, args.force)
    except ReportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(index_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
