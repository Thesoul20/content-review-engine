# TASK-0082: Add Batch Combined CLI Output Option

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate、LLM sidecar 输出、LLM Markdown report、review index、manual review checklist、artifact examples、LLM-to-core finding adapter、single-file combined result、single-file combined Markdown report、single-file combined CLI output、batch combined result，以及 batch combined Markdown report。

截至 TASK-0081，batch 层已经具备完整的 internal combined 链路：

```text
BatchReviewResult
Batch LLM result
Per-file LLMReviewResult
LLMCoreFindingCandidate
  ↓
BatchCombinedReviewResult
  ↓
render_batch_combined_markdown_report(...)
```

但目前 batch combined JSON / Markdown 还没有通过 CLI 暴露给用户。

本任务是 LLM 合并主程序的第七步：

> 给 `content-review batch` 增加显式 opt-in 的 batch combined output 入口，让用户可以主动输出 batch combined JSON 或 Markdown，但不改变 batch 默认输出、不改变 deterministic quality gate、不改变 batch LLM sidecar 行为。

---

## 2. 任务目标

为 batch 命令新增显式 combined output 能力。

目标行为：

```bash
content-review batch input_dir --profile profile.yml \
  --enable-llm \
  --combined-output batch-combined-report.md \
  --combined-output-format markdown
```

或：

```bash
content-review batch input_dir --profile profile.yml \
  --enable-llm \
  --combined-output batch-combined-result.json \
  --combined-output-format json
```

本任务完成后，用户可以主动生成：

1. batch combined Markdown report；
2. batch combined JSON result。

但以下行为必须保持不变：

1. `content-review batch` 默认输出不变；
2. existing `--format` 行为不变；
3. existing `--output` 行为不变；
4. existing batch `--llm-output` 行为不变；
5. batch deterministic quality gate 行为不变；
6. batch CLI exit code 行为不变；
7. 单文件 `content-review review` 的 TASK-0079 行为不变。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 修改 batch CLI 命令 `content-review batch`，新增显式 opt-in 参数：

   ```text
   --combined-output PATH
   --combined-output-format {json,markdown}
   ```

2. 仅当用户显式传入 `--combined-output` 时，写出 batch combined output 文件。

3. 当 `--combined-output-format markdown` 时，使用 TASK-0081 的 renderer：

   ```python
   render_batch_combined_markdown_report(...)
   ```

4. 当 `--combined-output-format json` 时，使用 TASK-0080 的 serializer：

   ```python
   batch_combined_review_result_to_dict(...)
   ```

   或现有 JSON helper：

   ```python
   batch_combined_review_result_to_json(...)
   ```

5. 在 batch CLI 路径中构造：

   ```python
   BatchCombinedReviewResult
   ```

6. 复用现有 deterministic `BatchReviewResult`。

7. 复用现有 batch LLM sidecar result。

8. 复用现有 batch LLM error / partial failure 语义。

9. 支持以下状态：

   ```text
   succeeded
   failed
   skipped
   not_run
   partial_failure
   ```

   其中 `partial_failure` 可以作为 report-level summary 状态展示，不一定作为 per-file status。

10. 当用户没有启用 LLM，但仍传入 `--combined-output` 时，允许输出 batch combined result，并将每个文件的 LLM 状态记录为 `not_run` 或 `skipped`，具体以现有语义为准。

11. 新增 batch CLI 测试，覆盖 combined Markdown 输出、combined JSON 输出、LLM disabled 状态、partial failure、all failed、默认行为不变、quality gate 不变、`--output` / `--llm-output` / `--combined-output` 并存。

12. 更新 CLI 文档和相关架构 / 数据模型 / LLM 使用文档。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许修改 `BatchReviewResult` schema。

2. 不允许修改 `ReviewResult` schema。

3. 不允许修改 `BatchCombinedReviewResult` schema，除非发现 TASK-0080 中存在明显 bug，且必须保持兼容。

4. 不允许把 LLM findings 写入 deterministic `ReviewResult.findings`。

5. 不允许把 LLM findings 写入 deterministic `BatchReviewResult`。

6. 不允许修改 deterministic batch runner。

7. 不允许修改 deterministic rule engine。

8. 不允许修改 `content-review batch` 默认输出。

9. 不允许改变 existing `--format` 语义。

10. 不允许改变 existing `--output` 语义。

11. 不允许改变 existing batch `--llm-output` 语义。

12. 不允许让 `--combined-output` 替代 `--output`。

13. 不允许让 `--combined-output` 替代 `--llm-output`。

14. 不允许修改单文件 `content-review review` 的 combined output 行为。

15. 不允许修改 existing batch Markdown report 默认输出。

16. 不允许修改 quality gate 行为。

17. 不允许让 LLM findings 参与 deterministic `severity_counts`、`rule_counts`、quality gate、fail-on 或 exit code。

18. 不允许接入新的真实 LLM API。

19. 不允许修改 provider contract。

20. 不允许修改 sidecar JSON schema。

21. 不允许让 `examples/llm_review_artifacts/` 成为 runtime dependency。

22. 不允许新增 API、MCP、GUI、Supabase、前端或商业化能力。

23. 不允许把 manual review checklist 持久化进 canonical schema。

---

## 5. 需要修改的文件

预计修改：

```text
src/content_review_engine/cli.py
docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
PROJECT_STATE.md
CHANGELOG.md
tests/test_llm_provider_usage_docs.py
```

预计新增：

```text
tests/test_llm_batch_combined_cli_output.py
```

如果现有 batch CLI 测试文件更适合扩展，也可以直接扩展现有测试，但必须保证 batch combined CLI 输出路径有明确覆盖。

---

## 6. 实现要求

### 6.1 CLI 参数设计

在 batch 命令中新增：

```text
--combined-output PATH
```

用于指定 batch combined output 写出路径。

新增：

```text
--combined-output-format {json,markdown}
```

用于指定输出格式。

推荐默认值：

```text
markdown
```

也就是说：

```bash
content-review batch input_dir --profile profile.yml \
  --combined-output batch-combined.md
```

默认写出 Markdown。

如果单文件 `review` 命令中已经有同名参数，应尽量保持 batch 命令参数语义一致。

---

### 6.2 默认行为不变

如果用户没有传入：

```text
--combined-output
```

则 batch CLI 行为必须与 TASK-0081 之前完全一致。

必须保持：

1. stdout 行为不变；
2. `--output` 行为不变；
3. `--format` 行为不变；
4. batch `--llm-output` 行为不变；
5. exit code 行为不变；
6. quality gate 行为不变。

---

### 6.3 combined output 触发条件

只有当用户显式传入：

```text
--combined-output
```

时，才写出 batch combined output。

示例：

```bash
content-review batch input_dir --profile profile.yml \
  --enable-llm \
  --combined-output batch-combined.md
```

应生成 batch combined Markdown。

示例：

```bash
content-review batch input_dir --profile profile.yml \
  --enable-llm \
  --combined-output batch-combined.json \
  --combined-output-format json
```

应生成 batch combined JSON。

---

### 6.4 LLM enabled 且全部成功

当用户传入：

```text
--enable-llm
```

并且 batch LLM 全部文件执行成功时：

1. existing deterministic batch review 正常运行；

2. existing batch LLM review 正常运行；

3. existing `--llm-output` 行为不变；

4. 构造 `BatchCombinedReviewResult`；

5. per-file status 应为：

   ```text
   succeeded
   ```

6. combined output 中应包含 LLM finding candidates；

7. combined output 中应包含 batch LLM summary；

8. combined output 中应明确 advisory policy；

9. quality gate 仍然只看 deterministic result。

---

### 6.5 LLM partial failure

当 batch LLM 出现 partial failure 时：

1. deterministic batch result 仍然完整存在；
2. succeeded 文件应包含 LLM finding candidates；
3. failed 文件应包含 structured error；
4. failed 文件的 candidates 应为空；
5. batch combined summary 应正确展示 failed count / error count；
6. combined Markdown 应展示 LLM Error Summary；
7. combined JSON 应包含 per-file error；
8. existing batch LLM sidecar 行为不变；
9. deterministic quality gate 不受影响。

---

### 6.6 LLM all failed

当 batch LLM 全部文件失败时：

1. deterministic batch result 仍然完整存在；
2. 所有 combined file status 为 `failed`；
3. 所有 candidates 为空；
4. error summary 正确；
5. combined output 可以写出；
6. existing CLI failure / exit code 语义不被本任务改变；
7. 不吞掉现有 LLM failure 语义；
8. 不泄漏 secret / traceback。

---

### 6.7 LLM disabled

当用户没有传入：

```text
--enable-llm
```

但传入了：

```text
--combined-output
```

时，不应该强制调用 LLM。

推荐行为：

1. deterministic batch review 正常运行；

2. 不调用 LLM provider；

3. 不读取 API key；

4. 不访问网络；

5. 构造 `BatchCombinedReviewResult`；

6. 每个文件 status 使用：

   ```text
   not_run
   ```

   或者如果现有语义更适合，则使用：

   ```text
   skipped
   ```

7. combined Markdown 中应显示：

   ```text
   LLM review was not run.
   ```

   或等价说明。

8. combined JSON 中应包含稳定的 `llm.summary` 和 `llm.files`。

要求：

1. 不要因为 `--combined-output` 自动启用 LLM；
2. 不要因为缺少 `--enable-llm` 报错；
3. 不要创建 reviewer；
4. 不要调用 provider。

---

### 6.8 combined Markdown 输出

当：

```text
--combined-output-format markdown
```

时，必须使用：

```python
render_batch_combined_markdown_report(...)
```

要求：

1. 不要在 CLI 中手写 Markdown。
2. 不要复制 batch combined Markdown renderer 逻辑。
3. 输出文件应为 UTF-8 文本。
4. 输出内容应以单个换行结尾。
5. 路径处理应与现有 `--output` 风格保持一致。
6. 不要单独引入不一致的父目录创建行为。

---

### 6.9 combined JSON 输出

当：

```text
--combined-output-format json
```

时，必须使用：

```python
batch_combined_review_result_to_dict(...)
```

或：

```python
batch_combined_review_result_to_json(...)
```

要求：

1. 不要在 CLI 中手写 combined JSON schema。
2. 输出必须 JSON-compatible。
3. JSON 格式缩进应遵守项目现有 JSON 输出风格。
4. 输出文件应为 UTF-8 文本。
5. 不要修改 existing deterministic batch serializer。
6. 不要修改 existing batch LLM sidecar serializer。

---

### 6.10 与 `--llm-output` 的关系

本任务必须保持 batch `--llm-output` 行为不变。

如果用户同时传入：

```text
--llm-output batch-llm-result.json
--combined-output batch-combined.md
```

则应该同时写出：

1. existing raw batch LLM result sidecar；
2. new batch combined output。

要求：

1. `--llm-output` 仍然只写 raw batch LLM result；
2. `--combined-output` 写 batch combined envelope / report；
3. 二者不能互相覆盖；
4. 二者文件路径相同的情况，可以遵守现有 output conflict 处理风格；如果项目没有冲突处理，至少测试不要使用同一路径。

---

### 6.11 与 `--output` 的关系

本任务必须保持 batch `--output` 行为不变。

如果用户同时传入：

```text
--output batch-deterministic-report.md
--llm-output batch-llm-result.json
--combined-output batch-combined-report.md
```

则应该同时写出：

1. existing deterministic batch output；
2. existing raw batch LLM sidecar；
3. new batch combined output。

要求：

1. `--output` 仍然写原本的 deterministic batch result/report；
2. `--combined-output` 写 batch combined result/report；
3. 不要让 combined output 替代 deterministic output；
4. 不要改变 stdout 逻辑。

---

### 6.12 与 quality gate 的关系

本任务不得改变 quality gate。

要求：

1. batch `--fail-on` 仍然只基于 deterministic findings；
2. LLM advisory candidates 不参与 `severity_counts`；
3. LLM advisory candidates 不参与 `rule_counts`；
4. LLM advisory candidates 不影响 exit code；
5. combined report 中可以展示 LLM severity，但必须保持 advisory；
6. 测试必须覆盖 LLM finding severity 不影响 batch exit code。

---

### 6.13 错误与 secret 处理

combined output 中的 error 信息不得泄漏 secret。

要求：

1. 不输出 API key；
2. 不输出完整环境变量；
3. 不输出 provider raw secret；
4. 不输出 Python traceback；
5. 如果复用现有 redaction helper，应保持一致；
6. 测试应覆盖 no secret leakage。

---

## 7. 测试要求

新增或更新 batch CLI 测试，建议新增：

```text
tests/test_llm_batch_combined_cli_output.py
```

至少覆盖以下场景。

### 7.1 batch combined Markdown 输出

运行类似：

```bash
content-review batch input_dir --profile profile.yml \
  --enable-llm \
  --combined-output batch-combined.md \
  --combined-output-format markdown
```

验证：

1. 命令成功；

2. `batch-combined.md` 存在；

3. 内容包含：

   ```text
   # Batch Combined Content Review Report
   ```

4. 内容包含 deterministic batch review 内容；

5. 内容包含 LLM summary；

6. 内容包含 file status summary；

7. 内容包含 advisory policy；

8. 内容包含 quality gate boundary；

9. 默认 deterministic batch 输出行为不变。

---

### 7.2 batch combined JSON 输出

运行类似：

```bash
content-review batch input_dir --profile profile.yml \
  --enable-llm \
  --combined-output batch-combined.json \
  --combined-output-format json
```

验证：

1. 命令成功；

2. `batch-combined.json` 存在；

3. JSON 可解析；

4. 顶层包含：

   ```text
   schema_version
   batch_review_result
   llm
   ```

5. `llm.advisory == true`；

6. `llm.summary` 存在；

7. `llm.files` 存在；

8. raw batch sidecar schema 不变。

---

### 7.3 LLM disabled with batch combined output

运行类似：

```bash
content-review batch input_dir --profile profile.yml \
  --combined-output batch-combined.md
```

验证：

1. 命令成功；
2. 不调用 LLM provider；
3. batch combined output 存在；
4. per-file status 为 `not_run` 或 `skipped`；
5. summary 中 not_run / skipped count 正确；
6. Markdown 中说明 LLM review 未运行或被跳过；
7. deterministic batch result 正常。

---

### 7.4 batch partial failure combined output

用 mock provider 或现有测试机制模拟 partial failure。

验证：

1. deterministic batch review 仍然完成；
2. batch combined output 存在；
3. succeeded 文件有 LLM candidates；
4. failed 文件有 structured error；
5. failed 文件没有 fake candidates；
6. summary 中 failed_count / error_count 正确；
7. quality gate 行为不变。

---

### 7.5 batch all failed combined output

用 mock provider 或现有测试机制模拟所有文件 LLM 失败。

验证：

1. deterministic batch review 仍然完成；
2. combined output 存在；
3. 所有 files status 为 failed；
4. error summary 完整；
5. advisory findings 为空；
6. 不泄漏 secret / traceback；
7. existing CLI failure / exit code 语义不被本任务改变。

---

### 7.6 同时输出 deterministic output、batch LLM sidecar 和 batch combined output

运行类似：

```bash
content-review batch input_dir --profile profile.yml \
  --enable-llm \
  --format markdown \
  --output batch-deterministic.md \
  --llm-output batch-llm-result.json \
  --combined-output batch-combined.md
```

验证：

1. `batch-deterministic.md` 存在；
2. `batch-llm-result.json` 存在；
3. `batch-combined.md` 存在；
4. 三者内容职责不同；
5. deterministic output 没有变成 combined output；
6. LLM sidecar 没有变成 combined output。

---

### 7.7 quality gate 不变

构造 LLM finding severity 为 `error` 或 `critical`，但 deterministic findings 不触发 fail-on。

验证：

1. CLI exit code 不因 LLM candidate 失败；
2. `--fail-on` 仍然基于 deterministic findings；
3. combined report 明确 deterministic-only。

---

### 7.8 默认 batch 行为不变

运行现有 batch 命令，不传：

```text
--combined-output
```

验证：

1. stdout 与现有预期一致；
2. `--output` 与现有预期一致；
3. 不生成 combined output；
4. existing tests 不需要大规模重写。

---

### 7.9 invalid combined output format

运行：

```bash
content-review batch input_dir --profile profile.yml \
  --combined-output batch-combined.txt \
  --combined-output-format invalid
```

验证 CLI 给出清晰错误。

如果 CLI 框架已经自动处理 choices，则测试对应行为即可。

---

### 7.10 不调用真实 LLM

测试不得依赖：

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
真实网络
真实 PydanticAI provider
真实模型响应
```

必须使用项目现有 mock / test provider 机制。

---

## 8. 文档更新要求

需要更新：

```text
docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
PROJECT_STATE.md
CHANGELOG.md
```

### 8.1 docs/CLI.md

新增 batch combined output 使用说明。

必须包含：

1. batch `--combined-output`；
2. batch `--combined-output-format json|markdown`；
3. Markdown 示例；
4. JSON 示例；
5. 与 batch `--output` 的区别；
6. 与 batch `--llm-output` 的区别；
7. 说明该功能是 explicit opt-in；
8. 说明 batch 默认输出不变；
9. 说明 quality gate 仍然 deterministic-only；
10. 说明单文件 `review` 的 combined output 行为不变。

示例：

```bash
content-review batch input_dir --profile profile.yml \
  --enable-llm \
  --combined-output batch-combined-report.md \
  --combined-output-format markdown
```

---

### 8.2 docs/ARCHITECTURE.md

说明 batch CLI 集成位置：

```text
BatchReviewResult
Batch LLM result
BatchCombinedReviewResult
  ↓
batch combined JSON / batch combined Markdown
  ↓
explicit batch CLI output option
```

必须明确：

1. CLI 只是显式输出入口；
2. batch 默认 CLI 行为不变；
3. quality gate 不变；
4. combined output 不替代 deterministic output；
5. combined output 不替代 batch LLM sidecar。

---

### 8.3 docs/DATA_MODELS.md

说明本任务没有改变 canonical schema。

必须明确：

1. batch combined JSON 使用 `BatchCombinedReviewResult` envelope；
2. deterministic `BatchReviewResult` 仍然是 deterministic audit record；
3. LLM findings 仍然是 advisory candidates；
4. LLM findings 不参与 deterministic counts；
5. LLM findings 不参与 quality gate；
6. manual review checklist 不持久化。

---

### 8.4 docs/LLM_PROVIDER_USAGE.md

说明：

1. provider contract 不变；
2. batch `--combined-output` 使用 provider 之后的 batch LLM result；
3. raw batch `--llm-output` 仍然可用；
4. combined output 可与 raw batch LLM sidecar 同时写出；
5. LLM disabled 时不会因为 combined output 自动调用 provider；
6. LLM partial failure / all failed 时 combined output 可以记录 error；
7. deterministic batch result 仍然有效。

---

### 8.5 PROJECT_STATE.md

记录 TASK-0082 完成后状态：

```text
Batch combined CLI output option added as explicit opt-in.
```

同时明确：

```text
Default batch CLI output, BatchReviewResult schema, ReviewResult schema, and quality gate behavior remain unchanged.
```

---

### 8.6 CHANGELOG.md

新增 TASK-0082 条目，说明：

1. 新增 batch `--combined-output`；
2. 新增 batch `--combined-output-format json|markdown`；
3. 支持 batch combined JSON output；
4. 支持 batch combined Markdown output；
5. 可与 batch `--output` / `--llm-output` 并存；
6. 支持 partial failure 展示；
7. 不改变 batch 默认 CLI 行为；
8. 不改变 quality gate；
9. 新增测试。

---

## 9. 验收标准

本任务完成后应满足：

1. `content-review batch` 新增 `--combined-output`；
2. `content-review batch` 新增 `--combined-output-format json|markdown`；
3. 不传 `--combined-output` 时 batch 默认行为完全不变；
4. batch combined Markdown 输出使用 `render_batch_combined_markdown_report(...)`；
5. batch combined JSON 输出使用 `batch_combined_review_result_to_dict(...)` 或 `batch_combined_review_result_to_json(...)`；
6. LLM enabled 且成功时，combined output 包含 per-file LLM advisory findings；
7. LLM disabled 时，combined output 不会自动调用 LLM；
8. LLM partial failure 时，combined output 可以记录 succeeded findings 和 failed errors；
9. LLM all failed 时，combined output 可以记录 structured errors；
10. batch `--output` 行为不变；
11. batch `--llm-output` 行为不变；
12. batch `--output`、`--llm-output`、`--combined-output` 可以并存；
13. 单文件 `review` 行为不变；
14. `BatchReviewResult` schema 不变；
15. `ReviewResult` schema 不变；
16. deterministic findings 不包含 LLM findings；
17. quality gate 不变；
18. LLM advisory candidates 不影响 exit code；
19. provider contract 不变；
20. sidecar JSON schema 不变；
21. 不接入新的真实 LLM API；
22. 不读取 examples 目录作为 runtime dependency；
23. 新增测试通过；
24. 全量测试通过；
25. 文档同步更新。

---

## 10. 风险与注意事项

### 10.1 不要改变 batch 默认输出

这是本任务最大的边界。

只有显式传入：

```text
--combined-output
```

才允许生成 batch combined output。

---

### 10.2 不要让 combined output 替代 deterministic output

`--output` 和 `--combined-output` 是两个不同概念。

```text
--output
  原有 deterministic batch output

--combined-output
  新增 batch combined output
```

不要改变 `--output` 的语义。

---

### 10.3 不要让 combined output 替代 batch LLM sidecar

`--llm-output` 和 `--combined-output` 是两个不同概念。

```text
--llm-output
  原始 batch LLM sidecar result

--combined-output
  deterministic + batch LLM integration envelope/report
```

不要改变 `--llm-output` 的语义。

---

### 10.4 不要自动启用 LLM

用户传入 `--combined-output` 不代表用户同意调用 LLM。

LLM 调用仍应由现有 `--enable-llm` 控制。

---

### 10.5 不要影响 quality gate

即使 combined output 中展示了 LLM `error` 或 `critical`，也不能改变 deterministic quality gate 和 exit code。

---

### 10.6 不要重写 renderer / serializer

CLI 只负责调度。

Markdown 必须复用：

```python
render_batch_combined_markdown_report(...)
```

JSON 必须复用：

```python
batch_combined_review_result_to_dict(...)
```

或：

```python
batch_combined_review_result_to_json(...)
```

不要把 Markdown 或 JSON schema 直接写在 CLI 中。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_batch_combined_cli_output.py
uv run pytest tests/test_llm_batch_combined_markdown_report.py
uv run pytest tests/test_llm_batch_combined_result.py
uv run pytest tests/test_llm_batch_cli_integration.py
uv run pytest tests/test_batch_markdown_report.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest
```

如果修改或扩展了其它 CLI 测试，也请运行对应测试文件，例如：

```bash
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_single_file_combined_cli_output.py
```

---

