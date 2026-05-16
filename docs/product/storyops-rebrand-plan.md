# StoryOps / 叙构 全方位 Rebrand 任务计划

## Summary

当前分支已经从原始 PlotPilot 功能集合演进为“长篇小说 AI 创作控制台”：有章节蓝图、Authority Lock、Prompt Contract、质量门禁、张力诊断、局部 Diff 改稿、记忆防污染和重写快照。产品定位已经不适合继续使用 `PlotPilot / 墨枢`。

新的品牌命名：

- 中文名：**叙构**
- 英文名：**StoryOps**
- 全称：**StoryOps · Long-form Fiction Console**

Rebrand 目标不是简单替换名称，而是让产品、UI、文档、API 描述、操作语言和项目叙事统一到“长篇小说创作控制台 / 可信创作闭环”的方向。

## Positioning

### 产品定位

StoryOps 是一个面向长篇小说的 AI 总编控制台，帮助作者完成：

- 从 premise 到 Bible / Knowledge 的设定建档。
- 从幕级蓝图到章级蓝图的结构规划。
- 以 Authority Lock 和 Prompt Contract 约束章节生成。
- 通过质量门禁、张力诊断、一致性审稿判断章节是否可信。
- 用局部 Diff 改稿和重写快照修复问题。
- 在用户确认后把章节状态提交到长期记忆。
- 在全托管或监管式自动驾驶中持续推进长篇创作。

### 产品一句话

> StoryOps / 叙构，是一个面向长篇小说的 AI 创作控制台，用蓝图、上下文锁、质量门禁和可回退记忆，帮助作者稳定推进百万字级故事。

### 不再使用的定位

- 不再称为 “PlotPilot”。
- 不再称为 “墨枢”。
- 不再表达为“AI 小说生成工具集合”。
- 不再用营销式大标题包装成 landing page。
- 不再强调“全自动写完”，而强调“可监管、可追踪、可回退的创作流程”。

## Brand Rules

### 命名规范

- 首次出现：`StoryOps · Long-form Fiction Console（叙构）`
- 中文界面主名：`叙构`
- 英文/工程展示名：`StoryOps`
- 长描述：`Long-form Fiction Console`
- 页面 title 推荐：`StoryOps · 叙构`
- 控制台顶部推荐：`StoryOps Console`

### 术语系统

| 旧表达 | 新表达 |
| --- | --- |
| PlotPilot | StoryOps |
| 墨枢 | 叙构 |
| 新建书目 | 新建项目 / 新建长篇项目 |
| AI 生成 | 生成章节草稿 |
| 全托管 | 全托管驾驶 |
| 自动生成 | 执行写作任务 |
| 一致性检查 | 质量门禁 / 审稿任务 |
| 上下文预览 | Context Package / 上下文包 |
| Bible | Bible / 设定档案 |
| 知识图谱 | Knowledge Graph / 叙事图谱 |
| 重写本章 | 重写回退 / Reset for Rewrite |

### 语气原则

- 像控制台，不像宣传页。
- 像总编工作台，不像聊天机器人。
- 强调状态、依据、风险、下一步动作。
- 减少“神奇、一键、自动完成”等不可信词汇。
- 允许中英混合，但核心动作要中文清楚。

## Scope

### P0：用户可见品牌替换

替换所有用户直接可见的 `PlotPilot / 墨枢`：

- 首页标题、副标题、footer。
- 顶栏、侧边栏、工作台标题。
- 浏览器 title。
- favicon / logo alt 文案。
- 空状态、错误页、加载页。
- 设置弹窗、LLM 控制台、提示词广场、统计面板。
- README 首屏标题和项目简介。
- docs/product 中的产品名。
- OpenAPI title / description。

验收标准：启动前端后，普通用户路径中不再看到 `PlotPilot / 墨枢` 品牌文案。

### P0：控制台语言统一

统一产品模块命名：

- 首页：`新建项目控制台`。
- 工作台：`章节控制台` / `Writing Console`。
- 蓝图：`结构蓝图` / `Chapter Blueprint`。
- 上下文：`Context Package` / `上下文包`。
- 生成前检查：`Preflight` / `生成前预检`。
- 质量检查：`Quality Gate` / `质量门禁`。
- 张力诊断：`Tension Review` / `张力审稿`。
- 改稿：`Local Diff Revision` / `局部 Diff 改稿`。
- 入库：`Memory Commit` / `记忆提交`。
- 重写：`Rewrite Reset` / `重写回退`。
- 自动驾驶：`Autopilot` / `自动驾驶`，包含 `全托管驾驶` 与 `监管式驾驶`。

验收标准：同一个功能在不同页面不再出现多个互相冲突的叫法。

### P0：Legal / Attribution 保留

Rebrand 不等于抹除来源。需要检查原仓库 license，并保留必要开源信息：

- 保留 `LICENSE`。
- 如原项目有 `NOTICE`、版权声明或 README attribution，按 license 要求保留。
- README 可加入：`StoryOps is developed from a fork of PlotPilot ...`，具体措辞视 license 决定。
- UI footer 不展示原项目身份；开源来源放在 README / About / License 页。

验收标准：用户界面完成新品牌，但仓库层面的 license/attribution 合规。

### P1：工程元数据替换

替换工程显示名，但不做高风险包名重构：

- `frontend/package.json` 的 `name` 可改为 `storyops-console`。
- Vite / app title 改为 `StoryOps · 叙构`。
- README 标题改为 `StoryOps · Long-form Fiction Console`。
- API docs title 改为 `StoryOps API`。
- Docker / deploy 文档中的展示名改为 StoryOps。

暂不改：

- 仓库目录名 `PlotPilot`。
- Python 包路径。
- 数据库表名。
- 已存在 migration 名称。
- 历史 branch 名称。

验收标准：构建、启动、测试不因路径重命名产生风险。

### P1：视觉品牌整理

StoryOps 的视觉应继续走“控制台”方向：

- 默认白/石色画布 + 深色控制台区块。
- 避免大营销 hero。
- 首页更像项目 registry + run config。
- 工作台优先显示当前状态、风险和下一步。
- 主要 CTA 使用清晰动词：`创建项目`、`生成蓝图`、`运行预检`、`提交记忆`。

建议新增轻量品牌资产：

- 文本 logo：`StoryOps` / `叙构`。
- favicon：可用 `SO` 或抽象结构节点符号。
- About 面板：说明版本、fork 来源、license。

验收标准：用户进入页面后感知为“创作控制台”，不是“旧项目换名”。

### P1：数据与兼容提示

旧数据可能仍包含 `PlotPilot / 墨枢` 字符串，不做强制迁移：

- 旧小说标题、用户正文、历史摘要不替换。
- 系统配置中的旧品牌字段只在显示层 fallback。
- 新建项目默认使用 StoryOps 文案。
- 如需要，后续提供一次性“品牌文案迁移脚本”，但默认不执行。

验收标准：旧数据不被误改，新项目不再产生旧品牌文案。

## Implementation Plan

### Phase 1：Inventory

全仓库搜索以下关键词：

- `PlotPilot`
- `plotpilot`
- `墨枢`
- `由 PlotPilot`
- `AI 小说生成`
- `新建书目`

分类结果：

- 用户可见 UI 文案。
- 工程元数据。
- 文档文案。
- License / attribution。
- 历史数据或测试样例。
- 不应改动的技术路径。

### Phase 2：UI Rebrand

优先替换用户可见路径：

- `frontend/src/views/Home.vue`
- `frontend/src/views/Workbench.vue`
- `frontend/src/App.vue`
- `frontend/src/components/**`
- `frontend/index.html` 或 Vite title 来源。
- favicon / logo 资源。

同时统一首页为“项目控制台”结构：

- Project Registry。
- New Project Console。
- Run Config。
- Recent Projects。

### Phase 3：Docs / Metadata

更新：

- `README.md`
- `docs/product/*.md`
- API docs title / description。
- `frontend/package.json`
- 部署文档中的展示名。

保留：

- License。
- fork attribution。

### Phase 4：Prompt / Runtime Naming

检查 prompt 中是否仍有旧品牌身份：

- 不需要把所有 prompt 都塞入 StoryOps，但系统身份应统一为“长篇小说控制台”。
- 不允许 prompt 自称 PlotPilot / 墨枢。
- LLM 控制台 stats 可显示：`StoryOps Prompt Contract`。

### Phase 5：Validation

执行：

- `rg "PlotPilot|plotpilot|墨枢"`，确认剩余命中都属于 license、attribution、历史说明或不可改技术路径。
- `npm run build`。
- 相关后端测试。
- 浏览器检查首页、工作台、设置、Context Preview、重写弹窗、张力诊断弹窗。

## Acceptance Criteria

- 首页、工作台、设置、弹窗、footer 中不再出现 `PlotPilot / 墨枢`。
- 产品主名统一为 `StoryOps / 叙构`。
- 页面 title 显示 `StoryOps · 叙构`。
- README 和产品文档说明新定位。
- License / attribution 合规保留。
- 新建项目和工作台文案明显是控制台风格。
- `npm run build` 通过。
- 后端目标测试通过。
- 搜索旧品牌时，剩余命中都有明确保留原因。

## Risks

- 直接改包名、目录名或数据库名风险较高，第一版不做。
- 旧数据里的品牌字符串不应批量替换，否则可能误改用户正文。
- License 要求不明确时，不能删除原始 attribution。
- UI rebrand 如果只换名字不改信息架构，会继续被感知为旧产品换皮。

## Recommended Versioning

Rebrand 完成后建议打一个 beta 版本：

- Version：`v0.3.0-beta`
- Codename：`StoryOps Rebrand Beta`
- Release title：`StoryOps · Long-form Fiction Console Beta`

版本说明建议包含：

- 品牌升级为 StoryOps / 叙构。
- 产品定位升级为长篇小说 AI 创作控制台。
- 保留开源来源与 license。
- 可信创作闭环、Prompt Contract、Memory Guard 已作为核心能力。

