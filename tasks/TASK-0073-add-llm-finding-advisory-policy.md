# TASK-0073: Add LLM Finding Advisory Policy

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
11. Hybrid Review Report Index。

在 TASK-0072 完成后，项目已经可以清楚地区分这些输出：

```text
--output        deterministic 主输出
--llm-output    LLM JSON sidecar
--llm-report    LLM Markdown report
--report-index  输出导航与解释型 Markdown index
```

目前项目仍然保持正确边界：

1. deterministic review 是稳定、可复现、可用于 quality gate 的主审计结果；
2. LLM review 是语义审计建议；
3. LLM findings 不进入 `ReviewResult`；
4. LLM findings 不进入 `BatchReviewResult`；
5. LLM findings 不参与 fail-on / quality gate；
6. LLM Markdown report 和 report index 只是展示层。

但是，随着 LLM 输出逐渐进入用户可见层，项目需要进一步明确：

1. LLM finding 的来源如何标识；
2. LLM finding 的 severity 是否等同于 deterministic severity；
3. LLM finding 是否应被视为 advisory；
4. LLM finding 是否会影响 quality gate；
5. LLM finding 的 rule_id 如何展示；
6. LLM finding 的 confidence / confidence-like 信息如何处理；
7. report 中如何避免用户误解“LLM error/warning”等同于硬规则失败。

因此，本任务需要新增一个 **LLM Finding Advisory Policy**。

本任务不是把 LLM findings 合并进主审计结果，也不是让 LLM 参与质量门禁，而是新增一个内部 policy 层，用来规范 LLM finding 的展示语义和未来集成边界。

---

## 2. 任务目标

新增一个 LLM finding advisory policy 模块，用于把 LLM findings 解释为：

```text
source = llm
advisory = true
quality_gate_participation = false
```

并在 LLM Markdown report 与 report index 中明确展示：

1. LLM findings 来自 LLM semantic review；
2. LLM findings 是 advisory semantic suggestions；
3. LLM findings 不参与 deterministic finding counts；
4. LLM findings 不参与 fail-on / quality gate；
5. LLM severity 是 LLM advisory severity，不等同于 deterministic hard-rule severity；
6. LLM rule_id 是 LLM 层规则或模型输出规则，不等同于 deterministic rule engine rule_id。

本任务完成后，用户阅读 LLM report 或 report index 时，应能明确知道：

> LLM findings 是语义审计建议，不是确定性规则失败；它们可以辅助人工判断，但不会改变 deterministic review 的 pass/fail 结果。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增 LLM finding advisory policy 模块；
2. 新增用于描述 LLM finding 展示语义的轻量内部类型；
3. 对 LLM finding 的 source、advisory status、quality gate participation 做统一定义；
4. 对 LLM finding severity 做展示层 normalization；
5. 对 LLM finding rule_id 做展示层 normalization；
6. 对可用的 confidence / confidence-like 字段做展示层处理；
7. 在 LLM Markdown report 中增加 advisory policy 说明；
8. 在 LLM Markdown report 的 finding 展示中标注 source / advisory / quality gate participation；
9. 在 report index 中增加 LLM advisory boundary 说明；
10. 在 batch partial failure 场景中保持现有行为，只补充 advisory policy 说明；
11. 新增 policy 单元测试；
12. 更新 LLM Markdown report renderer 测试；
13. 更新 report index renderer 测试；
14. 更新 CLI 集成测试中与 report 文本相关的断言；
15. 更新 CLI、LLM provider usage、data models、architecture、CI、project state 和 changelog 文档。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许修改 `ReviewResult` schema；
2. 不允许修改 `BatchReviewResult` schema；
3. 不允许把 LLM findings 合并进 deterministic findings；
4. 不允许让 LLM findings 参与 quality gate；
5. 不允许改变 fail-on 判断；
6. 不允许改变 deterministic severity counts；
7. 不允许改变 deterministic rule counts；
8. 不允许改变 deterministic Markdown report 的核心结构；
9. 不允许改变 deterministic JSON 输出；
10. 不允许改变 batch stdout；
11. 不允许改变 LLM JSON sidecar schema，除非现有模型已经有可选字段且本任务只是展示；
12. 不允许新增真实 provider；
13. 不允许新增真实 LLM API 调用；
14. 不允许在测试中调用真实 LLM API；
15. 不允许新增 API / MCP / GUI；
16. 不允许新增 Supabase、用户系统、审计历史或商业化能力；
17. 不允许把 `--report-index` 做成 full combined report；
18. 不允许把 LLM advisory severity 映射为 deterministic hard-rule severity；
19. 不允许让 `critical` / `error` 级别的 LLM finding 自动导致 CLI 失败；
20. 不允许引入当前时间戳、随机 ID 或环境相关的非稳定输出。

---

## 5. 需要修改的文件

预计新增：

```text
src/content_review_engine/llm/policy.py
tests/test_llm_finding_policy.py
```

预计修改：

```text
src/content_review_engine/llm/__init__.py
src/content_review_engine/reports/llm_markdown.py
src/content_review_engine/reports/report_index.py
tests/test_llm_markdown_report.py
tests/test_report_index.py
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

如当前仓库的实际文件命名不同，请保持项目已有风格，但必须覆盖同等功能与测试范围。

---

## 6. 实现要求

### 6.1 新增 LLM policy 模块

新增：

```text
src/content_review_engine/llm/policy.py
```

该模块只负责定义 LLM finding 的 advisory policy，不负责：

1. 调用 LLM；
2. 解析 CLI；
3. 写文件；
4. 生成 JSON；
5. 执行 deterministic review；
6. 执行 quality gate；
7. 修改 review result 对象。

建议提供类似以下常量或函数，具体命名应与项目现有风格保持一致：

```python
LLM_FINDING_SOURCE = "llm"
LLM_FINDING_ADVISORY = True
LLM_FINDING_PARTICIPATES_IN_QUALITY_GATE = False

def normalize_llm_finding_severity(value: object) -> str:
    ...

def normalize_llm_finding_rule_id(value: object) -> str:
    ...

def render_llm_finding_policy_note() -> str:
    ...

def build_llm_finding_display_metadata(finding: object) -> LLMFindingDisplayMetadata:
    ...
```

可以使用 dataclass、TypedDict 或项目现有模型风格定义轻量内部类型，例如：

```python
@dataclass(frozen=True)
class LLMFindingDisplayMetadata:
    source: str
    advisory: bool
    participates_in_quality_gate: bool
    severity: str
    rule_id: str
    confidence: str | None
```

注意：

1. 这是展示层 metadata；
2. 不应作为新的 canonical persisted schema；
3. 不应写入 deterministic `ReviewResult`；
4. 不应改变 LLM JSON sidecar schema；
5. 不应要求 LLM provider 必须返回 confidence 字段。

### 6.2 Severity normalization

LLM finding severity 应保持 advisory 语义。

如果现有 LLM finding 已有 severity 字段，则渲染时应使用该字段，但需要做稳定 normalization：

```text
critical
error
warning
info
unknown
```

要求：

1. canonical ordering 仍为 `critical`, `error`, `warning`, `info`, `unknown`；
2. 未知 severity 显示为 `unknown`；
3. 空 severity 显示为 `unknown`；
4. 大小写应稳定处理，例如 `Warning` -> `warning`；
5. 不要因为 LLM severity 是 `critical` 或 `error` 就影响 CLI exit code；
6. 文档中要明确 LLM severity 是 advisory severity。

### 6.3 Rule ID normalization

LLM finding rule_id 应作为 LLM 层展示字段，不等同于 deterministic rule engine rule_id。

要求：

1. 如果 LLM finding 有 rule_id，则稳定展示；
2. 如果缺失或为空，则展示为 `llm.semantic_review`；
3. 如果 rule_id 包含空白或换行，应做稳定处理；
4. 不要把 LLM rule_id 加入 deterministic rule counts；
5. 文档中要明确 LLM rule_id 属于 LLM semantic review layer。

### 6.4 Confidence handling

如果现有 LLM finding 模型中已经有 confidence、score 或类似字段，可以在展示层显示。

如果没有，不要修改模型强行添加。

要求：

1. 如果存在 confidence-like 字段，展示为稳定字符串；
2. 如果不存在，展示为 `not provided`；
3. 不要要求 provider 必须返回 confidence；
4. 不要用 confidence 改变 severity；
5. 不要用 confidence 改变 quality gate；
6. 不要在本任务中新增 confidence-based filtering。

### 6.5 LLM Markdown report 更新

更新：

```text
src/content_review_engine/reports/llm_markdown.py
```

在单文件 LLM report 中增加一个稳定 section，例如：

```markdown
## Advisory Policy

- Source: LLM semantic review
- Advisory: yes
- Quality Gate Participation: no
- LLM findings do not modify deterministic finding counts.
- LLM findings do not participate in fail-on / quality gate decisions.
- LLM severity is advisory and should be reviewed by a human.
```

在 batch LLM report 中也增加同样的 `## Advisory Policy` section。

在 findings 表格中，允许增加以下列：

```text
Source
Advisory
Quality Gate
```

例如：

```markdown
| Source | Advisory | Quality Gate | Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| llm | yes | no | warning | llm.semantic_review | 12 | 4 | ... | ... |
```

如果现有 LLM Markdown report 表格结构不方便新增列，也可以在 Detailed Findings 中增加：

```markdown
- Source: llm
- Advisory: yes
- Quality Gate Participation: no
```

但必须保证用户可以清楚看到每条 LLM finding 的 advisory 语义。

### 6.6 Report index 更新

更新：

```text
src/content_review_engine/reports/report_index.py
```

在 report index 中增加 LLM boundary 说明，例如：

```markdown
## LLM Advisory Boundary

- LLM findings are advisory semantic review results.
- LLM findings are not deterministic rule findings.
- LLM findings do not modify deterministic review counts.
- LLM findings do not participate in quality gate decisions.
- Use deterministic output for CI and fail-on decisions.
- Use LLM reports for human semantic review.
```

要求：

1. LLM 未启用时，可以显示 `LLM Review | not enabled`，但不需要强行输出完整 LLM advisory boundary；
2. LLM 启用时，必须输出 LLM advisory boundary；
3. batch partial failure 时，仍然输出 advisory boundary；
4. 不复制所有 detailed findings 到 index；
5. 不让 index 成为 full combined report。

### 6.7 CLI 行为

本任务不新增 CLI 参数。

现有 CLI 行为必须保持：

1. `--output` 仍负责 deterministic 主输出；
2. `--llm-output` 仍负责 LLM JSON sidecar；
3. `--llm-report` 仍负责 LLM Markdown report；
4. `--report-index` 仍负责导航 / 解释型 index；
5. `--report-index` 不隐式开启 LLM；
6. `--enable-llm` 仍必须配合 `--llm-output` 或 `--llm-report`；
7. LLM finding severity 不影响 exit code；
8. LLM finding rule_id 不影响 deterministic rule counts；
9. LLM findings 不参与 quality gate；
10. batch partial failure exit code 保持已有行为。

### 6.8 输出稳定性

所有新增输出必须稳定。

禁止包含：

1. 当前时间戳；
2. 随机 ID；
3. 绝对路径，除非当前项目已有测试和文档约定使用绝对路径；
4. API key；
5. 环境变量值；
6. 当前机器用户名；
7. provider secret；
8. 非确定性排序。

Markdown 表格中必须继续处理：

1. `|`；
2. 换行；
3. 空值；
4. `None`；
5. 长文本的稳定展示。

---

## 7. 测试要求

### 7.1 新增 policy 单元测试

新增：

```text
tests/test_llm_finding_policy.py
```

至少覆盖：

1. default source is `llm`；
2. advisory is always true；
3. quality gate participation is always false；
4. known severity normalization；
5. unknown severity normalization；
6. empty severity normalization；
7. mixed-case severity normalization；
8. missing rule_id fallback to `llm.semantic_review`；
9. blank rule_id fallback；
10. rule_id whitespace / newline normalization；
11. confidence not provided；
12. confidence-like field display if supported by existing model；
13. policy note text contains advisory boundary；
14. policy helper does not mutate input finding。

### 7.2 更新 LLM Markdown report 测试

更新：

```text
tests/test_llm_markdown_report.py
```

至少覆盖：

1. single-file report includes `## Advisory Policy`；
2. batch report includes `## Advisory Policy`；
3. findings include source `llm`；
4. findings include advisory `yes`；
5. findings include quality gate `no`；
6. missing rule_id uses `llm.semantic_review`；
7. unknown severity displays `unknown`；
8. no findings report still includes advisory policy when LLM review ran；
9. batch partial failure report still includes advisory policy；
10. Markdown escaping remains stable；
11. existing no-findings behavior remains stable；
12. output does not include timestamp or nondeterministic values。

### 7.3 更新 report index 测试

更新：

```text
tests/test_report_index.py
```

至少覆盖：

1. hybrid single-file index includes LLM advisory boundary；
2. hybrid batch index includes LLM advisory boundary；
3. deterministic-only index does not incorrectly claim LLM findings exist；
4. LLM-enabled index says quality gate source is deterministic review only；
5. batch partial failure index still includes advisory boundary；
6. index does not copy detailed findings；
7. index output remains stable；
8. Markdown escaping remains stable。

### 7.4 更新 CLI 集成测试

更新相关 CLI integration tests，至少覆盖：

1. `--llm-report` output contains advisory policy；
2. `--report-index` output contains LLM advisory boundary when LLM enabled；
3. deterministic-only `--report-index` remains valid；
4. LLM severity `critical` does not cause deterministic quality gate failure；
5. LLM findings do not change deterministic findings count；
6. LLM findings do not change deterministic rule counts；
7. batch partial failure behavior remains unchanged；
8. tests do not require real network；
9. tests do not require real API key。

### 7.5 更新文档断言测试

如果项目已有文档断言测试，例如：

```text
tests/test_llm_provider_usage_docs.py
```

需要同步更新，确保文档中包含：

1. LLM findings are advisory；
2. LLM findings do not participate in quality gate；
3. LLM severity is advisory severity；
4. LLM rule_id belongs to LLM semantic review layer；
5. deterministic review remains the quality gate source；
6. JSON sidecar remains canonical machine-readable LLM output；
7. Markdown report and report index are presentation outputs。

---

## 8. 文档更新要求

### 8.1 docs/CLI.md

需要补充：

1. LLM findings 的 advisory-only 语义；
2. `--llm-report` 中 advisory policy 的含义；
3. `--report-index` 中 LLM advisory boundary 的含义；
4. LLM severity 不影响 CLI exit code；
5. LLM findings 不参与 fail-on / quality gate；
6. LLM rule_id 不进入 deterministic rule counts；
7. batch partial failure 行为不变。

### 8.2 docs/LLM_PROVIDER_USAGE.md

需要补充：

1. LLM finding advisory policy；
2. LLM severity policy；
3. LLM rule_id policy；
4. confidence / confidence-like 字段处理原则；
5. 为什么 LLM findings 现阶段不参与 quality gate；
6. 人工审阅 LLM findings 的推荐方式；
7. 测试仍然不需要真实 API key；
8. 手动验证仍建议使用小样本 Markdown。

### 8.3 docs/DATA_MODELS.md

需要补充：

1. LLM advisory policy 是展示层 / interpretation layer；
2. 本任务不新增 canonical persisted schema；
3. 本任务不修改 `ReviewResult`；
4. 本任务不修改 `BatchReviewResult`；
5. 本任务不修改 LLM JSON sidecar schema；
6. LLM display metadata 不应被下游当作稳定 API schema；
7. machine-readable LLM 输出仍以 LLM JSON sidecar 为准。

### 8.4 docs/ARCHITECTURE.md

需要补充：

1. `llm/policy.py` 所在层级；
2. policy 位于 LLM result 与 presentation renderer 之间；
3. policy 不负责 provider；
4. policy 不负责 runner；
5. policy 不负责 CLI；
6. policy 不负责 quality gate；
7. policy 不修改 result object；
8. policy 只规范 LLM finding 的展示解释边界。

### 8.5 docs/CI.md

需要补充：

1. LLM findings 不参与 CI quality gate；
2. LLM advisory severity 不改变 CI pass/fail；
3. deterministic fail-on 仍是 CI gate 来源；
4. LLM report 和 report index 可以作为 CI artifact；
5. LLM critical / error 只表示 advisory review severity；
6. batch LLM partial failure exit code 仍遵循已有 CLI 语义。

### 8.6 PROJECT_STATE.md

记录 TASK-0073 完成后项目状态：

1. 已新增 LLM finding advisory policy；
2. LLM report 中已明确 advisory boundary；
3. report index 中已明确 LLM advisory boundary；
4. LLM findings 仍未合并进主 ReviewResult；
5. LLM findings 仍不参与 quality gate；
6. API / MCP / GUI 仍未开始。

### 8.7 CHANGELOG.md

新增 TASK-0073 条目，说明：

1. 新增 LLM finding advisory policy；
2. 新增 LLM finding source / advisory / quality gate participation 展示语义；
3. 更新 LLM Markdown report；
4. 更新 hybrid report index；
5. 不改变 canonical schema；
6. 不改变 quality gate。

---

## 9. 验收标准

本任务完成后，应满足以下标准：

1. 新增 `src/content_review_engine/llm/policy.py`；
2. 新增 `tests/test_llm_finding_policy.py`；
3. LLM finding 的 source 稳定显示为 `llm`；
4. LLM finding 的 advisory status 稳定显示为 `yes`；
5. LLM finding 的 quality gate participation 稳定显示为 `no`；
6. LLM severity 缺失或未知时稳定显示为 `unknown`；
7. LLM rule_id 缺失时稳定显示为 `llm.semantic_review`；
8. 单文件 LLM Markdown report 包含 advisory policy；
9. batch LLM Markdown report 包含 advisory policy；
10. LLM Markdown report 中每条 finding 可见 advisory 语义；
11. hybrid report index 中包含 LLM advisory boundary；
12. deterministic-only report index 不错误宣称 LLM 已启用；
13. LLM severity 不影响 exit code；
14. LLM findings 不改变 deterministic finding counts；
15. LLM findings 不改变 deterministic rule counts；
16. LLM findings 不参与 quality gate；
17. 不修改 `ReviewResult` schema；
18. 不修改 `BatchReviewResult` schema；
19. 不修改 LLM JSON sidecar schema；
20. 不新增真实 provider；
21. 不新增 API / MCP / GUI；
22. 所有新增测试通过；
23. `uv run pytest` 全量通过；
24. 文档已同步更新。

---

## 10. 风险与注意事项

1. 不要把 advisory policy 做成 quality gate policy；
2. 不要让 LLM severity 影响 fail-on；
3. 不要把 LLM rule_id 加入 deterministic rule counts；
4. 不要修改 deterministic report 的含义；
5. 不要修改 deterministic JSON 的含义；
6. 不要修改 LLM JSON sidecar schema；
7. 不要强制 provider 返回 confidence；
8. 不要新增 confidence filtering；
9. 不要在 policy 中调用 provider；
10. 不要在 policy 中解析 CLI；
11. 不要在 policy 中写文件；
12. 不要在 tests 中调用真实 LLM；
13. 不要把 report index 扩展成 full combined report；
14. 不要复制 detailed findings 到 index；
15. 不要输出 secret、API key 或环境变量值；
16. 不要加入时间戳或随机值。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_finding_policy.py
uv run pytest tests/test_llm_markdown_report.py
uv run pytest tests/test_report_index.py
uv run pytest tests/test_llm_single_file_cli_integration.py
uv run pytest tests/test_llm_batch_cli_integration.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest tests/test_cli.py
uv run pytest
```

如果某些测试文件在当前仓库中不存在，请根据实际文件名调整，但必须覆盖同等测试范围。

---
