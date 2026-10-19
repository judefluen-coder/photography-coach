# 一起让摄影教练更会看片

最欢迎三种改进：指出具体错例、让视觉报告更好用、补充真正相关且可核验的摄影方法。

## 先从一个小问题开始

- **点评看错了**：贴原话，指出画面中可见的反证，以及照做会损失什么。不要求你是摄影专家。
- **参考图不相关**：给出具体作品页，说清两张图的机制为什么不能相互借鉴；同题材、相似色调并不足够。
- **界面不好用**：附页面版本、屏幕宽度和操作步骤。可以直接用仓库的列车示例复现，不必上传自己的照片。

请先搜索 [已有 Issues](https://github.com/judefluen-coder/photography-coach/issues)，再用[反馈表](https://github.com/judefluen-coder/photography-coach/issues/new/choose)提交。不要贴 API Key、私有文件路径或敏感照片。对无公开再分发许可的作品，只给官方作品页链接。

## 改代码前

代码许可证尚未选定；仓库可见不代表已授予修改或再分发许可。请先通过 Issue 与维护者确认代码贡献、复用及授权安排。本说明不另行授予许可，也不要求转让贡献者权利。

范围确认后，尽量一次只改一件事。修改入口：

| 要改什么 | 从这里开始 |
|---|---|
| 项目首页 | `docs/index.html`、`docs/site.css`、`docs/site.js` |
| 所有新报告的界面 | `assets/visual-report-template.html`，不要只手改生成的示例 |
| 报告字段或安全约束 | `scripts/render_visual_report.py`、`references/visual-report.md` |
| 点评与参考作品规则 | `SKILL.md` 及其直接引用的规范 |
| 质量评测 | `references/benchmark-method.md`，保留失败与冻结证据 |

## 最小验证

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/validate_knowledge.py
node scripts/test_visual_report_ui.mjs docs/demo/index.html
node scripts/test_project_home.mjs
```

报告模板有改动时，按[示例再生成说明](docs/demo/README.md)生成到仓库外，再更新公共 `docs/demo/index.html`。只使用已有公开样例；私人报告和照片必须保存在仓库外。

提交前实际打开桌面和手机宽度页面，检查照片未被意外裁切、版本按钮、滑动对照、完整图片下载、位置标记、键盘操作和复制失败路径。JS 的 DOM 测试不代替浏览器布局测试。

请在 PR 中说明：解决哪个问题、改了什么、怎么验证、截图来源及许可、还有什么没验证。不要把 CI 通过宣传为摄影水平提升；不要把参与过调参的照片继续标为独立盲测。
