# TASK-0079: Add Single-File Combined CLI Output Option

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate、LLM sidecar 输出、LLM Markdown report、review index、manual review checklist、artifact examples、LLM-to-core finding adapter、single-file combined review result envelope，以及 single-file combined Markdown renderer。

截至 TASK-0078，项目中已经具备以下链路：

```text
ReviewResult
LLMReviewResult
LLMCoreFindingCandidate
  ↓
SingleFileCombinedReviewResult
  ↓
render_single_file_combined_markdown_report(...)
```

也就是说，单文件层面已经可以构造 combined result，也可以渲染 combined Markdown report。

但是目前该 combined result / combined Markdown report 还没有通过 CLI 暴露给用户。

本任务是 LLM 合并主程序的第四步：

> 给单文件 `content-review review` 增加一个显式 opt-in 的 combined output 入口，让用户可以主动输出 single-file combined JSON 或 Markdown，但不改变 CLI 默认行为、不改变 batch 行为、不改变 quality gate 行为。

本任务只做单文件 CLI 的显式输出选项，不把 combined output 变成默认输出。

---

## 2. 任务目标

为单文件命令新增显式 combined output 能力。

目标行为：

```bash
content-review review input.md --profile profile.yml \
  --enable-llm \
  --combined-output combined-report.md \
  --combined-output-format markdown
```

或：

```bash
content-review review input.md --profile profile.yml \
  --enable-llm \
  --combined-output combined-result.json \
  --combined-output-format json
```

本任务完成后，用户可以主动生成：

1. single-file combined Markdown report；
2. single-file combined JSON result。

但以下行为必须保持不变：

1. `content-review review` 默认输出不变；
2. existing `--format` 行为不变；
3. existing `--output` 行为不变；
4. existing `--llm-output` 行为不变；
5. deterministic quality gate 行为不变；
6. CLI exit code 行为不变；
7. batch 命令不变。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 修改单文件 CLI 命令 `content-review review`，新增显式 opt-in 参数：

   ```text
   --combined-output PATH
   --combined-output-format {json,markdown}
   ```

2. 仅当用户显式传入 `--combined-output` 时，写出 combined output 文件。

3. 当 `--combined-output-format markdown` 时，使用 TASK-0078 的 renderer：

   ```python
   render_single_file_combined_markdown_report(...)
   ```

4. 当 `--combined-output-format json` 时，使用 TASK-0077 的 serializer：

   ```python
   single_file_combined_review_result_to_dict(...)
   ```

5. 在单文件 CLI 路径中构造：

   ```python
   SingleFileCombinedReviewResult
   ```

6. 复用现有 deterministic `ReviewResult`。

7. 复用现有 LLM 执行结果。

8. 复用现有 LLM error handling / sidecar 语义，不能新增另一套 LLM 执行逻辑。

9. 支持以下状态：

   ```text
   succeeded
   failed
   skipped
   not_run
   ```

10. 当用户没有启用 LLM，但仍传入 `--combined-output` 时，允许输出 combined result，并将 LLM 状态记录为 `skipped` 或 `not_run`，具体以现有语义为准。

11. 新增 CLI 测试，覆盖 combined Markdown 输出、combined JSON 输出、LLM disabled 状态、LLM failed 状态、默认行为不变、quality gate 不变。

12. 更新 CLI 文档和相关架构 / 数据模型 / LLM 使用文档。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许修改主 `ReviewResult` schema。

2. 不允许把 LLM findings 写入 `ReviewResult.findings`。

3. 不允许修改 deterministic review runner。

4. 不允许修改 deterministic rule engine 行为。

5. 不允许修改 `content-review review` 默认输出。

6. 不允许改变现有 `--format` 语义。

7. 不允许改变现有 `--output` 语义。

8. 不允许改变现有 `--llm-output` 语义。

9. 不允许让 `--combined-output` 替代 `--llm-output`。

10. 不允许修改 batch command。

11. 不允许新增 batch combined output。

12. 不允许修改 Markdown 主报告默认输出。

13. 不允许让 LLM findings 参与 deterministic `severity_counts`、`rule_counts`、quality gate 或 exit code。

14. 不允许修改 quality gate 策略。

15. 不允许接入新的真实 LLM API。

16. 不允许修改 provider contract。

17. 不允许修改 sidecar JSON schema。

18. 不允许新增 API、MCP、GUI、Supabase、前端或商业化能力。

19. 不允许让 `examples/llm_review_artifacts/` 成为 runtime dependency。

20. 不允许把 manual review checklist 持久化进 canonical schema。

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
tests/test_cli.py
tests/test_llm_single_file_cli_integration.py
tests/test_llm_provider_usage_docs.py
```

可能新增：

```text
tests/test_llm_single_file_combined_cli_output.py
```

如果现有测试文件已经有更合适的位置，可以直接扩展现有测试，但必须保证 combined CLI 输出路径有明确测试覆盖。

---

## 6. 实现要求

### 6.1 CLI 参数设计

在单文件 `content-review review` 命令中新增：

```text
--combined-output PATH
```

用于指定 combined output 写出路径。

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
content-review review input.md --profile profile.yml --combined-output combined.md
```

默认写出 Markdown。

如果项目现有 CLI 对 format 参数有统一风格，可以遵守现有风格，但必须避免和主 `--format` 混淆。

---

### 6.2 默认行为不变

如果用户没有传入：

```text
--combined-output
```

则 CLI 行为必须与 TASK-0078 之前完全一致。

必须保持：

1. stdout 行为不变；
2. `--output` 行为不变；
3. `--format` 行为不变；
4. `--llm-output` 行为不变；
5. exit code 行为不变。

---

### 6.3 combined output 触发条件

只有当用户显式传入：

```text
--combined-output
```

时，才写出 combined output。

示例：

```bash
content-review review input.md --profile profile.yml \
  --enable-llm \
  --combined-output combined.md
```

应生成 combined Markdown。

示例：

```bash
content-review review input.md --profile profile.yml \
  --enable-llm \
  --combined-output combined.json \
  --combined-output-format json
```

应生成 combined JSON。

---

### 6.4 LLM enabled 情况

当用户传入：

```text
--enable-llm
```

并且 LLM 执行成功时：

1. existing deterministic review 正常运行；

2. existing LLM review 正常运行；

3. existing `--llm-output` 行为不变；

4. 构造 `SingleFileCombinedReviewResult`；

5. `llm_status` 应为：

   ```text
   succeeded
   ```

6. combined output 中应包含 LLM finding candidates；

7. combined output 中应明确 advisory policy；

8. quality gate 仍然只看 deterministic result。

---

### 6.5 LLM disabled 情况

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

1. deterministic review 正常运行；

2. 不调用 LLM provider；

3. 构造 `SingleFileCombinedReviewResult`；

4. `llm_status` 使用：

   ```text
   skipped
   ```

   或者如果现有语义更适合，则使用：

   ```text
   not_run
   ```

5. combined Markdown 中应显示：

   ```text
   LLM review was skipped.
   ```

   或等价说明。

6. combined JSON 中应包含稳定的 `llm.status`。

要求：

1. 不要因为 `--combined-output` 自动启用 LLM。
2. 不要因为缺少 `--enable-llm` 报错。
3. 不要读取 API key。
4. 不要调用 provider。

---

### 6.6 LLM failed 情况

当 LLM 执行失败时：

1. deterministic review result 仍然存在；

2. existing LLM failure handling 不应被破坏；

3. combined result 应记录：

   ```text
   llm_status = failed
   ```

4. combined result 应包含结构化 `llm_error`；

5. combined Markdown 应展示 `## LLM Error`；

6. combined JSON 应包含 `llm.error`；

7. LLM failed 不应影响 deterministic quality gate；

8. LLM failed 不应改变 deterministic exit code 策略，除非现有 CLI 已有明确 LLM failure exit behavior，本任务不得改变它。

---

### 6.7 combined Markdown 输出

当：

```text
--combined-output-format markdown
```

时，必须使用：

```python
render_single_file_combined_markdown_report(...)
```

要求：

1. 不要在 CLI 中手写 Markdown。
2. 不要复制 combined Markdown renderer 逻辑。
3. 输出文件应为 UTF-8 文本。
4. 输出内容应以单个换行结尾。
5. 如果目标目录不存在，遵守现有 `--output` 路径处理方式。
6. 如果现有项目没有自动创建父目录，则不要为 combined output 单独引入不一致行为。

---

### 6.8 combined JSON 输出

当：

```text
--combined-output-format json
```

时，必须使用：

```python
single_file_combined_review_result_to_dict(...)
```

要求：

1. 不要在 CLI 中手写 combined JSON。
2. 输出必须 JSON-compatible。
3. JSON 格式缩进应遵守项目现有 JSON 输出风格。
4. 输出文件应为 UTF-8 文本。
5. 不要修改 existing deterministic JSON serializer。
6. 不要修改 existing LLM sidecar serializer。

---

### 6.9 与 `--llm-output` 的关系

本任务必须保持 `--llm-output` 行为不变。

如果用户同时传入：

```text
--llm-output llm-result.json
--combined-output combined.md
```

则应该同时写出：

1. existing raw LLM result sidecar；
2. new combined output。

要求：

1. `--llm-output` 仍然只写 raw LLM result；
2. `--combined-output` 写 combined envelope / report；
3. 二者不能互相覆盖；
4. 二者文件路径相同的情况，可以遵守现有 output conflict 处理风格；如果项目没有冲突处理，至少测试不要使用同一路径。

---

### 6.10 与 `--output` 的关系

本任务必须保持 `--output` 行为不变。

如果用户同时传入：

```text
--output deterministic-report.md
--combined-output combined-report.md
```

则应该同时写出：

1. existing deterministic output；
2. new combined output。

要求：

1. `--output` 仍然写原本的 deterministic result/report；
2. `--combined-output` 写 combined result/report；
3. 不要让 combined output 替代 deterministic output；
4. 不要改变 stdout 逻辑。

---

### 6.11 与 quality gate 的关系

本任务不得改变 quality gate。

要求：

1. `--fail-on` 仍然只基于 deterministic findings；
2. LLM advisory candidates 不参与 `severity_counts`；
3. LLM advisory candidates 不参与 `rule_counts`；
4. LLM advisory candidates 不影响 exit code；
5. combined report 中可以展示 LLM severity，但必须保持 advisory；
6. 测试必须覆盖 LLM finding severity 不影响 exit code。

---

### 6.12 错误与 secret 处理

combined output 中的 error 信息不得泄漏 secret。

要求：

1. 不输出 API key；
2. 不输出完整环境变量；
3. 不输出 provider raw secret；
4. 不输出 Python traceback；
5. 如果复用现有 redaction helper，应保持一致。

---

## 7. 测试要求

新增或更新 CLI 测试，建议新增：

```text
tests/test_llm_single_file_combined_cli_output.py
```

至少覆盖以下场景。

### 7.1 combined Markdown 输出

运行类似：

```bash
content-review review input.md --profile profile.yml \
  --enable-llm \
  --combined-output combined.md \
  --combined-output-format markdown
```

验证：

1. 命令成功；

2. `combined.md` 存在；

3. 内容包含：

   ```text
   # Combined Content Review Report
   ```

4. 内容包含 deterministic review 内容；

5. 内容包含 LLM status；

6. 内容包含 advisory policy；

7. 内容包含 quality gate boundary；

8. 默认 deterministic 输出行为不变。

---

### 7.2 combined JSON 输出

运行类似：

```bash
content-review review input.md --profile profile.yml \
  --enable-llm \
  --combined-output combined.json \
  --combined-output-format json
```

验证：

1. 命令成功；

2. `combined.json` 存在；

3. JSON 可解析；

4. 顶层包含：

   ```text
   schema_version
   review_result
   llm
   ```

5. `llm.status` 正确；

6. `llm.advisory == true`；

7. `llm.finding_candidates` 存在；

8. raw sidecar schema 不变。

---

### 7.3 LLM disabled with combined output

运行类似：

```bash
content-review review input.md --profile profile.yml \
  --combined-output combined.md
```

验证：

1. 命令成功；
2. 不调用 LLM provider；
3. combined output 存在；
4. `llm.status` 为 `skipped` 或 `not_run`；
5. Markdown 中说明 LLM review 未运行或被跳过；
6. deterministic result 正常。

---

### 7.4 同时输出 deterministic output、LLM sidecar 和 combined output

运行类似：

```bash
content-review review input.md --profile profile.yml \
  --enable-llm \
  --format markdown \
  --output deterministic.md \
  --llm-output llm-result.json \
  --combined-output combined.md
```

验证：

1. `deterministic.md` 存在；
2. `llm-result.json` 存在；
3. `combined.md` 存在；
4. 三者内容职责不同；
5. deterministic output 没有变成 combined output；
6. LLM sidecar 没有变成 combined output。

---

### 7.5 LLM failed combined output

用 mock provider 或现有测试机制模拟 LLM 失败。

验证：

1. deterministic review 仍然完成；
2. combined output 存在；
3. combined output 中 `llm.status == failed`；
4. combined output 中包含 structured error；
5. 不包含 secret/API key；
6. quality gate 行为不变。

---

### 7.6 quality gate 不变

构造 LLM finding severity 为 `error` 或 `critical`，但 deterministic findings 不触发 fail-on。

验证：

1. CLI exit code 不因 LLM candidate 失败；
2. `--fail-on` 仍然基于 deterministic findings；
3. combined report 明确 deterministic-only。

---

### 7.7 默认行为不变

运行现有单文件 review 命令，不传：

```text
--combined-output
```

验证：

1. stdout 与现有预期一致；
2. `--output` 与现有预期一致；
3. 不生成 combined output；
4. existing tests 不需要大规模重写。

---

### 7.8 invalid combined output format

运行：

```bash
content-review review input.md --profile profile.yml \
  --combined-output combined.txt \
  --combined-output-format invalid
```

验证 CLI 给出清晰错误。

如果 CLI 框架已经自动处理 choices，则测试对应行为即可。

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

新增单文件 combined output 使用说明。

必须包含：

1. `--combined-output`；
2. `--combined-output-format json|markdown`；
3. Markdown 示例；
4. JSON 示例；
5. 与 `--output` 的区别；
6. 与 `--llm-output` 的区别；
7. 说明该功能是 explicit opt-in；
8. 说明默认输出不变；
9. 说明 quality gate 仍然 deterministic-only；
10. 不要声明 batch 支持该功能。

示例：

```bash
content-review review input.md --profile profile.yml \
  --enable-llm \
  --combined-output combined-report.md \
  --combined-output-format markdown
```

---

### 8.2 docs/ARCHITECTURE.md

说明 CLI 集成位置：

```text
ReviewResult
LLMReviewResult
LLMCoreFindingCandidate
  ↓
SingleFileCombinedReviewResult
  ↓
combined JSON / combined Markdown
  ↓
explicit single-file CLI output option
```

必须明确：

1. CLI 只是显式输出入口；
2. 默认 CLI 行为不变；
3. quality gate 不变；
4. batch 尚未接入；
5. combined output 不替代 deterministic output 或 LLM sidecar。

---

### 8.3 docs/DATA_MODELS.md

说明本任务没有改变 canonical `ReviewResult` schema。

必须明确：

1. combined JSON 使用 `SingleFileCombinedReviewResult` envelope；
2. deterministic `ReviewResult` 仍然是 deterministic audit record；
3. LLM findings 仍然是 advisory candidates；
4. LLM findings 不参与 deterministic counts；
5. LLM findings 不参与 quality gate。

---

### 8.4 docs/LLM_PROVIDER_USAGE.md

说明：

1. provider contract 不变；
2. `--combined-output` 使用 provider 之后的 result；
3. raw `--llm-output` 仍然可用；
4. combined output 可与 raw LLM sidecar 同时写出；
5. LLM disabled 时不会因为 combined output 自动调用 provider；
6. LLM failed 时 combined output 可以记录 error，但 deterministic result 仍然有效。

---

### 8.5 PROJECT_STATE.md

记录 TASK-0079 完成后状态：

```text
Single-file combined CLI output option added as explicit opt-in.
```

同时明确：

```text
Default CLI output, batch output, ReviewResult schema, and quality gate behavior remain unchanged.
```

---

### 8.6 CHANGELOG.md

新增 TASK-0079 条目，说明：

1. 新增 `--combined-output`；
2. 新增 `--combined-output-format json|markdown`；
3. 支持 single-file combined JSON output；
4. 支持 single-file combined Markdown output；
5. 可与 `--output` / `--llm-output` 并存；
6. 不改变默认 CLI 行为；
7. 不改变 batch；
8. 不改变 quality gate；
9. 新增测试。

---

## 9. 验收标准

本任务完成后应满足：

1. 单文件 `content-review review` 新增 `--combined-output`；
2. 单文件 `content-review review` 新增 `--combined-output-format json|markdown`；
3. 不传 `--combined-output` 时默认行为完全不变；
4. combined Markdown 输出使用 `render_single_file_combined_markdown_report(...)`；
5. combined JSON 输出使用 `single_file_combined_review_result_to_dict(...)`；
6. LLM enabled 且成功时，combined output 包含 LLM advisory findings；
7. LLM disabled 时，combined output 不会自动调用 LLM；
8. LLM failed 时，combined output 可以记录 structured error；
9. `--output` 行为不变；
10. `--llm-output` 行为不变；
11. `--output`、`--llm-output`、`--combined-output` 可以并存；
12. batch command 不变；
13. `ReviewResult` schema 不变；
14. `ReviewResult.findings` 不包含 LLM findings；
15. quality gate 不变；
16. LLM advisory candidates 不影响 exit code；
17. provider contract 不变；
18. sidecar JSON schema 不变；
19. 不接入新的真实 LLM API；
20. 不读取 examples 目录作为 runtime dependency；
21. 新增测试通过；
22. 全量测试通过；
23. 文档同步更新。

---

## 10. 风险与注意事项

### 10.1 不要改变默认输出

这是本任务最大的边界。

只有显式传入：

```text
--combined-output
```

才允许生成 combined output。

---

### 10.2 不要让 combined output 替代 deterministic output

`--output` 和 `--combined-output` 是两个不同概念。

```text
--output
  原有 deterministic output

--combined-output
  新增 combined output
```

不要改变 `--output` 的语义。

---

### 10.3 不要让 combined output 替代 LLM sidecar

`--llm-output` 和 `--combined-output` 也是两个不同概念。

```text
--llm-output
  原始 LLMReviewResult sidecar

--combined-output
  deterministic + LLM integration envelope/report
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

### 10.6 不要处理 batch

本任务只做 single-file CLI。

Batch combined output 后续单独做。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_single_file_combined_cli_output.py
uv run pytest tests/test_llm_single_file_combined_markdown_report.py
uv run pytest tests/test_llm_single_file_combined_result.py
uv run pytest tests/test_llm_finding_adapter.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest
```

如果实际扩展了现有 CLI 测试文件，也请运行对应测试文件，例如：

```bash
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_single_file_cli_integration.py
```

---
