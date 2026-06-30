# TASK-0080: Add Batch Combined Review Result

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate、LLM sidecar 输出、LLM Markdown report、review index、manual review checklist、artifact examples、LLM-to-core finding adapter、single-file combined review result envelope、single-file combined Markdown renderer，以及 single-file combined CLI output option。

截至 TASK-0079，单文件链路已经形成：

```text
deterministic ReviewResult
LLMReviewResult
LLMCoreFindingCandidate
  ↓
SingleFileCombinedReviewResult
  ↓
combined JSON / combined Markdown
  ↓
explicit single-file CLI output option
```

但 batch 层目前还没有与之对应的 combined result envelope。

当前 batch 侧已有：

```text
BatchReviewResult
Batch LLM result / batch LLM sidecar
batch LLM Markdown report
batch review index
batch partial failure artifact examples
```

本任务是 LLM 合并主程序的第五步：

> 新增 batch combined review result envelope，用于同时携带 deterministic BatchReviewResult、batch LLM result、每个文件的 LLM finding candidates、LLM file status summary、LLM error summary 和 advisory policy。

本任务只新增 batch combined result 数据结构与 JSON-compatible serializer，不接入 batch CLI，不修改 batch 默认输出，不修改 quality gate。

---

## 2. 任务目标

新增 batch combined result envelope。

该结构应能表达：

1. deterministic `BatchReviewResult`；
2. batch LLM result；
3. 每个文件的 LLM execution status；
4. 每个文件的 LLM finding candidates；
5. batch-level LLM status summary；
6. batch-level LLM error summary；
7. LLM advisory policy；
8. deterministic-only quality gate boundary。

推荐新增结构，例如：

```text
BatchCombinedReviewResult
BatchCombinedFileResult
BatchCombinedLLMSummary
BatchCombinedLLMError
```

具体命名可以根据现有代码风格调整。

本任务完成后，项目应能在纯函数层面构造和序列化 batch combined result，但 CLI 暂时不暴露该能力。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增 batch combined result 模块，例如：

   ```text
   src/content_review_engine/llm/batch_combined_result.py
   ```

   或者在现有 `combined_result.py` 中扩展 batch 部分，前提是结构清晰。

2. 新增 batch combined result 数据结构。

3. 新增 batch per-file combined result 数据结构。

4. 新增 batch LLM summary 数据结构。

5. 新增 batch LLM structured error 数据结构。

6. 新增 build helper，例如：

   ```python
   build_batch_combined_review_result(...)
   ```

7. 新增 serializer，例如：

   ```python
   batch_combined_review_result_to_dict(...)
   batch_combined_review_result_to_json(...)
   ```

8. 复用 TASK-0076 的 LLM finding adapter，将每个文件的 `LLMReviewResult` 转换为 `LLMCoreFindingCandidate`。

9. 复用现有 deterministic batch serializer。

10. 复用现有 batch LLM result serializer。

11. 支持 batch partial failure：

```text
部分文件 LLM succeeded
部分文件 LLM failed
部分文件 LLM skipped / not_run
deterministic batch result 仍然完整存在
```

12. 新增测试覆盖 batch success、partial failure、all failed、LLM not_run、LLM skipped、summary counts、error summary、serialization、quality gate boundary、deterministic result 不变。

13. 更新相关文档、PROJECT_STATE.md 和 CHANGELOG.md。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许修改 `BatchReviewResult` schema。

2. 不允许修改单文件 `ReviewResult` schema。

3. 不允许把 LLM findings 写入 deterministic `ReviewResult.findings`。

4. 不允许把 LLM findings 写入 deterministic `BatchReviewResult` 的原始结果列表中。

5. 不允许修改 deterministic batch runner。

6. 不允许修改 deterministic rule engine。

7. 不允许修改 batch CLI 默认输出。

8. 不允许给 batch CLI 新增 `--combined-output`。

9. 不允许修改单文件 CLI 的 0079 行为。

10. 不允许修改 existing `--output`、`--llm-output`、`--format` 语义。

11. 不允许修改 batch Markdown report renderer。

12. 不允许新增 batch combined Markdown renderer。

13. 不允许修改 quality gate 行为。

14. 不允许让 LLM findings 参与 deterministic `severity_counts`、`rule_counts`、quality gate 或 exit code。

15. 不允许接入新的真实 LLM API。

16. 不允许修改 provider contract。

17. 不允许修改 sidecar JSON schema。

18. 不允许让 `examples/llm_review_artifacts/` 成为 runtime dependency。

19. 不允许新增 API、MCP、GUI、Supabase、前端或商业化能力。

20. 不允许把 manual review checklist 持久化进 canonical schema。

---

## 5. 需要修改的文件

预计新增：

```text
src/content_review_engine/llm/batch_combined_result.py
tests/test_llm_batch_combined_result.py
```

预计修改：

```text
src/content_review_engine/llm/__init__.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
PROJECT_STATE.md
CHANGELOG.md
tests/test_llm_provider_usage_docs.py
```

如果现有项目中已经有更适合放置 batch combined result 的模块，可以按现有风格调整，但必须保持：

```text
combined data model 位于 llm / integration 层
report renderer 位于 reports 层
CLI 不承载数据模型逻辑
batch deterministic result 不被污染
```

---

## 6. 实现要求

### 6.1 新增 schema version

新增 batch combined result schema version。

推荐：

```text
batch-combined-review-result.v1
```

建议常量：

```python
BATCH_COMBINED_REVIEW_RESULT_SCHEMA_VERSION = "batch-combined-review-result.v1"
```

要求：

1. schema version 必须出现在数据结构中；
2. schema version 必须出现在 dict serializer 输出中；
3. schema version 需要测试覆盖；
4. 不得复用 single-file combined schema version。

---

### 6.2 新增 BatchCombinedReviewResult

建议结构：

```python
@dataclass(frozen=True)
class BatchCombinedReviewResult:
    schema_version: str
    batch_review_result: BatchReviewResult
    batch_llm_result: Any | None
    files: tuple[BatchCombinedFileResult, ...]
    llm_summary: BatchCombinedLLMSummary
    advisory: bool
```

字段说明：

```text
schema_version
  batch-combined-review-result.v1

batch_review_result
  原始 deterministic BatchReviewResult

batch_llm_result
  原始 batch LLM result；如果 LLM 未运行或跳过，可以为 None

files
  每个文件的 combined LLM 状态与 finding candidates

llm_summary
  batch-level LLM 状态汇总

advisory
  固定为 True
```

要求：

1. `batch_review_result` 必须保留原始 deterministic batch result。
2. `batch_llm_result` 必须保留原始 batch LLM result 或为 `None`。
3. `files` 中每个文件的顺序应尽量与 deterministic batch result 文件顺序一致。
4. `advisory` 必须为 `True`。
5. 不允许修改 deterministic batch result。
6. 不允许把 LLM findings 混入 deterministic batch result。

---

### 6.3 新增 BatchCombinedFileResult

建议结构：

```python
@dataclass(frozen=True)
class BatchCombinedFileResult:
    file: str
    llm_status: str
    llm_error: BatchCombinedLLMError | None
    llm_result: LLMReviewResult | None
    llm_finding_candidates: tuple[LLMCoreFindingCandidate, ...]
    advisory: bool
```

字段说明：

```text
file
  文件路径或文件标识，应与 batch review result / batch LLM result 的文件字段保持一致

llm_status
  not_run / skipped / succeeded / failed

llm_error
  单文件 LLM 错误，失败时存在

llm_result
  单文件 LLMReviewResult，成功时存在

llm_finding_candidates
  由 adapter 生成的候选 findings

advisory
  固定为 True
```

要求：

1. 每个文件都应有一条 `BatchCombinedFileResult`。
2. deterministic-only 文件也应能表达 `not_run` 或 `skipped`。
3. LLM failed 文件的 candidates 必须为空。
4. LLM succeeded 文件的 candidates 来自 adapter。
5. 每个 candidate 必须保留 `source="llm"` 与 `advisory=True`。
6. 不允许在这里新增 deterministic finding。

---

### 6.4 新增 BatchCombinedLLMSummary

建议结构：

```python
@dataclass(frozen=True)
class BatchCombinedLLMSummary:
    total_files: int
    succeeded_count: int
    failed_count: int
    skipped_count: int
    not_run_count: int
    advisory_finding_count: int
    files_with_advisory_findings: int
    error_count: int
```

要求：

1. `total_files` 应等于 combined files 数量。
2. 各 status count 应与 files 中的状态一致。
3. `advisory_finding_count` 汇总所有 LLM candidates。
4. `files_with_advisory_findings` 统计 candidates 非空的文件数。
5. `error_count` 应与 failed files 或 error summary 保持一致。
6. 所有 summary 字段必须有测试覆盖。

---

### 6.5 新增 BatchCombinedLLMError

建议结构：

```python
@dataclass(frozen=True)
class BatchCombinedLLMError:
    type: str
    message: str
    provider: str | None = None
    retryable: bool | None = None
```

要求：

1. 不输出 traceback；
2. 不输出 API key；
3. 不输出 provider raw secret；
4. 不输出环境变量；
5. serializer 中字段稳定；
6. failed 文件必须能携带该 error。

---

### 6.6 LLM status 语义

Batch combined result 应复用 single-file combined result 的 status 语义：

```text
not_run
skipped
succeeded
failed
```

建议语义：

```text
not_run
  没有运行 LLM，也没有显式 skip 或 error。

skipped
  LLM 被显式跳过，例如 batch 未启用 LLM。

succeeded
  当前文件存在成功的 LLMReviewResult。

failed
  当前文件 LLM 执行失败，存在结构化 error。
```

要求：

1. 状态值必须稳定；
2. 不要引入与 single-file 不一致的新状态；
3. 状态应进入 serializer；
4. summary counts 应基于状态生成；
5. status 行为必须有测试覆盖。

---

### 6.7 build helper 要求

新增构建函数，例如：

```python
def build_batch_combined_review_result(
    *,
    batch_review_result: BatchReviewResult,
    batch_llm_result: Any | None = None,
    default_llm_status: str = "not_run",
) -> BatchCombinedReviewResult:
    ...
```

实际参数可根据现有 batch LLM result 类型调整。

要求：

1. 函数必须是纯函数。
2. 不读文件。
3. 不写文件。
4. 不调用 CLI。
5. 不调用 provider。
6. 不读取环境变量。
7. 不读取 examples 目录。
8. 不修改传入的 deterministic batch result。
9. 不修改传入的 batch LLM result。
10. 必须生成完整 `files` 列表。
11. 必须生成 `llm_summary`。
12. 必须支持 batch LLM result 为 `None`。
13. 必须支持 batch partial failure。
14. 必须尽量按 deterministic batch result 的文件顺序输出 files。
15. 如果 batch LLM result 中出现 deterministic result 中不存在的文件，应按保守方式处理，并有测试覆盖或明确文档说明。

---

### 6.8 与现有 batch LLM result 的关系

本任务必须复用现有 batch LLM result 结构。

要求：

1. 不修改 batch LLM sidecar schema。
2. 不重命名现有 batch LLM result 字段。
3. 不复制一份新的 batch LLM execution model。
4. 如果现有 batch LLM result 中已有 file status / error 字段，应直接转换。
5. 如果现有 batch LLM result 中缺少某些字段，应安全降级为 `not_run`、`skipped` 或 `failed`。
6. 文档必须说明 batch combined result 是 integration envelope，不是 batch LLM sidecar 的替代品。

---

### 6.9 serializer 要求

新增：

```python
def batch_combined_review_result_to_dict(
    result: BatchCombinedReviewResult,
) -> dict[str, Any]:
    ...
```

可选新增：

```python
def batch_combined_review_result_to_json(
    result: BatchCombinedReviewResult,
) -> str:
    ...
```

序列化输出建议结构：

```json
{
  "schema_version": "batch-combined-review-result.v1",
  "batch_review_result": {
    "...": "existing deterministic batch result dict"
  },
  "llm": {
    "advisory": true,
    "summary": {
      "total_files": 3,
      "succeeded_count": 2,
      "failed_count": 1,
      "skipped_count": 0,
      "not_run_count": 0,
      "advisory_finding_count": 4,
      "files_with_advisory_findings": 2,
      "error_count": 1
    },
    "result": {
      "...": "existing batch LLM result dict"
    },
    "files": [
      {
        "file": "article-a.md",
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
    ]
  }
}
```

要求：

1. 必须复用 existing deterministic batch serializer。
2. 必须复用 existing batch LLM result serializer。
3. 必须复用 existing LLMReviewResult serializer。
4. 不允许手写重复的完整 deterministic batch serializer。
5. 不允许手写重复的完整 LLM result serializer。
6. 输出必须 JSON-compatible。
7. `llm.advisory` 必须为 `true`。
8. 每个 file 的 `advisory` 必须为 `true`。
9. 每个 candidate 的 `advisory` 必须为 `true`。
10. failed / skipped / not_run 场景下结构也必须稳定。

---

### 6.10 advisory policy 要求

batch combined result 必须明确表达：

```text
LLM findings are advisory.
```

实现要求：

1. `BatchCombinedReviewResult.advisory` 为 `True`。
2. `BatchCombinedFileResult.advisory` 为 `True`。
3. 每个 `LLMCoreFindingCandidate.advisory` 为 `True`。
4. serializer 中 `llm.advisory` 为 `true`。
5. serializer 中每个 file 的 `advisory` 为 `true`。
6. 文档中明确：LLM findings 不参与 deterministic quality gate。
7. 测试中覆盖 advisory policy。

---

### 6.11 quality gate boundary

本任务不得改变 quality gate。

要求：

1. batch deterministic quality gate 仍然只看 deterministic findings。
2. LLM candidates 不参与 deterministic `severity_counts`。
3. LLM candidates 不参与 deterministic `rule_counts`。
4. LLM candidates 不影响 fail-on。
5. LLM candidates 不影响 exit code。
6. 需要测试 combined result 不改变 deterministic batch summary/counts。

---

### 6.12 导出要求

在：

```text
src/content_review_engine/llm/__init__.py
```

中导出新增类型和函数。

建议导出：

```python
BATCH_COMBINED_REVIEW_RESULT_SCHEMA_VERSION
BatchCombinedReviewResult
BatchCombinedFileResult
BatchCombinedLLMSummary
BatchCombinedLLMError
build_batch_combined_review_result
batch_combined_review_result_to_dict
batch_combined_review_result_to_json
```

如果有 helper 仅内部使用，则不必导出。

---

## 7. 测试要求

新增：

```text
tests/test_llm_batch_combined_result.py
```

至少覆盖以下测试。

### 7.1 batch all succeeded

构造 deterministic `BatchReviewResult` 和所有文件成功的 batch LLM result。

验证：

1. schema version 正确；
2. files 数量正确；
3. 每个 file status 是 `succeeded`；
4. 每个 file advisory 是 `True`；
5. LLM candidates 来自 adapter；
6. summary `succeeded_count` 正确；
7. summary `advisory_finding_count` 正确；
8. deterministic batch result 没有被修改。

---

### 7.2 batch partial failure

构造三类文件：

```text
article-a.md -> succeeded
article-b.md -> succeeded
article-with-llm-error.md -> failed
```

验证：

1. failed 文件有 structured error；
2. failed 文件 candidates 为空；
3. succeeded 文件 candidates 正常；
4. summary `failed_count` 正确；
5. summary `succeeded_count` 正确；
6. summary `error_count` 正确；
7. deterministic batch result 仍然完整存在。

---

### 7.3 batch all failed

验证：

1. 所有 file status 是 `failed`；
2. candidates 全为空；
3. error summary 正确；
4. deterministic batch result 仍然完整存在；
5. quality gate 不变。

---

### 7.4 batch LLM not_run

当 `batch_llm_result is None` 且 default status 是 `not_run`：

验证：

1. 每个 file status 是 `not_run`；
2. candidates 为空；
3. errors 为空；
4. summary `not_run_count` 等于 total files；
5. deterministic batch result 被保留。

---

### 7.5 batch LLM skipped

当 default status 是 `skipped`：

验证：

1. 每个 file status 是 `skipped`；
2. summary `skipped_count` 等于 total files；
3. 不调用 provider；
4. deterministic batch result 被保留。

---

### 7.6 serializer structure

验证 `batch_combined_review_result_to_dict(...)` 输出包含：

```text
schema_version
batch_review_result
llm.advisory
llm.summary
llm.result
llm.files
```

并验证每个 file 包含：

```text
file
status
advisory
error
result
finding_candidates
```

---

### 7.7 JSON serializable

验证 dict 输出可以通过：

```python
json.dumps(...)
```

---

### 7.8 sidecar serialization 不变

验证 existing batch LLM result serializer 输出不因本任务改变。

---

### 7.9 deterministic batch serialization 不变

验证 existing batch deterministic serializer 输出不因本任务改变。

---

### 7.10 quality gate 不变

验证：

1. deterministic batch severity counts 不因 LLM candidates 改变；
2. deterministic quality gate / fail-on helper 行为不变；
3. LLM candidate severity 为 `critical` 也不影响 deterministic gate。

---

### 7.11 status ordering / file ordering

验证 files 顺序稳定，优先跟随 deterministic batch result 的文件顺序。

---

### 7.12 no secret leakage

构造 error message 或 provider 字段，确保 serializer 不输出 API key、secret 或 traceback。

---

### 7.13 不调用真实 LLM

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

说明新增 batch combined result envelope 的位置：

```text
BatchReviewResult
Batch LLM result
Per-file LLMReviewResult
LLMCoreFindingCandidate
  ↓
BatchCombinedReviewResult
  ↓
future batch combined Markdown / CLI output
```

必须明确：

1. batch combined result 是 integration envelope；
2. 它不修改 `BatchReviewResult`；
3. 它不修改 per-file `ReviewResult`；
4. 它不修改 batch CLI 默认输出；
5. 它不修改 quality gate；
6. 它不新增 batch combined Markdown renderer；
7. 它为后续 batch combined output 做准备。

---

### 8.2 docs/DATA_MODELS.md

新增 `BatchCombinedReviewResult` 说明。

必须说明：

1. schema version；
2. 字段含义；
3. `batch_review_result` 是 deterministic batch result；
4. `llm.result` 是原始 batch LLM result；
5. `llm.files` 是 per-file LLM integration view；
6. `llm.summary` 是 batch-level LLM summary；
7. `llm.advisory = true`；
8. LLM findings 仍不参与 deterministic counts；
9. LLM findings 仍不参与 quality gate。

---

### 8.3 docs/LLM_PROVIDER_USAGE.md

说明：

1. provider contract 不变；
2. batch provider / runner 仍然产生现有 batch LLM result；
3. batch combined result 是 provider 之后的 integration envelope；
4. sidecar JSON 不变；
5. partial failure 可以被 combined result 表达；
6. deterministic batch result 在 LLM partial failure / all failure 时仍然存在；
7. LLM findings 仍然 advisory。

---

### 8.4 docs/CLI.md

说明：

1. 本任务新增的是 internal batch combined result model；
2. 当前 batch CLI 尚未暴露 `--combined-output`；
3. 不要在文档中声明 batch combined CLI 参数已经可用；
4. 单文件 0079 的 `--combined-output` 行为保持不变；
5. batch combined CLI output 将由后续任务决定。

---

### 8.5 PROJECT_STATE.md

记录 TASK-0080 完成后状态：

```text
Batch combined review result envelope added.
```

同时明确：

```text
Batch combined result is not yet wired into batch CLI output, batch Markdown report, or quality gate behavior.
```

---

### 8.6 CHANGELOG.md

新增 TASK-0080 条目，说明：

1. 新增 batch combined result envelope；
2. 新增 per-file batch combined LLM status；
3. 新增 batch LLM summary；
4. 新增 batch structured error support；
5. 新增 serializer；
6. 复用 adapter；
7. 新增测试；
8. 未改变 batch CLI / batch report / quality gate / provider behavior。

---

## 9. 验收标准

本任务完成后应满足：

1. 新增 batch combined result schema version；
2. 新增 batch combined result 数据结构；
3. 新增 per-file batch combined result 数据结构；
4. 新增 batch LLM summary 数据结构；
5. 新增 batch structured error 数据结构；
6. 新增 build helper；
7. 新增 dict serializer；
8. 可选新增 JSON serializer；
9. 能表达 all succeeded；
10. 能表达 partial failure；
11. 能表达 all failed；
12. 能表达 not_run；
13. 能表达 skipped；
14. 能聚合 status counts；
15. 能聚合 advisory finding count；
16. 能聚合 files with advisory findings；
17. 能聚合 error count；
18. 能复用 LLM finding adapter；
19. 能保留 deterministic batch result；
20. 能保留原始 batch LLM result；
21. serializer 输出 JSON-compatible；
22. 不修改 `BatchReviewResult` schema；
23. 不修改 `ReviewResult` schema；
24. 不把 LLM findings 写入 deterministic findings；
25. 不修改 batch CLI；
26. 不新增 batch CLI 参数；
27. 不新增 batch combined Markdown report；
28. 不修改 quality gate；
29. 不修改 provider contract；
30. 不修改 sidecar JSON；
31. 不接入真实 LLM；
32. 新增测试通过；
33. 全量测试通过；
34. 文档同步更新。

---

## 10. 风险与注意事项

### 10.1 不要提前接入 batch CLI

本任务只做 batch combined result 和 serializer。

不要新增：

```text
content-review batch --combined-output
```

batch CLI 接入留给后续任务。

---

### 10.2 不要提前做 batch combined Markdown report

本任务不做 batch combined Markdown renderer。

后续可以单独做：

```text
TASK-0081: Add Batch Combined Markdown Report
```

---

### 10.3 不要修改 deterministic batch result

`BatchCombinedReviewResult` 是 envelope，不是 `BatchReviewResult` 的替代品。

不要把 LLM findings 塞进 deterministic result。

---

### 10.4 不要影响 quality gate

LLM candidates 即使 severity 为 `critical`，当前仍然是 advisory，不参与 deterministic quality gate。

---

### 10.5 注意 partial failure

batch LLM 的核心复杂度是 partial failure。

本任务必须确保：

```text
deterministic batch result 完整存在
LLM succeeded 文件有 candidates
LLM failed 文件有 structured error
summary 能准确反映状态
```

---

### 10.6 不要读取 examples 作为 runtime dependency

`examples/llm_review_artifacts/` 是 reference-only，不允许成为 build helper 或 serializer 的输入来源。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_batch_combined_result.py
uv run pytest tests/test_llm_finding_adapter.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest
```

如果修改或复用了 batch LLM 相关测试，也请运行：

```bash
uv run pytest tests/test_llm_batch_cli_integration.py
uv run pytest tests/test_llm_batch_report.py
```

如果实际项目中相关测试文件名称不同，请运行对应的 batch LLM / batch report / serializer 测试文件。

---
