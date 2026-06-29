# TASK-0068: Convert Validated LLM Semantic Output to LLMReviewResult

## 1. 背景

当前项目已经完成：

```text
TASK-0061: Add LLM Provider Secret Resolver
TASK-0062: Wire LLM Secret Resolver into LLM Check
TASK-0063: Enable Real PydanticAI Provider Construction
TASK-0064: Add Optional Live PydanticAI Runtime Smoke Check
TASK-0065: Add LLM Semantic Review Prompt Contract
TASK-0066: Add LLM Semantic Review Output Validation
TASK-0067: Wire Prompt Contract and Output Validation into PydanticAI Provider
```

目前 LLM 层已经具备：

1. secret resolver；
2. `llm-check` secret preflight；
3. PydanticAI provider construction check；
4. optional live runtime smoke check；
5. LLM semantic review prompt contract；
6. raw LLM output parser / validator；
7. `ValidatedLLMSemanticReviewOutput`；
8. `ValidatedLLMSemanticFinding`；
9. `PydanticAIReviewer.run_semantic_review(request)`；
10. provider-level semantic review pipeline：

```text
LLMReviewRequest
  ↓
prompt contract
  ↓
PydanticAI provider execution
  ↓
raw model output
  ↓
output validation
  ↓
ValidatedLLMSemanticReviewOutput
```

上一任务只完成了 provider 层的 semantic review execution，并返回 `ValidatedLLMSemanticReviewOutput`。

但当前 validated output 仍不是项目内部正式的 LLM 审计结果。后续要接入 `review` / `batch` / sidecar / report 前，需要先建立一个独立转换层：

```text
ValidatedLLMSemanticReviewOutput
  ↓
conversion layer
  ↓
LLMReviewResult
```

本任务的目标是新增 **Validated LLM Semantic Output → LLMReviewResult** 转换能力。

本任务只做转换层，不接入 `content-review review`，不接入 `content-review batch`，不修改 sidecar metadata，不修改 deterministic review engine。

---

## 2. 任务目标

本任务需要完成：

1. 新增 validated semantic output 到 `LLMReviewResult` 的转换 helper；
2. 将 `ValidatedLLMSemanticReviewOutput.findings` 转换为现有 `LLMReviewResult` 中的 finding 结构；
3. 保留 `schema_version`、summary、provider、model、source metadata 等必要信息；
4. 明确 severity、rule_id、line、column、message、evidence、suggestion、confidence 的映射规则；
5. 保证转换后结果符合当前 `LLMReviewResult` schema；
6. 不修改 `ReviewResult`、`BatchReviewResult`、`LLMReviewResult` 的公开 schema，除非当前模型完全无法表达 LLM findings 且必须做最小兼容补充；
7. 增加转换层单元测试；
8. 增加 provider-level 回归测试，确保 `PydanticAIReviewer.run_semantic_review()` 仍返回 validated output，不直接返回 `LLMReviewResult`；
9. 更新文档、项目状态和 changelog。

完成后，项目应该具备：

```text
ValidatedLLMSemanticReviewOutput
  ↓
LLMReviewResult
```

的稳定转换能力，为后续 `TASK-0069` 接入单文件 `review` 命令打基础。

---

## 3. 本任务允许做什么

本任务允许：

1. 新增 LLM result conversion 模块；
2. 新增 conversion helper；
3. 新增 conversion error 类型；
4. 小范围补充 LLM data models，仅限必要 metadata；
5. 更新 `llm/__init__.py` 导出；
6. 增加转换层测试；
7. 更新 LLM model 测试；
8. 更新 provider usage 文档测试；
9. 更新 LLM 文档；
10. 更新 architecture 文档；
11. 更新 data models 文档；
12. 更新 `PROJECT_STATE.md`；
13. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许：

1. 不允许接入 `content-review review` 主流程；
2. 不允许接入 `content-review batch` 主流程；
3. 不允许新增 `review` 或 `batch` 的 LLM CLI 开关；
4. 不允许修改 deterministic review engine 行为；
5. 不允许把 LLM findings 合并进 `ReviewResult`；
6. 不允许修改 `ReviewResult` schema；
7. 不允许修改 `BatchReviewResult` schema；
8. 不允许修改 sidecar metadata；
9. 不允许修改 `llm-check` live / construction 行为；
10. 不允许调用真实 LLM API；
11. 不允许访问外部网络；
12. 不允许读取 `.env`；
13. 不允许读取 `os.environ`；
14. 不允许新增 plaintext API key 参数；
15. 不允许让 provider factory 读取环境变量；
16. 不允许让 reserved providers 变成可创建；
17. 不允许新增 API、MCP、Skill、GUI、Supabase、用户系统或商业化能力；
18. 不允许引入 LangChain、CrewAI 或其他大型框架。

---

## 5. 需要修改的文件

预计会新增或修改以下文件：

```text
src/content_review_engine/llm/result_conversion.py
src/content_review_engine/llm/models.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/__init__.py

tests/test_llm_result_conversion.py
tests/test_llm_pydanticai_provider.py
tests/test_llm_output_validation.py
tests/test_llm_provider_usage_docs.py

docs/LLM_PROVIDER_USAGE.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前仓库已有更合适的模块命名，应优先遵守现有结构，不要为了本任务大规模重命名文件。

---

## 6. 实现要求

### 6.1 新增 result conversion 模块

建议新增：

```text
src/content_review_engine/llm/result_conversion.py
```

该模块应提供稳定 helper，例如：

```python
convert_validated_semantic_output_to_llm_review_result(
    output: ValidatedLLMSemanticReviewOutput,
    request: LLMReviewRequest,
    *,
    provider: str | None = None,
    model: str | None = None,
) -> LLMReviewResult
```

或遵守当前项目已有命名风格。

该 helper 负责：

1. 接收 `ValidatedLLMSemanticReviewOutput`；
2. 接收原始 `LLMReviewRequest`；
3. 可选接收 provider / model metadata；
4. 构造并返回 `LLMReviewResult`；
5. 不调用 provider；
6. 不访问网络；
7. 不读取环境变量；
8. 不修改输入对象。

---

### 6.2 映射规则要求

需要明确以下字段映射。

#### schema_version

`LLMReviewResult.schema_version` 应继续使用当前项目中已有的 LLM review result schema version。

不要把 `llm-semantic-review-output.v1` 直接作为 `LLMReviewResult.schema_version`。

`llm-semantic-review-output.v1` 可以进入 metadata 或 source contract 字段，前提是当前模型支持。

#### summary

`ValidatedLLMSemanticReviewOutput.summary` 应保留到 `LLMReviewResult` 中。

如果当前 `LLMReviewResult` 没有 summary 字段，可以：

1. 放入 metadata；
2. 放入 provider-specific details；
3. 或暂时不放入正式模型，但文档中说明当前 summary 未进入 result。

优先选择不破坏 schema 的方式。

#### findings

每个 `ValidatedLLMSemanticFinding` 应转换为 `LLMReviewResult` 中已有 finding 类型。

字段映射建议：

```text
ValidatedLLMSemanticFinding.rule_id      -> LLM finding rule_id
ValidatedLLMSemanticFinding.severity     -> LLM finding severity
ValidatedLLMSemanticFinding.line         -> LLM finding line
ValidatedLLMSemanticFinding.column       -> LLM finding column
ValidatedLLMSemanticFinding.message      -> LLM finding message
ValidatedLLMSemanticFinding.evidence     -> LLM finding matched_text / evidence / context
ValidatedLLMSemanticFinding.suggestion   -> LLM finding suggestion
ValidatedLLMSemanticFinding.confidence   -> LLM finding metadata / confidence field
```

具体字段名必须以当前 `LLMReviewResult` / LLM finding 模型为准。

不要为了完全照搬 validated output 而大幅修改正式模型。

---

### 6.3 confidence 处理要求

`TASK-0066` 中 validator 允许：

```text
confidence: number in 0..1 or null
```

本任务必须明确转换规则：

1. 如果 `confidence` 是数字，应保留；
2. 如果 `confidence` 是 `null`，应保持为 `None` 或省略；
3. 不允许把 `null` 强行转换为 `0`；
4. 不允许把 `null` 强行转换为 `1`；
5. 文档中说明 `confidence` 是模型自评置信度，不应作为确定性质量门禁依据。

---

### 6.4 rule_id 处理要求

validated output 已保证 `rule_id` 以 `llm.` 开头。

转换层应：

1. 保留原始 `rule_id`；
2. 不自动重命名；
3. 不自动映射为 deterministic rule_id；
4. 不去掉 `llm.` 前缀；
5. 不把 LLM rule_id 混入 deterministic rule namespace。

---

### 6.5 severity 处理要求

validated output 已保证 severity 属于：

```text
info
warning
error
critical
```

转换层应：

1. 保留 severity；
2. 不自动升级 severity；
3. 不自动降级 severity；
4. 不根据 confidence 调整 severity；
5. 不把 LLM severity 与 deterministic severity 规则混在一起。

---

### 6.6 location 处理要求

line / column 可能是：

```text
正整数
null
```

转换层应：

1. 保留 line；
2. 保留 column；
3. 对 `null` 使用当前项目模型允许的缺省值；
4. 不自动推断 line / column；
5. 不重新扫描原文定位 evidence。

后续如果需要 evidence-to-location alignment，应单独拆任务。

---

### 6.7 metadata 要求

如果当前 `LLMReviewResult` 支持 metadata，应保留：

1. semantic output schema version；
2. summary；
3. provider；
4. model；
5. review language；
6. source file；
7. finding count；
8. deterministic findings count，如果 request 中存在；
9. conversion version。

如果当前模型不支持 metadata，不应为了本任务大规模修改 schema。可以只记录在文档中说明后续补充。

---

### 6.8 错误处理要求

由于输入已经是 `ValidatedLLMSemanticReviewOutput`，转换失败应该很少。

仍建议新增或复用错误类型，例如：

```python
LLMReviewResultConversionError
```

要求：

1. 转换错误与 parse / validation error 区分；
2. 错误信息稳定；
3. 错误信息包含字段路径或 finding index；
4. 错误信息不包含 secret；
5. 错误信息不包含完整原文内容；
6. 错误信息不包含完整 raw model output。

---

### 6.9 provider 行为要求

本任务不要求修改 `PydanticAIReviewer.run_semantic_review()` 的返回类型。

它应继续返回：

```python
ValidatedLLMSemanticReviewOutput
```

不要让 provider 直接返回 `LLMReviewResult`。

转换 helper 应作为单独步骤存在：

```text
validated output
  ↓
conversion helper
  ↓
LLMReviewResult
```

这样后续可以在 runner 层、CLI 层或 sidecar 层显式使用转换逻辑。

---

### 6.10 安全要求

转换层不应：

1. 读取 `.env`；
2. 读取 `os.environ`；
3. 访问网络；
4. 调用 provider；
5. 调用 `llm-check`；
6. 调用 PydanticAI；
7. 输出 secret；
8. 输出完整用户原文；
9. 输出完整 raw model output；
10. 修改全局状态。

---

## 7. 测试要求

### 7.1 新增 result conversion 测试

新增：

```text
tests/test_llm_result_conversion.py
```

覆盖：

1. 空 findings 可以转换为 `LLMReviewResult`；
2. 单个 valid finding 可以转换；
3. 多个 findings 可以转换；
4. rule_id 保持 `llm.` 前缀；
5. severity 保持不变；
6. line / column 保持不变；
7. line / column 为 null 时可以转换；
8. message 映射正确；
9. evidence 映射正确；
10. suggestion 映射正确；
11. confidence 数字可以保留；
12. confidence 为 null 时不被强行转成 0 或 1；
13. summary 被保留或按文档约定处理；
14. provider / model metadata 被保留或按文档约定处理；
15. conversion 不修改 input object；
16. conversion 不读取 env；
17. conversion 不访问网络；
18. conversion 不调用 provider；
19. conversion error 不泄露 secret；
20. conversion output 符合当前 `LLMReviewResult` schema。

---

### 7.2 PydanticAI provider 回归测试

更新或保持：

```text
tests/test_llm_pydanticai_provider.py
```

确保：

1. `run_semantic_review()` 仍返回 `ValidatedLLMSemanticReviewOutput`；
2. provider 不直接返回 `LLMReviewResult`；
3. provider 仍复用 prompt contract；
4. provider 仍复用 output validation；
5. secret 仍不进入 prompt / output / error。

---

### 7.3 output validation 回归测试

更新或保持：

```text
tests/test_llm_output_validation.py
```

确保：

1. validated output 仍独立于 `LLMReviewResult`；
2. confidence null / numeric 行为与 conversion 测试一致；
3. schema version 保持一致；
4. parse / validation error 语义不变。

---

### 7.4 文档测试

更新：

```text
tests/test_llm_provider_usage_docs.py
```

确保文档中包含：

1. validated semantic output 到 `LLMReviewResult` 的转换层；
2. 转换层不调用 LLM；
3. 转换层不接入 `review` / `batch`；
4. provider 仍返回 validated output；
5. `LLMReviewResult` generation 是独立步骤；
6. LLM findings 仍未合并进 deterministic `ReviewResult`。

---

## 8. 文档更新要求

### 8.1 `docs/LLM_PROVIDER_USAGE.md`

补充：

1. validated semantic output conversion 的用途；
2. 如何从 `ValidatedLLMSemanticReviewOutput` 转成 `LLMReviewResult`；
3. provider execution 与 result conversion 的边界；
4. conversion 不调用 LLM；
5. conversion 不接入 `review` / `batch`；
6. confidence 的处理规则；
7. LLM rule_id namespace 与 deterministic rule_id namespace 的区别。

---

### 8.2 `docs/DATA_MODELS.md`

补充：

1. `ValidatedLLMSemanticReviewOutput` 与 `LLMReviewResult` 的区别；
2. 转换映射表；
3. `rule_id` 映射规则；
4. severity 映射规则；
5. line / column 映射规则；
6. evidence / suggestion 映射规则；
7. confidence 映射规则；
8. metadata 处理规则；
9. 说明 `ReviewResult` / `BatchReviewResult` schema 未改变。

---

### 8.3 `docs/ARCHITECTURE.md`

补充：

1. result conversion layer 在 LLM 架构中的位置；
2. prompt contract、provider execution、output validation、result conversion 四层关系；
3. 为什么 conversion 不放在 provider 内部；
4. 为什么本任务仍不接入 main review；
5. 后续任务如何接入 `review` / `batch`。

---

### 8.4 `PROJECT_STATE.md`

更新：

1. 标记 `TASK-0068` 完成后新增 result conversion layer；
2. 说明当前已有 provider execution + output validation + result conversion；
3. 说明 `review` / `batch` integration、report integration、quality gate integration 仍是后续任务。

---

### 8.5 `CHANGELOG.md`

新增 `TASK-0068` 记录。

---

## 9. 验收标准

本任务完成后应满足：

1. 存在独立 conversion helper；
2. 可以把空 findings 的 validated output 转成 `LLMReviewResult`；
3. 可以把包含 findings 的 validated output 转成 `LLMReviewResult`；
4. rule_id 保持 `llm.` 前缀；
5. severity 保持不变；
6. line / column 保持不变；
7. evidence / suggestion 映射正确；
8. confidence 数字被保留；
9. confidence null 不被强行转为 0 或 1；
10. provider / model metadata 按文档约定处理；
11. conversion 不修改 input object；
12. conversion 不读取 env；
13. conversion 不访问网络；
14. conversion 不调用 provider；
15. provider `run_semantic_review()` 仍返回 `ValidatedLLMSemanticReviewOutput`；
16. 不接入 `review` / `batch`；
17. 不修改 deterministic pipeline；
18. 不修改 sidecar metadata；
19. 不修改 `ReviewResult` / `BatchReviewResult` schema；
20. 文档已同步；
21. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 不要让 provider 直接返回 `LLMReviewResult`。
2. 不要把 conversion 接进 `review` CLI。
3. 不要把 LLM findings 合并进 deterministic `ReviewResult`。
4. 不要自动修改 severity。
5. 不要自动推断 line / column。
6. 不要把 confidence null 转成 0 或 1。
7. 不要把 LLM rule_id 改成 deterministic rule_id。
8. 不要为 metadata 大幅修改公开 schema。
9. 不要调用 provider、网络或环境变量。
10. 本任务完成后，下一步才考虑单文件 `review` 的 LLM 接入。

---

## 11. 完成后需要运行的命令

可以先运行局部测试：

```bash
uv run pytest tests/test_llm_result_conversion.py
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_output_validation.py
uv run pytest tests/test_llm_provider_usage_docs.py
```

最后必须运行全量测试：

```bash
uv run pytest
```

---

