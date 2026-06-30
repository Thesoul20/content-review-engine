# TASK-0078: Add Single-File Combined Markdown Report

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate、LLM sidecar 输出、LLM Markdown report、review index、manual review checklist、artifact examples、LLM-to-core finding adapter，以及 single-file combined review result envelope。

截至 TASK-0077，项目已经存在单文件组合结果结构：

```text
ReviewResult
LLMReviewResult
LLMCoreFindingCandidate
  ↓
SingleFileCombinedReviewResult
```

`SingleFileCombinedReviewResult` 可以同时携带：

1. deterministic `ReviewResult`；
2. raw `LLMReviewResult`；
3. adapter 生成的 `LLMCoreFindingCandidate`；
4. LLM execution status；
5. advisory policy；
6. structured LLM error。

但是目前这个 combined result 还没有对应的人类可读 Markdown 展示层。

本任务是 LLM 合并主程序的第三步：

> 新增 single-file combined Markdown report renderer，用于把 `SingleFileCombinedReviewResult` 渲染为人类可读 Markdown 报告，但暂时不改变 CLI 默认输出、batch 行为或 quality gate 行为。

本任务只增加一个可测试、可复用的 report rendering 层，不把它接入 CLI 默认路径。

---

## 2. 任务目标

新增一个单文件 combined Markdown report renderer。

该 renderer 应能够从 `SingleFileCombinedReviewResult` 生成 Markdown 文本，清晰展示：

1. deterministic review summary；
2. deterministic findings；
3. LLM execution status；
4. LLM advisory policy；
5. LLM finding candidates；
6. LLM error；
7. manual review guidance；
8. quality gate 边界说明。

本任务完成后，项目应存在类似函数：

```python
render_single_file_combined_markdown_report(...)
```

或根据现有命名风格采用类似名称。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增 single-file combined Markdown report renderer 模块，例如：

   ```text
   src/content_review_engine/reports/combined_markdown.py
   ```

   或者根据项目现有结构选择更合适的文件名。

2. 新增渲染函数，例如：

   ```python
   render_single_file_combined_markdown_report(
       result: SingleFileCombinedReviewResult,
   ) -> str
   ```

3. 复用现有 deterministic Markdown report renderer，避免重复实现 deterministic report 的全部渲染逻辑。

4. 复用现有 LLM Markdown report / helper，如果已有可用函数适合复用。

5. 为 LLM finding candidates 新增 Markdown 表格或列表展示。

6. 展示 LLM status：

   ```text
   not_run
   skipped
   succeeded
   failed
   ```

7. 展示 advisory policy：

   ```text
   LLM findings are advisory and do not affect deterministic quality gate behavior.
   ```

8. failed 状态下展示结构化 LLM error。

9. not_run / skipped 状态下展示清晰说明，不输出空洞或误导性的 LLM findings 表格。

10. 新增测试覆盖 succeeded、not_run、skipped、failed、LLM candidates 表格、advisory policy、quality gate boundary、deterministic report 内容保留、Markdown escaping。

11. 更新相关文档，说明 combined Markdown report 是 presentation layer，不改变 CLI 默认输出和 quality gate。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许修改主 `ReviewResult` schema。

2. 不允许把 LLM findings 写入 `ReviewResult.findings`。

3. 不允许修改 `SingleFileCombinedReviewResult` 的核心 schema，除非发现 0077 中存在明显 bug，且必须保持兼容。

4. 不允许修改 deterministic review runner。

5. 不允许修改 deterministic rule engine 行为。

6. 不允许修改 `content-review review` 默认输出。

7. 不允许新增 CLI 参数。

8. 不允许修改现有 CLI 参数语义。

9. 不允许把 combined Markdown report 接入 CLI 默认路径。

10. 不允许修改 batch result schema。

11. 不允许修改 batch LLM 行为。

12. 不允许新增 batch combined Markdown report。

13. 不允许修改 quality gate 行为。

14. 不允许让 LLM findings 参与 deterministic `severity_counts`、`rule_counts`、quality gate 或 exit code。

15. 不允许接入真实 LLM API。

16. 不允许修改 provider contract。

17. 不允许修改 sidecar JSON schema。

18. 不允许让 `examples/llm_review_artifacts/` 成为 runtime dependency。

19. 不允许新增 API、MCP、GUI、Supabase、前端或商业化能力。

20. 不允许把 manual review checklist 持久化进 schema。

---

## 5. 需要修改的文件

预计新增：

```text
src/content_review_engine/reports/combined_markdown.py
tests/test_llm_single_file_combined_markdown_report.py
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

如果现有项目已有更合适的 report 模块命名，可以按现有代码风格调整，但必须保持：

```text
combined result model 位于 llm 层
combined markdown renderer 位于 reports 层
CLI 不直接承载 renderer 逻辑
```

---

## 6. 实现要求

### 6.1 Renderer 函数

新增渲染函数，例如：

```python
def render_single_file_combined_markdown_report(
    result: SingleFileCombinedReviewResult,
) -> str:
    ...
```

要求：

1. 输入 `SingleFileCombinedReviewResult`。
2. 输出 Markdown 字符串。
3. 函数必须是纯函数。
4. 不读文件。
5. 不写文件。
6. 不调用 CLI。
7. 不调用 provider。
8. 不读取环境变量。
9. 不读取 examples 目录。
10. 不改变传入的 result。
11. 输出稳定、可测试。
12. 输出结尾建议保留单个换行符。

---

### 6.2 推荐 Markdown 结构

建议输出结构如下：

```md
# Combined Content Review Report

## Summary

| Field | Value |
| --- | --- |
| File | ... |
| Profile | ... |
| Deterministic Findings | ... |
| LLM Status | succeeded |
| LLM Advisory Findings | ... |
| Quality Gate Scope | deterministic-only |

## Deterministic Review

<existing deterministic markdown report or deterministic summary/findings section>

## LLM Review

### LLM Execution

| Field | Value |
| --- | --- |
| Status | succeeded |
| Advisory | yes |
| Error | none |

### LLM Advisory Findings

| Severity | Rule | Location | Message | Suggestion |
| --- | --- | --- | --- | --- |
| warning | llm.misleading_claim | 3:1 | ... | ... |

## Manual Review Workflow

- Review deterministic findings first.
- Review LLM advisory findings as semantic suggestions.
- Confirm or reject each LLM advisory finding manually.
- Do not treat LLM findings as deterministic quality gate failures unless a future explicit policy enables that behavior.

## Quality Gate Boundary

LLM findings are advisory and do not affect deterministic quality gate behavior in this report.
```

可根据现有报告风格调整标题和表格列，但必须包含以下信息：

1. deterministic review 内容；
2. LLM status；
3. advisory policy；
4. LLM finding candidates；
5. failed 状态下的 error；
6. quality gate deterministic-only 说明；
7. manual review workflow。

---

### 6.3 Deterministic report 复用要求

如果项目已有函数，例如：

```python
render_markdown_report(...)
```

或类似 deterministic Markdown renderer，本任务应尽量复用它。

要求：

1. 不要复制粘贴 deterministic report 的完整渲染逻辑。
2. 如果直接嵌入 existing deterministic report，需要避免重复顶级标题造成混乱。
3. 如果现有 renderer 不方便嵌入，可以提取轻量 helper，但不得大规模重构 report 系统。
4. 不允许改变现有 deterministic Markdown report 的输出。

---

### 6.4 LLM finding candidates 展示要求

LLM candidate 表格至少包含：

```text
Severity
Rule
Location
Message
Suggestion
```

建议包含：

```text
Matched Text
Category
Context
```

但不要让表格过宽到不可读。如果现有 LLM report 已经有稳定展示方式，可以复用或保持风格一致。

要求：

1. 所有 LLM finding candidates 必须显示为 advisory。
2. rule id 应显示 `llm.` 前缀。
3. severity 可以显示 canonical severity。
4. location 应从 `line` / `column` 生成。
5. 无 location 时显示 `-`。
6. 无 suggestion 时显示 `-`。
7. 无 matched_text / context 时显示 `-` 或省略。
8. 表格内容必须做 Markdown escaping，避免 `|` 破坏表格。

---

### 6.5 LLM status 展示要求

#### succeeded

如果 `llm_status == "succeeded"`：

1. 显示 LLM status 为 `succeeded`。
2. 显示 advisory finding 数量。
3. 如果 candidates 非空，渲染 findings 表格。
4. 如果 candidates 为空，显示：

   ```text
   No LLM advisory findings.
   ```

#### not_run

如果 `llm_status == "not_run"`：

1. 显示 LLM status 为 `not_run`。
2. 不渲染空 findings 表格。
3. 显示：

   ```text
   LLM review was not run for this result.
   ```

#### skipped

如果 `llm_status == "skipped"`：

1. 显示 LLM status 为 `skipped`。
2. 不渲染空 findings 表格。
3. 显示：

   ```text
   LLM review was skipped.
   ```

#### failed

如果 `llm_status == "failed"`：

1. 显示 LLM status 为 `failed`。
2. 显示 LLM error 表格。
3. 不渲染 advisory findings 表格，或明确显示 no advisory findings due to LLM failure。
4. 明确 deterministic review result 仍然有效。
5. 明确 quality gate 仍然 deterministic-only。

---

### 6.6 LLM error 展示要求

failed 状态下展示结构化 error。

建议表格：

```md
| Field | Value |
| --- | --- |
| Type | provider_error |
| Message | ... |
| Provider | openai |
| Retryable | true |
```

要求：

1. 不输出 secret/API key。
2. 如果 error 字段为空，显示 `-`。
3. message 需要 Markdown escaping。
4. 不要输出 Python traceback。
5. 不要输出环境变量或 provider raw config。

---

### 6.7 Manual Review Workflow 展示要求

combined Markdown report 必须包含 manual review workflow。

推荐内容：

```md
## Manual Review Workflow

1. Review deterministic findings first.
2. Review LLM advisory findings as semantic suggestions.
3. Confirm, reject, or rewrite each LLM advisory finding manually.
4. Treat LLM findings as presentation-only unless a future explicit policy enables enforcement.
```

要求：

1. 明确 LLM findings 是 advisory。
2. 明确 checklist/workflow 是 presentation-only。
3. 不把 manual review workflow 写回 schema。
4. 不影响 quality gate。

---

### 6.8 Quality Gate Boundary 展示要求

combined Markdown report 必须包含 quality gate 边界说明。

推荐内容：

```md
## Quality Gate Boundary

LLM findings are advisory in this report. They do not affect deterministic severity counts, rule counts, quality gate decisions, or CLI exit codes.
```

要求：

1. 必须提到 deterministic-only。
2. 必须提到 LLM findings 不影响 quality gate。
3. 必须提到不影响 exit code。
4. 该说明必须有测试覆盖。

---

### 6.9 Markdown escaping 要求

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

### 6.10 导出要求

在：

```text
src/content_review_engine/reports/__init__.py
```

中导出新增 renderer。

建议导出：

```python
render_single_file_combined_markdown_report
```

如果新增 helper 是内部函数，不必导出。

---

## 7. 测试要求

新增：

```text
tests/test_llm_single_file_combined_markdown_report.py
```

至少覆盖以下测试。

### 7.1 succeeded 状态渲染

构造一个 deterministic `ReviewResult` 和一个带 LLM findings 的 `SingleFileCombinedReviewResult`。

验证输出包含：

1. `# Combined Content Review Report`；
2. `## Summary`；
3. `## Deterministic Review`；
4. `## LLM Review`；
5. `succeeded`；
6. `llm.` rule id；
7. LLM finding message；
8. LLM finding suggestion；
9. `advisory`；
10. `deterministic-only`。

---

### 7.2 succeeded 但无 LLM finding

验证输出包含：

```text
No LLM advisory findings.
```

并且不输出误导性的 failure/error 内容。

---

### 7.3 not_run 状态渲染

验证输出包含：

```text
LLM review was not run
```

并且不输出空 LLM findings 表格。

---

### 7.4 skipped 状态渲染

验证输出包含：

```text
LLM review was skipped
```

并且不输出空 LLM findings 表格。

---

### 7.5 failed 状态渲染

构造 `SingleFileCombinedReviewResult`，其中 `llm_status == "failed"` 且有 `llm_error`。

验证输出包含：

1. `failed`；
2. error type；
3. error message；
4. provider；
5. retryable；
6. deterministic review result 仍然存在；
7. quality gate deterministic-only；
8. 不输出 fake LLM findings。

---

### 7.6 deterministic report 内容保留

验证 combined Markdown report 中包含 deterministic result 的关键内容，例如：

1. deterministic finding message；
2. deterministic rule id；
3. deterministic severity；
4. file/profile 信息。

同时验证现有 deterministic renderer 的独立输出没有被修改。

---

### 7.7 Markdown escaping

构造 LLM finding，其中 message / suggestion / matched_text 包含：

```text
|
换行
```

验证 Markdown 表格没有被破坏。

---

### 7.8 advisory policy

验证输出明确包含：

```text
LLM findings are advisory
```

或等价文案。

---

### 7.9 quality gate boundary

验证输出明确包含：

```text
do not affect deterministic quality gate
```

或等价文案。

---

### 7.10 不改变 CLI / provider / sidecar

如适合，增加测试或断言，确保：

1. CLI 默认测试不需要更新；
2. provider usage docs 测试通过；
3. sidecar JSON serialization 不变；
4. combined Markdown renderer 不调用 provider。

---

### 7.11 不调用真实 LLM

测试不得依赖：

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
真实网络
真实 PydanticAI provider
真实模型响应
```

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

说明新增 single-file combined Markdown report rendering 层：

```text
SingleFileCombinedReviewResult
  ↓
single-file combined Markdown renderer
  ↓
future CLI/report integration
```

必须明确：

1. renderer 是 presentation layer；
2. renderer 不修改 combined result；
3. renderer 不修改 deterministic ReviewResult；
4. renderer 不修改 CLI 默认输出；
5. renderer 不修改 quality gate；
6. renderer 不处理 batch。

---

### 8.2 docs/DATA_MODELS.md

说明本任务没有新增 canonical schema。

必须明确：

1. `SingleFileCombinedReviewResult` schema 不变；
2. Markdown report 是 presentation output；
3. manual review workflow 不持久化；
4. quality gate boundary 只是展示说明，不是执行策略变更。

---

### 8.3 docs/LLM_PROVIDER_USAGE.md

说明：

1. provider contract 不变；
2. provider 不知道 combined Markdown renderer；
3. renderer 消费的是 `SingleFileCombinedReviewResult`；
4. sidecar JSON 不变；
5. LLM findings 仍然 advisory；
6. failed 状态可在 report 中展示，但不影响 deterministic review result。

---

### 8.4 docs/CLI.md

说明：

1. single-file combined Markdown renderer 已存在；
2. 当前不改变 CLI 默认行为；
3. 如果当前 CLI 尚未暴露该 renderer，则标注为 internal/report integration building block；
4. 后续任务会决定是否通过 CLI 输出 combined Markdown report。

不要在 docs/CLI.md 中声明尚未实现的 CLI 参数。

---

### 8.5 PROJECT_STATE.md

记录 TASK-0078 完成后状态：

```text
Single-file combined Markdown report renderer added.
```

同时明确：

```text
The renderer is not yet wired into CLI default output, batch output, or quality gate behavior.
```

---

### 8.6 CHANGELOG.md

新增 TASK-0078 条目，说明：

1. 新增 single-file combined Markdown renderer；
2. 展示 deterministic review + LLM advisory findings；
3. 展示 LLM status / error；
4. 展示 manual review workflow；
5. 展示 quality gate boundary；
6. 新增测试；
7. 未改变 CLI / batch / quality gate / provider behavior。

---

## 9. 验收标准

本任务完成后应满足：

1. 新增 single-file combined Markdown renderer；
2. renderer 输入 `SingleFileCombinedReviewResult`；
3. renderer 输出稳定 Markdown；
4. succeeded 状态可以展示 LLM advisory findings；
5. succeeded 无 findings 时有清晰空状态文案；
6. not_run 状态有清晰说明；
7. skipped 状态有清晰说明；
8. failed 状态可以展示结构化 LLM error；
9. report 中包含 deterministic review 内容；
10. report 中包含 manual review workflow；
11. report 中包含 quality gate boundary；
12. report 明确 LLM findings are advisory；
13. Markdown table 内容做 escaping；
14. 不修改 `ReviewResult` schema；
15. 不修改 `ReviewResult.findings`；
16. 不修改 `SingleFileCombinedReviewResult` 核心语义；
17. 不修改 CLI 默认输出；
18. 不新增 CLI 参数；
19. 不修改 batch result；
20. 不新增 batch combined report；
21. 不修改 quality gate；
22. 不修改 provider contract；
23. 不修改 sidecar JSON；
24. 不接入真实 LLM；
25. 新增测试通过；
26. 全量测试通过；
27. 文档同步更新。

---

## 10. 风险与注意事项

### 10.1 不要提前接入 CLI

本任务只新增 renderer。

即使 renderer 可以生成 Markdown，也不要让 `content-review review --format markdown` 默认输出 combined Markdown report。

CLI 接入留给后续任务。

---

### 10.2 不要提前处理 batch

本任务只处理 single-file。

Batch combined result 和 batch combined Markdown report 留给后续任务。

---

### 10.3 不要改变 deterministic report

可以复用 deterministic Markdown renderer，但不能改变它的独立输出。

现有 deterministic Markdown report 测试不应该因为本任务发生变化。

---

### 10.4 不要让 LLM finding 影响 quality gate

Markdown report 可以展示 LLM severity，但必须明确它是 advisory。

LLM severity 不得影响 deterministic quality gate 或 exit code。

---

### 10.5 注意 Markdown 表格 escaping

LLM 输出可能包含 `|`、换行、多段文本。必须避免破坏 Markdown 表格。

---

### 10.6 不要把 manual review workflow 写入 schema

manual review workflow 是 presentation-only。

不要为了展示 checklist 而修改 combined result schema。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_single_file_combined_markdown_report.py
uv run pytest tests/test_llm_single_file_combined_result.py
uv run pytest tests/test_llm_finding_adapter.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest
```

如果修改了其它相关测试，也请运行对应测试文件。

---

