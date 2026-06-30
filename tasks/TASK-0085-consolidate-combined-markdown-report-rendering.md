# TASK-0085: Consolidate Combined Markdown Report Rendering

## 1. 背景

当前项目已经完成 deterministic review 主线能力，并逐步完成 LLM 语义审计侧线能力，包括：

1. deterministic single-file / batch review；
2. deterministic JSON / Markdown report；
3. deterministic quality gate / CI；
4. LLM provider boundary；
5. LLM runner；
6. LLM sidecar output；
7. explicit combined output；
8. combined output 文档、reference examples 和兼容性测试；
9. stable combined review envelope builder。

上一张任务卡 `TASK-0084` 已经完成：

1. 新增或整理 runtime-level combined envelope builder；
2. single-file `--combined-output` 复用 combined envelope builder；
3. batch `--combined-output` 复用 combined envelope builder；
4. 保持 `--output` / `--llm-output` / `--combined-output` 用户可见行为不变；
5. 保持 deterministic quality gate / exit code 行为不变；
6. 更新相关文档和测试。

但是当前 combined Markdown report 仍然需要进一步稳定：

> combined JSON envelope 已经有了统一 runtime builder，但 combined Markdown report 还需要形成稳定的渲染入口、章节结构、single-file / batch 展示规范和测试覆盖，避免后续 report、API、MCP、GUI 各自解释 combined envelope。

因此，本任务的目标不是改变数据模型，也不是让 LLM findings 进入 deterministic 主结果，而是把 explicit opt-in 的 combined Markdown report 展示层收敛成稳定、可测试、可维护的 report rendering contract。

---

## 2. 任务目标

本任务目标是：

> 基于现有 combined envelope，整理并稳定 single-file 和 batch combined Markdown report 的渲染入口、章节结构、展示边界和测试覆盖，同时保持 JSON schema、CLI 行为、quality gate 和 exit code 不变。

完成后应达到：

1. single-file combined Markdown report 有稳定章节结构；
2. batch combined Markdown report 有稳定章节结构；
3. combined Markdown report 明确展示 deterministic findings 与 LLM findings 的边界；
4. combined Markdown report 明确说明 quality gate 仍然 deterministic-only；
5. combined Markdown report 复用 combined envelope，而不是重新拼接业务数据；
6. combined Markdown report 渲染逻辑集中在 reports 层；
7. reference examples 被刷新或验证；
8. 相关测试能防止展示结构漂移。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 整理 `src/content_review_engine/reports/combined.py` 中的 combined Markdown report 渲染逻辑。
2. 如有必要，可以新增更明确的 report helper，例如：

   * `render_single_file_combined_markdown_report(...)`
   * `render_batch_combined_markdown_report(...)`
   * `render_combined_markdown_report(...)`
3. 让 combined Markdown report 复用 `combined_envelope.py` 的输出结构。
4. 稳定 single-file combined Markdown report 的章节结构。
5. 稳定 batch combined Markdown report 的章节结构。
6. 刷新 single-file / batch combined Markdown reference artifacts。
7. 新增或更新 Markdown rendering tests。
8. 更新 CLI 文档中关于 combined Markdown report 的说明。
9. 更新架构文档中 report rendering 层的位置说明。
10. 更新数据模型文档中 combined envelope 与 Markdown report 的关系。
11. 更新 `PROJECT_STATE.md` 和 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许改变 combined JSON envelope schema。
2. 不允许改变 `--output` 的 deterministic 主输出语义。
3. 不允许改变 `--llm-output` 的 raw LLM sidecar 语义。
4. 不允许改变 `--combined-output` 的 explicit opt-in 语义。
5. 不允许让 `--combined-output` 自动启用 LLM。
6. 不允许把 LLM findings 合并进 deterministic `ReviewResult.findings`。
7. 不允许让 LLM findings 进入 deterministic `severity_counts`。
8. 不允许让 LLM findings 进入 deterministic `rule_counts`。
9. 不允许让 LLM findings 影响 `--fail-on`。
10. 不允许让 LLM findings 影响 quality gate。
11. 不允许让 LLM findings 改变 CLI exit code。
12. 不允许修改 provider interface。
13. 不允许新增真实 LLM provider。
14. 不允许修改 PydanticAI provider 调用逻辑。
15. 不允许新增 API / MCP / GUI。
16. 不允许引入数据库、Supabase、用户系统或商业化能力。
17. 不允许大规模重构 deterministic Markdown report。
18. 不允许把 deterministic `--output markdown` 改成 combined report。
19. 不允许删除 0083 / 0084 已经明确的 artifact boundary 文档。

---

## 5. 预计需要修改的文件

预计包括但不限于：

```text
src/content_review_engine/reports/combined.py
src/content_review_engine/reports/__init__.py
src/content_review_engine/cli.py

examples/llm_review_artifacts/single-file/combined-report.md
examples/llm_review_artifacts/batch/batch-combined-report.md

tests/test_llm_combined_markdown_report.py
tests/test_llm_single_file_combined_cli_output.py
tests/test_llm_batch_combined_cli_output.py
tests/test_llm_artifact_examples.py
tests/test_llm_combined_output_docs.py

docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果仓库中已经存在 combined Markdown report 测试文件，应优先复用或扩展现有测试文件，不要重复创建语义相同的测试文件。

如果 `src/content_review_engine/reports/combined.py` 已经足够承载本任务，不要新增不必要的平行模块。

---

## 6. 实现要求

### 6.1 Combined Markdown report 渲染入口

需要为 combined Markdown report 提供清晰的渲染入口。

建议根据现有代码风格提供类似：

```python
render_single_file_combined_markdown_report(...)
render_batch_combined_markdown_report(...)
render_combined_markdown_report(...)
```

具体命名应遵循仓库现有风格。

渲染入口应位于 reports 层，而不是 LLM provider 层、deterministic engine 层或 CLI 参数解析层。

### 6.2 复用 combined envelope

combined Markdown report 应基于现有 combined envelope 构建结果渲染。

推荐数据流：

```text
deterministic review result
        +
LLM sidecar result
        ↓
combined envelope builder
        ↓
combined Markdown report renderer
        ↓
--combined-output <path>.md
```

不应在 Markdown renderer 中重新计算 deterministic summary、LLM summary 或 quality gate 结果。

### 6.3 Single-file combined Markdown report 结构

single-file combined Markdown report 建议稳定为以下结构，具体标题可根据现有风格微调，但测试应覆盖关键标题：

```text
# Combined Content Review Report

## Artifact Boundary
说明这是 explicit combined artifact，不替代 deterministic --output 或 raw --llm-output。

## Deterministic Review Summary
展示 deterministic review 的 file、profile、total findings、severity counts、rule counts、quality gate 状态。

## Deterministic Findings
展示 deterministic findings。

## LLM Review Summary
展示 LLM review 的 provider / model / status / finding count / schema version 等已有字段。

## LLM Findings
展示 LLM findings。

## Manual Review Checklist
如当前 LLM manual review helper 已经存在，则展示 checklist；如果不存在对应数据，不应伪造。

## Quality Gate Behavior
明确说明 quality gate / --fail-on / exit code 仍然 deterministic-only。

## Artifact Notes
说明 --output、--llm-output、--combined-output 三者可以并存，互不替代。
```

如果当前 reference artifact 已经使用不同标题，本任务可以保留现有标题，但必须确保信息边界完整、稳定、可测试。

### 6.4 Batch combined Markdown report 结构

batch combined Markdown report 建议稳定为以下结构，具体标题可根据现有风格微调：

```text
# Batch Combined Content Review Report

## Artifact Boundary
说明这是 explicit batch combined artifact。

## Deterministic Batch Summary
展示 deterministic batch summary，包括 files discovered、files reviewed、files with findings、total findings、severity counts。

## LLM Batch Summary
展示 batch LLM sidecar summary，包括 reviewed files、LLM finding count、provider/model/status 等已有字段。

## Combined File Results
按 deterministic 顺序逐文件展示 deterministic result 与 LLM result 的对应关系。

## Deterministic Findings by File
展示每个文件的 deterministic findings。

## LLM Findings by File
展示每个文件的 LLM findings。

## Manual Review Checklist
如存在 batch manual review checklist，则展示；不存在时不伪造。

## Quality Gate Behavior
明确说明 batch quality gate / --fail-on / exit code 仍然 deterministic-only。

## Artifact Notes
说明 batch combined report 不替代 deterministic batch output 或 raw batch LLM sidecar。
```

### 6.5 空结果处理

需要稳定处理以下情况：

1. deterministic findings 为空；
2. LLM findings 为空；
3. LLM 未启用但用户显式请求 combined output；
4. batch 中部分文件没有 LLM result；
5. batch 中所有文件都没有 LLM findings；
6. provider metadata 缺失或为空；
7. manual review checklist 为空。

这些情况下，Markdown report 应输出清晰的空状态说明，而不是崩溃或伪造 findings。

### 6.6 CLI 行为要求

CLI 仍然保持现有行为：

1. `--combined-output <path>.json` 写出 combined JSON envelope；
2. `--combined-output <path>.md` 写出 combined Markdown report；
3. `--combined-output` 不自动启用 LLM；
4. `--output` 仍然是 deterministic 主输出；
5. `--llm-output` 仍然是 raw LLM sidecar；
6. 三者可以并存。

如果当前 CLI 是根据文件后缀决定 JSON / Markdown 输出，应保持该行为不变。

### 6.7 不改变 deterministic Markdown report

本任务不得改变 deterministic `--output markdown` 的核心结构和语义。

如确实需要共享某些 formatting helper，必须保证 deterministic Markdown report 的 snapshot / fixture / existing tests 不发生非预期变化。

### 6.8 Reference artifacts

需要刷新或确认以下文件：

```text
examples/llm_review_artifacts/single-file/combined-report.md
examples/llm_review_artifacts/batch/batch-combined-report.md
```

reference artifact 应体现新的稳定章节结构。

不得在 examples 中写入：

1. API key；
2. secret；
3. 本地绝对路径；
4. traceback；
5. 临时调试信息；
6. 不稳定时间戳。

---

## 7. 测试要求

本任务必须新增或更新测试。

### 7.1 新增 combined Markdown report tests

建议新增：

```text
tests/test_llm_combined_markdown_report.py
```

测试至少覆盖：

1. single-file combined Markdown report 包含稳定标题；
2. single-file combined Markdown report 包含 deterministic summary；
3. single-file combined Markdown report 包含 LLM summary；
4. single-file combined Markdown report 明确 artifact boundary；
5. single-file combined Markdown report 明确 deterministic-only quality gate；
6. batch combined Markdown report 包含稳定标题；
7. batch combined Markdown report 包含 deterministic batch summary；
8. batch combined Markdown report 包含 LLM batch summary；
9. batch combined Markdown report 按文件展示结果；
10. 空 deterministic findings 能正常渲染；
11. 空 LLM findings 能正常渲染；
12. manual review checklist 缺失时不伪造内容；
13. Markdown report 不包含 secret、API key、traceback。

### 7.2 更新 CLI combined output tests

需要更新或确认以下测试仍然通过：

```text
tests/test_llm_single_file_combined_cli_output.py
tests/test_llm_batch_combined_cli_output.py
```

测试重点：

1. `--combined-output output.md` 写出 Markdown report；
2. Markdown report 包含 expected headings；
3. `--combined-output output.json` 行为不变；
4. `--combined-output` 不自动启用 LLM；
5. `--output`、`--llm-output`、`--combined-output` 可以并存；
6. quality gate exit code 不受 LLM findings 影响。

### 7.3 更新 artifact examples tests

需要更新或确认：

```text
tests/test_llm_artifact_examples.py
```

测试重点：

1. single-file combined Markdown reference artifact 包含关键标题；
2. batch combined Markdown reference artifact 包含关键标题；
3. examples 不含 API key、secret、traceback；
4. examples 标记为 reference-only。

### 7.4 更新 docs tests

需要更新或确认：

```text
tests/test_llm_combined_output_docs.py
tests/test_llm_provider_usage_docs.py
```

测试重点：

1. docs 中说明 combined Markdown report 复用 combined envelope；
2. docs 中说明 combined Markdown report 不替代 deterministic `--output markdown`；
3. docs 中说明 quality gate 仍然 deterministic-only；
4. docs 中说明 `--combined-output` 不自动启用 LLM。

### 7.5 全量测试

完成后必须运行：

```bash
uv run pytest
```

---

## 8. 文档更新要求

本任务需要更新以下文档：

```text
docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
PROJECT_STATE.md
CHANGELOG.md
```

### 8.1 docs/CLI.md

需要补充或确认：

1. `--combined-output <path>.md` 输出 combined Markdown report；
2. combined Markdown report 是 explicit artifact；
3. combined Markdown report 不替代 deterministic `--output markdown`；
4. combined Markdown report 不替代 raw `--llm-output`；
5. combined Markdown report 复用 combined envelope；
6. quality gate 仍然 deterministic-only。

### 8.2 docs/ARCHITECTURE.md

需要补充 combined Markdown renderer 在架构中的位置：

```text
deterministic review result
        +
LLM sidecar result
        ↓
combined envelope builder
        ↓
combined Markdown renderer
        ↓
combined Markdown artifact
```

并强调：

1. Markdown renderer 属于 reports 层；
2. Markdown renderer 不负责 provider 调用；
3. Markdown renderer 不负责 deterministic rule evaluation；
4. Markdown renderer 不改变 quality gate；
5. Markdown renderer 不改变 CLI exit code。

### 8.3 docs/DATA_MODELS.md

需要补充：

1. combined envelope 是数据层 contract；
2. combined Markdown report 是 envelope 的展示层 projection；
3. Markdown report 不定义新的 schema；
4. Markdown report 不改变 deterministic result；
5. Markdown report 不改变 raw LLM sidecar。

### 8.4 docs/LLM_PROVIDER_USAGE.md

需要补充：

1. LLM provider 只产生 raw LLM review result；
2. combined envelope 在 provider 之后构建；
3. combined Markdown report 在 envelope 之后渲染；
4. provider 不负责 Markdown report；
5. `--combined-output` 不自动启用 provider。

### 8.5 PROJECT_STATE.md

记录 TASK-0085 完成的能力：

1. combined Markdown report rendering 已稳定；
2. single-file / batch combined Markdown report 已有明确章节结构；
3. reference artifacts 已刷新或验证；
4. quality gate 仍然 deterministic-only。

### 8.6 CHANGELOG.md

记录本次新增或整理的 combined Markdown report 渲染、测试和文档更新。

---

## 9. 验收标准

满足以下条件即可认为任务完成：

1. single-file combined Markdown report 有稳定渲染入口；
2. batch combined Markdown report 有稳定渲染入口；
3. combined Markdown report 复用 combined envelope；
4. combined Markdown report 明确 deterministic findings 与 LLM findings 的边界；
5. combined Markdown report 明确 quality gate deterministic-only；
6. combined Markdown report 能处理空 deterministic findings；
7. combined Markdown report 能处理空 LLM findings；
8. combined Markdown reference artifacts 已刷新或验证；
9. `--combined-output .md` CLI 行为保持兼容；
10. `--combined-output .json` CLI 行为保持兼容；
11. `--output markdown` deterministic report 行为不变；
12. quality gate / exit code 行为不变；
13. 新增或更新必要测试；
14. 文档同步更新；
15. 全量测试通过。

---

## 10. 风险与注意事项

### 10.1 不要把 Markdown report 当成数据模型

combined Markdown report 是展示层，不是 schema source of truth。

source of truth 应该是：

```text
deterministic ReviewResult
LLMReviewResult / LLM sidecar
CombinedReviewEnvelope
```

Markdown report 只是基于 envelope 的 projection。

### 10.2 不要改变 deterministic 主报告

`--output markdown` 应继续保持 deterministic-only。

本任务只处理 `--combined-output <path>.md`。

### 10.3 不要让 LLM 影响 quality gate

即使 combined Markdown report 展示了 LLM findings，也不能因此改变 `--fail-on`、quality gate 或 exit code。

### 10.4 不要伪造 LLM findings

当 LLM 未启用或没有 findings 时，应展示空状态说明，而不是生成占位 findings。

### 10.5 不要过度设计 UI

本任务只做 Markdown report，不做 HTML、Web UI、桌面端、API、MCP 或 GUI。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_combined_markdown_report.py
uv run pytest tests/test_llm_single_file_combined_cli_output.py
uv run pytest tests/test_llm_batch_combined_cli_output.py
uv run pytest tests/test_llm_artifact_examples.py
uv run pytest tests/test_llm_combined_output_docs.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest tests/test_cli.py
uv run pytest
```

如果某些测试文件不存在，应根据本任务实际新增或更新后的文件名运行对应测试，并在最终输出中说明。

---

