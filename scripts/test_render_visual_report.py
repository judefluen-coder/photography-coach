#!/usr/bin/env python3

from __future__ import annotations

import base64
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("render_visual_report.py")
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
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


def report_payload(source: Path, treatment: Path | None = None) -> dict:
    payload = {
        "title": "第一眼被亮处带走，动作还没站稳。",
        "source_image": str(source),
        "summary": "先看见左边的亮面，再看到中间的人。画面有层次，但主次还可以更清楚。",
        "priority": {"title": "让手和工具先分开。", "body": "中间两处边缘叠在一起，动作读起来慢。"},
        "strength": {"title": "保留前后的距离。", "body": "前景和后方大小不同，让观看位置很清楚。"},
        "observations": [
            {"label": "构图", "priority": "首要", "text": "左边亮面与中间动作同样抢眼。"},
            {"label": "边缘", "priority": "次要", "text": "右边空间比左边更松。"},
            {"label": "明暗", "priority": "次要", "text": "高光比脸和手更快被看见。"},
            {"label": "空间", "priority": "要保护", "text": "前中后景的大小变化很清楚。"},
            {"label": "时机", "priority": "次要", "text": "手势和器具还没有分开。"},
            {"label": "画质", "priority": "无明显问题", "text": "关键轮廓仍然能读。"},
        ],
        "scores": [
            {"dimension": dimension, "interval": "3-4 / 5", "reason": f"{dimension}有具体可见依据。"}
            for dimension in SCORE_DIMENSIONS
        ],
        "reshoot": {
            "action": "向右挪半步，等手露出来再按。",
            "effect": "动作会先被看见。",
            "cost": "前景包围感会少一点。",
            "availability": "相似场景",
        },
        "edit": {
            "summary": "先整理亮暗，再微调颜色。",
            "crop": "上边裁去少量空白。",
            "tone_color": "压高光，提中间调，收一点黄色。",
            "limit": "不能补回被挡住的手势。",
        },
        "reference": {
            "photographer": "Example Photographer",
            "title": "Exact Work",
            "year": "1994",
            "url": "https://example.com/exact-work",
            "looking_task": "先用 30 秒找出前三个落点。",
            "match": "都在处理复杂环境里的观看顺序。",
            "difference": "参考图靠颜色分组，这张主要靠距离。",
        },
        "exercise": {
            "title": "拍 12 张，只改变左右位置。",
            "instructions": "两秒内能说出第一和第二落点就算通过。",
        },
        "boundary_note": "人物身份、关系和地点仍然未知。",
        "research_status": "实验版 v1.6。不是专家认证、客观审美分或学习效果证明。",
    }
    if treatment:
        payload["treatment_image"] = str(treatment)
    return payload


class RenderVisualReportTest(unittest.TestCase):
    def run_renderer(self, payload: dict, root: Path) -> subprocess.CompletedProcess[str]:
        input_path = root / "report.json"
        input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return subprocess.run(
            ["python3", str(SCRIPT), "--input", str(input_path), "--output", str(root / "output")],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_renders_with_treatment_and_escapes_embedded_markup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            treatment = root / "treatment.png"
            source.write_bytes(PNG_1X1)
            treatment.write_bytes(PNG_1X1)
            payload = report_payload(source, treatment)
            payload["summary"] = "可见文字 <script>alert(1)</script> 只应当作文字。"

            result = self.run_renderer(payload, root)

            self.assertEqual(result.returncode, 0, result.stderr)
            output = root / "output"
            html = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("\\u003cscript\\u003e", html)
            self.assertNotIn("<script>alert(1)</script>", html)
            self.assertTrue((output / "assets" / "source.png").is_file())
            self.assertTrue((output / "assets" / "treatment.png").is_file())
            self.assertIn('"treatment_asset":"assets/treatment.png"', html)

    def test_renders_source_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            source.write_bytes(PNG_1X1)

            result = self.run_renderer(report_payload(source), root)

            self.assertEqual(result.returncode, 0, result.stderr)
            html = (root / "output" / "index.html").read_text(encoding="utf-8")
            self.assertIn('"treatment_asset":null', html)

    def test_rejects_wrong_score_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            source.write_bytes(PNG_1X1)
            payload = report_payload(source)
            payload["scores"][0], payload["scores"][1] = payload["scores"][1], payload["scores"][0]

            result = self.run_renderer(payload, root)

            self.assertEqual(result.returncode, 2)
            self.assertIn("eight stable dimensions", result.stderr)

    def test_rejects_output_inside_skill_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            source.write_bytes(PNG_1X1)
            input_path = root / "report.json"
            input_path.write_text(json.dumps(report_payload(source), ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--output",
                    str(SCRIPT.parent.parent / "private-report"),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("outside the skill repository", result.stderr)


if __name__ == "__main__":
    unittest.main()
