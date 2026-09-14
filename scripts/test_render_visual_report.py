#!/usr/bin/env python3

from __future__ import annotations

import base64
import json
import re
import shutil
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
    def embedded_data(self, root: Path) -> dict:
        html = (root / 'output' / 'index.html').read_text(encoding='utf-8')
        return json.loads(re.search(r'<script id="reportData" type="application/json">(.*?)</script>', html, re.S)[1])

    def test_copies_color_master_and_preview_with_distinct_downloads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, color, treatment, preview = [root / name for name in ('source.png', 'color.png', 'treatment.png', 'preview.png')]
            for path in (source, color, treatment, preview):
                path.write_bytes(PNG_1X1)
            payload = report_payload(source, treatment)
            payload.update(color_image=str(color), color_preview_image=str(preview),
                           source_preview_image=str(preview), treatment_preview_image=str(preview),
                           source_download='javascript:alert(1)', color_asset='../stale.png')
            result = self.run_renderer(payload, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = self.embedded_data(root)
            for kind in ('source', 'color', 'treatment'):
                self.assertEqual(data[f'{kind}_asset'], f'assets/{kind}-preview.png')
                self.assertEqual(data[f'{kind}_download'], f'assets/{kind}.png')
                self.assertEqual((root / 'output' / data[f'{kind}_download']).read_bytes(), PNG_1X1)
                self.assertTrue((root / 'output' / data[f'{kind}_asset']).is_file())
                self.assertNotIn(f'{kind}_image', data)
                self.assertNotIn(f'{kind}_preview_image', data)

    def test_color_only_does_not_invent_combined_treatment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.png'
            source.write_bytes(PNG_1X1)
            payload = report_payload(source)
            payload.update(color_image=str(source), treatment_asset='../stale.png', treatment_download='../stale.png')
            result = self.run_renderer(payload, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = self.embedded_data(root)
            self.assertEqual(data['color_download'], 'assets/color.png')
            self.assertIsNone(data['treatment_asset'])
            self.assertIsNone(data['treatment_download'])

    def test_missing_color_or_preview_files_fail_before_output(self) -> None:
        for field in ('color_image', 'source_preview_image'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / 'source.png'
                source.write_bytes(PNG_1X1)
                payload = report_payload(source)
                payload[field] = 'missing.png'
                result = self.run_renderer(payload, root)
                self.assertEqual(result.returncode, 2)
                self.assertIn(field, result.stderr)
                self.assertFalse((root / 'output').exists())

    def test_orphan_previews_are_not_masters(self) -> None:
        for kind in ('color', 'treatment'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / 'source.png'
                source.write_bytes(PNG_1X1)
                payload = report_payload(source)
                payload[f'{kind}_preview_image'] = str(source)
                result = self.run_renderer(payload, root)
                self.assertEqual(result.returncode, 2)
                self.assertIn(f'requires {kind}_image', result.stderr)

    def test_optional_integrity_and_credit_survive_with_escaped_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.png'
            source.write_bytes(PNG_1X1)
            payload = report_payload(source)
            payload['integrity'] = [{'family': family, 'verdict': '观察', 'basis': '具体位置仍待复核。'}
                                    for family in ['边缘/裁切', '暗部', '高光', '色彩', '轴线/透视', '细节']]
            payload['source_credit'] = {'author': '<script>untrusted()</script>', 'url': 'https://example.com/photo',
                                        'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
                                        'changes': '仅调色，作者未背书。'}
            result = self.run_renderer(payload, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = self.embedded_data(root)
            self.assertEqual(data['integrity'], payload['integrity'])
            self.assertEqual(data['source_credit'], payload['source_credit'])
            self.assertNotIn('<script>untrusted()</script>', (root / 'output' / 'index.html').read_text())
            if shutil.which('node'):
                ui = subprocess.run(['node', str(SCRIPT.with_name('test_visual_report_ui.mjs')),
                                     str(root / 'output' / 'index.html')], capture_output=True, text=True)
                self.assertEqual(ui.returncode, 0, ui.stdout + ui.stderr)

    def test_rejects_unsafe_credit_urls(self) -> None:
        from render_visual_report import ReportError, validate_report
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.png'
            source.write_bytes(PNG_1X1)
            payload = report_payload(source)
            payload['source_credit'] = {'author': 'Example', 'url': 'javascript:alert(1)',
                                        'license': 'CC BY', 'license_url': 'https://example.com/license', 'changes': 'None'}
            with self.assertRaisesRegex(ReportError, 'source_credit.url'):
                validate_report(payload, root)

    def test_rejects_incomplete_or_misordered_integrity_checks(self) -> None:
        from render_visual_report import ReportError, validate_report
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.png'
            source.write_bytes(PNG_1X1)
            for checks in ([], [{'family': '暗部', 'verdict': '通过', 'basis': '说明'}] * 6):
                payload = report_payload(source)
                payload['integrity'] = checks
                with self.subTest(checks=checks), self.assertRaisesRegex(ReportError, 'six'):
                    validate_report(payload, root)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for inline-JS unit checks')
    def test_inline_ui_handles_all_four_version_combinations(self) -> None:
        for has_color, has_treatment in ((False, False), (True, False), (False, True), (True, True)):
            with self.subTest(color=has_color, treatment=has_treatment), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / 'source.png'
                source.write_bytes(PNG_1X1)
                payload = report_payload(source, source if has_treatment else None)
                if has_color:
                    payload['color_image'] = str(source)
                payload['edit']['crop_region'] = {'x': 0, 'y': 0, 'width': 1, 'height': 1}
                result = self.run_renderer(payload, root)
                self.assertEqual(result.returncode, 0, result.stderr)
                ui = subprocess.run(['node', str(SCRIPT.with_name('test_visual_report_ui.mjs')),
                                     str(root / 'output' / 'index.html')], capture_output=True, text=True)
                self.assertEqual(ui.returncode, 0, ui.stdout + ui.stderr)

    def test_scores_reject_out_of_range_reversed_and_non_interval_values(self) -> None:
        from render_visual_report import ReportError, validate_report
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.png'
            source.write_bytes(PNG_1X1)
            for interval in ['5-6 / 5', '4-2 / 5', '3.5-4 / 5', '90%', '4 / 5']:
                payload = report_payload(source)
                payload['scores'][0]['interval'] = interval
                with self.subTest(interval=interval), self.assertRaisesRegex(ReportError, 'ordered 0-5'):
                    validate_report(payload, root)

    def test_scores_accept_bounded_integer_intervals_and_not_applicable(self) -> None:
        from render_visual_report import validate_report
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.png'
            source.write_bytes(PNG_1X1)
            for interval in ['0-0 / 5', '0-5 / 5', '5-5/5', 'N/A']:
                payload = report_payload(source)
                payload['scores'][0]['interval'] = interval
                with self.subTest(interval=interval):
                    validate_report(payload, root)

    def test_region_coordinates_reject_out_of_frame_and_nonfinite_values(self) -> None:
        from render_visual_report import ReportError, validate_rectangle
        for value in [
            {"x": .9, "y": 0, "width": .2, "height": .1},
            {"x": float('nan'), "y": 0, "width": .2, "height": .1},
            {"x": True, "y": 0, "width": .2, "height": .1},
            {"x": 0, "y": 0, "width": 0, "height": .1},
        ]:
            with self.subTest(value=value), self.assertRaises(ReportError):
                validate_rectangle(value, 'regions')

    def test_regions_crop_and_optional_uncertainty_survive_render(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            source.write_bytes(PNG_1X1)
            payload = report_payload(source)
            payload['decision'] = 'NO_STRUCTURAL_BOTTLENECK'
            payload['observations'][0]['regions'] = [{"x": .1, "y": .2, "width": .4, "height": .3}]
            payload['edit']['crop_region'] = {"x": .1, "y": .1, "width": .9, "height": .8}
            payload['scores'][0]['uncertainty'] = '原始分辨率不足。'
            result = self.run_renderer(payload, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            html = (root / 'output' / 'index.html').read_text()
            self.assertIn('"decision":"NO_STRUCTURAL_BOTTLENECK"', html)
            self.assertIn('"regions":[{"x":0.1', html)
            self.assertIn('"uncertainty":"原始分辨率不足。"', html)

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
