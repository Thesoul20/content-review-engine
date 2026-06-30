# TASK-0083: Consolidate Combined LLM Output Documentation and Compatibility

## 1. 背景

当前项目已经完成了从 LLM finding adapter 到 single-file / batch combined output 的主链路。

截至 TASK-0082，项目已经具备：

```text
LLMReviewResult
  ↓
LLMCoreFindingCandidate
  ↓
SingleFileCombinedReviewResult
  ↓
single-file combined JSON / Markdown
  ↓
content-review review --combined-output

Batch LLM result
  ↓
BatchCombinedReviewResult
  ↓
batch combined JSON / Markdown
  ↓
content-review batch --combined-output
```

这意味着 LLM 审计结果已经可以通过显式 opt-in 的方式合并到单文件和批量审计输出中。

但是 0076～0082 连续引入了多个新概念：

```text
LLMCoreFindingCandidate
SingleFileCombinedReviewResult
SingleFileCombined Markdown report
single-file --combined-output
BatchCombinedReviewResult
BatchCombined Markdown report
batch --combined-output
```

现在需要一个收口任务，统一整理：

1. single-file / batch combined output 的文档；
2. CLI 参数行为矩阵；
3. artifact examples；
4. compatibility boundary；
5. quality gate boundary；
6. advisory policy；
7. docs 测试断言；
8. 示例文件是否过期；
9. README / ARCHITECTURE / DATA_MODELS / CLI / LLM_PROVIDER_USAGE 是否一致。

本任务是 LLM combined output 阶段的整理任务：

> 统一 single-file 和 batch combined output 的文档、示例和兼容性说明，确保 0076～0082 的新增能力在用户视角、开发者视角和测试视角上保持一致。

本任务不新增运行时能力。

---

## 2. 任务目标

本任务目标是完成一次 combined LLM output 的文档与兼容性收口。

完成后，项目文档中应清楚回答以下问题：

1. `--output`、`--llm-output`、`--combined-output` 分别是什么；
2. single-file 和 batch 是否都支持 `--combined-output`；
3. combined output 支持哪些格式；
4. combined output 是否会自动启用 LLM；
5. LLM disabled 时 combined output 如何表达；
6. LLM failed / partial failure 时 combined output 如何表达；
7. LLM findings 是否进入 `ReviewResult.findings`；
8. LLM findings 是否影响 severity counts / rule counts；
9. LLM findings 是否影响 quality gate / exit code；
10. raw LLM sidecar 和 combined output 的区别是什么；
11. deterministic output 和 combined output 的区别是什么；
12. examples 目录中的 artifact 是否能反映当前实现。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 更新 `docs/CLI.md`，统一 single-file / batch combined output 用法。

2. 更新 `docs/ARCHITECTURE.md`，整理 combined output 在整体架构中的位置。

3. 更新 `docs/DATA_MODELS.md`，整理 combined result schema、candidate、advisory policy 的关系。

4. 更新 `docs/LLM_PROVIDER_USAGE.md`，整理 provider、sidecar、combined envelope、combined report 的边界。

5. 更新 `docs/CI.md`，说明 combined output 与 quality gate / exit code 的关系。

6. 更新 `examples/llm_review_artifacts/`，补充或刷新 single-file / batch combined output 示例。

7. 如果当前 examples 缺少 combined artifact，可以新增：

   ```text
   examples/llm_review_artifacts/single-file/combined-result.json
   examples/llm_review_artifacts/single-file/combined-report.md
   examples/llm_review_artifacts/batch/batch-combined-result.json
   examples/llm_review_artifacts/batch/batch-combined-report.md
   ```

8. 更新 `examples/llm_review_artifacts/README.md`，增加 combined artifact map。

9. 新增或更新 docs / examples 测试，确保文档中提到的 combined output 参数和示例文件存在。

10. 新增或更新 compatibility 测试，确保默认行为、schema boundary、quality gate boundary 的说明没有漂移。

11. 更新 `PROJECT_STATE.md`，记录 combined output 阶段已经完成并进入文档收口状态。

12. 更新 `CHANGELOG.md`，记录 TASK-0083。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许新增 CLI 参数。

2. 不允许修改现有 CLI 参数语义。

3. 不允许修改 `content-review review` 默认输出。

4. 不允许修改 `content-review batch` 默认输出。

5. 不允许修改 `--output` 行为。

6. 不允许修改 `--llm-output` 行为。

7. 不允许修改 `--combined-output` 行为。

8. 不允许修改 `--combined-output-format` 行为。

9. 不允许修改 `ReviewResult` schema。

10. 不允许修改 `BatchReviewResult` schema。

11. 不允许修改 `SingleFileCombinedReviewResult` schema。

12. 不允许修改 `BatchCombinedReviewResult` schema。

13. 不允许把 LLM findings 写入 deterministic findings。

14. 不允许修改 deterministic runner。

15. 不允许修改 rule engine。

16. 不允许修改 quality gate 行为。

17. 不允许让 LLM findings 参与 severity counts、rule counts、fail-on、quality gate 或 exit code。

18. 不允许修改 provider contract。

19. 不允许修改 sidecar JSON schema。

20. 不允许接入新的真实 LLM API。

21. 不允许新增 API、MCP、GUI、Supabase、前端或商业化能力。

22. 不允许让 examples 目录成为 runtime dependency。

23. 不允许把 manual review checklist 持久化进 canonical schema。

---

## 5. 需要修改的文件

预计修改：

```text
docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
docs/CI.md
examples/llm_review_artifacts/README.md
PROJECT_STATE.md
CHANGELOG.md
tests/test_llm_provider_usage_docs.py
tests/test_llm_artifact_examples.py
```

可能新增：

```text
tests/test_llm_combined_output_docs.py
```

可能新增或更新 examples：

```text
examples/llm_review_artifacts/single-file/combined-result.json
examples/llm_review_artifacts/single-file/combined-report.md
examples/llm_review_artifacts/batch/batch-combined-result.json
examples/llm_review_artifacts/batch/batch-combined-report.md
```

如果已有等价文件或测试，可以更新现有文件，不必强行新增。

---

## 6. 实现要求

### 6.1 CLI 文档收口

`docs/CLI.md` 必须清楚说明以下三类输出：

```text
--output
  deterministic 主输出

--llm-output
  raw LLM sidecar 输出

--combined-output
  deterministic + LLM 的 combined envelope / report 输出
```

必须分别说明 single-file 和 batch 的用法。

#### single-file 示例

```bash
content-review review input.md --profile profile.yml \
  --enable-llm \
  --combined-output combined-report.md \
  --combined-output-format markdown
```

```bash
content-review review input.md --profile profile.yml \
  --enable-llm \
  --combined-output combined-result.json \
  --combined-output-format json
```

#### batch 示例

```bash
content-review batch input_dir --profile profile.yml \
  --enable-llm \
  --combined-output batch-combined-report.md \
  --combined-output-format markdown
```

```bash
content-review batch input_dir --profile profile.yml \
  --enable-llm \
  --combined-output batch-combined-result.json \
  --combined-output-format json
```

必须明确：

1. `--combined-output` 是 explicit opt-in；
2. 不传 `--combined-output` 时默认输出不变；
3. `--combined-output` 不会自动启用 LLM；
4. `--combined-output` 不替代 `--output`；
5. `--combined-output` 不替代 `--llm-output`；
6. `--combined-output-format` 支持 `json` 和 `markdown`；
7. 默认格式是 `markdown`；
8. single-file 和 batch 都支持 combined output。

---

### 6.2 行为矩阵

在 `docs/CLI.md` 或 `docs/LLM_PROVIDER_USAGE.md` 中新增 combined output behavior matrix。

建议表格：

```md
| Command | LLM Enabled | Combined Output | LLM Status | Writes Combined File | Calls Provider | Affects Quality Gate |
| --- | --- | --- | --- | --- | --- | --- |
| review | no | no | - | no | no | no |
| review | no | yes | not_run | yes | no | no |
| review | yes | yes | succeeded / failed | yes | yes | no |
| batch | no | no | - | no | no | no |
| batch | no | yes | not_run | yes | no | no |
| batch | yes | yes | succeeded / partial_failure / failed | yes | yes | no |
```

要求：

1. single-file 和 batch 都要覆盖；
2. LLM disabled + combined output 必须说明不调用 provider；
3. LLM failure / partial failure 必须说明 deterministic result 仍然存在；
4. quality gate 必须始终 deterministic-only。

---

### 6.3 Architecture 文档收口

`docs/ARCHITECTURE.md` 应新增或整理 combined output 架构段落。

建议结构：

```text
deterministic review
  ↓
ReviewResult / BatchReviewResult

LLM review
  ↓
LLMReviewResult / Batch LLM result
  ↓
LLMCoreFindingCandidate

combined integration
  ↓
SingleFileCombinedReviewResult / BatchCombinedReviewResult

presentation
  ↓
combined JSON / combined Markdown

CLI
  ↓
explicit --combined-output only
```

必须明确：

1. combined result 是 envelope；
2. combined output 不替代 deterministic result；
3. LLM findings 是 advisory；
4. provider contract 不知道 combined output；
5. quality gate 不消费 combined result；
6. examples 是 reference-only，不是 runtime dependency。

---

### 6.4 Data Models 文档收口

`docs/DATA_MODELS.md` 应统一说明以下模型关系：

```text
LLMReviewResult
LLMCoreFindingCandidate
SingleFileCombinedReviewResult
BatchCombinedReviewResult
```

必须明确：

1. `LLMCoreFindingCandidate` 不是 deterministic finding；
2. `source="llm"`；
3. `advisory=True`；
4. rule id 使用 `llm.` 前缀；
5. single-file combined JSON 使用 `SingleFileCombinedReviewResult`；
6. batch combined JSON 使用 `BatchCombinedReviewResult`；
7. manual review checklist 不持久化；
8. Markdown report 是 presentation output；
9. examples JSON 不是 schema source of truth。

---

### 6.5 LLM Provider Usage 文档收口

`docs/LLM_PROVIDER_USAGE.md` 应统一说明 provider 与 combined output 的关系。

必须明确：

1. provider 仍然返回 `LLMReviewResult`；
2. batch LLM runner 仍然产生现有 batch LLM sidecar；
3. adapter 在 provider 之后运行；
4. combined result 在 adapter 之后构造；
5. combined output 是 CLI 显式输出层；
6. provider 不知道 `--combined-output`；
7. `--combined-output` 不会自动启用 LLM；
8. LLM failed / partial failure 可以被 combined output 记录；
9. deterministic result 仍然有效；
10. secret / API key 不应进入 combined output。

---

### 6.6 CI 文档收口

`docs/CI.md` 应说明 combined output 与 CI / quality gate 的关系。

必须明确：

1. quality gate 仍然 deterministic-only；
2. fail-on 仍然只基于 deterministic findings；
3. LLM findings 不影响 exit code；
4. LLM failed / partial failure 不应改变 deterministic gate 语义；
5. combined output 可以作为 CI artifact 上传；
6. combined report 可以帮助人工复核，但不是 gate source of truth。

建议增加示例：

```bash
content-review batch docs --profile profile.yml \
  --enable-llm \
  --format markdown \
  --output deterministic-report.md \
  --llm-output batch-llm-result.json \
  --combined-output batch-combined-report.md \
  --combined-output-format markdown
```

并说明：

```text
deterministic-report.md is the gate record.
batch-llm-result.json is the raw LLM sidecar.
batch-combined-report.md is the human review artifact.
```

---

### 6.7 Examples 收口

更新 `examples/llm_review_artifacts/README.md`。

必须增加 combined artifact map。

建议结构：

```text
single-file/
  deterministic-report.md
  llm-result.json
  llm-report.md
  review-index.md
  combined-result.json
  combined-report.md

batch/
  deterministic-report.md
  batch-llm-result.json
  batch-llm-report.md
  batch-review-index.md
  batch-combined-result.json
  batch-combined-report.md
```

必须说明：

1. deterministic report 是 canonical audit record；
2. raw LLM result 是 sidecar；
3. combined result 是 integration envelope；
4. combined Markdown 是 human review artifact；
5. manual review checklist 是 presentation-only；
6. examples 是 reference-only；
7. examples 不参与 runtime。

---

### 6.8 示例文件要求

如果新增 combined examples，应保证：

1. JSON 可解析；
2. Markdown 包含 expected headings；
3. 不包含 API key；
4. 不包含 secret；
5. 不包含 traceback；
6. single-file 示例包含 `SingleFileCombinedReviewResult` 结构；
7. batch 示例包含 `BatchCombinedReviewResult` 结构；
8. batch 示例体现 partial failure；
9. 文档引用路径真实存在。

---

### 6.9 测试要求

新增或更新测试，覆盖：

1. docs 中提到 `--combined-output`；
2. docs 中提到 `--combined-output-format`；
3. docs 中同时覆盖 single-file 和 batch；
4. docs 中明确 `--combined-output` 是 explicit opt-in；
5. docs 中明确不会自动启用 LLM；
6. docs 中明确 quality gate deterministic-only；
7. examples 中 combined JSON 可解析；
8. examples 中 combined Markdown 存在关键标题；
9. examples 不包含 API key / secret；
10. examples README 中包含 artifact map；
11. docs 不声明不存在的 CLI 行为；
12. default behavior unchanged 的现有 CLI 测试仍通过。

---

## 7. 测试要求

请至少更新或新增以下测试：

```text
tests/test_llm_provider_usage_docs.py
tests/test_llm_artifact_examples.py
```

可以新增：

```text
tests/test_llm_combined_output_docs.py
```

测试至少覆盖以下内容。

### 7.1 CLI docs combined output

验证 `docs/CLI.md` 包含：

```text
--combined-output
--combined-output-format
content-review review
content-review batch
json
markdown
explicit opt-in
deterministic-only
```

### 7.2 LLM provider usage docs

验证 `docs/LLM_PROVIDER_USAGE.md` 包含：

```text
provider contract unchanged
combined output
adapter
advisory
not automatically enable LLM
partial failure
```

或等价文案。

### 7.3 Architecture docs

验证 `docs/ARCHITECTURE.md` 包含：

```text
LLMCoreFindingCandidate
SingleFileCombinedReviewResult
BatchCombinedReviewResult
explicit --combined-output
quality gate
```

### 7.4 CI docs

验证 `docs/CI.md` 包含：

```text
combined output
CI artifact
deterministic-only
exit code
fail-on
```

### 7.5 Examples combined artifacts

如果新增 examples，验证文件存在：

```text
examples/llm_review_artifacts/single-file/combined-result.json
examples/llm_review_artifacts/single-file/combined-report.md
examples/llm_review_artifacts/batch/batch-combined-result.json
examples/llm_review_artifacts/batch/batch-combined-report.md
```

### 7.6 Examples JSON parseability

验证 combined JSON 示例可被 `json.loads(...)` 解析，并包含：

single-file:

```text
schema_version
review_result
llm
```

batch:

```text
schema_version
batch_review_result
llm
```

### 7.7 Examples no secret leakage

验证 examples 中不包含：

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
api_key
secret
sk-
traceback
```

### 7.8 Runtime behavior unchanged

运行已有测试：

```text
tests/test_llm_single_file_combined_cli_output.py
tests/test_llm_batch_combined_cli_output.py
tests/test_cli.py
```

确保本任务没有改变 CLI 行为。

---

## 8. 文档更新要求

需要更新：

```text
docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
docs/CI.md
examples/llm_review_artifacts/README.md
PROJECT_STATE.md
CHANGELOG.md
```

### 8.1 PROJECT_STATE.md

记录 TASK-0083 完成后状态：

```text
Combined LLM output documentation, examples, and compatibility boundaries consolidated.
```

同时明确：

```text
No runtime behavior, schema, CLI default output, provider contract, sidecar schema, or quality gate behavior was changed.
```

### 8.2 CHANGELOG.md

新增 TASK-0083 条目，说明：

1. 统一 combined output 文档；
2. 统一 single-file / batch behavior matrix；
3. 更新 combined artifact examples；
4. 增加 docs / examples tests；
5. 明确 quality gate deterministic-only；
6. 明确 combined output 是 explicit opt-in；
7. 未改变 runtime behavior。

---

## 9. 验收标准

本任务完成后应满足：

1. CLI 文档完整说明 single-file combined output；
2. CLI 文档完整说明 batch combined output；
3. 文档说明 `--combined-output` 是 explicit opt-in；
4. 文档说明 `--combined-output` 不自动启用 LLM；
5. 文档说明 `--output`、`--llm-output`、`--combined-output` 的区别；
6. 文档说明 quality gate deterministic-only；
7. 架构文档说明 combined output 的层级位置；
8. 数据模型文档说明 combined envelope 与 deterministic schema 的区别；
9. LLM provider usage 文档说明 provider contract 不变；
10. CI 文档说明 combined output 可作为 artifact，但不是 gate source of truth；
11. examples README 包含 combined artifact map；
12. combined example JSON 可解析；
13. combined example Markdown 有关键标题；
14. examples 不包含 secret / API key / traceback；
15. docs 测试通过；
16. examples 测试通过；
17. 相关 CLI 测试通过；
18. 全量测试通过；
19. 不修改 runtime behavior；
20. 不修改 schema；
21. 不修改 provider contract；
22. 不修改 sidecar schema；
23. 不修改 quality gate；
24. 不新增 CLI 参数；
25. 不接入真实 LLM API。

---

## 10. 风险与注意事项

### 10.1 不要把文档任务变成功能任务

本任务是 consolidation，不是新功能开发。

不要修改 CLI 行为或 schema。

---

### 10.2 不要让 examples 成为 runtime dependency

examples 只能用于文档、测试和开发者参考。

runtime 代码不得读取 examples。

---

### 10.3 不要声明不存在的行为

文档必须只描述已经实现的能力。

如果某个行为尚未实现，不要写成已支持。

---

### 10.4 不要模糊 `--output` / `--llm-output` / `--combined-output`

三者必须保持职责清晰：

```text
--output
  deterministic output

--llm-output
  raw LLM sidecar

--combined-output
  deterministic + LLM combined output
```

---

### 10.5 不要改变 quality gate

LLM findings 仍然 advisory。

quality gate 仍然 deterministic-only。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest tests/test_llm_artifact_examples.py
uv run pytest tests/test_llm_single_file_combined_cli_output.py
uv run pytest tests/test_llm_batch_combined_cli_output.py
uv run pytest tests/test_cli.py
uv run pytest
```

如果新增了 combined docs 测试，也请运行：

```bash
uv run pytest tests/test_llm_combined_output_docs.py
```

---
