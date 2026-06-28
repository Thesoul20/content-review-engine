# TASK-0052: Add LLM Provider Config File and CLI Overrides

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计相关的 provider interface、mock reviewer、runner、sidecar JSON、sidecar Markdown report、provider configuration boundary、PydanticAI secret resolution、PydanticAI request / response mapping、PydanticAI runtime call、timeout、runtime error classification、真实 provider 使用文档、retry configuration 和 request pacing guardrails。

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
TASK-0048: Add PydanticAI Runtime Timeout and Error Classification
TASK-0049: Add PydanticAI Provider Usage Guide and Manual Verification Fixtures
TASK-0050: Add PydanticAI Provider Retry Configuration
TASK-0051: Add PydanticAI Provider Rate Limit Guardrails
```

当前 LLM provider 已经支持较多 CLI 参数：

```text
--llm-provider
--llm-model
--llm-api-key-env
--llm-base-url
--llm-timeout-seconds
--llm-retry-attempts
--llm-retry-backoff-seconds
--llm-min-request-interval-seconds
```

这些参数在真实 provider 使用时会变得很长。为了提高可复用性，需要支持一个独立的 LLM provider 配置文件，让用户可以把 provider/model/timeout/retry/pacing 等参数保存到 YAML 文件中，然后通过 CLI 引用。

本任务只做 LLM provider 配置文件加载和 CLI override 规则，不改变 provider runtime 行为，不改变 sidecar schema，不改变 Quality Gate。

---

## 2. 任务目标

新增 LLM provider config file 支持。

完成后应满足：

1. review 和 batch 命令都支持 `--llm-config <path>`；
2. LLM provider 配置可以从 YAML 文件加载；
3. CLI 参数可以覆盖 config file 中的同名配置；
4. config file 不保存真实 API key，只保存 env var name；
5. config file 支持当前已有 provider 字段；
6. mock provider 行为不变；
7. pydanticai provider 行为不变；
8. deterministic review 行为不变；
9. sidecar JSON schema 不变；
10. LLM sidecar Markdown report 结构不变；
11. Quality Gate 语义不变；
12. 测试不依赖真实 API key 或真实网络。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 新增 LLM provider config file 数据结构；
2. 新增 YAML config loader；
3. 新增 `--llm-config <path>` CLI 参数；
4. 支持 review 命令读取 LLM config file；
5. 支持 batch 命令读取 LLM config file；
6. 支持 CLI 参数覆盖 config file；
7. 支持 config file validation；
8. 新增 example LLM config file；
9. 更新 LLM provider usage docs；
10. 更新 CLI docs；
11. 更新 CI docs；
12. 更新 architecture / data model docs；
13. 更新 PROJECT_STATE.md 和 CHANGELOG.md；
14. 新增或更新测试。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不新增新的 provider；
2. 不新增 OpenAI / Anthropic direct provider；
3. 不改变 PydanticAI runtime call；
4. 不改变 retry 行为；
5. 不改变 timeout 行为；
6. 不改变 request pacing 行为；
7. 不实现 provider fallback；
8. 不实现多模型 fallback；
9. 不实现 streaming；
10. 不实现 batch concurrency；
11. 不实现 rate limit queue；
12. 不新增 `--fail-on-llm`；
13. 不让 Quality Gate 根据 LLM 结果失败；
14. 不把 LLM findings 合并进主 ReviewResult；
15. 不改变 LLMSidecarResult JSON schema；
16. 不改变 LLM sidecar Markdown report 结构；
17. 不改变 deterministic ReviewResult schema；
18. 不改变 deterministic JSON 输出结构；
19. 不改变 deterministic Markdown report 默认结构；
20. 不改变 batch manifest schema；
21. 不实现 API / MCP / GUI；
22. 不引入 Supabase、用户系统、SaaS、多租户、支付等能力；
23. 不让 tests 依赖真实 API key 或真实网络；
24. 不把真实 API key 写入 config、fixture、docs、sidecar、report、日志或错误信息；
25. 不在 CI 中运行真实 provider 调用；
26. 不重构整个 CLI；
27. 不重构整个 LLM runner；
28. 不重构 provider runtime。

---

## 5. 需要修改的文件

预计包括但不限于：

```text
src/content_review_engine/llm/config.py
src/content_review_engine/cli.py
tests/test_llm_config.py
tests/test_cli.py
docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

建议新增：

```text
src/content_review_engine/llm/config_loader.py
tests/test_llm_config_loader.py
examples/llm/pydanticai/llm-provider.yml
examples/llm/mock/llm-provider.yml
```

如果当前项目已有 config loader 模式，也可以复用现有结构，不强制新增 `config_loader.py`。

---

## 6. 实现要求

### 6.1 LLM provider config file 格式

新增 YAML 格式的 LLM provider config file。

建议格式：

```yaml
provider: pydanticai
model: openai:gpt-4o-mini
api_key_env: OPENAI_API_KEY
base_url: null
timeout_seconds: 30
retry_attempts: 2
retry_backoff_seconds: 1.0
min_request_interval_seconds: 2.0
```

mock provider 示例：

```yaml
provider: mock
model: mock-model
api_key_env: null
base_url: null
timeout_seconds: null
retry_attempts: 0
retry_backoff_seconds: 0.0
min_request_interval_seconds: 0.0
```

要求：

1. 不允许保存真实 API key；
2. 只允许保存 API key env var name；
3. 未知字段应返回清晰 config error；
4. provider 字段必须合法；
5. timeout_seconds 必须符合已有校验；
6. retry_attempts 必须符合已有校验；
7. retry_backoff_seconds 必须符合已有校验；
8. min_request_interval_seconds 必须符合已有校验；
9. base_url 可以为空；
10. model 行为沿用当前 `LLMProviderConfig` 规则；
11. 不新增 secret value 字段；
12. 不新增 provider fallback 字段；
13. 不新增 concurrency / queue / requests_per_minute 字段。

---

### 6.2 新增 CLI 参数

为 review 和 batch 命令新增：

```text
--llm-config <path>
```

要求：

1. 只有启用 `--enable-llm` 时才实际加载并使用；
2. 未启用 `--enable-llm` 时可以解析，但不影响 deterministic review；
3. 文件不存在时返回清晰错误；
4. 文件不是有效 YAML 时返回清晰错误；
5. 文件 schema 无效时返回清晰错误；
6. 错误信息不包含 secret value；
7. 不改变现有 LLM CLI 参数；
8. 不删除现有 LLM CLI 参数；
9. 不改变 `--profile` 的 ReviewProfile 语义；
10. 不把 LLM config file 与 ReviewProfile 混在一起。

---

### 6.3 CLI override 规则

当同时提供 `--llm-config` 和单独 CLI 参数时，CLI 参数应覆盖 config file。

优先级：

```text
explicit CLI args > --llm-config file > LLMProviderConfig defaults
```

例如：

```bash
uv run content-review review article.md \
  --profile profile.yml \
  --enable-llm \
  --llm-config examples/llm/pydanticai/llm-provider.yml \
  --llm-model openai:gpt-4.1-mini
```

最终 model 应为：

```text
openai:gpt-4.1-mini
```

要求覆盖以下字段：

```text
provider
model
api_key_env
base_url
timeout_seconds
retry_attempts
retry_backoff_seconds
min_request_interval_seconds
```

注意：

1. 只有用户显式传入的 CLI 参数才覆盖；
2. CLI 参数未传入时，不应用 parser 默认值覆盖 config file；
3. 需要避免 “默认值把 config file 值覆盖掉” 的 bug；
4. 对 None / 空字符串的处理要清晰；
5. 如果用户显式传入空 base_url，需按当前 CLI 约定处理；
6. 文档必须说明覆盖规则。

---

### 6.4 Config loader 行为

建议新增函数：

```text
load_llm_provider_config(path: Path) -> LLMProviderConfig
```

或：

```text
load_llm_provider_config_file(path: Path) -> LLMProviderConfig
```

要求：

1. 文件不存在时抛 `LLMProviderConfigError`；
2. YAML 解析失败时抛 `LLMProviderConfigError`；
3. YAML 顶层不是 mapping 时抛 `LLMProviderConfigError`；
4. 未知字段时抛 `LLMProviderConfigError`；
5. 字段类型错误时抛 `LLMProviderConfigError`；
6. secret value 字段出现时抛 `LLMProviderConfigError`；
7. 错误信息不包含文件全文；
8. 错误信息不包含 secret；
9. 错误信息稳定，适合测试；
10. 不读取环境变量；
11. 不发起网络请求；
12. 不实例化 provider runtime。

---

### 6.5 Secret safety

LLM config file 只允许保存：

```text
api_key_env: OPENAI_API_KEY
```

不允许保存：

```text
api_key: sk-...
secret: ...
token: ...
password: ...
```

建议对以下字段名进行拒绝：

```text
api_key
secret
token
password
access_token
refresh_token
```

如果出现这些字段，应抛出 `LLMProviderConfigError`，并提示：

```text
LLM provider config files must reference secrets by environment variable name only.
```

要求：

1. 错误信息不回显 secret value；
2. 测试中覆盖 secret-like field；
3. docs 中明确不要把 API key 写进 config；
4. `.env.example` 仍只包含 placeholder；
5. 不改变 secret resolver 逻辑。

---

### 6.6 Examples

新增示例文件：

```text
examples/llm/pydanticai/llm-provider.yml
examples/llm/mock/llm-provider.yml
```

pydanticai 示例不能包含真实 key。

建议内容：

```yaml
provider: pydanticai
model: openai:gpt-4o-mini
api_key_env: OPENAI_API_KEY
base_url: null
timeout_seconds: 30
retry_attempts: 2
retry_backoff_seconds: 1.0
min_request_interval_seconds: 2.0
```

mock 示例：

```yaml
provider: mock
model: mock-model
api_key_env: null
base_url: null
timeout_seconds: null
retry_attempts: 0
retry_backoff_seconds: 0.0
min_request_interval_seconds: 0.0
```

要求：

1. examples 不包含真实 API key；
2. examples 可以被 loader 加载；
3. pydanticai example 适合 docs 手动验证；
4. mock example 适合 CI / docs 示例；
5. examples 不触发真实网络；
6. examples 不要求真实 API key，除非实际使用 pydanticai runtime。

---

### 6.7 ReviewProfile 边界

必须明确 LLM provider config file 与 ReviewProfile 不同。

```text
ReviewProfile:
  - deterministic rules
  - forbidden terms
  - severity settings
  - quality gate related deterministic rule behavior

LLM provider config:
  - provider
  - model
  - api_key_env
  - base_url
  - timeout
  - retry
  - pacing
```

要求：

1. 不把 provider config 写入 ReviewProfile；
2. 不修改 ReviewProfile schema；
3. 不让 ReviewProfile 加载 provider runtime 配置；
4. 不让 provider config 影响 deterministic rule behavior；
5. 文档说明两者边界。

---

### 6.8 Sidecar / report / Quality Gate 行为

本任务不得改变以下结构和行为：

```text
LLMSidecarResult JSON schema
LLM sidecar Markdown report structure
deterministic ReviewResult
deterministic JSON output
deterministic Markdown report
batch manifest schema
Quality Gate
```

要求：

1. 使用 config file 后的 LLM result 与直接 CLI 参数行为一致；
2. sidecar 中 provider/model 应来自最终 merged config；
3. Quality Gate 仍只看 deterministic findings；
4. provider config file 错误不应变成 deterministic finding；
5. provider config file 不应写入 sidecar；
6. secret value 不应写入 sidecar 或 report。

---

## 7. 测试要求

所有测试必须避免真实 API key 和真实网络。

### 7.1 Config loader 测试

新增 `tests/test_llm_config_loader.py`，覆盖：

1. 加载 pydanticai config file 成功；
2. 加载 mock config file 成功；
3. 文件不存在时报 `LLMProviderConfigError`；
4. YAML 无效时报 `LLMProviderConfigError`；
5. YAML 顶层不是 mapping 报错；
6. unknown field 报错；
7. secret-like field 报错；
8. invalid timeout 报错；
9. invalid retry_attempts 报错；
10. invalid retry_backoff_seconds 报错；
11. invalid min_request_interval_seconds 报错；
12. 错误信息不包含 secret value；
13. loader 不读取 env；
14. loader 不发起网络；
15. example config files 可以加载。

---

### 7.2 CLI override 测试

更新 `tests/test_cli.py`，覆盖：

1. review 命令支持 `--llm-config`；
2. batch 命令支持 `--llm-config`；
3. config file 中的 provider/model/api_key_env 被使用；
4. CLI `--llm-model` 覆盖 config file model；
5. CLI `--llm-provider` 覆盖 config file provider；
6. CLI `--llm-api-key-env` 覆盖 config file api_key_env；
7. CLI `--llm-base-url` 覆盖 config file base_url；
8. CLI `--llm-timeout-seconds` 覆盖 config file timeout；
9. CLI `--llm-retry-attempts` 覆盖 config file retry_attempts；
10. CLI `--llm-retry-backoff-seconds` 覆盖 config file retry_backoff_seconds；
11. CLI `--llm-min-request-interval-seconds` 覆盖 config file min interval；
12. parser 默认值不会覆盖 config file；
13. 未启用 `--enable-llm` 时 `--llm-config` 不影响 deterministic review；
14. invalid config file 返回清晰错误；
15. mock config file 可用于 mock sidecar；
16. pydanticai config file 可通过 fake runtime 测试；
17. Quality Gate 不受 config file 影响；
18. CLI stderr / sidecar / report 不包含 secret。

---

### 7.3 Example fixture 测试

新增或更新 docs/example 测试，覆盖：

1. examples/llm/pydanticai/llm-provider.yml 存在；
2. examples/llm/mock/llm-provider.yml 存在；
3. examples 不包含真实 API key；
4. pydanticai example 可以加载；
5. mock example 可以加载；
6. usage docs 引用了真实存在的 example path；
7. docs 不包含明显真实 key 模式。

---

### 7.4 Regression 测试

确保已有测试通过：

```bash
uv run pytest
```

如果新增专门测试文件，请额外运行：

```bash
uv run pytest tests/test_llm_config_loader.py
uv run pytest tests/test_llm_config.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_provider_usage_docs.py
```

具体测试文件名以实际仓库为准。

---

## 8. 文档更新要求

需要更新：

```text
docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

更新重点：

1. `docs/LLM_PROVIDER_USAGE.md` 增加 `--llm-config` 用法；
2. `docs/LLM_PROVIDER_USAGE.md` 增加 pydanticai config file 示例；
3. `docs/LLM_PROVIDER_USAGE.md` 增加 mock config file 示例；
4. `docs/LLM_PROVIDER_USAGE.md` 说明 CLI override 规则；
5. `docs/LLM_PROVIDER_USAGE.md` 说明 secret 只能通过 env var name 引用；
6. `docs/CLI.md` 增加 `--llm-config` 参数说明；
7. `docs/CLI.md` 更新 review / batch 示例；
8. `docs/CI.md` 说明 CI 可使用 mock config file，但不使用真实 provider config 执行真实网络；
9. `docs/ARCHITECTURE.md` 说明 LLM provider config file 属于 provider runtime boundary；
10. `docs/DATA_MODELS.md` 说明 config file 字段和 `LLMProviderConfig` 映射；
11. `PROJECT_STATE.md` 记录 TASK-0052 完成后状态；
12. `CHANGELOG.md` 记录本次变更。

---

## 9. 验收标准

本任务完成后应满足：

1. review 命令支持 `--llm-config`；
2. batch 命令支持 `--llm-config`；
3. LLM provider config file 可以加载为 `LLMProviderConfig`；
4. CLI 显式参数可以覆盖 config file；
5. parser 默认值不会错误覆盖 config file；
6. config file unknown field 会报错；
7. config file secret-like field 会报错；
8. config file 不允许保存真实 API key；
9. pydanticai example config 存在且可加载；
10. mock example config 存在且可加载；
11. 使用 config file 不改变 provider runtime 行为；
12. 使用 config file 不改变 sidecar schema；
13. 使用 config file 不改变 report 结构；
14. 使用 config file 不改变 deterministic review；
15. 使用 config file 不改变 Quality Gate；
16. 不改变 ReviewProfile schema；
17. 测试不依赖真实 API key；
18. 测试不发起真实网络；
19. 文档、PROJECT_STATE.md、CHANGELOG.md 已同步更新；
20. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 本任务只做 LLM provider config file，不做 provider runtime 新能力；
2. 不要把 LLM config 混进 ReviewProfile；
3. 不要改变 ReviewProfile schema；
4. 不要在 config file 中支持真实 API key；
5. 不要让 parser 默认值覆盖 config file 值；
6. 不要改变 provider runtime 行为；
7. 不要改变 sidecar schema；
8. 不要改变 report 结构；
9. 不要改变 Quality Gate；
10. 不要新增 provider fallback；
11. 不要新增 batch concurrency；
12. 不要新增 API / MCP / GUI；
13. 测试不得访问真实网络；
14. 测试不得依赖真实 API key；
15. docs/examples 不得包含真实 secret。

---

## 11. 完成后需要运行的命令

```bash
uv run pytest
```

如果新增专门测试文件，请额外运行：

```bash
uv run pytest tests/test_llm_config_loader.py
uv run pytest tests/test_llm_config.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_provider_usage_docs.py
```

具体测试文件名以实际仓库为准。

---

