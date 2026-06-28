# TASK-0060: Add Real LLM Provider Configuration Contract

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

TASK-0059 已经让 single 和 batch LLM sidecar output 都记录 provider metadata，包括：

1. `llm_provider`
2. `llm_provider_source`

这让当前 mock / testmodel provider 的 sidecar 输出具备了可追踪性。

但是项目仍然没有进入真实 LLM API 接入阶段。后续如果要接入 OpenAI、Anthropic、Gemini、DeepSeek、Qwen、本地模型或其他 provider，需要先明确配置契约：

1. 哪些 provider name 是真实 provider name；
2. 真实 provider 需要哪些配置字段；
3. 哪些字段是必须的；
4. API key / secret 应该如何表示；
5. 当前阶段是否允许读取 `.env`；
6. 当前阶段是否允许真实网络请求；
7. 缺少配置时应该抛出什么错误；
8. 不支持的 provider 与“支持但未实现”的 provider 应如何区分。

本任务的目标是：

> 新增真实 LLM provider 的配置契约、校验边界和文档说明，但不实现任何真实 provider 调用。

本任务是接入真实 LLM API 之前的准备任务。

---

## 2. 任务目标

新增真实 LLM provider config contract，使项目能够明确表达：

1. 当前哪些 provider 是 test provider；
2. 后续哪些 provider name 预留为 real provider；
3. 真实 provider 的配置字段应该如何组织；
4. 缺少 API key / model / base URL 等配置时应该如何报错；
5. 当前阶段真实 provider 仍不可用；
6. 当前阶段不会读取 `.env`；
7. 当前阶段不会访问外部网络；
8. 当前阶段不会要求用户提供真实 API key；
9. 当前阶段不会改变 `review` / `batch` / `llm-check` 的现有行为。

本任务完成后，项目应具备一个清晰的配置契约层，例如：

```text
LLMProviderConfig
        ↓
validate_llm_provider_config(...)
        ↓
supported test provider / reserved real provider / invalid provider
        ↓
clear error boundary
```

本任务不是实现 OpenAI / Anthropic / Gemini / DeepSeek provider。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 梳理现有 `LLMProviderConfig`；
2. 如有必要，新增或调整 LLM provider config helper；
3. 新增 provider config validation 函数；
4. 明确 test provider 与 real provider 的 provider name 边界；
5. 明确 reserved real provider 的状态；
6. 新增真实 provider 尚未实现时的错误类型；
7. 新增缺少必要配置时的错误类型或错误信息；
8. 添加配置校验测试；
9. 添加 provider name 边界测试；
10. 添加文档约束测试；
11. 更新 LLM provider 使用文档；
12. 更新数据模型文档；
13. 更新架构文档；
14. 更新 CLI 文档中关于真实 provider 尚未接入的说明；
15. 更新 `PROJECT_STATE.md`；
16. 更新 `CHANGELOG.md`。

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
8. 不允许让 `create_llm_reviewer("openai")` 返回可调用真实 provider；
9. 不允许读取 `.env`；
10. 不允许读取环境变量中的真实 API key；
11. 不允许新增 secret resolver；
12. 不允许要求用户提供 API key；
13. 不允许访问外部网络；
14. 不允许新增真实 provider CLI 参数；
15. 不允许修改 `content-review review` 默认行为；
16. 不允许修改 `content-review batch` 默认行为；
17. 不允许修改 `content-review llm-check` 用户可见行为；
18. 不允许修改 single sidecar `--llm-provider` 用户可见行为；
19. 不允许修改 batch sidecar `--llm-provider` 用户可见行为；
20. 不允许把 LLM 结果合并进主 `ReviewResult`；
21. 不允许把 LLM 结果合并进主 `BatchReviewResult`；
22. 不允许把 LLM findings 合并进 Markdown report；
23. 不允许修改 Quality Gate 行为；
24. 不允许新增 API / MCP / GUI；
25. 不允许引入 LangChain / CrewAI；
26. 不允许引入 OpenAI / Anthropic / Gemini / DeepSeek SDK；
27. 不允许让测试依赖外部网络或真实模型调用。

---

## 5. 需要修改的文件

预计修改或新增以下文件：

```text
src/content_review_engine/llm/config.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/factory.py
src/content_review_engine/llm/__init__.py
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

如果当前项目中已经存在 `LLMProviderConfig` 所在文件，例如：

```text
src/content_review_engine/llm/models.py
src/content_review_engine/llm/provider.py
```

请沿用现有结构，不要为了本任务大规模搬迁文件。

如果当前项目已经有 `config.py`，请在现有文件中最小修改。

---

## 6. 实现要求

### 6.1 Provider 分类

需要明确区分三类 provider：

```text
test providers
real providers reserved for future implementation
unsupported providers
```

当前 test providers 应包括：

```text
mock
pydantic-ai-testmodel
```

reserved real providers 可以先文档化或常量化，例如：

```text
openai
anthropic
gemini
deepseek
qwen
local
```

是否把 reserved real providers 放进代码常量由当前项目结构决定。

如果放入代码中，必须保证：

```python
create_llm_reviewer("openai")
```

仍然不会创建真实 provider。

它应该抛出明确错误，例如：

```text
Real LLM provider is reserved but not implemented: openai.
```

不要让 reserved real provider 与 unsupported provider 混淆。

---

### 6.2 错误类型

如果当前错误层级允许，建议新增错误类型：

```python
LLMProviderConfigError
RealLLMProviderNotImplementedError
```

推荐继承现有 LLM error hierarchy，例如：

```python
LLMReviewError
```

或当前项目已有的等价基础错误。

错误语义建议如下：

```text
LLMProviderConfigError
  provider 配置字段不完整、不合法或组合冲突。

RealLLMProviderNotImplementedError
  provider name 是未来计划支持的真实 provider，但当前尚未实现。
```

如果不新增错误类型，也必须用现有错误类型返回清晰错误信息。

---

### 6.3 Config Contract

如果当前已有 `LLMProviderConfig`，应在不破坏现有行为的前提下补充配置契约文档和测试。

可以支持或文档化类似字段：

```python
provider: str
model: str | None
api_key_env: str | None
base_url: str | None
timeout_seconds: float | None
```

但本任务不得读取这些字段对应的真实 secret。

这些字段即使存在，也只用于配置校验和未来真实 provider 设计，不用于真实网络调用。

如果当前 `LLMProviderConfig` 已经有不同字段命名，请沿用当前命名，不要强行重命名。

---

### 6.4 Validation Helper

建议新增 helper：

```python
validate_llm_provider_config(config: LLMProviderConfig) -> None
```

或：

```python
class LLMProviderConfigValidator:
    ...
```

该 helper 至少应覆盖：

1. provider name 不能为空；
2. provider name 必须是 test provider、reserved real provider 或现有 config-driven provider；
3. test provider 不需要 API key；
4. reserved real provider 当前不可创建；
5. reserved real provider 如果缺少必要字段，应返回清晰配置错误；
6. unsupported provider 返回明确错误；
7. 不读取 `.env`；
8. 不访问网络。

如果当前项目有更合适的命名或 validation 入口，请沿用现有风格。

---

### 6.5 Factory 行为

本任务可以调整 `create_llm_reviewer()` 对 reserved real provider 的错误信息，但不得让它创建真实 provider。

当前仍只允许创建：

```text
mock
pydantic-ai-testmodel
```

示例：

```python
create_llm_reviewer("mock")
# returns MockLLMReviewer

create_llm_reviewer("pydantic-ai-testmodel")
# returns PydanticAITestModelReviewer

create_llm_reviewer("openai")
# raises RealLLMProviderNotImplementedError or clear equivalent error

create_llm_reviewer("unknown")
# raises UnsupportedLLMProviderError
```

如果当前项目已经明确要求 `openai` 被视作 unsupported provider，也可以保持现有行为，但必须在文档中说明：真实 provider name 还没有进入 factory 支持范围。

不要破坏现有测试 provider 行为。

---

### 6.6 不改变 CLI 用户行为

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

不应新增：

```bash
--api-key
--llm-model
--llm-base-url
--llm-api-key-env
```

这些真实 provider CLI 参数留到后续任务。

---

### 6.7 文档边界

文档必须明确：

1. 当前可运行 provider 仍只有 `mock` 和 `pydantic-ai-testmodel`；
2. 真实 provider 只是配置契约准备；
3. 本任务不代表真实 API 已接入；
4. 不需要 API key；
5. 不读取 `.env`；
6. 不访问外部网络；
7. 主 `ReviewResult` / `BatchReviewResult` 仍不合并 LLM 结果。

---

## 7. 测试要求

需要新增或更新测试，至少覆盖以下内容。

### 7.1 Config validation tests

新增测试文件：

```text
tests/test_llm_provider_config.py
```

测试至少覆盖：

1. `mock` provider config 合法；
2. `pydantic-ai-testmodel` provider config 合法；
3. provider name 为空时报错；
4. unsupported provider 报错；
5. reserved real provider 当前不可创建或明确报错；
6. reserved real provider 错误信息包含 provider name；
7. reserved real provider 错误信息说明尚未实现；
8. config validation 不读取 `.env`；
9. config validation 不访问网络；
10. test provider 不需要 API key。

### 7.2 Factory regression tests

更新：

```text
tests/test_llm_provider_factory.py
```

至少覆盖：

1. `create_llm_reviewer("mock")` 仍可用；
2. `create_llm_reviewer("pydantic-ai-testmodel")` 仍可用；
3. `create_llm_reviewer("openai")` 不会创建真实 provider；
4. `create_llm_reviewer("openai")` 报错清晰；
5. `create_llm_reviewer("unknown")` 仍报 unsupported provider；
6. factory 不读取 API key；
7. factory 不访问网络。

如果当前项目决定不把 `openai` 放进 reserved real provider 常量，则第 3、4 点可以改成断言 `openai` 仍是 unsupported provider，并在文档中说明真实 provider 尚未进入 factory 支持范围。

### 7.3 CLI regression tests

保留或新增测试，确保以下行为不变：

1. `llm-check --provider mock` 仍通过；
2. `llm-check --provider pydantic-ai-testmodel` 仍通过；
3. single sidecar `--llm-provider mock` 仍通过；
4. single sidecar `--llm-provider pydantic-ai-testmodel` 仍通过；
5. batch sidecar `--llm-provider mock` 仍通过；
6. batch sidecar `--llm-provider pydantic-ai-testmodel` 仍通过；
7. review 默认行为不变；
8. batch 默认行为不变。

### 7.4 Documentation tests

更新：

```text
tests/test_llm_provider_usage_docs.py
```

确保文档明确：

1. 当前可运行 provider 只有 `mock` 和 `pydantic-ai-testmodel`；
2. 真实 provider 尚未接入；
3. 不需要 API key；
4. 不读取 `.env`；
5. 不访问外部网络；
6. 主结果不合并 LLM 结果。

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

新增或补充：

1. 当前可运行 provider；
2. test provider 与 real provider 的区别；
3. real provider config contract；
4. reserved real provider 的当前状态；
5. 为什么当前还不读取 API key；
6. 为什么当前还不访问外部网络；
7. 后续真实 provider 接入的预期顺序。

### 8.2 docs/DATA_MODELS.md

说明：

1. `LLMProviderConfig` 当前字段；
2. provider config validation 行为；
3. test provider 配置规则；
4. reserved real provider 配置规则；
5. 本任务不改变 `LLMReviewResult`；
6. 本任务不改变 `ReviewResult`；
7. 本任务不改变 `BatchReviewResult`;
8. 本任务不改变 sidecar envelope v2 schema。

### 8.3 docs/ARCHITECTURE.md

补充真实 provider 接入前的配置边界：

```text
LLMProviderConfig
        ↓
validate_llm_provider_config()
        ↓
create_llm_reviewer()
        ↓
test provider now / real provider later
```

并明确：

1. 当前只有 test provider 可运行；
2. real provider 仍未实现；
3. API key loading 仍未实现；
4. secret resolver 仍未实现；
5. external network access 仍未引入。

### 8.4 docs/CLI.md

补充或强调：

1. 当前 `--llm-provider` 只支持 `mock` 和 `pydantic-ai-testmodel`；
2. 不能使用 `openai` / `anthropic` / `gemini` 等真实 provider；
3. 当前没有 `--api-key` / `--llm-model` / `--llm-base-url` 参数；
4. 真实 provider 接入属于后续任务。

### 8.5 PROJECT_STATE.md

更新当前状态：

```text
TASK-0060 completed:
Added real LLM provider configuration contract and validation boundary without implementing real provider calls.
```

同时明确尚未完成：

```text
No real LLM API provider.
No API key loading.
No .env loading.
No secret resolver.
No external network access.
No LLM result merge into main ReviewResult or BatchReviewResult.
No Markdown report integration.
No API / MCP / GUI integration.
```

### 8.6 CHANGELOG.md

新增 TASK-0060 变更记录。

---

## 9. 验收标准

本任务完成后必须满足：

1. 项目有清晰的 LLM provider config contract；
2. test provider 与 reserved real provider 边界清晰；
3. `mock` provider config 合法；
4. `pydantic-ai-testmodel` provider config 合法；
5. unsupported provider 报错清晰；
6. reserved real provider 当前不会被创建为真实 provider；
7. reserved real provider 错误信息清晰；
8. config validation 不读取 `.env`；
9. config validation 不读取真实 API key；
10. config validation 不访问外部网络；
11. `create_llm_reviewer("mock")` 仍可用；
12. `create_llm_reviewer("pydantic-ai-testmodel")` 仍可用；
13. `create_llm_reviewer("openai")` 不会创建真实 provider；
14. CLI 现有 provider 行为不变；
15. single sidecar provider selection 行为不变；
16. batch sidecar provider selection 行为不变；
17. sidecar metadata 行为不变；
18. `LLMReviewResult` schema 不变；
19. `ReviewResult` schema 不变；
20. `BatchReviewResult` schema 不变；
21. sidecar envelope v2 schema 不被无关修改；
22. Markdown Report 不受影响；
23. Quality Gate 不受影响；
24. 不新增真实 SDK 依赖；
25. 不新增 API / MCP / GUI；
26. 文档同步更新；
27. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

本任务最容易出现的风险是 Agent 顺手开始实现真实 provider。

必须避免以下问题：

1. 不要安装 OpenAI SDK；
2. 不要安装 Anthropic SDK；
3. 不要安装 Gemini SDK；
4. 不要安装 DeepSeek SDK；
5. 不要新增真实 provider class；
6. 不要读取 `.env`；
7. 不要读取 API key；
8. 不要新增 secret resolver；
9. 不要访问外部网络；
10. 不要新增真实 provider CLI 参数；
11. 不要让 `openai` 等 provider 在 CLI 中成功运行；
12. 不要改变 mock / testmodel 现有行为；
13. 不要改变 sidecar metadata；
14. 不要修改主结果 schema；
15. 不要修改 Markdown Report；
16. 不要修改 Quality Gate。

本任务的本质是：

```text
真实 provider 接入前的配置契约与边界设计。
```

而不是：

```text
真实 provider 接入。
```

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_provider_config.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_sidecar.py
uv run pytest tests/test_llm_smoke_check.py
uv run pytest
```

如果项目中没有 `tests/test_llm_provider_config.py`，本任务应新增该测试文件。

如果项目中存在 lint / format 命令，也可以运行，但不得因此引入大范围无关格式化改动。

---
