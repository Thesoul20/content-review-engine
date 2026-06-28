# TASK-0047: Add PydanticAI Provider Runtime Call

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计相关的 provider interface、mock reviewer、runner、sidecar JSON、sidecar Markdown report、provider configuration boundary、PydanticAI secret resolution boundary 和 PydanticAI request / response mapping。

已完成任务包括：

```text
TASK-0040: Add Batch LLM Sidecar Output
TASK-0041: Add LLM Sidecar Summary and Error Handling
TASK-0042: Add LLM Sidecar Markdown Report
TASK-0043: Add Real LLM Provider Configuration Boundary
TASK-0044: Normalize PydanticAI Provider Adapter Boundary
TASK-0045: Add PydanticAI Provider Dependency and Secret Resolution
TASK-0046: Add PydanticAI Provider Request and Response Mapping
```

当前 provider 状态是：

```text
provider="mock"
  -> 当前唯一能够生成 LLMReviewResult 的可运行 provider。

provider="pydanticai"
  -> 依赖已恢复；
  -> secret resolution 已完成；
  -> request / prompt / response mapping 已完成；
  -> 仍然不执行真实 review；
  -> secret 存在时仍返回 LLMProviderNotImplementedError。
```

TASK-0046 已经建立了：

```text
LLMReviewRequest
  -> PydanticAIReviewRequestPayload
  -> system_prompt / user_prompt
  -> PydanticAIReviewResponse
  -> LLMReviewResult
```

因此，下一步可以正式实现 PydanticAI provider 的 runtime call。

本任务只做一件核心事情：

> 让 `PydanticAIReviewer.review()` 在显式选择 `--enable-llm --llm-provider pydanticai` 且 secret 存在时，调用 PydanticAI runtime，并把结构化响应映射为 `LLMReviewResult`。

本任务不做 retry、timeout、rate limit、streaming、并发优化、主报告合并、Quality Gate 集成、API / MCP / GUI。

---

## 2. 任务目标

实现 PydanticAI provider 的真实 runtime review 调用。

完成后应满足：

1. `PydanticAIReviewer.review()` 可以在 secret 存在时执行真实 PydanticAI review；
2. 真实 provider 调用复用 TASK-0046 的 prompt builder 和 response mapper；
3. PydanticAI 返回的结构化响应可以转换为项目内部 `LLMReviewResult`；
4. `provider="pydanticai"` 不再返回 `LLMProviderNotImplementedError`；
5. `provider="pydanticai"` 在 secret 缺失时仍返回 `LLMProviderSecretError`；
6. provider runtime error 应转换为稳定的 `LLMProviderError` 或合适错误类型；
7. response validation error 应继续使用 `LLMResponseValidationError`；
8. mock provider 行为不变；
9. sidecar JSON 输出继续通过现有 LLMSidecarResult 结构；
10. sidecar Markdown report 继续通过现有 report renderer；
11. deterministic review、主 JSON、主 Markdown report 和 Quality Gate 行为不变；
12. 测试中不得依赖真实 API key 或真实网络。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 实现 `PydanticAIReviewer.review()` 的真实 PydanticAI runtime 调用；
2. 使用已有 secret resolution 获取 API key；
3. 使用已有 `LLMProviderConfig.model` 选择模型；
4. 使用已有 `LLMProviderConfig.base_url`，如果当前 PydanticAI 依赖支持且实现成本低；
5. 复用 TASK-0046 的 system prompt / user prompt / request payload；
6. 复用 TASK-0046 的 structured response schema；
7. 复用 TASK-0046 的 response -> `LLMReviewResult` mapping；
8. 将 PydanticAI runtime 异常转换为稳定 provider error；
9. 将 response validation 异常转换为 `LLMResponseValidationError`；
10. 更新 provider factory / CLI 行为，使 pydanticai provider 在 secret 存在时不再返回 not implemented；
11. 新增 mockable runtime 单元测试；
12. 新增 CLI 测试，使用 fake / stub provider 或 monkeypatch，避免真实网络；
13. 更新相关文档；
14. 更新 PROJECT_STATE.md 和 CHANGELOG.md。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不在测试中调用真实 LLM API；
2. 不在测试中依赖真实 API key；
3. 不把真实 API key 写入 config、sidecar、report、日志或错误信息；
4. 不新增 retry 机制；
5. 不新增 timeout 机制；
6. 不新增 rate limit 机制；
7. 不新增 streaming；
8. 不新增 batch 并发；
9. 不新增多模型 fallback；
10. 不新增 prompt template 管理系统；
11. 不把 LLM findings 合并进主 ReviewResult；
12. 不改变 LLMSidecarResult JSON schema；
13. 不改变 LLM sidecar Markdown report 结构；
14. 不改变 deterministic review JSON schema；
15. 不改变 deterministic Markdown report 结构；
16. 不让 Quality Gate 根据 LLM 结果失败；
17. 不新增 `--fail-on-llm`；
18. 不实现 API / MCP / GUI；
19. 不引入 Supabase、用户系统、SaaS、多租户、支付等能力；
20. 不重构整个 CLI；
21. 不重构整个 LLM runner；
22. 不直接接入 OpenAI / Anthropic 官方 SDK 作为独立 provider；
23. 不绕过 `LLMReviewer` provider interface。

---

## 5. 需要修改的文件

预计包括但不限于：

```text
src/content_review_engine/llm/pydanticai.py
src/content_review_engine/llm/pydanticai_mapping.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/factory.py
src/content_review_engine/llm/__init__.py
src/content_review_engine/cli.py
tests/test_llm_pydanticai_provider.py
tests/test_llm_pydanticai_mapping.py
tests/test_llm_provider_factory.py
tests/test_cli.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
docs/CI.md
PROJECT_STATE.md
CHANGELOG.md
```

如果为了测试 runtime call 需要新增 fake runtime helper，可以新增：

```text
tests/test_llm_pydanticai_runtime.py
```

如果实现中需要隔离 PydanticAI runtime adapter，也可以新增：

```text
src/content_review_engine/llm/pydanticai_runtime.py
```

但只有在能明显降低耦合、提升可测试性时才新增。不要过度拆分。

---

## 6. 实现要求

### 6.1 Runtime call 总体边界

本任务完成后，PydanticAI provider 的执行链路应为：

```text
LLMReviewRequest
  -> PydanticAIReviewer.review()
  -> resolve_llm_api_key(config)
  -> build_pydanticai_review_request(request)
  -> PydanticAI runtime call
  -> PydanticAIReviewResponse
  -> validate_pydanticai_review_response()
  -> pydanticai_response_to_llm_review_result()
  -> LLMReviewResult
  -> LLMSidecarResult
```

关键要求：

1. runtime call 只能发生在用户显式启用 LLM 且选择 `pydanticai` provider 时；
2. mock provider 行为保持不变；
3. PydanticAI provider 不 fallback 到 mock；
4. PydanticAI provider 不绕过 mapper；
5. PydanticAI provider 不直接返回自然语言文本；
6. PydanticAI provider 必须返回结构化响应并映射为 `LLMReviewResult`。

---

### 6.2 PydanticAI runtime 使用要求

实现时应以当前项目实际安装的 PydanticAI 版本为准。

编码前需要检查：

```text
pyproject.toml
uv.lock
PydanticAI 当前版本对应的官方 API
当前已有 pydanticai.py skeleton
当前已有 pydanticai_mapping.py
```

实现要求：

1. 使用 PydanticAI 的结构化输出能力；
2. 不直接解析自然语言 Markdown；
3. 不通过正则从模型文本中抽取 JSON；
4. 不绕过 `PydanticAIReviewResponse` schema；
5. 不把 provider runtime 对象暴露给 CLI；
6. 不把 PydanticAI 相关细节泄漏到 core review engine；
7. 不在 import 时创建真实 client 或发起网络请求；
8. 不在 tests 中发起真实网络请求。

如果 PydanticAI API 需要 `Agent`、`RunContext`、`result_type` 或类似结构，请按当前安装版本选择最小、可测试实现。

---

### 6.3 Model / provider config 使用

使用 `LLMProviderConfig` 中已有字段：

```text
provider
model
api_key_env
base_url
```

要求：

1. `model` 应用于 PydanticAI runtime；
2. 如果 `model` 缺失，应使用清晰默认值或返回 config error；
3. 默认值必须在文档中说明；
4. `api_key_env` 通过 secret resolver 读取；
5. `base_url` 如果支持且实现简单，可以传入；如果当前 PydanticAI API 不适合本任务实现，应明确暂不使用并在文档说明；
6. 不把 API key value 存入 config；
7. 不把 API key value 写入错误信息、日志、sidecar 或 report。

推荐默认模型：

```text
openai:gpt-4o-mini
```

如果项目已有默认模型约定，请遵循已有约定。

---

### 6.4 Secret handling

继续使用 TASK-0045 的 secret resolution。

要求：

1. `api_key_env` 缺失时报 `LLMProviderSecretError`；
2. env var 不存在时报 `LLMProviderSecretError`；
3. env var 为空时报 `LLMProviderSecretError`；
4. secret 存在时才允许尝试 runtime call；
5. 不输出 secret value；
6. 不把 secret value 放入 prompt；
7. 不把 secret value 放入 PydanticAIReviewRequestPayload；
8. 不把 secret value 放入 LLMReviewResult；
9. 不把 secret value 放入 sidecar JSON；
10. 不把 secret value 放入 sidecar Markdown report；
11. 不把 secret value 放入 exception message。

---

### 6.5 Response mapping

必须复用 TASK-0046 的 mapping：

```text
PydanticAIReviewResponse
  -> validate_pydanticai_review_response()
  -> pydanticai_response_to_llm_review_result()
```

要求：

1. 空 findings 正常映射；
2. 单 finding 正常映射；
3. 多 findings 正常映射；
4. summary 正常映射；
5. invalid severity 抛 `LLMResponseValidationError`；
6. 空 rule_id 抛 `LLMResponseValidationError`；
7. 空 message 抛 `LLMResponseValidationError`；
8. 字段类型错误抛 `LLMResponseValidationError`；
9. validation error 不包含 secret；
10. validation error 不包含完整 prompt；
11. validation error 不包含完整文章内容；
12. validation error 不包含 traceback。

---

### 6.6 Runtime error handling

PydanticAI runtime 可能出现：

```text
provider authentication error
network error
model error
rate limit error
invalid response error
unexpected runtime exception
```

本任务不实现 retry，也不做复杂分类，但必须提供稳定错误边界。

要求：

1. PydanticAI runtime 异常转换为 `LLMProviderError` 或合适 provider error；
2. response validation 问题转换为 `LLMResponseValidationError`；
3. secret 问题转换为 `LLMProviderSecretError`；
4. error message 清晰；
5. error message 不包含 secret；
6. error message 不包含完整 prompt；
7. error message 不包含完整文章内容；
8. error message 不包含 traceback；
9. 不吞掉异常后返回假成功；
10. 不 fallback 到 mock。

---

### 6.7 CLI 行为

本任务会改变 `pydanticai` provider 的 CLI 行为。

之前 TASK-0045 / TASK-0046 行为：

```text
--enable-llm --llm-provider pydanticai
  -> secret 存在时仍返回 not implemented
```

本任务完成后应改为：

```text
--enable-llm --llm-provider pydanticai
  -> secret 缺失：命令错误或 sidecar failed，按当前 CLI provider initialization 策略处理
  -> secret 存在：执行真实 PydanticAI review
  -> 成功时生成 LLM sidecar JSON
  -> 如指定 --llm-markdown-output，也生成 LLM sidecar Markdown report
```

要求：

1. `--enable-llm --llm-provider mock` 行为不变；
2. `--enable-llm --llm-provider pydanticai` 不再返回 not implemented；
3. 未启用 `--enable-llm` 时 provider 参数仍不影响 deterministic review；
4. `--llm-output` / `--llm-output-dir` / `--llm-markdown-output` 语义保持不变；
5. 不新增 `--fail-on-llm`；
6. Quality Gate 仍只由 deterministic findings 决定；
7. provider runtime failure 不应被当作 deterministic finding；
8. CLI 测试必须使用 fake / monkeypatch，不得真实调用 API。

对于 runtime failure 是否写入 sidecar：

1. 如果当前 LLM runner 已支持 failed sidecar entry，应复用；
2. 如果 provider 初始化阶段失败导致无法生成 sidecar，可保持现有 command error 行为；
3. 不要为了本任务大改 runner 失败语义。

---

### 6.8 单文件与 batch 行为

由于现有 CLI 已经支持单文件和 batch sidecar，本任务需要明确 pydanticai provider 的适用范围。

推荐要求：

1. 单文件 review 支持 pydanticai provider runtime call；
2. batch review 可以复用同一个 provider runner，以顺序方式处理文件；
3. 不新增 batch 并发；
4. batch 中单个文件 provider runtime failure 应尽量通过已有 partial failure sidecar 机制表达；
5. 不新增 rate limit；
6. 不新增 retry；
7. 不改变 batch deterministic review 行为；
8. 不改变 batch manifest schema；
9. 不改变 batch sidecar Markdown report 结构。

如果当前架构中 batch 接入真实 provider 会牵涉较大改动，本任务可以优先保证单文件真实 pydanticai runtime，batch 只通过现有 runner 路径自然支持；不要额外做复杂 batch provider orchestration。

---

## 7. 测试要求

所有测试必须避免真实 API key 和真实网络。

### 7.1 PydanticAI runtime 单元测试

必须新增或更新测试，覆盖：

1. secret 存在时会调用 fake PydanticAI runtime；
2. fake runtime 返回空 findings，可以映射为空 `LLMReviewResult`；
3. fake runtime 返回单 finding，可以映射为 `LLMReviewResult`；
4. fake runtime 返回多个 findings，可以映射为 `LLMReviewResult`；
5. fake runtime 返回 summary，可以映射为 `LLMReviewSummary`；
6. fake runtime invalid response 触发 `LLMResponseValidationError`；
7. fake runtime 抛异常时转换为 `LLMProviderError`；
8. 不 fallback 到 mock；
9. 不发起真实网络请求；
10. 不泄露 secret。

建议通过 monkeypatch / fake runtime / dependency injection 测试，不要真实调用 PydanticAI API。

---

### 7.2 Secret 测试

继续覆盖：

1. 缺失 `api_key_env`；
2. env var 不存在；
3. env var 为空；
4. env var 存在；
5. 错误信息不包含 secret value；
6. runtime error 不包含 secret value；
7. response validation error 不包含 secret value。

如果已有 `tests/test_llm_secrets.py` 已覆盖基础部分，本任务只需要补充 runtime 相关 secret 泄露测试。

---

### 7.3 Provider factory 测试

更新 factory 测试，覆盖：

1. `provider="mock"` 返回 `MockLLMReviewer`；
2. `provider="pydanticai"` 返回可执行 runtime 的 `PydanticAIReviewer`；
3. unknown provider 返回 `LLMProviderConfigError`；
4. pydanticai 不 fallback 到 mock；
5. factory 不发起网络请求；
6. factory 不读取 secret value，除非当前设计明确在 review 阶段读取 secret；
7. factory 不直接执行 review。

---

### 7.4 CLI 测试

必须更新 CLI 测试，覆盖：

1. `--enable-llm --llm-provider mock` 行为不变；
2. `--enable-llm --llm-provider pydanticai` 在 fake runtime 成功时生成 sidecar JSON；
3. `--enable-llm --llm-provider pydanticai --llm-markdown-output` 在 fake runtime 成功时生成 sidecar Markdown report；
4. pydanticai runtime 返回 finding 时，sidecar JSON 包含 finding；
5. pydanticai runtime 返回 no findings 时，sidecar JSON finding_count 为 0；
6. pydanticai runtime failure 不影响 deterministic review 输出；
7. Quality Gate 不受 pydanticai findings 或 runtime failure 影响；
8. 未启用 `--enable-llm` 时 provider 参数不影响 deterministic review；
9. CLI stderr / sidecar / report 不包含 secret value；
10. 测试不得使用真实 API key 或真实网络。

如果 batch pydanticai runtime 通过现有 runner 自然支持，也应增加一个最小 batch fake runtime 测试，覆盖 batch manifest / sidecar report 基本行为。

---

### 7.5 Mapping 回归测试

确保已有 mapping 测试继续通过：

```text
tests/test_llm_pydanticai_mapping.py
```

不得因为 runtime 接入而降低 mapping 层测试覆盖。

---

### 7.6 回归测试

必须确保已有测试全部通过：

```bash
uv run pytest
```

如果新增或修改了专门测试文件，也请额外运行：

```bash
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_pydanticai_mapping.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_secrets.py
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
docs/CI.md
PROJECT_STATE.md
CHANGELOG.md
```

更新重点：

1. 在 `docs/ARCHITECTURE.md` 中说明 PydanticAI provider runtime call 已接入；
2. 在 `docs/ARCHITECTURE.md` 中说明 runtime call 仍通过 provider interface、secret resolver 和 mapper；
3. 在 `docs/DATA_MODELS.md` 中说明 runtime response 仍映射到 `LLMReviewResult`；
4. 在 `docs/CLI.md` 中说明如何使用 `--enable-llm --llm-provider pydanticai`；
5. 在 `docs/CLI.md` 中说明需要设置 `--llm-api-key-env`；
6. 在 `docs/CLI.md` 中说明 pydanticai runtime 结果仍通过 sidecar JSON / Markdown report 输出；
7. 在 `docs/CI.md` 中说明真实 LLM provider 结果仍不影响 deterministic Quality Gate；
8. 在 `PROJECT_STATE.md` 中记录 TASK-0047 已完成后项目状态；
9. 在 `CHANGELOG.md` 中记录本次变更。

---

## 9. 验收标准

本任务完成后应满足：

1. `PydanticAIReviewer.review()` 可以执行 PydanticAI runtime call；
2. pydanticai provider 不再返回 not implemented；
3. secret 缺失仍返回 `LLMProviderSecretError`；
4. runtime 异常转换为稳定 provider error；
5. invalid response 转换为 `LLMResponseValidationError`；
6. runtime response 复用 TASK-0046 mapping 转换为 `LLMReviewResult`；
7. 空 findings、单 finding、多 findings、summary 都能正确处理；
8. CLI 可以通过 `--enable-llm --llm-provider pydanticai` 使用真实 provider；
9. CLI 能输出 pydanticai sidecar JSON；
10. CLI 能输出 pydanticai sidecar Markdown report；
11. mock provider 行为不变；
12. sidecar JSON schema 不变；
13. sidecar Markdown report 结构不变；
14. deterministic review JSON / Markdown report 行为不变；
15. Quality Gate 语义不变；
16. 不新增 retry / timeout / rate limit；
17. 不新增 streaming；
18. 不新增 batch 并发；
19. 测试不依赖真实 API key；
20. 测试不发起真实网络请求；
21. 文档、PROJECT_STATE.md、CHANGELOG.md 已同步更新；
22. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 本任务是第一个真实 LLM runtime call 任务，必须保持范围克制；
2. 不要顺手实现 retry / timeout / rate limit；
3. 不要顺手实现 streaming；
4. 不要顺手实现 batch 并发；
5. 不要把 LLM findings 合并进主 ReviewResult；
6. 不要让 LLM findings 影响 Quality Gate；
7. 不要把 secret value 写入任何输出；
8. 不要把完整 prompt 或完整文章内容写入 provider error；
9. 不要让 runtime exception 泄露 traceback；
10. 不要 fallback 到 mock；
11. 不要绕过 TASK-0046 mapping；
12. 测试必须使用 fake / monkeypatch，不得访问真实网络；
13. 如果 PydanticAI API 使用方式不确定，应优先保持最小实现，并在文档中说明限制；
14. 后续 retry / timeout / rate limit 应单独放到 TASK-0048 或之后。

---

## 11. 完成后需要运行的命令

```bash
uv run pytest
```

如果涉及专门测试文件，请额外运行：

```bash
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_pydanticai_mapping.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_secrets.py
uv run pytest tests/test_cli.py
```

具体测试文件名以实际仓库为准。

---

