# TASK-0038: Add PydanticAI OpenAI-Compatible LLM Provider

## 1. 背景

当前项目已经完成：

```text
TASK-0035: Add LLM provider interface and mock reviewer
  ✅ 已完成

TASK-0036: Add LLM semantic review runner
  ✅ 已完成

TASK-0037: Add CLI LLM review plumbing
  ✅ 已完成
```

当前 LLM 层已经具备以下数据流：

```text
content-review review
        ↓
deterministic review flow
        ↓
optional --enable-llm
        ↓
LLMReviewRequest
        ↓
LLMReviewRunner
        ↓
LLMReviewer provider interface
        ↓
MockLLMReviewer
        ↓
LLMReviewResult sidecar JSON
```

但是目前 CLI 只能使用 `mock` provider，还没有真实 LLM provider。

因此，本任务需要新增一个基于 **PydanticAI** 的 **OpenAI-compatible LLM provider**，让现有 `LLMReviewer` interface 可以调用真实 LLM，并让 CLI 的 `--llm-provider` 可以选择该真实 provider。

本任务仍然必须保持小步推进：

* 只新增真实 provider；
* 只接入单文件 review CLI 的 existing LLM sidecar flow；
* 不修改主 deterministic `ReviewResult`；
* 不修改 Markdown report；
* 不修改 quality gate；
* 不实现 batch LLM review；
* 不实现 API / MCP / GUI。

---

## 2. 任务目标

新增一个真实 LLM provider：

```text
PydanticAI OpenAI-compatible LLM provider
```

本任务完成后，应支持：

1. 新增 PydanticAI provider 实现，并符合现有 `LLMReviewer` interface；
2. 该 provider 接收已有 `LLMReviewRequest`；
3. 该 provider 返回已有 `LLMReviewResult`；
4. 该 provider 通过 PydanticAI 调用 OpenAI-compatible 模型；
5. CLI 可以通过 `--llm-provider pydanticai-openai` 选择该 provider；
6. CLI 可以通过环境变量读取 API key；
7. CLI 可以通过参数指定模型名；
8. CLI 可以可选指定 OpenAI-compatible `base_url`；
9. LLM 结果仍然只写入独立 sidecar JSON；
10. 默认 CLI 行为不变；
11. mock provider 行为不变；
12. 主 review JSON schema 不变；
13. Markdown report 不变；
14. quality gate 行为不变；
15. batch review 行为不变。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 添加 PydanticAI 相关依赖；
2. 新增 PydanticAI OpenAI-compatible provider；
3. 让该 provider 实现现有 `LLMReviewer` interface；
4. 为真实 provider 增加最小配置模型或 helper；
5. 为 CLI 增加真实 provider 选择能力；
6. 为 CLI 增加 `--llm-model` 参数；
7. 为 CLI 增加 `--llm-api-key-env` 参数；
8. 为 CLI 增加可选 `--llm-base-url` 参数；
9. 保留 `mock` provider；
10. 使用现有 `LLMReviewRunner`；
11. 使用现有 `LLMReviewRequest`；
12. 使用现有 `LLMReviewResult`；
13. 使用现有 LLM result serialization helper；
14. 新增 provider 单元测试；
15. 新增 CLI provider 参数测试；
16. 更新 CLI 文档；
17. 更新架构文档；
18. 更新数据模型文档；
19. 更新 `PROJECT_STATE.md`；
20. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许把 LLM findings 合并进当前 deterministic `ReviewResult`；
2. 不允许改变当前 review JSON schema；
3. 不允许改变当前 Markdown report 输出结构；
4. 不允许让 quality gate 统计 LLM findings；
5. 不允许修改 batch review 行为；
6. 不允许给 batch command 增加 LLM 支持；
7. 不允许新增 API；
8. 不允许新增 MCP；
9. 不允许新增 GUI；
10. 不允许新增 streaming；
11. 不允许新增 retry policy；
12. 不允许新增 cache；
13. 不允许新增 token accounting；
14. 不允许新增 cost tracking；
15. 不允许新增 telemetry；
16. 不允许新增 tracing / Logfire 集成；
17. 不允许新增 prompt template registry；
18. 不允许在代码中硬编码 API key；
19. 不允许在代码中硬编码真实用户凭据；
20. 不允许默认启用真实 LLM；
21. 不允许在未传 `--enable-llm` 时读取 API key 或调用 provider；
22. 不允许在测试中进行真实网络请求；
23. 不允许要求测试环境必须有真实 API key。

---

## 5. 需要修改的文件

预计需要修改或新增以下文件：

```text
pyproject.toml
uv.lock
src/content_review_engine/cli.py
src/content_review_engine/llm/__init__.py
src/content_review_engine/llm/pydanticai.py
tests/test_llm_pydanticai_provider.py
tests/test_cli.py
docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前项目已有专门的 CLI LLM 测试文件，也可以改为新增或更新：

```text
tests/test_cli_llm.py
```

如果当前项目已有 provider factory/helper，也应优先复用；如果没有，可以新增轻量 helper，例如：

```text
src/content_review_engine/llm/factory.py
```

但该 helper 只能做 provider 构造，不允许做复杂 routing、retry、cache、telemetry 或多 provider orchestration。

---

## 6. 实现要求

### 6.1 依赖要求

添加 PydanticAI 依赖。

优先考虑使用较轻量的 OpenAI provider 依赖，例如：

```bash
uv add "pydantic-ai-slim[openai]"
```

如果项目风格更适合完整包，也可以使用：

```bash
uv add pydantic-ai
```

但需要在 Agent 输出中说明选择原因。

依赖变更应体现在：

```text
pyproject.toml
uv.lock
```

不要手动编辑 lock 文件，应通过 `uv` 命令更新。

---

### 6.2 Provider 文件

新增文件：

```text
src/content_review_engine/llm/pydanticai.py
```

该文件用于实现 PydanticAI provider。

建议类名：

```python
PydanticAIReviewer
```

或更明确：

```python
PydanticAIOpenAIReviewer
```

最终命名应符合现有项目风格。

该 provider 必须实现现有 `LLMReviewer` interface。

推荐结构：

```python
class PydanticAIOpenAIReviewer:
    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        base_url: str | None = None,
    ) -> None:
        ...

    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        ...
```

如果现有 `LLMReviewer` interface 使用不同方法名，应遵循现有 interface。

---

### 6.3 Provider 配置规则

真实 provider 至少需要以下配置：

```text
model
api_key
base_url optional
```

CLI 层不应直接接收明文 API key。

推荐 CLI 参数：

```text
--llm-provider pydanticai-openai
--llm-model <model>
--llm-api-key-env OPENAI_API_KEY
--llm-base-url <url>
```

规则：

1. `--llm-model` 仅在真实 provider 下需要；
2. `--llm-api-key-env` 默认可以是 `OPENAI_API_KEY`；
3. `--llm-api-key-env` 的值是环境变量名称，不是 API key 本身；
4. CLI 应从该环境变量读取 API key；
5. 如果环境变量不存在或为空，应返回清晰错误；
6. `--llm-base-url` 可选，用于 OpenAI-compatible endpoint；
7. 不允许新增 `--llm-api-key` 明文参数；
8. 不允许把 API key 写入输出、日志、错误信息或 sidecar JSON。

---

### 6.4 CLI provider 选择规则

当前 TASK-0037 已支持：

```text
--llm-provider mock
```

本任务应扩展为：

```text
--llm-provider mock
--llm-provider pydanticai-openai
```

行为要求：

#### mock provider

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider mock \
  --llm-output llm-review.json
```

应保持 TASK-0037 行为不变。

#### PydanticAI OpenAI-compatible provider

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai-openai \
  --llm-model gpt-5-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-output llm-review.json
```

可选 base URL：

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai-openai \
  --llm-model deepseek-chat \
  --llm-api-key-env DEEPSEEK_API_KEY \
  --llm-base-url https://api.deepseek.com \
  --llm-output llm-review.json
```

注意：上述模型名和 base URL 只是用法示例，不应在代码中硬编码。

---

### 6.5 参数校验规则

需要补充以下参数校验：

1. `--llm-provider mock` 时，不要求 `--llm-model`；
2. `--llm-provider mock` 时，不应读取 API key；
3. `--llm-provider mock` 时，不应要求 `--llm-api-key-env`；
4. `--llm-provider pydanticai-openai` 时，必须提供 `--llm-model`；
5. `--llm-provider pydanticai-openai` 时，必须能从 `--llm-api-key-env` 指定的环境变量读取 API key；
6. `--llm-provider pydanticai-openai` 时，`--llm-base-url` 可选；
7. `--llm-model` 未配合 `--enable-llm` 使用时应失败；
8. `--llm-api-key-env` 未配合 `--enable-llm` 使用时应失败；
9. `--llm-base-url` 未配合 `--enable-llm` 使用时应失败；
10. unsupported provider 仍然失败；
11. 参数错误应按现有 CLI 风格返回，不应抛 traceback。

---

### 6.6 PydanticAI 调用规则

provider 内部应使用 PydanticAI `Agent`。

建议使用结构化输出，让模型返回一个可验证的数据结构，然后再转换成已有 `LLMReviewResult`。

推荐思路：

```text
LLMReviewRequest
        ↓
prompt / instructions
        ↓
PydanticAI Agent with structured output
        ↓
provider output model
        ↓
LLMReviewResult
```

实现要求：

1. 不要让 provider 返回自由文本；
2. 不要把自由文本直接塞进 `LLMReviewResult`；
3. 应尽量使用结构化输出；
4. provider 输出结构应能映射到已有 `LLMReviewResult`；
5. 如果模型输出无法验证，应抛出或包装为 `LLMResponseValidationError`；
6. 如果 provider/API 调用失败，应抛出或包装为 `LLMProviderError`；
7. 不要把第三方异常直接泄露到 CLI 用户界面；
8. 不要在 provider 中调用 `sys.exit()`；
9. 不要在 provider 中打印到 stdout/stderr。

---

### 6.7 Prompt / instructions 要求

本任务可以新增一个最小 prompt / instructions，但不要做复杂 prompt registry。

Prompt 应明确要求模型执行内容审计，并返回结构化结果。

应覆盖：

1. 输入内容；
2. review profile 或 profile 中可用于 LLM 的上下文；
3. 输出必须符合结构化 schema；
4. finding 应包含 severity、rule_id、message、suggestion、location 或 context；
5. 没有问题时返回空 findings；
6. 不应编造不存在的原文；
7. 不应输出 Markdown 报告；
8. 不应输出非结构化解释。

如果现有 `LLMReviewRequest` 已经包含 profile/rules/context，则应优先使用现有字段。

---

### 6.8 错误处理要求

应将错误映射到现有错误类型：

```text
LLMReviewError
LLMProviderError
LLMResponseValidationError
```

推荐规则：

1. API key 缺失：CLI 参数错误或 provider configuration error；
2. provider 初始化失败：`LLMProviderError`；
3. API 调用失败：`LLMProviderError`；
4. 模型返回内容无法验证：`LLMResponseValidationError`；
5. 其他 LLM provider 相关错误：`LLMReviewError` 或其子类。

如果现有错误类型不足，不要大规模重构；可以新增最小必要错误类型，但需保持错误层级清晰。

---

### 6.9 Sidecar 输出规则

本任务继续沿用 TASK-0037 的 sidecar 输出模式。

启用真实 provider 后：

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai-openai \
  --llm-model gpt-5-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-output llm-review.json
```

输出仍然是：

```text
llm-review.json
```

且必须：

1. 使用已有 `llm_review_result_to_json` helper；
2. 包含 `schema_version`；
3. 不包含 API key；
4. 不包含 provider secret；
5. 不合并 deterministic review result；
6. 不改变主 `--format json` 输出；
7. 不改变 Markdown report；
8. 不影响 quality gate。

---

### 6.10 测试不得访问网络

所有测试必须离线运行。

不允许测试真实 API。

测试真实 provider 时应使用：

1. monkeypatch；
2. fake PydanticAI agent；
3. fake result；
4. fake provider object；
5. dependency injection；
6. 或现有测试工具。

测试中不得要求：

```text
OPENAI_API_KEY
DEEPSEEK_API_KEY
真实网络
真实模型响应
```

---

## 7. 测试要求

### 7.1 Provider 单元测试

新增：

```text
tests/test_llm_pydanticai_provider.py
```

至少覆盖：

1. provider 实现 `LLMReviewer` interface；
2. provider 能把 `LLMReviewRequest` 转换为 PydanticAI prompt/input；
3. provider 能把 fake structured output 转换为 `LLMReviewResult`；
4. provider 输出包含正确 `schema_version`；
5. provider 能返回空 findings；
6. provider 能返回一个或多个 findings；
7. provider 调用失败时抛出 `LLMProviderError`；
8. provider 输出验证失败时抛出 `LLMResponseValidationError`；
9. provider 不把 API key 暴露在异常字符串或输出中。

---

### 7.2 CLI 测试

更新：

```text
tests/test_cli.py
```

或新增：

```text
tests/test_cli_llm.py
```

至少覆盖：

#### mock provider 兼容性

1. `--llm-provider mock` 仍然可用；
2. mock provider 不需要 `--llm-model`；
3. mock provider 不读取 API key；
4. mock sidecar 输出仍然稳定。

#### pydanticai-openai provider 参数校验

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai-openai \
  --llm-output llm-review.json
```

应失败，因为缺少 `--llm-model`。

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai-openai \
  --llm-model gpt-5-mini \
  --llm-api-key-env MISSING_API_KEY \
  --llm-output llm-review.json
```

应失败，因为环境变量不存在或为空。

#### pydanticai-openai provider 成功路径

使用 monkeypatch / fake provider，测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai-openai \
  --llm-model fake-model \
  --llm-api-key-env FAKE_API_KEY \
  --llm-output llm-review.json
```

应验证：

1. 命令成功；
2. sidecar JSON 被创建；
3. sidecar JSON 使用 `llm-review-result.v1`；
4. sidecar JSON 包含 fake provider 返回的 findings；
5. 主 JSON 输出不包含 `llm_review`；
6. Markdown report 不包含 LLM section；
7. quality gate 行为不受影响。

#### 参数未配合 --enable-llm

以下参数如果没有 `--enable-llm` 应失败：

```text
--llm-model
--llm-api-key-env
--llm-base-url
```

---

### 7.3 完整测试

最终运行：

```bash
uv run pytest
```

确保所有测试通过。

---

## 8. 文档更新要求

### 8.1 更新 docs/CLI.md

需要补充真实 provider 用法。

说明：

1. LLM review 仍然是 explicit opt-in；
2. `mock` provider 仍然可用；
3. 新增 `pydanticai-openai` provider；
4. 真实 provider 需要 `--llm-model`；
5. 真实 provider 默认从 `OPENAI_API_KEY` 或 `--llm-api-key-env` 指定的环境变量读取 API key；
6. 可以使用 `--llm-base-url` 连接 OpenAI-compatible endpoint；
7. API key 不应通过 CLI 明文传入；
8. LLM output 仍然写入独立 sidecar JSON；
9. 主 review JSON 不变；
10. Markdown report 不变；
11. quality gate 不受 LLM result 影响；
12. batch 暂不支持 LLM review。

示例：

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai-openai \
  --llm-model gpt-5-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-output llm-review.json
```

OpenAI-compatible endpoint 示例：

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai-openai \
  --llm-model deepseek-chat \
  --llm-api-key-env DEEPSEEK_API_KEY \
  --llm-base-url https://api.deepseek.com \
  --llm-output llm-review.json
```

---

### 8.2 更新 docs/ARCHITECTURE.md

补充真实 provider 架构：

```text
CLI review command
        ↓
optional --enable-llm
        ↓
LLMReviewRequest
        ↓
LLMReviewRunner
        ↓
LLMReviewer interface
        ↓
MockLLMReviewer or PydanticAIOpenAIReviewer
        ↓
LLMReviewResult sidecar JSON
```

说明：

1. provider interface 仍然是边界；
2. PydanticAI 只存在于 provider 实现内；
3. deterministic review engine 不依赖 PydanticAI；
4. reports 不依赖 PydanticAI；
5. quality gate 不依赖 PydanticAI；
6. CLI 只负责 provider 选择和配置；
7. 真实 provider 不影响默认 CLI 行为。

---

### 8.3 更新 docs/DATA_MODELS.md

补充：

1. PydanticAI provider 的结构化输出会转换为 `LLMReviewResult`；
2. `LLMReviewResult` sidecar schema 保持不变；
3. `ReviewResult` schema 仍然不变；
4. LLM provider 配置不属于 review result；
5. API key 不会写入 result；
6. provider metadata 如需要记录，必须避免包含 secret。

---

### 8.4 更新 PROJECT_STATE.md

记录：

1. TASK-0038 已完成；
2. 新增 PydanticAI OpenAI-compatible provider；
3. CLI 可以选择 `mock` 或 `pydanticai-openai`；
4. 真实 provider 仍然 explicit opt-in；
5. LLM result 仍然 sidecar 输出；
6. 主 review JSON / Markdown report / quality gate / batch 行为不变；
7. report integration、batch LLM review、API、MCP、GUI 尚未实现。

---

### 8.5 更新 CHANGELOG.md

记录：

1. 新增 PydanticAI OpenAI-compatible provider；
2. 新增 provider 配置参数；
3. CLI `--llm-provider` 支持真实 provider；
4. 新增 provider 和 CLI 测试；
5. 更新文档；
6. 明确未改变主 review schema、Markdown report、quality gate、batch、API、MCP、GUI。

---

## 9. 验收标准

本任务完成后应满足：

1. 项目添加 PydanticAI 依赖；
2. 存在 PydanticAI OpenAI-compatible provider；
3. provider 实现 `LLMReviewer` interface；
4. provider 接收 `LLMReviewRequest`；
5. provider 返回 `LLMReviewResult`；
6. provider 使用结构化输出或等价的严格验证流程；
7. provider 调用失败映射为 LLM 错误类型；
8. provider 输出验证失败映射为 LLM 错误类型；
9. CLI 支持 `--llm-provider pydanticai-openai`；
10. CLI 支持 `--llm-model`；
11. CLI 支持 `--llm-api-key-env`；
12. CLI 支持可选 `--llm-base-url`；
13. CLI 不支持明文 `--llm-api-key`；
14. mock provider 行为保持不变；
15. 默认 CLI 行为保持不变；
16. LLM result 仍然写入 sidecar JSON；
17. 主 review JSON schema 不变；
18. Markdown report 不变；
19. quality gate 行为不变；
20. batch 行为不变；
21. 测试不进行真实网络请求；
22. 测试不要求真实 API key；
23. provider 单元测试通过；
24. CLI LLM 测试通过；
25. `uv run pytest` 全部通过；
26. docs/CLI.md 已更新；
27. docs/ARCHITECTURE.md 已更新；
28. docs/DATA_MODELS.md 已更新；
29. PROJECT_STATE.md 已更新；
30. CHANGELOG.md 已更新。

---

## 10. 风险与注意事项

### 10.1 防止把 provider 侵入 core

PydanticAI 只能存在于 LLM provider 实现内。

不要让以下模块依赖 PydanticAI：

```text
core models
deterministic rules
review runner
reports
quality gate
batch review
```

---

### 10.2 防止测试访问真实网络

所有测试必须离线可运行。

不要在测试中调用真实 API。

---

### 10.3 防止泄露 API key

不要：

1. 把 API key 写进测试 fixture；
2. 把 API key 写进 docs 示例；
3. 把 API key 打印到 stdout；
4. 把 API key 写入 sidecar JSON；
5. 把 API key 写入异常信息；
6. 把 API key 写入 PROJECT_STATE.md 或 CHANGELOG.md。

---

### 10.4 防止输出 schema 膨胀

本任务不应改动主 review result。

不要添加：

```json
{
  "llm_review": {}
}
```

到 deterministic review JSON。

---

### 10.5 防止 report integration 提前发生

不要在 Markdown report 中新增：

```md
## LLM Review
```

这属于后续任务。

---

## 11. 完成后需要运行的命令

如果添加依赖，先使用 uv 更新依赖：

```bash
uv add "pydantic-ai-slim[openai]"
```

或在确有理由时：

```bash
uv add pydantic-ai
```

运行 provider 测试：

```bash
uv run pytest tests/test_llm_pydanticai_provider.py
```

运行 CLI 测试：

```bash
uv run pytest tests/test_cli.py
```

最后运行完整测试：

```bash
uv run pytest
```

---

