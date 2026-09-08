#!/usr/bin/env python3
"""Structural validator for Photography Coach Markdown responses."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Mapping

from analyze_image_integrity import analyze


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

INTEGRITY_FAMILIES = (
    "边缘/裁切",
    "暗部",
    "高光",
    "色彩",
    "轴线/透视",
    "细节",
)

INTEGRITY_AUDIT_LABELS = {
    "边缘/裁切": "对边：",
    "暗部": "暗面：",
    "高光": "亮面：",
    "色彩": "色彩对照：",
    "轴线/透视": "参照：",
    "细节": "同尺度：",
}

PRIMARY_FAMILY_PATTERNS = {
    "边缘/裁切": r"取景|边缘|裁切|画框",
    "暗部": r"暗部|阴影|黑位|影调|明暗",
    "高光": r"高光|亮部|白位|影调|明暗",
    "色彩": r"色彩|颜色|饱和|偏色|白平衡",
    "轴线/透视": r"轴线|透视|水平|垂直|倾斜|滚转",
    "细节": r"细节|清晰|纹理|锐化|噪点|技术",
    "注意力/形式": r"注意力|形式|观看顺序|视觉层级|线条|形状|节奏",
    "空间/层次": r"空间|层次|远近|遮挡|图地|透视",
    "时机/关系": r"时机|瞬间|动作|姿态|人物|物体|关系",
    "信息/意义": r"信息|叙事|故事|意义|情绪|语境",
}

PRIORITY_FACTORS = (
    "信息损失",
    "关系断裂",
    "影响范围",
    "可逆性",
    "修复价值",
    "保护代价",
)

RELATION_COVERAGE_LABELS = (
    "边缘/中心",
    "空间/动作",
    "光色/材质",
)

FACT_BOUNDARY_LABELS = (
    "角色/关系",
    "状态/过程",
    "感受/含义",
    "地点/时间/因果",
)

FACT_BOUNDARY_DISPOSITIONS = r"保留未知|仅描述|观看推测|不作判断|经核验语境"

# These are high-risk assertion tokens, not forbidden concepts. In a blind response they
# need an uncertainty/viewing-effect marker in the same sentence where they first occur.
INFERENCE_RISK_PATTERN = re.compile(
    r"工人|导游|工作人员|员工|夫妻|家人|亲子|亲属|"
    r"沸水|沸腾|烹煮|腌制|腌渍|"
    r"秋天|秋季|秋日|秋林|秋色|阴天|晴天|雨天|深夜|"
    r"啤酒|外脆内软|鲜嫩|新鲜|"
    r"高速|飞速|"
    r"祭台|供物|祭祀|仪式性|"
    r"亲和感|开心|悲伤|愤怒|思考|沉思|焦虑"
)

INFERENCE_QUALIFIER_PATTERN = re.compile(
    r"似乎|仿佛|可能|或许|看起来|视觉上|让人联想到|"
    r"读作|可读成|像是|显得|形成.{0,4}感|带来.{0,4}感|"
    r"不确定|无法确认|不能确认|不能判断|未知|未必|也可能|"
    r"如果|若|假如|经核验|标题|说明文字|用户补充"
)

GENERIC_AUDIT_PHRASES = (
    "关键轮廓比附近次要纹理更值得保护",
    "边缘与主体关系仍可再整理",
    "已有视觉中心，但次级元素需要降权",
    "主调可读，局部明暗和色彩应克制处理",
    "前后关系成立，还可用站位进一步厘清",
    "当前单张足以提出工作假设，语境仍未知",
    "边缘有可再精炼的余量",
    "主体级信息足以支持当前读法",
)


def integrity_signal_map(image_path: Path) -> dict[str, str]:
    return {
        item["family"]: item["strength"]
        for item in analyze(image_path)["signals"]
    }


def validate(
    text: str,
    *,
    require_integrity_probe: bool = False,
    require_reference: bool = False,
    integrity_signals: Mapping[str, str] | None = None,
) -> list[str]:
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

    if "完整性六检" not in map_text:
        errors.append("whole-frame map must expose 完整性六检")
    probe_line = next(
        (line for line in map_text.splitlines() if "完整性量化" in line),
        "",
    )
    probe_match = re.search(r"完整性量化[：:]\s*(已运行|不可用)", probe_line)
    if not probe_match:
        errors.append("whole-frame map must record 完整性量化 as 已运行 or 不可用")
    elif require_integrity_probe and probe_match.group(1) != "已运行":
        errors.append("benchmark response must record 完整性量化：已运行")
    elif require_integrity_probe:
        if integrity_signals is not None:
            if not integrity_signals and "无阈值信号" not in probe_line:
                errors.append("integrity probe returned no signals; record 无阈值信号")
            for family, strength in integrity_signals.items():
                label = "强" if strength == "strong" else "复核"
                if f"{family}[{label}]" not in probe_line:
                    errors.append(
                        f"integrity probe line must record actual trigger: {family}[{label}]"
                    )
            reported = {
                family
                for family in INTEGRITY_FAMILIES
                if re.search(rf"{re.escape(family)}\s*\[(?:强|复核)\]", probe_line)
            }
            unexpected = sorted(reported - set(integrity_signals))
            if unexpected:
                errors.append(
                    "integrity probe line reports unraised families: "
                    + ", ".join(unexpected)
                )
        elif "触发：" not in probe_line and "无阈值信号" not in probe_line:
            errors.append("benchmark probe line must list 触发 families or 无阈值信号")

    family_lines: dict[str, str] = {}
    family_verdicts: dict[str, str] = {}
    for family in INTEGRITY_FAMILIES:
        family_line = next(
            (
                line for line in map_text.splitlines()
                if family in line and "完整性量化" not in line
            ),
            "",
        )
        family_lines[family] = family_line
        if not family_line:
            errors.append(f"integrity check missing family: {family}")
        else:
            verdict_match = re.search(r"通过|观察|问题", family_line)
            if verdict_match:
                family_verdicts[family] = verdict_match.group(0)
        if family_line and family not in family_verdicts:
            errors.append(f"integrity family needs 通过/观察/问题 verdict: {family}")
        if require_integrity_probe and family_line:
            audit_label = INTEGRITY_AUDIT_LABELS[family]
            if audit_label not in family_line or "与" not in family_line:
                errors.append(
                    f"benchmark integrity family needs paired visible evidence "
                    f"using {audit_label}…与…: {family}"
                )
            if family == "边缘/裁切" and not (
                ("左" in family_line and "右" in family_line)
                or ("上" in family_line and "下" in family_line)
            ):
                errors.append("benchmark crop check must compare 左/右 or 上/下 edges")
            if family == "轴线/透视":
                if not re.search(r"共同滚转[：:]\s*(是|否|不确定)", family_line):
                    errors.append("benchmark axis check must record 共同滚转：是/否/不确定")
                if "透视检验：" not in family_line:
                    errors.append("benchmark axis check must include 透视检验：")
            if family == "细节":
                if "关键接口：" not in family_line:
                    errors.append("benchmark detail check must localize a 关键接口：")

    if require_integrity_probe and integrity_signals is not None:
        for family, strength in integrity_signals.items():
            if family_verdicts.get(family) == "通过" and "反证：" not in family_lines[family]:
                errors.append(
                    f"raised integrity family marked 通过 needs localized 反证: {family}"
                )
            if (
                family == "轴线/透视"
                and strength == "strong"
                and family_verdicts.get(family) == "通过"
            ):
                errors.append("strong axis consensus cannot be marked 通过")
            if (
                family == "色彩"
                and strength == "strong"
                and family_verdicts.get(family) == "通过"
            ):
                for label in ("材质分离：", "饱和层级：", "中性锚点："):
                    if label not in family_lines[family]:
                        errors.append(
                            f"strong color pass needs structured counter-evidence: {label}"
                        )

    if require_integrity_probe:
        edge_ledger = next(
            (line for line in map_text.splitlines() if "四边账本：" in line),
            "",
        )
        if not edge_ledger:
            errors.append("benchmark map must include 四边账本：")
        elif not all(label in edge_ledger for label in ("左=", "右=", "上=", "下=", "中心锚点=")):
            errors.append("四边账本 must name 左/右/上/下 and 中心锚点")

        localization = next(
            (line for line in map_text.splitlines() if "关键区域定位：" in line),
            "",
        )
        if not localization:
            errors.append("benchmark map must include 关键区域定位：")
        elif not all(label in localization for label in ("①", "②", "③")) or localization.count("→") < 3:
            errors.append("关键区域定位 must contain ①/②/③ with three visible relation arrows")

        relation_line = next(
            (line for line in map_text.splitlines() if "关系覆盖：" in line),
            "",
        )
        if not relation_line:
            errors.append("benchmark map must include 关系覆盖：")
        else:
            for label in RELATION_COVERAGE_LABELS:
                if not re.search(
                    rf"{re.escape(label)}=[^；;\n]*与[^；;\n]*→[^；;\n]+",
                    relation_line,
                ):
                    errors.append(
                        f"relationship coverage needs localized pair and effect: {label}=…与…→…"
                    )

        priority_line = next(
            (line for line in map_text.splitlines() if "优先级裁决：" in line),
            "",
        )
        if not priority_line:
            errors.append("benchmark map must include 优先级裁决：")
        else:
            for label in ("候选A=", "候选B=", "依据=", "结论="):
                if label not in priority_line:
                    errors.append(f"priority adjudication missing field: {label}")
            loss_gate = re.search(r"损失栅栏=(触发|未触发)", priority_line)
            if not loss_gate:
                errors.append("priority adjudication must record 损失栅栏=触发/未触发")
            else:
                has_integrity_problem = any(
                    verdict == "问题" for verdict in family_verdicts.values()
                )
                if has_integrity_problem and loss_gate.group(1) != "触发":
                    errors.append("an integrity 问题 must trigger the information-loss gate")
                if loss_gate.group(1) == "触发":
                    candidate_a = priority_line.split("候选A=", 1)[1].split("；", 1)[0]
                    if not any(family in candidate_a for family in INTEGRITY_FAMILIES):
                        errors.append("triggered loss gate must place an integrity family in 候选A")
            factor_count = sum(factor in priority_line for factor in PRIORITY_FACTORS)
            if factor_count < 2:
                errors.append("priority adjudication must compare at least two decision factors")
            named_classes = [
                family for family in PRIMARY_FAMILY_PATTERNS
                if family in priority_line.split("依据=", 1)[0]
            ]
            if len(set(named_classes)) < 2:
                errors.append("priority adjudication must compare two distinct named candidate classes")
            conclusion_match = re.search(
                r"结论=\s*(" + "|".join(map(re.escape, PRIMARY_FAMILY_PATTERNS)) + r")",
                priority_line,
            )
            if not conclusion_match:
                errors.append("priority adjudication conclusion must name one supported class")
            else:
                conclusion = conclusion_match.group(1)
                primary_lines = [line for line in map_text.splitlines() if "首要" in line]
                primary_line = primary_lines[0] if len(primary_lines) == 1 else ""
                if primary_line and not re.search(PRIMARY_FAMILY_PATTERNS[conclusion], primary_line):
                    errors.append("priority adjudication conclusion must match the single 首要 line")

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

    if require_integrity_probe and integrity_signals is not None:
        unresolved_strong = [
            family
            for family, strength in integrity_signals.items()
            if strength == "strong" and family_verdicts.get(family) != "通过"
        ]
        if unresolved_strong:
            primary_lines = [line for line in map_text.splitlines() if "首要" in line]
            primary_line = primary_lines[0] if len(primary_lines) == 1 else ""
            if not any(
                re.search(PRIMARY_FAMILY_PATTERNS[family], primary_line)
                for family in unresolved_strong
            ):
                errors.append(
                    "an unresolved strong integrity signal must drive the single 首要: "
                    + ", ".join(unresolved_strong)
                )

    if not re.search(r"裁切.{0,30}(上|下|左|右|边缘|比例|画面)", text, re.S):
        errors.append("crop plan must use a visible boundary or proportion")

    for dimension in DIMENSIONS:
        if dimension not in text:
            errors.append(f"missing dimension: {dimension}")

    score_match = re.search(
        r"^##\s+(?:10\.\s*)?八维区间\s*$([\s\S]*?)(?=^##\s+)",
        text,
        re.M,
    )
    score_text = score_match.group(1) if score_match else ""
    dimension_lines = [line for line in score_text.splitlines() if any(d in line for d in DIMENSIONS)]
    reasoned_dimensions = [line for line in dimension_lines if re.search(r"[—：:].{4,}", line)]
    if len(reasoned_dimensions) < 8:
        errors.append("each dimension interval needs an image-specific reason")
    reasons = []
    for line in reasoned_dimensions:
        reason = re.sub(r".*?(?:[0-5]\s*[–-]\s*[0-5]\s*/\s*5|N/A)\s*[；;，,：:\-—]*", "", line)
        reasons.append(re.sub(r"\s+", "", reason).strip("。；;"))
    if len(reasons) >= 8 and len(set(reasons)) < 8:
        errors.append("each score dimension needs a distinct image-specific reason")

    interval_count = len(re.findall(r"(?:[0-5]\s*[–-]\s*[0-5]\s*/\s*5|N/A)", text))
    if interval_count < 8:
        errors.append("expected eight dimension intervals or N/A values")

    status = "研究状态：实验版 v1.5；不是专家认证、客观审美分或学习效果证明。"
    if status not in text:
        errors.append("missing research-status disclaimer")

    if re.search(r"(?:总分|综合得分|大师分|百分位)\s*[：:]?\s*\d", text):
        errors.append("forbidden aggregate/ranking score")

    generic_hits = [phrase for phrase in GENERIC_AUDIT_PHRASES if phrase in text]
    if len(generic_hits) >= 2:
        errors.append("response contains repeated generic audit boilerplate instead of image evidence")

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
    elif require_reference:
        errors.append("benchmark response needs at least one verified exact-work reference")
    elif "本次未提供未经核验的图例。" not in reference_text:
        errors.append("reference section needs verified links or the explicit omission line")

    if "锐化" in text and re.search(r"锐化.{0,12}(恢复|找回|修复).{0,8}(焦点|合焦|细节)", text):
        errors.append("sharpening is claimed to restore missed focus/detail")

    if require_integrity_probe:
        boundary_match = re.search(
            r"^##\s+(?:11\.\s*)?未知项与事实边界\s*$([\s\S]*?)(?=^##\s+)",
            text,
            re.M,
        )
        boundary_text = boundary_match.group(1) if boundary_match else ""
        boundary_line = next(
            (line for line in boundary_text.splitlines() if "事实边界审计：" in line),
            "",
        )
        if not boundary_line:
            errors.append("benchmark response must include 事实边界审计：")
        else:
            for label in FACT_BOUNDARY_LABELS:
                segment_match = re.search(
                    rf"{re.escape(label)}=([^；;\n]+)",
                    boundary_line,
                )
                if not segment_match or not re.search(
                    FACT_BOUNDARY_DISPOSITIONS,
                    segment_match.group(1),
                ):
                    errors.append(
                        f"fact-boundary audit needs an explicit disposition for {label}"
                    )

        analysis_match = re.search(
            r"\A([\s\S]*?)(?=^##\s+(?:9\.\s*)?方法图例与摄影师方向\s*$)",
            text,
            re.M,
        )
        analysis_text = analysis_match.group(1) if analysis_match else text
        risky_assertions: list[str] = []
        for sentence in re.split(r"(?<=[。！？!?；;])|\n", analysis_text):
            risk = INFERENCE_RISK_PATTERN.search(sentence)
            if risk and not INFERENCE_QUALIFIER_PATTERN.search(sentence):
                risky_assertions.append(risk.group(0))
        if risky_assertions:
            errors.append(
                "unqualified single-frame inference at first mention: "
                + ", ".join(sorted(set(risky_assertions)))
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("response", type=Path, help="Markdown critique to validate")
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Require a completed integrity probe and one exact-work reference",
    )
    args = parser.parse_args()

    try:
        text = args.response.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read {args.response}: {exc}", file=sys.stderr)
        return 2

    signals = None
    if args.benchmark:
        image_path = args.response.parent.parent / "images" / f"{args.response.stem}.jpg"
        if not image_path.exists():
            print(f"ERROR: benchmark image is missing: {image_path}", file=sys.stderr)
            return 2
        signals = integrity_signal_map(image_path)

    errors = validate(
        text,
        require_integrity_probe=args.benchmark,
        require_reference=args.benchmark,
        integrity_signals=signals,
    )
    if errors:
        print(f"FAIL: {len(errors)} structural issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: response matches the Photography Coach structural contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
