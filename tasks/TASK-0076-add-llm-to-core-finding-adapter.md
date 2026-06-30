# TASK-0076: Add LLM-to-Core Finding Adapter

## 1. 背景

当前项目已经完成了确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计的 sidecar 输出、Markdown report、review index、manual review checklist 和 artifact examples。

TASK-0075 已经补充了 `examples/llm_review_artifacts/`，用于说明 deterministic report、LLM result、LLM report、review index、manual review checklist、batch partial failure 等 artifact 之间的关系。

下一阶段目标是逐步把 LLM 审计结果合并进主程序审计链路。

但在正式修改主 `ReviewResult`、主 Markdown report、batch result、quality gate 和 CLI 默认行为之前，必须先增加一个稳定的数据适配层。

本任务是 LLM 合并主程序的第一步：

> 增加一个 LLM-to-core finding adapter，将 LLM findings 规范化为“可被主审计链路理解的 finding candidate”，但暂时不改变主程序运行时行为。

本任务必须遵守项目当前的分层原则：LLM 相关能力应保持在 `llm` 层内，不能直接污染 core review engine、CLI、report renderer 或 quality gate。项目规则要求保持“小步任务、严格边界、结构化数据、测试优先、文档同步”。

---

## 2. 任务目标

本任务目标是新增一个 LLM finding 适配层，用于把现有 `LLMReviewResult` 中的 LLM findings 转换成统一、稳定、可测试的内部 finding candidate。

该 finding candidate 后续会被 TASK-0077 / TASK-0078 / TASK-0079 用于：

1. 单文件主结果合并；
2. 主 Markdown report 合并；
3. batch 主结果合并；
4. 后续 CLI 体验收口。

但本任务本身只做适配层，不做最终合并。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增 LLM finding adapter 模块，例如：

   ```text
   src/content_review_engine/llm/finding_adapter.py
   ```

2. 新增轻量内部数据结构，例如：

   ```text
   LLMCoreFindingCandidate
   LLMFindingAdapterConfig
   ```

   具体命名可根据现有代码风格调整。

3. 新增转换函数，例如：

   ```python
   adapt_llm_review_result_to_core_finding_candidates(...)
   adapt_llm_finding_to_core_finding_candidate(...)
   build_llm_core_rule_id(...)
   normalize_llm_finding_severity(...)
   ```

4. 将 LLM finding 的字段规范化为主程序更容易理解的结构，例如：

   ```text
   source
   advisory
   rule_id
   severity
   message
   suggestion
   line
   column
   matched_text
   context
   category / risk_type
   original_llm_rule_id
   original_index
   ```

5. 保证所有 LLM adapter 输出都明确标记为：

   ```text
   source = "llm"
   advisory = true
   ```

6. 保证 LLM rule id 不会与 deterministic rule id 冲突。

   推荐使用前缀：

   ```text
   llm.
   ```

   例如：

   ```text
   llm.semantic_review
   llm.exaggerated_claim
   llm.misleading_statement
   llm.unsafe_medical_claim
   ```

7. 新增单元测试，覆盖：

   * 单条 LLM finding 转换；
   * 多条 LLM findings 转换；
   * 空 LLMReviewResult；
   * severity 映射；
   * rule_id 前缀；
   * line / column 保留；
   * suggestion / context / matched_text 保留；
   * advisory 标记；
   * 不影响 quality gate；
   * 不修改原始 LLMReviewResult；
   * 不引入真实 LLM 调用。

8. 更新相关文档，说明 adapter 是后续主结果合并的准备层，而不是 runtime behavior change。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许修改主 `ReviewResult` schema。

2. 不允许把 LLM findings 写入主 `ReviewResult.findings`。

3. 不允许修改 deterministic review runner。

4. 不允许修改 deterministic rule engine 行为。

5. 不允许修改 `content-review review` 或 `content-review batch` 的默认输出行为。

6. 不允许新增 CLI 参数。

7. 不允许修改现有 CLI 参数语义。

8. 不允许修改 Markdown report renderer 的主输出逻辑。

9. 不允许把 LLM findings 合并进主 Markdown report。

10. 不允许修改 batch result schema。

11. 不允许让 LLM findings 参与 `severity_counts`、`rule_counts`、`quality gate` 或 `exit code`。

12. 不允许修改 quality gate 策略。

13. 不允许接入真实 LLM API。

14. 不允许新增 OpenAI / Anthropic / PydanticAI provider 行为。

15. 不允许新增 API、MCP、GUI、Supabase、前端或商业化相关能力。

16. 不允许让 examples 目录成为 runtime dependency。

17. 不允许把 manual review checklist 持久化进主 schema。

---

## 5. 需要修改的文件

预计新增：

```text
src/content_review_engine/llm/finding_adapter.py
tests/test_llm_finding_adapter.py
```

预计修改：

```text
src/content_review_engine/llm/__init__.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果现有项目中已有更合适的模块命名，可以根据现有结构调整，但必须保持 LLM adapter 位于 `src/content_review_engine/llm/` 分层内。

---

## 6. 实现要求

### 6.1 新增 adapter 数据结构

新增一个轻量内部数据结构，用于表达 LLM finding 转换后的“主程序候选 finding”。

建议字段如下：

```python
@dataclass(frozen=True)
class LLMCoreFindingCandidate:
    source: str
    advisory: bool
    rule_id: str
    severity: str
    message: str
    suggestion: str | None = None
    line: int | None = None
    column: int | None = None
    matched_text: str | None = None
    context: str | None = None
    category: str | None = None
    original_llm_rule_id: str | None = None
    original_index: int | None = None
```

如果项目现有模型使用 Pydantic 或 dataclass，应遵守现有风格。

要求：

1. `source` 固定为：

   ```text
   llm
   ```

2. `advisory` 固定为：

   ```python
   True
   ```

3. `rule_id` 必须带有 `llm.` 前缀。

4. `severity` 必须归一化为项目已有 canonical severity：

   ```text
   info
   warning
   error
   critical
   ```

5. 不允许在 adapter 中引入新的 severity 等级。

---

### 6.2 severity 映射规则

实现一个明确的 severity normalization helper。

建议规则：

```text
critical -> critical
error    -> error
warning  -> warning
info     -> info
```

对于未知、空值或大小写不一致的输入：

```text
"High"      -> warning 或 error，按现有项目语义选择
"medium"    -> warning
"low"       -> info
None        -> warning
""          -> warning
unknown     -> warning
```

要求：

1. 映射规则必须有测试覆盖。
2. 映射逻辑必须集中在一个 helper 中。
3. 不允许在多个地方散落 severity 映射逻辑。
4. 文档中要说明：LLM severity 虽然被归一化，但本任务不会让它参与 quality gate。

---

### 6.3 rule_id 生成规则

实现一个 `build_llm_core_rule_id(...)` helper。

推荐逻辑：

1. 如果 LLM finding 中已有 `rule_id` / `category` / `risk_type` 之类字段，则 slug 化后加前缀：

   ```text
   llm.<slug>
   ```

2. 如果没有可用分类，则使用：

   ```text
   llm.semantic_review
   ```

3. 必须避免以下情况：

   ```text
   forbidden_terms
   title_length
   required_section
   ```

   这类 deterministic rule id 不能被 LLM adapter 直接复用。

4. 如果输入已经带 `llm.` 前缀，不要重复生成：

   ```text
   llm.llm.xxx
   ```

5. rule id slug 化建议：

   ```text
   "Unsafe Medical Claim" -> "llm.unsafe_medical_claim"
   "misleading-claim"     -> "llm.misleading_claim"
   "LLM: Marketing Tone"  -> "llm.marketing_tone"
   ```

---

### 6.4 finding 字段映射规则

适配函数应尽可能保留 LLM finding 的原始语义。

建议映射：

```text
LLM message / issue / reason
  -> candidate.message

LLM suggestion / recommended_fix / rewrite_suggestion
  -> candidate.suggestion

LLM line
  -> candidate.line

LLM column
  -> candidate.column

LLM matched_text / evidence / quote
  -> candidate.matched_text

LLM context / rationale
  -> candidate.context

LLM category / risk_type
  -> candidate.category

LLM rule_id
  -> candidate.original_llm_rule_id
```

具体字段名以现有 `LLMReviewResult` / LLM finding 模型为准。

要求：

1. 不要为了适配而修改现有 `LLMReviewResult`。
2. 不要破坏现有 LLM sidecar JSON 输出。
3. 如果某些字段不存在，应安全降级为 `None`。
4. 如果 LLM result 没有 findings，应返回空 list。
5. adapter 不应该抛出不必要异常；只有输入类型明显错误时才可以抛出明确异常。

---

### 6.5 adapter 函数要求

建议提供以下函数：

```python
def adapt_llm_review_result_to_core_finding_candidates(
    result: LLMReviewResult,
) -> list[LLMCoreFindingCandidate]:
    ...
```

以及单条 finding 转换函数：

```python
def adapt_llm_finding_to_core_finding_candidate(
    finding: LLMReviewFinding,
    *,
    original_index: int | None = None,
) -> LLMCoreFindingCandidate:
    ...
```

如果现有代码中没有单独的 `LLMReviewFinding` 类型，应根据实际 LLM finding 模型调整命名。

要求：

1. 输入一个 `LLMReviewResult`。
2. 输出 `list[LLMCoreFindingCandidate]`。
3. 输出顺序必须与原始 LLM findings 顺序一致。
4. 每个 candidate 应保留 `original_index`。
5. 函数必须是纯函数，不读文件、不写文件、不调用 provider、不调用 CLI、不依赖环境变量。
6. 不允许读取 `examples/llm_review_artifacts/` 作为运行时数据。

---

### 6.6 导出要求

在 `src/content_review_engine/llm/__init__.py` 中导出新增类型和函数。

建议导出：

```python
LLMCoreFindingCandidate
adapt_llm_review_result_to_core_finding_candidates
adapt_llm_finding_to_core_finding_candidate
build_llm_core_rule_id
normalize_llm_finding_severity
```

具体名称以最终实现为准。

---

## 7. 测试要求

新增：

```text
tests/test_llm_finding_adapter.py
```

测试至少覆盖以下场景：

### 7.1 单条 finding 转换

验证：

1. `source == "llm"`；
2. `advisory is True`；
3. `rule_id` 带 `llm.` 前缀；
4. `severity` 被归一化；
5. `message` 被保留；
6. `suggestion` 被保留；
7. `line` / `column` 被保留；
8. `matched_text` / `context` 被保留。

---

### 7.2 多条 findings 转换

验证：

1. 输出数量正确；
2. 输出顺序与输入顺序一致；
3. `original_index` 正确；
4. 每条 finding 都是 advisory；
5. 每条 rule_id 都带 `llm.` 前缀。

---

### 7.3 空 result

验证：

```python
adapt_llm_review_result_to_core_finding_candidates(empty_result) == []
```

---

### 7.4 severity normalization

覆盖：

```text
critical
error
warning
info
High / high
Medium / medium
Low / low
unknown
None
""
```

---

### 7.5 rule_id normalization

覆盖：

```text
"Unsafe Medical Claim" -> "llm.unsafe_medical_claim"
"misleading-claim" -> "llm.misleading_claim"
"llm.marketing_tone" -> "llm.marketing_tone"
None -> "llm.semantic_review"
"" -> "llm.semantic_review"
```

---

### 7.6 不影响主程序行为

增加测试或断言，确保本任务没有改变：

1. deterministic review result；
2. existing LLM result serialization；
3. quality gate 行为；
4. CLI 默认行为。

如果不适合直接测试 CLI，也至少要确保新增 adapter 测试不依赖 CLI。

---

### 7.7 不调用真实 LLM

测试不得依赖：

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
真实网络
真实 PydanticAI provider
真实模型响应
```

---

## 8. 文档更新要求

需要更新以下文档：

```text
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
PROJECT_STATE.md
CHANGELOG.md
```

### 8.1 docs/ARCHITECTURE.md

说明新增 adapter 层的位置：

```text
LLMReviewResult
  ↓
LLM finding adapter
  ↓
LLMCoreFindingCandidate
  ↓
future combined ReviewResult integration
```

并明确：

1. adapter 是纯转换层；
2. adapter 不调用 provider；
3. adapter 不改变 CLI；
4. adapter 不改变 quality gate；
5. adapter 不让 LLM findings 进入主 result。

---

### 8.2 docs/DATA_MODELS.md

说明新增 `LLMCoreFindingCandidate`。

必须明确：

1. 它是 internal candidate，不是主 `ReviewResult` schema；
2. 它用于后续合并；
3. `source="llm"`；
4. `advisory=True`；
5. `rule_id` 使用 `llm.` 前缀；
6. 当前不会参与 `severity_counts`、`rule_counts` 或 quality gate。

---

### 8.3 docs/LLM_PROVIDER_USAGE.md

说明：

1. provider 返回的仍然是 `LLMReviewResult`；
2. adapter 可将 `LLMReviewResult` 规范化为 candidate；
3. adapter 不改变 provider contract；
4. adapter 不改变 sidecar JSON；
5. adapter 不改变真实 provider / mock provider 行为。

---

### 8.4 PROJECT_STATE.md

记录 TASK-0076 完成后，项目状态从：

```text
LLM artifact examples / manual review workflow documented
```

推进到：

```text
LLM-to-core finding adapter added as preparation for combined review result integration
```

但必须说明：

```text
LLM findings are not yet merged into main ReviewResult or quality gate.
```

---

### 8.5 CHANGELOG.md

新增 TASK-0076 记录，说明：

1. 新增 LLM finding adapter；
2. 新增 candidate 数据结构；
3. 新增 severity / rule_id normalization；
4. 新增测试；
5. 未改变 runtime CLI / report / quality gate 行为。

---

## 9. 验收标准

本任务完成后应满足：

1. 新增 LLM finding adapter 模块；
2. 新增 LLM core finding candidate 数据结构；
3. LLM findings 可以被转换为稳定 candidate list；
4. 所有 candidate 都有 `source="llm"`；
5. 所有 candidate 都有 `advisory=True`；
6. 所有 candidate 的 `rule_id` 都以 `llm.` 开头；
7. severity 被归一化到 canonical severity；
8. 空 LLM result 返回空 list；
9. 转换函数不读写文件、不调用 provider、不依赖环境变量；
10. 不修改主 `ReviewResult` schema；
11. 不修改 CLI 行为；
12. 不修改 report renderer 行为；
13. 不修改 quality gate 行为；
14. 不引入真实 LLM 调用；
15. 新增测试通过；
16. 全量测试通过；
17. 文档同步更新。

---

## 10. 风险与注意事项

### 10.1 不要提前合并主结果

本任务只是 adapter，不是 combined result。

不要把 LLM findings 加入：

```text
ReviewResult.findings
BatchReviewResult
Markdown report 主 Findings
severity_counts
rule_counts
quality gate
exit code
```

这些应该留给后续任务。

---

### 10.2 不要把 advisory finding 当 deterministic finding

LLM finding 是语义建议，不等同于 deterministic rule violation。

因此 candidate 必须明确包含：

```text
source = "llm"
advisory = true
```

---

### 10.3 不要破坏 sidecar 输出

现有 LLM sidecar JSON、LLM Markdown report、review index、artifact examples 都不应该因为本任务发生行为变化。

---

### 10.4 不要读取 examples 作为 runtime 依赖

`examples/llm_review_artifacts/` 是 reference-only。

Adapter 不能从 examples 中读取模板、schema 或默认值。

---

### 10.5 注意 rule_id 冲突

LLM adapter 输出的 rule id 必须带 `llm.` 前缀，避免与 deterministic rules 混淆。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_finding_adapter.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest
```

如果修改了其它相关测试，也请运行对应测试文件。

---

