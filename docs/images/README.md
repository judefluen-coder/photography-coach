# README 界面截图、历史示意图与署名

## 当前真实截图 · 2026-11-16

- `project-home-browser.jpg`：暗房风格的项目首页，工作台真实截图和两种使用入口。
- `workbench-browser.jpg`：独立本机工作台的免密钥公开案例；左侧完整照片、右侧建议与区间评分，已选择取景维度查看理由。
- `report-annotation-browser.jpg`：同一工作台，展开“人物的远近”点评；矩形和连线表示讨论位置，不是对照片像素的修改。
- `report-scores-browser.jpg`：选择“取景与边缘控制”，展开全部分数与理由的实际状态。

四张均为实际浏览器页面的 JPEG 截图，视口及输出图片均为 1600×1000。截图仅从 PNG 转为 JPEG，没有重新绘制界面、改写照片或拼接状态。工作台显示预先写好的演示点评，未使用真实 API。README 图片不能操作；独立工作台需启动本机服务，GitHub Pages 首页不在线评图。[本轮验收](../darkroom-verification-20261115.md)另列检查范围。

`layout-before-after.jpg` 为 2026-11-16 本轮实拍的并排对照：左旧布局、右修正后；每一侧都在 1280×720、同一张照片、完整取景和暗色状态下捕获，合成图 2560×720。仅将两张真实截图并排放置，没有重绘界面。两侧均使用下述 Fons 摄影，同按 CC BY-SA 4.0 提供。[布局修正记录](../layout-density-20261116.md)。

当前截图的照片来自 **Fons Heijnsbroek** 的[骑行街拍](https://commons.wikimedia.org/wiki/File:A_small_familie_is_biking_through_the_bicycle_tunnel,_in_the_city;_free_photo_Amsterdam_by_Fons_Heijnsbroek,_04-2022.jpg)，按 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)使用。照片未裁切、未调色、未生成式重画；本项目加入了界面、图表和点评标记。作者未背书本项目。截图（包括界面与文案）同按 CC BY-SA 4.0 提供；此许可不扩展到仓库代码。来源详见[街拍示例](../demo-street/README.md)。

下述历史截图和示意图使用另一张摄影作品，与当前四张截图分开署名。私人照片、黑白设计稿及其验收截图不随仓库分发。

## 保留的历史示意图

`report-compare-browser.jpg` 是保留的旧版浅色报告真实截图，1440×960，左侧仅调色、右侧原图；它不代表当前暗房界面。当前模板的滑动对照改为左原图、右调色。

本目录中的 `report-overview.png` 与 `report-color-comparison.png` 是按现有 `assets/visual-report-template.html` 和 2026-09-14 列车示例绘制的静态界面摘录。使用代码绘制文字、容器和按钮，并置入已存在的照片预览，不是浏览器截图，不是新的设计方案，也不构成交互测试证据。部分排版与文字为适应 README 作了简化。

图中的原图、仅调色和裁切＋调色来自已有示例文件，没有为制作 README 重新生成或修改照片里的物体。示意按钮不能在 GitHub README 中操作；项目仍是 Codex 技能和本地报告，不是在线评图服务。

## 摄影来源

- 作者：**Reinhold Möller（Ermell）**。
- 作品：**Behringersmühle Dampfeisenbahn-20220731-RM-111152.jpg**。
- [Wikimedia Commons 原图页](https://commons.wikimedia.org/wiki/File:Behringersm%C3%BChle_Dampfeisenbahn-20220731-RM-111152.jpg)。
- 摄影作品许可：[Creative Commons Attribution-ShareAlike 4.0 International（CC BY-SA 4.0）](https://creativecommons.org/licenses/by-sa/4.0/)，2026-09-14 重新核对。
- 原摄影师未背书本项目、点评或调整。

## 改动说明

原图使用先前准备的 JPEG 副本。已有仅调色版本保持取景不变，轻提车头现有暗部、降低外围亮绿叶的饱和度及亮度；已有裁切版本从该调色版本去掉上方 60 像素和右侧 120 像素，保留左、下边。制作示意时将对应预览按比例缩小显示，加入界面文字、控件图形、署名和“非浏览器截图”说明，没有生成式重画。

## 示意图许可

**上述两张 PNG（包括本项目加入的界面图形与文案）以 CC BY-SA 4.0 提供。** 使用时保留摄影师署名、原作品和许可证链接，说明调整及界面排版改动，并遵守相同方式共享要求。该许可仅适用于这两张示意图，不为仓库代码或其他材料指定许可证。

## 素材绑定

历史排版使用的既有 JPEG 预览 SHA-256 如下。公开原图副本和全尺寸调整文件现保存在 `docs/demo/assets/`；私人照片不随仓库提供。以下记录用于核对素材来源，不是浏览器验收或审美效果认证。

| 输入预览 | SHA-256 |
|---|---|
| source-preview.jpg | aca51c6ef5472a7fb3be070755e1e5400b23ef68429d44e1cb6e71281e62de19 |
| color-preview.jpg | eb6081184961c282dcb3fc562f242009bf604b65cb9cd558870816b455ca4ae2 |
| crop-color-preview.jpg | d88da3691ecfbae5a62cdfe8bdacceca98219d70582df058f88a080ced2f9a88 |
