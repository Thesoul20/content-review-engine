# TASK-0056: Add LLM Check Provider Selection

## 1. 背景

当前项目已经完成确定性内容审计主链路，包括 Markdown 读取、Profile 加载、规则审计、单文件 CLI、批量 CLI、JSON / Markdown 报告输出，以及 Quality Gate / CI 门禁。

LLM 语义审计阶段目前已经完成了以下能力：

1. `LLMReviewRequest`
2. `LLMReviewer` provider interface
3. `MockLLMReviewer`
4. `LLMReviewResult`
5. LLM semantic review runner
6. LLM sidecar output
7. batch LLM sidecar output
8. `content-review llm-check` smoke check
9. `PydanticAITestModelReviewer`
10. `create_llm_reviewer()` provider factory
11. `UnsupportedLLMProviderError`

TASK-0055 已经新增了统一的 LLM reviewer provider factory，可以通过 provider name 创建：

1. `mock`
2. `pydantic-ai-testmodel`

但是当前 `content-review llm-check` 还没有提供显式的 provider 选择入口。

本任务的目标是让 `content-review llm-check` 支持一个安全、有限的 provider 选择参数，使开发者可以通过 CLI 验证不同的测试 provider 是否能通过统一 factory 正常运行。

本任务只扩展 `llm-check` 命令，不接入正式内容审计流程，不修改 `content-review review` 或 `content-review batch` 的默认行为。

---

## 2. 任务目标

为 `content-review llm-check` 新增 provider 选择能力。

本任务完成后，应支持：

```bash
content-review llm-check
```

保持现有默认行为。

同时支持：

```bash
content-review llm-check --provider pydantic-ai-testmodel
```

以及：

```bash
content-review llm-check --provider mock
```

其中：

1. `pydantic-ai-testmodel` 使用 `PydanticAITestModelReviewer`；
2. `mock` 使用 `MockLLMReviewer`；
3. provider 创建必须通过 `create_llm_reviewer()`；
4. unsupported provider 必须返回清晰错误；
5. 不允许访问真实 LLM API；
6. 不允许要求 API key；
7. 不允许修改正式 review / batch 审计流程。

本任务完成后的内部结构应大致为：

```text
content-review llm-check --provider <name>
        ↓
create_llm_reviewer(<name>)
        ↓
MockLLMReviewer / PydanticAITestModelReviewer
        ↓
build_llm_smoke_check_request()
        ↓
reviewer.review(request)
        ↓
render_llm_smoke_check_result()
```

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 给 `content-review llm-check` 新增 `--provider` 参数；
2. 允许 `--provider mock`；
3. 允许 `--provider pydantic-ai-testmodel`；
4. 默认 provider 必须保持当前 `llm-check` 的既有行为；
5. 使用 TASK-0055 的 `create_llm_reviewer()` 创建 reviewer；
6. 在 `llm-check` 中处理 unsupported provider 错误；
7. 更新 `llm-check` 相关测试；
8. 更新 provider factory 相关测试；
9. 更新 CLI 文档；
10. 更新 LLM provider 使用文档；
11. 更新架构文档；
12. 更新 `PROJECT_STATE.md`；
13. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许接入真实 OpenAI / Anthropic / Gemini / DeepSeek / Qwen / 本地模型 API；
2. 不允许读取 `.env`；
3. 不允许要求用户提供 API key；
4. 不允许新增 secret resolver；
5. 不允许新增真实 provider 配置；
6. 不允许新增 `content-review review --provider`；
7. 不允许新增 `content-review review --enable-llm`；
8. 不允许新增 `content-review batch --provider`；
9. 不允许修改 `content-review review` 默认行为；
10. 不允许修改 `content-review batch` 默认行为；
11. 不允许把 LLM 结果合并进主 `ReviewResult`；
12. 不允许把 LLM findings 合并进 Markdown report；
13. 不允许修改 quality gate 行为；
14. 不允许修改 deterministic review 输出结构；
15. 不允许新增 API / MCP / GUI；
16. 不允许引入 LangChain / CrewAI；
17. 不允许让测试访问外部网络；
18. 不允许让测试依赖真实模型调用；
19. 不允许把 unsupported provider 静默 fallback 到 mock；
20. 不允许删除或弱化现有 `llm-check` smoke check 行为。

---

## 5. 需要修改的文件

预计修改以下文件：

```text
src/content_review_engine/cli.py
src/content_review_engine/llm/smoke_check.py
tests/test_llm_smoke_check.py
tests/test_cli.py
docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前项目中已有更合适的测试文件或 helper 文件，可以沿用现有结构。

如果 `llm-check` 的 provider 选择逻辑可以完全在 `cli.py` 中完成，则可以不修改 `smoke_check.py`。

但必须避免把 provider factory 逻辑复制到 CLI 中；CLI 应调用 `create_llm_reviewer()`，而不是手动判断并实例化 provider。

---

## 6. 实现要求

### 6.1 CLI 参数

给 `content-review llm-check` 新增参数：

```bash
--provider <provider-name>
```

支持的 provider name：

```text
mock
pydantic-ai-testmodel
```

推荐默认值：

```text
pydantic-ai-testmodel
```

但是如果当前 `llm-check` 的既有默认行为不是 `pydantic-ai-testmodel`，则必须以当前既有行为为准，不能改变默认用户体验。

也就是说：

```bash
content-review llm-check
```

在本任务前后应保持用户可见行为兼容。

---

### 6.2 Provider 创建

`llm-check` 必须通过 TASK-0055 中已有的 factory 创建 reviewer：

```python
create_llm_reviewer(provider)
```

不允许在 CLI 中写类似下面的重复逻辑：

```python
if provider == "mock":
    reviewer = MockLLMReviewer()
elif provider == "pydantic-ai-testmodel":
    reviewer = PydanticAITestModelReviewer()
```

provider 选择逻辑应集中在 factory 中。

---

### 6.3 Smoke Check Request

`llm-check` 仍应使用现有 smoke check request 构造逻辑，例如：

```python
build_llm_smoke_check_request()
```

不得为不同 provider 创建完全不同的请求模型。

不同 provider 应消费同一个 `LLMReviewRequest`。

---

### 6.4 Smoke Check Result

`llm-check` 仍应渲染现有 smoke check result。

如果当前已有：

```python
render_llm_smoke_check_result()
```

应继续复用。

允许在输出中增加 provider 信息，例如：

```text
Provider: pydantic-ai-testmodel
```

或：

```text
Provider: mock
```

但必须保证测试固定输出，避免快照不稳定。

---

### 6.5 Unsupported Provider

如果用户运行：

```bash
content-review llm-check --provider openai
```

或：

```bash
content-review llm-check --provider pydantic-ai
```

应返回清晰错误。

错误信息至少包含：

1. unknown provider name；
2. supported provider names。

示例：

```text
Unsupported LLM reviewer provider: openai. Supported providers: mock, pydantic-ai-testmodel.
```

CLI 应返回非零退出码。

不允许静默 fallback 到 mock。

---

### 6.6 不改变正式审计流程

以下命令的默认行为不能改变：

```bash
content-review review ...
content-review batch ...
```

本任务只允许扩展：

```bash
content-review llm-check
```

不允许在正式审计流程中启用 LLM。

---

### 6.7 不引入真实 Provider 配置

本任务不新增：

```text
API key
model name
base URL
temperature
timeout
provider config file
.env loading
secret resolver
```

provider 参数只允许是当前两个测试 provider name。

真实 provider 配置留到后续任务。

---

## 7. 测试要求

需要新增或更新测试，至少覆盖以下内容：

### 7.1 llm-check 默认行为

测试：

```bash
content-review llm-check
```

仍然成功运行，并且保持当前默认 provider 行为。

### 7.2 显式 pydantic-ai-testmodel provider

测试：

```bash
content-review llm-check --provider pydantic-ai-testmodel
```

应成功运行。

需要验证：

1. exit code 为 0；
2. 输出包含 smoke check 成功信息；
3. 输出可以包含 provider name；
4. 不需要 API key；
5. 不访问外部网络。

### 7.3 显式 mock provider

测试：

```bash
content-review llm-check --provider mock
```

应成功运行。

需要验证：

1. exit code 为 0；
2. 输出包含 smoke check 成功信息；
3. 输出可以包含 provider name；
4. 返回结果结构合法；
5. 不需要 API key；
6. 不访问外部网络。

### 7.4 unsupported provider

测试：

```bash
content-review llm-check --provider openai
```

应失败。

需要验证：

1. exit code 非 0；
2. 错误信息包含 `openai`；
3. 错误信息包含 `mock`；
4. 错误信息包含 `pydantic-ai-testmodel`；
5. 不发生真实网络请求；
6. 不 fallback 到 mock。

### 7.5 不影响 review / batch

需要保留或新增测试，证明：

```bash
content-review review ...
content-review batch ...
```

默认行为不变。

### 7.6 不影响 factory

运行已有 factory 测试，确保：

```bash
uv run pytest tests/test_llm_provider_factory.py
```

仍然通过。

---

## 8. 文档更新要求

需要更新以下文档：

```text
docs/CLI.md
docs/LLM_PROVIDER_USAGE.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

### 8.1 docs/CLI.md

补充 `llm-check` 用法：

```bash
content-review llm-check
content-review llm-check --provider pydantic-ai-testmodel
content-review llm-check --provider mock
```

并说明：

1. `llm-check` 是独立 LLM smoke check；
2. 它不读取 Markdown；
3. 它不需要 profile；
4. 它不改变正式审计流程；
5. 当前 provider 只支持测试 provider。

### 8.2 docs/LLM_PROVIDER_USAGE.md

补充：

1. `llm-check --provider` 如何使用；
2. `mock` 的用途；
3. `pydantic-ai-testmodel` 的用途；
4. 二者都不需要真实 API key；
5. unsupported provider 会明确失败；
6. 真实 provider 仍未接入。

### 8.3 docs/ARCHITECTURE.md

补充 `llm-check` 当前调用路径：

```text
CLI llm-check
        ↓
create_llm_reviewer(provider)
        ↓
LLMReviewer
        ↓
LLMReviewRequest
        ↓
LLMReviewResult
```

并明确：

1. 这是 smoke check 路径；
2. 不是正式内容审计路径；
3. `review` / `batch` 默认不启用 LLM。

### 8.4 PROJECT_STATE.md

更新当前状态：

```text
TASK-0056 completed:
Added provider selection for content-review llm-check using the LLM reviewer provider factory.
```

同时明确尚未完成：

```text
No real LLM API provider.
No review/batch LLM CLI integration.
No API key loading.
No LLM result merge into main ReviewResult.
No Markdown report integration.
```

### 8.5 CHANGELOG.md

新增 TASK-0056 变更记录。

---

## 9. 验收标准

本任务完成后必须满足：

1. `content-review llm-check` 保持默认可运行；
2. `content-review llm-check --provider pydantic-ai-testmodel` 可运行；
3. `content-review llm-check --provider mock` 可运行；
4. `llm-check` provider 创建通过 `create_llm_reviewer()`；
5. unsupported provider 返回明确错误；
6. unsupported provider 不会 fallback 到 mock；
7. unsupported provider 返回非零退出码；
8. 不需要真实 API key；
9. 不读取 `.env`；
10. 不访问外部网络；
11. 不修改 `content-review review` 默认行为；
12. 不修改 `content-review batch` 默认行为；
13. 不合并 LLM result 到主 `ReviewResult`；
14. 不修改 Markdown report；
15. 不修改 quality gate；
16. 不新增 API / MCP / GUI；
17. 文档同步更新；
18. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

本任务最容易出现的风险是 Agent 顺手把 provider 选择扩展到正式审计流程。

必须避免以下问题：

1. 不要新增 `content-review review --provider`；
2. 不要新增 `content-review review --enable-llm`；
3. 不要新增 `content-review batch --provider`；
4. 不要读取 Markdown 进行 LLM 审计；
5. 不要把 LLM findings 合并进主结果；
6. 不要修改 JSON / Markdown report；
7. 不要修改 quality gate；
8. 不要接真实 API；
9. 不要读取 API key；
10. 不要读取 `.env`；
11. 不要把 unsupported provider fallback 到 mock；
12. 不要复制 factory 的 provider 判断逻辑。

本任务的本质是：

```text
让 llm-check 可以通过 factory 显式选择已有测试 provider。
```

而不是：

```text
让正式内容审计流程支持 LLM provider。
```

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_smoke_check.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_pydantic_ai_provider.py
uv run pytest tests/test_cli.py
uv run pytest
```

如果项目中存在 lint / format 命令，也可以运行，但不得因此引入大范围无关格式化改动。

---

