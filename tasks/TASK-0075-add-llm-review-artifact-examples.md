# TASK-0075: Add LLM Review Artifact Examples

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
10. 批量 LLM Markdown report；
11. Hybrid Review Report Index；
12. LLM Finding Advisory Policy；
13. LLM Manual Review Checklist。

在 TASK-0074 完成后，LLM 审计结果已经可以形成较完整的人工可读 artifact：

```text
--output        deterministic 主输出
--llm-output    LLM JSON sidecar
--llm-report    LLM Markdown report
--report-index  输出导航与解释型 Markdown index
```

其中：

1. deterministic output 是稳定、可复现、可用于 quality gate 的主审计结果；
2. LLM JSON sidecar 是 LLM 层的机器可读输出；
3. LLM Markdown report 是 LLM 层的人类可读报告；
4. report index 是导航与解释层；
5. manual review checklist 是 presentation-only 的人工审阅清单；
6. LLM findings 仍不进入主 `ReviewResult` / `BatchReviewResult`；
7. LLM findings 仍不参与 `--fail-on` / quality gate。

但是，目前这些输出主要通过测试和文档零散描述，缺少一组完整、可浏览、可验证的示例 artifact。

这会导致后续几个问题：

1. 用户不容易理解这些输出之间的关系；
2. 后续 API / MCP / GUI 设计缺少稳定参考；
3. 文档中没有一组完整的 single-file / batch artifact 示例；
4. CI artifact 使用方式不够直观；
5. Agent 后续开发时容易误解哪些输出是 canonical，哪些只是 presentation layer；
6. LLM manual review checklist 的用途还不够可视化。

因此，本任务需要新增一组 **LLM Review Artifact Examples**。

本任务只新增示例、fixtures、文档和测试，不改变任何运行时行为。

---

## 2. 任务目标

新增一组完整的示例 artifact，用来展示：

1. 单文件 deterministic Markdown report；
2. 单文件 LLM JSON sidecar；
3. 单文件 LLM Markdown report；
4. 单文件 report index；
5. 批量 deterministic Markdown report；
6. 批量 LLM JSON sidecar；
7. 批量 LLM Markdown report；
8. 批量 report index；
9. batch partial failure 示例；
10. LLM advisory policy 示例；
11. LLM manual review checklist 示例；
12. CI artifact navigation 示例。

建议新增目录：

```text
examples/llm_review_artifacts/
```

目录下建议包含：

```text
examples/llm_review_artifacts/
  README.md

  single-file/
    input.md
    profile.yml
    deterministic-report.md
    llm-result.json
    llm-report.md
    review-index.md

  batch/
    input/
      article-a.md
      article-b.md
      article-with-llm-error.md
    profile.yml
    deterministic-report.md
    batch-llm-result.json
    batch-llm-report.md
    batch-review-index.md
```

如果项目现有示例目录命名不同，可以采用已有风格，但必须保证示例组织清晰、路径稳定、文档可读。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增 LLM review artifact 示例目录；
2. 新增 single-file 示例输入 Markdown；
3. 新增 single-file 示例 profile；
4. 新增 single-file deterministic report 示例；
5. 新增 single-file LLM JSON sidecar 示例；
6. 新增 single-file LLM Markdown report 示例；
7. 新增 single-file report index 示例；
8. 新增 batch 示例输入 Markdown；
9. 新增 batch 示例 profile；
10. 新增 batch deterministic report 示例；
11. 新增 batch LLM JSON sidecar 示例；
12. 新增 batch LLM Markdown report 示例；
13. 新增 batch report index 示例；
14. 新增 batch partial failure 示例；
15. 新增示例 README；
16. 新增或更新测试，验证示例 JSON 可解析、Markdown 包含关键 section；
17. 更新 CLI、LLM provider usage、data models、architecture、CI、project state 和 changelog 文档；
18. 如果项目已有 docs assertion 测试，可以补充示例文档断言。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许修改 `ReviewResult` schema；
2. 不允许修改 `BatchReviewResult` schema；
3. 不允许修改 `LLMReviewResult` schema；
4. 不允许修改 `LLMSidecarResult` schema；
5. 不允许修改 LLM JSON sidecar schema；
6. 不允许改变 deterministic Markdown report renderer；
7. 不允许改变 LLM Markdown report renderer；
8. 不允许改变 report index renderer；
9. 不允许改变 manual review checklist renderer；
10. 不允许新增 CLI 参数；
11. 不允许新增 CLI 命令；
12. 不允许新增 accept / dismiss / resolve / ignore 工作流；
13. 不允许新增持久化 review state；
14. 不允许让 LLM findings 参与 quality gate；
15. 不允许改变 `--fail-on` 行为；
16. 不允许改变 CLI exit code 行为；
17. 不允许改变 batch partial failure 行为；
18. 不允许新增真实 provider；
19. 不允许新增真实 LLM API 调用；
20. 不允许在测试中调用真实 LLM API；
21. 不允许要求真实 API key；
22. 不允许新增 API / MCP / GUI；
23. 不允许新增 Supabase、用户系统、审计历史或商业化能力；
24. 不允许在示例中包含真实 secret、API key、个人信息或敏感内容；
25. 不允许在示例输出中包含当前时间戳、随机 ID 或环境相关信息；
26. 不允许把示例 artifact 当成新的 canonical schema。

---

## 5. 需要修改的文件

预计新增：

```text
examples/llm_review_artifacts/README.md

examples/llm_review_artifacts/single-file/input.md
examples/llm_review_artifacts/single-file/profile.yml
examples/llm_review_artifacts/single-file/deterministic-report.md
examples/llm_review_artifacts/single-file/llm-result.json
examples/llm_review_artifacts/single-file/llm-report.md
examples/llm_review_artifacts/single-file/review-index.md

examples/llm_review_artifacts/batch/input/article-a.md
examples/llm_review_artifacts/batch/input/article-b.md
examples/llm_review_artifacts/batch/input/article-with-llm-error.md
examples/llm_review_artifacts/batch/profile.yml
examples/llm_review_artifacts/batch/deterministic-report.md
examples/llm_review_artifacts/batch/batch-llm-result.json
examples/llm_review_artifacts/batch/batch-llm-report.md
examples/llm_review_artifacts/batch/batch-review-index.md

tests/test_llm_artifact_examples.py
```

预计修改：

```text
tests/test_llm_provider_usage_docs.py
docs/CLI.md
docs/LLM_PROVIDER_USAGE.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
docs/CI.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前仓库已有 `examples/`、`docs/examples/` 或 `tests/fixtures/` 规范，请优先遵守仓库已有结构，但必须保证 examples 是用户可直接阅读的示例，而不只是测试 fixture。

---

## 6. 实现要求

### 6.1 示例目录要求

新增：

```text
examples/llm_review_artifacts/
```

该目录必须包含一个顶层 README：

```text
examples/llm_review_artifacts/README.md
```

README 应解释：

1. 这些示例是什么；
2. single-file 示例如何阅读；
3. batch 示例如何阅读；
4. deterministic output 与 LLM output 的区别；
5. 哪些文件是 machine-readable；
6. 哪些文件是 human-readable；
7. 哪些文件只是导航 / presentation layer；
8. LLM findings 为什么是 advisory；
9. manual review checklist 为什么不持久化；
10. quality gate 为什么仍只基于 deterministic review；
11. batch partial failure 示例如何理解。

README 中应包含一个 artifact map 表格，例如：

```markdown
| Artifact | Format | Source | Purpose | Canonical |
| --- | --- | --- | --- | --- |
| deterministic-report.md | Markdown | deterministic review | human-readable deterministic report | yes, for deterministic review |
| llm-result.json | JSON | LLM review | machine-readable LLM result | yes, for LLM layer |
| llm-report.md | Markdown | LLM review | human-readable advisory report | no |
| review-index.md | Markdown | report index | navigation and interpretation | no |
```

### 6.2 Single-file 示例要求

新增：

```text
examples/llm_review_artifacts/single-file/
```

必须包含：

```text
input.md
profile.yml
deterministic-report.md
llm-result.json
llm-report.md
review-index.md
```

`input.md` 应是一个简短、虚构、无敏感信息的 Markdown 示例。

建议包含：

1. 标题；
2. 一段普通正文；
3. 一个可能触发 deterministic rule 的词或表达；
4. 一个适合 LLM advisory review 的表达，例如夸大宣传、语气不稳或逻辑不清。

`profile.yml` 应是最小可读的 profile 示例。

要求：

1. 不要依赖真实业务敏感词；
2. 不要包含真实品牌风险内容；
3. 不要包含真实个人信息；
4. 不要包含政治、医疗、金融等高风险真实断言；
5. 示例应稳定、短小、可读。

`deterministic-report.md` 应展示 deterministic findings。

`llm-result.json` 应是合法 JSON，并展示至少一个 LLM finding。

`llm-report.md` 应包含以下 section：

```text
# LLM Review Report
## Summary
## Advisory Policy
## Severity Counts
## Findings
## Manual Review Checklist
## Detailed Findings
```

`review-index.md` 应包含以下 section：

```text
# Review Output Index
## Summary
## Output Files
## Interpretation
## Deterministic Review Summary
## LLM Review Summary
## Manual Review Workflow
```

### 6.3 Batch 示例要求

新增：

```text
examples/llm_review_artifacts/batch/
```

必须包含：

```text
input/article-a.md
input/article-b.md
input/article-with-llm-error.md
profile.yml
deterministic-report.md
batch-llm-result.json
batch-llm-report.md
batch-review-index.md
```

batch 示例应覆盖：

1. 至少一个文件有 deterministic finding；
2. 至少一个文件有 LLM advisory finding；
3. 至少一个文件无 LLM finding；
4. 至少一个文件展示 LLM execution error / partial failure。

`batch-llm-result.json` 应是合法 JSON，并包含：

1. per-file success；
2. per-file no findings；
3. per-file error；
4. schema version；
5. 不包含 secret；
6. 不包含真实 provider response；
7. 不包含真实 API key；
8. 不包含时间戳。

`batch-llm-report.md` 应包含：

```text
# Batch LLM Review Report
## Summary
## Advisory Policy
## Severity Counts
## File Status
## Manual Review Checklist
## LLM Execution Review Checklist
## Findings By File
```

`batch-review-index.md` 应包含：

```text
# Review Output Index
## Summary
## Output Files
## Interpretation
## Deterministic Review Summary
## LLM Review Summary
## Manual Review Workflow
```

如果当前 renderer 实际输出 section 与上述略有差异，应以当前已测试的实际输出为准，但必须展示同等信息。

### 6.4 示例数据一致性

示例 artifact 之间必须保持基本一致：

1. `review-index.md` 中列出的路径必须真实存在；
2. `llm-report.md` 中的 finding 数量应与 `llm-result.json` 大体一致；
3. `batch-llm-report.md` 中的 file status 应与 `batch-llm-result.json` 一致；
4. `batch-review-index.md` 中的 LLM error summary 应与 `batch-llm-result.json` 一致；
5. manual review checklist 的 ID 应稳定；
6. execution review checklist 的 ID 应稳定；
7. 示例中不能出现互相矛盾的说明，例如一边说 LLM not enabled，一边展示 LLM findings。

### 6.5 示例生成方式

本任务不要求新增自动生成脚本。

允许 Agent 手工创建 curated examples，但必须满足测试验证。

不允许：

1. 在测试中调用真实 LLM；
2. 在示例中放入真实 provider 输出；
3. 在示例中要求真实 API key；
4. 在示例中加入当前时间戳；
5. 在示例中加入本机绝对路径。

如果 Agent 选择通过现有 renderer 辅助生成示例，必须确保最终提交的是稳定静态文件，且测试不依赖真实网络。

### 6.6 新增示例测试

新增：

```text
tests/test_llm_artifact_examples.py
```

至少覆盖：

1. example root README exists；
2. single-file example files exist；
3. batch example files exist；
4. single-file `llm-result.json` 是合法 JSON；
5. batch `batch-llm-result.json` 是合法 JSON；
6. single-file LLM report 包含 `## Advisory Policy`；
7. single-file LLM report 包含 `## Manual Review Checklist`；
8. single-file report index 包含 `## Manual Review Workflow`；
9. batch LLM report 包含 `## LLM Execution Review Checklist`；
10. batch report index 包含 `## Manual Review Workflow`；
11. example files do not contain `OPENAI_API_KEY`；
12. example files do not contain obvious placeholder secret values like `sk-`；
13. example files do not contain current timestamp-like generated text if avoidable；
14. README contains artifact map；
15. README states LLM findings are advisory；
16. README states quality gate is deterministic-only；
17. README states checklist status is not persisted；
18. output paths referenced in README or index exist where practical。

### 6.7 文档断言测试

如果已有：

```text
tests/test_llm_provider_usage_docs.py
```

需要更新，确保文档中包含：

1. `examples/llm_review_artifacts`；
2. `deterministic-report.md`；
3. `llm-result.json`；
4. `llm-report.md`；
5. `review-index.md`；
6. `Manual Review Checklist`；
7. `LLM Execution Review Checklist`；
8. advisory；
9. deterministic-only quality gate。

### 6.8 输出稳定性

所有示例必须稳定，不应包含：

1. 当前时间戳；
2. 随机 UUID；
3. 本机绝对路径；
4. 当前用户名；
5. API key；
6. secret；
7. 真实用户内容；
8. 真实未授权文章；
9. 网络请求结果；
10. provider 原始响应。

---

## 7. 测试要求

### 7.1 新增示例测试

新增并运行：

```text
tests/test_llm_artifact_examples.py
```

至少覆盖：

1. 示例目录存在；
2. single-file 示例完整；
3. batch 示例完整；
4. JSON 示例可解析；
5. Markdown 示例包含必要 section；
6. README 包含 artifact map；
7. README 明确 canonical / presentation 边界；
8. README 明确 LLM findings advisory；
9. README 明确 manual review checklist 不持久化；
10. README 明确 quality gate deterministic-only；
11. batch 示例包含 partial failure；
12. 示例文件不包含 API key / secret；
13. 示例路径引用基本有效；
14. 示例输出稳定。

### 7.2 更新文档断言测试

更新：

```text
tests/test_llm_provider_usage_docs.py
```

或项目中对应文档测试，确保新增示例在文档中被引用。

### 7.3 全量测试

完成后必须运行：

```bash
uv run pytest tests/test_llm_artifact_examples.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest
```

如果示例测试还影响其他文档或 CLI 测试，应额外运行相关测试。

---

## 8. 文档更新要求

### 8.1 examples/llm_review_artifacts/README.md

必须新增完整说明，包含：

1. 示例目录结构；
2. single-file 示例说明；
3. batch 示例说明；
4. artifact map；
5. canonical machine-readable 输出说明；
6. human-readable report 说明；
7. presentation-only 输出说明；
8. LLM advisory policy 说明；
9. manual review checklist 说明；
10. batch execution review checklist 说明；
11. quality gate 边界说明；
12. 如何在 CI artifact 中使用这些示例作为参考。

### 8.2 docs/CLI.md

需要补充：

1. 指向 `examples/llm_review_artifacts`；
2. 说明可以参考示例理解 `--output`、`--llm-output`、`--llm-report`、`--report-index`；
3. 说明示例不需要真实 API key；
4. 说明示例中的 LLM findings 是 advisory；
5. 说明示例中的 checklist 是 presentation-only。

### 8.3 docs/LLM_PROVIDER_USAGE.md

需要补充：

1. artifact examples 位置；
2. single-file artifact workflow；
3. batch artifact workflow；
4. partial failure 示例；
5. manual review checklist 示例；
6. 推荐真实验证时先对比示例输出；
7. 示例不代表真实 provider 质量，只代表 artifact contract。

### 8.4 docs/DATA_MODELS.md

需要补充：

1. 示例 artifact 与 canonical schema 的关系；
2. LLM JSON sidecar 是 LLM 层 canonical machine-readable 示例；
3. Markdown report / index / checklist 是 presentation-only 示例；
4. 示例不新增 schema；
5. 示例不改变现有模型。

### 8.5 docs/ARCHITECTURE.md

需要补充：

1. examples 在架构中的作用；
2. examples 是 artifact contract documentation；
3. examples 不参与运行时；
4. examples 不负责 provider；
5. examples 不负责 quality gate；
6. examples 可作为 API / MCP / GUI 后续设计参考。

### 8.6 docs/CI.md

需要补充：

1. 示例如何帮助理解 CI artifact；
2. deterministic report 是 CI gate 依据；
3. LLM report / report index / checklist 是 CI artifact；
4. partial failure 示例如何辅助排查；
5. 示例不改变 CI pass/fail 行为。

### 8.7 PROJECT_STATE.md

记录 TASK-0075 完成后项目状态：

1. 已新增 LLM review artifact examples；
2. single-file artifact 示例已完成；
3. batch artifact 示例已完成；
4. partial failure 示例已完成；
5. manual review checklist 示例已完成；
6. 示例仅作为文档与测试 artifact；
7. runtime behavior 未改变；
8. API / MCP / GUI 仍未开始。

### 8.8 CHANGELOG.md

新增 TASK-0075 条目，说明：

1. 新增 `examples/llm_review_artifacts/`；
2. 新增 single-file artifact examples；
3. 新增 batch artifact examples；
4. 新增 partial failure artifact examples；
5. 新增 manual review checklist examples；
6. 新增 artifact example tests；
7. 不改变 runtime behavior；
8. 不改变 schema；
9. 不改变 quality gate。

---

## 9. 验收标准

本任务完成后，应满足以下标准：

1. 新增 `examples/llm_review_artifacts/README.md`；
2. 新增 single-file 示例输入、profile 和 artifact；
3. 新增 batch 示例输入、profile 和 artifact；
4. single-file 示例包含 deterministic report；
5. single-file 示例包含 LLM JSON sidecar；
6. single-file 示例包含 LLM Markdown report；
7. single-file 示例包含 report index；
8. batch 示例包含 deterministic report；
9. batch 示例包含 batch LLM JSON sidecar；
10. batch 示例包含 batch LLM Markdown report；
11. batch 示例包含 batch report index；
12. batch 示例包含 partial failure；
13. LLM report 示例包含 advisory policy；
14. LLM report 示例包含 manual review checklist；
15. batch LLM report 示例包含 execution review checklist；
16. report index 示例包含 manual review workflow；
17. README 包含 artifact map；
18. README 明确 canonical / presentation 边界；
19. README 明确 LLM findings advisory；
20. README 明确 quality gate deterministic-only；
21. README 明确 checklist 不持久化；
22. 新增 `tests/test_llm_artifact_examples.py`；
23. JSON 示例可被测试解析；
24. Markdown 示例 section 可被测试断言；
25. 示例中不包含 API key / secret；
26. 不修改任何 result schema；
27. 不修改任何 CLI 行为；
28. 不修改任何 renderer 行为；
29. 不新增真实 provider；
30. 不新增 API / MCP / GUI；
31. `uv run pytest tests/test_llm_artifact_examples.py` 通过；
32. `uv run pytest` 全量通过；
33. 文档已同步更新。

---

## 10. 风险与注意事项

1. 不要把 examples 做成运行时依赖；
2. 不要让 tests 调用真实 LLM；
3. 不要让 examples 需要真实 API key；
4. 不要在 examples 中放 secret；
5. 不要在 examples 中放真实用户文章；
6. 不要在 examples 中放真实敏感业务内容；
7. 不要修改 renderer 以适配示例；
8. 不要修改 schema；
9. 不要修改 CLI 行为；
10. 不要把 Markdown checklist 当作持久化状态；
11. 不要把 report index 当作 canonical schema；
12. 不要把示例中的 LLM output 描述成真实 provider 质量保证；
13. 不要加入时间戳、随机 UUID 或机器相关路径；
14. 不要把本任务扩展成 API / MCP / GUI；
15. 不要把本任务扩展成真实 provider smoke test。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_artifact_examples.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest
```

如果修改影响其他文档或测试，请额外运行相关测试。

---
