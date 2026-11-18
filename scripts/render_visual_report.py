#!/usr/bin/env python3
"""Render a self-contained local Photography Coach report from validated JSON."""

from __future__ import annotations

import argparse
import json
import math
import re
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


class JudgmentError(ReportError):
    """Bounded, authored consistency errors safe to display in the local workbench."""


def validate_coaching(data: dict) -> None:
    """Check explicit links and a narrow contradiction sentinel, not arbitrary semantics."""
    decision = data["decision"]
    # Sentence starts avoid treating “不必重构” or a quoted alternative as an obligation.
    severe = re.compile(r"(?:^|[。！？；\n])\s*(?:(?:当前(?:的)?(?:构图|画面)|这张(?:照片)?|整张(?:照片)?)[，,:：]?)?(?:必须(?:大幅裁切|重构|重拍|重新构图)|完全不成立)")
    if decision == "NO_STRUCTURAL_BOTTLENECK" and severe.search(data["priority"]["title"] + "\n" + data["priority"]["body"]):
        raise JudgmentError("点评前后不一致：一边判断无需重构，一边要求必须重构或重拍。本次未展示矛盾报告；没有自动再次调用模型。")
    no_fault = re.compile(r"(?:^|[。！？；\n])\s*(?:(?:这张(?:照片)?|整张(?:照片)?|当前(?:画面|构图))[，,:：]?)?(?:无需任何调整|不需要任何调整|完全没有问题|没有任何问题|所有方面均无明显问题)\s*(?:[。！？；]|$)")
    if decision == "STRUCTURAL_BOTTLENECK" and no_fault.search(data["summary"]):
        raise JudgmentError("点评前后不一致：总结声称完全没有问题，决策却判定存在结构瓶颈。本次未展示矛盾报告；没有自动再次调用模型。")
    coaching = data.get("coaching")
    if coaching is None:
        return  # Older offline reports remain readable; no invented linkage or confidence.
    if not isinstance(coaching, dict):
        raise JudgmentError("点评的练习关联格式无效。")
    allowed = {
        "STRUCTURAL_BOTTLENECK": {"优先修正"},
        "CONDITIONAL_BRANCH": {"按目的选择"},
        "NO_STRUCTURAL_BOTTLENECK": {"局部修正", "可选尝试", "保留"},
    }
    if coaching.get("action_type") not in allowed[decision]:
        raise JudgmentError("点评的总体判断与建议性质不一致。本次未展示矛盾报告；没有自动再次调用模型。")
    observations = data["observations"]
    for key in ("observation_index", "exercise_observation_index"):
        value = coaching.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < len(observations):
            raise JudgmentError("点评或练习没有关联到有效的画面观察。")
    target = observations[coaching["observation_index"]]
    if target["priority"] != "首要" and not (coaching["action_type"] == "保留" and target["priority"] == "要保护"):
        raise JudgmentError("主建议没有关联到本次重点或明确保留项。")
    mode = coaching.get("exercise_mode")
    if mode == "围绕重点":
        if coaching["exercise_observation_index"] != coaching["observation_index"]:
            raise JudgmentError("练习与主建议没有对齐。若有意巩固优点，需明确说明并关联保留项。")
    elif mode == "巩固优点":
        if observations[coaching["exercise_observation_index"]]["priority"] != "要保护":
            raise JudgmentError("巩固练习必须关联一项已经成立、值得保留的关系。")
    else:
        raise JudgmentError("练习需要说明是围绕重点还是巩固优点。")
    for key in ("exercise_connection", "success_criterion"):
        value = coaching.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > 600:
            raise JudgmentError("练习缺少具体关联理由或可观察的检查标准。")


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
    decision = data.get("decision", "STRUCTURAL_BOTTLENECK")
    if decision not in {"STRUCTURAL_BOTTLENECK", "CONDITIONAL_BRANCH", "NO_STRUCTURAL_BOTTLENECK"}:
        raise ReportError("decision is invalid")
    data["decision"] = decision

    for section, required in NESTED_FIELDS.items():
        value = data.get(section)
        if section == "reference" and value is None:
            data["reference_status"] = nonempty_text(data.get("reference_status"), "reference_status")
            continue
        if not isinstance(value, dict):
            raise ReportError(f"{section} must be an object")
        section_missing = sorted(required - value.keys())
        if section_missing:
            raise ReportError(f"{section} is missing: {', '.join(section_missing)}")
        for field in required:
            value[field] = nonempty_text(value[field], f"{section}.{field}")

    if data["reference"] is not None:
        data["reference"]["url"] = validate_url(data["reference"]["url"], "reference.url")
    # Preserve the six-check summary and attribution when supplied by newer reports.
    if "integrity" in data:
        checks = data["integrity"]
        families = ["边缘/裁切", "暗部", "高光", "色彩", "轴线/透视", "细节"]
        if not isinstance(checks, list) or len(checks) != len(families):
            raise ReportError("integrity must contain the six integrity families")
        for index, (check, family) in enumerate(zip(checks, families)):
            if not isinstance(check, dict) or check.get("family") != family:
                raise ReportError("integrity must use the six families in documented order")
            if check.get("verdict") not in {"通过", "观察", "问题", "无法判断"}:
                raise ReportError(f"integrity[{index}].verdict is invalid")
            check["basis"] = nonempty_text(check.get("basis"), f"integrity[{index}].basis")
    if "source_credit" in data:
        credit = data["source_credit"]
        if not isinstance(credit, dict):
            raise ReportError("source_credit must be an object")
        for field in ("author", "license", "changes"):
            credit[field] = nonempty_text(credit.get(field), f"source_credit.{field}")
        for field in ("url", "license_url"):
            credit[field] = validate_url(credit.get(field), f"source_credit.{field}")
    if "visual_guides" in data:
        validate_visual_guides(data["visual_guides"])

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
        regions = item.get("regions", [])
        if not isinstance(regions, list) or len(regions) > 4:
            raise ReportError(f"observations[{index}].regions must contain at most four rectangles")
        for region in regions:
            validate_rectangle(region, f"observations[{index}].regions")
    if priority_counts["首要"] != 1:
        raise ReportError("observations must contain exactly one 首要")
    if not 2 <= priority_counts["次要"] <= 5:
        raise ReportError("observations must contain 2 to 5 次要 items")
    if priority_counts["要保护"] < 1:
        raise ReportError("observations must contain at least one 要保护")
    if data.get("learning_check") is not None:
        validate_learning_check(data["learning_check"], len(observations))

    scores = data.get("scores")
    if not isinstance(scores, list) or len(scores) != 8:
        raise ReportError("scores must contain exactly eight items")
    dimensions: list[str] = []
    for index, item in enumerate(scores):
        if not isinstance(item, dict):
            raise ReportError(f"scores[{index}] must be an object")
        for field in ["dimension", "interval", "reason"]:
            item[field] = nonempty_text(item.get(field), f"scores[{index}].{field}")
        interval = item["interval"]
        if interval != "N/A":
            match = re.fullmatch(r"([0-5])\s*-\s*([0-5])\s*/\s*5", interval)
            if not match or int(match[1]) > int(match[2]):
                raise ReportError(f"scores[{index}].interval must be an ordered 0-5 integer interval or N/A")
        dimensions.append(item["dimension"])
        if item.get("uncertainty") is not None:
            item["uncertainty"] = nonempty_text(item["uncertainty"], f"scores[{index}].uncertainty")
        if "confidence" in item:
            if item["confidence"] not in {"高", "中", "低"}:
                raise ReportError(f"scores[{index}].confidence is invalid")
            if item["confidence"] != "高" and not item.get("uncertainty"):
                raise JudgmentError("评分把握不足时，需要说明具体缺少什么信息。")
    if dimensions != SCORE_DIMENSIONS:
        raise ReportError("scores must use all eight stable dimensions in the documented order")
    validate_coaching(data)

    source_path = resolve_image(data["source_image"], "source_image", base_dir)
    treatment_path: Path | None = None
    if data.get("treatment_image") not in (None, ""):
        treatment_path = resolve_image(data["treatment_image"], "treatment_image", base_dir)
    if data.get("color_image") not in (None, ""):
        resolve_image(data["color_image"], "color_image", base_dir)
    for kind in ("source", "color", "treatment"):
        field = f"{kind}_preview_image"
        if data.get(field) not in (None, ""):
            if not data.get(f"{kind}_image"):
                raise ReportError(f"{field} requires {kind}_image; a preview is not a downloadable master")
            resolve_image(data[field], field, base_dir)
    if "crop_region" in data["edit"]:
        validate_rectangle(data["edit"]["crop_region"], "edit.crop_region")

    return data, source_path, treatment_path


def validate_learning_check(check: Any, observation_count: int) -> None:
    """An optional, photo-specific comparison, never an aesthetic exam or gate."""
    if not isinstance(check, dict):
        raise ReportError("learning_check must be an object or null")
    index = check.get("observation_index")
    if isinstance(index, bool) or not isinstance(index, (int, float)) or not math.isfinite(index) or int(index) != index or not 0 <= index < observation_count:
        raise ReportError("learning_check.observation_index must refer to an existing observation")
    for field, limit in (("question", 80), ("takeaway", 160)):
        check[field] = nonempty_text(check.get(field), f"learning_check.{field}")
        if len(check[field]) > limit:
            raise ReportError(f"learning_check.{field} is too long")
    options = check.get("options")
    if not isinstance(options, list) or len(options) != 2:
        raise ReportError("learning_check.options must contain two approaches")
    for option in options:
        if not isinstance(option, dict):
            raise ReportError("learning_check option must be an object")
        for field, limit in (("title", 24), ("effect", 120), ("cost", 120)):
            option[field] = nonempty_text(option.get(field), f"learning_check.option.{field}")
            if len(option[field]) > limit:
                raise ReportError(f"learning_check.option.{field} is too long")
    if options[0]["title"] == options[1]["title"]:
        raise ReportError("learning_check options must describe different approaches")


def validate_visual_guides(guides: Any) -> None:
    """Validate optional teaching geometry, never an edit or a measured scene model."""
    if not isinstance(guides, list) or len(guides) > 3:
        raise ReportError("visual_guides must contain at most three diagrams")
    tones = {"accent", "secondary", "dark", "light", "warm", "cool"}

    def point(value: Any) -> None:
        if not isinstance(value, dict):
            raise ReportError("visual_guides point must be an object")
        for key in ("x", "y"):
            number = value.get(key)
            if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number) or not 0 <= number <= 1:
                raise ReportError("visual_guides coordinates must be finite numbers within 0 to 1")

    for guide in guides:
        if not isinstance(guide, dict):
            raise ReportError("visual_guides item must be an object")
        for field, limit in (("title", 24), ("takeaway", 240), ("boundary", 240)):
            guide[field] = nonempty_text(guide.get(field), f"visual_guides.{field}")
            if len(guide[field]) > limit:
                raise ReportError(f"visual_guides.{field} is too long")
        for group, maximum in (("areas", 6), ("lines", 8), ("labels", 6)):
            values = guide.get(group)
            if not isinstance(values, list) or len(values) > maximum:
                raise ReportError(f"visual_guides.{group} has an invalid item count")
            for item in values:
                if not isinstance(item, dict):
                    raise ReportError(f"visual_guides.{group} item must be an object")
                if group == "labels":
                    point(item)
                    item["text"] = nonempty_text(item.get("text"), "visual_guides.label")
                    if len(item["text"]) > 24:
                        raise ReportError("visual_guides label is too long")
                    if "explanation" in item:
                        item["explanation"] = nonempty_text(item["explanation"], "visual_guides.label.explanation")
                        if len(item["explanation"]) > 160:
                            raise ReportError("visual_guides label explanation is too long")
                    continue
                if not isinstance(item.get("tone"), str) or item["tone"] not in tones:
                    raise ReportError("visual_guides tone is invalid")
                points = item.get("points")
                minimum = 3 if group == "areas" else 2
                if not isinstance(points, list) or not minimum <= len(points) <= 24:
                    raise ReportError("visual_guides path has an invalid point count")
                for value in points:
                    point(value)
                if group == "lines" and not isinstance(item.get("arrow"), bool):
                    raise ReportError("visual_guides arrow must be boolean")
        if not guide["areas"] and not guide["lines"]:
            raise ReportError("visual_guides must show at least one area or line")


def validate_rectangle(value: Any, field: str) -> None:
    """Coordinates refer to the source image, with the top-left at (0, 0)."""
    if not isinstance(value, dict):
        raise ReportError(f"{field} must be a rectangle")
    for key in ("x", "y", "width", "height"):
        number = value.get(key)
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
            raise ReportError(f"{field}.{key} must be a finite number")
    if (value["x"] < 0 or value["y"] < 0 or value["width"] <= 0 or value["height"] <= 0
            or value["x"] + value["width"] > 1.000000001
            or value["y"] + value["height"] > 1.000000001):
        raise ReportError(f"{field} must stay within source coordinates 0 to 1")


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

    color_path = (resolve_image(data["color_image"], "color_image", input_path.parent)
                  if data.get("color_image") else None)
    for kind, master in (("source", source_path), ("color", color_path), ("treatment", treatment_path)):
        # Generated paths always replace caller-supplied paths, including stale demo overrides.
        data[f"{kind}_asset"] = None
        data[f"{kind}_download"] = None
        data[f"{kind}_extension"] = None
        if master:
            name = f"{kind}{master.suffix.lower()}"
            shutil.copy2(master, asset_dir / name)
            data[f"{kind}_asset"] = data[f"{kind}_download"] = f"assets/{name}"
            data[f"{kind}_extension"] = master.suffix.lower().lstrip(".")
            preview_field = f"{kind}_preview_image"
            if data.get(preview_field):
                preview = resolve_image(data[preview_field], preview_field, input_path.parent)
                preview_name = f"{kind}-preview{preview.suffix.lower()}"
                shutil.copy2(preview, asset_dir / preview_name)
                data[f"{kind}_asset"] = f"assets/{preview_name}"
        data.pop(f"{kind}_image", None)
        data.pop(f"{kind}_preview_image", None)

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
