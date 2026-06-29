# TASK-0064: Add Optional Live PydanticAI Runtime Smoke Check

## 1. 背景

当前项目已经完成：

```text
TASK-0061: Add LLM Provider Secret Resolver
TASK-0062: Wire LLM Secret Resolver into LLM Check
TASK-0063: Enable Real PydanticAI Provider Construction
```

目前 LLM provider 链路已经具备：

1. `LLMProviderConfig.api_key_env` 作为 secret reference；
2. `resolve_llm_provider_secret(config, env=None)`；
3. `redact_secret_value()`；
4. `content-review llm-check` 的 config-driven secret preflight；
5. `--llm-api-key-env` 安全传递环境变量名称；
6. `create_llm_reviewer(config, secret_value=...)`；
7. `provider="pydanticai"` 可以通过 factory 构造；
8. `PydanticAIReviewer.run_construction_check()`；
9. `llm-check` 默认输出：

   * `Construction: ok`
   * `Live call: not run`
10. 普通测试不依赖真实 API key；
11. 普通测试不访问外部网络；
12. reserved providers 仍不可创建；
13. 主 `review` / `batch` 流程仍未接入 LLM；
14. `ReviewResult`、`BatchReviewResult`、`LLMReviewResult` schema 均未改变。

上一任务只完成了 **PydanticAI provider construction check**，也就是确认 provider 可以在本地构造，但没有真实调用外部 LLM 服务。

本任务的目标是：在 `content-review llm-check` 中新增一个 **显式 opt-in 的 live runtime smoke check**，用于用户手动验证真实 PydanticAI provider 是否可以完成一次最小 LLM 调用。

默认情况下，`llm-check` 仍然不得发起真实 LLM API 调用。只有用户显式传入 live 参数时，才允许进行真实 runtime smoke check。

---

## 2. 任务目标

本任务需要完成：

1. 为 `content-review llm-check` 增加显式 live check 开关；
2. 默认仍保持 `Live call: not run`；
3. 用户显式启用 live check 时，才允许调用真实 PydanticAI provider；
4. live check 使用已解析的 secret value；
5. live check 不得泄露完整 secret；
6. live check 应发送最小、稳定、低风险的 smoke prompt；
7. live check 成功时输出稳定成功状态；
8. live check 失败时输出清晰、可行动、不会泄露 secret 的错误；
9. 普通单元测试不得访问外部网络；
10. 普通单元测试不得要求真实 API key；
11. live 行为需要通过 fake / monkeypatch / stub 测试；
12. 文档中明确区分 construction check 与 live runtime check。

完成后，用户可以通过类似命令手动验证真实 PydanticAI provider：

```bash
content-review llm-check \
  --provider pydanticai \
  --llm-model gpt-4.1-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --live
```

具体参数名称以当前项目已有 CLI 风格为准。如果当前模型参数不是 `--llm-model`，应使用仓库现有命名，不要为了本任务强行重命名。

---

## 3. 本任务允许做什么

本任务允许：

1. 为 `content-review llm-check` 增加显式 live check 参数，例如 `--live` 或当前项目更合适的等价名称；
2. 在 `llm/smoke_check.py` 中增加 live check 编排逻辑；
3. 在 `PydanticAIReviewer` 中新增 live runtime check 方法；
4. 让 live check 调用真实 PydanticAI provider；
5. 让 live check 使用已解析 secret；
6. 增加 live check result 字段；
7. 增加 live check 成功与失败渲染；
8. 增加 live check 相关错误类型；
9. 通过 fake / monkeypatch / stub 测试 live check；
10. 增加 CLI 测试；
11. 增加 smoke check 测试；
12. 增加 PydanticAI provider 测试；
13. 更新 provider factory 相关测试；
14. 更新文档与项目状态。

---

## 4. 本任务不允许做什么

本任务不允许：

1. 不允许默认执行 live call；
2. 不允许在普通 `llm-check` 中自动访问外部网络；
3. 不允许在普通测试中调用真实 LLM API；
4. 不允许在普通测试中要求真实 API key；
5. 不允许新增 plaintext API key CLI 参数；
6. 不允许输出完整 secret value；
7. 不允许读取 `.env` 文件；
8. 不允许让 provider factory 读取 `os.environ`；
9. 不允许让 provider factory 调用 secret resolver；
10. 不允许把 live check 接入 `content-review review`；
11. 不允许把 live check 接入 `content-review batch`；
12. 不允许实现正式 LLM 内容审计 prompt；
13. 不允许实现 LLMReviewResult 生产逻辑；
14. 不允许修改 `ReviewResult`、`BatchReviewResult` 或 `LLMReviewResult` schema；
15. 不允许修改 sidecar metadata；
16. 不允许修改 deterministic review engine 行为；
17. 不允许让 `openai`、`anthropic`、`gemini`、`deepseek`、`qwen`、`local` 等 reserved providers 变成可创建；
18. 不允许新增 API、MCP、Skill、GUI、Supabase、用户系统或商业化能力；
19. 不允许引入 LangChain、CrewAI 或其他大型框架。

---

## 5. 需要修改的文件

预计会修改以下文件：

```text
src/content_review_engine/cli.py
src/content_review_engine/llm/smoke_check.py
src/content_review_engine/llm/pydanticai.py
src/content_review_engine/llm/factory.py
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

如果实际仓库文件名与上述列表略有差异，应优先遵守当前项目已有结构。例如当前项目已经使用：

```text
src/content_review_engine/llm/factory.py
src/content_review_engine/llm/pydanticai.py
```

则应继续使用该命名，不要改成 `provider_factory.py` 或 `pydanticai_provider.py`。

---

## 6. 实现要求

### 6.1 CLI 参数要求

为 `content-review llm-check` 增加显式 live 参数。

推荐命名：

```bash
--live
```

如果项目已有类似命名规范，也可以使用更一致的名称，例如：

```bash
--llm-live
```

但不要同时引入多个重复参数。

默认行为必须保持：

```text
Live call: not run
```

只有用户显式传入 live 参数时，才允许执行真实 runtime call。

示例：

```bash
content-review llm-check \
  --provider pydanticai \
  --llm-model gpt-4.1-mini \
  --llm-api-key-env OPENAI_API_KEY
```

输出应仍然类似：

```text
Construction: ok
Live call: not run
```

显式启用 live：

```bash
content-review llm-check \
  --provider pydanticai \
  --llm-model gpt-4.1-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --live
```

输出应类似：

```text
Construction: ok
Live call: ok
```

具体输出文案可以遵守当前项目已有风格，但必须稳定、可测试。

---

### 6.2 smoke check 分层要求

本任务必须保持当前分层：

```text
cli.py
  ↓
llm/smoke_check.py
  ↓
resolve_llm_provider_secret()
  ↓
create_llm_reviewer(config, secret_value=...)
  ↓
PydanticAIReviewer.run_construction_check()
  ↓
PydanticAIReviewer.run_live_check()
```

其中：

1. `cli.py` 只负责参数解析、调用 smoke check、渲染结果和设置 exit code；
2. `smoke_check.py` 负责编排 secret preflight、construction check、optional live check；
3. `factory.py` 只负责 provider construction；
4. `factory.py` 不得读取环境变量；
5. `factory.py` 不得调用 secret resolver；
6. `PydanticAIReviewer` 负责 provider-specific construction / live check；
7. live check 只在显式启用时执行。

---

### 6.3 PydanticAI live check 要求

在 `PydanticAIReviewer` 中新增方法。

推荐命名：

```python
run_live_check()
```

或遵守当前项目已有命名风格。

该方法应：

1. 发起一次最小 PydanticAI 调用；
2. 使用构造时注入的 in-memory secret；
3. 使用当前 config 中的 model；
4. 使用稳定、低风险 prompt；
5. 验证模型返回了非空响应；
6. 返回结构化 live check 结果或抛出稳定错误；
7. 不输出完整 secret；
8. 不修改全局环境。

推荐 smoke prompt：

```text
Reply with exactly: ok
```

live check 不应要求模型执行内容审计，不应读取用户文件，不应生成 LLM findings。

---

### 6.4 live check 结果要求

`LLMSmokeCheckResult` 或当前等价内部结果结构可以增加 live 相关字段。

允许增加类似字段：

```python
live_requested: bool
live_status: Literal["not_run", "ok", "failed"]
live_message: str | None
```

具体字段名称以当前代码风格为准。

要求：

1. 默认 `live_requested=False`；
2. 默认 `live_status="not_run"`；
3. 显式启用且成功时 `live_status="ok"`；
4. 显式启用且失败时 `live_status="failed"`；
5. 失败信息不得包含完整 secret；
6. 该结构仍属于 smoke check internal result；
7. 不得修改 `ReviewResult`、`BatchReviewResult`、`LLMReviewResult` schema。

---

### 6.5 输出要求

默认输出：

```text
LLM check passed

Provider: pydanticai
Model: gpt-4.1-mini
API key env: OPENAI_API_KEY
API key: sk-...cdef
Secret: resolved
Construction: ok
Live call: not run
```

显式 live 成功输出：

```text
LLM check passed

Provider: pydanticai
Model: gpt-4.1-mini
API key env: OPENAI_API_KEY
API key: sk-...cdef
Secret: resolved
Construction: ok
Live call: ok
```

显式 live 失败输出：

```text
LLM check failed

Provider: pydanticai
Model: gpt-4.1-mini
API key env: OPENAI_API_KEY
API key: sk-...cdef
Secret: resolved
Construction: ok
Live call: failed

Reason: ...
```

要求：

1. 不泄露完整 secret；
2. 不输出 traceback；
3. failure reason 清晰；
4. exit code 非 0；
5. 区分 construction failure 与 live failure；
6. 明确 live call 是否执行。

---

### 6.6 错误处理要求

如果需要新增错误类型，可以新增：

```python
LLMLiveCheckError
```

或遵守当前项目 error hierarchy 中已有命名。

错误处理要求：

1. PydanticAI live call 抛错时，转换为稳定错误；
2. 网络错误、鉴权错误、模型错误、响应为空等情况都应返回失败；
3. 错误信息不得包含完整 secret；
4. CLI 不应输出未捕获 traceback；
5. 普通 construction error 和 live error 应可区分；
6. reserved provider error 行为保持不变。

---

### 6.7 测试隔离要求

普通测试不得访问外部网络。

测试 live check 时必须使用：

1. fake PydanticAI model；
2. PydanticAI TestModel；
3. monkeypatch；
4. stubbed reviewer；
5. 或当前项目已有等价测试方式。

普通测试不得依赖：

1. 真实 OpenAI API key；
2. 真实 Anthropic API key；
3. 真实 Gemini API key；
4. 真实 DeepSeek API key；
5. 真实 Qwen API key；
6. 开发者本机环境变量；
7. 外部网络。

如需提供真实 live check 手动验证说明，只能写入文档，不得加入默认测试。

---

### 6.8 手动 live check 文档要求

文档中可以说明：

```bash
export OPENAI_API_KEY=...
content-review llm-check \
  --provider pydanticai \
  --llm-model gpt-4.1-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --live
```

但注意：

1. 不得写入真实 API key；
2. 不得要求 CI 运行该命令；
3. 应说明该命令会访问外部 LLM 服务；
4. 应说明可能产生费用；
5. 应说明默认 `llm-check` 不会执行 live call；
6. 应说明 live check 不是正式内容审计。

---

## 7. 测试要求

### 7.1 PydanticAI provider 测试

更新：

```text
tests/test_llm_pydanticai_provider.py
```

覆盖：

1. `run_live_check()` 成功路径；
2. `run_live_check()` 使用 fake / stub，不访问真实网络；
3. live response 非空时成功；
4. live response 为空时失败；
5. provider exception 会转换为稳定错误；
6. full secret 不出现在错误信息中；
7. construction check 仍不执行 live call；
8. construction check 与 live check 可区分。

---

### 7.2 smoke check 测试

更新：

```text
tests/test_llm_smoke_check.py
```

覆盖：

1. 默认不执行 live call；
2. 默认输出 `Live call: not run`；
3. `live=True` 时执行 live check；
4. live 成功时输出 `Live call: ok` 或等价文案；
5. live 失败时返回失败 result；
6. construction failure 时不继续 live check；
7. secret missing / empty 时不继续 construction 或 live check；
8. full secret 不出现在 rendered output；
9. reserved provider 行为保持稳定。

---

### 7.3 CLI 测试

更新：

```text
tests/test_cli.py
```

覆盖：

1. 不传 live 参数时默认不执行 live call；
2. 传入 live 参数时进入 live check 路径；
3. live 成功时 exit code 为 0；
4. live 失败时 exit code 非 0；
5. stdout / stderr 不包含完整 secret；
6. 输出包含 `Construction: ok`；
7. 输出包含 `Live call: not run` 或 `Live call: ok`；
8. plaintext `--api-key` 参数仍不存在；
9. missing env var 行为保持稳定；
10. empty env var 行为保持稳定。

---

### 7.4 provider factory 测试

更新或保持：

```text
tests/test_llm_provider_factory.py
```

确保：

1. factory 不执行 live check；
2. factory 只构造 provider；
3. factory 不读取 env；
4. factory 不调用 secret resolver；
5. factory 不泄露 secret；
6. reserved providers 仍不可创建。

---

### 7.5 文档测试

更新：

```text
tests/test_llm_provider_usage_docs.py
```

确保文档中包含：

1. `--live` 或实际 live 参数；
2. 默认 `Live call: not run`；
3. live check 会访问外部服务；
4. live check 可能产生费用；
5. live check 不是正式内容审计；
6. 不支持 plaintext API key；
7. 不读取 `.env`；
8. redacted secret 示例。

---

## 8. 文档更新要求

### 8.1 `docs/LLM_PROVIDER_USAGE.md`

补充：

1. construction check 与 live check 的区别；
2. 默认不执行 live call；
3. 如何显式运行 live check；
4. live check 会访问外部 LLM 服务；
5. live check 可能产生费用；
6. live check 使用 `--llm-api-key-env`；
7. live check 不支持 plaintext API key；
8. live check 不读取 `.env`；
9. live check 不是正式内容审计；
10. CI 默认不应运行 live check。

---

### 8.2 `docs/CLI.md`

补充或更新：

1. `content-review llm-check` 的 live 参数；
2. 默认输出示例；
3. live 成功输出示例；
4. live 失败输出示例；
5. exit code 说明；
6. secret 脱敏说明；
7. live check 与正式审计的区别。

---

### 8.3 `docs/ARCHITECTURE.md`

补充：

1. optional live runtime smoke check 在 LLM provider layer 中的位置；
2. resolver、smoke check、factory、PydanticAI provider 的职责边界；
3. live check 为什么必须显式 opt-in；
4. live check 为什么不接入主 review / batch；
5. live check 为什么不改变 canonical schemas；
6. 普通测试如何避免真实网络。

---

### 8.4 `docs/DATA_MODELS.md`

补充或更新：

1. `LLMSmokeCheckResult` 的 live check 字段；
2. live check result 是内部检查结果；
3. live check 不修改 `LLMReviewResult`；
4. live check 不修改 `ReviewResult`；
5. live check 不修改 `BatchReviewResult`；
6. secret value 不进入 canonical data model。

---

### 8.5 `PROJECT_STATE.md`

更新：

1. 标记 `TASK-0064` 完成后新增 optional live smoke check；
2. 说明默认仍不执行 live call；
3. 说明主 review / batch 仍未接入 LLM；
4. 说明 LLM prompt contract、LLM output validation、review integration 仍是后续任务。

---

### 8.6 `CHANGELOG.md`

新增 `TASK-0064` 记录。

---

## 9. 验收标准

本任务完成后应满足：

1. `content-review llm-check` 默认仍不执行 live call；
2. 默认输出仍显示 `Live call: not run`；
3. 显式传入 live 参数后才执行 live runtime check；
4. live 成功时输出 `Live call: ok` 或等价稳定文案；
5. live 失败时输出清晰失败信息；
6. live 失败时 exit code 非 0；
7. stdout / stderr / error message 不泄露完整 secret；
8. provider factory 不执行 live check；
9. provider factory 不解析 secret；
10. provider factory 不读取 env；
11. 普通测试不访问真实网络；
12. 普通测试不要求真实 API key；
13. reserved providers 仍不可创建；
14. 不新增 plaintext API key 参数；
15. 不读取 `.env`；
16. 不修改 `ReviewResult`、`BatchReviewResult`、`LLMReviewResult` schema；
17. 不修改 sidecar metadata；
18. 不接入主 `review` 或 `batch` 流程；
19. 不实现正式 LLM 内容审计 prompt；
20. 文档已同步；
21. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 最大风险是把 live check 做成默认行为，必须避免。
2. 第二大风险是普通测试误访问真实网络，必须通过 fake / monkeypatch / stub 隔离。
3. 不要把 live check 和正式内容审计混在一起。
4. 不要在这个任务中设计正式审计 prompt。
5. 不要生成 `LLMReviewResult`。
6. 不要修改主报告 schema。
7. 不要把 secret value 写入 config、report、JSON、日志或异常。
8. 不要在 factory 中加入 live 行为。
9. 不要让 reserved providers 顺手变成可用。
10. 文档中必须提醒 live check 可能访问外部服务并产生费用。

---

## 11. 完成后需要运行的命令

可以先运行局部测试：

```bash
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_smoke_check.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_provider_usage_docs.py
```

最后必须运行全量测试：

```bash
uv run pytest
```

---

