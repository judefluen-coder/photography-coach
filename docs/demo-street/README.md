# 街拍示例：迎面来的骑车人

本地工作台的默认演示案例；无需 API，不会产生模型调用费用，也不写入私人点评记录。直接打开 `index.html` 可离线查看。

- 照片：Fons Heijnsbroek，2022-04-09，[Wikimedia 原作品页](https://commons.wikimedia.org/wiki/File:A_small_familie_is_biking_through_the_bicycle_tunnel,_in_the_city;_free_photo_Amsterdam_by_Fons_Heijnsbroek,_04-2022.jpg)。仓库使用其 1280×960 JPEG 预览，不是全尺寸相机原片。
- 许可：[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。保留署名、来源、许可与修改说明；作者未背书本项目。照片未裁切、未调色，页面的数字与区域框是可隐藏的讲解层。
- 点评：重新针对这张照片编写，未沿用列车示例的结论或评分。八项区间分、七项观察、六项图像检查；标注说明默认收起，点击照片上的标签或数字展开，再点收起。
- 参考作品：André Kertész 的 [Meudon（MoMA 单图页面）](https://www.moma.org/collection/works/57425)。仅链接，不分发馆藏图片。
- 图表设计：[Figma 可编辑设计稿](https://www.figma.com/design/L4jKAiN1l1lbQFaEHQlpBz?node-id=5-134)。评分主视图为 0 到 5 的双轮廓雷达图，点选维度查看理由；实线和虚线分别表示区间上、下限。未评分项留空，不当零分，图形面积不是总分。逐项区间条仍在明细中；照片标记不是眼动测量。
- 照片图解：人物与空间、线条与取景、明暗与冷暖。原图标记对照结构简图；解释放进各自标签的可收起说明中，不再重复放在图下。可隐藏图解或切回逐项点评；无法定位的整体观察保留文字。坐标来自这张照片的人工看片，色块与线条不是精确分割、实测色值或真实距离，不是修改后的照片。新点评合同支持同样的可选图解结构，不强制每张照片都套用这三项。
- 后期学习：明暗与颜色、裁切与取景分开显示。逐项点评的第 3 个标注可跳到后期建议；其中可展开“整张提亮 / 只提黑衣附近暗部”的方法比较，选择或直接跳过都能看完整解释，再返回原标注。不计对错、不保存学习分数，也不会调用模型；两个选项不是两张已生成的调整图片。

此案例没有调色成品，不伪造前后对照。需要体验已完成的局部调色、裁切和滑动对照，可打开 [列车案例](../demo/index.html)。

从 `report.json` 重建：

```bash
python3 scripts/render_visual_report.py --input docs/demo-street/report.json --output /tmp/photography-street-report
node scripts/test_visual_report_ui.mjs /tmp/photography-street-report/index.html
```

输出目录须为空或尚不存在。页面由共享模板生成，不要直接维护生成 HTML。来源核对日期：2026-11-09。
