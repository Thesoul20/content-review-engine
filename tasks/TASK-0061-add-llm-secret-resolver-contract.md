# TASK-0061: Add LLM Secret Resolver Contract

## 1. 背景

当前项目已经完成确定性内容审计主链路，包括 Markdown 读取、Profile 加载、规则审计、单文件 CLI、批量 CLI、JSON / Markdown 报告输出，以及 Quality Gate / CI 门禁。

LLM 语义审计阶段目前已经完成了以下能力：

1. `LLMReviewRequest`
2. `LLMReviewer` provider interface
3. `MockLLMReviewer`
4. `LLMReviewResult`
5. LLM semantic review runner
6. 单文件 LLM sidecar output
7. batch LLM sidecar output
8. `content-review llm-check` smoke check
9. `PydanticAITestModelReviewer`
10. `create_llm_reviewer()` provider factory
11. `UnsupportedLLMProviderError`
12. `content-review llm-check --provider`
13. 单文件 LLM sidecar `--llm-provider`
14. batch LLM sidecar `--llm-provider`
15. single / batch sidecar provider metadata
16. sidecar envelope schema version `llm-sidecar-result.v2`
17. real LLM provider configuration contract
18. provider name validation boundary
19. reserved real provider boundary

TASK-0060 已经新增了真实 LLM provider 接入前的配置契约和校验边界，明确了：

1. 当前 test providers：`mock`、`pydantic-ai-testmodel`
2. reserved real providers：`openai`、`anthropic`、`gemini`、`deepseek`、`qwen`、`local`
3. unsupported provider 的错误边界
4. reserved real provider 当前不可创建真实 reviewer
5. 当前不读取 `.env`
6. 当前不读取真实 API key
7. 当前不访问外部网络

但是项目仍然缺少一个独立的 secret resolver 边界。后续如果要接入真实 provider，不能让 provider、CLI、config loader 或 factory 到处直接读取环境变量，也不能在错误信息、日志、sidecar metadata、report 中泄露 API key。

本任务的目标是：

> 新增一个最小、独立、可测试的 LLM secret resolver contract，用于未来真实 provider 从环境变量解析 API key，但本任务不实现任何真实 provider 调用。

本任务仍属于真实 provider 接入前的准备任务。

---

## 2. 任务目标

新增 LLM secret resolver contract，使项目能够明确表达：

1. API key 以后通过 `LLMProviderConfig.api_key_env` 指向环境变量名；
2. secret resolver 可以在被显式调用时从环境变量映射中解析 secret；
3. secret resolver 不读取 `.env` 文件；
4. secret resolver 不自动参与 `mock` / `pydantic-ai-testmodel`；
5. secret resolver 不自动让 reserved real provider 可用；
6. 缺少 `api_key_env` 时应有清晰错误；
7. `api_key_env` 指向的环境变量不存在时应有清晰错误；
8. API key 不能为空字符串；
9. 错误信息不得包含 secret value；
10. 文档、测试和错误边界都明确：本任务不接真实 LLM API。

本任务完成后，项目应具备类似以下边界：

```text
LLMProviderConfig(api_key_env="OPENAI_API_KEY")
        ↓
resolve_llm_provider_secret(config, env=os.environ)
        ↓
resolved API key string
```

但这个 resolver 只能作为未来真实 provider 的准备能力，不应被当前 CLI 自动用于真实 provider 调用。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 新增 LLM secret resolver 模块；
2. 新增从环境变量映射中解析 API key 的 helper；
3. 支持通过 `LLMProviderConfig.api_key_env` 解析 secret；
4. 支持测试中传入 fake env mapping；
5. 支持运行时显式使用 `os.environ`；
6. 新增缺少 secret reference 的错误；
7. 新增环境变量缺失的错误；
8. 新增环境变量为空字符串的错误；
9. 新增 secret value redaction / masking helper；
10. 确保错误信息不泄露 secret value；
11. 添加 secret resolver 单元测试；
12. 添加 provider config 回归测试；
13. 添加 factory 回归测试；
14. 添加文档约束测试；
15. 更新 LLM provider 使用文档；
16. 更新数据模型文档；
17. 更新架构文档；
18. 更新 CLI 文档中关于真实 provider / API key 的说明；
19. 更新 `PROJECT_STATE.md`；
20. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许接入真实 OpenAI API；
2. 不允许接入真实 Anthropic API；
3. 不允许接入真实 Gemini API；
4. 不允许接入真实 DeepSeek API；
5. 不允许接入真实 Qwen API；
6. 不允许接入本地模型 API；
7. 不允许新增任何真实 provider class；
8. 不允许让 `create_llm_reviewer("openai")` 成功；
9. 不允许让 `content-review llm-check --provider openai` 成功；
10. 不允许让 single sidecar `--llm-provider openai` 成功；
11. 不允许让 batch sidecar `--llm-provider openai` 成功；
12. 不允许读取 `.env` 文件；
13. 不允许引入 `python-dotenv`；
14. 不允许新增 secret resolver 以外的真实 provider 配置系统；
15. 不允许新增 `--api-key` CLI 参数；
16. 不允许新增 `--llm-api-key-env` CLI 参数；
17. 不允许新增 `--llm-model` CLI 参数；
18. 不允许新增 `--llm-base-url` CLI 参数；
19. 不允许访问外部网络；
20. 不允许把 secret value 写入 sidecar；
21. 不允许把 secret value 写入 ReviewResult；
22. 不允许把 secret value 写入 BatchReviewResult；
23. 不允许把 secret value 写入 Markdown Report；
24. 不允许把 secret value 写入错误消息；
25. 不允许把 secret value 写入文档示例；
26. 不允许修改 `content-review review` 默认行为；
27. 不允许修改 `content-review batch` 默认行为；
28. 不允许修改 `content-review llm-check` 用户可见行为，除非只是保留现有错误语义；
29. 不允许修改 sidecar metadata schema；
30. 不允许把 LLM 结果合并进主 `ReviewResult`；
31. 不允许把 LLM 结果合并进主 `BatchReviewResult`；
32. 不允许修改 Markdown Report；
33. 不允许修改 Quality Gate；
34. 不允许新增 API / MCP / GUI；
35. 不允许引入 LangChain / CrewAI；
36. 不允许引入 OpenAI / Anthropic / Gemini / DeepSeek SDK。

---

## 5. 需要修改的文件

预计新增或修改以下文件：

```text
src/content_review_engine/llm/secrets.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/config.py
src/content_review_engine/llm/__init__.py
tests/test_llm_secret_resolver.py
tests/test_llm_provider_config.py
tests/test_llm_provider_factory.py
tests/test_llm_provider_usage_docs.py
docs/LLM_PROVIDER_USAGE.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
docs/CLI.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前项目已有更合适的命名，例如：

```text
src/content_review_engine/llm/secret_resolver.py
```

可以沿用现有命名风格。

如果现有错误类型已经足够表达 secret resolution error，可以复用现有错误层级，但错误语义必须清晰。

---

## 6. 实现要求

### 6.1 Secret Resolver 模块

建议新增：

```text
src/content_review_engine/llm/secrets.py
```

建议提供 helper：

```python
resolve_llm_api_key(config: LLMProviderConfig, env: Mapping[str, str] | None = None) -> str
```

或更通用命名：

```python
resolve_llm_provider_secret(config: LLMProviderConfig, env: Mapping[str, str] | None = None) -> str
```

推荐行为：

1. 如果 `env` 为 `None`，使用当前进程的 `os.environ`；
2. 如果传入 `env`，只从传入 mapping 读取；
3. 不读取 `.env`；
4. 不读取文件系统；
5. 不访问网络；
6. 不打印 secret value；
7. 不把 secret value 包进 exception message。

测试中必须通过 fake env mapping 或 pytest monkeypatch 使用假值。

---

### 6.2 Secret Reference

resolver 应通过 `LLMProviderConfig.api_key_env` 指定环境变量名。

示例：

```python
config = LLMProviderConfig(
    provider="openai",
    model="gpt-4.1-mini",
    api_key_env="OPENAI_API_KEY",
)
```

resolver 行为：

```python
resolve_llm_provider_secret(config, env={"OPENAI_API_KEY": "fake-test-key"})
# returns "fake-test-key"
```

注意：这里返回的是测试用 fake key，不是真实 key。

本任务不得在任何地方硬编码真实 API key。

---

### 6.3 缺少 api_key_env

如果调用 resolver 时 `config.api_key_env` 为空或 `None`，应抛出清晰错误。

建议新增错误类型：

```python
LLMProviderSecretError
MissingLLMProviderSecretReferenceError
```

错误信息应说明：

```text
LLM provider secret reference is missing: api_key_env is required for secret resolution.
```

错误信息不得包含任何 secret value。

---

### 6.4 环境变量不存在

如果 `config.api_key_env = "OPENAI_API_KEY"`，但是 env mapping 中没有该变量，应抛出清晰错误。

建议错误类型：

```python
MissingLLMProviderSecretError
```

错误信息应包含环境变量名：

```text
LLM provider secret environment variable is not set: OPENAI_API_KEY.
```

可以包含 env var name，因为它不是 secret value。

不得包含 secret value。

---

### 6.5 环境变量为空

如果环境变量存在但值为空字符串，或者 trim 后为空，应抛出清晰错误。

建议错误信息：

```text
LLM provider secret environment variable is empty: OPENAI_API_KEY.
```

不得返回空字符串。

不得把空 secret 视为合法。

---

### 6.6 Secret Redaction

建议新增一个小的 redaction helper：

```python
redact_secret(value: str | None) -> str
```

推荐行为：

```text
None        -> "<missing>"
""          -> "<empty>"
"abc"       -> "***"
"sk-abc..." -> "sk-***"
```

具体规则可以根据项目风格确定。

要求：

1. 不返回完整 secret；
2. 不在错误信息中自动输出完整 secret；
3. 测试覆盖 redaction 行为；
4. 文档说明不要把真实 key 写入日志、sidecar、report。

如果项目认为本任务不需要 redaction helper，也可以不实现，但必须有测试证明 secret value 不会进入错误信息。

---

### 6.7 与 Provider Config Validation 的关系

TASK-0060 已经新增：

```python
validate_llm_provider_name()
validate_llm_provider_config()
```

本任务可以在 `validate_llm_provider_config()` 中补充对 `api_key_env` 字段格式的轻量校验，但不得让 config validation 自动读取环境变量。

推荐边界：

```text
validate_llm_provider_config()
  校验 provider name、字段形状、api_key_env 名称合法性
  不读取 secret value

resolve_llm_provider_secret()
  在未来真实 provider 显式调用时，从 env 解析 secret value
```

也就是说：

1. config validation 不读取 `.env`；
2. config validation 不读取 `os.environ`；
3. secret resolver 被显式调用时才读取 env mapping；
4. 当前 `mock` / `pydantic-ai-testmodel` 不需要 resolver。

---

### 6.8 与 Factory 的关系

`create_llm_reviewer()` 当前仍只允许创建：

```text
mock
pydantic-ai-testmodel
```

本任务不得让：

```python
create_llm_reviewer("openai")
```

成功。

如果 factory 中检测到 reserved real provider，应继续抛出 `LLMProviderNotImplementedError` 或当前等价错误。

secret resolver 只是未来真实 provider 的依赖，不代表真实 provider 已经可创建。

---

### 6.9 与 CLI 的关系

本任务不新增任何 CLI 参数。

以下命令的用户可见行为不能改变：

```bash
content-review llm-check
content-review llm-check --provider mock
content-review llm-check --provider pydantic-ai-testmodel

content-review review input.md --profile profile.yml
content-review review input.md --profile profile.yml --enable-llm --llm-output llm.json --llm-provider mock
content-review review input.md --profile profile.yml --enable-llm --llm-output llm.json --llm-provider pydantic-ai-testmodel

content-review batch input_dir --profile profile.yml
content-review batch input_dir --profile profile.yml --enable-llm --llm-output-dir llm-results --llm-provider mock
content-review batch input_dir --profile profile.yml --enable-llm --llm-output-dir llm-results --llm-provider pydantic-ai-testmodel
```

本任务不新增：

```bash
--api-key
--llm-api-key-env
--llm-model
--llm-base-url
```

---

### 6.10 Secret 不进入输出

必须确保 secret value 不进入：

1. sidecar JSON；
2. sidecar manifest；
3. main `ReviewResult`;
4. main `BatchReviewResult`;
5. JSON report；
6. Markdown report；
7. Quality Gate output；
8. CLI error text；
9. docs examples；
10. tests snapshot。

测试中可以使用 fake key，例如：

```text
fake-openai-key-for-test
```

但测试也应该验证这个 fake value 不出现在错误消息或 sidecar output 中。

---

## 7. 测试要求

需要新增测试文件：

```text
tests/test_llm_secret_resolver.py
```

至少覆盖以下内容。

### 7.1 Resolve secret from fake env mapping

测试：

```python
config = LLMProviderConfig(
    provider="openai",
    model="gpt-test",
    api_key_env="OPENAI_API_KEY",
)

resolve_llm_provider_secret(
    config,
    env={"OPENAI_API_KEY": "fake-openai-key-for-test"},
)
```

应返回 fake key。

### 7.2 Missing api_key_env

当 `api_key_env` 为 `None` 或空字符串时，应抛出清晰错误。

错误信息应包含 `api_key_env`，但不包含任何 secret value。

### 7.3 Missing environment variable

当 `api_key_env = "OPENAI_API_KEY"`，但 env 中不存在该变量时，应抛出清晰错误。

错误信息应包含 `OPENAI_API_KEY`。

### 7.4 Empty environment variable

当 env 中存在：

```python
{"OPENAI_API_KEY": ""}
```

或：

```python
{"OPENAI_API_KEY": "   "}
```

应抛出清晰错误。

不得返回空字符串。

### 7.5 No `.env` loading

测试 resolver 不读取 `.env` 文件。

可以通过构造临时目录中的 `.env` 文件并传入空 env mapping 来验证：resolver 仍然报缺失，而不是读取 `.env`。

### 7.6 No network access

测试 secret resolver 不访问网络。

可以沿用项目现有 no-network 测试方式。

### 7.7 Secret value does not appear in error messages

构造 fake key，触发错误路径，确保 fake secret value 不出现在 exception message 中。

### 7.8 Redaction helper

如果实现 `redact_secret()`，测试：

1. `None`
2. 空字符串
3. 短 secret
4. 长 secret
5. 带常见前缀的 fake key

确保不会返回完整 secret。

### 7.9 Config validation regression

更新：

```text
tests/test_llm_provider_config.py
```

覆盖：

1. `validate_llm_provider_config()` 不读取 env；
2. `validate_llm_provider_config()` 不解析 secret value；
3. test provider 不需要 `api_key_env`；
4. reserved real provider 的 config 可以校验字段形状，但仍不可创建 reviewer。

### 7.10 Factory regression

更新：

```text
tests/test_llm_provider_factory.py
```

覆盖：

1. `create_llm_reviewer("mock")` 仍成功；
2. `create_llm_reviewer("pydantic-ai-testmodel")` 仍成功；
3. `create_llm_reviewer("openai")` 仍失败；
4. factory 不调用 secret resolver；
5. factory 不读取 API key。

### 7.11 CLI regression

更新或保留：

```text
tests/test_cli.py
```

覆盖：

1. CLI provider selection 行为不变；
2. `openai` 仍不可用于 `llm-check` / single sidecar / batch sidecar；
3. CLI 不新增 API key 参数；
4. CLI 错误信息不包含 fake secret value。

### 7.12 Documentation tests

更新：

```text
tests/test_llm_provider_usage_docs.py
```

确保文档明确：

1. secret resolver contract exists；
2. no `.env` loading；
3. no real provider calls；
4. no API key in CLI yet；
5. do not print or persist secret values。

---

## 8. 文档更新要求

需要更新以下文档：

```text
docs/LLM_PROVIDER_USAGE.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
docs/CLI.md
PROJECT_STATE.md
CHANGELOG.md
```

### 8.1 docs/LLM_PROVIDER_USAGE.md

补充：

1. `api_key_env` 的用途；
2. secret resolver 的用途；
3. secret resolver 只在未来真实 provider 显式调用时使用；
4. 当前仍没有真实 provider；
5. 当前 CLI 没有 API key 参数；
6. 当前不读取 `.env`；
7. 不应将 API key 写入 sidecar / report / logs；
8. 示例只能使用 fake key 名称，不得使用真实 key。

### 8.2 docs/DATA_MODELS.md

补充：

1. `LLMProviderConfig.api_key_env` 是 secret reference，不是 secret value；
2. secret value 不属于 `LLMProviderConfig`；
3. secret value 不属于 `LLMReviewResult`；
4. secret value 不属于 sidecar envelope；
5. secret value 不属于 `ReviewResult` / `BatchReviewResult`;
6. `LLMReviewResult` schema 不变；
7. sidecar envelope v2 schema 不变。

### 8.3 docs/ARCHITECTURE.md

补充 secret resolver 边界：

```text
LLMProviderConfig(api_key_env)
        ↓
validate_llm_provider_config()
        ↓
resolve_llm_provider_secret()
        ↓
future real provider only
```

并明确：

1. config validation 不读取 secret；
2. resolver 被显式调用时才读取 env mapping；
3. 当前 test providers 不需要 secret；
4. 当前 real providers 仍未实现；
5. secret 不进入 report / sidecar / main result。

### 8.4 docs/CLI.md

补充或强调：

1. 当前没有 `--api-key`；
2. 当前没有 `--llm-api-key-env`；
3. 当前不能通过 CLI 使用 OpenAI / Anthropic 等真实 provider；
4. 当前 `--llm-provider` 仍只支持 `mock` 和 `pydantic-ai-testmodel`；
5. secret resolver 是内部未来准备能力。

### 8.5 PROJECT_STATE.md

更新当前状态：

```text
TASK-0061 completed:
Added LLM secret resolver contract for future real provider API key resolution without enabling real provider calls.
```

同时明确尚未完成：

```text
No real LLM API provider.
No API key CLI parameter.
No .env loading.
No real provider secret injection into provider runtime.
No external network access.
No LLM result merge into main ReviewResult or BatchReviewResult.
No Markdown report integration.
No API / MCP / GUI integration.
```

### 8.6 CHANGELOG.md

新增 TASK-0061 变更记录。

---

## 9. 验收标准

本任务完成后必须满足：

1. 项目有独立 LLM secret resolver contract；
2. resolver 可通过 fake env mapping 解析 fake API key；
3. resolver 支持 `LLMProviderConfig.api_key_env`；
4. 缺少 `api_key_env` 时错误清晰；
5. env var 缺失时错误清晰；
6. env var 为空时错误清晰；
7. 错误信息不包含 secret value；
8. 不读取 `.env`；
9. 不引入 `python-dotenv`；
10. 不访问外部网络；
11. config validation 不读取 secret；
12. factory 不读取 secret；
13. CLI 不读取 secret；
14. `mock` provider 行为不变；
15. `pydantic-ai-testmodel` provider 行为不变；
16. reserved real provider 仍不可创建；
17. `create_llm_reviewer("openai")` 仍失败；
18. CLI 不新增 API key 参数；
19. CLI provider selection 行为不变；
20. sidecar metadata 行为不变；
21. sidecar envelope v2 schema 不变；
22. `LLMReviewResult` schema 不变；
23. `ReviewResult` schema 不变；
24. `BatchReviewResult` schema 不变；
25. Markdown Report 不受影响；
26. Quality Gate 不受影响；
27. 不新增真实 SDK 依赖；
28. 不新增 API / MCP / GUI；
29. 文档同步更新；
30. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

本任务最容易出现的风险是 Agent 顺手把 secret resolver 接进真实 provider 或 CLI。

必须避免以下问题：

1. 不要实现 OpenAI provider；
2. 不要实现 Anthropic provider；
3. 不要实现 Gemini provider；
4. 不要实现 DeepSeek provider；
5. 不要安装真实 provider SDK；
6. 不要读取 `.env`；
7. 不要新增 `--api-key`；
8. 不要新增 `--llm-api-key-env`；
9. 不要让 CLI 真实调用 secret resolver；
10. 不要让 `openai` provider 成功运行；
11. 不要把 secret value 写入 sidecar；
12. 不要把 secret value 写入 report；
13. 不要把 secret value 写入 error message；
14. 不要改变 existing test provider 行为；
15. 不要修改主结果 schema；
16. 不要修改 sidecar schema；
17. 不要访问外部网络。

本任务的本质是：

```text
真实 provider 接入前的 secret 解析边界。
```

而不是：

```text
真实 provider 接入或真实 API key 使用。
```

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_secret_resolver.py
uv run pytest tests/test_llm_provider_config.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_sidecar.py
uv run pytest tests/test_llm_smoke_check.py
uv run pytest
```

如果项目中存在 lint / format 命令，也可以运行，但不得因此引入大范围无关格式化改动。

---

