#!/usr/bin/env python3
"""Structural validator for Photography Coach Markdown responses."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HEADINGS = [
    "我怎样读这张照片",
    "最成立的一点",
    "全画面看片地图",
    "决策",
    "下一次怎么拍",
    "裁切与调色方案",
    "后期：能做 / 不能做",
    "20–40 分钟练习",
    "方法图例与摄影师方向",
    "八维区间",
    "未知项与事实边界",
    "可选语境复核",
]

OBSERVATION_FAMILIES = {
    "capture/technical": r"技术|清晰|焦点|曝光|噪点|动态范围|处理",
    "framing/edge": r"取景|构图|边缘|裁切|画幅|留白",
    "attention/form": r"注意力|观看顺序|视觉层级|形式|线条|形状|平衡|节奏|重复",
    "light/tone/color": r"光线|影调|明暗|反差|色彩|颜色|白平衡|饱和",
    "space/perspective": r"空间|虚实|景深|层次|分离|大小|远近|透视|遮挡",
    "moment/relationship": r"时机|瞬间|动作|姿态|视线|人物|物体|关系",
    "information/meaning": r"信息|叙事|故事|意义|情绪|歧义|语境",
}

DECISIONS = {
    "STRUCTURAL_BOTTLENECK",
    "CONDITIONAL_BRANCH",
    "NO_STRUCTURAL_BOTTLENECK",
}

DIMENSIONS = [
    "技术可读性",
    "取景与边缘控制",
    "注意力与形式组织",
    "光线影调色彩",
    "空间与层次",
    "时机与关键关系",
    "信息叙事情绪",
    "表达一致性与完成度",
]


def validate(text: str) -> list[str]:
    errors: list[str] = []

    positions: list[int] = []
    for heading in HEADINGS:
        match = re.search(rf"^##\s+(?:\d+\.\s*)?{re.escape(heading)}\s*$", text, re.M)
        if not match:
            errors.append(f"missing heading: {heading}")
        else:
            positions.append(match.start())
    if len(positions) == len(HEADINGS) and positions != sorted(positions):
        errors.append("headings are out of order")

    found_decisions = [token for token in DECISIONS if re.search(rf"\b{token}\b", text)]
    if len(found_decisions) != 1:
        errors.append(f"expected exactly one decision token, found {len(found_decisions)}")

    for label in ("动作：", "预期效果：", "代价：", "可得性："):
        if label not in text:
            errors.append(f"missing advice field: {label}")

    if not re.search(r"可得性：\s*(即时|相似场景|稀有事件)", text):
        errors.append("availability must be 即时, 相似场景, or 稀有事件")

    map_match = re.search(
        r"^##\s+(?:3\.\s*)?全画面看片地图\s*$([\s\S]*?)(?=^##\s+)",
        text,
        re.M,
    )
    map_text = map_match.group(1) if map_match else ""

    covered_families = [
        family for family, pattern in OBSERVATION_FAMILIES.items()
        if re.search(pattern, map_text)
    ]
    if len(covered_families) < 6:
        errors.append(
            "whole-frame map must cover at least six relevant observation families; "
            f"found {len(covered_families)}"
        )

    primary_count = len(re.findall(r"首要", map_text))
    if primary_count != 1:
        errors.append(f"whole-frame map must mark exactly one 首要, found {primary_count}")
    secondary_count = len(re.findall(r"次要", map_text))
    if not 2 <= secondary_count <= 5:
        errors.append(f"whole-frame map must mark 2–5 次要 observations, found {secondary_count}")
    if "要保护" not in map_text:
        errors.append("whole-frame map must mark at least one protected strength: 要保护")

    if not re.search(r"裁切.{0,30}(上|下|左|右|边缘|比例|画面)", text, re.S):
        errors.append("crop plan must use a visible boundary or proportion")

    for dimension in DIMENSIONS:
        if dimension not in text:
            errors.append(f"missing dimension: {dimension}")

    dimension_lines = [line for line in text.splitlines() if any(d in line for d in DIMENSIONS)]
    reasoned_dimensions = [line for line in dimension_lines if re.search(r"[—：:].{4,}", line)]
    if len(reasoned_dimensions) < 8:
        errors.append("each dimension interval needs an image-specific reason")

    interval_count = len(re.findall(r"(?:[0-5]\s*[–-]\s*[0-5]\s*/\s*5|N/A)", text))
    if interval_count < 8:
        errors.append("expected eight dimension intervals or N/A values")

    status = "研究状态：实验版 v0.1；不是专家认证、客观审美分或学习效果证明。"
    if status not in text:
        errors.append("missing research-status disclaimer")

    if re.search(r"(?:总分|综合得分|大师分|百分位)\s*[：:]?\s*\d", text):
        errors.append("forbidden aggregate/ranking score")

    has_embedded_image = bool(re.search(r"!\[[^\]]*\]\([^\)]+\)", text))
    if has_embedded_image:
        for label in ("作者：", "来源：", "许可："):
            if label not in text:
                errors.append(f"embedded image missing attribution field: {label}")

    reference_match = re.search(
        r"^##\s+(?:9\.\s*)?方法图例与摄影师方向\s*$([\s\S]*?)(?=^##\s+)",
        text,
        re.M,
    )
    reference_text = reference_match.group(1) if reference_match else ""
    if "http" in reference_text:
        for label in ("看片任务：", "对应本图：", "重点看：", "关键差异：", "可迁移实验："):
            if label not in reference_text:
                errors.append(f"linked reference missing method-match field: {label}")
        if not re.search(r"\b(?:18|19|20)\d{2}\b", reference_text):
            errors.append("linked reference needs a named photograph year")
    elif "本次未提供未经核验的图例。" not in reference_text:
        errors.append("reference section needs verified links or the explicit omission line")

    if "锐化" in text and re.search(r"锐化.{0,12}(恢复|找回|修复).{0,8}(焦点|合焦|细节)", text):
        errors.append("sharpening is claimed to restore missed focus/detail")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("response", type=Path, help="Markdown critique to validate")
    args = parser.parse_args()

    try:
        text = args.response.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read {args.response}: {exc}", file=sys.stderr)
        return 2

    errors = validate(text)
    if errors:
        print(f"FAIL: {len(errors)} structural issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: response matches the Photography Coach structural contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
