# TASK-0074: Add LLM Manual Review Checklist

## 1. 背景

当前项目已经完成以下能力：

1. 确定性规则审计；
2. 单文件与批量 CLI；
3. deterministic JSON / Markdown report 输出；
4. Quality Gate / CI 质量门禁；
5. LLM provider interface；
6. LLM runner；
7. 单文件 LLM JSON sidecar 输出；
8. 批量 LLM JSON sidecar 输出；
9. 单文件 LLM Markdown report；
10. 批量 LLM Markdown report；
11. Hybrid Review Report Index；
12. LLM Finding Advisory Policy。

在 TASK-0073 完成后，项目已经明确了 LLM finding 的解释边界：

```text
source = llm
advisory = yes
quality gate participation = no
```

这意味着：

1. LLM findings 是语义审计建议；
2. LLM findings 不进入 deterministic `ReviewResult`；
3. LLM findings 不进入 deterministic `BatchReviewResult`；
4. LLM findings 不参与 `--fail-on`；
5. LLM findings 不参与 quality gate；
6. LLM severity 是 advisory severity，不等同于 deterministic hard-rule severity。

但是，对真实用户来说，LLM report 现在仍然更像“发现项展示”，还不是一个方便人工处理的审阅工作台。用户看完 LLM findings 后，仍然需要手动判断：

1. 哪些 LLM findings 需要优先看；
2. 哪些只是低优先级建议；
3. 每条 finding 是否已经人工确认；
4. 是否接受、忽略或后续修改；
5. batch partial failure 时哪些文件需要重新跑 LLM；
6. CI artifact 中如何快速定位需要人工处理的 LLM 事项。

因此，本任务需要在不改变任何 canonical schema、不新增状态持久化、不改变 CLI exit code、不改变 quality gate 的前提下，为 LLM Markdown report 和 report index 增加一个**人工审阅清单 / Manual Review Checklist**。

本任务的重点是：

> 把 LLM advisory findings 转化为一个稳定、可复制、可人工勾选的 Markdown checklist，帮助用户进行人工审核，但不把这些人工处理状态写回任何数据模型。

---

## 2. 任务目标

新增 LLM manual review checklist 展示能力。

完成后，单文件 LLM Markdown report 中应包含类似结构：

```markdown
## Manual Review Checklist

| ID | Priority | Status | Decision | Quality Gate | Rule | Location | Message | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LLM-001 | high | needs_review | pending | no | llm.semantic_review | line 12, column 4 | ... |  |
| LLM-002 | medium | needs_review | pending | no | llm.tone | line 24, column 1 | ... |  |
```

批量 LLM Markdown report 中应包含类似结构：

```markdown
## Manual Review Checklist

| ID | File | Priority | Status | Decision | Quality Gate | Rule | Location | Message | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LLM-001 | articles/a.md | high | needs_review | pending | no | llm.semantic_review | line 12, column 4 | ... |  |
| LLM-002 | articles/b.md | medium | needs_review | pending | no | llm.tone | line 5, column 1 | ... |  |
```

batch partial failure 场景下，还应展示 LLM execution issue checklist，例如：

```markdown
## LLM Execution Review Checklist

| ID | File | Status | Suggested Action | Error Type | Error Message | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| LLM-ERR-001 | articles/c.md | needs_rerun | rerun_llm_review | LLMProviderError | ... |  |
```

Report index 中应增加一个轻量说明，让用户知道：

1. LLM manual review checklist 是人工审阅辅助；
2. checklist 中的 status / decision 是 Markdown 展示，不是持久化状态；
3. checklist 不影响 deterministic counts；
4. checklist 不影响 fail-on / quality gate；
5. batch partial failure 中的 execution issues 需要人工判断是否重跑。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增 LLM manual review checklist helper；
2. 新增用于展示人工审阅清单的轻量内部类型；
3. 为 LLM findings 生成稳定的 checklist ID；
4. 为 LLM findings 生成人工审阅 priority；
5. 为 LLM findings 生成默认 review status；
6. 为 LLM findings 生成默认 decision；
7. 为 batch LLM execution errors 生成 execution review checklist；
8. 更新单文件 LLM Markdown report；
9. 更新批量 LLM Markdown report；
10. 更新 hybrid report index；
11. 新增 manual review checklist 单元测试；
12. 更新 LLM Markdown report 测试；
13. 更新 report index 测试；
14. 更新 CLI 集成测试中与 report 文本相关的断言；
15. 更新 CLI、LLM provider usage、data models、architecture、CI、project state 和 changelog 文档。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许修改 `ReviewResult` schema；
2. 不允许修改 `BatchReviewResult` schema；
3. 不允许修改 `LLMReviewResult` schema；
4. 不允许修改 `LLMSidecarResult` schema；
5. 不允许把 manual review status 写入 JSON sidecar；
6. 不允许新增持久化 review state 文件；
7. 不允许新增 accept / dismiss / resolve / ignore CLI 命令；
8. 不允许新增 `--review-status`、`--accept-llm-finding`、`--dismiss-llm-finding` 等参数；
9. 不允许让 manual review status 影响 CLI exit code；
10. 不允许让 manual review decision 影响 quality gate；
11. 不允许让 LLM findings 参与 `--fail-on`；
12. 不允许改变 deterministic severity counts；
13. 不允许改变 deterministic rule counts；
14. 不允许改变 deterministic Markdown report 的核心结构；
15. 不允许改变 deterministic JSON 输出；
16. 不允许改变 LLM JSON sidecar 输出；
17. 不允许改变 batch stdout；
18. 不允许新增真实 provider；
19. 不允许新增真实 LLM API 调用；
20. 不允许在测试中调用真实 LLM API；
21. 不允许新增 API / MCP / GUI；
22. 不允许新增 Supabase、用户系统、审计历史或商业化能力；
23. 不允许把 report index 扩展成 full combined report；
24. 不允许使用随机 ID、时间戳或环境相关信息；
25. 不允许输出 secret、API key 或环境变量值。

---

## 5. 需要修改的文件

预计新增：

```text
src/content_review_engine/llm/manual_review.py
tests/test_llm_manual_review.py
```

预计修改：

```text
src/content_review_engine/llm/__init__.py
src/content_review_engine/reports/llm_markdown.py
src/content_review_engine/reports/report_index.py
tests/test_llm_markdown_report.py
tests/test_report_index.py
tests/test_llm_single_file_cli_integration.py
tests/test_llm_batch_cli_integration.py
tests/test_llm_provider_usage_docs.py
docs/CLI.md
docs/LLM_PROVIDER_USAGE.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
docs/CI.md
PROJECT_STATE.md
CHANGELOG.md
```

如当前仓库已有更合适的模块命名，请保持项目已有风格，但必须满足同等功能边界与测试覆盖。

---

## 6. 实现要求

### 6.1 新增 manual review helper

新增：

```text
src/content_review_engine/llm/manual_review.py
```

该模块只负责把 LLM finding / LLM execution error 转成展示层 manual review checklist item。

它不负责：

1. 调用 LLM；
2. 解析 CLI；
3. 写文件；
4. 生成 JSON；
5. 执行 deterministic review；
6. 执行 quality gate；
7. 修改 review result 对象；
8. 读取或保存人工处理状态。

建议定义轻量内部类型，例如：

```python
@dataclass(frozen=True)
class LLMManualReviewItem:
    checklist_id: str
    priority: str
    status: str
    decision: str
    quality_gate: str
    rule_id: str
    location: str
    message: str
    notes: str
```

batch 场景可以使用：

```python
@dataclass(frozen=True)
class LLMBatchManualReviewItem:
    checklist_id: str
    file_path: str
    priority: str
    status: str
    decision: str
    quality_gate: str
    rule_id: str
    location: str
    message: str
    notes: str
```

LLM execution error 可以使用：

```python
@dataclass(frozen=True)
class LLMExecutionReviewItem:
    checklist_id: str
    file_path: str
    status: str
    suggested_action: str
    error_type: str
    error_message: str
    notes: str
```

具体类型名称可以根据项目风格调整。

### 6.2 Checklist ID 规则

Checklist ID 必须稳定，不能使用随机值。

单文件 LLM findings 使用：

```text
LLM-001
LLM-002
LLM-003
```

批量 LLM findings 仍使用全局递增：

```text
LLM-001
LLM-002
LLM-003
```

批量 execution errors 使用：

```text
LLM-ERR-001
LLM-ERR-002
```

要求：

1. ID 基于当前 report 渲染顺序；
2. ID 不保证跨运行永久稳定；
3. 文档中要说明 checklist ID 是 report-local display ID；
4. 不要把 ID 写回 JSON sidecar；
5. 不要把 ID 当成持久化 finding ID。

### 6.3 Priority 规则

基于 LLM advisory severity 生成人工审阅 priority。

建议规则：

```text
critical -> high
error    -> high
warning  -> medium
info     -> low
unknown  -> review
```

要求：

1. priority 只用于人工审阅排序；
2. priority 不影响 CLI exit code；
3. priority 不影响 quality gate；
4. priority 不影响 deterministic counts；
5. priority 不应写入 JSON sidecar；
6. unknown severity 不应导致失败。

### 6.4 Status 与 decision 规则

默认 status：

```text
needs_review
```

默认 decision：

```text
pending
```

默认 quality gate：

```text
no
```

要求：

1. 这些字段只出现在 Markdown report；
2. 不写入 JSON；
3. 不持久化；
4. 不影响 deterministic review；
5. 不影响 LLM review result；
6. 不影响 exit code；
7. 不影响 quality gate；
8. 未来如果需要 accept / dismiss，必须另开任务。

### 6.5 Location 规则

location 应稳定展示。

建议格式：

```text
line 12, column 4
```

如果缺失：

```text
not provided
```

如果只有 line：

```text
line 12
```

如果只有 column：

```text
column 4
```

不要因为位置缺失导致渲染失败。

### 6.6 Message 与 notes 规则

message 应来自 finding message 或等价字段。

如果缺失：

```text
not provided
```

notes 默认留空或使用稳定占位，例如：

```text
—
```

建议使用空字符串或 `—`，但必须在测试中稳定。

不要生成模型式新建议，不要调用 LLM 生成 notes。

### 6.7 Batch execution errors

对于 batch LLM sidecar 中的 per-file error，应生成 execution review checklist。

建议字段：

```text
ID
File
Status
Suggested Action
Error Type
Error Message
Notes
```

默认 status：

```text
needs_rerun
```

默认 suggested action：

```text
rerun_llm_review
```

要求：

1. 只展示 LLM execution failure；
2. 不改变 TASK-0070 的 partial failure exit code；
3. 不改变 sidecar JSON；
4. 不改变 deterministic batch result；
5. 不把 execution error 当成 LLM finding；
6. 不参与 severity counts；
7. 不参与 quality gate。

### 6.8 更新 LLM Markdown report

更新：

```text
src/content_review_engine/reports/llm_markdown.py
```

单文件 LLM report 应增加：

```markdown
## Manual Review Checklist
```

如果有 findings，输出 checklist 表格。

如果没有 findings，输出稳定文本：

```markdown
No LLM findings require manual review.
```

批量 LLM report 应增加：

```markdown
## Manual Review Checklist
```

如果有 LLM findings，输出含 `File` 列的 checklist 表格。

如果没有 LLM findings，输出：

```markdown
No LLM findings require manual review.
```

如果 batch 中存在 LLM execution errors，应增加：

```markdown
## LLM Execution Review Checklist
```

如果没有 execution errors，可以不输出该 section，或输出稳定文本：

```markdown
No LLM execution issues require review.
```

建议只有存在 execution errors 时输出该 section，以减少噪音。

### 6.9 更新 report index

更新：

```text
src/content_review_engine/reports/report_index.py
```

当 LLM 启用时，index 中增加或补充：

```markdown
## Manual Review Workflow

- LLM manual review checklist items are report-local Markdown markers.
- Checklist IDs are stable within the generated report but are not persisted identifiers.
- Status and decision fields are editable human-review placeholders.
- Manual review status does not affect deterministic findings.
- Manual review status does not participate in fail-on / quality gate decisions.
```

batch partial failure 时，应补充说明：

```markdown
- LLM execution errors should be reviewed separately and may require rerunning LLM review.
```

deterministic-only index 不应错误声称有 LLM checklist，可以只说明：

```markdown
LLM Review: not enabled
```

### 6.10 CLI 行为

本任务不新增 CLI 参数。

现有 CLI 行为必须保持：

1. `--output` 仍负责 deterministic 主输出；
2. `--llm-output` 仍负责 LLM JSON sidecar；
3. `--llm-report` 仍负责 LLM Markdown report；
4. `--report-index` 仍负责导航 / 解释型 index；
5. `--report-index` 不隐式开启 LLM；
6. `--enable-llm` 仍必须配合 `--llm-output` 或 `--llm-report`；
7. manual review priority 不影响 exit code；
8. manual review status 不影响 exit code；
9. manual review decision 不影响 quality gate；
10. LLM execution review checklist 不改变 partial failure exit behavior。

### 6.11 输出稳定性

所有新增输出必须稳定。

禁止包含：

1. 当前时间戳；
2. 随机 ID；
3. 绝对路径，除非项目现有测试和文档已经使用绝对路径；
4. API key；
5. 环境变量值；
6. 当前机器用户名；
7. provider secret；
8. 非确定性排序。

Markdown 表格中必须继续处理：

1. `|`；
2. 换行；
3. 空值；
4. `None`；
5. 长文本的稳定展示。

---

## 7. 测试要求

### 7.1 新增 manual review 单元测试

新增：

```text
tests/test_llm_manual_review.py
```

至少覆盖：

1. single-file checklist ID starts at `LLM-001`；
2. multiple findings get stable sequential IDs；
3. batch checklist IDs are globally sequential；
4. execution error IDs start at `LLM-ERR-001`；
5. critical severity maps to high priority；
6. error severity maps to high priority；
7. warning severity maps to medium priority；
8. info severity maps to low priority；
9. unknown severity maps to review priority；
10. missing severity maps to review priority；
11. default status is `needs_review`；
12. default decision is `pending`；
13. default quality gate is `no`；
14. missing location renders `not provided`；
15. missing message renders `not provided`；
16. helper does not mutate input finding；
17. checklist ID is deterministic and not random；
18. execution error suggested action is `rerun_llm_review`。

### 7.2 更新 LLM Markdown report 测试

更新：

```text
tests/test_llm_markdown_report.py
```

至少覆盖：

1. single-file report includes `## Manual Review Checklist`；
2. single-file checklist contains `LLM-001`；
3. single-file checklist contains priority；
4. single-file checklist contains status `needs_review`；
5. single-file checklist contains decision `pending`；
6. single-file checklist contains quality gate `no`；
7. single-file no findings outputs `No LLM findings require manual review.`；
8. batch report includes `## Manual Review Checklist`；
9. batch checklist includes file path；
10. batch checklist uses global sequential IDs；
11. batch partial failure includes `## LLM Execution Review Checklist`；
12. batch execution error checklist contains `LLM-ERR-001`；
13. batch execution error checklist contains `needs_rerun`；
14. batch execution error checklist contains `rerun_llm_review`；
15. Markdown escaping remains stable；
16. advisory policy remains present；
17. output does not include timestamp or random values。

### 7.3 更新 report index 测试

更新：

```text
tests/test_report_index.py
```

至少覆盖：

1. hybrid single-file index includes `Manual Review Workflow`；
2. hybrid batch index includes `Manual Review Workflow`；
3. manual review workflow says checklist IDs are report-local；
4. manual review workflow says status / decision do not affect quality gate；
5. deterministic-only index does not incorrectly claim LLM checklist exists；
6. batch partial failure index mentions LLM execution errors may require rerun；
7. index does not copy full checklist；
8. index output remains stable；
9. Markdown escaping remains stable。

### 7.4 更新 CLI 集成测试

更新相关 CLI integration tests，至少覆盖：

1. `--llm-report` output contains manual review checklist；
2. `--llm-report` no findings contains no-review-needed text；
3. batch `--llm-report` output contains manual review checklist；
4. batch partial failure `--llm-report` output contains execution review checklist；
5. `--report-index` output contains manual review workflow when LLM enabled；
6. deterministic-only `--report-index` remains valid；
7. manual review priority does not affect exit code；
8. manual review status does not affect quality gate；
9. tests do not require real network；
10. tests do not require real API key。

### 7.5 更新文档断言测试

如果项目已有文档断言测试，例如：

```text
tests/test_llm_provider_usage_docs.py
```

需要同步更新，确保文档中包含：

1. manual review checklist；
2. report-local checklist ID；
3. needs_review；
4. pending；
5. quality gate no；
6. execution review checklist；
7. rerun_llm_review；
8. manual review status does not affect quality gate；
9. manual review checklist is not persisted；
10. JSON sidecar remains canonical machine-readable LLM output。

---

## 8. 文档更新要求

### 8.1 docs/CLI.md

需要补充：

1. LLM Markdown report 中 manual review checklist 的含义；
2. checklist ID 是 report-local display ID；
3. status 默认是 `needs_review`；
4. decision 默认是 `pending`；
5. quality gate 默认是 `no`；
6. batch partial failure 中 execution review checklist 的含义；
7. manual review checklist 不影响 CLI exit code；
8. manual review checklist 不影响 quality gate；
9. manual review checklist 不写入 JSON sidecar。

### 8.2 docs/LLM_PROVIDER_USAGE.md

需要补充：

1. manual review workflow；
2. 如何使用 LLM Markdown report 进行人工审阅；
3. priority 规则；
4. status / decision 字段只是 Markdown 占位；
5. execution errors 如何人工处理；
6. 为什么不在本任务中实现 accept / dismiss；
7. 测试仍然不需要真实 API key；
8. 手动验证建议使用小样本 Markdown。

### 8.3 docs/DATA_MODELS.md

需要补充：

1. manual review checklist 是 presentation-only；
2. checklist ID 不是持久化 ID；
3. status / decision 不进入 canonical schema；
4. 不修改 `ReviewResult`；
5. 不修改 `BatchReviewResult`；
6. 不修改 `LLMReviewResult`；
7. 不修改 `LLMSidecarResult`；
8. machine-readable LLM 输出仍以 LLM JSON sidecar 为准。

### 8.4 docs/ARCHITECTURE.md

需要补充：

1. `llm/manual_review.py` 所在层级；
2. manual review helper 位于 LLM policy 与 presentation renderer 之间；
3. manual review helper 不负责 provider；
4. manual review helper 不负责 runner；
5. manual review helper 不负责 CLI；
6. manual review helper 不负责 persistence；
7. manual review helper 不负责 quality gate；
8. manual review helper 不修改 result object。

### 8.5 docs/CI.md

需要补充：

1. LLM manual review checklist 可以作为 CI artifact；
2. checklist status 不影响 CI pass/fail；
3. checklist decision 不影响 CI pass/fail；
4. priority 不影响 CI pass/fail；
5. deterministic fail-on 仍是 CI gate 来源；
6. batch execution review checklist 可帮助定位需要重跑 LLM 的文件。

### 8.6 PROJECT_STATE.md

记录 TASK-0074 完成后项目状态：

1. 已新增 LLM manual review checklist；
2. LLM Markdown report 已包含人工审阅清单；
3. batch LLM report 已包含 execution review checklist；
4. report index 已说明 manual review workflow；
5. manual review checklist 仍是 presentation-only；
6. LLM findings 仍未合并进主 ReviewResult；
7. LLM findings 仍不参与 quality gate；
8. API / MCP / GUI 仍未开始。

### 8.7 CHANGELOG.md

新增 TASK-0074 条目，说明：

1. 新增 LLM manual review checklist；
2. 新增 report-local checklist ID；
3. 新增 manual review priority / status / decision 展示；
4. 新增 batch LLM execution review checklist；
5. 更新 LLM Markdown report；
6. 更新 hybrid report index；
7. 不改变 canonical schema；
8. 不改变 quality gate。

---

## 9. 验收标准

本任务完成后，应满足以下标准：

1. 新增 `src/content_review_engine/llm/manual_review.py`；
2. 新增 `tests/test_llm_manual_review.py`；
3. 单文件 LLM Markdown report 包含 `## Manual Review Checklist`；
4. 批量 LLM Markdown report 包含 `## Manual Review Checklist`；
5. 有 LLM findings 时生成稳定 `LLM-001`、`LLM-002` 等 ID；
6. batch LLM findings 使用稳定全局顺序 ID；
7. batch partial failure 时生成 `## LLM Execution Review Checklist`；
8. execution errors 使用稳定 `LLM-ERR-001`、`LLM-ERR-002` 等 ID；
9. priority 根据 advisory severity 稳定生成；
10. 默认 status 是 `needs_review`；
11. 默认 decision 是 `pending`；
12. 默认 quality gate 是 `no`；
13. no findings 时输出稳定 no-review-needed 文本；
14. report index 中说明 manual review workflow；
15. checklist ID 明确为 report-local display ID；
16. manual review status 不影响 exit code；
17. manual review decision 不影响 quality gate；
18. manual review priority 不影响 deterministic counts；
19. 不修改 `ReviewResult` schema；
20. 不修改 `BatchReviewResult` schema；
21. 不修改 `LLMReviewResult` schema；
22. 不修改 `LLMSidecarResult` schema；
23. 不修改 LLM JSON sidecar 输出；
24. 不新增 accept / dismiss CLI；
25. 不新增真实 provider；
26. 不新增 API / MCP / GUI；
27. 所有新增测试通过；
28. `uv run pytest` 全量通过；
29. 文档已同步更新。

---

## 10. 风险与注意事项

1. 不要把 checklist 做成持久化状态；
2. 不要把 checklist ID 当作永久 finding ID；
3. 不要把 status / decision 写入 JSON sidecar；
4. 不要新增 accept / dismiss 命令；
5. 不要让 priority 影响 exit code；
6. 不要让 status 影响 quality gate；
7. 不要让 decision 影响 deterministic findings；
8. 不要让 execution review checklist 改变 partial failure 行为；
9. 不要把 execution error 当成 LLM finding；
10. 不要改变 severity counts；
11. 不要改变 rule counts；
12. 不要修改 deterministic report；
13. 不要修改 deterministic JSON；
14. 不要在 tests 中调用真实 LLM；
15. 不要输出 secret、API key 或环境变量值；
16. 不要加入时间戳或随机值；
17. 不要把 report index 扩展成 full combined report；
18. 不要把本任务扩展到 API / MCP / GUI。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_manual_review.py
uv run pytest tests/test_llm_markdown_report.py
uv run pytest tests/test_report_index.py
uv run pytest tests/test_llm_single_file_cli_integration.py
uv run pytest tests/test_llm_batch_cli_integration.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest tests/test_cli.py
uv run pytest
```

如果某些测试文件在当前仓库中不存在，请根据实际文件名调整，但必须覆盖同等测试范围。

---

