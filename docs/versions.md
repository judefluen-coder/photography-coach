# 一个项目，三类版本

不要把不同对象的版本号混成同一种产品进度。

| 对象 | 版本与位置 | 含义 |
|---|---|---|
| 项目发行版 | [v0.1.0](https://github.com/judefluen-coder/photography-coach/releases/tag/v0.1.0) | 首次研究预览，保留原标签 |
| 项目发行版 | [v0.2.0-alpha.1](https://github.com/judefluen-coder/photography-coach/releases/tag/v0.2.0-alpha.1) | 视觉展示与实验底层模块快照；工作台未接通 |
| 项目发行版 | [v0.2.0-alpha.2](https://github.com/judefluen-coder/photography-coach/releases/tag/v0.2.0-alpha.2) | 同一仓库内整理历史原型与研究资料，隔离本地数据；不是新增自动评图能力 |
| 摄影规范 | [v0.2–v0.6 归档](../research/archive/README.md)及当前 `references/` | 规范演变，与项目发行号不同；当前使用以根 Skill 引用为准 |
| 历史界面 | [prototype-v0.1](archive/prototype-v0.1/RUN.md)、当前 [demo](demo/index.html) | 旧界面源码与现行静态报告示例，不是独立仓库或可用 AI 服务 |

开发只在这一主仓库继续：`SKILL.md` 是 Codex 使用入口，`app/` 是独立界面入口的建设位置，两者共用规则与必要的 `core/` 能力。正式可用程度和摄影质量证据分别报告。

GitHub 上没有发现需要合并或删除的同名／相似项目，只有当前仓库的 `main` 和上述阶段标签。保留已有 Release 和 Git 历史，不覆盖旧标签，不新建 `photography-coach-v2` 一类版本仓库。
