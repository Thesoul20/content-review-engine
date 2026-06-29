# TASK-0063: Enable Real PydanticAI Provider Construction

## 1. 背景

当前项目已经完成：

```text
TASK-0061: Add LLM Provider Secret Resolver
TASK-0062: Wire LLM Secret Resolver into LLM Check
```

现在项目已经具备：

1. `LLMProviderConfig.api_key_env` 作为 secret reference；
2. `resolve_llm_provider_secret(config, env=None)`；
3. `redact_secret_value()`；
4. `content-review llm-check` 的 config-driven secret preflight；
5. `--llm-api-key-env` 安全传递环境变量名称；
6. `llm-check` 可以输出 redacted secret 状态；
7. provider factory 仍不解析 secret；
8. reserved real providers 仍不可创建；
9. 主审计流程、sidecar metadata、ReviewResult schema 均未改变。

上一任务只完成了 secret preflight，没有让真实 provider 进入可构造状态。

本任务的目标是：在不执行真实外部 LLM API 调用、不接入主 `review` 流程、不改变报告 schema 的前提下，让 `pydanticai` provider 可以通过 provider factory 被构造出来，并继续保持普通测试不依赖真实 API key、真实网络或真实模型服务。

---

## 2. 任务目标

本任务需要完成：

1. 新增或完善真实 `PydanticAI` provider class；
2. 让 provider factory 可以基于 `LLMProviderConfig(provider="pydanticai", ...)` 构造 PydanticAI provider；
3. factory 接收已经解析好的 secret value，但不直接读取环境变量；
4. provider 构造过程不得执行真实 LLM API 调用；
5. 普通测试中不得访问外部网络；
6. 普通测试中不得要求真实 API key；
7. 保持 reserved providers 仍不可创建；
8. 保持 `content-review llm-check` 默认仍只做 preflight / construction check，不做真实 live call；
9. 补充 provider construction、factory、CLI、文档测试；
10. 更新相关文档和项目状态。

完成后，`pydanticai` provider 应该从“reserved / unavailable”进入“可由 factory 构造”的状态，但还不代表它已经接入主内容审计流程。

---

## 3. 本任务允许做什么

本任务允许：

1. 新增或完善 PydanticAI provider 实现文件；
2. 修改 provider factory，使其支持 `provider="pydanticai"`；
3. 修改 provider config 或 factory 参数，以便传入已解析 secret；
4. 修改 `llm/smoke_check.py`，让 `llm-check` 可以验证 PydanticAI provider construction；
5. 修改 `llm/__init__.py`，导出必要类型；
6. 增加 PydanticAI provider construction 测试；
7. 增加 factory 对 pydanticai provider 的测试；
8. 增加 CLI `llm-check` 对 pydanticai construction 的测试；
9. 使用 PydanticAI 官方测试模型、fake model、monkeypatch 或 stub 来保证测试稳定；
10. 更新 `docs/LLM_PROVIDER_USAGE.md`；
11. 更新 `docs/CLI.md`；
12. 更新 `docs/ARCHITECTURE.md`；
13. 更新 `docs/DATA_MODELS.md`；
14. 更新 `PROJECT_STATE.md`；
15. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许：

1. 不允许在普通测试中调用真实 LLM API；
2. 不允许在普通测试中访问外部网络；
3. 不允许要求 CI 或开发者本机存在真实 API key；
4. 不允许新增 plaintext API key CLI 参数；
5. 不允许输出完整 secret value；
6. 不允许读取 `.env` 文件；
7. 不允许让 provider factory 直接读取 `os.environ`；
8. 不允许让 `openai`、`anthropic`、`gemini`、`deepseek`、`qwen`、`local` 等 reserved providers 变成可创建；
9. 不允许实现 `--live` 或真实 runtime smoke call；
10. 不允许把 LLM 审计接入 `content-review review` 主流程；
11. 不允许把 LLM 审计接入 `content-review batch` 主流程；
12. 不允许修改 `ReviewResult`、`BatchReviewResult` 或 `LLMReviewResult` schema；
13. 不允许修改 sidecar metadata；
14. 不允许修改 deterministic review engine 行为；
15. 不允许新增 API、MCP、Skill、GUI、Supabase、用户系统或商业化能力；
16. 不允许引入 LangChain、CrewAI 或其他大型框架。

---

## 5. 需要修改的文件

预计会修改或新增以下文件：

```text
src/content_review_engine/llm/pydanticai_provider.py
src/content_review_engine/llm/provider_factory.py
src/content_review_engine/llm/provider_config.py
src/content_review_engine/llm/smoke_check.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/__init__.py

tests/test_llm_pydanticai_provider.py
tests/test_llm_provider_factory.py
tests/test_llm_smoke_check.py
tests/test_cli.py
tests/test_llm_provider_usage_docs.py

docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前仓库中已有 PydanticAI provider 文件或测试文件，应优先复用现有结构，不要为了本任务大规模重命名或移动文件。

---

## 6. 实现要求

### 6.1 provider class 要求

需要新增或完善一个 PydanticAI provider class。

命名可以遵守当前项目已有风格，例如：

```python
PydanticAILLMReviewer
```

或：

```python
PydanticAIReviewer
```

具体名称以当前代码已有命名为准。

该 provider 必须实现现有的：

```python
LLMReviewer
```

provider interface。

provider construction 阶段允许保存：

1. provider config；
2. model name；
3. 已解析 secret；
4. PydanticAI agent / model wrapper；
5. 其他必要的静态配置。

但是 construction 阶段不允许：

1. 调用真实 LLM；
2. 访问网络；
3. 从环境变量读取 secret；
4. 输出完整 secret；
5. 修改全局环境。

---

### 6.2 factory 要求

provider factory 应支持：

```python
provider="pydanticai"
```

并返回 PydanticAI provider instance。

factory 的职责是：

```text
输入 provider config + 已解析 secret
        ↓
构造 provider instance
        ↓
返回 LLMReviewer
```

factory 不允许：

1. 读取 `os.environ`；
2. 调用 `resolve_llm_provider_secret()`；
3. 读取 `.env`；
4. 调用真实 LLM；
5. 泄露 secret。

如果当前 factory 还没有参数可以接收已解析 secret，可以新增显式参数，例如：

```python
create_llm_reviewer(config, secret=None)
```

或使用当前项目已有的等价设计。

但要注意：不要把 plaintext secret 写入 `LLMProviderConfig` 的持久化字段中。

---

### 6.3 secret 传递要求

`TASK-0061` 和 `TASK-0062` 已经明确：

```text
LLMProviderConfig.api_key_env 是 secret reference
secret value 由 resolver 解析
factory 不解析 secret
```

本任务必须保持这个边界。

推荐链路：

```text
LLMProviderConfig
  ↓
resolve_llm_provider_secret(config, env=None)
  ↓
secret value
  ↓
create_llm_reviewer(config, secret=secret_value)
  ↓
PydanticAI provider instance
```

secret value 只允许保存在内存对象中，不得写入文档、日志、异常、JSON 输出或 report schema。

---

### 6.4 smoke check 要求

`content-review llm-check` 当前已经可以完成 secret preflight。

本任务可以让 `llm-check` 进一步验证：

```text
secret preflight passed
        ↓
factory can construct pydanticai provider
        ↓
construction check passed
```

成功输出可以包含类似信息：

```text
LLM check passed

Provider: pydanticai
Model: gpt-4.1-mini
API key env: OPENAI_API_KEY
API key: sk-...cdef
Secret: resolved
Provider construction: ok
Live call: not run
```

如果是不需要 secret 的 test mode，可以输出：

```text
Secret: not required
Provider construction: ok
Live call: not run
```

注意：

1. 本任务不实现真实 live call；
2. 不要加入 `--live` 行为；
3. 如果已有 `llm-check` 输出风格不同，应保持当前风格一致；
4. 输出必须稳定可测试；
5. 输出不得包含完整 secret。

---

### 6.5 PydanticAI 测试要求

普通测试必须使用以下方式之一：

1. PydanticAI TestModel；
2. fake model；
3. monkeypatch；
4. stub provider dependency；
5. 项目中已有的测试模型封装。

不允许普通测试依赖：

1. 真实 OpenAI key；
2. 真实 Anthropic key；
3. 真实 Gemini key；
4. 真实 DeepSeek key；
5. 真实 Qwen key；
6. 外部网络；
7. 开发者本机环境变量。

如果 PydanticAI 的 API 版本存在差异，应优先以当前项目 lockfile / installed dependency 为准，不要为了本任务升级依赖，除非当前测试无法通过且有明确必要。

---

### 6.6 reserved provider 要求

本任务只允许打开：

```text
pydanticai
```

不允许打开：

```text
openai
anthropic
gemini
deepseek
qwen
local
```

这些 provider 如果当前是 reserved / unavailable 状态，本任务后仍应保持不可创建。

需要增加或保留测试证明：

```text
openai / anthropic / gemini / deepseek / qwen / local
```

仍然不可创建。

---

### 6.7 错误处理要求

需要提供稳定错误行为：

1. PydanticAI dependency 不可用时，应返回清晰错误；
2. provider construction 失败时，应返回 provider construction error；
3. error message 不得包含 secret；
4. CLI 不应输出未捕获 traceback；
5. factory error 类型应与现有 LLM error hierarchy 兼容；
6. 文档中应说明 construction check 不等于 live API check。

如果需要新增错误类型，可以新增类似：

```python
LLMProviderConstructionError
```

或使用当前 error hierarchy 中已有合适类型。

---

## 7. 测试要求

### 7.1 PydanticAI provider 测试

更新或新增：

```text
tests/test_llm_pydanticai_provider.py
```

覆盖：

1. PydanticAI provider 可以被构造；
2. construction 不访问网络；
3. construction 不读取环境变量；
4. construction 不泄露 secret；
5. provider 实现 `LLMReviewer` interface；
6. provider 保存 model 配置；
7. provider 可以使用测试模型或 fake model 初始化；
8. dependency 不可用或构造失败时返回稳定错误。

---

### 7.2 provider factory 测试

更新：

```text
tests/test_llm_provider_factory.py
```

覆盖：

1. `provider="pydanticai"` 可以创建 provider；
2. factory 接收已解析 secret；
3. factory 不读取 `os.environ`；
4. factory 不调用 secret resolver；
5. factory 不泄露 secret；
6. reserved providers 仍不可创建；
7. unknown provider 仍返回稳定错误。

---

### 7.3 smoke check 测试

更新：

```text
tests/test_llm_smoke_check.py
```

覆盖：

1. secret preflight 成功后可以执行 provider construction check；
2. PydanticAI provider construction 成功时输出 `Provider construction: ok` 或等价文案；
3. live call 明确显示未执行；
4. provider construction failure 时返回稳定失败；
5. full secret 不出现在 rendered output；
6. reserved provider 仍不可创建；
7. missing / empty secret 行为保持 TASK-0062 结果不变。

---

### 7.4 CLI 测试

更新：

```text
tests/test_cli.py
```

覆盖：

1. `content-review llm-check --provider pydanticai ...` 可以通过 construction check；
2. 输出包含 provider、model、secret 状态、provider construction 状态；
3. 输出说明 live call 未执行；
4. stdout / stderr 不包含完整 secret；
5. missing env var 仍失败；
6. empty env var 仍失败；
7. plaintext `--api-key` 参数仍不存在；
8. reserved provider 行为保持稳定。

---

### 7.5 文档测试

更新：

```text
tests/test_llm_provider_usage_docs.py
```

确保文档中包含：

1. PydanticAI provider construction check；
2. `llm-check` 不执行 live API call；
3. secret 只通过 env reference；
4. redacted secret 示例；
5. reserved provider 边界说明。

---

## 8. 文档更新要求

### 8.1 `docs/LLM_PROVIDER_USAGE.md`

补充：

1. PydanticAI provider 当前状态；
2. 如何通过 `llm-check` 检查 PydanticAI provider construction；
3. `--llm-api-key-env` 用法；
4. redacted secret 输出；
5. construction check 与 live call 的区别；
6. 普通测试不需要真实 API key；
7. 本任务仍不接入主 review 流程；
8. reserved providers 仍不可用。

---

### 8.2 `docs/CLI.md`

补充或更新：

1. `content-review llm-check` 的 PydanticAI construction check 行为；
2. 成功输出示例；
3. 失败输出示例；
4. exit code 说明；
5. `Live call: not run` 或等价说明；
6. 不支持 plaintext API key 的说明。

---

### 8.3 `docs/ARCHITECTURE.md`

补充：

1. PydanticAI provider 在 LLM provider layer 中的位置；
2. secret resolver、smoke check、factory、provider class 的职责边界；
3. construction check 不等于 live runtime check；
4. factory 不解析 secret；
5. provider construction 不访问外网；
6. 当前仍未接入主 review / batch 流程。

---

### 8.4 `docs/DATA_MODELS.md`

补充或更新：

1. `LLMProviderConfig` 仍只保存 secret reference；
2. secret value 不进入 canonical data model；
3. PydanticAI provider construction 不改变 `LLMReviewResult`；
4. smoke check result 属于内部检查结果，不改变 review schema。

---

### 8.5 `PROJECT_STATE.md`

更新：

1. 标记 `TASK-0063` 完成后新增的 PydanticAI provider construction 能力；
2. 说明当前 `llm-check` 可做 secret preflight + provider construction check；
3. 说明真实 live API check、主 review 接入、report 合并仍是后续任务。

---

### 8.6 `CHANGELOG.md`

新增 `TASK-0063` 记录。

---

## 9. 验收标准

本任务完成后应满足：

1. `provider="pydanticai"` 可以通过 factory 创建 provider；
2. factory 不读取环境变量；
3. factory 不调用 secret resolver；
4. secret value 只通过显式参数传入；
5. provider construction 不访问网络；
6. provider construction 不调用真实 LLM API；
7. `content-review llm-check` 可以显示 PydanticAI provider construction check 结果；
8. `llm-check` 明确显示 live call 未执行；
9. stdout / stderr / errors 不泄露完整 secret；
10. plaintext `--api-key` 参数仍不存在；
11. reserved providers 仍不可创建；
12. `ReviewResult` / `BatchReviewResult` / `LLMReviewResult` schema 不变；
13. sidecar metadata 不变；
14. deterministic review 行为不变；
15. 文档已同步；
16. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 不要把 provider construction 误做成 live API call。
2. 不要让普通测试依赖真实 API key 或真实网络。
3. 不要在 factory 中读取环境变量。
4. 不要把 secret value 写入 `LLMProviderConfig`。
5. 不要让 reserved providers 顺手变成可用。
6. 不要修改主审计 schema。
7. 不要把 PydanticAI provider 接入 `review` 或 `batch` 主流程。
8. 如果 PydanticAI API 使用方式与预期不一致，应以当前项目依赖版本为准，并用测试模型保持测试稳定。
9. 如果发现现有 `pydantic_ai` DeprecationWarning，不要在本任务中做大规模依赖升级；可以只记录为后续维护项。

---

## 11. 完成后需要运行的命令

可以先运行局部测试：

```bash
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_smoke_check.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_provider_usage_docs.py
```

最后必须运行全量测试：

```bash
uv run pytest
```

---
