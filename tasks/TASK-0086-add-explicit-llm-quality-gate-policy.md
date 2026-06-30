# TASK-0086: Add Explicit LLM Quality Gate Policy

## 1. 背景

当前项目已经完成 deterministic review 主线能力，并逐步完成 LLM 语义审计相关能力，包括：

1. deterministic single-file / batch review；
2. deterministic JSON / Markdown report；
3. deterministic quality gate / CI；
4. LLM provider boundary；
5. LLM runner；
6. LLM sidecar output；
7. explicit combined output；
8. stable combined review envelope builder；
9. stable combined Markdown report rendering；
10. combined output 文档、reference examples 和兼容性测试。

前序任务已经明确：

1. `--output` 是 deterministic 主输出；
2. `--llm-output` 是 raw LLM sidecar；
3. `--combined-output` 是 explicit opt-in 的 combined envelope / combined report；
4. `--combined-output` 不会自动启用 LLM；
5. LLM findings 不进入 deterministic findings；
6. LLM findings 不进入 deterministic `severity_counts`；
7. LLM findings 不进入 deterministic `rule_counts`；
8. 默认 quality gate / `--fail-on` / CLI exit code 仍然 deterministic-only。

但是，随着 combined Markdown report 和 combined envelope 已经稳定，下一步可以考虑一个更实际的 CI 使用场景：

> 用户可能希望在显式开启 LLM 审计时，让 LLM findings 也可以作为独立的 quality gate 条件影响 exit code。

本任务的目标不是改变默认行为，而是新增一个明确、可测试、可文档化的 opt-in LLM quality gate policy。

---

## 2. 任务目标

本任务目标是：

> 新增显式 opt-in 的 LLM quality gate policy，让用户只有在明确传入新的 LLM gate 参数时，才允许 LLM findings 影响 CLI exit code；默认情况下 deterministic-only quality gate 行为保持完全不变。

完成后应达到：

1. 默认不启用 LLM quality gate；
2. 现有 `--fail-on` 仍然只作用于 deterministic findings；
3. 新增独立的 LLM gate 参数，例如 `--llm-fail-on`；
4. 只有用户显式传入 `--llm-fail-on` 时，LLM findings 才能参与 exit code 判断；
5. LLM findings 仍然不进入 deterministic `ReviewResult.findings`；
6. LLM findings 仍然不进入 deterministic `severity_counts` / `rule_counts`；
7. combined JSON / Markdown 可以展示 LLM gate policy 和 LLM gate result；
8. docs / CI 文档明确说明 deterministic gate 与 LLM gate 的区别；
9. 单文件和批量路径都需要覆盖；
10. 行为必须可测试、可复现、可维护。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增 LLM quality gate policy / result 的内部 helper 或数据结构。
2. 新增 CLI 参数，例如：

   * `--llm-fail-on <severity>`
3. 让 single-file LLM review 支持显式 LLM quality gate。
4. 让 batch LLM review 支持显式 LLM quality gate。
5. 在 combined envelope 中增加 LLM quality gate metadata。
6. 在 combined Markdown report 中展示 LLM quality gate behavior / result。
7. 更新 CLI help 和文档。
8. 更新 CI 文档，说明如何显式启用 LLM quality gate。
9. 新增或更新测试，覆盖默认 deterministic-only 行为和 explicit LLM gate 行为。
10. 更新 `PROJECT_STATE.md` 和 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许改变默认 quality gate 行为。
2. 不允许让 LLM findings 默认影响 exit code。
3. 不允许改变现有 `--fail-on` 的 deterministic-only 语义。
4. 不允许把 LLM findings 合并进 deterministic `ReviewResult.findings`。
5. 不允许让 LLM findings 进入 deterministic `severity_counts`。
6. 不允许让 LLM findings 进入 deterministic `rule_counts`。
7. 不允许改变 deterministic JSON schema。
8. 不允许改变 raw LLM sidecar schema，除非已有模型中存在可安全扩展 metadata 的位置。
9. 不允许改变 combined JSON envelope 的既有字段语义。
10. 不允许让 `--combined-output` 自动启用 LLM。
11. 不允许让 `--llm-fail-on` 自动启用 LLM，除非现有 CLI 已经有明确的 LLM 启用行为约定。
12. 不允许新增真实 LLM provider。
13. 不允许修改 PydanticAI provider 的真实调用逻辑。
14. 不允许新增 API / MCP / GUI。
15. 不允许引入数据库、Supabase、用户系统或商业化能力。
16. 不允许大规模重构 deterministic review engine。
17. 不允许把 LLM quality gate 与 deterministic quality gate 混成一个不可区分的结果。
18. 不允许删除或弱化 0083 / 0084 / 0085 已经明确的 artifact boundary 文档。

---

## 5. 预计需要修改的文件

预计包括但不限于：

```text id="r7c29p"
src/content_review_engine/cli.py

src/content_review_engine/llm/quality_gate.py
src/content_review_engine/llm/combined_envelope.py
src/content_review_engine/llm/__init__.py

src/content_review_engine/reports/combined_markdown.py
src/content_review_engine/reports/batch_combined_markdown.py

tests/test_llm_quality_gate.py
tests/test_llm_single_file_quality_gate_cli.py
tests/test_llm_batch_quality_gate_cli.py
tests/test_llm_single_file_combined_cli_output.py
tests/test_llm_batch_combined_cli_output.py
tests/test_llm_combined_markdown_report.py
tests/test_llm_combined_output_docs.py
tests/test_ci_docs.py
tests/test_cli.py

docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果仓库中已经存在 deterministic quality gate helper，应参考其风格，但不要把 LLM gate 逻辑塞进 deterministic gate 逻辑里导致边界混乱。

如果仓库中已经存在 LLM quality gate 相关 helper，应优先复用和补齐测试，不要创建重复模块。

---

## 6. 实现要求

### 6.1 新增显式 CLI 参数

建议新增：

```text id="gx523e"
--llm-fail-on <severity>
```

参数语义：

1. 只作用于 LLM findings；
2. 与 existing `--fail-on` 相互独立；
3. 不改变 `--fail-on` 的 deterministic-only 行为；
4. 不传该参数时，LLM findings 不影响 exit code；
5. 传该参数时，如果 LLM findings 中存在达到阈值的 finding，则 CLI exit code 应为 `1`；
6. 支持的 severity 应与项目现有 severity 等级保持一致，例如：

   * `info`
   * `warning`
   * `error`
   * `critical`

如果现有 deterministic `--fail-on` 使用的是 severity threshold 语义，则 `--llm-fail-on` 应保持同样 threshold 语义。

如果现有 deterministic `--fail-on` 使用的是枚举匹配或列表语义，则 `--llm-fail-on` 应跟随现有风格。

### 6.2 不自动启用 LLM

`--llm-fail-on` 不应悄悄启用 LLM。

推荐行为：

1. 如果用户传入 `--llm-fail-on` 但没有启用 LLM review，应返回清晰 CLI usage error；
2. 该错误应提示用户需要显式启用 LLM review；
3. 不应静默忽略 `--llm-fail-on`；
4. 不应伪造空 LLM result；
5. 不应因为没有 LLM result 而错误地通过或失败。

如果项目当前对类似参数已有统一错误处理风格，应遵循现有风格。

### 6.3 LLM quality gate helper

建议新增或整理：

```python id="mgq3h8"
evaluate_llm_quality_gate(...)
```

可以返回明确的结果结构，例如：

```python id="y1u4r9"
LLMQualityGateResult(
    enabled=True,
    fail_on="error",
    failed=True,
    matched_finding_count=2,
    matched_severity_counts={
        "critical": 1,
        "error": 1,
        "warning": 0,
        "info": 0,
    },
)
```

具体是否使用 dataclass / Pydantic model / plain dict helper，应遵循仓库现有风格。

最低要求是：

1. 结果结构化；
2. JSON-compatible；
3. 可在 combined envelope 中展示；
4. 可在 combined Markdown report 中展示；
5. 可被测试稳定断言。

### 6.4 Single-file 行为

single-file review 行为应满足：

1. 不传 `--llm-fail-on` 时：

   * LLM findings 不影响 exit code；
   * existing tests 应保持通过。
2. 传 `--llm-fail-on error` 且存在 `error` 或 `critical` 级别 LLM finding 时：

   * CLI exit code 为 `1`。
3. 传 `--llm-fail-on critical` 且只存在 `error` 级别 LLM finding 时：

   * CLI exit code 不应因为 LLM gate 失败。
4. deterministic gate 和 LLM gate 同时存在时：

   * 任一 gate 失败，exit code 为 `1`；
   * 但输出中应能区分 deterministic gate 与 LLM gate。

### 6.5 Batch 行为

batch review 行为应满足：

1. 不传 `--llm-fail-on` 时：

   * batch LLM findings 不影响 exit code；
   * existing deterministic quality gate 行为不变。
2. 传 `--llm-fail-on error` 且任一文件存在 `error` 或 `critical` 级别 LLM finding 时：

   * CLI exit code 为 `1`。
3. batch LLM quality gate result 应能展示：

   * enabled；
   * fail_on；
   * failed；
   * matched file count；
   * matched finding count；
   * matched severity counts；
   * optionally matched file paths。
4. batch 文件顺序应保持 deterministic。
5. batch deterministic summary 不应被 LLM findings 污染。

### 6.6 Combined envelope 扩展

combined envelope 可以增加一个可选区域，例如：

```json id="qaixdf"
"quality_gates": {
  "deterministic": {
    "enabled": true,
    "fail_on": "error",
    "failed": false
  },
  "llm": {
    "enabled": true,
    "fail_on": "error",
    "failed": true,
    "matched_finding_count": 2
  }
}
```

具体字段应根据现有结构调整。

要求：

1. 不改变 existing combined envelope 既有字段语义；
2. 如果添加新字段，应保持向后兼容；
3. 未启用 LLM quality gate 时，应明确表现为 disabled / absent，但不要伪造 failed result；
4. docs 和 tests 应覆盖该字段。

### 6.7 Combined Markdown report 更新

combined Markdown report 应展示 LLM quality gate policy。

建议在现有 `## Quality Gate Behavior` 章节中补充：

1. deterministic gate 是否启用；
2. deterministic `fail_on`；
3. deterministic gate 是否 failed；
4. LLM gate 是否启用；
5. LLM `fail_on`；
6. LLM gate 是否 failed；
7. LLM gate matched finding count；
8. 明确说明默认仍然 deterministic-only；
9. 只有显式传入 `--llm-fail-on` 时，LLM gate 才参与 exit code。

不得把 LLM gate 描述成默认行为。

### 6.8 Raw LLM sidecar

本任务不应强制修改 raw LLM sidecar schema。

如果当前 sidecar 有 metadata 扩展位，可以记录 LLM quality gate policy；如果没有，不要为了本任务破坏 sidecar schema。

优先让 combined envelope / combined report 展示 quality gate result。

### 6.9 CLI exit code 合并规则

最终 exit code 规则应清晰：

```text id="agv970"
exit_code = 1 if deterministic_gate_failed or explicit_llm_gate_failed else 0
```

其中：

1. `deterministic_gate_failed` 来自 existing deterministic `--fail-on`；
2. `explicit_llm_gate_failed` 只有在 `--llm-fail-on` 显式传入时才可能为 true；
3. LLM provider error 的处理语义应保持现有行为；
4. LLM 未启用时不得计算 LLM gate。

---

## 7. 测试要求

本任务必须新增或更新测试。

### 7.1 新增 LLM quality gate unit tests

建议新增：

```text id="h8rr8e"
tests/test_llm_quality_gate.py
```

测试至少覆盖：

1. 默认 disabled result；
2. `--llm-fail-on error` 匹配 `error` finding；
3. `--llm-fail-on error` 匹配 `critical` finding；
4. `--llm-fail-on critical` 不匹配 `error` finding；
5. `--llm-fail-on warning` 匹配 warning / error / critical；
6. 空 LLM findings 不失败；
7. severity counts 稳定；
8. batch matched file count 稳定；
9. invalid severity 报错或被 CLI 拒绝；
10. serialization output 是 JSON-compatible。

### 7.2 新增 single-file CLI tests

建议新增：

```text id="6dfpr4"
tests/test_llm_single_file_quality_gate_cli.py
```

测试至少覆盖：

1. 不传 `--llm-fail-on` 时，LLM findings 不影响 exit code；
2. 传 `--llm-fail-on error` 且有 matching LLM finding 时，exit code 为 `1`；
3. 传 `--llm-fail-on critical` 且只有 error LLM finding 时，exit code 不因 LLM gate 失败；
4. deterministic `--fail-on` 和 LLM `--llm-fail-on` 可以并存；
5. `--llm-fail-on` 不自动启用 LLM；
6. 未启用 LLM 但传 `--llm-fail-on` 时，CLI 给出清晰错误；
7. invalid severity 被拒绝；
8. combined Markdown report 中展示 LLM gate result。

### 7.3 新增 batch CLI tests

建议新增：

```text id="3zfjod"
tests/test_llm_batch_quality_gate_cli.py
```

测试至少覆盖：

1. 不传 `--llm-fail-on` 时，batch LLM findings 不影响 exit code；
2. 传 `--llm-fail-on error` 且任一文件有 matching LLM finding 时，exit code 为 `1`；
3. matched file count 正确；
4. matched finding count 正确；
5. deterministic batch summary 不被 LLM findings 污染；
6. batch combined Markdown report 中展示 LLM gate result；
7. `--llm-fail-on` 不自动启用 LLM；
8. invalid severity 被拒绝。

### 7.4 更新 combined output tests

需要更新或确认：

```text id="xuze2d"
tests/test_llm_single_file_combined_cli_output.py
tests/test_llm_batch_combined_cli_output.py
tests/test_llm_combined_markdown_report.py
```

测试重点：

1. combined JSON envelope 可以包含 LLM quality gate metadata；
2. combined Markdown report 可以展示 LLM quality gate policy；
3. 未启用 LLM gate 时，combined output 明确表示 disabled 或不展示 failed；
4. existing JSON schema 兼容性不被破坏；
5. `.json` 和 `.md` 输出路径都不漂移。

### 7.5 更新 docs / CI tests

需要更新或确认：

```text id="pon1rn"
tests/test_llm_combined_output_docs.py
tests/test_llm_provider_usage_docs.py
tests/test_ci_docs.py
tests/test_cli.py
```

测试重点：

1. `docs/CLI.md` 说明 `--llm-fail-on`；
2. `docs/CI.md` 说明 LLM quality gate 是 explicit opt-in；
3. docs 明确默认仍 deterministic-only；
4. docs 明确 `--fail-on` 和 `--llm-fail-on` 的区别；
5. CLI help 包含新参数；
6. invalid severity 行为被覆盖。

### 7.6 全量测试

完成后必须运行：

```bash id="qxzhv0"
uv run pytest
```

---

## 8. 文档更新要求

本任务需要更新以下文档：

```text id="zfrxym"
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
PROJECT_STATE.md
CHANGELOG.md
```

### 8.1 docs/CLI.md

需要补充：

1. `--llm-fail-on` 参数说明；
2. `--fail-on` 与 `--llm-fail-on` 的区别；
3. 默认 quality gate 仍 deterministic-only；
4. `--llm-fail-on` 不自动启用 LLM；
5. `--combined-output` 不自动启用 LLM；
6. deterministic gate 与 LLM gate 同时失败时 exit code 行为；
7. single-file 示例；
8. batch 示例。

### 8.2 docs/CI.md

需要补充：

1. 默认 CI quality gate 仍 deterministic-only；
2. 如何显式开启 LLM quality gate；
3. LLM quality gate 的适用场景；
4. LLM quality gate 的风险；
5. 推荐在 CI 中先以 non-blocking mode 使用 LLM review；
6. 如果启用 `--llm-fail-on`，应明确 provider 稳定性、成本、网络和模型输出一致性风险。

### 8.3 docs/ARCHITECTURE.md

需要补充 LLM quality gate 的架构位置：

```text id="qjh1ta"
LLMReviewResult
        ↓
LLM quality gate evaluator
        ↓
explicit LLM gate result
        ↓
combined envelope / combined report / CLI exit code
```

并强调：

1. LLM quality gate 不属于 deterministic rule engine；
2. LLM quality gate 不改变 deterministic ReviewResult；
3. LLM quality gate 必须显式启用；
4. CLI exit code 是 deterministic gate 与 explicit LLM gate 的组合结果。

### 8.4 docs/DATA_MODELS.md

需要补充：

1. LLM quality gate policy；
2. LLM quality gate result；
3. single-file result 字段；
4. batch result 字段；
5. serialization contract；
6. 与 deterministic quality gate 的区别。

### 8.5 docs/LLM_PROVIDER_USAGE.md

需要补充：

1. provider 只负责产生 LLMReviewResult；
2. provider 不负责判断 CI 是否失败；
3. LLM quality gate 在 provider 之后执行；
4. `--llm-fail-on` 不自动启用 provider；
5. LLM quality gate 结果可以进入 combined output。

### 8.6 PROJECT_STATE.md

记录 TASK-0086 完成的能力：

1. 显式 LLM quality gate policy；
2. `--llm-fail-on`；
3. single-file / batch opt-in gate；
4. default deterministic-only behavior unchanged。

### 8.7 CHANGELOG.md

记录本次新增 CLI 参数、LLM gate helper、测试和文档更新。

---

## 9. 验收标准

满足以下条件即可认为任务完成：

1. 新增显式 LLM quality gate 参数，例如 `--llm-fail-on`；
2. 默认不启用 LLM quality gate；
3. `--fail-on` 仍然 deterministic-only；
4. LLM findings 不进入 deterministic findings；
5. LLM findings 不进入 deterministic severity / rule counts；
6. `--llm-fail-on` 不自动启用 LLM；
7. 未启用 LLM 但传入 `--llm-fail-on` 时有清晰错误；
8. single-file LLM gate 行为正确；
9. batch LLM gate 行为正确；
10. combined envelope 可以展示 LLM gate metadata；
11. combined Markdown report 可以展示 LLM gate result；
12. deterministic quality gate / exit code 兼容；
13. invalid severity 行为被测试覆盖；
14. docs / CI 文档明确说明 explicit opt-in；
15. 全量测试通过。

---

## 10. 风险与注意事项

### 10.1 不要改变默认 CI 行为

这是本任务最大的风险。

默认行为必须继续是：

```text id="w14eee"
LLM findings do not affect exit code unless --llm-fail-on is explicitly provided.
```

### 10.2 不要让 `--llm-fail-on` 自动启用 LLM

`--llm-fail-on` 是 gate policy，不是 LLM execution switch。

如果用户没有启用 LLM review，应报清晰错误，而不是静默启用 provider。

### 10.3 不要混淆 deterministic gate 和 LLM gate

`--fail-on` 和 `--llm-fail-on` 必须保持两个独立概念。

### 10.4 不要修改 provider contract

provider 只返回 LLMReviewResult，不负责判断 CI 是否失败。

### 10.5 不要过早承诺合规保证

LLM quality gate 只是辅助 gate，不代表法律、医学、金融或平台合规保证。

文档中应避免写成“开启后保证内容合规”。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash id="m0iwkk"
uv run pytest tests/test_llm_quality_gate.py
uv run pytest tests/test_llm_single_file_quality_gate_cli.py
uv run pytest tests/test_llm_batch_quality_gate_cli.py
uv run pytest tests/test_llm_single_file_combined_cli_output.py
uv run pytest tests/test_llm_batch_combined_cli_output.py
uv run pytest tests/test_llm_combined_markdown_report.py
uv run pytest tests/test_llm_combined_output_docs.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest tests/test_ci_docs.py
uv run pytest tests/test_cli.py
uv run pytest
```

如果某些测试文件不存在，应根据本任务实际新增或更新后的文件名运行对应测试，并在最终输出中说明。

---

