# TASK-0045: Add PydanticAI Provider Dependency and Secret Resolution

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计相关的 provider interface、mock reviewer、runner、sidecar JSON、sidecar Markdown report 和 provider configuration boundary。

已完成任务包括：

```text
TASK-0040: Add Batch LLM Sidecar Output
TASK-0041: Add LLM Sidecar Summary and Error Handling
TASK-0042: Add LLM Sidecar Markdown Report
TASK-0043: Add Real LLM Provider Configuration Boundary
TASK-0044: Normalize PydanticAI Provider Adapter Boundary
```

当前 provider 状态是：

```text
provider="mock"
  -> 当前唯一可运行 provider。

provider="pydanticai"
  -> 名称已识别，但当前仍返回 LLMProviderNotImplementedError。

unknown provider
  -> 返回 LLMProviderConfigError。
```

TASK-0044 已经把旧的 PydanticAI adapter 降级为 explicit skeleton，并移除了历史遗留的真实 PydanticAI SDK 依赖，使当前边界保持一致。

下一步需要为真实 PydanticAI provider 接入做准备，但仍然不应该一次性实现真实 LLM review 调用。

因此，本任务只做两件事：

1. 重新以明确、受控、可测试的方式引入 PydanticAI provider 所需依赖；
2. 建立 secret resolution 边界，用于从 `api_key_env` 中安全解析 API key 是否存在和取值。

本任务不实现真实 PydanticAI review 逻辑，不发起真实网络请求，不调用真实 LLM API。

本任务是后续 TASK-0046 正式实现 PydanticAI provider review 逻辑的前置任务。

---

## 2. 任务目标

实现 PydanticAI provider 的依赖和 secret resolution 边界。

完成后应满足：

1. 项目以明确方式重新引入 PydanticAI provider 所需依赖；
2. PydanticAI adapter skeleton 可以安全 import 依赖，但仍不执行真实 review；
3. 新增 secret resolution 逻辑，用于根据 `LLMProviderConfig.api_key_env` 读取环境变量；
4. secret resolution 不应泄露 API key 值；
5. 缺失 API key 时返回清晰、结构化、可测试的错误；
6. provider factory 中 `pydanticai` 仍然不应变成完整可运行 review provider；
7. 不发起真实网络请求；
8. 不调用真实 LLM API；
9. 不改变 sidecar JSON、sidecar Markdown report、deterministic review 和 Quality Gate 行为；
10. 为后续真实 provider 实现留下清晰入口。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 在 `pyproject.toml` 中重新添加 PydanticAI provider 所需依赖；
2. 刷新 `uv.lock`；
3. 新增或更新 PydanticAI provider skeleton，使其可以作为 future real provider 的明确入口；
4. 新增 secret resolution 模块或函数；
5. 根据 `LLMProviderConfig.api_key_env` 读取环境变量；
6. 在 secret 缺失时返回结构化错误；
7. 确保错误信息不包含 API key 值；
8. 新增或更新 LLM secret 相关错误类型；
9. 更新 PydanticAI skeleton 测试；
10. 更新 provider factory 测试；
11. 更新 CLI 测试；
12. 更新相关文档；
13. 更新 PROJECT_STATE.md 和 CHANGELOG.md。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不实现真实 PydanticAI review 逻辑；
2. 不调用真实 LLM API；
3. 不发起真实网络请求；
4. 不在测试中依赖真实 API key；
5. 不把 API key 值写入 config、sidecar、report、日志或错误信息；
6. 不实现 prompt template；
7. 不实现 response parsing；
8. 不实现 retry / timeout / rate limit；
9. 不把 PydanticAI provider 接入为完整可运行 provider；
10. 不把 LLM findings 合并进主 ReviewResult；
11. 不改变 LLMSidecarResult JSON schema；
12. 不改变 LLM sidecar Markdown report 结构；
13. 不改变 deterministic review JSON schema；
14. 不改变 deterministic Markdown report 结构；
15. 不让 Quality Gate 根据 LLM 结果失败；
16. 不实现 API / MCP / GUI；
17. 不引入 Supabase、用户系统、SaaS、多租户、支付等能力；
18. 不重构整个 LLM runner；
19. 不重构整个 CLI；
20. 不新增 OpenAI / Anthropic 官方 SDK 的直接 provider 实现。

---

## 5. 需要修改的文件

预计包括但不限于：

```text
pyproject.toml
uv.lock
src/content_review_engine/llm/config.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/factory.py
src/content_review_engine/llm/pydanticai.py
src/content_review_engine/llm/__init__.py
tests/test_llm_config.py
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

如果更适合项目结构，也可以新增：

```text
src/content_review_engine/llm/secrets.py
tests/test_llm_secrets.py
```

是否新增单独 `secrets.py` 由实际实现复杂度决定。若 secret resolution 逻辑较短，可以放在 `config.py`；若后续会继续扩展，建议单独放在 `llm/secrets.py`。

---

## 6. 实现要求

### 6.1 依赖引入

本任务需要以明确方式重新引入 PydanticAI provider 所需依赖。

建议使用：

```text
pydantic-ai-slim[openai]
```

或者项目当前更适合的 PydanticAI 轻量依赖形式。

要求：

1. 只引入 PydanticAI provider 后续实现所需的最小依赖；
2. 不额外引入 OpenAI / Anthropic 直接 SDK provider；
3. 不引入 LangChain / CrewAI 等大型框架；
4. 不新增不必要依赖；
5. 更新 `uv.lock`；
6. 文档说明该依赖只是为 future PydanticAI provider 准备；
7. 本任务不使用该依赖发起真实调用。

---

### 6.2 Secret resolution 边界

新增 secret resolution 逻辑。

建议接口类似：

```text
resolve_api_key(config: LLMProviderConfig) -> str
```

或：

```text
resolve_llm_secret(config: LLMProviderConfig) -> ResolvedLLMSecret
```

推荐更安全的结构：

```text
ResolvedLLMSecret
  api_key: str
  api_key_env: str
```

但必须注意：

1. `repr(ResolvedLLMSecret)` 不应显示 `api_key` 值；
2. 序列化时不应包含 `api_key` 值；
3. 错误信息不应包含 `api_key` 值；
4. 测试中不能把真实 key 写入 fixture；
5. 可以使用测试环境变量，例如 `CONTENT_REVIEW_TEST_LLM_API_KEY`；
6. 缺失环境变量时应抛出结构化错误；
7. 空字符串环境变量应视为 missing 或 invalid；
8. 只保存 env var name 是可以展示的；
9. env var value 不允许进入 sidecar 或 report。

---

### 6.3 新增错误类型

可以新增或复用错误类型：

```text
LLMProviderConfigError
LLMProviderNotImplementedError
LLMProviderSecretError
```

建议新增：

```text
LLMProviderSecretError
```

用于表达：

```text
api_key_env 未设置
api_key_env 指向的环境变量不存在
api_key_env 指向的环境变量为空
secret resolution 失败
```

错误信息示例：

```text
LLM API key environment variable 'OPENAI_API_KEY' is not set.
```

不要出现：

```text
OPENAI_API_KEY=sk-...
```

也不要输出任何 secret value。

---

### 6.4 PydanticAI skeleton 行为

`src/content_review_engine/llm/pydanticai.py` 仍然应该是 skeleton，不实现真实 review。

本任务允许它：

1. import PydanticAI 相关依赖，前提是不会发起网络请求；
2. 保存 `LLMProviderConfig`；
3. 保存或接收 secret resolver；
4. 校验 secret 是否存在；
5. 明确抛出 `LLMProviderNotImplementedError`，说明真实 review 尚未实现。

本任务不允许它：

1. 调用真实 model；
2. 创建会立刻发起网络请求的 client；
3. 执行 prompt；
4. parse LLM response；
5. 生成真实 LLMReviewResult；
6. fallback 到 mock。

建议行为：

```text
PydanticAIReviewer.review(...)
  -> 先不执行真实 review
  -> raise LLMProviderNotImplementedError(
       "Provider 'pydanticai' dependency and secret boundary is available, but review is not implemented yet."
     )
```

如果实现中需要先验证 secret，应确保测试覆盖：

```text
missing secret -> LLMProviderSecretError
present secret -> still LLMProviderNotImplementedError
```

---

### 6.5 Provider factory 行为

本任务完成后，provider factory 行为可以演进为：

```text
provider="mock"
  -> 返回 MockLLMReviewer

provider="pydanticai"
  -> 可以构造 PydanticAIReviewer skeleton
  -> 但 review 调用仍抛 LLMProviderNotImplementedError
  -> 缺失 secret 时抛 LLMProviderSecretError 或在创建阶段抛出清晰错误

unknown provider
  -> 抛 LLMProviderConfigError
```

关键边界：

1. `pydanticai` 不能 fallback 到 mock；
2. `pydanticai` 不能执行真实 review；
3. `pydanticai` 可以从 “factory 直接 not implemented” 过渡为 “factory 创建 skeleton reviewer，但 reviewer review not implemented”；
4. 如果采用这个过渡方式，必须更新文档和测试；
5. CLI 用户仍然不能得到真实 LLM review 结果。

---

### 6.6 CLI 行为

CLI 参数沿用 TASK-0043：

```text
--llm-provider
--llm-model
--llm-api-key-env
--llm-base-url
```

本任务要求：

1. `--enable-llm --llm-provider mock` 继续正常；
2. `--enable-llm --llm-provider pydanticai` 不应执行真实 review；
3. 如果缺少 `--llm-api-key-env` 或 env var 不存在，应返回清晰 secret error；
4. 如果 env var 存在，仍应返回 clear not implemented error；
5. 错误信息不包含 API key value；
6. 未启用 `--enable-llm` 时，provider 参数不影响 deterministic review；
7. Quality Gate 不受 provider secret resolution 影响；
8. 不新增 `--fail-on-llm`；
9. 不改变 `--llm-output`、`--llm-output-dir`、`--llm-markdown-output` 的既有语义。

注意：

如果当前 CLI 对 provider 初始化错误采用直接退出行为，可以保持该行为，但要保证错误文案清晰、可测试，并且不被误认为 deterministic Quality Gate failure。

---

### 6.7 Sidecar / report 行为

本任务不应改变 sidecar 和 report 结构。

要求：

1. mock provider 下 sidecar JSON 行为不变；
2. mock provider 下 sidecar Markdown report 行为不变；
3. pydanticai provider 因 secret error 或 not implemented error 失败时，可按现有 LLM failed sidecar 机制记录；
4. 不修改 LLMSidecarSummary 字段；
5. 不修改 LLMSidecarFile 字段；
6. 不修改 LLM sidecar Markdown report 结构；
7. 不把 secret value 写入 sidecar JSON；
8. 不把 secret value 写入 Markdown report。

---

## 7. 测试要求

必须新增或更新测试，覆盖以下情况。

### 7.1 Secret resolution 测试

新增或更新测试，覆盖：

1. `api_key_env` 存在且 env var 存在时可以解析；
2. `api_key_env` 缺失时返回 `LLMProviderSecretError`；
3. env var 不存在时返回 `LLMProviderSecretError`；
4. env var 为空字符串时返回 `LLMProviderSecretError`；
5. 错误信息不包含 secret value；
6. `repr` 不泄露 secret；
7. serialization 不泄露 secret。

建议新增：

```text
tests/test_llm_secrets.py
```

如果实现放在 `config.py`，也可以放在：

```text
tests/test_llm_config.py
```

---

### 7.2 PydanticAI skeleton 测试

更新 `tests/test_llm_pydanticai_provider.py`，覆盖：

1. skeleton 可以导入；
2. skeleton 不发起网络请求；
3. skeleton 不 fallback 到 mock；
4. 缺失 secret 时返回 secret error；
5. secret 存在时仍返回 not implemented error；
6. skeleton 错误信息不泄露 API key；
7. skeleton 保存的是 config / env var name，而不是 secret value。

---

### 7.3 Provider factory 测试

更新 `tests/test_llm_provider_factory.py`，覆盖：

1. `provider="mock"` 仍返回 `MockLLMReviewer`；
2. `provider="pydanticai"` 的 factory 行为符合最终设计；
3. 如果 factory 创建 skeleton，则返回 `PydanticAIReviewer` skeleton；
4. 如果 secret 缺失在 factory 阶段报错，则断言 `LLMProviderSecretError`；
5. unknown provider 仍返回 `LLMProviderConfigError`;
6. pydanticai 不 fallback 到 mock；
7. factory 不发起网络请求；
8. factory 不泄露 secret。

---

### 7.4 CLI 测试

更新 CLI 测试，覆盖：

1. `--enable-llm --llm-provider mock` 仍成功；
2. `--enable-llm --llm-provider pydanticai` 缺少 env 时返回 secret error；
3. `--enable-llm --llm-provider pydanticai --llm-api-key-env TEST_KEY` 且 env 不存在时返回 secret error；
4. env 存在时，仍返回 not implemented error；
5. stderr / sidecar / report 不包含 secret value；
6. 未启用 `--enable-llm` 时 provider 参数不影响 deterministic review；
7. Quality Gate 不受 provider secret resolution 影响。

---

### 7.5 回归测试

必须确保已有测试全部通过：

```bash
uv run pytest
```

如果涉及专门测试文件，也请额外运行：

```bash
uv run pytest tests/test_llm_secrets.py
uv run pytest tests/test_llm_config.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_pydanticai_provider.py
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

1. 在 `docs/ARCHITECTURE.md` 中说明 PydanticAI provider dependency 已引入，但真实 review 仍未实现；
2. 在 `docs/ARCHITECTURE.md` 中说明 secret resolution boundary；
3. 在 `docs/DATA_MODELS.md` 中说明 `LLMProviderConfig.api_key_env` 和 secret resolution 结构；
4. 在 `docs/DATA_MODELS.md` 中说明 secret value 不进入 config serialization / sidecar / report；
5. 在 `docs/CLI.md` 中说明 `--llm-api-key-env` 的行为；
6. 在 `docs/CLI.md` 中说明 `pydanticai` 当前仍不能执行真实 review；
7. 在 `docs/CI.md` 中说明 provider secret resolution 不影响 deterministic Quality Gate；
8. 在 `PROJECT_STATE.md` 中记录 TASK-0045 已完成后项目状态；
9. 在 `CHANGELOG.md` 中记录本次变更。

---

## 9. 验收标准

本任务完成后应满足：

1. PydanticAI provider 所需依赖已明确加入项目；
2. `uv.lock` 已同步更新；
3. 存在 secret resolution 边界；
4. secret resolution 可以读取 env var value；
5. secret resolution 不泄露 secret value；
6. 缺失 secret 返回结构化错误；
7. PydanticAI skeleton 可以作为 future provider 入口；
8. PydanticAI skeleton 仍不执行真实 review；
9. PydanticAI skeleton 不发起网络请求；
10. PydanticAI skeleton 不 fallback 到 mock；
11. mock provider 现有行为不变；
12. unknown provider 现有行为不变；
13. sidecar JSON schema 不变；
14. sidecar Markdown report 结构不变；
15. deterministic review JSON / Markdown report 行为不变；
16. Quality Gate 语义不变；
17. 不实现 prompt template；
18. 不实现 response parsing；
19. 不实现 retry / timeout / rate limit；
20. 新增或更新测试通过；
21. 文档、PROJECT_STATE.md、CHANGELOG.md 已同步更新；
22. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 本任务只是 dependency + secret boundary，不是真实 provider review；
2. 不要在本任务中生成真实 LLM findings；
3. 不要把 PydanticAI provider 做成完整可运行 provider；
4. 不要把 secret value 存入 config、sidecar、report、日志、错误信息；
5. 不要让 tests 依赖真实用户环境变量；
6. 测试必须使用 monkeypatch / 临时 env；
7. 不要新增 OpenAI / Anthropic direct provider；
8. 不要新增 LangChain / CrewAI；
9. 不要改 sidecar schema；
10. 不要改 Quality Gate；
11. 不要 fallback 到 mock；
12. 不要过度重构；
13. 依赖变更必须在 commit message 中明确说明；
14. 后续真实 review 应单独放到 TASK-0046。

---

## 11. 完成后需要运行的命令

```bash
uv run pytest
```

如果涉及专门测试文件，请额外运行：

```bash
uv run pytest tests/test_llm_secrets.py
uv run pytest tests/test_llm_config.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_cli.py
```

具体测试文件名以实际仓库为准。

---

