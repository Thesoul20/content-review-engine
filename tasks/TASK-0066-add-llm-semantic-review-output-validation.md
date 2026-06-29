# TASK-0066: Add LLM Semantic Review Output Validation

## 1. 背景

当前项目已经完成：

```text
TASK-0061: Add LLM Provider Secret Resolver
TASK-0062: Wire LLM Secret Resolver into LLM Check
TASK-0063: Enable Real PydanticAI Provider Construction
TASK-0064: Add Optional Live PydanticAI Runtime Smoke Check
TASK-0065: Add LLM Semantic Review Prompt Contract
```

目前 LLM 层已经具备：

1. secret resolver；
2. `llm-check` secret preflight；
3. PydanticAI provider construction check；
4. optional live runtime smoke check；
5. 独立的 LLM semantic review prompt contract；
6. `llm-semantic-review-output.v1` JSON 输出约定；
7. severity 枚举约束；
8. `llm.` rule_id 前缀约束；
9. finding 字段约束；
10. prompt builder 与 provider execution 已保持分离。

上一任务只定义了“希望 LLM 返回什么 JSON”，但还没有实现“真实或模拟 LLM 输出返回后，如何解析、校验和处理错误”。

本任务的目标是新增 **LLM semantic review output validation layer**。

该层只负责：

```text
raw LLM output text
  ↓
JSON extraction / parsing
  ↓
schema_version validation
  ↓
field validation
  ↓
semantic finding validation
  ↓
validated semantic review output
```

本任务不调用真实 LLM，不接入 provider execution，不生成正式 `LLMReviewResult`，不接入 `review` / `batch` 主流程。

---

## 2. 任务目标

本任务需要完成：

1. 新增 LLM semantic review output parser；
2. 新增 LLM semantic review output validator；
3. 支持解析 prompt contract 中定义的 `llm-semantic-review-output.v1`；
4. 校验 `schema_version`；
5. 校验 `summary`；
6. 校验 `findings` 数组；
7. 校验 finding 字段：

   * `rule_id`
   * `severity`
   * `line`
   * `column`
   * `message`
   * `evidence`
   * `suggestion`
   * `confidence`
8. 校验 severity 只能是：

   * `info`
   * `warning`
   * `error`
   * `critical`
9. 校验 `rule_id` 必须以 `llm.` 开头；
10. 校验 `confidence` 必须在 `0` 到 `1` 之间；
11. 支持常见 LLM 输出恢复，例如去除 Markdown code fence；
12. 对无效 JSON、缺失字段、字段类型错误、非法枚举、非法 confidence 等返回稳定错误；
13. 错误信息不得泄露 secret；
14. 增加完整测试；
15. 更新文档、项目状态和 changelog。

完成后，项目应具备一个独立、可测试、可复用的 LLM 输出解析与校验层，为后续 provider execution wiring 和 `LLMReviewResult` 生成打基础。

---

## 3. 本任务允许做什么

本任务允许：

1. 新增 LLM output validation 模块；
2. 新增 parser helper；
3. 新增 validator helper；
4. 新增 validated output 数据结构；
5. 新增 validation error 类型；
6. 支持从纯 JSON 字符串解析；
7. 支持从 Markdown fenced JSON block 中提取 JSON；
8. 支持对字段进行严格校验；
9. 支持返回稳定的 validated semantic review output；
10. 增加 output validation 测试；
11. 更新 prompt contract 测试或文档测试；
12. 更新 LLM 数据模型文档；
13. 更新架构文档；
14. 更新 provider usage 文档；
15. 更新 `PROJECT_STATE.md`；
16. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许：

1. 不允许调用真实 LLM API；
2. 不允许访问外部网络；
3. 不允许调用 PydanticAI provider；
4. 不允许修改 `content-review review` 主流程；
5. 不允许修改 `content-review batch` 主流程；
6. 不允许新增 `review` 或 `batch` 的 LLM CLI 开关；
7. 不允许把 validated output 转换成正式 `LLMReviewResult`；
8. 不允许把 LLM finding 合并进 `ReviewResult`；
9. 不允许修改 `ReviewResult` schema；
10. 不允许修改 `BatchReviewResult` schema；
11. 不允许修改 `LLMReviewResult` schema，除非当前已有模型无法表达错误类型且必须小范围补充；
12. 不允许修改 sidecar metadata；
13. 不允许修改 deterministic review engine 行为；
14. 不允许修改 `llm-check` live / construction 行为；
15. 不允许新增 plaintext API key 参数；
16. 不允许读取 `.env`；
17. 不允许读取 `os.environ`；
18. 不允许让 provider factory 读取环境变量；
19. 不允许让 reserved providers 变成可创建；
20. 不允许新增 API、MCP、Skill、GUI、Supabase、用户系统或商业化能力；
21. 不允许引入 LangChain、CrewAI 或其他大型框架。

---

## 5. 需要修改的文件

预计会新增或修改以下文件：

```text
src/content_review_engine/llm/output_validation.py
src/content_review_engine/llm/models.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/__init__.py

tests/test_llm_output_validation.py
tests/test_llm_prompt_contract.py
tests/test_llm_provider_usage_docs.py

docs/LLM_PROVIDER_USAGE.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前仓库已有更合适的命名，应优先遵守现有结构。

---

## 6. 实现要求

### 6.1 新增 output validation 模块

建议新增：

```text
src/content_review_engine/llm/output_validation.py
```

该模块应提供稳定 public helper，例如：

```python
parse_llm_semantic_review_output(raw_output: str) -> ValidatedLLMSemanticReviewOutput
```

或者当前项目风格下的等价命名。

推荐拆分为：

```python
extract_llm_semantic_review_json(raw_output: str) -> str
parse_llm_semantic_review_output(raw_output: str) -> ValidatedLLMSemanticReviewOutput
validate_llm_semantic_review_output(data: object) -> ValidatedLLMSemanticReviewOutput
```

其中：

1. `extract_*` 负责从 raw text 中提取 JSON；
2. `parse_*` 负责 JSON parsing；
3. `validate_*` 负责字段与语义校验。

不要在这个模块中调用 provider。

---

### 6.2 validated output 数据结构要求

可以在 `llm/models.py` 中新增内部 validated output 模型，例如：

```python
ValidatedLLMSemanticFinding
ValidatedLLMSemanticReviewOutput
```

或当前项目风格下的等价命名。

推荐字段：

```python
schema_version: str
summary: str
findings: list[ValidatedLLMSemanticFinding]
```

finding 推荐字段：

```python
rule_id: str
severity: str
line: int | None
column: int | None
message: str
evidence: str
suggestion: str
confidence: float
```

注意：

1. 这是 prompt output validation model；
2. 不是正式 `LLMReviewResult`；
3. 不应改变 `LLMReviewResult` schema；
4. 不应改变 `ReviewResult` schema；
5. 不应改变 `BatchReviewResult` schema。

---

### 6.3 schema_version 校验要求

必须要求：

```text
llm-semantic-review-output.v1
```

如果缺失或不匹配，应抛出稳定 validation error。

错误信息应说明 expected / actual，但不得包含完整 raw output。

---

### 6.4 JSON parsing 要求

应支持以下输入：

纯 JSON：

```json
{
  "schema_version": "llm-semantic-review-output.v1",
  "summary": "No major issues.",
  "findings": []
}
```

Markdown fenced JSON：

````text
```json
{
  "schema_version": "llm-semantic-review-output.v1",
  "summary": "No major issues.",
  "findings": []
}
````

````

也可以支持无语言标签的 fenced block：

```text
````

{
"schema_version": "llm-semantic-review-output.v1",
"summary": "No major issues.",
"findings": []
}

```
```

不要求实现复杂、多段、模糊自然语言中的 JSON 自动修复。
如果输出不是可解析 JSON，应返回稳定错误。

---

### 6.5 findings 校验要求

`findings` 必须是数组。

没有问题时必须允许：

```json
"findings": []
```

每个 finding 必须校验：

#### rule_id

要求：

1. 必须是非空字符串；
2. 必须以 `llm.` 开头。

允许示例：

```text
llm.semantic.overclaim
llm.semantic.misleading
llm.semantic.unsupported_claim
llm.semantic.risky_advice
llm.semantic.ambiguous_expression
llm.semantic.inappropriate_tone
llm.semantic.needs_human_review
```

本任务可以只强制 `llm.` 前缀，不必限制在固定列表中，避免后续扩展受阻。

#### severity

只能是：

```text
info
warning
error
critical
```

其他值必须失败。

#### line

允许：

1. 正整数；
2. `null`。

不允许：

1. 负数；
2. 0；
3. 字符串；
4. 浮点数。

#### column

允许：

1. 正整数；
2. `null`。

不允许：

1. 负数；
2. 0；
3. 字符串；
4. 浮点数。

#### message

要求：

1. 必须是非空字符串；
2. 应去除首尾空白；
3. 为空时失败。

#### evidence

要求：

1. 必须是非空字符串；
2. 应引用原文短片段；
3. 本任务不需要验证 evidence 是否真实存在于原文中，后续任务可扩展。

#### suggestion

要求：

1. 必须是非空字符串；
2. 应给出可执行修改建议；
3. 为空时失败。

#### confidence

要求：

1. 必须是数字；
2. 必须在 `0` 到 `1` 之间；
3. `0` 和 `1` 都允许；
4. 字符串 `"0.8"` 不应自动接受，除非项目现有模型风格允许宽松转换。

推荐保持严格。

---

### 6.6 summary 校验要求

`summary` 必须是字符串。

允许空字符串还是不允许空字符串，可以根据项目风格决定。
推荐要求非空字符串。

如果 findings 为空，summary 可以类似：

```text
No semantic findings.
```

---

### 6.7 错误类型要求

建议在 `llm/errors.py` 中新增：

```python
LLMSemanticReviewOutputError
LLMSemanticReviewOutputParseError
LLMSemanticReviewOutputValidationError
```

或使用当前 error hierarchy 中已有合适类型。

要求：

1. parse error 和 validation error 可区分；
2. 错误消息稳定；
3. 错误消息不要包含完整 raw output；
4. 错误消息不要包含 secret；
5. 错误消息应包含字段路径或原因，例如：

   * `schema_version`
   * `findings[0].severity`
   * `findings[0].confidence`
6. 错误类型应从现有 LLM error base class 派生。

---

### 6.8 recovery 边界要求

本任务允许的 recovery 仅限：

1. trim whitespace；
2. 去除单个 Markdown code fence；
3. 识别 ```json fenced block；
4. 识别无语言标签 fenced block。

本任务不允许：

1. 自动修复残缺 JSON；
2. 自动补字段；
3. 自动改 severity；
4. 自动把字符串 confidence 转成 float；
5. 自动把非法 rule_id 改成合法 rule_id；
6. 自动推断 line / column；
7. 自动生成 suggestion。

输出不合规时应失败，而不是静默修复。

---

### 6.9 安全要求

parser / validator 不应：

1. 读取 `.env`；
2. 读取 `os.environ`；
3. 访问网络；
4. 调用 provider；
5. 调用 `llm-check`；
6. 修改全局状态；
7. 输出完整 raw output；
8. 输出 secret-like value。

如果 raw output 中包含疑似 secret，错误信息也不应原样包含该值。

---

## 7. 测试要求

### 7.1 新增 output validation 测试

新增：

```text
tests/test_llm_output_validation.py
```

覆盖：

1. 纯 JSON 输出可解析；
2. fenced JSON 输出可解析；
3. fenced block 无语言标签时可解析；
4. 前后空白可处理；
5. valid empty findings 可通过；
6. valid finding 可通过；
7. schema_version 缺失失败；
8. schema_version 错误失败；
9. summary 缺失失败；
10. findings 缺失失败；
11. findings 不是数组失败；
12. finding 缺少 rule_id 失败；
13. rule_id 不以 `llm.` 开头失败；
14. severity 非法失败；
15. line 为 0、负数、字符串、浮点数时失败；
16. column 为 0、负数、字符串、浮点数时失败；
17. message 为空失败；
18. evidence 为空失败；
19. suggestion 为空失败；
20. confidence 小于 0 失败；
21. confidence 大于 1 失败；
22. confidence 为字符串失败；
23. 非 JSON 输出失败；
24. 残缺 JSON 输出失败；
25. error message 包含字段路径；
26. error message 不包含完整 raw output；
27. error message 不泄露疑似 secret；
28. parser 不读取环境变量；
29. parser 不访问网络；
30. parser 不调用 provider；
31. repeated parsing 结果稳定。

---

### 7.2 prompt contract 回归测试

更新或保持：

```text
tests/test_llm_prompt_contract.py
```

确保：

1. prompt contract 中的 schema version 与 validator 一致；
2. prompt contract 中的 severity 枚举与 validator 一致；
3. prompt contract 中的 finding 字段与 validator 一致；
4. prompt contract 仍不调用 provider；
5. prompt contract 仍不读取 env；
6. prompt contract 仍不访问网络。

---

### 7.3 文档测试

更新：

```text
tests/test_llm_provider_usage_docs.py
```

确保文档中包含：

1. output validation layer；
2. `llm-semantic-review-output.v1`；
3. JSON parse / validation 说明；
4. parse error 与 validation error 的区别；
5. validator 不调用 LLM；
6. validator 不接入 `review` / `batch`；
7. parser / validator 不会自动修复不合规输出。

---

## 8. 文档更新要求

### 8.1 `docs/LLM_PROVIDER_USAGE.md`

补充：

1. LLM semantic review output validation 的作用；
2. 输入是 raw LLM output；
3. 输出是 validated semantic review output；
4. 支持纯 JSON 和 fenced JSON；
5. 不支持自动修复残缺 JSON；
6. parse error 与 validation error 的区别；
7. validator 不调用 LLM；
8. validator 不接入 `review` / `batch`；
9. validator 不生成正式 `LLMReviewResult`。

---

### 8.2 `docs/DATA_MODELS.md`

补充：

1. validated semantic review output model；
2. validated semantic finding model；
3. 字段约束；
4. schema_version；
5. severity 枚举；
6. `llm.` rule_id 前缀；
7. confidence 范围；
8. 与 `LLMReviewResult` 的区别；
9. 与 `ReviewResult` / `BatchReviewResult` 的区别。

---

### 8.3 `docs/ARCHITECTURE.md`

补充：

1. output validation layer 在 LLM 架构中的位置；
2. prompt contract 与 output validation 的关系；
3. output validation 与 provider execution 的关系；
4. output validation 不调用 provider；
5. output validation 不接入 main review；
6. 后续任务如何从 validated output 生成 `LLMReviewResult`。

---

### 8.4 `PROJECT_STATE.md`

更新：

1. 标记 `TASK-0066` 完成后新增 output validation layer；
2. 说明当前已具备 prompt contract + output validation；
3. 说明 provider execution wiring、`LLMReviewResult` generation、review/batch integration 仍是后续任务。

---

### 8.5 `CHANGELOG.md`

新增 `TASK-0066` 记录。

---

## 9. 验收标准

本任务完成后应满足：

1. 可以解析合法纯 JSON LLM output；
2. 可以解析合法 fenced JSON LLM output；
3. 可以校验 `llm-semantic-review-output.v1`；
4. 可以校验 summary；
5. 可以校验 findings 数组；
6. 可以校验 finding 必填字段；
7. 可以校验 severity 枚举；
8. 可以校验 `llm.` rule_id 前缀；
9. 可以校验 line / column；
10. 可以校验 confidence 范围；
11. 非 JSON 输出返回 parse error；
12. JSON 字段不合规返回 validation error；
13. 错误信息稳定且包含字段路径；
14. 错误信息不泄露完整 raw output；
15. parser / validator 不读取 env；
16. parser / validator 不访问网络；
17. parser / validator 不调用 provider；
18. 不生成正式 `LLMReviewResult`；
19. 不接入 `review` / `batch`；
20. 不修改公开 review result schema；
21. 不修改 sidecar metadata；
22. 文档已同步；
23. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 不要在本任务中调用 provider。
2. 不要在本任务中生成正式 `LLMReviewResult`。
3. 不要把 validator 接进 `review` CLI。
4. 不要自动修复模型输出，否则后续错误会被隐藏。
5. 不要把 prompt output contract 和 internal review result schema 混淆。
6. 不要输出完整 raw LLM output 到错误信息中。
7. 不要把 secret-like value 原样写入错误信息。
8. 不要为了方便测试而放宽 confidence / severity / line / column 校验。
9. 不要让 parser 读取环境变量或网络。
10. 本任务完成后，下一步才考虑 provider execution wiring。

---

## 11. 完成后需要运行的命令

可以先运行局部测试：

```bash
uv run pytest tests/test_llm_output_validation.py
uv run pytest tests/test_llm_prompt_contract.py
uv run pytest tests/test_llm_provider_usage_docs.py
```

最后必须运行全量测试：

```bash
uv run pytest
```

---

