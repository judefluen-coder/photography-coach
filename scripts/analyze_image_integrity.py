#!/usr/bin/env python3
"""Measure image-level cues that deserve visual integrity review.

The output is intentionally a set of attention signals, not an aesthetic verdict.
Every signal still needs a localized visual confirmation or falsifier.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps


MAX_ANALYSIS_SIDE = 640
AXIS_SAMPLE_STEP = 2


def _fraction(count: int, total: int) -> float:
    return round(count / total, 6) if total else 0.0


def _quantile(histogram: list[int], quantile: float) -> int:
    target = sum(histogram) * quantile
    running = 0
    for value, count in enumerate(histogram):
        running += count
        if running >= target:
            return value
    return len(histogram) - 1


def _analysis_copy(image: Image.Image) -> Image.Image:
    result = ImageOps.exif_transpose(image).convert("RGB")
    result.thumbnail((MAX_ANALYSIS_SIDE, MAX_ANALYSIS_SIDE), Image.Resampling.LANCZOS)
    return result


def _pixel_metrics(image: Image.Image) -> dict[str, Any]:
    luminance_histogram = [0] * 256
    saturation_histogram = [0] * 256
    near_black = deep_shadow = low_shadow = 0
    near_white = all_channel_clip = any_channel_clip = 0
    high_saturation = extreme_saturation = 0
    neutral_count = neutral_red = neutral_green = neutral_blue = 0

    pixels = list(image.get_flattened_data())
    for red, green, blue in pixels:
        luminance = (54 * red + 183 * green + 19 * blue) >> 8
        maximum = max(red, green, blue)
        minimum = min(red, green, blue)
        saturation = round(255 * (maximum - minimum) / maximum) if maximum else 0
        luminance_histogram[luminance] += 1
        saturation_histogram[saturation] += 1
        near_black += luminance <= 4
        deep_shadow += luminance <= 16
        low_shadow += luminance <= 32
        near_white += luminance >= 245
        all_channel_clip += red >= 250 and green >= 250 and blue >= 250
        any_channel_clip += maximum >= 250
        high_saturation += saturation >= 217
        extreme_saturation += saturation >= 242
        if saturation <= 38 and 32 <= luminance <= 224:
            neutral_count += 1
            neutral_red += red
            neutral_green += green
            neutral_blue += blue

    total = len(pixels)
    low_shadow_count = max(low_shadow, 1)
    neutral_means = None
    neutral_cast_spread = None
    if neutral_count:
        neutral_means = {
            "red": round(neutral_red / neutral_count, 2),
            "green": round(neutral_green / neutral_count, 2),
            "blue": round(neutral_blue / neutral_count, 2),
        }
        neutral_cast_spread = round(
            (max(neutral_means.values()) - min(neutral_means.values())) / 255,
            6,
        )

    return {
        "shadow": {
            "near_black_fraction": _fraction(near_black, total),
            "deep_shadow_fraction": _fraction(deep_shadow, total),
            "low_shadow_fraction": _fraction(low_shadow, total),
            "shadow_floor_concentration": round(near_black / low_shadow_count, 6),
            "luminance_p01": _quantile(luminance_histogram, 0.01),
            "luminance_p10": _quantile(luminance_histogram, 0.10),
        },
        "highlight": {
            "near_white_fraction": _fraction(near_white, total),
            "all_channel_clip_fraction": _fraction(all_channel_clip, total),
            "any_channel_clip_fraction": _fraction(any_channel_clip, total),
            "luminance_p90": _quantile(luminance_histogram, 0.90),
            "luminance_p99": _quantile(luminance_histogram, 0.99),
        },
        "color": {
            "saturation_mean": round(
                sum(value * count for value, count in enumerate(saturation_histogram))
                / max(total * 255, 1),
                6,
            ),
            "saturation_p90": round(_quantile(saturation_histogram, 0.90) / 255, 6),
            "high_saturation_fraction": _fraction(high_saturation, total),
            "extreme_saturation_fraction": _fraction(extreme_saturation, total),
            "neutral_anchor_fraction": _fraction(neutral_count, total),
            "neutral_anchor_rgb_mean": neutral_means,
            "neutral_cast_spread": neutral_cast_spread,
        },
    }


def _gradient_metrics(image: Image.Image) -> dict[str, Any]:
    gray = image.convert("L")
    width, height = gray.size
    values = list(gray.get_flattened_data())
    gradients: list[int] = []
    orientation_energy = [0.0] * 91
    horizontal_axis_energy = [0.0] * 31
    vertical_axis_energy = [0.0] * 31
    border_energy = {"left": 0.0, "right": 0.0, "top": 0.0, "bottom": 0.0}
    border_samples = {key: 0 for key in border_energy}
    border_x = max(2, round(width * 0.04))
    border_y = max(2, round(height * 0.04))

    for y in range(1, height - 1, AXIS_SAMPLE_STEP):
        row = y * width
        for x in range(1, width - 1, AXIS_SAMPLE_STEP):
            gx = values[row + x + 1] - values[row + x - 1]
            gy = values[row + width + x] - values[row - width + x]
            magnitude = abs(gx) + abs(gy)
            gradients.append(magnitude)
            if magnitude >= 28:
                line_angle = (math.degrees(math.atan2(gy, gx)) + 90.0) % 180.0
                deviation = line_angle if line_angle <= 45 else (
                    line_angle - 90 if line_angle <= 135 else line_angle - 180
                )
                bin_index = min(90, round(deviation + 45))
                orientation_energy[bin_index] += magnitude
                if line_angle <= 15 or line_angle >= 165:
                    horizontal_deviation = line_angle if line_angle <= 15 else line_angle - 180
                    horizontal_axis_energy[round(horizontal_deviation) + 15] += magnitude
                elif 75 <= line_angle <= 105:
                    vertical_deviation = line_angle - 90
                    vertical_axis_energy[round(vertical_deviation) + 15] += magnitude
            for key, inside in (
                ("left", x < border_x),
                ("right", x >= width - border_x),
                ("top", y < border_y),
                ("bottom", y >= height - border_y),
            ):
                if inside:
                    border_energy[key] += magnitude
                    border_samples[key] += 1

    if not gradients:
        return {
            "detail": {"gradient_mean": 0.0, "gradient_p95": 0.0, "strong_edge_fraction": 0.0},
            "axis": {"dominant_axis_deviation_degrees": None, "axis_support_fraction": 0.0},
            "border": {"normalized_edge_energy": {}, "opposite_edge_imbalance": None},
        }

    gradients.sort()
    total_gradient = sum(gradients)
    p95 = gradients[min(len(gradients) - 1, round(0.95 * (len(gradients) - 1)))]
    strong_count = sum(value >= 48 for value in gradients)

    total_orientation = sum(orientation_energy)
    axis_start = 30  # -15 degrees from the nearest frame axis
    axis_end = 61    # +15 degrees from the nearest frame axis
    axis_energy = orientation_energy[axis_start:axis_end]
    peak_index = (
        axis_start + max(range(len(axis_energy)), key=axis_energy.__getitem__)
        if sum(axis_energy)
        else 45
    )
    peak_start = max(0, peak_index - 2)
    peak_end = min(len(orientation_energy), peak_index + 3)
    peak_support = sum(orientation_energy[peak_start:peak_end])
    axis_band_energy = sum(axis_energy)
    dominant_deviation = peak_index - 45 if axis_band_energy else None

    def axis_peak(energy: list[float]) -> tuple[int | None, float]:
        total = sum(energy)
        if not total:
            return None, 0.0
        index = max(range(len(energy)), key=energy.__getitem__)
        start = max(0, index - 2)
        end = min(len(energy), index + 3)
        return index - 15, sum(energy[start:end])

    horizontal_deviation, horizontal_peak_support = axis_peak(horizontal_axis_energy)
    vertical_deviation, vertical_peak_support = axis_peak(vertical_axis_energy)
    horizontal_band_energy = sum(horizontal_axis_energy)
    vertical_band_energy = sum(vertical_axis_energy)
    consensus_deviation = None
    if (
        horizontal_deviation is not None
        and vertical_deviation is not None
        and abs(horizontal_deviation - vertical_deviation) <= 3
    ):
        consensus_deviation = round(
            (
                horizontal_deviation * horizontal_peak_support
                + vertical_deviation * vertical_peak_support
            )
            / max(horizontal_peak_support + vertical_peak_support, 1e-9),
            2,
        )

    whole_mean = total_gradient / len(gradients)
    normalized = {
        key: round((border_energy[key] / max(border_samples[key], 1)) / max(whole_mean, 1e-9), 4)
        for key in border_energy
    }
    horizontal_pair = max(normalized["left"], normalized["right"]) / max(
        min(normalized["left"], normalized["right"]), 0.05
    )
    vertical_pair = max(normalized["top"], normalized["bottom"]) / max(
        min(normalized["top"], normalized["bottom"]), 0.05
    )

    return {
        "detail": {
            "gradient_mean": round(whole_mean / 510, 6),
            "gradient_p95": round(p95 / 510, 6),
            "strong_edge_fraction": _fraction(strong_count, len(gradients)),
        },
        "axis": {
            "dominant_axis_deviation_degrees": dominant_deviation,
            "axis_support_fraction": round(axis_band_energy / total_orientation, 6)
            if total_orientation else 0.0,
            "axis_peak_fraction": round(peak_support / axis_band_energy, 6)
            if axis_band_energy else 0.0,
            "horizontal_axis_deviation_degrees": horizontal_deviation,
            "vertical_axis_deviation_degrees": vertical_deviation,
            "axis_consensus_deviation_degrees": consensus_deviation,
            "independent_axis_support_fraction": round(
                min(horizontal_band_energy, vertical_band_energy) / total_orientation,
                6,
            ) if total_orientation else 0.0,
        },
        "border": {
            "normalized_edge_energy": normalized,
            "opposite_edge_imbalance": round(max(horizontal_pair, vertical_pair), 4),
        },
    }


def _signals(metrics: dict[str, Any]) -> list[dict[str, str]]:
    signals: list[dict[str, str]] = []
    shadow = metrics["shadow"]
    highlight = metrics["highlight"]
    color = metrics["color"]
    detail = metrics["detail"]
    axis = metrics["axis"]
    border = metrics["border"]

    def add(family: str, strength: str, basis: str) -> None:
        existing = next((item for item in signals if item["family"] == family), None)
        if existing is None:
            signals.append({"family": family, "strength": strength, "basis": basis})
            return
        if strength == "strong":
            existing["strength"] = "strong"
        existing["basis"] = f"{existing['basis']} {basis}"

    if shadow["deep_shadow_fraction"] >= 0.12 and shadow["shadow_floor_concentration"] >= 0.18:
        add(
            "暗部",
            "strong",
            "深暗像素占比较大且集中在接近纯黑的窄区间；检查关键暗面是否仍有材质和边界。",
        )
    elif shadow["deep_shadow_fraction"] >= 0.06:
        add("暗部", "review", "深暗区域占比较大；逐区确认它是局部剪影还是多种材料被合并。")

    if highlight["all_channel_clip_fraction"] >= 0.02 or highlight["any_channel_clip_fraction"] >= 0.12:
        add(
            "高光",
            "strong",
            "近白或单通道顶格像素占比较大；检查最亮主体表面是否失去纹理、形状或色相。",
        )
    elif highlight["all_channel_clip_fraction"] >= 0.005 or highlight["any_channel_clip_fraction"] >= 0.05:
        add("高光", "review", "存在成片接近上限的亮像素；区分小反光与需要保留信息的亮面。")

    if color["high_saturation_fraction"] >= 0.20 or color["extreme_saturation_fraction"] >= 0.08:
        add(
            "色彩",
            "strong",
            "高饱和像素覆盖面较大；检查不同材料是否失去内部色相/明度差，以及饱和度是否仍有层级。",
        )
    elif color["high_saturation_fraction"] >= 0.08:
        add("色彩", "review", "高饱和区域不小；确认它是否集中于视觉锚点，而不是平均铺满多个平面。")
    if (
        color["neutral_anchor_fraction"] >= 0.05
        and color["neutral_cast_spread"] is not None
        and color["neutral_cast_spread"] >= 0.05
    ):
        add("色彩", "review", "低色度锚点的 RGB 均值分离明显；检查偏色是否符合画面内的光源关系。")

    if (
        detail["gradient_mean"] <= 0.012
        and detail["gradient_p95"] <= 0.05
    ) or (
        detail["strong_edge_fraction"] <= 0.0005
        and detail["gradient_p95"] <= 0.06
    ):
        add(
            "细节",
            "review",
            "全图边缘能量偏低；在 100% 下比较关键区域与同尺度邻近纹理，排除重采样、涂抹或失焦。",
        )

    if (
        axis.get("axis_consensus_deviation_degrees") is not None
        and abs(axis["axis_consensus_deviation_degrees"]) >= 3
        and axis.get("independent_axis_support_fraction", 0) >= 0.035
    ):
        add(
            "轴线/透视",
            "strong",
            "水平与垂直边缘在同一偏角形成独立共识；必须以画面中的两条具名稳定参照复核全局滚转。",
        )
    elif (
        axis["dominant_axis_deviation_degrees"] is not None
        and abs(axis["dominant_axis_deviation_degrees"]) >= 3
        and axis["axis_support_fraction"] >= 0.25
    ):
        add(
            "轴线/透视",
            "review",
            "较强边缘在偏离画框轴线的位置形成峰值；必须再找两条本应水平或垂直的独立参照。",
        )

    if border["opposite_edge_imbalance"] is not None and border["opposite_edge_imbalance"] >= 2.5:
        add(
            "边缘/裁切",
            "review",
            "相对两边的边缘信息密度差异较大；检查高密度一侧是否切入关键轮廓，同时另一侧留有无关余量。",
        )
    return signals


def analyze(path: Path) -> dict[str, Any]:
    with Image.open(path) as opened:
        original_size = opened.size
        image = _analysis_copy(opened)
    metrics = _pixel_metrics(image)
    metrics.update(_gradient_metrics(image))
    return {
        "image": {
            "path": str(path.resolve()),
            "original_width": original_size[0],
            "original_height": original_size[1],
            "analysis_width": image.width,
            "analysis_height": image.height,
        },
        "metrics": metrics,
        "signals": _signals(metrics),
        "interpretation_rule": (
            "Signals route attention only. Confirm each with localized visible evidence; "
            "absence of a signal does not prove that the family passes."
        ),
    }


def _print_text(result: dict[str, Any]) -> None:
    image = result["image"]
    print(
        f"Integrity probe: {image['original_width']}x{image['original_height']} "
        f"(analysis {image['analysis_width']}x{image['analysis_height']})"
    )
    if not result["signals"]:
        print("- No threshold signal. This is not a six-family pass; continue visual review.")
    for signal in result["signals"]:
        print(f"- {signal['family']} [{signal['strength']}]: {signal['basis']}")
    print(f"- Rule: {result['interpretation_rule']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--json", action="store_true", help="Emit the complete JSON record")
    args = parser.parse_args()
    try:
        result = analyze(args.image)
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot analyze {args.image}: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
