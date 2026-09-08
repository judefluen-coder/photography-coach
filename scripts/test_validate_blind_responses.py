#!/usr/bin/env python3
"""Tests for batch validation of frozen blind responses."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validate_blind_responses import validate_run
from validate_response import validate


def valid_response(marker: str) -> str:
    dimensions = [
        "技术可读性", "取景与边缘控制", "注意力与形式组织", "光线影调色彩",
        "空间与层次", "时机与关键关系", "信息叙事情绪", "表达一致性与完成度",
    ]
    scores = "\n".join(
        f"- {name}：3–4/5 — {marker}处的{name}证据与邻近区域可区分。"
        for name in dimensions
    )
    return f"""## 我怎样读这张照片
我先看到{marker}，再看到后方边缘；判断信心为中。

## 最成立的一点
主体左侧轮廓与右侧亮面分开，距离关系可读。

## 全画面看片地图
完整性六检：
- 完整性量化：已运行（无阈值信号，仍继续人工六检）。
- 边缘/裁切｜通过｜对边：左侧人物与右侧门框均留有间隔。
- 暗部｜通过｜暗面：左下衣服与右下地面仍可分。
- 高光｜通过｜亮面：中央墙面与右侧灯罩都保留纹理。
- 色彩｜通过｜色彩对照：冷色墙面与暖色衣服各有内部变化。
- 轴线/透视｜通过｜参照：左侧门柱与右侧窗框均和画框一致；共同滚转：否；透视检验：两者没有向同一消失点异常侧倒。
- 细节｜通过｜同尺度：主体眼睛与附近衣纹边缘都自然；关键接口：眼睛轮廓和衣纹转折均可辨。

四边账本：左=人物外有间隔；右=门框外有余量；上=灯罩完整；下=鞋底未切；中心锚点=主体双眼。
关键区域定位：①左侧人物→轮廓与墙面分离；②中央双眼→视线关系可读；③右侧门框→限定空间深度。
关系覆盖：边缘/中心=左侧轮廓与中央双眼→观看路径闭合；空间/动作=双眼与后方门框→前后层次可读；光色/材质=暖色衣服与冷色墙面→人物和墙面分离。
优先级裁决：候选A=细节（双眼可读）；候选B=边缘/裁切（右侧余量）；损失栅栏=未触发（六检没有问题）；依据=关系断裂较小、保护代价较低；结论=细节。

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
作者：Henri Cartier-Bresson，《Behind the Gare Saint-Lazare》，1932
来源：https://www.moma.org/collection/works/98333
看片任务：用二十秒标出人物、倒影与栏杆的三个间隔。
对应本图：都用边缘间隔决定动作是否清楚。
重点看：脚、倒影和栏杆之间没有粘连。
关键差异：参考图是动态瞬间，本图夹具只验证结构。
可迁移实验：固定机位，只改变动作相位拍十二张。

## 八维区间
{scores}

## 未知项与事实边界
人物身份、地点和器材未知。
事实边界审计：角色/关系=保留未知（中央人物）；状态/过程=仅描述（站立姿态）；感受/含义=观看推测（视线集中）；地点/时间/因果=保留未知（室内表面）。

研究状态：实验版 v1.5；不是专家认证、客观审美分或学习效果证明。

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

    def test_missing_visible_integrity_gate_is_rejected(self) -> None:
        self.write_inputs(1)
        text = valid_response("中央主体").replace("完整性六检：\n", "")
        (self.responses / "bench-001.md").write_text(text, encoding="utf-8")
        errors, valid, total = validate_run(self.root)
        self.assertEqual((valid, total), (0, 1))
        self.assertTrue(any("must expose 完整性六检" in error for error in errors))

    def test_missing_integrity_family_is_rejected(self) -> None:
        self.write_inputs(1)
        text = valid_response("中央主体").replace(
            "- 轴线/透视｜通过｜参照：左侧门柱与右侧窗框均和画框一致；共同滚转：否；透视检验：两者没有向同一消失点异常侧倒。\n",
            "",
        )
        (self.responses / "bench-001.md").write_text(text, encoding="utf-8")
        errors, valid, total = validate_run(self.root)
        self.assertEqual((valid, total), (0, 1))
        self.assertTrue(any("missing family: 轴线/透视" in error for error in errors))

    def test_missing_integrity_probe_is_rejected(self) -> None:
        self.write_inputs(1)
        text = valid_response("中央主体").replace(
            "- 完整性量化：已运行（无阈值信号，仍继续人工六检）。\n",
            "",
        )
        (self.responses / "bench-001.md").write_text(text, encoding="utf-8")
        errors, valid, total = validate_run(self.root)
        self.assertEqual((valid, total), (0, 1))
        self.assertTrue(any("must record 完整性量化" in error for error in errors))

    def test_missing_reference_is_rejected_in_benchmark(self) -> None:
        self.write_inputs(1)
        text = valid_response("中央主体")
        start = text.index("## 方法图例与摄影师方向")
        end = text.index("## 八维区间")
        text = text[:start] + "## 方法图例与摄影师方向\n本次未提供未经核验的图例。\n\n" + text[end:]
        (self.responses / "bench-001.md").write_text(text, encoding="utf-8")
        errors, valid, total = validate_run(self.root)
        self.assertEqual((valid, total), (0, 1))
        self.assertTrue(any("needs at least one verified exact-work reference" in error for error in errors))

    def test_actual_probe_trigger_and_falsifier_can_pass(self) -> None:
        text = valid_response("中央建筑").replace(
            "完整性量化：已运行（无阈值信号，仍继续人工六检）",
            "完整性量化：已运行（触发：轴线/透视[复核]）",
        ).replace(
            "参照：左侧门柱与右侧窗框均和画框一致；共同滚转：否；透视检验：两者没有向同一消失点异常侧倒。",
            "参照：左侧门柱与右侧窗框均和画框一致；共同滚转：否；透视检验：两者没有向同一消失点异常侧倒；反证：两根独立竖线平行且没有同向侧倒。",
        )
        self.assertEqual(
            validate(
                text,
                require_integrity_probe=True,
                require_reference=True,
                integrity_signals={"轴线/透视": "review"},
            ),
            [],
        )

    def test_actual_probe_trigger_must_be_transcribed(self) -> None:
        errors = validate(
            valid_response("中央建筑"),
            require_integrity_probe=True,
            require_reference=True,
            integrity_signals={"轴线/透视": "review"},
        )
        self.assertTrue(any("actual trigger: 轴线/透视[复核]" in error for error in errors))

    def test_unresolved_strong_signal_must_drive_primary(self) -> None:
        text = valid_response("中央建筑").replace(
            "完整性量化：已运行（无阈值信号，仍继续人工六检）",
            "完整性量化：已运行（触发：色彩[强]）",
        ).replace(
            "色彩｜通过｜",
            "色彩｜观察｜",
        )
        errors = validate(
            text,
            require_integrity_probe=True,
            require_reference=True,
            integrity_signals={"色彩": "strong"},
        )
        self.assertTrue(any("must drive the single 首要" in error for error in errors))

    def test_strong_axis_consensus_cannot_be_marked_pass(self) -> None:
        text = valid_response("中央建筑").replace(
            "完整性量化：已运行（无阈值信号，仍继续人工六检）",
            "完整性量化：已运行（触发：轴线/透视[强]）",
        ).replace(
            "参照：左侧门柱与右侧窗框均和画框一致；共同滚转：否；透视检验：两者没有向同一消失点异常侧倒。",
            "参照：左侧门柱与右侧窗框均和画框一致；共同滚转：否；透视检验：两者没有向同一消失点异常侧倒；反证：两根独立竖线平行。",
        )
        errors = validate(
            text,
            require_integrity_probe=True,
            require_reference=True,
            integrity_signals={"轴线/透视": "strong"},
        )
        self.assertIn("strong axis consensus cannot be marked 通过", errors)

    def test_benchmark_family_requires_paired_visible_evidence(self) -> None:
        text = valid_response("中央建筑").replace(
            "暗面：左下衣服与右下地面仍可分。",
            "暗部看起来正常。",
        )
        errors = validate(
            text,
            require_integrity_probe=True,
            require_reference=True,
        )
        self.assertTrue(any("暗面：…与…: 暗部" in error for error in errors))

    def test_benchmark_requires_four_edge_ledger(self) -> None:
        text = valid_response("中央建筑").replace(
            "四边账本：左=人物外有间隔；右=门框外有余量；上=灯罩完整；下=鞋底未切；中心锚点=主体双眼。\n",
            "",
        )
        errors = validate(text, require_integrity_probe=True, require_reference=True)
        self.assertIn("benchmark map must include 四边账本：", errors)

    def test_benchmark_requires_three_localized_relations(self) -> None:
        text = valid_response("中央建筑").replace("③右侧门框→限定空间深度", "右侧门框限定空间")
        errors = validate(text, require_integrity_probe=True, require_reference=True)
        self.assertTrue(any("关键区域定位 must contain" in error for error in errors))

    def test_priority_adjudication_must_match_primary(self) -> None:
        text = valid_response("中央建筑").replace(
            "结论=细节。",
            "结论=边缘/裁切。",
        )
        errors = validate(text, require_integrity_probe=True, require_reference=True)
        self.assertIn("priority adjudication conclusion must match the single 首要 line", errors)

    def test_benchmark_requires_three_relation_lanes(self) -> None:
        text = valid_response("中央建筑").replace(
            "关系覆盖：边缘/中心=左侧轮廓与中央双眼→观看路径闭合；空间/动作=双眼与后方门框→前后层次可读；光色/材质=暖色衣服与冷色墙面→人物和墙面分离。\n",
            "",
        )
        errors = validate(text, require_integrity_probe=True, require_reference=True)
        self.assertIn("benchmark map must include 关系覆盖：", errors)

    def test_integrity_problem_triggers_loss_gate(self) -> None:
        text = valid_response("中央建筑").replace(
            "- 细节｜通过｜",
            "- 细节｜问题｜",
        )
        errors = validate(text, require_integrity_probe=True, require_reference=True)
        self.assertIn("an integrity 问题 must trigger the information-loss gate", errors)

    def test_benchmark_requires_fact_boundary_audit(self) -> None:
        text = valid_response("中央建筑").replace(
            "事实边界审计：角色/关系=保留未知（中央人物）；状态/过程=仅描述（站立姿态）；感受/含义=观看推测（视线集中）；地点/时间/因果=保留未知（室内表面）。\n",
            "",
        )
        errors = validate(text, require_integrity_probe=True, require_reference=True)
        self.assertIn("benchmark response must include 事实边界审计：", errors)

    def test_unqualified_single_frame_inference_is_rejected(self) -> None:
        text = valid_response("中央建筑").replace(
            "我先看到中央建筑，再看到后方边缘；判断信心为中。",
            "我先看到一名导游，秋天的阴天里他正在思考；判断信心为中。",
        )
        errors = validate(text, require_integrity_probe=True, require_reference=True)
        self.assertTrue(any("unqualified single-frame inference" in error for error in errors))

    def test_qualified_viewing_hypothesis_is_allowed(self) -> None:
        text = valid_response("中央建筑").replace(
            "我先看到中央建筑，再看到后方边缘；判断信心为中。",
            "我先看到戴帽的人，灰蓝天空视觉上让人联想到阴天，但天气未知；判断信心为中。",
        )
        errors = validate(text, require_integrity_probe=True, require_reference=True)
        self.assertFalse(any("unqualified single-frame inference" in error for error in errors))

    def test_axis_check_requires_roll_and_perspective_tests(self) -> None:
        text = valid_response("中央建筑").replace(
            "；共同滚转：否；透视检验：两者没有向同一消失点异常侧倒",
            "",
        )
        errors = validate(text, require_integrity_probe=True, require_reference=True)
        self.assertIn("benchmark axis check must record 共同滚转：是/否/不确定", errors)
        self.assertIn("benchmark axis check must include 透视检验：", errors)

    def test_strong_color_pass_requires_structured_counterevidence(self) -> None:
        text = valid_response("中央建筑").replace(
            "完整性量化：已运行（无阈值信号，仍继续人工六检）",
            "完整性量化：已运行（触发：色彩[强]）",
        ).replace(
            "色彩对照：冷色墙面与暖色衣服各有内部变化。",
            "色彩对照：冷色墙面与暖色衣服各有内部变化；反证：二者仍可分。",
        )
        errors = validate(
            text,
            require_integrity_probe=True,
            require_reference=True,
            integrity_signals={"色彩": "strong"},
        )
        self.assertTrue(any("strong color pass needs structured counter-evidence" in error for error in errors))

    def test_repeated_score_reason_is_rejected(self) -> None:
        text = valid_response("中央建筑")
        for name in (
            "技术可读性", "取景与边缘控制", "注意力与形式组织", "光线影调色彩",
            "空间与层次", "时机与关键关系", "信息叙事情绪", "表达一致性与完成度",
        ):
            text = text.replace(
                f"中央建筑处的{name}证据与邻近区域可区分。",
                "中央建筑轮廓与邻近区域可区分。",
            )
        errors = validate(text)
        self.assertIn("each score dimension needs a distinct image-specific reason", errors)

    def test_repeated_generic_audit_boilerplate_is_rejected(self) -> None:
        text = valid_response("中央建筑") + "\n边缘与主体关系仍可再整理。前后关系成立，还可用站位进一步厘清。\n"
        errors = validate(text)
        self.assertIn(
            "response contains repeated generic audit boilerplate instead of image evidence",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
