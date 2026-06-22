
# Agent 长期开发协作规则

## 0. 文档目的

本文档用于解决长期使用 AI Agent 开发项目时产生的上下文断层问题。

本项目的规划、架构原则、任务边界、阶段目标、开发约束，不能只存在于网页对话中，而必须沉淀到项目仓库里。

核心原则：

> 不要让网页聊天记录承担项目记忆。
> 真正的项目记忆必须放进仓库文档中，并让 Agent 每次从仓库文档恢复上下文。

---

# 1. 核心问题：长期 Agent 开发中的 Gap

在长期开发中，常见 Gap 包括：

```text
ChatGPT 规划      →  Agent 执行
设计文档          →  真实代码
长期目标          →  当前任务
架构原则          →  具体文件修改
上一轮开发结果     →  下一轮继续开发
```

这些 Gap 的根本原因是：

```text
Agent 通常只能看到当前提示词、当前仓库文件、当前终端结果和有限上下文。
它不会天然记住之前在网页对话中形成的所有规划和决策。
```

因此，不能依赖 Agent 自己“记住项目”，而要让 Agent 每次通过仓库文档恢复项目上下文。

---

# 2. 总体协作原则

长期 Agent 开发遵循以下原则：

```text
聊天负责决策
文档负责固化
任务卡负责执行
测试负责验收
Git 负责回滚
ADR 负责记录重大决策
```

也可以理解为：

```text
ChatGPT 对话 = 设计讨论会
AGENTS.md = 施工规范
ROADMAP.md = 总工期计划
TASK 文件 = 每日施工单
PROJECT_STATE.md = 当前施工进度
tests = 验收标准
git commit = 阶段归档
ADR = 重大变更记录
```

不要把“设计讨论会”直接当成“施工图”。

每次讨论后的结论，都应该沉淀为仓库中的文档、任务卡或 ADR。

---

# 3. 仓库中的项目控制文档

建议在项目根目录建立以下文件：

```text
content-review-engine/
  AGENTS.md
  PROJECT_STATE.md
  ROADMAP.md
  CHANGELOG.md

  docs/
    ARCHITECTURE.md
    DATA_MODELS.md
    REVIEW_RULES.md
    CLI_CONTRACT.md
    MCP_CONTRACT.md
    API_CONTRACT.md

  decisions/
    ADR-0001-core-package-first.md
    ADR-0002-cli-before-mcp.md
    ADR-0003-review-result-schema.md

  tasks/
    TASK-0001-project-skeleton.md
    TASK-0002-basic-review-rules.md
    TASK-0003-cli-review-command.md
```

---

# 4. 四个最重要的控制文件

## 4.1 `AGENTS.md`

`AGENTS.md` 是写给开发 Agent 的总说明书。

它负责告诉 Agent：

```text
这个项目是什么
哪些文件是核心
哪些原则不能破坏
每次开发前要读什么
每次开发后要更新什么
什么事情不能擅自做
```

建议内容：

```markdown
# AGENTS.md

## Project

This project is a Python package-first content review engine.

The core goal is to review Markdown content and return structured review results.

## Architecture Rules

1. Core business logic must stay in `src/content_review_engine/`.
2. CLI, Skill, MCP, and API are adapters around the core package.
3. Do not duplicate review logic in CLI, MCP, Skill, or API layers.
4. Review output must use Pydantic models defined in `core/models.py`.
5. Any change to ReviewResult or ReviewIssue requires updating `docs/DATA_MODELS.md`.
6. Any new review rule must have a stable rule_id and be documented in `docs/REVIEW_RULES.md`.
7. Any major architecture change requires a new ADR in `decisions/`.

## Before Coding

Read these files first:

- PROJECT_STATE.md
- ROADMAP.md
- docs/ARCHITECTURE.md
- docs/DATA_MODELS.md
- the current task file in `tasks/`

## After Coding

Update these files when relevant:

- PROJECT_STATE.md
- CHANGELOG.md
- related docs
- related tests

## Do Not

- Do not introduce MCP before the CLI contract is stable.
- Do not put API/database logic into the core package.
- Do not change public data models without documenting the reason.
- Do not create large abstractions before there are at least two real use cases.
```

---

## 4.2 `PROJECT_STATE.md`

`PROJECT_STATE.md` 是当前项目状态说明。

它不是长期规划，而是告诉下一轮 Agent：

```text
现在已经完成了什么
当前卡在哪里
下一步是什么
哪些设计已经确定
哪些设计还没确定
哪些内容暂时不能改
```

建议内容：

```markdown
# PROJECT_STATE.md

## Current Phase

M0: Project skeleton and deterministic review rules.

## Completed

- Project uses Python package-first architecture.
- Core package is placed under `src/content_review_engine/`.
- ReviewIssue, ReviewResult, ReviewProfile are the current core data models.
- The first target platform is WeChat official account Markdown review.

## In Progress

- Build a minimum CLI command:
  `content-review review examples/article.md --profile wechat`

## Next Tasks

1. Add Markdown reader.
2. Add basic WeChat title length rule.
3. Add basic paragraph length rule.
4. Add JSON output for CLI.
5. Add regression tests.

## Open Questions

- Whether rewritten Markdown should be generated in v0.1.0 or postponed to v0.2.0.
- Whether AI review should be added before or after deterministic rules are stable.

## Do Not Change Yet

- Do not add MCP server yet.
- Do not add FastAPI yet.
- Do not add Supabase yet.
```

每次 Agent 完成一轮开发后，都必须更新这个文件。

---

## 4.3 `ROADMAP.md`

`ROADMAP.md` 是长期路线图。

它的作用是防止 Agent 在当前阶段做太多超前工作。

建议内容：

```markdown
# ROADMAP.md

## v0.1.0 Core Package MVP

Goal:

- Read Markdown
- Load review profile
- Run deterministic rules
- Return ReviewResult
- Provide basic CLI output

Not included:

- PydanticAI
- MCP
- Skill
- API
- Database
- Frontend

## v0.2.0 CLI Stable

Goal:

- Stable CLI command design
- JSON output
- Markdown report output
- Local config support

## v0.3.0 AI Review Adapter

Goal:

- Add PydanticAI reviewer
- Add structured AI output
- Add prompt versioning
- Add LLM mock tests

## v0.4.0 Skill

Goal:

- Add Skill document
- Explain how Agent should call CLI
- Add usage examples

## v0.5.0 MCP

Goal:

- Expose review_markdown tool
- Expose rewrite_markdown tool
- Expose list_profiles tool

## v0.6.0 API

Goal:

- Add FastAPI backend prototype
- Add document review endpoint
- Add review job records
```

---

## 4.4 `tasks/TASK-xxxx.md`

每一轮 Agent 开发都必须有一个任务卡。

不要直接让 Agent “继续开发项目”。

正确方式是：

```text
给 Agent 一个明确的 TASK 文件。
让 Agent 只完成当前 TASK。
任务完成后更新 PROJECT_STATE.md 和 CHANGELOG.md。
```

任务卡模板：

```markdown
# TASK-0002: Add Basic WeChat Review Rules

## Goal

Add two deterministic review rules for WeChat Markdown content.

## Background

The project uses a Python package-first design. Review rules should live under:

`src/content_review_engine/rules/`

All rule outputs must use `ReviewIssue`.

## Scope

Implement:

1. WECHAT_TITLE_001
   - Detect first-level Markdown title longer than profile.max_title_length.

2. WECHAT_PARAGRAPH_001
   - Detect paragraph longer than profile.max_paragraph_length.

## Files To Modify

- src/content_review_engine/rules/base.py
- src/content_review_engine/rules/wechat.py
- docs/REVIEW_RULES.md
- tests/test_rules.py

## Do Not Modify

- MCP files
- API files
- database files
- project packaging unless necessary

## Acceptance Criteria

- Each rule has a stable rule_id.
- Each rule returns a list of ReviewIssue.
- Tests pass with `uv run pytest`.
- docs/REVIEW_RULES.md documents both rules.
- No CLI behavior is changed in this task.
```

---

# 5. 标准开发流程

每一轮开发都应该遵循以下流程：

```text
1. 在 ChatGPT 中讨论设计和任务边界
2. 将结论写入 ROADMAP / ARCHITECTURE / TASK
3. 让 Agent 读取 AGENTS.md + PROJECT_STATE.md + 当前 TASK
4. Agent 只完成当前 TASK
5. Agent 运行测试
6. Agent 更新 PROJECT_STATE.md / CHANGELOG.md / docs
7. 人工检查 git diff
8. 通过后提交 commit
9. 进入下一张 TASK
```

核心规则：

```text
没有 TASK，不让 Agent 开发。
没有验收标准，不让 Agent 开发。
没有更新 PROJECT_STATE，不算完成。
没有测试，不算完成。
架构变化没有 ADR，不准合并。
```

---

# 6. 每次给 Agent 的启动提示词

以后每轮开发可以使用下面这个固定提示词。

## 中文版

```text
你现在在这个仓库中开发。

编码前请先阅读：

1. AGENTS.md
2. PROJECT_STATE.md
3. ROADMAP.md
4. docs/ARCHITECTURE.md
5. 当前任务文件：tasks/TASK-xxxx.md

然后只实现当前任务。

不要添加当前任务之外的功能。
不要添加 MCP、API、数据库或前端代码，除非当前任务明确要求。
不要修改核心数据模型，除非当前任务明确要求。
如果任务要求和 AGENTS.md 冲突，请先停止并说明冲突点。

完成后：

1. 运行测试
2. 更新 PROJECT_STATE.md
3. 更新 CHANGELOG.md
4. 更新相关 docs
5. 总结修改的文件
6. 报告测试结果
7. 报告是否存在未解决问题
```

## 英文版

```text
You are working on this repository.

Before coding, read:

1. AGENTS.md
2. PROJECT_STATE.md
3. ROADMAP.md
4. docs/ARCHITECTURE.md
5. the current task file: tasks/TASK-xxxx.md

Then implement only the current task.

Do not add features outside the current task.
Do not add MCP, API, database, or frontend code unless explicitly required by the task.
Do not change core data models unless explicitly required by the task.
If the task conflicts with AGENTS.md, stop and explain the conflict first.

After implementation:

1. Run tests.
2. Update PROJECT_STATE.md.
3. Update CHANGELOG.md.
4. Update related docs.
5. Summarize changed files.
6. Report test results.
7. Report unresolved issues, if any.
```

---

# 7. 每轮开发后的 Handoff

每轮 Agent 开发结束后，必须留下交接信息。

交接信息应该写入 `PROJECT_STATE.md`。

模板：

```markdown
## Last Handoff

### Completed

- Added ReviewIssue, ReviewResult, ReviewProfile.
- Added WeChat title length rule.
- Added paragraph length rule.
- Added tests for both rules.

### Changed Files

- src/content_review_engine/core/models.py
- src/content_review_engine/rules/wechat.py
- tests/test_rules.py
- docs/REVIEW_RULES.md

### Test Result

`uv run pytest` passed.

### Next Recommended Task

TASK-0003: Add CLI review command.

### Notes

No changes were made to MCP, API, or Skill layers.
```

这个 Handoff 是下一轮开发的起点。

---

# 8. 冻结点规则

长期项目必须有冻结点。

冻结点不是永远不能改，而是：

```text
修改冻结点内容必须写 ADR。
修改冻结点内容必须更新文档。
修改冻结点内容必须更新测试。
修改冻结点内容必须说明迁移影响。
```

建议冻结点：

```text
v0.1.0 冻结 ReviewIssue / ReviewResult 初版结构
v0.2.0 冻结 CLI 命令格式
v0.3.0 冻结 AI Review Adapter 接口
v0.4.0 冻结 Skill 调用方式
v0.5.0 冻结 MCP tools schema
v0.6.0 冻结 API contract
```

---

# 9. ADR 规则

ADR 是 Architecture Decision Record，即架构决策记录。

以下情况必须新增 ADR：

```text
更换核心框架
修改核心目录结构
修改核心数据模型
提前引入 MCP / API / 数据库
修改 CLI 设计原则
修改 ReviewResult 结构
修改长期 Roadmap
改变 package-first 的核心原则
```

ADR 模板：

```markdown
# ADR-0001: Core Package First

## Status

Accepted

## Context

本项目需要长期扩展到 CLI、Skill、MCP、API 和服务器后端。
如果一开始将业务逻辑写入 CLI 或 API，后续会造成重复实现和维护困难。

## Decision

采用 Python package-first 的架构。
核心业务逻辑放在 `src/content_review_engine/`。
CLI、Skill、MCP、API 都作为 adapter 调用核心 package。

## Consequences

好处：

- 核心逻辑可复用
- CLI / MCP / API 不会重复造轮子
- 更适合测试和长期演进

代价：

- 前期需要更明确的数据模型设计
- 不能快速把所有功能堆在入口层
```

---

# 10. 文档单一事实来源原则

项目必须建立“单一事实来源”。

某一类信息只能有一个权威来源，其他地方只能引用或解释，不能重新定义。

| 信息类型     | 单一事实来源                                        |
| -------- | --------------------------------------------- |
| 核心数据结构   | `src/content_review_engine/core/models.py`    |
| 数据模型说明   | `docs/DATA_MODELS.md`                         |
| 审阅规则     | `src/content_review_engine/rules/`            |
| 审阅规则说明   | `docs/REVIEW_RULES.md`                        |
| CLI 命令设计 | `docs/CLI_CONTRACT.md`                        |
| CLI 实现   | `src/content_review_engine/interfaces/cli.py` |
| MCP 工具设计 | `docs/MCP_CONTRACT.md`                        |
| API 设计   | `docs/API_CONTRACT.md`                        |
| 项目当前状态   | `PROJECT_STATE.md`                            |
| 长期路线     | `ROADMAP.md`                                  |
| 架构决策     | `decisions/ADR-xxxx.md`                       |

禁止在 README、Skill、MCP、API 文档中各自重复定义同一套 schema。

---

# 11. 规则 ID 机制

所有审阅规则必须有稳定的 `rule_id`。

示例：

```text
WECHAT_TITLE_001
WECHAT_PARAGRAPH_001
SAFETY_RISK_001
READABILITY_001
STYLE_TONE_001
```

每条规则都必须同时出现在：

```text
规则代码
规则文档
测试样例
审阅报告
```

规则文档模板：

```markdown
## WECHAT_TITLE_001: 标题过长

### Description

公众号文章标题不宜过长，否则影响手机端阅读和点击率。

### Trigger

标题长度超过 32 个中文字符。

### Severity

medium

### Example

Bad:

《这是一个非常非常长的标题，用户在手机端很难快速理解这篇文章到底讲什么》

Good:

《如何设计 AI Agent 的自动审阅流程》

### Implementation

`src/content_review_engine/rules/wechat.py`
```

---

# 12. Prompt 版本化规则

Prompt 也是项目资产，必须像代码一样管理。

不要只在代码里写：

```python
SYSTEM_PROMPT = "你是一个内容审阅专家..."
```

建议结构：

```text
prompts/
  review_v1.jinja
  rewrite_v1.jinja
  summarize_v1.jinja
```

每次模型调用建议记录：

```text
prompt_name
prompt_version
model_name
review_profile
input_hash
output_hash
```

Prompt 改动必须说明：

```text
为什么改
影响什么任务
是否影响输出结构
是否需要更新测试样例
是否需要更新文档
```

---

# 13. 测试与验收规则

每个任务都必须有验收标准。

最低验收要求：

```text
代码可以运行
测试可以通过
相关文档已更新
PROJECT_STATE.md 已更新
CHANGELOG.md 已更新
没有引入任务范围之外的功能
```

每条规则必须有测试。

每个核心函数必须有测试。

每个冻结接口必须有测试。

每个版本发布前必须跑回归样例。

建议建立：

```text
examples/regression/
  wechat_long_title.md
  wechat_bad_structure.md
  academic_abstract.md
  sensitive_expression.md
```

---

# 14. Git 提交规则

每轮任务完成后，建议使用小 commit。

提交粒度：

```text
一个 TASK 对应一个或少数几个 commit。
不要一个 commit 同时完成多个阶段目标。
不要在一个 commit 里混合架构重构、功能开发和格式化。
```

推荐 commit message：

```text
feat: add basic wechat review rules
docs: update review rules documentation
test: add tests for wechat title rule
chore: update project state after task 0002
```

---

# 15. 禁止行为

长期 Agent 开发中禁止以下行为：

```text
禁止没有 TASK 就让 Agent 自由开发
禁止让 Agent 一次性实现 CLI、MCP、API、数据库和前端
禁止在 CLI / MCP / API 中重复写核心审阅逻辑
禁止擅自修改 ReviewResult / ReviewIssue
禁止新增规则但不写 rule_id
禁止修改规则但不更新 docs/REVIEW_RULES.md
禁止修改 Prompt 但不记录版本
禁止修改架构但不写 ADR
禁止任务结束后不更新 PROJECT_STATE.md
禁止测试失败时继续推进下一任务
禁止把网页聊天记录当作项目唯一记忆
```

---

# 16. 推荐的阶段推进顺序

项目推进顺序：

```text
v0.1.0 Python Core Package MVP
→ v0.2.0 CLI Stable
→ v0.3.0 PydanticAI Review Adapter
→ v0.4.0 Skill
→ v0.5.0 MCP Server
→ v0.6.0 FastAPI Backend
→ v0.7.0 Supabase / 用户系统 / 商业化能力
→ v1.0.0 稳定版本
```

不要反过来做。

尤其不要在核心 package 和 CLI 未稳定之前，就开始做 MCP、API、数据库和前端。

---

# 17. 最小可执行协作系统

当前项目刚开始时，最小需要建立这些文件：

```text
AGENTS.md
PROJECT_STATE.md
ROADMAP.md
CHANGELOG.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/REVIEW_RULES.md
tasks/TASK-0001-project-skeleton.md
```

只要这几个文件存在，项目就具备长期演进的基础。

---

# 18. 最终原则总结

本项目的长期开发原则可以总结为：

```text
设计不只存在于聊天中，必须写入仓库。
Agent 不靠记忆工作，而靠仓库文档恢复上下文。
每轮开发必须有明确 TASK。
每个 TASK 必须有验收标准。
每轮完成必须留下 Handoff。
架构变化必须写 ADR。
规则变化必须有 rule_id。
Prompt 变化必须有版本号。
冻结接口不能随意改。
测试不通过不能进入下一阶段。
```

最终目标：

> 让项目即使经过多轮 Agent 开发、多次上下文切换、多次需求演进，仍然能够保持同一套设计原则、同一套架构边界、同一套数据模型和同一条演进路线。
