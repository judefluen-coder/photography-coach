# 摄影研究与历史规范

这里保存研究方法和规范的演变，不是另一个摄影教练产品。**当前使用标准始终在 [references/](../references/evaluation-standard.md)，当前技能入口是 [SKILL.md](../SKILL.md)。** 历史协议、失败记录和旧版本不能作为当前准确率或正式盲测通过的证明。

## 可公开归档

| 内容 | 入口 | 如何理解 |
|---|---|---|
| 评价标准 v0.2–v0.6 | [规范版本索引](archive/README.md#历史规范) | 当时的观察与评分设计；不是当前八维合同 |
| 早期反馈模拟 | [v0.1 反馈模拟](archive/standards/photography-feedback-simulation-v0.1.md) | 文字研究样品，原始图片不随此次整理公开 |
| 10 例公开共识试运行 | [协议](archive/2026-09/public-consensus-pilot-10/protocol.md) | 样本抽取、信息隔离与编码方法 |
| 30 例正式研究 | [协议](archive/2026-09/public-consensus-formal-30/protocol.md) | 当年的预注册约束，不能理解为今天已经通过 |
| v0.6 新保留集计划 | [协议](archive/2026-09/public-consensus-holdout-30-v0.6/protocol.md) | 针对冻结版本的研究计划 |
| 参考图 A/B 设计 | [协议](archive/2026-09/reference-ab-test-v0.1/protocol.md) · [评分规则](archive/2026-09/reference-ab-test-v0.1/scoring-rubric.md) | 研究设计不代表实际招募、实验完成或学习提升 |
| 反馈卡 v0.2 | [格式规范](archive/2026-09/ordinary-12-v0.2/feedback-card-spec-v0.2.md) | 已被现行输出合同替代，保留演变依据 |

归档保留旧内容和失败边界，只修正公开阅读所需的路径。涉及本机报告或未公开图片的链接改为指向本说明，不复制素材、不伪造在线入口。涉及历史哈希时，以本地保留的冻结原文为准，不能拿修正链接后的阅读版重新冒充原始冻结文件。

## 本地原始研究资料

维护者本地完整资料集中在项目的 `.local-data/`，**不进入 Git，不随 clone 或 Release 分发**：

| 目录 | 保存什么 |
|---|---|
| `.local-data/research/benchmark-202609/` | 原 `photography-benchmark` 全部原始研究、候选、映射、评论缓存、结果、脚本及第三方工具检出 |
| `.local-data/benchmark-runs/` | 原主仓库中的冻结答卷、审查与运行包 |
| `.local-data/benchmark-cache/` | 原主仓库中的评测图像物化缓存 |
| `.local-data/reports/` | 原 Codex visualizations 中的本项目历史页面、照片、调整图与截图 |
| `.local-data/tool-cache/` | 旧原型的工具缓存，共用依赖只保留一份实体 |
| `.local-data/migrations/20261019/` | 迁移前逐文件 SHA-256、验证结果、公开阅读版调整前的原文和清理记录 |

例如，历史报告仍在原始研究内的 `public-consensus-pilot-10/results/pilot-summary.md`、`public-consensus-formal-30/results/formal-summary.md`，协议修订在 `public-consensus-formal-30/amendment-log.md`。这些路径是本地资料索引，不是假装可以在线访问的链接。

`vendor/aestheval` 是第三方评测工具的独立检出，保留自己的远端和 Git 历史；它不是摄影教练的重复仓库，也不并入项目源码。未确认可再分发的照片、评论和身份映射继续留在本地。

旧路径可通过本机兼容链接继续读取，不再有第二份实体。新贡献者不需要这些私人材料即可运行公开工程检查；完整研究复现需要另行核对数据来源、权限和冻结版本。

版本含义与当前入口见[版本地图](../docs/versions.md)，迁移范围与核验结果见[整理记录](../docs/repository-organization.md)。
