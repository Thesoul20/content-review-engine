# TASK-0062: Wire LLM Secret Resolver into LLM Check

## 1. 背景

当前项目已经完成 `TASK-0061: Add LLM Provider Secret Resolver`。

目前已经具备：

1. `LLMProviderConfig.api_key_env` 作为 secret reference；
2. `resolve_llm_provider_secret(config, env=None) -> str`；
3. `redact_secret_value()`；
4. 兼容包装 `resolve_llm_api_key`；
5. dedicated secret resolver errors：

   * `MissingLLMProviderSecretReferenceError`
   * `MissingLLMProviderSecretEnvironmentVariableError`
   * `EmptyLLMProviderSecretEnvironmentVariableError`
6. 文档已明确：

   * resolver 不读取 `.env`；
   * resolver 不访问外部网络；
   * factory 不负责解析 secret；
   * CLI 不提供 plaintext API key 参数；
   * 错误信息不应泄露 secret value。

上一任务只完成了 secret resolver 的底层 contract，没有把 resolver 接入 `content-review llm-check` 的运行时检查链路。

因此，本任务的目标是：在不引入真实 provider、不执行真实外部 LLM 调用、不改变主审计流程的前提下，让 `llm-check` 能够检查 provider config 中的 secret reference 是否可解析，并安全地输出 secret 状态。

---

## 2. 任务目标

本任务需要完成：

1. 将 `resolve_llm_provider_secret(config, env=None)` 接入 `content-review llm-check` 的检查流程；
2. 让 `llm-check` 可以基于 `LLMProviderConfig.api_key_env` 检查 secret 是否存在；
3. 在输出中展示 secret reference 与脱敏后的 secret 状态；
4. 缺失 secret reference、缺失环境变量、空环境变量时返回清晰错误；
5. 确保 stdout、stderr、异常信息和文档示例中都不会泄露完整 secret；
6. 保持 provider factory 不解析 secret 的边界；
7. 保持 reserved real provider 不可创建的现有行为；
8. 补充测试与文档。

完成后，用户应该可以通过 `content-review llm-check` 判断 LLM provider 的 secret 配置是否正确，而不需要真正调用外部 LLM API。

---

## 3. 本任务允许做什么

本任务允许：

1. 修改 `content-review llm-check` 的内部检查流程；
2. 修改或扩展 `llm/smoke_check.py` 中的 smoke check 结果模型、构建逻辑或渲染逻辑；
3. 在 `llm-check` 中接收或传递 `api_key_env` 这类 secret reference 参数；
4. 使用 `resolve_llm_provider_secret(config, env=None)` 检查 secret；
5. 使用 `redact_secret_value()` 输出脱敏 secret；
6. 捕获 secret resolver errors 并转换为稳定、可测试的失败结果；
7. 更新 CLI 测试；
8. 更新 smoke check 测试；
9. 更新 provider usage 文档；
10. 更新 CLI 文档；
11. 更新 architecture / data models 文档；
12. 更新 `PROJECT_STATE.md`；
13. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许：

1. 不允许新增 plaintext API key CLI 参数，例如 `--api-key sk-xxx`；
2. 不允许在命令行、日志、异常或文档中输出完整 secret；
3. 不允许读取 `.env` 文件；
4. 不允许新增真实 provider class；
5. 不允许接入 OpenAI、Anthropic、Gemini、DeepSeek、Qwen 或其他真实 SDK；
6. 不允许让 reserved real provider 变成可用；
7. 不允许执行真实外部 LLM API 调用；
8. 不允许访问外部网络；
9. 不允许修改 `ReviewResult`、`BatchReviewResult` 或 `LLMReviewResult` schema；
10. 不允许修改 sidecar metadata；
11. 不允许把 LLM 审计接入主 `review` 命令；
12. 不允许把 LLM 审计接入 `batch` 主流程；
13. 不允许修改 deterministic review engine 行为；
14. 不允许新增 API、MCP、GUI、Supabase、用户系统或商业化能力；
15. 不允许引入 LangChain、CrewAI 或其他大型框架。

---

## 5. 需要修改的文件

预计会修改以下文件：

```text
src/content_review_engine/cli.py
src/content_review_engine/llm/smoke_check.py
src/content_review_engine/llm/secrets.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/provider_config.py
src/content_review_engine/llm/provider_factory.py
src/content_review_engine/llm/__init__.py

tests/test_llm_smoke_check.py
tests/test_llm_secret_resolver.py
tests/test_llm_provider_factory.py
tests/test_cli.py
tests/test_llm_provider_usage_docs.py

docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果实际仓库结构与上述列表略有差异，应优先遵守现有文件结构，不要为了本任务大规模重命名或移动文件。

---

## 6. 实现要求

### 6.1 分层要求

本任务必须保持如下分层：

```text
cli.py
  ↓
llm/smoke_check.py
  ↓
LLMProviderConfig
  ↓
llm/secrets.py
  ↓
provider factory / provider availability check
```

其中：

1. `cli.py` 只负责参数解析、调用 smoke check、渲染输出和设置 exit code；
2. `smoke_check.py` 负责组织 provider config、secret resolver、provider availability check；
3. `secrets.py` 继续只负责 secret 解析和脱敏；
4. `provider_factory.py` 不允许直接读取环境变量；
5. reserved real provider 仍保持不可创建。

---

### 6.2 CLI 参数要求

如果当前 `llm-check` 已经存在 provider / model 参数，应在现有参数基础上扩展。

允许新增 secret reference 参数：

```bash
--api-key-env OPENAI_API_KEY
```

但不允许新增 plaintext secret 参数：

```bash
--api-key sk-...
```

如果当前项目已有等价参数，应复用已有命名，不要引入重复参数。

推荐行为：

```bash
content-review llm-check --provider pydanticai --model test
```

对于不需要 secret 的 test provider，应成功。

```bash
content-review llm-check --provider pydanticai --model gpt-4.1-mini --api-key-env OPENAI_API_KEY
```

对于需要 secret reference 的 provider，应检查 `OPENAI_API_KEY` 是否存在，并输出脱敏状态。

注意：本任务不要求真实调用 `gpt-4.1-mini` 或任何外部模型。

---

### 6.3 secret resolver 接入要求

smoke check 中应构造或接收 `LLMProviderConfig`，然后调用：

```python
resolve_llm_provider_secret(config, env=None)
```

行为要求：

1. 如果 provider / model 不需要 secret，应明确显示 `Secret: not required`；
2. 如果 provider / model 需要 secret 且 `api_key_env` 存在，应解析环境变量；
3. 如果解析成功，应只显示脱敏后的 secret；
4. 如果缺少 `api_key_env`，应返回失败结果；
5. 如果 `api_key_env` 指向的环境变量不存在，应返回失败结果；
6. 如果环境变量存在但为空，应返回失败结果；
7. 失败结果中可以显示 env var name，但不允许显示 secret value；
8. 不允许读取 `.env`；
9. 测试中应优先通过显式 env mapping 控制行为，避免污染真实环境。

---

### 6.4 输出要求

成功输出应包含：

```text
LLM check passed
Provider: ...
Model: ...
API key env: ...
API key: ...
Secret: resolved
```

或在不需要 secret 时：

```text
LLM check passed
Provider: ...
Model: ...
Secret: not required
```

失败输出应包含：

```text
LLM check failed
Reason: ...
```

示例失败：

```text
LLM check failed

Reason: Missing API key environment variable OPENAI_API_KEY

Set the environment variable and retry.
```

输出文案可以遵守当前项目已有风格，但必须满足：

1. 可读；
2. 稳定；
3. 可测试；
4. 不泄露完整 secret；
5. exit code 正确。

---

### 6.5 exit code 要求

`content-review llm-check` 应保持：

1. 成功时 exit code 为 `0`；
2. secret reference 缺失时 exit code 非 `0`；
3. env var 缺失时 exit code 非 `0`；
4. env var 为空时 exit code 非 `0`；
5. 无效 provider 时 exit code 非 `0`；
6. reserved real provider 不可创建时 exit code 非 `0` 或保持当前已有失败语义；
7. 不应因内部未捕获异常直接输出 traceback，除非项目已有 debug 模式明确要求。

---

### 6.6 reserved provider 行为要求

本任务不允许让以下 provider 变成可运行：

```text
openai
anthropic
gemini
deepseek
qwen
local
```

如果这些 provider 当前属于 reserved / unavailable 状态，本任务应保持该行为。

允许 `llm-check` 对它们做 secret reference 检查，但不允许创建真实 provider，也不允许调用真实 API。

---

### 6.7 secret 脱敏要求

必须复用：

```python
redact_secret_value()
```

测试中可以使用假 secret，例如：

```text
sk-test-1234567890abcdef
```

但是断言必须确认以下内容不会出现在 stdout / stderr / error message 中：

```text
sk-test-1234567890abcdef
```

可以出现脱敏值，例如：

```text
sk-...cdef
```

具体脱敏格式以 `redact_secret_value()` 的实际实现为准。

---

## 7. 测试要求

### 7.1 smoke check 测试

更新或新增：

```text
tests/test_llm_smoke_check.py
```

覆盖：

1. 不需要 secret 的 test provider 可以通过；
2. 需要 secret 且 env mapping 存在时可以通过；
3. 需要 secret 但缺少 `api_key_env` 时失败；
4. 指定 `api_key_env` 但 env var 不存在时失败；
5. env var 存在但为空字符串时失败；
6. secret 成功解析后输出为脱敏形式；
7. 原始 secret 不出现在 rendered output 中；
8. secret resolver error 会被转换为稳定 smoke check failure；
9. provider factory 仍不直接解析 secret；
10. reserved provider 仍不可创建。

---

### 7.2 CLI 测试

更新：

```text
tests/test_cli.py
```

覆盖：

1. `content-review llm-check` 成功时 exit code 为 `0`；
2. `--api-key-env` 指向存在的环境变量时可以显示脱敏 secret 状态；
3. `--api-key-env` 指向不存在的环境变量时 exit code 非 `0`；
4. `--api-key-env` 指向空环境变量时 exit code 非 `0`；
5. stdout / stderr 不包含完整 secret；
6. 不存在 plaintext `--api-key` 参数；
7. 无效 provider 行为保持稳定；
8. reserved real provider 行为保持稳定。

---

### 7.3 secret resolver 回归测试

更新或保持：

```text
tests/test_llm_secret_resolver.py
```

确保：

1. resolver contract 不被破坏；
2. resolver 仍不读取 `.env`；
3. resolver 仍不访问网络；
4. error message 仍不泄露 secret；
5. `redact_secret_value()` 行为稳定；
6. `resolve_llm_api_key` 兼容包装仍可用。

---

### 7.4 provider factory 回归测试

更新或保持：

```text
tests/test_llm_provider_factory.py
```

确保：

1. factory 不读取 `os.environ`；
2. factory 不调用 secret resolver；
3. factory reserved provider 行为不变；
4. factory error 不包含 secret value。

---

### 7.5 文档测试

如果当前项目已有文档 usage 测试，更新：

```text
tests/test_llm_provider_usage_docs.py
```

确保文档示例与实际 CLI 行为一致。

---

## 8. 文档更新要求

### 8.1 `docs/LLM_PROVIDER_USAGE.md`

补充：

1. `api_key_env` 的使用方式；
2. `content-review llm-check --api-key-env ...` 示例；
3. 成功输出示例；
4. missing env var 示例；
5. empty env var 示例；
6. secret 脱敏说明；
7. 不读取 `.env` 的说明；
8. 不支持 plaintext API key 参数的说明；
9. 本任务不执行真实 LLM API 调用的说明。

---

### 8.2 `docs/CLI.md`

补充或更新：

1. `content-review llm-check` 参数说明；
2. `--api-key-env` 说明；
3. exit code 说明；
4. secret 安全输出说明；
5. reserved provider 行为说明；
6. 不会修改主审计流程的说明。

---

### 8.3 `docs/DATA_MODELS.md`

补充或更新：

1. `LLMProviderConfig.api_key_env` 是 secret reference；
2. secret value 不应进入持久化数据模型；
3. smoke check 输出只能保存或显示脱敏 secret；
4. factory 不负责解析 secret。

---

### 8.4 `docs/ARCHITECTURE.md`

补充：

1. `llm-check` 如何调用 secret resolver；
2. CLI、smoke check、resolver、factory 的职责边界；
3. 为什么不在 factory 中读取环境变量；
4. 为什么不在 config 中保存 plaintext secret；
5. 当前仍未接入真实 provider 和主 review 流程。

---

### 8.5 `PROJECT_STATE.md`

更新：

1. 标记 `TASK-0062` 完成后新增的能力；
2. 说明当前 `llm-check` 已能验证 secret reference；
3. 说明真实 provider、LLM 主审计接入、报告合并仍是后续任务。

---

### 8.6 `CHANGELOG.md`

新增 `TASK-0062` 记录。

---

## 9. 验收标准

本任务完成后应满足：

1. `content-review llm-check` 可以检查 `api_key_env` secret reference；
2. secret 存在时输出脱敏状态；
3. secret 缺失时返回清晰失败；
4. secret 为空时返回清晰失败；
5. stdout / stderr / error message 不泄露完整 secret；
6. CLI 不支持 plaintext API key 参数；
7. resolver 不读取 `.env`；
8. resolver 不访问外部网络；
9. provider factory 不解析 secret；
10. reserved real provider 仍不可创建；
11. 不修改主审计结果 schema；
12. 不修改 sidecar metadata；
13. 不接入真实 LLM API；
14. 不改变 deterministic review 行为；
15. 文档已同步；
16. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 最大风险是 secret 泄露，必须在测试中明确断言完整 secret 不会出现在输出中。
2. 不要把 `api_key_env` 误实现成 plaintext API key。
3. 不要让 provider factory 读取 `os.environ`。
4. 不要因为 smoke check 需要 secret 就提前实现真实 provider。
5. 不要让测试依赖开发者本机真实环境变量。
6. 不要读取 `.env`，否则会改变 `TASK-0061` 明确建立的 contract。
7. 不要修改主审计 schema，这会把任务扩大到 report integration。
8. 不要把 `llm-check` 的成功误定义为真实 LLM API 可用。本任务的成功只表示配置和 secret reference 检查通过。

---

## 11. 完成后需要运行的命令

可以先运行局部测试：

```bash
uv run pytest tests/test_llm_smoke_check.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_secret_resolver.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_provider_usage_docs.py
```

最后必须运行全量测试：

```bash
uv run pytest
```

---
