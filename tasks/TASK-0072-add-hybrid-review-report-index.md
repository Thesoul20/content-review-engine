# TASK-0072: Add Hybrid Review Report Index

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
10. 批量 LLM Markdown report。

在 TASK-0071 完成后，项目已经可以同时产出多种输出：

```text
deterministic JSON / Markdown output
LLM JSON sidecar
LLM Markdown report
```

这些输出各自职责清晰：

1. deterministic output 是稳定、可复现、可用于 quality gate 的主审计结果；
2. LLM JSON sidecar 是机器可读的 LLM 语义审计结果；
3. LLM Markdown report 是人类可读的 LLM 语义审计报告；
4. LLM findings 目前仍不进入 `ReviewResult` / `BatchReviewResult`；
5. LLM findings 目前仍不参与 quality gate。

但是，对于真实用户来说，同时生成多个文件后，可能不清楚：

1. 应该先看哪个文件；
2. deterministic report 和 LLM report 的关系是什么；
3. 哪个结果是 CI / quality gate 的依据；
4. 哪个结果只是语义建议；
5. batch partial failure 时，整体结果应该如何理解；
6. `--output`、`--llm-output`、`--llm-report` 各自用途是什么。

因此，本任务需要新增一个**混合审计输出索引 / Hybrid Review Report Index**。

本任务的核心不是合并数据模型，也不是把 LLM findings 写入主报告，而是新增一个轻量的 Markdown 索引文件，用来说明本次审计产生了哪些输出、各自用途、关键汇总指标，以及 deterministic 与 LLM 审计结果的解释边界。

---

## 2. 任务目标

新增一个可选的 Markdown index 输出能力：

```bash
content-review review article.md \
  --profile profiles/default.yml \
  --format markdown \
  --output deterministic-report.md \
  --enable-llm \
  --llm-output llm-result.json \
  --llm-report llm-report.md \
  --report-index review-index.md
```

以及：

```bash
content-review batch articles/ \
  --profile profiles/default.yml \
  --recursive \
  --format markdown \
  --output batch-deterministic-report.md \
  --enable-llm \
  --llm-output batch-llm-result.json \
  --llm-report batch-llm-report.md \
  --report-index batch-review-index.md
```

新增的 `--report-index <path>` 用于生成一个 Markdown 索引文件。

该索引文件应回答：

1. 本次审计是单文件还是批量审计；
2. deterministic review 是否完成；
3. LLM review 是否启用；
4. deterministic 输出在哪里；
5. LLM JSON sidecar 在哪里；
6. LLM Markdown report 在哪里；
7. deterministic findings 有多少；
8. LLM findings 有多少；
9. batch 模式下有多少文件成功、多少文件有 findings、多少文件有 LLM error；
10. 哪些输出是 canonical machine-readable data；
11. 哪些输出是 human-readable report；
12. 哪些结果参与 quality gate；
13. 哪些结果只是 advisory semantic review。

本任务必须保持：

1. 不修改 `ReviewResult` schema；
2. 不修改 `BatchReviewResult` schema；
3. 不修改 `LLMReviewResult` schema；
4. 不修改 `LLMSidecarResult` schema；
5. 不修改 deterministic Markdown report；
6. 不修改 LLM Markdown report；
7. 不让 LLM findings 参与 quality gate；
8. 不改变现有 exit code 语义；
9. 不新增真实 LLM provider；
10. 不新增 API / MCP / GUI。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增 hybrid report index renderer；
2. 为单文件 review 生成 Markdown index；
3. 为 batch review 生成 Markdown index；
4. 在 `content-review review` 中新增 `--report-index <path>` 参数；
5. 在 `content-review batch` 中新增 `--report-index <path>` 参数；
6. index 中展示 deterministic output、LLM JSON sidecar、LLM Markdown report 的路径与用途；
7. index 中展示 deterministic summary；
8. index 中展示 LLM summary；
9. index 中说明 deterministic findings 与 LLM findings 的解释边界；
10. index 中说明 quality gate 只基于 deterministic review；
11. batch partial failure 时，index 中展示 LLM partial failure summary；
12. 新增 renderer 单元测试；
13. 新增或更新 CLI 集成测试；
14. 更新 CLI、LLM 使用、架构、数据模型、CI、项目状态和 changelog 文档。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许修改 `ReviewResult` schema；
2. 不允许修改 `BatchReviewResult` schema；
3. 不允许修改 `LLMReviewResult` schema；
4. 不允许修改 `LLMSidecarResult` schema；
5. 不允许把 LLM findings 合并进 deterministic findings；
6. 不允许让 LLM findings 参与 quality gate；
7. 不允许改变 deterministic Markdown report 的结构；
8. 不允许改变 LLM Markdown report 的结构；
9. 不允许改变 deterministic JSON 输出；
10. 不允许改变 LLM JSON sidecar 输出；
11. 不允许改变 batch stdout 输出；
12. 不允许新增 combined full report，将 deterministic report 和 LLM report 全量拼接到一个大文件中；
13. 不允许新增离线 JSON-to-Markdown 转换命令；
14. 不允许新增 API；
15. 不允许新增 MCP；
16. 不允许新增 GUI；
17. 不允许新增 Supabase、用户系统、审计历史或商业化能力；
18. 不允许新增真实 provider 类型；
19. 不允许在测试中调用真实 LLM API；
20. 不允许让 `--report-index` 隐式开启 LLM；
21. 不允许让 `--report-index` 替代 `--llm-output` 或 `--llm-report` 成为 LLM 详细结果输出。

---

## 5. 需要修改的文件

预计新增：

```text
src/content_review_engine/reports/report_index.py
tests/test_report_index.py
```

预计修改：

```text
src/content_review_engine/cli.py
src/content_review_engine/reports/__init__.py
tests/test_cli.py
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

如果当前仓库已经存在更合适的测试文件或 report 模块命名，请保持项目已有风格，但必须覆盖同等测试场景。

---

## 6. 实现要求

### 6.1 新增 report index renderer

新增一个独立渲染模块，例如：

```text
src/content_review_engine/reports/report_index.py
```

建议提供类似函数：

```python
render_single_file_report_index(...)
render_batch_report_index(...)
```

具体签名可以根据现有项目模型调整，但要求：

1. renderer 只负责 Markdown 字符串渲染；
2. renderer 不负责 CLI 参数解析；
3. renderer 不负责文件读取；
4. renderer 不负责 LLM 调用；
5. renderer 不负责 quality gate 判断；
6. renderer 不负责 JSON 序列化；
7. renderer 不改变任何 review result 对象。

### 6.2 单文件 index 内容

单文件 `--report-index` 建议输出结构：

```markdown
# Review Output Index

## Summary

| Field | Value |
| --- | --- |
| Mode | single-file |
| File | article.md |
| Profile | profiles/default.yml |
| Deterministic Review | completed |
| LLM Review | enabled |
| Deterministic Findings | 3 |
| LLM Findings | 2 |
| Quality Gate Source | deterministic review only |

## Output Files

| Output | Path | Format | Purpose | Canonical |
| --- | --- | --- | --- | --- |
| Deterministic Output | deterministic-report.md | markdown | Stable rule-based report | yes |
| LLM JSON Sidecar | llm-result.json | json | Machine-readable LLM result | yes, for LLM layer |
| LLM Markdown Report | llm-report.md | markdown | Human-readable LLM report | no |
| Report Index | review-index.md | markdown | Navigation and interpretation guide | no |

## Interpretation

- Deterministic findings are stable, reproducible, and used by quality gate.
- LLM findings are advisory semantic review results.
- LLM findings do not change deterministic finding counts.
- LLM findings do not participate in fail-on / quality gate decisions.
- Use the deterministic report for CI and hard-rule compliance.
- Use the LLM report for semantic review suggestions.

## Deterministic Review Summary

...

## LLM Review Summary

...
```

如果 LLM 未启用，index 应稳定输出：

```markdown
LLM Review | not enabled
```

并且 LLM output rows 可以显示 `not generated`。

### 6.3 Batch index 内容

Batch `--report-index` 建议输出结构：

```markdown
# Batch Review Output Index

## Summary

| Field | Value |
| --- | --- |
| Mode | batch |
| Input Directory | articles/ |
| Profile | profiles/default.yml |
| Files Reviewed | 10 |
| Files With Deterministic Findings | 3 |
| Deterministic Findings | 12 |
| LLM Review | enabled |
| Files With LLM Findings | 2 |
| Files With LLM Errors | 1 |
| Total LLM Findings | 5 |
| Quality Gate Source | deterministic review only |

## Output Files

| Output | Path | Format | Purpose | Canonical |
| --- | --- | --- | --- | --- |
| Deterministic Output | batch-deterministic-report.md | markdown | Stable batch report | yes |
| LLM JSON Sidecar | batch-llm-result.json | json | Machine-readable batch LLM result | yes, for LLM layer |
| LLM Markdown Report | batch-llm-report.md | markdown | Human-readable LLM batch report | no |
| Report Index | batch-review-index.md | markdown | Navigation and interpretation guide | no |

## Interpretation

- Deterministic batch review remains the source for quality gate decisions.
- LLM batch review is advisory and may have partial failures.
- LLM partial failures are reported separately and do not modify BatchReviewResult.
- Exit codes remain governed by existing CLI behavior.

## Deterministic Review Summary

...

## LLM Review Summary

...

## LLM File Status Summary

| Status | Count |
| --- | ---: |
| success | 9 |
| error | 1 |
```

如果 batch LLM 有 partial failure，index 必须展示：

1. LLM review enabled；
2. files with LLM errors；
3. total LLM findings from successful files；
4. a clear note that detailed per-file errors live in `--llm-report` and/or `--llm-output`；
5. existing exit code behavior remains unchanged.

### 6.4 Markdown 输出稳定性

Report index 必须稳定，不能包含：

1. 当前时间戳；
2. 随机 ID；
3. 绝对路径，除非现有 CLI 文档和测试已经采用绝对路径；
4. 环境相关的非确定性信息；
5. 当前机器用户名；
6. API key 或 secret。

Markdown 表格中的文本必须进行基本转义，至少处理：

1. `|`；
2. 换行；
3. 空值；
4. `None`；
5. 路径中的特殊字符。

### 6.5 CLI 参数行为

为 `content-review review` 新增：

```text
--report-index <path>
```

为 `content-review batch` 新增：

```text
--report-index <path>
```

行为要求：

1. `--report-index` 不要求启用 LLM；
2. LLM 未启用时，index 只展示 deterministic review 信息，并说明 LLM not enabled；
3. LLM 启用时，index 展示 deterministic + LLM 输出关系；
4. `--report-index` 不应隐式开启 LLM；
5. `--report-index` 不应替代 `--llm-output` 或 `--llm-report`；
6. 如果当前规则要求 `--enable-llm` 必须提供 `--llm-output` 或 `--llm-report`，则 `--report-index` 不应满足这个要求；
7. `--report-index` 可以与 `--output` 同时使用；
8. `--report-index` 可以与 `--llm-output` 同时使用；
9. `--report-index` 可以与 `--llm-report` 同时使用；
10. `--report-index` 写入失败时应返回清晰错误；
11. `--report-index` 写入失败不应产生部分损坏文件；
12. 不改变 existing stdout 行为；
13. 不改变 existing deterministic output 行为；
14. 不改变 existing LLM output 行为；
15. 不改变 existing quality gate 行为；
16. 不改变 existing LLM failure exit behavior。

### 6.6 与已有输出的关系

本任务新增的是 index，不是新的 canonical result。

必须明确：

1. deterministic JSON / Markdown output 仍然是 deterministic review 的主输出；
2. LLM JSON sidecar 仍然是 LLM 层的机器可读主输出；
3. LLM Markdown report 仍然是 LLM 层的人类可读报告；
4. report index 只是导航、汇总和解释层；
5. report index 不能被下游程序当作稳定 schema；
6. report index 不应包含所有 detailed findings 的完整复制；
7. detailed findings 应继续放在 deterministic report 和 LLM report 中。

---

## 7. 测试要求

### 7.1 新增 renderer 单元测试

新增 `tests/test_report_index.py`，至少覆盖：

1. single-file deterministic-only index；
2. single-file hybrid index with LLM JSON and LLM Markdown paths；
3. single-file index with deterministic findings and LLM findings counts；
4. single-file index when LLM is not enabled；
5. batch deterministic-only index；
6. batch hybrid index；
7. batch hybrid index with partial LLM failure；
8. batch index with all files no deterministic findings；
9. batch index with all LLM no findings；
10. output file rows contain correct purpose and canonical status；
11. quality gate source always says deterministic review only；
12. Markdown escaping for `|` and newlines；
13. stable output ordering；
14. no timestamp or nondeterministic output.

### 7.2 更新 CLI 测试

更新 `tests/test_cli.py`，至少覆盖：

1. `review` parser supports `--report-index`；
2. `batch` parser supports `--report-index`；
3. `--report-index` does not require `--enable-llm`；
4. `--report-index` does not satisfy `--enable-llm` output-target requirement；
5. `--report-index` can be used with `--output`；
6. `--report-index` can be used with `--llm-output`；
7. `--report-index` can be used with `--llm-report`；
8. `--report-index` write failure returns clear error。

### 7.3 更新单文件 CLI 集成测试

更新 `tests/test_llm_single_file_cli_integration.py` 或对应文件，至少覆盖：

1. single-file deterministic-only `--report-index` writes index；
2. single-file `--enable-llm --llm-output --report-index` writes index；
3. single-file `--enable-llm --llm-report --report-index` writes index；
4. single-file `--enable-llm --llm-output --llm-report --report-index` writes index；
5. index includes deterministic summary；
6. index includes LLM summary；
7. index includes output paths；
8. index states quality gate source is deterministic review only；
9. index write failure returns clear error；
10. tests do not require real network；
11. tests do not require real API key。

### 7.4 更新 batch CLI 集成测试

更新 `tests/test_llm_batch_cli_integration.py` 或对应文件，至少覆盖：

1. batch deterministic-only `--report-index` writes index；
2. batch `--enable-llm --llm-output --report-index` writes index；
3. batch `--enable-llm --llm-report --report-index` writes index；
4. batch `--enable-llm --llm-output --llm-report --report-index` writes index；
5. batch index includes files reviewed；
6. batch index includes deterministic findings summary；
7. batch index includes LLM findings summary；
8. batch index includes LLM partial failure summary；
9. batch partial failure still preserves existing exit code behavior；
10. index write failure returns clear error；
11. deterministic batch output remains unchanged；
12. tests do not require real network；
13. tests do not require real API key。

### 7.5 更新文档断言测试

如果项目已有 docs assertion 测试，例如：

```text
tests/test_llm_provider_usage_docs.py
```

需要同步更新，确保文档中包含：

1. `--report-index`；
2. deterministic output 与 LLM output 的区别；
3. report index 的用途；
4. report index 不是 canonical data model；
5. quality gate 仍只基于 deterministic review；
6. LLM findings 仍不进入 deterministic result。

---

## 8. 文档更新要求

### 8.1 docs/CLI.md

需要补充：

1. `--report-index` 的用途；
2. 单文件用法示例；
3. batch 用法示例；
4. `--output`、`--llm-output`、`--llm-report`、`--report-index` 的区别；
5. `--report-index` 不会隐式开启 LLM；
6. `--report-index` 不替代 `--llm-output` 或 `--llm-report`；
7. `--report-index` 不影响 quality gate；
8. batch partial failure 时 index 如何展示。

### 8.2 docs/LLM_PROVIDER_USAGE.md

需要补充：

1. hybrid output workflow；
2. 推荐真实使用命令；
3. 如何同时生成 deterministic report、LLM JSON、LLM Markdown report、report index；
4. LLM output 与 deterministic output 的解释边界；
5. LLM findings 是 advisory；
6. 测试不需要真实 API key；
7. 手动验证时建议使用小样本 Markdown 文件。

### 8.3 docs/DATA_MODELS.md

需要补充：

1. report index 是展示层；
2. report index 不新增 canonical schema；
3. report index 不替代 `ReviewResult`；
4. report index 不替代 `BatchReviewResult`；
5. report index 不替代 `LLMReviewResult`；
6. report index 不替代 `LLMSidecarResult`；
7. machine-readable 输出仍应使用 JSON。

### 8.4 docs/ARCHITECTURE.md

需要补充：

1. report index renderer 所在层级；
2. report index 与 deterministic report renderer 的关系；
3. report index 与 LLM Markdown renderer 的关系；
4. report index 不负责审计；
5. report index 不负责 provider；
6. report index 不负责 quality gate；
7. CLI 如何组装 index 所需的 summary 信息。

### 8.5 docs/CI.md

需要补充：

1. `--report-index` 可用于 CI artifact navigation；
2. `--report-index` 不影响 CI pass/fail；
3. CI 质量门禁仍由 deterministic review / fail-on 控制；
4. LLM findings 不参与 CI gate；
5. LLM partial failure 的 exit code 仍遵循现有 CLI 行为。

### 8.6 PROJECT_STATE.md

需要记录：

1. TASK-0072 完成后新增 hybrid report index；
2. 当前已有 deterministic report、LLM JSON、LLM Markdown report、report index；
3. LLM findings 仍未合并进主 ReviewResult；
4. quality gate 仍未接纳 LLM findings；
5. API / MCP / GUI 仍未开始。

### 8.7 CHANGELOG.md

新增 TASK-0072 条目，说明：

1. 新增 `--report-index`；
2. 新增 hybrid review report index renderer；
3. 支持 single-file 与 batch；
4. 支持 deterministic-only 与 hybrid LLM 模式；
5. 不改变任何 canonical schema；
6. 不改变 quality gate。

---

## 9. 验收标准

本任务完成后，应满足以下标准：

1. `content-review review --report-index <path>` 可以生成 deterministic-only index；
2. `content-review batch --report-index <path>` 可以生成 deterministic-only index；
3. `content-review review --enable-llm --llm-output <path> --report-index <path>` 可以生成 hybrid index；
4. `content-review review --enable-llm --llm-report <path> --report-index <path>` 可以生成 hybrid index；
5. `content-review batch --enable-llm --llm-output <path> --report-index <path>` 可以生成 hybrid index；
6. `content-review batch --enable-llm --llm-report <path> --report-index <path>` 可以生成 hybrid index；
7. index 中包含 deterministic summary；
8. index 中包含 LLM summary；
9. index 中包含 output file path / purpose / canonical status；
10. index 中明确 quality gate source 是 deterministic review only；
11. batch partial failure 时 index 中展示 LLM error summary；
12. `--report-index` 不隐式开启 LLM；
13. `--report-index` 不替代 `--llm-output` 或 `--llm-report`；
14. `--report-index` 不改变 deterministic output；
15. `--report-index` 不改变 LLM output；
16. `--report-index` 不改变 quality gate；
17. 不修改 `ReviewResult` / `BatchReviewResult` / `LLMReviewResult` / `LLMSidecarResult` schema；
18. 所有新增测试通过；
19. `uv run pytest` 全量通过；
20. 文档已同步更新。

---

## 10. 风险与注意事项

1. 不要把 report index 做成 full combined report；
2. 不要复制所有 detailed findings 到 index；
3. 不要让 index 变成新的 canonical schema；
4. 不要让 index 影响 quality gate；
5. 不要让 index 影响 exit code；
6. 不要让 index 隐式开启 LLM；
7. 不要让 index 替代 LLM JSON 或 LLM Markdown report；
8. 不要修改 deterministic report renderer 的既有输出；
9. 不要修改 LLM Markdown report renderer 的既有输出；
10. 不要在测试中调用真实 LLM；
11. 不要在 index 中输出 secret、API key、环境变量值；
12. 不要加入时间戳，避免测试不稳定；
13. 不要使用绝对路径，除非项目现有测试已采用绝对路径；
14. 不要扩大到 API / MCP / GUI；
15. 不要将本任务扩展为真实 provider 验证任务。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_report_index.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_single_file_cli_integration.py
uv run pytest tests/test_llm_batch_cli_integration.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest
```

如果某些测试文件在当前仓库中不存在，请根据实际文件名调整，但必须覆盖同等测试范围。

---
