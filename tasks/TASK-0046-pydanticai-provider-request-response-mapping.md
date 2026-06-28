# TASK-0046: Add PydanticAI Provider Request and Response Mapping

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计相关的 provider interface、mock reviewer、runner、sidecar JSON、sidecar Markdown report、provider configuration boundary 和 PydanticAI secret resolution boundary。

已完成任务包括：

```text
TASK-0040: Add Batch LLM Sidecar Output
TASK-0041: Add LLM Sidecar Summary and Error Handling
TASK-0042: Add LLM Sidecar Markdown Report
TASK-0043: Add Real LLM Provider Configuration Boundary
TASK-0044: Normalize PydanticAI Provider Adapter Boundary
TASK-0045: Add PydanticAI Provider Dependency and Secret Resolution
```

当前 provider 状态是：

```text
provider="mock"
  -> 当前唯一能够真正生成 LLMReviewResult 的 provider。

provider="pydanticai"
  -> 已恢复依赖；
  -> 已具备 secret resolution；
  -> PydanticAIReviewer 仍是 future skeleton；
  -> secret 缺失时报 LLMProviderSecretError；
  -> secret 存在时报 LLMProviderNotImplementedError；
  -> 不执行真实 review；
  -> 不发起网络请求。
```

下一步不应该马上让 provider 发起真实 API 调用。更稳妥的做法是先建立 PydanticAI provider 的 request / prompt / response mapping 边界：

1. 如何从 `LLMReviewRequest` 构造 PydanticAI 输入；
2. 如何定义 PydanticAI 期望返回的结构化响应；
3. 如何把结构化响应转换为项目内部的 `LLMReviewResult`；
4. 如何处理无效响应；
5. 如何测试 mapping 行为；
6. 如何保证 mapping 不依赖真实网络和真实 API key。

因此，本任务只实现 PydanticAI provider 的 request / response mapping 和结构化响应契约，不实现真实 PydanticAI API 调用。

本任务是后续 TASK-0047 正式启用 PydanticAI provider runtime call 的前置任务。

---

## 2. 任务目标

实现 PydanticAI provider 的 request / response mapping 层。

完成后应满足：

1. 可以从 `LLMReviewRequest` 构造 PydanticAI provider 所需的 prompt / input payload；
2. 存在清晰的 PydanticAI structured response schema；
3. 可以将 PydanticAI structured response 转换为 `LLMReviewResult`；
4. 可以处理空 findings；
5. 可以处理多个 findings；
6. 可以处理无效 severity / 空 message / 非法字段等 response validation 错误；
7. mapping 层不发起真实网络请求；
8. mapping 层不调用真实 LLM API；
9. PydanticAIReviewer 仍不执行真实 review；
10. mock provider 行为不变；
11. sidecar JSON、sidecar Markdown report、deterministic review 和 Quality Gate 行为不变。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 新增 PydanticAI request builder；
2. 新增 PydanticAI prompt / instruction 构造逻辑；
3. 新增 PydanticAI structured response 数据模型；
4. 新增 response -> `LLMReviewResult` 转换逻辑；
5. 新增 response validation 错误处理；
6. 更新 PydanticAIReviewer skeleton，使其持有 mapping 组件或调用 mapping helper；
7. 新增或更新 mapping 相关单元测试；
8. 新增或更新 PydanticAI provider skeleton 测试；
9. 更新相关文档；
10. 更新 PROJECT_STATE.md 和 CHANGELOG.md。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不执行真实 PydanticAI review；
2. 不调用真实 LLM API；
3. 不发起真实网络请求；
4. 不在测试中依赖真实 API key；
5. 不把 PydanticAI provider 接入为完整可运行 provider；
6. 不让 CLI 使用 pydanticai 生成真实 LLMReviewResult；
7. 不新增真实 provider runtime 开关；
8. 不实现 retry / timeout / rate limit；
9. 不实现 streaming；
10. 不实现多模型 fallback；
11. 不实现复杂 prompt template 管理系统；
12. 不把 LLM findings 合并进主 ReviewResult；
13. 不改变 LLMSidecarResult JSON schema；
14. 不改变 LLM sidecar Markdown report 结构；
15. 不改变 deterministic review JSON schema；
16. 不改变 deterministic Markdown report 结构；
17. 不让 Quality Gate 根据 LLM 结果失败；
18. 不实现 API / MCP / GUI；
19. 不引入 Supabase、用户系统、SaaS、多租户、支付等能力；
20. 不重构整个 CLI；
21. 不重构整个 LLM runner。

---

## 5. 需要修改的文件

预计包括但不限于：

```text
src/content_review_engine/llm/pydanticai.py
src/content_review_engine/llm/models.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/__init__.py
tests/test_llm_pydanticai_provider.py
tests/test_llm_provider.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
PROJECT_STATE.md
CHANGELOG.md
```

如果实现复杂度较高，建议新增独立 mapping 模块：

```text
src/content_review_engine/llm/pydanticai_mapping.py
tests/test_llm_pydanticai_mapping.py
```

如果当前项目更偏向把 provider 专属逻辑放在 provider 文件中，也可以先放在 `pydanticai.py`，但应避免文件过大、职责混乱。

优先推荐：

```text
src/content_review_engine/llm/pydanticai_mapping.py
```

用于放置：

```text
build_pydanticai_prompt()
PydanticAIReviewFinding
PydanticAIReviewResponse
pydanticai_response_to_llm_review_result()
```

---

## 6. 实现要求

### 6.1 Request / prompt builder

新增从 `LLMReviewRequest` 构造 PydanticAI 输入的逻辑。

建议函数名：

```text
build_pydanticai_review_prompt(request: LLMReviewRequest) -> str
```

或：

```text
build_pydanticai_review_input(request: LLMReviewRequest) -> PydanticAIReviewInput
```

构造内容应包含：

1. 待审计文本；
2. 文件路径或 reviewed file 信息；
3. profile 信息；
4. 规则上下文；
5. 输出格式要求；
6. 严格结构化输出要求；
7. 不确定时不要编造；
8. 没有发现时返回空 findings；
9. 不要输出 Markdown prose；
10. 不要输出非 schema 字段。

如果当前 `LLMReviewRequest` 中字段有限，应只使用已有字段，不要为了 prompt builder 强行扩大核心模型。

---

### 6.2 Prompt 内容要求

prompt / instruction 应明确告诉模型：

1. 你是内容发布前审计助手；
2. 只根据输入文本和规则上下文判断；
3. 输出必须符合结构化 schema；
4. 每条 finding 应包含 severity、rule_id、message、suggestion 等项目已有字段；
5. severity 只能使用项目已有 severity 枚举；
6. 如果没有问题，返回空 findings；
7. 不要返回普通自然语言解释；
8. 不要输出 Markdown；
9. 不要包含 API key、环境变量或系统信息；
10. 不要声称已完成实际修改。

注意：本任务只是构造 prompt，不调用真实模型。

---

### 6.3 Structured response schema

新增 PydanticAI structured response schema。

建议模型包括：

```text
PydanticAIReviewFinding
PydanticAIReviewResponse
```

建议字段包括：

```text
PydanticAIReviewFinding:
  rule_id
  severity
  message
  suggestion
  line
  column
  matched_text
  context

PydanticAIReviewResponse:
  findings
```

字段应尽量映射到当前已有 `LLMFinding` / `LLMReviewResult` 字段。

如果当前 `LLMFinding` 字段与上面不一致，必须以当前实际模型为准。

不要为了 PydanticAI response schema 引入不必要的新核心字段。

---

### 6.4 Response -> LLMReviewResult mapping

新增转换逻辑：

```text
pydanticai_response_to_llm_review_result(
    response: PydanticAIReviewResponse,
    request: LLMReviewRequest,
) -> LLMReviewResult
```

转换要求：

1. response findings 转换为项目内部 LLM findings；
2. severity 必须校验；
3. rule_id 不能为空；
4. message 不能为空；
5. suggestion 可以为空或 None，按当前模型规则处理；
6. line / column 如果不存在，按当前模型规则处理；
7. matched_text / context 如果不存在，按当前模型规则处理；
8. result schema_version 使用当前 `LLMReviewResult` schema version；
9. 不改变现有 `LLMReviewResult` 模型；
10. 不改变现有 serialization 行为。

---

### 6.5 Response validation

mapping 层必须处理无效响应。

至少覆盖：

1. findings 不是 list；
2. severity 不合法；
3. rule_id 为空；
4. message 为空；
5. finding 字段类型不匹配；
6. response 缺少 findings；
7. response 为 None；
8. 非预期异常应转换为稳定错误类型。

优先复用已有错误类型：

```text
LLMResponseValidationError
```

如果已有错误层级不够，可以补充小范围错误类型，但不要过度设计。

错误信息要求：

1. 清晰；
2. 稳定；
3. 适合测试断言；
4. 不包含 secret；
5. 不包含完整 prompt；
6. 不包含完整用户文章内容；
7. 不包含 traceback。

---

### 6.6 PydanticAIReviewer skeleton 行为

本任务可以更新 `PydanticAIReviewer`，使其拥有 request / response mapping helper。

但 `review()` 仍不执行真实 LLM 调用。

建议行为：

```text
PydanticAIReviewer.review(request):
  1. resolve secret
  2. build prompt / input
  3. raise LLMProviderNotImplementedError
```

或者：

```text
PydanticAIReviewer.build_prompt(request)
PydanticAIReviewer.parse_response(response, request)
```

允许暴露 provider 内部 helper 以便测试，但不应让 CLI 或 runner 依赖 provider 私有方法。

关键要求：

1. secret 缺失时仍返回 `LLMProviderSecretError`；
2. secret 存在时仍返回 `LLMProviderNotImplementedError`；
3. 不执行真实 review；
4. 不发起网络请求；
5. 不 fallback 到 mock；
6. 可以单独测试 prompt builder 和 response mapper。

---

### 6.7 CLI 行为

本任务不应改变 CLI 用户可见行为。

保持 TASK-0045 行为：

```text
--enable-llm --llm-provider mock
  -> 正常生成 mock sidecar

--enable-llm --llm-provider pydanticai
  -> secret 缺失：命令错误，返回 2
  -> secret 存在：not implemented，返回 2
  -> 不写 sidecar
  -> 不执行真实 review
```

不要新增新的 CLI 参数。

不要新增真实 provider runtime flag。

---

### 6.8 Sidecar / report / quality gate 行为

本任务不得改变以下结构和行为：

```text
LLMSidecarResult JSON schema
LLM sidecar Markdown report structure
deterministic ReviewResult
deterministic JSON output
deterministic Markdown report
Quality Gate
```

mock provider 下现有 sidecar JSON 和 Markdown report 行为必须保持兼容。

pydanticai provider 仍不能生成真实 sidecar finding。

---

## 7. 测试要求

必须新增或更新测试，覆盖以下情况。

### 7.1 Prompt builder 测试

测试：

1. prompt 包含待审计文本；
2. prompt 包含 reviewed file 或 path 信息；
3. prompt 包含 profile / rule context；
4. prompt 明确要求结构化输出；
5. prompt 明确 severity 枚举；
6. prompt 明确没有 findings 时返回空 findings；
7. prompt 不包含 secret value；
8. prompt 输出稳定，适合断言。

---

### 7.2 Response schema / mapping 测试

测试：

1. 空 findings 可以转换为空 `LLMReviewResult`；
2. 单个 finding 可以转换；
3. 多个 findings 可以转换；
4. severity 映射正确；
5. rule_id 映射正确；
6. message 映射正确；
7. suggestion 映射正确；
8. line / column / matched_text / context 按当前模型规则映射；
9. result schema_version 正确；
10. serialization 兼容现有 LLMReviewResult。

---

### 7.3 Response validation 测试

测试：

1. response 为 None；
2. response 缺少 findings；
3. findings 不是 list；
4. severity 非法；
5. rule_id 为空；
6. message 为空；
7. 字段类型错误；
8. validation error 使用 `LLMResponseValidationError`；
9. error message 不包含 secret；
10. error message 不包含完整 prompt 或完整文章内容。

---

### 7.4 PydanticAI skeleton 测试

更新 `tests/test_llm_pydanticai_provider.py`，覆盖：

1. skeleton 可以 build prompt；
2. skeleton 可以调用 response mapper；
3. secret 缺失时仍返回 `LLMProviderSecretError`；
4. secret 存在时 review 仍返回 `LLMProviderNotImplementedError`；
5. skeleton 不发起网络请求；
6. skeleton 不 fallback 到 mock；
7. skeleton 不生成真实 `LLMReviewResult`。

---

### 7.5 CLI 回归测试

CLI 行为不应变化，但需要确保已有测试继续覆盖：

1. mock provider 仍正常；
2. pydanticai 缺 secret 返回 secret error；
3. pydanticai 有 secret 返回 not implemented；
4. deterministic review 不受影响；
5. Quality Gate 不受影响；
6. sidecar / report 结构不变。

如果已有 CLI 测试已经覆盖这些点，本任务不要求重复新增大量 CLI 测试。

---

### 7.6 回归测试

必须确保已有测试全部通过：

```bash
uv run pytest
```

如果新增专门测试文件，也请额外运行：

```bash
uv run pytest tests/test_llm_pydanticai_mapping.py
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_provider.py
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

如果 `docs/CI.md` 当前提到 PydanticAI provider 或 secret/preflight 行为，也可以同步更新；否则本任务不强制修改。

更新重点：

1. 在 `docs/ARCHITECTURE.md` 中说明 PydanticAI provider request / response mapping 边界；
2. 在 `docs/ARCHITECTURE.md` 中说明 mapping 层不执行真实调用；
3. 在 `docs/DATA_MODELS.md` 中说明 PydanticAI structured response schema；
4. 在 `docs/DATA_MODELS.md` 中说明 response -> LLMReviewResult 转换；
5. 在 `docs/CLI.md` 中说明 CLI 行为仍未变化，pydanticai 仍不能执行真实 review；
6. 在 `PROJECT_STATE.md` 中记录 TASK-0046 已完成后项目状态；
7. 在 `CHANGELOG.md` 中记录本次变更。

---

## 9. 验收标准

本任务完成后应满足：

1. 存在 PydanticAI request / prompt builder；
2. 存在 PydanticAI structured response schema；
3. 存在 response -> LLMReviewResult mapping；
4. response validation 使用稳定错误类型；
5. 空 findings、单 finding、多 findings 均可正确映射；
6. 无效 response 会返回 `LLMResponseValidationError`；
7. prompt / mapping 不泄露 secret；
8. PydanticAIReviewer 仍不执行真实 review；
9. PydanticAIReviewer 仍不发起网络请求；
10. PydanticAIReviewer 仍不 fallback 到 mock；
11. CLI 行为不变；
12. mock provider 行为不变；
13. sidecar JSON schema 不变；
14. sidecar Markdown report 结构不变；
15. deterministic review JSON / Markdown report 行为不变；
16. Quality Gate 语义不变；
17. 不实现 retry / timeout / rate limit；
18. 不实现 response parsing from real provider runtime；
19. 不实现真实 LLM API 调用；
20. 新增或更新测试通过；
21. 文档、PROJECT_STATE.md、CHANGELOG.md 已同步更新；
22. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 本任务只是 request / response mapping，不是真实 provider runtime；
2. 不要在本任务中调用 PydanticAI agent；
3. 不要发起真实网络请求；
4. 不要让 CLI 生成真实 pydanticai sidecar；
5. 不要把 pydanticai fallback 到 mock；
6. 不要把 secret、完整 prompt、完整文章内容放进错误信息；
7. 不要为了 mapping 扩大核心数据模型；
8. 不要改变 sidecar schema；
9. 不要改变 report 结构；
10. 不要改变 Quality Gate；
11. prompt 应稳定，避免测试不可靠；
12. response schema 应尽量贴近现有 LLMReviewResult，不要过度设计；
13. 后续真实 runtime call 应单独放到 TASK-0047。

---

## 11. 完成后需要运行的命令

```bash
uv run pytest
```

如果涉及专门测试文件，请额外运行：

```bash
uv run pytest tests/test_llm_pydanticai_mapping.py
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_provider.py
uv run pytest tests/test_cli.py
```

具体测试文件名以实际仓库为准。

---

