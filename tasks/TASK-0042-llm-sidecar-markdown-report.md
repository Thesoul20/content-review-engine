# TASK-0042: Add LLM Sidecar Markdown Report

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计相关的 provider interface、mock reviewer、runner、CLI sidecar 输出能力。

TASK-0040 已经为 batch 审计增加了 LLM sidecar output。

TASK-0041 已经为 LLM sidecar 增加了结构化 summary、per-file status、per-file error、partial success 语义，并引入了 batch LLM manifest，例如 `llm-review-manifest.json`。

当前 LLM sidecar 已经具备结构化 JSON 输出，但对于人工审阅来说，JSON 不够直观。后续接入真实 LLM provider 之前，需要先把 LLM sidecar 结果渲染成稳定、可读、可测试的 Markdown 报告。

因此，本任务的目标是在不接入真实 LLM provider、不合并 LLM findings 到主 ReviewResult、不影响 Quality Gate 的前提下，新增 LLM sidecar Markdown report 能力。

本任务是 TASK-0041 之后的可读性增强任务，为后续真实 provider 调试、人工审阅和报告集成做准备。

---

## 2. 任务目标

实现 LLM sidecar 的 Markdown 报告输出能力。

完成后，项目应支持将 LLM sidecar 结构化结果渲染为 Markdown 报告。

报告应覆盖：

1. 单文件 LLM sidecar Markdown report；
2. batch LLM sidecar Markdown report；
3. summary 信息；
4. per-file status；
5. per-file finding count；
6. failed 文件的 error_type / message；
7. success 文件中的 LLM findings；
8. skipped 文件的状态展示；
9. batch manifest 的聚合信息；
10. 原有 deterministic Markdown report 行为保持不变。

本任务只新增 LLM sidecar 的独立 Markdown report，不把 LLM findings 合并进主 Markdown report。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 新增 LLM sidecar Markdown renderer；
2. 支持单文件 LLMSidecarResult 渲染为 Markdown；
3. 支持 batch LLMSidecarResult / manifest 渲染为 Markdown；
4. 在 Markdown 中展示 summary；
5. 在 Markdown 中展示 per-file status；
6. 在 Markdown 中展示 per-file error；
7. 在 Markdown 中展示 LLM findings；
8. 为 CLI 增加或复用 sidecar Markdown 输出参数；
9. 增加或更新 Markdown report 测试；
10. 增加或更新 CLI 测试；
11. 更新相关文档；
12. 更新 PROJECT_STATE.md 和 CHANGELOG.md。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不接入真实 OpenAI / Anthropic / PydanticAI provider；
2. 不新增真实 LLM API key 配置；
3. 不引入新的外部 LLM SDK 依赖；
4. 不把 LLM findings 合并进主 ReviewResult；
5. 不把 LLM findings 合并进现有 deterministic Markdown report 主结构；
6. 不让 Quality Gate 根据 LLM sidecar 或 LLM Markdown report 失败；
7. 不改变现有 deterministic review JSON schema；
8. 不改变现有 deterministic Markdown report 输出结构；
9. 不改变 TASK-0041 已定义的 sidecar JSON schema，除非发现明显 bug；
10. 不实现 API / MCP / GUI；
11. 不引入 Supabase、用户系统、SaaS、多租户、支付等能力；
12. 不重构整个 CLI；
13. 不实现复杂主题、HTML、PDF、富文本导出；
14. 不新增 retry、timeout、rate limit 等真实 provider 运行机制。

---

## 5. 需要修改的文件

预计包括但不限于：

```text
src/content_review_engine/llm/sidecar.py
src/content_review_engine/llm/serialization.py
src/content_review_engine/llm/__init__.py
src/content_review_engine/cli.py
tests/test_llm_sidecar.py
tests/test_cli.py
docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

如果项目中已经存在专门的 report 模块，也可以新增或修改类似文件：

```text
src/content_review_engine/reports/llm_markdown.py
tests/test_llm_markdown_report.py
```

具体文件名以当前仓库结构为准。

如果已有报告模块命名风格是 `reports/markdown.py`，则优先遵循现有风格，避免新建不一致的目录结构。

---

## 6. 实现要求

### 6.1 LLM Markdown report 定位

LLM Markdown report 是 sidecar report，不是主 deterministic report。

也就是说：

```text
deterministic review
  -> ReviewResult
  -> existing JSON / Markdown report
  -> Quality Gate

LLM sidecar review
  -> LLMSidecarResult
  -> LLM sidecar JSON
  -> LLM sidecar Markdown report
```

本任务不应改变主审计链路。

---

### 6.2 单文件 LLM Markdown report

单文件 LLM sidecar Markdown report 建议结构如下：

```markdown
# LLM Sidecar Review Report

## Summary

| Field | Value |
| --- | --- |
| Files | 1 |
| Succeeded | 1 |
| Failed | 0 |
| Skipped | 0 |
| Findings | 2 |

## File Status

| File | Status | Findings | Error |
| --- | --- | ---: | --- |
| article.md | success | 2 |  |

## Findings

### 1. finding title or rule id

- Severity: warning
- Rule: llm.xxx
- Message: ...
- Suggestion: ...
- Location: ...
- Evidence: ...
```

实际字段应以当前 `LLMReviewResult` / `LLMFinding` 模型为准。

如果当前 LLM finding 没有 title、location、evidence 等字段，不要新增不必要字段；只展示已有字段。

---

### 6.3 batch LLM Markdown report

batch LLM sidecar Markdown report 建议结构如下：

```markdown
# Batch LLM Sidecar Review Report

## Summary

| Field | Value |
| --- | --- |
| Files | 3 |
| Succeeded | 2 |
| Failed | 1 |
| Skipped | 0 |
| Findings | 4 |

## File Status

| File | Status | Findings | Error |
| --- | --- | ---: | --- |
| a.md | success | 2 |  |
| b.md | failed | 0 | LLMProviderError: provider failed |
| c.md | success | 2 |  |

## Findings by File

### a.md

#### Finding 1

- Severity: warning
- Rule: llm.xxx
- Message: ...
- Suggestion: ...

### b.md

LLM review failed.

- Error type: LLMProviderError
- Message: provider failed

### c.md

#### Finding 1

- Severity: info
- Rule: llm.xxx
- Message: ...
- Suggestion: ...
```

报告应清晰表达：

1. 哪些文件成功；
2. 哪些文件失败；
3. 哪些文件被跳过；
4. 每个文件有多少 LLM findings；
5. 失败文件的错误类型和错误信息；
6. 成功文件的 LLM findings。

---

### 6.4 Markdown 转义与稳定性

Markdown renderer 应尽量保证输出稳定，便于 snapshot / fixture 测试。

需要注意：

1. 文件顺序应保持 deterministic；
2. severity / rule / finding 展示顺序应稳定；
3. 表格中的换行、竖线 `|` 应处理，避免破坏 Markdown 表格；
4. 缺失字段应显示为空字符串或 `-`，保持一致；
5. 不要输出 traceback；
6. 不要输出 API key、环境变量或敏感信息；
7. 不要输出随机时间戳，除非项目已有稳定时间策略；
8. 不要引入非确定性排序。

---

### 6.5 CLI 输出行为

本任务可以为 CLI 增加一个明确的 LLM sidecar Markdown 输出方式。

优先考虑以下设计之一，具体以当前 CLI 结构为准：

方案 A：新增独立参数

```bash
content-review review article.md \
  --profile profile.yml \
  --llm-sidecar-output article.llm.json \
  --llm-sidecar-markdown-output article.llm.md
```

batch 场景：

```bash
content-review batch docs/ \
  --profile profile.yml \
  --llm-sidecar-output llm-sidecars/ \
  --llm-sidecar-markdown-output llm-report.md
```

方案 B：如果当前 CLI 已有统一 `--format` 或 sidecar format 设计，则复用现有风格。

不管采用哪种方案，都必须满足：

1. 原有 deterministic `--output` 行为不变；
2. 原有 deterministic `--format markdown` 行为不变；
3. LLM Markdown report 是独立输出；
4. LLM Markdown report 不影响 Quality Gate；
5. LLM Markdown report 写入失败时，可以按照现有文件写入错误策略处理；
6. 不新增 `--fail-on-llm`。

---

### 6.6 batch manifest 与 Markdown report

如果 batch sidecar 当前会输出多个 per-file JSON 和一个 `llm-review-manifest.json`，则 Markdown report 可以基于 manifest 或内部 LLMSidecarResult 构建。

要求：

1. Markdown report 应展示 manifest summary；
2. Markdown report 应展示每个文件状态；
3. Markdown report 应能展示失败文件 error；
4. Markdown report 应能展示成功文件 findings；
5. 不要破坏现有 manifest JSON 结构；
6. 不要把 Markdown report 当作 manifest 的替代品。

---

### 6.7 空结果行为

需要处理以下情况：

1. 没有 findings；
2. 全部 success 但 finding_count 为 0；
3. 部分 failed；
4. 全部 failed；
5. skipped 文件存在但无 findings；
6. batch 中没有发现文件时，如果当前 batch 逻辑允许，应保持现有行为。

Markdown report 应在没有 findings 时显示清晰说明，例如：

```text
No LLM findings.
```

---

## 7. 测试要求

必须新增或更新测试，覆盖以下情况。

### 7.1 Renderer 测试

新增或更新 LLM Markdown renderer 测试。

至少覆盖：

1. 单文件 success 且有 findings；
2. 单文件 success 且无 findings；
3. 单文件 failed；
4. batch 全部 success；
5. batch partial failure；
6. batch 全部 failed；
7. skipped entry 展示；
8. error_type / message 展示；
9. summary 统计展示；
10. Markdown 表格转义。

建议使用 fixture 或 snapshot 风格测试，保证输出稳定。

---

### 7.2 CLI 测试

更新 CLI 测试，覆盖：

1. 单文件 LLM Markdown report 输出文件创建；
2. batch LLM Markdown report 输出文件创建；
3. Markdown report 包含 summary；
4. Markdown report 包含 per-file status；
5. Markdown report 包含 failed 文件 error；
6. Markdown report 包含 success 文件 findings；
7. deterministic Markdown report 不受影响；
8. Quality Gate 不受 LLM Markdown report 影响。

如果当前 CLI 不方便模拟 failed reviewer，可以优先在 renderer 层覆盖 failed 路径，在 CLI 层覆盖 success 路径。

---

### 7.3 回归测试

必须确保已有测试全部通过：

```bash
uv run pytest
```

如果新增专门测试文件，也请额外运行：

```bash
uv run pytest tests/test_llm_markdown_report.py
uv run pytest tests/test_llm_sidecar.py
uv run pytest tests/test_cli.py
```

具体测试文件名以实际仓库为准。

---

## 8. 文档更新要求

需要更新以下文档：

```text
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
PROJECT_STATE.md
CHANGELOG.md
```

更新重点：

1. 在 `docs/ARCHITECTURE.md` 中说明 LLM sidecar Markdown report 是旁路报告，不影响 deterministic review / Quality Gate；
2. 在 `docs/DATA_MODELS.md` 中说明 Markdown report 基于 LLMSidecarResult / LLMSidecarSummary / LLMSidecarFile / LLMSidecarError 渲染；
3. 在 `docs/CLI.md` 中说明如何生成单文件和 batch LLM sidecar Markdown report；
4. 在 `PROJECT_STATE.md` 中记录 TASK-0042 已完成后项目状态；
5. 在 `CHANGELOG.md` 中记录本次变更。

如果 `docs/CI.md` 当前已经提到 LLM sidecar report 与 Quality Gate 的关系，也可以同步更新；否则本任务不强制修改 `docs/CI.md`。

---

## 9. 验收标准

本任务完成后应满足：

1. 存在独立的 LLM sidecar Markdown renderer；
2. 单文件 LLM sidecar 可以渲染为 Markdown report；
3. batch LLM sidecar / manifest 可以渲染为 Markdown report；
4. Markdown report 包含 summary；
5. Markdown report 包含 per-file status；
6. Markdown report 包含 failed 文件 error_type / message；
7. Markdown report 包含 success 文件 findings；
8. Markdown report 能处理 no findings、partial failure、all failed、skipped 等情况；
9. Markdown 输出稳定、可测试；
10. CLI 可以生成独立 LLM sidecar Markdown report；
11. 原有 deterministic JSON / Markdown report 行为不变；
12. Quality Gate 不受 LLM sidecar Markdown report 影响；
13. 不引入真实 LLM provider；
14. 不新增外部 LLM SDK 依赖；
15. 文档、PROJECT_STATE.md、CHANGELOG.md 已同步更新；
16. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 不要把 LLM Markdown report 合并进 deterministic Markdown report；
2. 不要让 LLM Markdown report 影响 Quality Gate；
3. 不要为了展示 Markdown 而修改 LLMReviewResult 主模型；
4. 不要破坏 TASK-0041 的 sidecar JSON schema；
5. 不要输出 traceback、API key、环境变量等敏感信息；
6. 不要引入 HTML / PDF / 富文本导出；
7. 不要在报告中加入非确定性时间戳；
8. 不要重构整个 report 系统；
9. 不要提前接入真实 provider；
10. 不要新增复杂 CLI 交互，保持参数简单、明确、可测试。

---

## 11. 完成后需要运行的命令

```bash
uv run pytest
```

如果新增或修改了专门测试文件，也请额外运行：

```bash
uv run pytest tests/test_llm_markdown_report.py
uv run pytest tests/test_llm_sidecar.py
uv run pytest tests/test_cli.py
```

具体测试文件名以实际仓库为准。

---

