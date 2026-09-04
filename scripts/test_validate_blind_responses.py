#!/usr/bin/env python3
"""Tests for batch validation of frozen blind responses."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validate_blind_responses import validate_run


def valid_response(marker: str) -> str:
    dimensions = [
        "技术可读性", "取景与边缘控制", "注意力与形式组织", "光线影调色彩",
        "空间与层次", "时机与关键关系", "信息叙事情绪", "表达一致性与完成度",
    ]
    scores = "\n".join(f"- {name}：3–4/5 — {marker}处的可见关系基本成立。" for name in dimensions)
    return f"""## 我怎样读这张照片
我先看到{marker}，再看到后方边缘；判断信心为中。

## 最成立的一点
主体左侧轮廓与右侧亮面分开，距离关系可读。

## 全画面看片地图
- 技术清晰：关键区域可辨。首要
- 取景边缘：右边保留间隔。次要
- 注意力与线条：主线指向中央。次要
- 光线影调色彩：亮部支持主体。要保护
- 空间层次与远近：前后重叠可读。无明显问题
- 时机与人物关系：姿态保持分离。无明显问题
- 信息叙事：环境线索有限。无明显问题

## 决策
当前关系基本成立。

内部判断：NO_STRUCTURAL_BOTTLENECK

## 下一次怎么拍
动作：向右移动半步。 预期效果：分开轮廓。 代价：减少左侧环境。 可得性：相似场景

## 裁切与调色方案
裁切右边缘约百分之五，略压高光；代价是环境信息减少。

## 后期：能做 / 不能做
能微调亮度；不能恢复画外信息。

## 20–40 分钟练习
用二十分钟拍十二张，只改变左右位置，以轮廓是否分开为通过标准。

## 方法图例与摄影师方向
本次未提供未经核验的图例。

## 八维区间
{scores}

## 未知项与事实边界
人物身份、地点和器材未知。

研究状态：实验版 v0.1；不是专家认证、客观审美分或学习效果证明。

## 可选语境复核
如愿意可补充用途，再做第二遍语境复核。
"""


class BlindResponseValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.responses = self.root / "responses"
        self.responses.mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_inputs(self, count: int) -> None:
        rows = [
            {
                "ordinal": index,
                "case_id": f"bench-{index:03d}",
                "response_path": str(self.responses / f"bench-{index:03d}.md"),
            }
            for index in range(1, count + 1)
        ]
        (self.root / "blind-inputs.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
        )

    def test_two_distinct_valid_responses_pass(self) -> None:
        self.write_inputs(2)
        (self.responses / "bench-001.md").write_text(valid_response("左侧人物"), encoding="utf-8")
        (self.responses / "bench-002.md").write_text(valid_response("中央建筑"), encoding="utf-8")
        errors, valid, total = validate_run(self.root)
        self.assertEqual(errors, [])
        self.assertEqual((valid, total), (2, 2))

    def test_duplicate_response_is_rejected(self) -> None:
        self.write_inputs(2)
        text = valid_response("中央主体")
        (self.responses / "bench-001.md").write_text(text, encoding="utf-8")
        (self.responses / "bench-002.md").write_text(text, encoding="utf-8")
        errors, valid, total = validate_run(self.root)
        self.assertEqual((valid, total), (1, 2))
        self.assertTrue(any("byte-identical response duplicates" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
