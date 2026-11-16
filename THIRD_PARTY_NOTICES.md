# 授权范围与第三方素材

根目录的 [MIT 许可证](LICENSE)适用于本项目原创的软件代码及随附使用文档，包括 Skill、脚本、网页与报告模板、测试。它不将第三方摄影作品、其衍生图、包含照片的截图或外部参考作品重新授权为 MIT。研究数据中的外部作品信息也不因此获得再分发授权；使用时仍应核对各来源的权利与条件。

| 仓库文件 | 来源与适用许可 | 改动及边界 |
| --- | --- | --- |
| `docs/demo-street/assets/source.jpg` | Fons Heijnsbroek 的[骑行街拍](https://commons.wikimedia.org/wiki/File:A_small_familie_is_biking_through_the_bicycle_tunnel,_in_the_city;_free_photo_Amsterdam_by_Fons_Heijnsbroek,_04-2022.jpg)，[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Wikimedia 的 1280×960 JPEG 预览，未裁切或调色；可隐藏的点评标记由本项目添加。作者未背书；详见[街拍示例](docs/demo-street/README.md)。 |
| `docs/demo/assets/source.jpg`、`source-preview.jpg` | Reinhold Möller（Ermell）的[原摄影作品](https://commons.wikimedia.org/wiki/File:Behringersm%C3%BChle_Dampfeisenbahn-20220731-RM-111152.jpg)，[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | 同尺寸 JPEG 副本与缩小预览，不是项目原创照片。 |
| `docs/demo/assets/color.jpg`、`color-preview.jpg` | 同上，衍生图按 CC BY-SA 4.0 提供 | 保持取景，仅调整局部影调与色彩。 |
| `docs/demo/assets/treatment.jpg`、`treatment-preview.jpg` | 同上，衍生图按 CC BY-SA 4.0 提供 | 在调色基础上裁去上方及右侧少量画面。 |
| `docs/images/project-home-browser.jpg`、`workbench-browser.jpg`、`report-annotation-browser.jpg`、`report-scores-browser.jpg`、`layout-before-after.jpg` | 包含 Fons Heijnsbroek 的上述街拍；截图及截图对照按 CC BY-SA 4.0 提供 | 2026-11-16 实际运行截图及同视口旧／新版并排对照；加入界面与点评，照片未裁切或调色，详见[截图说明](docs/images/README.md)。 |
| `docs/images/report-compare-browser.jpg` | 包含 Reinhold Möller（Ermell）的上述摄影作品；整张截图按 CC BY-SA 4.0 提供 | 保留的旧版报告实际截图，不代表当前界面。 |
| `docs/images/report-overview.png`、`report-color-comparison.png` | 包含上述摄影作品；整张示意图按 CC BY-SA 4.0 提供 | 历史界面示意图，并非真实浏览器截图；详见[截图说明](docs/images/README.md)。 |

以上许可要求保留作者署名、原作品链接、许可链接，并说明修改；摄影师未背书本项目。原作品页另有作者对社交平台使用的提醒，向其他平台转载前应查看原页及目标平台条款，有疑问时联系作者。示例的详细处理过程见[公开报告说明](docs/demo/README.md)。`docs/social-preview.svg` 和 `.png` 是项目原创图形，不含上述照片，不应误标为摄影师作品。

`references/` 与 `research/` 中的外部作品名称、来源链接和评测元数据仅用于核验与研究。仓库没有把链接指向的第三方原图、馆藏图片或第三方工具代码一并授权；未获再分发许可的原始照片和研究缓存不应提交到仓库。

## 界面图标 · Phosphor Icons

工作台的 `image` 与报告的 `arrows-horizontal` 图标来自 [Phosphor Icons Core](https://github.com/phosphor-icons/core)，按其 [MIT 许可证](https://github.com/phosphor-icons/core/blob/main/LICENSE)使用。SVG 路径内置于页面，不请求第三方 CDN。以下版权与许可全文也保留在工作台及离线报告 HTML 中，随导出的报告一起分发：

```text
MIT License

Copyright (c) 2023 Phosphor Icons

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
