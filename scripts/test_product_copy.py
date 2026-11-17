"""Check agreed product wording, not subjective writing quality or model answers."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProductCopyTest(unittest.TestCase):
    def test_current_product_name_is_consistent(self):
        # Earlier screenshots/archives remain historical; current HTML uses the agreed name.
        for name in ('app/static/index.html', 'assets/visual-report-template.html',
                     'docs/index.html', 'docs/demo/index.html', 'docs/demo-street/index.html'):
            with self.subTest(file=name):
                html = (ROOT / name).read_text(encoding='utf-8')
                self.assertNotIn('见一张', html)
                self.assertIn('摄影教练', html)
                self.assertIn('Photography Coach', html)

    def test_removed_stock_phrases_stay_out_of_current_surfaces(self):
        # Historical documents and the style guide's before/after examples are excluded.
        paths = ('app/static/index.html', 'app/static/app.js', 'app/workbench.py',
                 'docs/index.html', 'docs/site.js', 'assets/visual-report-template.html',
                 'README.md', 'app/README.md', 'CONTRIBUTING.md')
        removed = ('这次，看看你拍的', '我们一起看', '第一张，从现在开始',
                   '这张，我们接着聊', '连接一次，就能开始', '把“为什么”',
                   '看懂这一张', '拍好下一张', '我已经直接帮你调了一版',
                   '不拿不相关的名作填空', '没有用原图副本冒充调色')
        for name in paths:
            content = (ROOT / name).read_text(encoding='utf-8')
            for phrase in removed:
                with self.subTest(file=name, phrase=phrase):
                    self.assertNotIn(phrase, content)

    def test_workspace_copy_names_actions_and_preserves_disclosures(self):
        html = (ROOT / 'app/static/index.html').read_text(encoding='utf-8')
        script = (ROOT / 'app/static/app.js').read_text(encoding='utf-8')
        for phrase in ('上传照片，获取点评', '还没有上传照片', '继续提问',
                       '发送问题', '配置 API 连接', '保存设置'):
            self.assertIn(phrase, html)
        # A wording cleanup must not remove the existing cost and data notices.
        for phrase in ('我确认将照片预览和补充文字发给所选模型，并承担该服务的 API 费用。',
                       '保存设置不会发起付费调用。', '关闭服务后需重新配置。',
                       '不是金额上限，也不包含输入 token。'):
            self.assertIn(phrase, html)
        self.assertIn('并承担该服务的 API 费用。', script)
        self.assertIn('预先写好的示例点评', script)
        self.assertIn('无需 API · 不产生费用', script)
        self.assertIn("showReport('/demo-street/index.html')", script)
        self.assertIn('暂不提供实时参考作品检索', script)

    def test_mobile_controls_are_not_removed_by_css(self):
        css = (ROOT / 'app/static/app.css').read_text(encoding='utf-8')
        for selector in ('#toggleHistory', '#showDemo'):
            self.assertNotRegex(css, rf'{selector}\s*\{{[^}}]*display:\s*none')
        self.assertIn('--header-height', css)

    def test_bundled_icon_license_survives_offline_export(self):
        for name in ('app/static/index.html', 'assets/visual-report-template.html'):
            html = (ROOT / name).read_text(encoding='utf-8')
            self.assertIn('Copyright (c) 2023 Phosphor Icons', html)
            self.assertIn('The above copyright notice and this permission notice', html)
            self.assertIn('SOFTWARE IS PROVIDED "AS IS"', html)


if __name__ == '__main__':
    unittest.main()
