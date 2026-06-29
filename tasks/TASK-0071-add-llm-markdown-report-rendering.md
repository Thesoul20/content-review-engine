# TASK-0071: Add LLM Markdown Report Rendering

## 1. 背景

当前项目已经完成确定性内容审计主链路，包括：

1. Markdown 文件读取；
2. ReviewProfile 加载；
3. 确定性规则审计；
4. 单文件与批量 CLI；
5. JSON / Markdown 报告输出；
6. Quality Gate / CI 质量门禁；
7. LLM provider interface；
8. LLM runner；
9. LLM smoke check；
10. 单文件 LLM sidecar JSON 输出；
11. 批量 LLM sidecar JSON 输出。

在 TASK-0069 与 TASK-0070 完成后，LLM 审计结果已经可以通过 JSON sidecar 输出：

1. 单文件 `content-review review` 可以输出原始 `LLMReviewResult` JSON；
2. 批量 `content-review batch` 可以输出 batch-level `LLMSidecarResult` JSON；
3. batch sidecar 支持 per-file review / error；
4. deterministic batch stdout / JSON / Markdown / quality gate / `BatchReviewResult` 不混入 LLM 结果。

但是目前 LLM 输出仍然主要面向机器读取。对于真实用户来说，只看 JSON 不方便理解 LLM 发现了什么问题、哪些文件失败、哪些文件没有发现问题。

因此，本任务需要在不改变主审计结果 schema、不改变 deterministic Markdown report、不改变 quality gate 行为的前提下，新增一个**独立的 LLM Markdown 报告渲染能力**。

本任务的重点是：

> 把已有 LLM review result / sidecar result 渲染成用户可读的 Markdown 报告，但不把 LLM findings 合并进主 ReviewResult / BatchReviewResult。

---

## 2. 任务目标

实现独立的 LLM Markdown report 输出能力。

完成后，CLI 应支持类似下面的用法：

```bash
content-review review article.md \
  --profile profiles/default.yml \
  --enable-llm \
  --llm-report llm-report.md
```

以及：

```bash
content-review batch articles/ \
  --profile profiles/default.yml \
  --recursive \
  --enable-llm \
  --llm-report batch-llm-report.md
```

其中：

1. `--llm-report` 用于写出 LLM Markdown 报告；
2. `--llm-report` 必须显式配合 `--enable-llm` 使用；
3. `--llm-report` 不要求必须同时提供 `--llm-output`；
4. `--llm-output` 仍然只负责 JSON sidecar；
5. `--llm-report` 只负责 Markdown report；
6. deterministic stdout / JSON / Markdown report / quality gate 行为保持不变；
7. LLM Markdown report 不参与 quality gate；
8. 本任务不新增任何额外真实 LLM 调用，只渲染当前 CLI 执行中已经得到的 LLM 结果。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增 LLM Markdown report renderer；
2. 为单文件 `LLMReviewResult` 生成 Markdown report；
3. 为批量 `LLMSidecarResult` 生成 Markdown report；
4. 在 `content-review review` 中新增 `--llm-report <path>` 参数；
5. 在 `content-review batch` 中新增 `--llm-report <path>` 参数；
6. 在 LLM 审计成功后写出对应 Markdown report；
7. 在 batch partial failure 场景下仍写出 LLM Markdown report，并在报告中展示成功文件与失败文件；
8. 复用已有 LLM runner / provider / secret resolver / provider factory；
9. 增加单元测试与 CLI 集成测试；
10. 更新 CLI、LLM 使用、数据模型、架构、项目状态与变更日志文档。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许修改 `ReviewResult` schema；
2. 不允许修改 `BatchReviewResult` schema；
3. 不允许把 LLM findings 合并进 deterministic findings；
4. 不允许让 LLM findings 参与 quality gate / fail-on 判断；
5. 不允许改变原有 deterministic Markdown report 的结构；
6. 不允许改变原有 deterministic JSON 输出；
7. 不允许改变原有 batch stdout 输出；
8. 不允许新增 API / MCP / GUI / 前端；
9. 不允许新增 Supabase、用户系统、审计历史或商业化能力；
10. 不允许新增真实 provider 类型；
11. 不允许绕过已有 provider factory 或 secret resolver；
12. 不允许在测试中调用真实 LLM API；
13. 不允许要求真实 API key 才能通过测试；
14. 不允许新增一个独立的 `content-review llm-report` 命令；
15. 不允许把本任务扩展成“从已有 JSON 文件读取并转换为 Markdown”的离线转换工具。

---

## 5. 需要修改的文件

预计需要新增或修改以下文件。

### 5.1 代码文件

预计新增：

```text
src/content_review_engine/reports/llm_markdown.py
```

如项目已有更合适的 report 模块结构，也可以使用已有位置，但必须保持 report 渲染逻辑与 CLI 解析逻辑分离。

预计修改：

```text
src/content_review_engine/cli.py
src/content_review_engine/reports/__init__.py
```

如果当前项目的导出结构不需要修改 `reports/__init__.py`，可以不修改。

### 5.2 测试文件

预计新增：

```text
tests/test_llm_markdown_report.py
```

预计修改：

```text
tests/test_llm_single_file_cli_integration.py
tests/test_llm_batch_cli_integration.py
tests/test_cli.py
tests/test_llm_provider_usage_docs.py
```

如现有测试文件名与项目实际名称不同，请以仓库中已有命名为准，但必须覆盖同等测试场景。

### 5.3 文档文件

预计修改：

```text
docs/CLI.md
docs/LLM_PROVIDER_USAGE.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

---

## 6. 实现要求

### 6.1 LLM Markdown renderer

新增一个独立的 Markdown 渲染模块，例如：

```text
src/content_review_engine/reports/llm_markdown.py
```

建议提供以下函数，具体名称可根据现有项目风格调整：

```python
render_llm_review_markdown(result: LLMReviewResult) -> str
render_llm_sidecar_markdown(sidecar: LLMSidecarResult) -> str
```

如果项目已有类似 render 命名规则，应优先保持一致。

### 6.2 单文件 LLM Markdown report 内容

单文件 LLM Markdown report 建议结构如下：

```markdown
# LLM Review Report

## Summary

| Field | Value |
| --- | --- |
| File | ... |
| Schema Version | ... |
| Total Findings | ... |

## Severity Counts

| Severity | Count |
| --- | --- |
| critical | 0 |
| error | 0 |
| warning | 0 |
| info | 0 |

## Findings

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| ... | ... | ... | ... | ... | ... |

## Detailed Findings

### 1. ...

- Severity: ...
- Rule: ...
- Location: line ..., column ...
- Message: ...
- Suggestion: ...
- Matched Text: ...
- Context: ...
```

如果 `LLMReviewResult` 的字段与上述字段不完全一致，应以现有模型为准，不要为了报告强行修改模型。

如果没有 findings，应输出稳定文本，例如：

```markdown
No LLM findings.
```

### 6.3 批量 LLM Markdown report 内容

批量 LLM Markdown report 建议结构如下：

```markdown
# Batch LLM Review Report

## Summary

| Field | Value |
| --- | --- |
| Files Reviewed | ... |
| Files With LLM Findings | ... |
| Files With LLM Errors | ... |
| Total LLM Findings | ... |
| Schema Version | ... |

## Severity Counts

| Severity | Count |
| --- | --- |
| critical | 0 |
| error | 0 |
| warning | 0 |
| info | 0 |

## Files

### path/to/file-1.md

#### Summary

| Field | Value |
| --- | --- |
| Status | success |
| Findings | ... |

#### Findings

...

### path/to/file-2.md

#### Summary

| Field | Value |
| --- | --- |
| Status | error |
| Error Type | ... |
| Error Message | ... |
```

要求：

1. batch report 必须展示每个文件的 LLM 状态；
2. 成功文件展示 findings 或 `No LLM findings.`；
3. 失败文件展示 error type / message；
4. partial failure 时仍然写出 report；
5. 文件顺序应稳定，优先使用 batch 处理顺序或按 path 排序；
6. severity counts 应稳定输出 canonical severity 顺序；
7. 不要在报告中加入当前时间戳，避免 snapshot 测试不稳定。

### 6.4 Markdown 转义

Markdown 表格中的文本必须进行基本转义，至少处理：

1. `|`；
2. 换行；
3. `None` / 空值；
4. 过长文本的稳定展示。

不要因为 message / suggestion / context 中含有竖线或换行导致 Markdown 表格破裂。

### 6.5 CLI 参数行为

为 `content-review review` 新增：

```text
--llm-report <path>
```

为 `content-review batch` 新增：

```text
--llm-report <path>
```

行为要求：

1. `--llm-report` 必须配合 `--enable-llm`；
2. 如果未启用 `--enable-llm` 却传入 `--llm-report`，CLI 应返回清晰错误；
3. `--llm-report` 不要求同时传入 `--llm-output`；
4. 可以同时传入 `--llm-output` 和 `--llm-report`；
5. `--llm-output` 写 JSON；
6. `--llm-report` 写 Markdown；
7. 写入失败时返回非零退出码，并输出清晰错误；
8. 不改变已有 `--output` deterministic report 行为；
9. 不改变已有 `--format markdown` deterministic Markdown report 行为。

### 6.6 LLM 失败行为

单文件场景：

1. 保持现有 LLM failure exit behavior；
2. 不要为了写 report 改变已有错误语义；
3. 如果 LLM 没有产生有效 result，不需要强行写 success report。

批量场景：

1. 保持 TASK-0070 的 partial failure 语义；
2. 如果部分文件 LLM 失败，Markdown report 应展示失败文件；
3. 任一 LLM failure 时，命令仍应保持 TASK-0070 既定 exit code；
4. 不要吞掉 error；
5. 不要让 LLM failure 影响 deterministic batch result 的生成逻辑，除非当前代码在 TASK-0070 中已有明确行为。

---

## 7. 测试要求

### 7.1 新增 renderer 单元测试

新增 `tests/test_llm_markdown_report.py`，至少覆盖：

1. 单文件 LLM result 无 findings；
2. 单文件 LLM result 有多个 findings；
3. severity counts 稳定排序；
4. finding 中包含 message / suggestion / context；
5. Markdown 表格转义 `|`；
6. Markdown 表格转义换行；
7. batch sidecar 所有文件成功；
8. batch sidecar 部分文件成功、部分文件失败；
9. batch sidecar 所有文件无 findings；
10. batch sidecar 文件顺序稳定；
11. batch error type / message 正确展示；
12. 输出不包含当前时间戳等不稳定内容。

### 7.2 更新 CLI 集成测试

更新单文件 CLI LLM 集成测试，至少覆盖：

1. `content-review review --enable-llm --llm-report <path>` 成功写出 Markdown；
2. `--llm-report` 不要求 `--llm-output`；
3. `--llm-output` 与 `--llm-report` 可同时使用；
4. 未传 `--enable-llm` 时使用 `--llm-report` 应失败；
5. report 写入失败时返回清晰错误；
6. 测试不依赖真实 LLM API；
7. 测试不需要真实 API key。

更新 batch CLI LLM 集成测试，至少覆盖：

1. `content-review batch --enable-llm --llm-report <path>` 成功写出 batch Markdown；
2. batch report 包含多个文件；
3. batch report 包含 per-file findings；
4. batch report 包含 partial failure error；
5. `--llm-report` 不要求 `--llm-output`；
6. `--llm-output` 与 `--llm-report` 可同时使用；
7. 未传 `--enable-llm` 时使用 `--llm-report` 应失败；
8. report 写入失败时返回清晰错误；
9. deterministic batch stdout / JSON / Markdown / quality gate 行为不变；
10. 测试不依赖真实网络和真实 API key。

### 7.3 更新 parser / docs 测试

如项目已有 parser 测试或文档断言测试，应同步更新：

```text
tests/test_cli.py
tests/test_llm_provider_usage_docs.py
```

确保：

1. CLI help / usage 中包含 `--llm-report`；
2. docs 中描述 `--llm-output` 与 `--llm-report` 的区别；
3. docs 中明确 LLM Markdown report 不参与 quality gate；
4. docs 中明确 batch partial failure 的 report 展示行为。

---

## 8. 文档更新要求

### 8.1 docs/CLI.md

需要补充：

1. 单文件 LLM Markdown report 用法；
2. batch LLM Markdown report 用法；
3. `--llm-output` 与 `--llm-report` 的区别；
4. `--llm-report` 必须配合 `--enable-llm`；
5. `--llm-report` 不改变 deterministic output；
6. `--llm-report` 不参与 quality gate；
7. batch partial failure 如何展示。

### 8.2 docs/LLM_PROVIDER_USAGE.md

需要补充：

1. LLM JSON sidecar 与 LLM Markdown report 的关系；
2. 单文件 report 示例；
3. batch report 示例；
4. no-network / no-real-key 测试策略；
5. 手动验证示例命令。

### 8.3 docs/DATA_MODELS.md

需要补充：

1. LLM Markdown report 是 `LLMReviewResult` / `LLMSidecarResult` 的展示层；
2. 本任务不新增主 schema；
3. 本任务不改变 `ReviewResult` / `BatchReviewResult`；
4. LLM report 不应被视为 canonical data model，canonical machine-readable output 仍然是 JSON。

### 8.4 docs/ARCHITECTURE.md

需要补充：

1. LLM report renderer 所处层级；
2. CLI 如何调用 renderer；
3. renderer 与 deterministic report renderer 的边界；
4. renderer 不负责 LLM 调用；
5. renderer 不负责 quality gate。

### 8.5 PROJECT_STATE.md

记录 TASK-0071 完成后项目状态：

1. LLM JSON sidecar 已完成；
2. LLM Markdown report rendering 已完成；
3. LLM findings 仍未合并进主 ReviewResult；
4. API / MCP / GUI 仍未开始。

### 8.6 CHANGELOG.md

新增 TASK-0071 条目，说明：

1. 新增 LLM Markdown report renderer；
2. 新增 `--llm-report`；
3. 支持单文件与 batch LLM report；
4. deterministic outputs / quality gate 未改变。

---

## 9. 验收标准

本任务完成后，应满足以下标准：

1. `content-review review --enable-llm --llm-report <path>` 可以写出单文件 LLM Markdown report；
2. `content-review batch --enable-llm --llm-report <path>` 可以写出 batch LLM Markdown report；
3. `--llm-report` 不要求同时提供 `--llm-output`；
4. `--llm-output` 与 `--llm-report` 可以同时使用；
5. 未启用 `--enable-llm` 时传入 `--llm-report` 会失败并给出清晰错误；
6. 单文件 LLM report 可以展示 findings 或 no findings；
7. batch LLM report 可以展示 per-file success / error；
8. partial failure 时 batch report 仍可写出；
9. deterministic `ReviewResult` 不变；
10. deterministic `BatchReviewResult` 不变；
11. deterministic Markdown report 不变；
12. quality gate 行为不变；
13. 所有新增测试通过；
14. `uv run pytest` 全量通过；
15. 文档已同步更新。

---

## 10. 风险与注意事项

1. 不要把 LLM findings 混入主 deterministic findings；
2. 不要让 LLM findings 影响 fail-on / quality gate；
3. 不要为了 Markdown report 修改 LLM result schema；
4. 不要加入当前时间戳，避免 snapshot 测试不稳定；
5. 不要在测试中调用真实 LLM API；
6. 不要让 `--llm-report` 隐式开启 LLM；
7. 不要让 `--llm-report` 隐式要求 `--llm-output`；
8. 不要把 JSON sidecar 当成 Markdown report 的唯一来源，CLI 执行时应优先从内存中的 result 渲染；
9. 不要新增离线转换命令；
10. 不要把本任务扩展成 report integration into main deterministic report。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_markdown_report.py
uv run pytest tests/test_llm_single_file_cli_integration.py
uv run pytest tests/test_llm_batch_cli_integration.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest
```

如果某些测试文件在当前仓库中不存在，请根据实际文件名调整，但必须覆盖同等测试范围。

---
