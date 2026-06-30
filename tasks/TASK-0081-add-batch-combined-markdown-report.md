# TASK-0081: Add Batch Combined Markdown Report

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate、LLM sidecar 输出、LLM Markdown report、review index、manual review checklist、artifact examples、LLM-to-core finding adapter、single-file combined review result envelope、single-file combined Markdown renderer、single-file combined CLI output option，以及 batch combined review result envelope。

截至 TASK-0080，batch 层已经存在：

```text
BatchReviewResult
Batch LLM result
Per-file LLMReviewResult
LLMCoreFindingCandidate
  ↓
BatchCombinedReviewResult
```

`BatchCombinedReviewResult` 可以表达：

1. deterministic `BatchReviewResult`；
2. 原始 batch LLM sidecar result；
3. per-file LLM status；
4. per-file LLM finding candidates；
5. batch-level LLM summary；
6. per-file structured LLM error；
7. advisory policy；
8. deterministic-only quality gate boundary。

但是目前 batch combined result 还没有对应的人类可读 Markdown 展示层。

本任务是 LLM 合并主程序的第六步：

> 新增 batch combined Markdown report renderer，用于把 `BatchCombinedReviewResult` 渲染为人类可读 Markdown 报告，但暂时不接入 batch CLI，不修改 batch 默认输出，不修改 quality gate。

本任务只增加 batch combined presentation layer。

---

## 2. 任务目标

新增一个 batch combined Markdown report renderer。

该 renderer 应能够从 `BatchCombinedReviewResult` 生成 Markdown 文本，清晰展示：

1. deterministic batch review summary；
2. LLM batch execution summary；
3. LLM per-file status summary；
4. LLM advisory findings；
5. LLM error summary；
6. manual review workflow；
7. manual review checklist；
8. quality gate boundary；
9. deterministic batch report 内容。

本任务完成后，项目应存在类似函数：

```python
render_batch_combined_markdown_report(...)
```

或根据现有命名风格采用类似名称。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增 batch combined Markdown renderer 模块，例如：

   ```text
   src/content_review_engine/reports/batch_combined_markdown.py
   ```

2. 新增渲染函数，例如：

   ```python
   render_batch_combined_markdown_report(
       result: BatchCombinedReviewResult,
   ) -> str
   ```

3. 复用 TASK-0080 的 `BatchCombinedReviewResult`。

4. 复用现有 deterministic batch Markdown renderer，避免重复实现 deterministic batch report 全部逻辑。

5. 复用或参考现有 batch LLM Markdown report / report index 的展示风格。

6. 展示 batch-level LLM summary：

   ```text
   total_files
   succeeded_count
   failed_count
   skipped_count
   not_run_count
   advisory_finding_count
   files_with_advisory_findings
   error_count
   ```

7. 展示 per-file LLM status：

   ```text
   succeeded
   failed
   skipped
   not_run
   ```

8. 展示 per-file LLM advisory findings。

9. 展示 failed 文件的 structured error。

10. 展示 manual review workflow。

11. 展示 manual review checklist，作为 presentation-only 内容。

12. 展示 quality gate boundary，明确 batch quality gate 仍然 deterministic-only。

13. 新增测试覆盖 all succeeded、partial failure、all failed、not_run、skipped、LLM findings、error summary、manual review workflow、quality gate boundary、Markdown escaping、deterministic report 内容保留。

14. 更新相关文档、PROJECT_STATE.md 和 CHANGELOG.md。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许修改 `BatchCombinedReviewResult` schema，除非发现 TASK-0080 中存在明显 bug，且必须保持兼容。

2. 不允许修改 `BatchReviewResult` schema。

3. 不允许修改单文件 `ReviewResult` schema。

4. 不允许把 LLM findings 写入 deterministic `ReviewResult.findings`。

5. 不允许把 LLM findings 写入 deterministic `BatchReviewResult`。

6. 不允许修改 deterministic batch runner。

7. 不允许修改 deterministic rule engine。

8. 不允许修改 batch CLI 默认输出。

9. 不允许新增 batch CLI 参数。

10. 不允许给 batch CLI 接入 `--combined-output`。

11. 不允许修改单文件 CLI 的 0079 行为。

12. 不允许修改 existing `--output`、`--llm-output`、`--format` 语义。

13. 不允许修改 existing batch Markdown report 默认输出。

14. 不允许修改 quality gate 行为。

15. 不允许让 LLM findings 参与 deterministic `severity_counts`、`rule_counts`、quality gate 或 exit code。

16. 不允许接入新的真实 LLM API。

17. 不允许修改 provider contract。

18. 不允许修改 sidecar JSON schema。

19. 不允许让 `examples/llm_review_artifacts/` 成为 runtime dependency。

20. 不允许新增 API、MCP、GUI、Supabase、前端或商业化能力。

21. 不允许把 manual review checklist 持久化进 canonical schema。

---

## 5. 需要修改的文件

预计新增：

```text
src/content_review_engine/reports/batch_combined_markdown.py
tests/test_llm_batch_combined_markdown_report.py
```

预计修改：

```text
src/content_review_engine/reports/__init__.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
PROJECT_STATE.md
CHANGELOG.md
tests/test_llm_provider_usage_docs.py
```

如果现有项目中有更合适的 report 模块命名，可以按现有风格调整，但必须保持：

```text
batch combined data model 位于 llm 层
batch combined Markdown renderer 位于 reports 层
CLI 不承载 renderer 逻辑
deterministic batch result 不被污染
```

---

## 6. 实现要求

### 6.1 Renderer 函数

新增渲染函数，例如：

```python
def render_batch_combined_markdown_report(
    result: BatchCombinedReviewResult,
) -> str:
    ...
```

要求：

1. 输入 `BatchCombinedReviewResult`。
2. 输出 Markdown 字符串。
3. 函数必须是纯函数。
4. 不读文件。
5. 不写文件。
6. 不调用 CLI。
7. 不调用 provider。
8. 不读取环境变量。
9. 不读取 examples 目录。
10. 不修改传入的 result。
11. 输出稳定、可测试。
12. 输出结尾建议保留单个换行符。

---

### 6.2 推荐 Markdown 结构

建议输出结构如下：

```md
# Batch Combined Content Review Report

## Summary

| Field | Value |
| --- | --- |
| Files Reviewed | 3 |
| Deterministic Findings | 5 |
| LLM Total Files | 3 |
| LLM Succeeded | 2 |
| LLM Failed | 1 |
| LLM Skipped | 0 |
| LLM Not Run | 0 |
| LLM Advisory Findings | 4 |
| Files With LLM Advisory Findings | 2 |
| LLM Errors | 1 |
| Quality Gate Scope | deterministic-only |

## LLM Execution Summary

| Status | Count |
| --- | --- |
| succeeded | 2 |
| failed | 1 |
| skipped | 0 |
| not_run | 0 |

## LLM File Status Summary

| File | Status | Advisory Findings | Error |
| --- | --- | --- | --- |
| article-a.md | succeeded | 2 | - |
| article-b.md | succeeded | 2 | - |
| article-with-llm-error.md | failed | 0 | provider_error |

## LLM Advisory Findings

| File | Severity | Rule | Location | Message | Suggestion |
| --- | --- | --- | --- | --- | --- |
| article-a.md | warning | llm.misleading_claim | 3:1 | ... | ... |

## LLM Error Summary

| File | Type | Message | Provider | Retryable |
| --- | --- | --- | --- | --- |
| article-with-llm-error.md | provider_error | ... | openai | true |

## Manual Review Workflow

1. Review deterministic batch findings first.
2. Review LLM advisory findings as semantic suggestions.
3. Resolve failed LLM files by rerunning or manually inspecting them.
4. Confirm, reject, or rewrite each LLM advisory finding manually.
5. Treat LLM findings as presentation-only unless a future explicit policy enables enforcement.

## Manual Review Checklist

| File | Item | Status |
| --- | --- | --- |
| article-a.md | Review LLM advisory finding 1 | pending |
| article-with-llm-error.md | Inspect LLM execution error | pending |

## Quality Gate Boundary

LLM findings are advisory in this report. They do not affect deterministic severity counts, rule counts, quality gate decisions, fail-on behavior, or CLI exit codes.

## Deterministic Batch Review

<existing deterministic batch markdown report or embedded deterministic batch summary/report>
```

可根据现有 report 风格调整标题和表格列，但必须包含：

1. batch summary；
2. LLM execution summary；
3. LLM file status summary；
4. LLM advisory findings；
5. failed 状态下的 error summary；
6. manual review workflow；
7. manual review checklist；
8. quality gate deterministic-only 说明；
9. deterministic batch review 内容。

---

### 6.3 Deterministic batch report 复用要求

如果项目已有函数，例如：

```python
render_batch_markdown_report(...)
```

或类似 deterministic batch Markdown renderer，本任务应尽量复用它。

要求：

1. 不要复制粘贴 deterministic batch report 的完整渲染逻辑。
2. 如果直接嵌入 existing deterministic batch report，需要避免改变其独立输出。
3. 如果现有 renderer 不方便嵌入，可以提取轻量 helper，但不得大规模重构 report 系统。
4. 不允许改变现有 deterministic batch Markdown report 的输出。

---

### 6.4 LLM execution summary 展示要求

Batch combined report 必须展示 batch-level LLM summary。

字段至少包括：

```text
total_files
succeeded_count
failed_count
skipped_count
not_run_count
advisory_finding_count
files_with_advisory_findings
error_count
```

要求：

1. summary 内容来自 `BatchCombinedLLMSummary`。
2. 不在 renderer 中重新推导一套不一致 summary。
3. 表格值必须稳定。
4. summary 区域必须有测试覆盖。

---

### 6.5 LLM file status summary 展示要求

必须展示每个文件的 LLM 状态。

表格至少包含：

```text
File
Status
Advisory Findings
Error
```

要求：

1. 文件顺序应跟随 `BatchCombinedReviewResult.files`。
2. `succeeded` 文件显示 advisory finding 数量。
3. `failed` 文件显示 error type 或 error message 摘要。
4. `skipped` / `not_run` 文件显示 0 findings。
5. 表格内容必须做 Markdown escaping。

---

### 6.6 LLM advisory findings 展示要求

如果存在 LLM advisory findings，必须展示 findings 表格。

表格至少包含：

```text
File
Severity
Rule
Location
Message
Suggestion
```

建议可包含：

```text
Matched Text
Category
Context
```

但不要让表格过宽到不可读。

要求：

1. 只展示 `LLMCoreFindingCandidate`。

2. 每条 finding 必须保持 advisory 语义。

3. rule id 必须显示 `llm.` 前缀。

4. location 应由 `line` / `column` 生成。

5. 无 location 时显示 `-`。

6. 无 suggestion 时显示 `-`。

7. 如果没有任何 LLM advisory findings，应显示：

   ```text
   No LLM advisory findings.
   ```

8. 不允许把 deterministic findings 放入 LLM advisory findings 表格。

---

### 6.7 LLM error summary 展示要求

如果存在 failed 文件或 error summary，必须展示 LLM error summary。

表格至少包含：

```text
File
Type
Message
Provider
Retryable
```

要求：

1. 不输出 secret/API key。
2. 不输出完整环境变量。
3. 不输出 Python traceback。
4. 字段为空时显示 `-`。
5. message 需要 Markdown escaping。
6. 如果没有 errors，可以省略 `## LLM Error Summary`，或者显示：

   ```text
   No LLM execution errors.
   ```

   但行为必须稳定并有测试覆盖。

---

### 6.8 各状态展示要求

#### all succeeded

当所有文件 status 都是 `succeeded`：

1. summary 中 `succeeded_count == total_files`。
2. `failed_count == 0`。
3. 可以省略 error summary，或显示 no errors。
4. 展示 LLM advisory findings 或 no findings 文案。
5. 展示 quality gate boundary。

#### partial failure

当部分文件 `failed`：

1. summary 中 failed count 正确。
2. file status summary 显示 succeeded / failed。
3. failed 文件出现在 error summary。
4. succeeded 文件仍展示 findings。
5. manual review workflow 提醒 failed 文件需要人工检查或 rerun。
6. deterministic batch report 仍然存在。

#### all failed

当所有文件 `failed`：

1. summary 中 `failed_count == total_files`。
2. advisory findings 为空。
3. error summary 展示所有文件错误。
4. deterministic batch report 仍然存在。
5. quality gate boundary 明确 deterministic-only。

#### not_run

当所有文件 `not_run`：

1. summary 中 `not_run_count == total_files`。
2. 不渲染空 LLM findings 表，或显示 no LLM advisory findings。
3. 显示 LLM was not run 或等价说明。
4. deterministic batch report 仍然存在。

#### skipped

当所有文件 `skipped`：

1. summary 中 `skipped_count == total_files`。
2. 显示 LLM review was skipped 或等价说明。
3. deterministic batch report 仍然存在。

---

### 6.9 Manual Review Workflow 展示要求

combined batch Markdown report 必须包含 manual review workflow。

推荐内容：

```md
## Manual Review Workflow

1. Review deterministic batch findings first.
2. Review LLM advisory findings as semantic suggestions.
3. For failed LLM files, inspect the structured error and decide whether to rerun LLM review.
4. Confirm, reject, or rewrite each LLM advisory finding manually.
5. Treat checklist status as presentation-only; it is not persisted into canonical schema.
```

要求：

1. 明确 LLM findings 是 advisory。
2. 明确 failed 文件需要人工检查或 rerun。
3. 明确 checklist/workflow 是 presentation-only。
4. 不把 manual review workflow 写回 schema。
5. 不影响 quality gate。

---

### 6.10 Manual Review Checklist 展示要求

可以基于 batch combined result 动态生成 presentation-only checklist。

建议规则：

1. 对每个 LLM advisory finding 生成一个 pending checklist item。
2. 对每个 failed 文件生成一个 pending error inspection item。
3. 对 skipped / not_run 文件可生成一个 optional item，或者只在 workflow 中说明。
4. Checklist 不应写入 schema。
5. Checklist 不应影响 serializer。
6. Checklist 不应影响 quality gate。

建议表格：

```md
| File | Item | Status |
| --- | --- | --- |
| article-a.md | Review LLM advisory finding 1 | pending |
| article-with-llm-error.md | Inspect LLM execution error | pending |
```

---

### 6.11 Quality Gate Boundary 展示要求

combined batch Markdown report 必须包含 quality gate boundary。

推荐内容：

```md
## Quality Gate Boundary

LLM findings are advisory in this report. They do not affect deterministic severity counts, rule counts, fail-on behavior, quality gate decisions, or CLI exit codes.
```

要求：

1. 必须提到 deterministic-only。
2. 必须提到 LLM findings 不影响 severity counts。
3. 必须提到 LLM findings 不影响 rule counts。
4. 必须提到 LLM findings 不影响 fail-on。
5. 必须提到 LLM findings 不影响 quality gate。
6. 必须提到 LLM findings 不影响 exit code。
7. 该说明必须有测试覆盖。

---

### 6.12 Markdown escaping 要求

新增 helper 或复用现有 helper，确保表格单元格不会被破坏。

至少处理：

```text
|
换行
None
```

建议规则：

```text
None -> "-"
"\n" -> "<br>"
"|" -> "\|"
```

如果项目已有 Markdown escaping helper，应复用现有实现。

---

### 6.13 导出要求

在：

```text
src/content_review_engine/reports/__init__.py
```

中导出新增 renderer。

建议导出：

```python
render_batch_combined_markdown_report
```

如果新增 helper 是内部函数，不必导出。

---

## 7. 测试要求

新增：

```text
tests/test_llm_batch_combined_markdown_report.py
```

至少覆盖以下测试。

### 7.1 all succeeded 渲染

构造 all succeeded 的 `BatchCombinedReviewResult`。

验证输出包含：

1. `# Batch Combined Content Review Report`；
2. `## Summary`；
3. `## LLM Execution Summary`；
4. `## LLM File Status Summary`；
5. `## LLM Advisory Findings`；
6. `succeeded`；
7. `llm.` rule id；
8. LLM finding message；
9. LLM finding suggestion；
10. `advisory`；
11. `deterministic-only`。

---

### 7.2 partial failure 渲染

构造 partial failure 的 `BatchCombinedReviewResult`。

验证输出包含：

1. succeeded 文件；
2. failed 文件；
3. `## LLM Error Summary`；
4. error type；
5. error message；
6. provider；
7. retryable；
8. succeeded 文件的 LLM findings；
9. failed 文件没有 fake findings；
10. deterministic batch report 仍然存在。

---

### 7.3 all failed 渲染

验证输出包含：

1. 所有文件状态为 failed；
2. error summary；
3. `No LLM advisory findings.`；
4. deterministic batch report；
5. quality gate deterministic-only。

---

### 7.4 not_run 渲染

验证输出包含：

1. `not_run`；
2. `LLM review was not run` 或等价文案；
3. `No LLM advisory findings.`；
4. deterministic batch report；
5. 不输出误导性的 fake findings。

---

### 7.5 skipped 渲染

验证输出包含：

1. `skipped`；
2. `LLM review was skipped` 或等价文案；
3. deterministic batch report；
4. quality gate boundary。

---

### 7.6 LLM summary counts

验证 summary 中包含并正确展示：

```text
total_files
succeeded_count
failed_count
skipped_count
not_run_count
advisory_finding_count
files_with_advisory_findings
error_count
```

---

### 7.7 file status summary

验证每个文件都有一行 status summary，且顺序稳定。

---

### 7.8 manual review workflow

验证输出包含：

```text
## Manual Review Workflow
```

并包含：

```text
deterministic batch findings first
LLM advisory findings
failed LLM files
presentation-only
```

或等价文案。

---

### 7.9 manual review checklist

验证输出包含：

```text
## Manual Review Checklist
```

并包含：

1. LLM advisory finding review item；
2. failed file error inspection item；
3. `pending` 状态；
4. checklist 不来自 schema 持久化字段。

---

### 7.10 quality gate boundary

验证输出明确包含：

```text
deterministic-only
do not affect deterministic severity counts
do not affect deterministic rule counts
do not affect fail-on
do not affect quality gate
do not affect exit code
```

或等价文案。

---

### 7.11 deterministic batch report 内容保留

验证 combined report 中包含 deterministic batch report 的关键内容，例如：

1. deterministic batch report title；
2. files reviewed；
3. total findings；
4. deterministic finding message；
5. deterministic rule id。

同时验证 existing deterministic batch Markdown renderer 的独立输出没有被修改。

---

### 7.12 Markdown escaping

构造 LLM finding / error，其中 message、suggestion、provider 或 file 包含：

```text
|
换行
```

验证 Markdown 表格没有被破坏。

---

### 7.13 不改变 serializers

验证：

1. `batch_combined_review_result_to_dict(...)` 输出不因 renderer 改变；
2. deterministic batch serializer 输出不变；
3. batch LLM sidecar serializer 输出不变。

---

### 7.14 不调用真实 LLM

测试不得依赖：

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
真实网络
真实 PydanticAI provider
真实模型响应
```

必须使用现有 mock / fixture / test model 机制。

---

## 8. 文档更新要求

需要更新：

```text
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
PROJECT_STATE.md
CHANGELOG.md
```

### 8.1 docs/ARCHITECTURE.md

说明新增 batch combined Markdown renderer 的位置：

```text
BatchCombinedReviewResult
  ↓
batch combined Markdown renderer
  ↓
future batch combined CLI output
```

必须明确：

1. renderer 是 presentation layer；
2. renderer 不修改 `BatchCombinedReviewResult`；
3. renderer 不修改 `BatchReviewResult`；
4. renderer 不修改 batch CLI 默认输出；
5. renderer 不修改 quality gate；
6. renderer 不调用 provider；
7. renderer 为后续 batch combined CLI output 做准备。

---

### 8.2 docs/DATA_MODELS.md

说明本任务没有新增 canonical schema。

必须明确：

1. `BatchCombinedReviewResult` schema 不变；
2. batch combined Markdown 是 presentation output；
3. manual review workflow 不持久化；
4. manual review checklist 不持久化；
5. quality gate boundary 是展示说明，不是执行策略变更。

---

### 8.3 docs/LLM_PROVIDER_USAGE.md

说明：

1. provider contract 不变；
2. batch provider / runner 不知道 batch combined Markdown renderer；
3. renderer 消费的是 `BatchCombinedReviewResult`；
4. sidecar JSON 不变；
5. partial failure 可以在 report 中展示；
6. failed 文件可以在 error summary 中展示；
7. LLM findings 仍然 advisory；
8. deterministic batch result 在 LLM partial failure / all failure 时仍然有效。

---

### 8.4 docs/CLI.md

说明：

1. batch combined Markdown renderer 已存在；
2. 当前 batch CLI 尚未暴露 `--combined-output`；
3. 不要在文档中声明 batch combined CLI 参数已经可用；
4. 单文件 0079 的 `--combined-output` 行为保持不变；
5. batch combined CLI output 将由后续任务决定。

---

### 8.5 PROJECT_STATE.md

记录 TASK-0081 完成后状态：

```text
Batch combined Markdown report renderer added.
```

同时明确：

```text
The renderer is not yet wired into batch CLI output, batch default output, or quality gate behavior.
```

---

### 8.6 CHANGELOG.md

新增 TASK-0081 条目，说明：

1. 新增 batch combined Markdown renderer；
2. 展示 batch deterministic review + LLM advisory findings；
3. 展示 batch LLM summary；
4. 展示 per-file LLM status；
5. 展示 LLM error summary；
6. 展示 manual review workflow；
7. 展示 manual review checklist；
8. 展示 quality gate boundary；
9. 新增测试；
10. 未改变 batch CLI / quality gate / provider behavior。

---

## 9. 验收标准

本任务完成后应满足：

1. 新增 batch combined Markdown renderer；
2. renderer 输入 `BatchCombinedReviewResult`；
3. renderer 输出稳定 Markdown；
4. all succeeded 状态可以展示 LLM advisory findings；
5. partial failure 状态可以展示 succeeded findings 和 failed errors；
6. all failed 状态可以展示 error summary 和 no advisory findings；
7. not_run 状态有清晰说明；
8. skipped 状态有清晰说明；
9. report 中包含 batch-level LLM summary；
10. report 中包含 per-file LLM status summary；
11. report 中包含 LLM advisory findings；
12. report 中包含 LLM error summary；
13. report 中包含 manual review workflow；
14. report 中包含 manual review checklist；
15. report 中包含 quality gate boundary；
16. report 明确 LLM findings are advisory；
17. Markdown table 内容做 escaping；
18. deterministic batch report 内容被保留；
19. 不修改 `BatchCombinedReviewResult` schema；
20. 不修改 `BatchReviewResult` schema；
21. 不修改 `ReviewResult` schema；
22. 不修改 batch CLI 默认输出；
23. 不新增 batch CLI 参数；
24. 不修改 existing batch Markdown report 默认输出；
25. 不修改 quality gate；
26. 不修改 provider contract；
27. 不修改 sidecar JSON；
28. 不接入真实 LLM；
29. 新增测试通过；
30. 全量测试通过；
31. 文档同步更新。

---

## 10. 风险与注意事项

### 10.1 不要提前接入 batch CLI

本任务只新增 renderer。

不要新增：

```text
content-review batch --combined-output
```

batch CLI 接入留给后续任务。

---

### 10.2 不要修改 existing batch Markdown report

可以复用 existing deterministic batch Markdown renderer，但不能改变它的独立输出。

---

### 10.3 不要改变 batch combined schema

本任务是 presentation layer，不是 data model 变更任务。

---

### 10.4 不要让 LLM finding 影响 quality gate

Markdown report 可以展示 LLM severity，但必须明确它是 advisory。

LLM severity 不得影响 deterministic quality gate 或 exit code。

---

### 10.5 注意 partial failure 展示

partial failure report 必须同时保留：

```text
deterministic batch report
succeeded 文件的 LLM advisory findings
failed 文件的 structured error
summary 中的 failed_count / error_count
```

---

### 10.6 注意 Markdown 表格 escaping

LLM 输出可能包含 `|`、换行、多段文本。必须避免破坏 Markdown 表格。

---

### 10.7 不要把 checklist 写入 schema

manual review checklist 是 presentation-only。

不要为了展示 checklist 而修改 `BatchCombinedReviewResult`。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_batch_combined_markdown_report.py
uv run pytest tests/test_llm_batch_combined_result.py
uv run pytest tests/test_llm_finding_adapter.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest
```

如果修改或复用了 batch report 相关测试，也请运行对应测试文件，例如：

```bash
uv run pytest tests/test_batch_markdown_report.py
uv run pytest tests/test_llm_batch_cli_integration.py
```

如果实际项目中相关测试文件名称不同，请运行对应的 batch report / batch LLM / serializer 测试文件。

---

