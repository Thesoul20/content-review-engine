# TASK-0048: Add PydanticAI Runtime Timeout and Error Classification

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计相关的 provider interface、mock reviewer、runner、sidecar JSON、sidecar Markdown report、provider configuration boundary、PydanticAI secret resolution、PydanticAI request / response mapping 和 PydanticAI runtime call。

已完成任务包括：

```text
TASK-0040: Add Batch LLM Sidecar Output
TASK-0041: Add LLM Sidecar Summary and Error Handling
TASK-0042: Add LLM Sidecar Markdown Report
TASK-0043: Add Real LLM Provider Configuration Boundary
TASK-0044: Normalize PydanticAI Provider Adapter Boundary
TASK-0045: Add PydanticAI Provider Dependency and Secret Resolution
TASK-0046: Add PydanticAI Provider Request and Response Mapping
TASK-0047: Add PydanticAI Provider Runtime Call
```

当前 provider 状态是：

```text
provider="mock"
  -> 可运行，生成 mock LLMReviewResult。

provider="pydanticai"
  -> 可运行；
  -> 使用 secret resolver；
  -> 使用 PydanticAI runtime call；
  -> 使用 TASK-0046 的 prompt / structured response / mapper；
  -> 结果输出到 LLM sidecar JSON / LLM sidecar Markdown report；
  -> 不影响 deterministic ReviewResult / Quality Gate。
```

TASK-0047 已经正式打开真实 PydanticAI runtime call，但当前 runtime 仍缺少两个生产化前的基础能力：

1. 可配置 timeout；
2. 更稳定、可测试、可文档化的 provider runtime error classification。

如果没有 timeout，真实 LLM 调用可能长时间阻塞 CLI 或 batch。
如果没有错误分类，用户看到的错误只能是笼统的 provider runtime failure，不利于判断是认证失败、网络失败、超时、限流、模型错误还是响应校验失败。

因此，本任务目标是：在不改变 sidecar schema、不改变 report 结构、不改变 Quality Gate 语义的前提下，为 PydanticAI runtime 增加 timeout 配置和错误分类边界。

本任务不做 retry、不做 rate limit、不做并发、不做 streaming、不做主报告合并。

---

## 2. 任务目标

实现 PydanticAI runtime 的 timeout 配置和 runtime error classification。

完成后应满足：

1. `LLMProviderConfig` 支持 timeout 配置；
2. CLI 支持配置 LLM runtime timeout；
3. timeout 配置可传递到 PydanticAI runtime 或其底层 provider/client；
4. timeout 必须可测试；
5. timeout 错误应映射为稳定错误类型；
6. PydanticAI runtime error 应能分类为稳定的 provider error；
7. secret/config/validation/runtime timeout 等错误边界清晰；
8. error message 不泄露 API key、完整 prompt、完整文章内容或 traceback；
9. sidecar JSON schema 不变；
10. LLM sidecar Markdown report 结构不变；
11. deterministic review 输出不变；
12. Quality Gate 语义不变；
13. mock provider 行为不变；
14. 测试不依赖真实 API key 或真实网络。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 为 `LLMProviderConfig` 增加 timeout 配置字段；
2. 为 CLI 增加 timeout 参数；
3. 校验 timeout 参数合法性；
4. 将 timeout 配置传递给 PydanticAI runtime；
5. 新增或更新 PydanticAI runtime error classifier；
6. 新增 timeout 相关错误类型，或复用现有 provider error 层级；
7. 将 timeout / auth / network / rate limit / model / unknown runtime errors 映射到稳定错误；
8. 保持 `LLMResponseValidationError` 继续只表达结构化响应校验失败；
9. 更新 PydanticAI provider runtime 测试；
10. 更新 CLI 测试；
11. 更新 provider config 测试；
12. 更新相关文档；
13. 更新 PROJECT_STATE.md 和 CHANGELOG.md。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不实现 retry；
2. 不实现 rate limit queue；
3. 不实现 batch 并发；
4. 不实现 streaming；
5. 不实现多模型 fallback；
6. 不实现 provider fallback；
7. 不新增 `--fail-on-llm`；
8. 不让 Quality Gate 根据 LLM 结果失败；
9. 不把 LLM findings 合并进主 ReviewResult；
10. 不改变 LLMSidecarResult JSON schema；
11. 不改变 LLM sidecar Markdown report 结构；
12. 不改变 deterministic ReviewResult schema；
13. 不改变 deterministic JSON 输出结构；
14. 不改变 deterministic Markdown report 默认结构；
15. 不改变 batch manifest schema，除非只是错误类型字符串自然变化；
16. 不实现 API / MCP / GUI；
17. 不引入 Supabase、用户系统、SaaS、多租户、支付等能力；
18. 不直接新增 OpenAI / Anthropic 官方 SDK provider；
19. 不绕过 `LLMReviewer` provider interface；
20. 不让 tests 依赖真实 API key 或真实网络；
21. 不把 API key 写入 config、sidecar、report、日志或错误信息。

---

## 5. 需要修改的文件

预计包括但不限于：

```text
src/content_review_engine/llm/config.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/pydanticai.py
src/content_review_engine/llm/factory.py
src/content_review_engine/llm/__init__.py
src/content_review_engine/cli.py
tests/test_llm_config.py
tests/test_llm_provider.py
tests/test_llm_provider_factory.py
tests/test_llm_pydanticai_provider.py
tests/test_cli.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
docs/CI.md
PROJECT_STATE.md
CHANGELOG.md
```

如果错误分类逻辑较多，建议新增独立模块：

```text
src/content_review_engine/llm/pydanticai_errors.py
tests/test_llm_pydanticai_errors.py
```

是否新增独立模块由实际复杂度决定。
如果分类逻辑很短，可以先放在 `pydanticai.py` 中，但不要让 `pydanticai.py` 变得过于臃肿。

---

## 6. 实现要求

### 6.1 LLMProviderConfig timeout 字段

为 `LLMProviderConfig` 增加 timeout 配置。

建议字段：

```text
timeout_seconds
```

建议类型：

```text
float | None
```

或按项目现有数据模型风格使用：

```text
int | None
```

要求：

1. 默认值可以为 `None`，表示使用 provider/runtime 默认 timeout；
2. 如果设置，必须大于 0；
3. 如果传入 0、负数、非数字，应返回 `LLMProviderConfigError` 或 CLI 参数错误；
4. 不要把 timeout 和 retry 混在一起；
5. 不要新增 retry_count；
6. 不要新增 rate_limit 配置；
7. 不要新增并发配置；
8. config serialization 不应包含 secret；
9. 文档中说明 timeout 当前只用于 LLM provider runtime。

如果项目希望提供默认 timeout，也可以设置明确默认值，例如：

```text
timeout_seconds = 60
```

但如果设置默认值，必须同步更新文档和测试。

---

### 6.2 CLI 参数

新增 CLI 参数：

```text
--llm-timeout-seconds <seconds>
```

适用于：

```text
content-review review ...
content-review batch ...
```

要求：

1. 只有启用 `--enable-llm` 时才会实际影响 LLM provider；
2. 未启用 `--enable-llm` 时，不应影响 deterministic review；
3. 对 mock provider 可以解析但不实际产生行为变化；
4. 对 pydanticai provider 应传递到 runtime config；
5. 非法值应给出清晰错误；
6. 错误信息不包含 secret；
7. 不新增 `--llm-retry`；
8. 不新增 `--llm-rate-limit`；
9. 不新增 `--llm-concurrency`。

示例：

```bash
content-review review article.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-timeout-seconds 30 \
  --llm-output article.llm.json
```

batch 示例：

```bash
content-review batch docs/ \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-timeout-seconds 30 \
  --llm-output-dir llm-sidecars \
  --llm-markdown-output llm-report.md
```

---

### 6.3 PydanticAI runtime timeout 使用

PydanticAI runtime call 应尽量使用当前安装版本支持的 timeout 配置路径。

实现前请检查：

```text
当前 pydantic-ai-slim 版本
pydantic_ai.Agent API
OpenAIProvider / OpenAIChatModel API
底层 client 是否支持 timeout
```

实现要求：

1. 如果当前 PydanticAI / OpenAIProvider / OpenAIChatModel 支持 timeout 参数，应将 `timeout_seconds` 传递进去；
2. 如果 timeout 需要通过底层 client 配置，应保持最小实现，不要重构整个 provider；
3. 如果当前 API 不适合实现硬 timeout，应至少保留 config、CLI、测试 fake runtime timeout 分类，并在文档中说明当前 timeout 以 provider 支持为准；
4. 不要用复杂线程 / 进程 / signal hack 实现 timeout；
5. 不要引入新的 async runtime 架构；
6. 不要为了 timeout 重构 CLI 或 runner；
7. 不要新增 retry；
8. 不要新增 rate limit。

测试必须通过 fake runtime / monkeypatch 覆盖 timeout 行为，不能依赖真实等待或真实网络。

---

### 6.4 Runtime error classification

新增 PydanticAI runtime error classification。

建议支持以下分类：

```text
secret_error
config_error
timeout_error
authentication_error
rate_limit_error
network_error
model_error
response_validation_error
provider_runtime_error
unknown_provider_error
```

不一定要把这些分类都做成新的异常类。可以采用以下两种方式之一：

#### 方案 A：异常类型细分

新增：

```text
LLMProviderTimeoutError
LLMProviderAuthenticationError
LLMProviderRateLimitError
LLMProviderNetworkError
```

它们都继承自：

```text
LLMProviderError
```

#### 方案 B：保持异常类型较少，但 message / error_type 稳定

保留主要错误类型：

```text
LLMProviderError
LLMProviderSecretError
LLMProviderConfigError
LLMResponseValidationError
```

并通过稳定 message 表达分类。

优先推荐方案 A，但不要过度设计。
如果实现中无法可靠识别某类错误，可以先归入 `LLMProviderError`，但应确保 timeout 有明确错误类型或稳定 error_type。

---

### 6.5 错误映射规则

建议错误映射如下：

```text
LLMProviderSecretError
  -> secret 缺失、env 不存在、env 为空

LLMProviderConfigError
  -> model 缺失、timeout 非法、provider config 非法

LLMProviderTimeoutError
  -> runtime timeout

LLMResponseValidationError
  -> provider 返回结构化响应无效

LLMProviderError
  -> 其他 PydanticAI runtime/provider 异常
```

如果新增更多细分错误类型，也要保持稳定命名，便于 sidecar 中的 `error_type` 可测试。

错误信息要求：

1. 清晰；
2. 稳定；
3. 不包含 API key；
4. 不包含完整 prompt；
5. 不包含完整文章内容；
6. 不包含 traceback；
7. 不包含环境变量值；
8. 可用于 CLI stderr；
9. 可用于 sidecar error.message；
10. 可用于 Markdown report error 展示。

---

### 6.6 Sidecar 错误表达

本任务不改变 sidecar schema。

现有 failed sidecar entry 应继续使用：

```text
status: failed
error:
  error_type: ...
  message: ...
```

要求：

1. timeout 失败时，`error_type` 应稳定；
2. provider runtime failure 时，`error_type` 应稳定；
3. response validation failure 时，`error_type` 应稳定；
4. 不把 traceback 放入 sidecar；
5. 不把 secret 放入 sidecar；
6. 不把完整 prompt 或完整文章放入 sidecar；
7. batch partial failure 语义不变；
8. batch manifest schema 不变。

---

### 6.7 CLI 行为

CLI 行为要求：

1. `--enable-llm --llm-provider mock` 行为不变；
2. `--enable-llm --llm-provider pydanticai` 行为不变，除了支持 timeout；
3. `--llm-timeout-seconds` 在未启用 LLM 时不影响 deterministic review；
4. invalid timeout 应返回清晰 CLI/config error；
5. pydanticai timeout/runtime failure 不应变成 deterministic finding；
6. Quality Gate 仍只看 deterministic findings；
7. 不新增 `--fail-on-llm`；
8. 不新增 retry 相关参数；
9. 不新增 rate limit 相关参数。

对于 provider runtime failure：

1. 单文件 sidecar 行为应复用现有 failed sidecar 机制或现有 command error 策略；
2. batch 中单文件 timeout/runtime failure 应尽量复用 partial failure sidecar；
3. 不要因为 timeout classification 大改 runner 语义。

---

### 6.8 Mock provider 行为

mock provider 不需要实现 timeout 行为。

要求：

1. mock provider 继续返回 mock LLMReviewResult；
2. mock provider 不受 timeout 配置影响；
3. CLI 可以接受 `--llm-timeout-seconds` 但 mock 不需要使用；
4. mock 相关测试不应因为 timeout 字段失败；
5. mock provider 不应模拟真实 runtime errors，除非已有测试机制需要。

---

### 6.9 Quality Gate 行为

Quality Gate 不应改变。

要求：

1. deterministic findings 仍然是 Quality Gate 唯一依据；
2. LLM timeout 不应直接导致 Quality Gate failure；
3. LLM provider runtime failure 不应变成 deterministic finding；
4. LLM sidecar failed 不应改变 deterministic exit code 语义，除非当前 CLI 对 provider initialization error 已有命令错误策略；
5. 不新增 LLM-based gate；
6. 不新增 `--fail-on-llm`。

文档中必须说明：

```text
LLM provider timeout / runtime errors are LLM sidecar/provider errors, not deterministic quality gate failures.
```

---

## 7. 测试要求

所有测试必须避免真实 API key 和真实网络。

### 7.1 Config 测试

更新 `tests/test_llm_config.py`，覆盖：

1. 默认 timeout 为 None 或项目约定默认值；
2. 可以设置合法 timeout；
3. timeout 可以序列化；
4. timeout 不影响 secret 安全；
5. 0 timeout 非法；
6. 负数 timeout 非法；
7. 非数字 timeout 在 CLI 或 config 层非法；
8. timeout 不影响 mock 默认行为。

---

### 7.2 Runtime error classification 测试

新增或更新测试，覆盖：

1. fake runtime timeout -> `LLMProviderTimeoutError` 或稳定 timeout error；
2. fake runtime network error -> stable provider/network error；
3. fake runtime auth error -> stable provider/auth error，如果实现了 auth 分类；
4. fake runtime rate limit error -> stable provider/rate limit error，如果实现了 rate limit 分类；
5. fake runtime unknown error -> `LLMProviderError`；
6. invalid structured response -> `LLMResponseValidationError`；
7. secret error 仍为 `LLMProviderSecretError`；
8. config error 仍为 `LLMProviderConfigError`；
9. error message 不包含 secret；
10. error message 不包含完整 prompt；
11. error message 不包含完整文章内容；
12. error message 不包含 traceback。

建议新增：

```text
tests/test_llm_pydanticai_errors.py
```

如果分类逻辑放在 `pydanticai.py`，也可以在：

```text
tests/test_llm_pydanticai_provider.py
```

中覆盖。

---

### 7.3 PydanticAI provider 测试

更新 `tests/test_llm_pydanticai_provider.py`，覆盖：

1. timeout_seconds 被传递到 fake runtime / fake runtime factory；
2. timeout_seconds 缺失时使用默认行为；
3. fake runtime timeout 时返回 timeout error；
4. fake runtime unknown error 时返回 provider error；
5. fake runtime invalid response 时返回 response validation error；
6. 不 fallback 到 mock；
7. 不发起真实网络；
8. 不泄露 secret；
9. model 缺失仍为 config error；
10. base_url 行为保持已有测试。

---

### 7.4 CLI 测试

更新 `tests/test_cli.py`，覆盖：

1. `--llm-timeout-seconds` 可以被 review 命令解析；
2. `--llm-timeout-seconds` 可以被 batch 命令解析；
3. valid timeout 传递到 fake pydanticai provider；
4. invalid timeout 返回清晰错误；
5. 未启用 `--enable-llm` 时 timeout 不影响 deterministic review；
6. mock provider 下 timeout 不改变行为；
7. pydanticai fake timeout 不影响 deterministic review 输出；
8. batch 中某文件 fake timeout 可进入 failed sidecar / manifest；
9. Quality Gate 不受 LLM timeout 影响；
10. CLI stderr / sidecar / report 不包含 secret。

---

### 7.5 Sidecar / report 测试

如果现有 sidecar tests 已覆盖 failed entry，可只补充 timeout-specific case。

至少覆盖：

1. timeout error 的 `error_type` 稳定；
2. timeout error 的 `message` 稳定；
3. batch manifest partial failure 中可记录 timeout；
4. LLM Markdown report 可以展示 timeout failed entry；
5. 不改变 sidecar schema；
6. 不改变 Markdown report 结构。

---

### 7.6 回归测试

必须确保已有测试全部通过：

```bash
uv run pytest
```

如果新增或修改了专门测试文件，也请额外运行：

```bash
uv run pytest tests/test_llm_config.py
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_pydanticai_errors.py
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
docs/CI.md
PROJECT_STATE.md
CHANGELOG.md
```

更新重点：

1. 在 `docs/ARCHITECTURE.md` 中说明 PydanticAI runtime timeout 边界；
2. 在 `docs/ARCHITECTURE.md` 中说明 runtime error classification；
3. 在 `docs/DATA_MODELS.md` 中说明 `LLMProviderConfig.timeout_seconds`；
4. 在 `docs/DATA_MODELS.md` 中说明新增或稳定化的 runtime error 类型；
5. 在 `docs/CLI.md` 中说明 `--llm-timeout-seconds` 用法；
6. 在 `docs/CLI.md` 中说明 timeout 对 review / batch 的影响；
7. 在 `docs/CI.md` 中说明 timeout/runtime errors 不影响 deterministic Quality Gate；
8. 在 `PROJECT_STATE.md` 中记录 TASK-0048 已完成后项目状态；
9. 在 `CHANGELOG.md` 中记录本次变更。

---

## 9. 验收标准

本任务完成后应满足：

1. `LLMProviderConfig` 支持 timeout 配置；
2. CLI 支持 `--llm-timeout-seconds`；
3. invalid timeout 会返回清晰错误；
4. pydanticai runtime 可以使用 timeout 配置；
5. timeout error 有稳定错误类型或稳定 error_type；
6. runtime unknown error 映射为稳定 provider error；
7. response validation error 仍是 `LLMResponseValidationError`；
8. secret error 仍是 `LLMProviderSecretError`；
9. config error 仍是 `LLMProviderConfigError`；
10. error message 不泄露 secret、完整 prompt、完整文章内容或 traceback；
11. sidecar JSON schema 不变；
12. LLM sidecar Markdown report 结构不变；
13. deterministic JSON / Markdown report 行为不变；
14. Quality Gate 语义不变；
15. mock provider 行为不变；
16. 不新增 retry；
17. 不新增 rate limit；
18. 不新增 streaming；
19. 不新增 batch 并发；
20. 测试不依赖真实 API key；
21. 测试不发起真实网络；
22. 文档、PROJECT_STATE.md、CHANGELOG.md 已同步更新；
23. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 本任务只做 timeout 与 error classification；
2. 不要顺手做 retry；
3. 不要顺手做 rate limit；
4. 不要顺手做 batch 并发；
5. 不要顺手做 streaming；
6. 不要改变 sidecar schema；
7. 不要改变 report 结构；
8. 不要改变 Quality Gate；
9. 不要把 timeout 当成 Quality Gate failure；
10. 不要把 runtime error 写成 deterministic finding；
11. 不要把 secret value 写入任何输出；
12. 不要把完整 prompt 或完整文章内容写入错误信息；
13. 不要用真实网络测试 timeout；
14. 不要通过 sleep 很久的测试制造不稳定测试；
15. 如果 PydanticAI 当前 API 的 timeout 支持有限，应采用最小可测试实现，并在文档中说明限制；
16. 后续 retry / rate limit / concurrency 应单独放到 TASK-0049 或之后。

---

## 11. 完成后需要运行的命令

```bash
uv run pytest
```

如果涉及专门测试文件，请额外运行：

```bash
uv run pytest tests/test_llm_config.py
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_pydanticai_errors.py
uv run pytest tests/test_llm_provider.py
uv run pytest tests/test_cli.py
```

具体测试文件名以实际仓库为准。

---

