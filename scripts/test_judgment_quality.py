"""Deterministic consistency rails; these tests do not certify photographic judgment."""

from __future__ import annotations

import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest

from render_visual_report import JudgmentError, ReportError, render_report, validate_report
from test_render_visual_report import PNG_1X1, report_payload


def coaching() -> dict:
    return {'action_type': '优先修正', 'observation_index': 0, 'exercise_observation_index': 0,
            'exercise_mode': '围绕重点', 'exercise_connection': '只改变同一处明暗竞争，不更换练习目标。',
            'success_criterion': '两张对照里，手与工具边界更容易分开，前后距离仍保留。'}


class JudgmentQualityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        source = self.root / 'source.png'
        source.write_bytes(PNG_1X1)
        self.report = report_payload(source)
        self.report['decision'] = 'STRUCTURAL_BOTTLENECK'
        self.report['coaching'] = coaching()
        for score in self.report['scores']:
            score.update(confidence='中', uncertainty='合成测试只检查字段，不是摄影评价证据。')

    def tearDown(self):
        self.temp.cleanup()

    def validate(self, report=None):
        return validate_report(copy.deepcopy(self.report if report is None else report), self.root)[0]

    def test_supported_quality_contract_preserves_original_intervals(self):
        validated = self.validate()
        self.assertEqual(validated['coaching'], self.report['coaching'])
        self.assertEqual([s['interval'] for s in validated['scores']], [s['interval'] for s in self.report['scores']])

    def test_explicit_no_rebuild_reconstruction_contradiction_is_rejected(self):
        for instruction in ('必须重构画面。', '必须重拍。', '必须大幅裁切。', '当前构图完全不成立。'):
            for legacy in (False, True):
                with self.subTest(instruction=instruction, legacy=legacy):
                    report = copy.deepcopy(self.report)
                    report['decision'] = 'NO_STRUCTURAL_BOTTLENECK'
                    report['summary'] = '无需调整，当前画面没有明显问题。'
                    report['priority']['title'] = instruction
                    if legacy:
                        del report['coaching']
                    else:
                        report['coaching']['action_type'] = '可选尝试'
                    with self.assertRaisesRegex(JudgmentError, '前后不一致'):
                        self.validate(report)

    def test_narrow_sentinel_does_not_claim_to_understand_every_sentence(self):
        report = copy.deepcopy(self.report)
        report['decision'] = 'NO_STRUCTURAL_BOTTLENECK'
        report['coaching']['action_type'] = '可选尝试'
        for text in ('不必重构，只是可选尝试。', '不是必须重拍，先保住人物间隔。', '如果想改为另一个主题，需要重新考虑取景。'):
            with self.subTest(text=text):
                report['priority']['title'] = text
                self.validate(report)

    def test_absolute_no_fault_summary_conflicts_with_a_structural_verdict(self):
        for summary in ('完全没有问题。', '这张照片无需任何调整。', '所有方面均无明显问题。'):
            with self.subTest(summary=summary):
                self.report['summary'] = summary
                with self.assertRaisesRegex(JudgmentError, '总结声称'):
                    self.validate()
        self.report['summary'] = '脸部没有任何问题，右侧亮面仍然遮住手的轮廓。'
        self.validate()

    def test_decision_and_action_nature_must_agree(self):
        for decision, action in (('STRUCTURAL_BOTTLENECK', '保留'), ('CONDITIONAL_BRANCH', '优先修正'),
                                 ('NO_STRUCTURAL_BOTTLENECK', '优先修正')):
            with self.subTest(decision=decision, action=action):
                report = copy.deepcopy(self.report)
                report['decision'] = decision
                report['coaching']['action_type'] = action
                with self.assertRaisesRegex(JudgmentError, '总体判断'):
                    self.validate(report)

    def test_links_are_real_integer_observation_indices(self):
        for key in ('observation_index', 'exercise_observation_index'):
            for value in (True, 0.5, -1, 6, '0'):
                with self.subTest(key=key, value=value):
                    report = copy.deepcopy(self.report)
                    report['coaching'][key] = value
                    with self.assertRaises(JudgmentError):
                        self.validate(report)

    def test_practice_cannot_silently_switch_to_another_observation(self):
        self.report['coaching']['exercise_observation_index'] = 3
        with self.assertRaisesRegex(JudgmentError, '没有对齐'):
            self.validate()

    def test_explicit_consolidation_can_target_a_protected_strength(self):
        self.report['coaching'].update(exercise_mode='巩固优点', exercise_observation_index=3,
                                      exercise_connection='当前修正会损失前后距离，先练保住这层关系。')
        self.validate()
        self.report['coaching']['exercise_observation_index'] = 1
        with self.assertRaisesRegex(JudgmentError, '已经成立'):
            self.validate()

    def test_connection_and_visible_success_criterion_are_required(self):
        for key in ('exercise_connection', 'success_criterion'):
            report = copy.deepcopy(self.report)
            report['coaching'][key] = ' '
            with self.subTest(key=key), self.assertRaisesRegex(JudgmentError, '检查标准'):
                self.validate(report)

    def test_uncertain_scores_name_the_actual_missing_evidence(self):
        for confidence in ('中', '低'):
            self.report['scores'][0].update(confidence=confidence, uncertainty=None)
            with self.subTest(confidence=confidence), self.assertRaisesRegex(JudgmentError, '缺少什么'):
                self.validate()
        self.report['scores'][0].update(confidence='高', uncertainty=None)
        self.validate()
        self.report['scores'][0]['confidence'] = '99%'
        with self.assertRaises(ReportError):
            self.validate()

    def test_unresolved_integrity_is_not_changed_to_a_pass(self):
        families = ['边缘/裁切', '暗部', '高光', '色彩', '轴线/透视', '细节']
        self.report['integrity'] = [{'family': f, 'verdict': '无法判断', 'basis': '没有足够像素或可靠参照。'} for f in families]
        self.assertTrue(all(row['verdict'] == '无法判断' for row in self.validate()['integrity']))

    def test_legacy_report_has_no_invented_confidence_or_linkage(self):
        legacy = report_payload(self.root / 'source.png')
        validated = self.validate(legacy)
        self.assertNotIn('coaching', validated)
        self.assertTrue(all('confidence' not in score for score in validated['scores']))

    def test_summary_is_not_hidden_inside_a_disclosure(self):
        input_path = self.root / 'report.json'
        input_path.write_text(json.dumps(self.report), encoding='utf-8')
        output = render_report(input_path, self.root / 'page')
        html = output.read_text(encoding='utf-8')

        class SummaryParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.details_depth = 0
                self.summary_depth = None

            def handle_starttag(self, tag, attrs):
                if tag == 'details':
                    self.details_depth += 1
                if dict(attrs).get('id') == 'summary':
                    self.summary_depth = self.details_depth

            def handle_endtag(self, tag):
                if tag == 'details':
                    self.details_depth -= 1

        parser = SummaryParser()
        parser.feed(html)
        self.assertEqual(parser.summary_depth, 0)
        self.assertLess(html.index('id="summary"'), html.index('id="priorityTitle"'))


if __name__ == '__main__':
    unittest.main()
