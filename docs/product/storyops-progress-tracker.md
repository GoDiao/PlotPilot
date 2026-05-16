# StoryOps / 叙构 产品化进度跟踪

> 本文档用于跟踪 StoryOps 从 PlotPilot fork 分支演进为独立长篇小说创作控制台的阶段进度。每完成一个阶段，应同步更新状态、完成度、提交记录和下一步。

## Current Snapshot

- 当前分支：`codex/product-trustworthy-creation-loop`
- 当前产品名：**StoryOps / 叙构**
- 产品全称：**StoryOps · Long-form Fiction Console**
- 当前版本判断：**v0.3.0-beta candidate**
- 当前总体状态：核心能力已成型，品牌第一阶段已落地；仍需深层独立化、真实浏览器验收和真实写作回归。

## Overall Progress

| 模块 | 完成度 | 状态 | 说明 |
| --- | ---: | --- | --- |
| 可信创作闭环 | 75% | In Progress | 章节状态、质量门禁、重写快照、记忆提交、张力诊断和局部 Diff 已具备基础闭环。 |
| Prompt Governance | 80% | In Progress | 核心生成、蓝图、诊断、改稿、Knowledge、Bible、章后抽取、审稿链路已接入 contract / guard。 |
| UI 控制台化 | 60% | In Progress | 首页、工作台、Context Preview、张力改稿、重写提示已有控制台化改造；仍需浏览器逐项验收。 |
| StoryOps Rebrand | 45% | In Progress | 用户可见品牌第一阶段完成；深层技术命名、视觉资产、About/Attribution 仍待完成。 |
| 真实小说链路回归 | 20% | Pending | 尚未完整跑新小说初始化、蓝图、生成、全托管 3～5 章。 |
| 发布/安装包独立化 | 25% | Pending | Tauri 元数据已改一部分；sidecar、crate、identifier、安装迁移策略仍未定稿。 |

## Phase Roadmap

### Phase 1：可信创作闭环 Beta

- 状态：**Mostly Done**
- 完成度：**75%**
- 目标：把规划、生成、诊断、修订、确认、入库、续写打成可解释闭环。
- 已完成：
  - 章节质量门禁。
  - 章节状态与锁定逻辑。
  - `draft_memory / pending_memory / canonical_memory` 基础结构。
  - 重写本章的写前快照与软回退能力。
  - 张力诊断与修订草稿。
  - Context Preview 中展示 Authority Lock / Prompt Contract。
- 未完成：
  - 三层记忆在 UI 中还不够产品化。
  - 问题收件箱动作还可以继续完善。
  - 高风险章节自动停靠和回滚解释还不够完整。
- 相关提交：
  - `db43f30 feat: build trustworthy creation loop`
  - `f58e41f feat: expose prompt contract and guard memory commits`

### Phase 2：Prompt Governance

- 状态：**Mostly Done**
- 完成度：**80%**
- 目标：所有关键 LLM 调用都遵守统一身份、输出契约、证据规则和污染防护。
- 已完成：
  - 新增共享 `Prompt Contract`。
  - 章节生成移除机械规则：不再强制多人、三段对话、高冲突、悬念结尾。
  - 蓝图规划接入张力曲线原则。
  - 张力诊断改为“是否贴合计划张力”。
  - Diff 改稿改为保守局部修订。
  - Knowledge / Bible / 章后抽取 / 一致性审稿接入记忆防污染和证据规则。
  - 场记、章节状态抽取、宏观重构、摘要归档、主线建议等 prompt 已扫尾。
- 未完成：
  - LLM 控制台还不能完整展示“每次调用使用了哪套 contract”。
  - 少量历史 prompt metadata 仍保留 upstream source。
  - 真实模型输出质量还需跑文验证。
- 相关提交：
  - `77bd399 refactor: govern creation prompts with blueprint contracts`
  - `f58e41f feat: expose prompt contract and guard memory commits`
  - `6f1c1bc chore: finish prompt governance and console UI polish`

### Phase 3：UI 控制台化

- 状态：**In Progress**
- 完成度：**60%**
- 目标：让产品从“工具集合 UI”转为“长篇创作控制台”。
- 已完成：
  - 首页改为新建项目控制台。
  - 工作台托管区滚动/溢出保护增强。
  - Context Preview 展示 Authority Lock 与 Prompt Contract。
  - 张力诊断说明改为贴合蓝图目标张力。
  - Diff 改稿按钮和提示改为局部修订语义。
  - 重写本章确认弹窗展示副作用范围、快照恢复范围、后续章节风险。
- 未完成：
  - 尚未逐项浏览器点验所有交互。
  - 蓝图编辑体验仍需进一步打磨。
  - 问题收件箱与记忆三层 UI 仍需产品化。
- 相关提交：
  - `7034b63 refactor: reshape frontend console experience`
  - `6f1c1bc chore: finish prompt governance and console UI polish`

### Phase 4：StoryOps Rebrand 第一阶段

- 状态：**Done**
- 完成度：**45%（整体 rebrand） / 100%（第一阶段）**
- 目标：完成用户可见品牌从 `PlotPilot / 墨枢` 到 `StoryOps / 叙构` 的第一阶段迁移。
- 已完成：
  - 首页标题、副标题替换。
  - 启动页 title / boot logo 替换。
  - 侧边栏品牌替换。
  - “新建书目”改为“新建项目”。
  - `frontend/package.json` 改为 `storyops-console`。
  - API title / description 改为 `StoryOps API`。
  - Tauri product/title/description/publisher/copyright 改为 StoryOps。
  - 安装器、启动器、错误提示中的用户可见品牌改为 StoryOps。
  - README、可信创作闭环文档、Prompt Plaza 文档切到 StoryOps 叙事。
  - 保留 fork attribution 与 upstream license 说明。
- 未完成：
  - Rust crate 仍叫 `plotpilot` / `plotpilot_lib`。
  - Tauri identifier 仍是 `com.plotpilot.app`。
  - backend sidecar 仍叫 `plotpilot-backend.exe`。
  - localStorage key 仍带 `plotpilot`，需兼容迁移策略。
  - EPUB identifier 仍是 `plotpilot:{uid}`。
  - README 图片文件名仍带 `plotpilot-readme.256.png`。
  - StoryOps logo / favicon / About 页面尚未完成。
- 相关提交：
  - `903c29e docs: add StoryOps rebrand plan`
  - `f7d4445 rebrand: introduce StoryOps console identity`
  - `8130c3e fix: restore chapter review prompt indentation`

### Phase 5：产品独立化 / 深层命名迁移

- 状态：**Pending**
- 完成度：**0%**
- 目标：决定是否以及如何迁移深层技术命名，避免破坏升级路径。
- 待决策：
  - 是否将 Tauri identifier 从 `com.plotpilot.app` 改为 StoryOps 命名。
  - 是否重命名 Rust crate / lib。
  - 是否重命名 sidecar 和打包目录。
  - 是否迁移 localStorage key，并提供旧 key fallback。
  - 是否迁移 EPUB identifier。
- 验收标准：
  - 新安装使用 StoryOps 技术标识。
  - 旧安装/旧数据有迁移或兼容策略。
  - 打包链路不破坏。

### Phase 6：视觉资产与 About / Attribution

- 状态：**Pending**
- 完成度：**0%**
- 目标：让 StoryOps 不只是文字替换，而有正式视觉和来源说明。
- 待完成：
  - StoryOps logo。
  - favicon。
  - README 头图替换。
  - About / License / Upstream Attribution 面板。
  - 文档中的品牌视觉说明。
- 验收标准：
  - UI 与 README 不再依赖旧品牌图片。
  - 用户能在 About 页面看到版本、license 和 upstream attribution。

### Phase 7：真实浏览器 UI 验收

- 状态：**Pending**
- 完成度：**0%**
- 目标：逐项确认 StoryOps 控制台真实可用。
- 验收清单：
  - 首页新建项目控制台。
  - 蓝图生成、编辑、确认。
  - Context Preview 展示 Authority Lock / Prompt Contract。
  - 张力诊断 → 局部 Diff 改稿 → 采用草稿。
  - 重写本章预览 → reset。
  - 全托管 / 监管式自动驾驶切换。
  - 工作台无内容溢出或不可见区域。

### Phase 8：真实小说链路回归

- 状态：**Pending**
- 完成度：**0%**
- 目标：用真实模型完整跑 3～5 章，验证写作质量。
- 验收清单：
  - 新建小说初始化 Bible / Knowledge 成功。
  - 结构蓝图可指导章节生成。
  - 每章不明显短章或突然截断。
  - 主角/POV 不漂移。
  - 低张力章节不被错误诊断为失败。
  - 章后抽取不污染长期记忆。
  - 重写回退能恢复副作用。

### Phase 9：Beta 发布准备

- 状态：**Pending**
- 完成度：**0%**
- 目标：在真实验收通过后打 beta tag。
- 建议版本：`v0.3.0-beta`
- Release title：`StoryOps · Long-form Fiction Console Beta`
- 前置条件：
  - Phase 7 浏览器验收通过。
  - Phase 8 真实写作回归通过。
  - 已确认 license / attribution 合规。
  - 已决定深层技术命名是否延后到 v0.4。

## Update Log

| 日期 | 更新 | 提交 |
| --- | --- | --- |
| 2026-05-16 | 完成 StoryOps Rebrand 计划文档 | `903c29e` |
| 2026-05-16 | 完成 StoryOps 用户可见品牌第一阶段迁移 | `f7d4445` |
| 2026-05-16 | 修复 Rebrand 后审稿 prompt 缩进错误 | `8130c3e` |

## Maintenance Rule

每完成一个阶段或关键里程碑，必须更新：

1. `Overall Progress` 中的完成度与状态。
2. 对应 `Phase` 的已完成/未完成清单。
3. `Update Log` 的日期、说明和提交号。
4. 如有新增风险，补充到对应阶段说明中。

