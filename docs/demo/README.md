# 可打开的完整报告示例

[打开报告](index.html) · [项目首页](../../README.md)

这是一个已生成的静态报告，不接收上传，也不在浏览器里调用模型。页面可以切换原图、仅调色和裁切＋调色；下载按钮指向本目录的原尺寸示例文件，不是缩小的展示预览。`report.json` 是生成这份报告的输入，`assets/` 是页面运行所需的全部图片。把整个 `demo/` 目录保存在一起，即可离线打开 `index.html`。

示例源图：Reinhold Möller（Ermell），[Wikimedia Commons 原文件](https://commons.wikimedia.org/wiki/File:Behringersm%C3%BChle_Dampfeisenbahn-20220731-RM-111152.jpg)，[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。本目录的 `source.jpg` 是同尺寸 JPEG 副本，不冒充相机原始文件。仅调色与裁切＋调色版基于该图调整，衍生图片同以 CC BY-SA 4.0 提供。作者未背书此项目、点评或调整。公开包将原尺寸调整版由 PNG 转为质量 94 的 JPEG 以便浏览；两者保留原像素尺寸，压缩有损。页面的小图另由原处理版本生成。

页面文字、评分和改图是一个实验示例，不是专家认证或新的独立盲测。参考作品链接指向美国国家美术馆的单图页面，示例没有复制该馆的图片。

重新生成页面：

```bash
python3 scripts/render_visual_report.py \
  --input docs/demo/report.json \
  --output /absolute/path/outside-repository/demo-rendered
```

请在仓库根目录运行；输出目标需不存在或为空。渲染器只打包已经写好的点评和实际图片，不会自动评价或调色。
