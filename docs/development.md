# 开发与验证

[返回项目首页](../README.md)

本指南面向需要运行脚本、修改规则或检查报告的贡献者。普通使用者直接在 Codex 中附图并调用技能，不需要手工编写报告 JSON。

## 环境

以下命令在仓库目录执行。Python 用于脚本；Pillow 用于图像探针和评测图像物化；Node.js 用于报告内联 JavaScript 的测试。纯报告渲染和知识结构校验使用 Python 标准库。

```bash
cd ~/.codex/skills/photography-coach
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r app/requirements.txt
node --version
```

Node.js 需另行安装。缺少它时部分测试会跳过，不能把跳过当成通过。虚拟环境只用于开发，不需提交到 Git。

`app/` 尚无可运行服务或界面。`core/` 的规则装配、传输和图像处理只是实验基础模块，状态与缺口见[工作台开发说明](../app/README.md)；安装依赖不会启动评图服务。

## 检查图像信号

```bash
python3 scripts/analyze_image_integrity.py /absolute/path/to/photo.jpg --json
```

探针只提示需要复核的明暗、颜色、细节、轴线和边缘信号，不会自动决定缺陷、优先级或审美分数。必须回到实际图像核对。

## 生成本地报告

1. 先完成实际看片、点评、参考核验和获授权的图像编辑。
2. 按[视觉报告合同](../references/visual-report.md)准备完整 JSON。合同中的 JSON 仅是字段示意，不能直接作为有效输入；实际需要全部八维评分和 6–9 条观察。
3. 将 JSON、照片与输出目录放在技能仓库外。

```bash
python3 scripts/render_visual_report.py \
  --input /absolute/path/to/report.json \
  --output /absolute/path/outside-repository/report-page
```

输出为 `index.html` 和 `assets/`。打开 HTML 查看；移动或分享时保留整个文件夹。输出目录非空时默认拒绝覆盖，只有明确需要替换报告文件时才使用 `--force`。

`source_image` 是原图，`color_image` 是保留取景的仅调色版，`treatment_image` 是综合调整版；后两项可省略。可选的 `*_preview_image` 用于较小的展示副本，下载仍指向完整文件。不要手工填写生成器管理的 `*_asset` 或 `*_download`。

渲染器不调用模型、不编辑像素，也不验证照片之间的内容保真、参考相关性或实际裁切是否匹配文字。输出前应逐图核对，再检查桌面与窄屏布局、版本切换、定位、裁切框、下载和复制练习。

## 运行验证

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/validate_knowledge.py
```

截至 2026-10-19，本地 171 项 Python 测试及知识结构校验通过。新底层模块的测试使用模拟传输和合成小图，不连接真实模型，不产生 API 费用，不验证实际摄影点评质量。单独检查自己生成的页面：

```bash
node scripts/test_visual_report_ui.mjs /absolute/path/to/report-page/index.html
node scripts/test_project_home.mjs
```

第一组在 DOM 测试替身中运行报告的真实内联 JavaScript，覆盖四种图像组合、默认版本、滑动对照、下载链接、区域/裁切标记及复制失败路径；第二组检查首页三版本、复制后备、主题切换及本地链接。它们不是真实浏览器验收，不验证下载完成、响应式布局或摄影判断。

项目首页位于 `docs/index.html`，直接打开即可；若需本地 HTTP 预览，在仓库根目录运行 `python3 -m http.server 8769 --bind 127.0.0.1 --directory docs`，再打开 `http://127.0.0.1:8769/`。不用构建或安装前端依赖，预览结束后按 Ctrl-C 停止服务器。

GitHub Actions 在推送和拉取请求时运行上述单元测试与知识结构校验，并重新生成 [公开报告示例](demo/README.md)，核对生成的 HTML 与仓库版本一致，再执行报告与首页的 JavaScript 状态测试。示例的二进制图片文件与报告输入均保存在 `docs/demo/`，不需要私有照片。

一项 v5 冻结快照测试依赖未公开的 `.benchmark-runs/` 文件；公开 CI 会明确跳过它，本地存在这两份文件时仍会核对哈希与条目数。跳过不算摄影发布验收通过。

正式发布另有质量门槛：

```bash
python3 scripts/validate_knowledge.py --release
```

**当前预期失败。** 历史发布证据已失效，12 张前向查错不满足完整发布要求。不要为获得绿灯降低阈值或将旧样本重评冒充新盲测。详见[评测方法](../references/benchmark-method.md)与[阶段复核记录](../references/gpt6-final-review-20260914.md)。

## 资料入口

| 文件 | 用途 |
|---|---|
| [SKILL.md](../SKILL.md) | 技能入口、必读资料与工作流 |
| [evaluation-standard.md](../references/evaluation-standard.md) | 观察维度、优先级与评分规则 |
| [response-card.md](../references/response-card.md) | 对话与审计输出格式 |
| [source-registry.jsonl](../references/source-registry.jsonl) | 课程、摄影师、机构等来源登记 |
| [masterwork-cards.jsonl](../references/masterwork-cards.jsonl) | 精确单图教学卡，不是推荐上限 |
| [critique-patterns.jsonl](../references/critique-patterns.jsonl) | 点评模式、反例、动作与练习 |
| [calibration-review-20260914.json](../references/calibration-review-20260914.json) | 24 张答案可见开发校准 |
| [forward-review-20260914.json](../references/forward-review-20260914.json) | 12 张冻结答卷的逐字段审查 |

完整图片与本地运行包不随仓库分发。仓库保留部分历史答卷和审查证据，本轮记录中的本机路径不是可公开访问的文件地址。请勿提交用户照片、调整图、私人报告、凭据或虚拟环境。
