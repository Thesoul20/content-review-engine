# TASK-0077: Add Single-File Combined Review Result

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate、LLM sidecar 输出、LLM Markdown report、review index、manual review checklist、artifact examples，以及 LLM-to-core finding adapter。

截至 TASK-0076，项目已经新增：

```text
LLMReviewResult
  ↓
LLM finding adapter
  ↓
LLMCoreFindingCandidate
```

`LLMCoreFindingCandidate` 已经可以把 LLM findings 规范化为后续主程序可理解的候选 finding，并且明确标记：

```text
source = "llm"
advisory = true
```

但目前 LLM findings 还没有进入单文件主审计结果的组合结构中。

本任务是 LLM 合并主程序的第二步：

> 新增单文件 combined review result envelope，用于同时携带 deterministic ReviewResult、LLMReviewResult、LLMCoreFindingCandidate，以及 LLM execution status，但暂时不改变 CLI 默认输出、Markdown 主报告、batch result 或 quality gate 行为。

本任务的目标不是把 LLM finding 直接塞进 `ReviewResult.findings`，而是先建立一个稳定、可序列化、可测试的单文件组合结果结构，为后续 CLI / report / batch 合并做准备。

---

## 2. 任务目标

新增一个单文件 combined review result 数据结构，用于表达：

```text
deterministic ReviewResult
LLMReviewResult
LLMCoreFindingCandidate list
LLM execution status
LLM advisory policy
```

本任务完成后，项目中应该存在一个稳定的单文件组合 envelope，例如：

```text
SingleFileCombinedReviewResult
```

或根据现有命名风格采用类似名称。

这个结构应支持序列化为 dict / JSON-compatible object，但本任务不要求 CLI 默认输出它。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增单文件 combined result 模块，例如：

   ```text
   src/content_review_engine/llm/combined_result.py
   ```

   或者使用项目中更合适的模块名。

2. 新增单文件 combined result 数据结构，例如：

   ```text
   SingleFileCombinedReviewResult
   SingleFileLLMIntegrationStatus
   ```

3. 新增构建函数，例如：

   ```python
   build_single_file_combined_review_result(...)
   ```

4. 新增序列化函数，例如：

   ```python
   single_file_combined_review_result_to_dict(...)
   ```

5. 使用 TASK-0076 的 adapter，把 `LLMReviewResult` 转换为 `LLMCoreFindingCandidate`。

6. 在 combined result 中保留 deterministic `ReviewResult`，但不修改它。

7. 在 combined result 中保留原始 `LLMReviewResult`，但不修改它。

8. 在 combined result 中明确记录 LLM findings 是 advisory。

9. 在 combined result 中明确记录 LLM 是否成功、失败、跳过或未运行。

10. 新增测试覆盖 combined result 构建、序列化、LLM success、LLM failure、LLM skipped、advisory policy、deterministic result 不变、quality gate 不变。

11. 更新相关文档，说明该结构是单文件 LLM 合并主程序的准备层，而不是 CLI 默认行为变更。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许修改主 `ReviewResult` schema。

2. 不允许把 LLM findings 写入 `ReviewResult.findings`。

3. 不允许修改 deterministic review runner。

4. 不允许修改 deterministic rule engine 行为。

5. 不允许修改 `content-review review` 默认输出。

6. 不允许新增 CLI 参数。

7. 不允许修改现有 CLI 参数语义。

8. 不允许修改 Markdown 主报告 renderer。

9. 不允许把 LLM findings 合并进主 Markdown report。

10. 不允许修改 batch result schema。

11. 不允许修改 batch LLM 行为。

12. 不允许修改 quality gate 行为。

13. 不允许让 LLM findings 参与 deterministic `severity_counts`、`rule_counts`、quality gate 或 exit code。

14. 不允许接入真实 LLM API。

15. 不允许修改 provider contract。

16. 不允许修改 sidecar JSON schema。

17. 不允许新增 API、MCP、GUI、Supabase、前端或商业化能力。

18. 不允许让 `examples/llm_review_artifacts/` 成为 runtime dependency。

19. 不允许把 manual review checklist 持久化进 combined result。

---

## 5. 需要修改的文件

预计新增：

```text
src/content_review_engine/llm/combined_result.py
tests/test_llm_single_file_combined_result.py
```

预计修改：

```text
src/content_review_engine/llm/__init__.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果现有项目中已有更合适的文件名或模块位置，可以根据现有结构调整，但必须保持分层清晰，不得把 combined result 逻辑塞进 CLI、report renderer 或 deterministic core engine。

---

## 6. 实现要求

### 6.1 新增 combined result 数据结构

建议新增一个单文件 combined result envelope。

示例结构如下：

```python
@dataclass(frozen=True)
class SingleFileCombinedReviewResult:
    schema_version: str
    review_result: ReviewResult
    llm_result: LLMReviewResult | None
    llm_finding_candidates: tuple[LLMCoreFindingCandidate, ...]
    llm_status: str
    llm_error: dict[str, Any] | None
    advisory: bool
```

如果项目中已有 schema version 常量风格，应遵守现有风格。

推荐 schema version：

```text
single-file-combined-review-result.v1
```

要求：

1. `review_result` 必须保留原始 deterministic `ReviewResult`。
2. `llm_result` 可以为 `None`，用于表示 LLM 未运行或跳过。
3. `llm_finding_candidates` 来自 TASK-0076 adapter。
4. `llm_status` 必须是稳定枚举值或受控字符串。
5. `advisory` 必须为 `True`。
6. 不允许在该结构中修改 `review_result.findings`。
7. 不允许把 LLM finding 混入 deterministic finding list。
8. 不允许让该结构改变任何 runtime 行为。

---

### 6.2 LLM status 语义

需要定义稳定的 LLM status。

推荐取值：

```text
not_run
skipped
succeeded
failed
```

建议语义：

```text
not_run
  表示调用方没有提供 LLMReviewResult，也没有显式错误。

skipped
  表示 LLM 被显式跳过，例如用户未启用 LLM 或配置不满足。

succeeded
  表示 LLMReviewResult 存在，并且没有执行错误。

failed
  表示 LLM 执行失败，combined result 中应保留结构化错误信息。
```

如果现有 LLM sidecar 已经有 status 命名，应优先复用现有命名，避免新旧不一致。

---

### 6.3 LLM error 表达

如果 LLM 执行失败，combined result 应支持携带结构化错误。

建议字段：

```python
llm_error: dict[str, Any] | None
```

错误信息至少可以表达：

```text
type
message
provider
retryable
```

但本任务不要求新增新的 error hierarchy，也不要求修改现有 provider error。

要求：

1. failed 状态下允许 `llm_result is None`。
2. failed 状态下 `llm_finding_candidates` 应为空。
3. failed 状态下 deterministic `review_result` 仍然存在。
4. failed 状态不影响 deterministic quality gate。
5. error dict 不应包含 secret、API key 或原始敏感配置。

---

### 6.4 构建函数要求

新增构建函数，例如：

```python
def build_single_file_combined_review_result(
    *,
    review_result: ReviewResult,
    llm_result: LLMReviewResult | None = None,
    llm_status: str | None = None,
    llm_error: dict[str, Any] | None = None,
) -> SingleFileCombinedReviewResult:
    ...
```

要求：

1. 函数必须是纯函数。
2. 不读文件。
3. 不写文件。
4. 不调用 CLI。
5. 不调用 provider。
6. 不读取环境变量。
7. 不读取 examples 目录。
8. 如果 `llm_result` 存在且没有显式失败，应生成 `llm_finding_candidates`。
9. 如果 `llm_result is None` 且无错误，应支持 `not_run` 或 `skipped` 状态。
10. 如果 `llm_error` 存在，应支持 `failed` 状态。
11. 不修改传入的 `review_result`。
12. 不修改传入的 `llm_result`。

---

### 6.5 序列化要求

新增序列化函数，例如：

```python
def single_file_combined_review_result_to_dict(
    result: SingleFileCombinedReviewResult,
) -> dict[str, Any]:
    ...
```

序列化输出建议结构：

```json
{
  "schema_version": "single-file-combined-review-result.v1",
  "review_result": {
    "...": "existing deterministic review result dict"
  },
  "llm": {
    "status": "succeeded",
    "advisory": true,
    "error": null,
    "result": {
      "...": "existing LLMReviewResult dict"
    },
    "finding_candidates": [
      {
        "source": "llm",
        "advisory": true,
        "rule_id": "llm.misleading_claim",
        "severity": "warning",
        "message": "...",
        "suggestion": "...",
        "line": 3,
        "column": 1,
        "matched_text": "...",
        "context": "...",
        "category": "...",
        "original_llm_rule_id": "misleading_claim",
        "original_index": 0
      }
    ]
  }
}
```

要求：

1. 必须复用现有 deterministic `ReviewResult` serializer。
2. 必须复用现有 `LLMReviewResult` serializer。
3. 不允许手写重复的完整 review result serialization 逻辑。
4. 输出必须 JSON-compatible。
5. 输出中必须明确 `llm.advisory = true`。
6. 输出中必须明确 `llm.status`。
7. 输出中必须包含 `llm.finding_candidates`。
8. 失败或跳过场景下输出也必须结构稳定。

---

### 6.6 Advisory policy 要求

combined result 必须明确表达：

```text
LLM findings are advisory.
```

实现层面要求：

1. `SingleFileCombinedReviewResult.advisory` 为 `True`。
2. 序列化输出中 `llm.advisory` 为 `true`。
3. 每个 `LLMCoreFindingCandidate.advisory` 为 `True`。
4. 文档中明确：本任务不让 LLM findings 参与 quality gate。
5. 测试中覆盖 advisory policy。

---

### 6.7 导出要求

在：

```text
src/content_review_engine/llm/__init__.py
```

中导出新增类型和函数。

建议导出：

```python
SINGLE_FILE_COMBINED_REVIEW_RESULT_SCHEMA_VERSION
SingleFileCombinedReviewResult
build_single_file_combined_review_result
single_file_combined_review_result_to_dict
```

如果有 status 常量或枚举，也应按现有风格导出。

---

## 7. 测试要求

新增：

```text
tests/test_llm_single_file_combined_result.py
```

至少覆盖以下测试。

### 7.1 succeeded 状态

构造一个 deterministic `ReviewResult` 和一个带 findings 的 `LLMReviewResult`。

验证：

1. `schema_version` 正确；
2. `llm_status == "succeeded"`；
3. `llm_result` 被保留；
4. `llm_finding_candidates` 数量正确；
5. candidate 来自 adapter；
6. candidate `source == "llm"`；
7. candidate `advisory is True`；
8. deterministic `review_result.findings` 没有被修改。

---

### 7.2 not_run 状态

构造只有 deterministic `ReviewResult` 的 combined result。

验证：

1. `llm_status == "not_run"` 或项目选定的等价状态；
2. `llm_result is None`；
3. `llm_finding_candidates` 为空；
4. `llm_error is None`；
5. deterministic result 被保留。

---

### 7.3 skipped 状态

显式构造 skipped 状态。

验证：

1. `llm_status == "skipped"`；
2. `llm_result is None`；
3. candidate 为空；
4. deterministic result 被保留；
5. quality gate 语义不变。

---

### 7.4 failed 状态

构造 deterministic `ReviewResult` 和结构化 `llm_error`。

验证：

1. `llm_status == "failed"`；
2. `llm_error` 被保留；
3. `llm_result is None`；
4. `llm_finding_candidates` 为空；
5. deterministic result 被保留；
6. 错误中不包含 secret/API key。

---

### 7.5 序列化结构

验证 `single_file_combined_review_result_to_dict(...)` 输出包含：

```text
schema_version
review_result
llm.status
llm.advisory
llm.error
llm.result
llm.finding_candidates
```

并验证输出可以 JSON 序列化。

---

### 7.6 不改变 deterministic result serialization

验证 existing `review_result_to_dict(...)` 输出不因本任务变化。

---

### 7.7 不改变 sidecar serialization

验证 existing `llm_review_result_to_dict(...)` 输出不因本任务变化。

---

### 7.8 不改变 quality gate

如果项目已有 quality gate helper，测试应验证：

1. deterministic quality gate 输入仍然只看 deterministic result；
2. combined result 不会被 quality gate 自动消费；
3. LLM candidate 的 severity 不会影响 exit code。

如果不适合直接测试 exit code，至少在单元测试中明确验证 combined result 没有修改 deterministic result 的 severity counts。

---

### 7.9 不调用真实 LLM

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
PROJECT_STATE.md
CHANGELOG.md
```

### 8.1 docs/ARCHITECTURE.md

说明新增单文件 combined result envelope 的位置：

```text
ReviewResult
LLMReviewResult
LLMCoreFindingCandidate
  ↓
SingleFileCombinedReviewResult
  ↓
future CLI / report integration
```

必须明确：

1. combined result 是 envelope；
2. 它不修改 `ReviewResult`；
3. 它不修改 CLI 默认行为；
4. 它不修改 report renderer；
5. 它不修改 quality gate；
6. 它只为后续主程序合并做准备。

---

### 8.2 docs/DATA_MODELS.md

新增 `SingleFileCombinedReviewResult` 说明。

必须说明：

1. schema version；
2. 字段含义；
3. `review_result` 是 deterministic result；
4. `llm.result` 是原始 LLMReviewResult；
5. `llm.finding_candidates` 是 adapter 输出；
6. `llm.advisory = true`；
7. LLM findings 仍不参与 deterministic counts；
8. LLM findings 仍不参与 quality gate。

---

### 8.3 docs/LLM_PROVIDER_USAGE.md

说明：

1. provider contract 仍然返回 `LLMReviewResult`；
2. combined result 是 provider 之后的 integration envelope；
3. provider 不需要知道 combined result；
4. sidecar JSON 不变；
5. CLI 行为不变；
6. 失败状态下 deterministic review result 仍可存在。

---

### 8.4 PROJECT_STATE.md

记录 TASK-0077 完成后状态：

```text
Single-file combined review result envelope added.
```

同时明确：

```text
LLM findings are still not merged into ReviewResult.findings, Markdown main report, batch result, quality gate, or CLI default output.
```

---

### 8.5 CHANGELOG.md

新增 TASK-0077 条目，说明：

1. 新增 single-file combined result；
2. 新增 LLM status 表达；
3. 新增 combined result serialization；
4. 复用 LLM finding adapter；
5. 新增测试；
6. 未改变 CLI / report / quality gate / provider behavior。

---

## 9. 验收标准

本任务完成后应满足：

1. 新增 single-file combined result 数据结构；
2. 新增 schema version；
3. 新增 build helper；
4. 新增 serialization helper；
5. 能同时携带 deterministic `ReviewResult` 和 `LLMReviewResult`；
6. 能携带 `LLMCoreFindingCandidate` list；
7. 能表达 `not_run`、`skipped`、`succeeded`、`failed` 状态；
8. failed 状态可以携带结构化 error；
9. advisory policy 明确存在；
10. 序列化输出 JSON-compatible；
11. 不修改主 `ReviewResult` schema；
12. 不修改 `ReviewResult.findings`；
13. 不修改 CLI 默认行为；
14. 不修改 Markdown 主报告；
15. 不修改 batch result；
16. 不修改 quality gate；
17. 不修改 provider contract；
18. 不修改 sidecar JSON；
19. 不接入真实 LLM；
20. 新增测试通过；
21. 全量测试通过；
22. 文档同步更新。

---

## 10. 风险与注意事项

### 10.1 不要把 envelope 当成主 schema 替代品

`SingleFileCombinedReviewResult` 是 integration envelope，不是当前主 `ReviewResult` 的替代品。

本任务不要删除、替换或重命名现有 `ReviewResult`。

---

### 10.2 不要提前修改 CLI

即使 combined result 已经可以序列化，本任务也不要让 `content-review review` 默认输出它。

CLI 接入应留给后续任务。

---

### 10.3 不要提前修改 report

本任务不修改 Markdown 主报告。

LLM findings 如何展示在主 report 中，留给后续 TASK-0078。

---

### 10.4 不要提前修改 batch

本任务只处理 single-file combined result。

Batch combined result 留给后续任务。

---

### 10.5 不要让 LLM severity 影响 quality gate

即使 LLM candidate 的 severity 是 `error` 或 `critical`，当前仍然是 advisory，不参与 quality gate。

---

### 10.6 不要重复实现 serializer

必须复用已有 deterministic result serializer 和 LLM result serializer。

不要复制粘贴一套新的 review result serialization 逻辑。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_single_file_combined_result.py
uv run pytest tests/test_llm_finding_adapter.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest
```

如果修改了其它相关测试，也请运行对应测试文件。

---

