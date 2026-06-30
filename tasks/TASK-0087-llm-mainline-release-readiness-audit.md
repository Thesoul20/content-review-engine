# TASK-0087: LLM Mainline Integration Release Readiness Audit

## 1. 背景

当前项目已经完成 deterministic review 主线能力，并逐步完成 LLM 语义审计主线辅助能力。

截至目前，LLM 阶段已经完成：

1. LLM provider boundary；
2. mock reviewer；
3. LLM runner；
4. secret resolver；
5. provider config / factory；
6. PydanticAI 测试模型路径；
7. `llm-check` smoke check；
8. single-file `--enable-llm`；
9. single-file / batch `--llm-output` raw sidecar；
10. explicit `--combined-output`；
11. combined output 文档、behavior matrix、reference examples；
12. stable combined envelope builder；
13. stable combined Markdown report rendering；
14. explicit opt-in LLM quality gate policy；
15. `--llm-fail-on`；
16. combined envelope 中的 `llm.quality_gate` metadata；
17. combined Markdown report 中的 LLM gate result 展示。

前序任务已经明确并保持以下边界：

1. `--output` 是 deterministic 主输出；
2. `--llm-output` 是 raw LLM sidecar；
3. `--combined-output` 是 explicit opt-in 的 combined envelope / combined report；
4. `--combined-output` 不会自动启用 LLM；
5. `--llm-fail-on` 不会自动启用 LLM；
6. `--fail-on` 仍然 deterministic-only；
7. LLM findings 默认不影响 exit code；
8. 只有显式传入 `--llm-fail-on` 时，LLM findings 才能影响 exit code；
9. LLM findings 不进入 deterministic `ReviewResult.findings`；
10. LLM findings 不进入 deterministic `severity_counts`；
11. LLM findings 不进入 deterministic `rule_counts`；
12. raw LLM sidecar schema 不被 LLM gate 污染。

现在需要一张收口任务卡，对 LLM 主线集成阶段做 release readiness audit，确保 CLI、schema、reports、examples、docs、quality gate、tests 之间没有不一致、不完整或行为漂移。

本任务不是继续新增大功能，而是做最终一致性审计、补齐缺口、固定契约。

---

## 2. 任务目标

本任务目标是：

> 对 LLM mainline integration 阶段进行 release readiness audit，确认 0083–0086 的 combined output、combined envelope、combined Markdown report、LLM quality gate、docs、examples 和 tests 已经形成稳定、清晰、可维护的契约。

完成后应达到：

1. CLI 参数边界清晰且文档一致；
2. `--output` / `--llm-output` / `--combined-output` / `--llm-fail-on` 行为矩阵完整；
3. single-file 与 batch 行为一致；
4. JSON examples 与 runtime schema 兼容；
5. Markdown examples 与 renderer 输出一致；
6. docs 中对 deterministic gate 与 LLM gate 的说明一致；
7. docs 中对 sidecar / combined envelope / report 的说明一致；
8. tests 覆盖主要行为矩阵；
9. `PROJECT_STATE.md` 准确反映 LLM 阶段状态；
10. `CHANGELOG.md` 有清晰收口记录；
11. 不引入新的 runtime 行为漂移。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 审计并补齐 LLM CLI 行为矩阵。
2. 审计并补齐 `--output` / `--llm-output` / `--combined-output` / `--llm-fail-on` 的文档边界。
3. 审计并补齐 single-file 与 batch 的行为一致性测试。
4. 审计并补齐 combined JSON examples 的兼容性测试。
5. 审计并补齐 combined Markdown examples 的兼容性测试。
6. 审计并补齐 docs 中 deterministic quality gate 与 LLM quality gate 的边界说明。
7. 审计并补齐 combined envelope 与 combined Markdown report 的关系说明。
8. 审计并补齐 raw LLM sidecar 与 combined envelope 的关系说明。
9. 添加小型 regression tests 来固定已实现行为。
10. 刷新 reference examples，但只在 runtime 输出格式已经发生合法扩展时进行。
11. 更新 `PROJECT_STATE.md`，记录 LLM mainline integration release readiness 状态。
12. 更新 `CHANGELOG.md`，记录本次收口审计。
13. 如发现轻微命名、文档或测试不一致，可以修复。
14. 如发现已有 report 文案缺少关键边界说明，可以补充。
15. 如发现 CLI help 缺少关键参数说明，可以补充。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许新增 API。
2. 不允许新增 MCP 接口。
3. 不允许新增 GUI / Web / Tauri 前端。
4. 不允许新增数据库、Supabase、用户系统或商业化能力。
5. 不允许新增真实 LLM provider。
6. 不允许修改 PydanticAI provider 的真实调用逻辑。
7. 不允许修改 provider interface。
8. 不允许改变 deterministic review engine。
9. 不允许改变 deterministic JSON schema。
10. 不允许改变 raw LLM sidecar schema。
11. 不允许改变 combined JSON envelope 的既有字段语义。
12. 不允许改变 `--output` 的 deterministic 主输出语义。
13. 不允许改变 `--llm-output` 的 raw LLM sidecar 语义。
14. 不允许改变 `--combined-output` 的 explicit opt-in 语义。
15. 不允许让 `--combined-output` 自动启用 LLM。
16. 不允许让 `--llm-fail-on` 自动启用 LLM。
17. 不允许改变 `--fail-on` 的 deterministic-only 语义。
18. 不允许让 LLM findings 默认影响 exit code。
19. 不允许把 LLM findings 合并进 deterministic `ReviewResult.findings`。
20. 不允许让 LLM findings 进入 deterministic `severity_counts`。
21. 不允许让 LLM findings 进入 deterministic `rule_counts`。
22. 不允许大规模重构 CLI、reports、LLM runner 或 batch runner。
23. 不允许引入 breaking changes 来让 tests 重新适配。
24. 不允许删除已有 examples 或降低 examples 测试覆盖。
25. 不允许把 release readiness audit 变成新功能开发任务。

---

## 5. 预计需要修改的文件

预计包括但不限于：

```text id="m28hqj"
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
examples/llm_review_artifacts/README.md
PROJECT_STATE.md
CHANGELOG.md

tests/test_cli.py
tests/test_ci_docs.py
tests/test_llm_provider_usage_docs.py
tests/test_llm_combined_output_docs.py
tests/test_llm_artifact_examples.py
tests/test_llm_single_file_combined_cli_output.py
tests/test_llm_batch_combined_cli_output.py
tests/test_llm_single_file_quality_gate_cli.py
tests/test_llm_batch_quality_gate_cli.py
tests/test_llm_combined_markdown_report.py
```

如果审计发现已有测试文件已经覆盖对应场景，应优先扩展现有测试文件，不要创建重复测试文件。

如果需要新增测试文件，可以新增：

```text id="gkk0dc"
tests/test_llm_mainline_release_readiness.py
```

但只有在现有测试文件不适合承载 release readiness matrix 时才新增。

本任务原则上不应修改 `src/` runtime 代码。
如果必须修改 `src/`，只能是修复审计中发现的轻微文案、CLI help、report note 或明显的非行为性一致性问题，并必须在最终输出中单独说明。

---

## 6. 实现要求

### 6.1 LLM CLI behavior matrix audit

需要审计并补齐 CLI 行为矩阵。

至少覆盖以下参数组合：

```text id="i9xbef"
--output
--llm-output
--combined-output
--enable-llm
--fail-on
--llm-fail-on
```

需要确认并测试：

1. `--output` 不启用 LLM；
2. `--llm-output` 不自动启用 LLM，除非现有项目已明确不同语义；
3. `--combined-output` 不自动启用 LLM；
4. `--llm-fail-on` 不自动启用 LLM；
5. `--llm-fail-on` without `--enable-llm` 返回 usage error；
6. `--fail-on` 只看 deterministic findings；
7. `--llm-fail-on` 只看 LLM findings；
8. `--fail-on` 和 `--llm-fail-on` 可以并存；
9. deterministic gate 失败时 exit code 为 `1`；
10. explicit LLM gate 失败时 exit code 为 `1`；
11. LLM provider / runner error 仍保持既有错误行为；
12. raw sidecar、combined JSON、combined Markdown 可以并存。

### 6.2 Single-file 与 batch 对齐

需要确认 single-file 与 batch 在以下方面一致：

1. LLM 启用方式；
2. raw sidecar 输出边界；
3. combined output opt-in 语义；
4. combined JSON envelope 中的 quality gate metadata；
5. combined Markdown report 中的 quality gate 展示；
6. `--llm-fail-on` 不自动启用 LLM；
7. invalid severity 行为；
8. exit code 合并规则；
9. examples 的 reference-only 定位；
10. docs 中的描述。

### 6.3 Examples audit

需要审计：

```text id="zzdsbc"
examples/llm_review_artifacts/single-file/combined-result.json
examples/llm_review_artifacts/single-file/combined-report.md
examples/llm_review_artifacts/batch/batch-combined-result.json
examples/llm_review_artifacts/batch/batch-combined-report.md
examples/llm_review_artifacts/README.md
```

要求：

1. JSON examples 可解析；
2. JSON examples 包含 expected top-level fields；
3. JSON examples 的 `llm.quality_gate` metadata 与 docs 一致；
4. Markdown examples 包含 stable headings；
5. Markdown examples 包含 artifact boundary；
6. Markdown examples 包含 deterministic-only default note；
7. Markdown examples 包含 explicit LLM gate note；
8. examples 不包含 API key；
9. examples 不包含 secret；
10. examples 不包含 traceback；
11. examples 不包含不稳定临时目录；
12. examples 不包含本地绝对路径；
13. README 明确 examples 是 reference-only，不是实时运行输出保证。

### 6.4 Docs consistency audit

需要重点审计以下文档：

```text id="dsqy5j"
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
```

需要确认这些文档对以下概念描述一致：

1. deterministic review；
2. LLM sidecar；
3. combined envelope；
4. combined Markdown report；
5. deterministic quality gate；
6. explicit LLM quality gate；
7. `--fail-on`；
8. `--llm-fail-on`；
9. `--enable-llm`；
10. `--combined-output`；
11. exit code；
12. provider responsibility；
13. report responsibility；
14. CI risk and recommendation。

### 6.5 Release readiness checklist

需要在 `PROJECT_STATE.md` 增加或更新 LLM 阶段 release readiness 状态。

建议包含：

```text id="bbi421"
LLM mainline integration status:
- provider boundary: complete
- runner: complete
- CLI opt-in execution: complete
- raw sidecar output: complete
- combined envelope: complete
- combined Markdown report: complete
- explicit LLM quality gate: complete
- default deterministic-only quality gate: preserved
- docs/examples/tests audit: complete
- API/MCP/GUI: not introduced
```

### 6.6 CHANGELOG 收口记录

需要在 `CHANGELOG.md` 中记录本次 release readiness audit。

建议说明：

1. 完成 LLM mainline integration audit；
2. 固化 CLI behavior matrix；
3. 固化 docs / examples / tests consistency；
4. 保持默认 deterministic-only gate；
5. 未引入 API / MCP / GUI / provider behavior changes。

---

## 7. 测试要求

本任务必须新增或更新测试。

### 7.1 CLI matrix tests

需要新增或更新测试，覆盖：

1. `--combined-output` 不自动启用 LLM；
2. `--llm-fail-on` 不自动启用 LLM；
3. `--llm-fail-on` without `--enable-llm` 返回 usage error；
4. `--fail-on` 和 `--llm-fail-on` 独立；
5. deterministic gate failure exit code；
6. explicit LLM gate failure exit code；
7. both gates pass exit code；
8. both gates can coexist；
9. single-file 和 batch 均覆盖。

可以更新：

```text id="a2uyj6"
tests/test_llm_single_file_quality_gate_cli.py
tests/test_llm_batch_quality_gate_cli.py
tests/test_cli.py
```

### 7.2 Combined output tests

需要确认或补齐：

```text id="eyxjk3"
tests/test_llm_single_file_combined_cli_output.py
tests/test_llm_batch_combined_cli_output.py
tests/test_llm_combined_markdown_report.py
```

测试重点：

1. combined JSON 包含 `llm.quality_gate` metadata；
2. combined Markdown 展示 LLM quality gate result；
3. `.json` 和 `.md` 后缀 dispatch 行为稳定；
4. raw sidecar 与 combined artifact 可以并存；
5. deterministic output 与 combined artifact 可以并存。

### 7.3 Docs tests

需要确认或补齐：

```text id="gpk0up"
tests/test_llm_combined_output_docs.py
tests/test_llm_provider_usage_docs.py
tests/test_ci_docs.py
```

测试重点：

1. docs 说明 `--llm-fail-on` 是 explicit opt-in；
2. docs 说明默认 deterministic-only；
3. docs 说明 `--llm-fail-on` 不自动启用 LLM；
4. docs 说明 `--combined-output` 不自动启用 LLM；
5. docs 说明 `--fail-on` 与 `--llm-fail-on` 的区别；
6. docs 说明 provider 不负责 quality gate；
7. docs 说明 combined report 不等于 raw sidecar。

### 7.4 Examples tests

需要确认或补齐：

```text id="q19f4s"
tests/test_llm_artifact_examples.py
```

测试重点：

1. combined JSON examples 可解析；
2. combined JSON examples 包含 `llm.quality_gate`；
3. combined Markdown examples 包含 stable headings；
4. examples 不含 API key；
5. examples 不含 secret；
6. examples 不含 traceback；
7. examples 不含本地绝对路径；
8. README 标明 reference-only。

### 7.5 可选 release readiness test

如果现有测试文件难以覆盖整体矩阵，可以新增：

```text id="qxg5z5"
tests/test_llm_mainline_release_readiness.py
```

该测试文件可以只做轻量 contract tests，不应重复大量 CLI integration tests。

### 7.6 全量测试

完成后必须运行：

```bash id="m9eb7g"
uv run pytest
```

---

## 8. 文档更新要求

本任务需要更新以下文档：

```text id="s9hnp1"
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
examples/llm_review_artifacts/README.md
PROJECT_STATE.md
CHANGELOG.md
```

### 8.1 docs/CLI.md

需要确认：

1. 参数表完整；
2. behavior matrix 完整；
3. `--output` / `--llm-output` / `--combined-output` 边界清晰；
4. `--enable-llm` / `--llm-fail-on` 边界清晰；
5. `--fail-on` / `--llm-fail-on` 边界清晰；
6. exit code 行为清晰；
7. single-file 与 batch 示例清晰。

### 8.2 docs/CI.md

需要确认：

1. 默认 CI gate deterministic-only；
2. explicit LLM gate 使用方式；
3. non-blocking LLM review 推荐；
4. blocking LLM review 风险；
5. provider/network/cost/model stability 风险；
6. exit code 说明准确。

### 8.3 docs/ARCHITECTURE.md

需要确认：

1. LLM provider boundary；
2. LLM runner；
3. LLM sidecar；
4. combined envelope；
5. combined Markdown renderer；
6. LLM quality gate evaluator；
7. deterministic engine 与 LLM layer 的边界；
8. future API/MCP/GUI 未引入。

### 8.4 docs/DATA_MODELS.md

需要确认：

1. deterministic result；
2. raw LLM sidecar；
3. combined envelope；
4. `llm.quality_gate` metadata；
5. combined Markdown report 是 projection，不是 schema source of truth；
6. schema compatibility notes。

### 8.5 docs/LLM_PROVIDER_USAGE.md

需要确认：

1. provider 只负责 LLMReviewResult；
2. provider 不负责 combined envelope；
3. provider 不负责 quality gate；
4. `--llm-fail-on` 不自动启用 provider；
5. raw sidecar 与 combined output 的关系清晰。

### 8.6 examples README

需要确认：

1. examples 是 reference-only；
2. examples 不保证实时运行环境完全一致；
3. examples 不包含 secret；
4. examples 解释 single-file / batch combined artifacts。

### 8.7 PROJECT_STATE.md

需要更新：

1. LLM mainline integration release readiness audit 已完成；
2. 当前 LLM 能力边界；
3. 默认 deterministic-only gate 保持；
4. explicit LLM gate 可用；
5. API / MCP / GUI 尚未引入；
6. 下一阶段建议。

### 8.8 CHANGELOG.md

需要记录：

1. LLM mainline integration audit；
2. docs / examples / tests consistency updates；
3. no behavior-breaking changes；
4. no API / MCP / GUI introduced。

---

## 9. 验收标准

满足以下条件即可认为任务完成：

1. LLM CLI behavior matrix 已审计并补齐；
2. single-file 与 batch 行为一致性已审计；
3. combined JSON examples 已验证；
4. combined Markdown examples 已验证；
5. docs 中 artifact boundary 一致；
6. docs 中 quality gate boundary 一致；
7. docs 中 provider responsibility 一致；
8. tests 覆盖关键 LLM mainline integration 行为；
9. `PROJECT_STATE.md` 反映 LLM 阶段 release readiness；
10. `CHANGELOG.md` 记录本次 audit；
11. 未改变默认 deterministic-only quality gate；
12. 未改变 raw LLM sidecar schema；
13. 未改变 combined JSON envelope 既有字段语义；
14. 未改变 provider interface；
15. 未新增 API / MCP / GUI；
16. 全量测试通过。

---

## 10. 风险与注意事项

### 10.1 不要把 audit 任务变成功能任务

本任务是收口任务，不是新功能开发任务。

如发现需要新增大功能，应记录为后续任务，不要在本任务中实现。

### 10.2 不要改变默认 CI 行为

默认行为仍必须是：

```text id="h91r3s"
--fail-on = deterministic-only
LLM findings do not affect exit code unless --llm-fail-on is explicitly provided
```

### 10.3 不要把 LLM gate 写成合规保证

文档中不能暗示：

```text id="n4e3fc"
LLM quality gate = compliance guarantee
```

只能说明它是辅助 gate。

### 10.4 不要让 examples 变成不稳定产物

examples 应为稳定 reference artifacts，不应包含：

1. local absolute paths；
2. timestamps；
3. temp directories；
4. API keys；
5. secrets；
6. tracebacks；
7. machine-specific output。

### 10.5 不要急着进入 API / MCP

API / MCP 应作为 LLM 阶段收口之后的新阶段任务，不应混入本任务。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash id="ya1ygh"
uv run pytest tests/test_llm_single_file_quality_gate_cli.py
uv run pytest tests/test_llm_batch_quality_gate_cli.py
uv run pytest tests/test_llm_single_file_combined_cli_output.py
uv run pytest tests/test_llm_batch_combined_cli_output.py
uv run pytest tests/test_llm_combined_markdown_report.py
uv run pytest tests/test_llm_combined_output_docs.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest tests/test_ci_docs.py
uv run pytest tests/test_llm_artifact_examples.py
uv run pytest tests/test_cli.py
uv run pytest
```

如果新增了 release readiness 测试文件，也请运行：

```bash id="vm29ss"
uv run pytest tests/test_llm_mainline_release_readiness.py
```

---

