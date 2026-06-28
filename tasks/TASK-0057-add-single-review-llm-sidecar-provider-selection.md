# TASK-0057: Add Single Review LLM Sidecar Provider Selection

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

TASK-0056 已经让 `content-review llm-check` 可以通过 `--provider` 显式选择 `mock` 或 `pydantic-ai-testmodel`。

但是当前已有的单文件 LLM sidecar 流程还缺少显式 provider 选择能力。后续如果要让 CLI、API、MCP 复用同一套 LLM provider 边界，就不应该继续依赖分散的 config-driven 或手动实例化路径。

本任务的目标是：

> 在不改变正式审计主结果的前提下，让单文件 review 的 LLM sidecar 流程可以通过 provider name 选择当前已有测试 provider。

本任务只扩展单文件 LLM sidecar 路径，不扩展 batch，不接入真实 LLM API，不合并主 `ReviewResult`，不修改 Markdown Report，不修改 Quality Gate。

---

## 2. 任务目标

为已有的单文件 LLM sidecar 输出流程新增 provider 选择能力。

本任务完成后，单文件 review 在启用已有 LLM sidecar 输出时，应可以指定 provider。

示例形式如下，具体参数名以当前项目已有 CLI 命名为准：

```bash
content-review review input.md --profile profile.yml --llm-sidecar-output llm.json --llm-provider mock
```

以及：

```bash
content-review review input.md --profile profile.yml --llm-sidecar-output llm.json --llm-provider pydantic-ai-testmodel
```

其中：

1. `mock` 使用 `MockLLMReviewer`；
2. `pydantic-ai-testmodel` 使用 `PydanticAITestModelReviewer`；
3. provider 创建必须通过 `create_llm_reviewer()`；
4. unsupported provider 必须返回清晰错误；
5. 不允许访问真实 LLM API；
6. 不允许要求 API key；
7. LLM 结果仍然只写入 sidecar output；
8. 不允许合并进主 `ReviewResult`；
9. 不允许影响 Markdown Report；
10. 不允许影响 Quality Gate。

如果当前项目中单文件 sidecar 的参数名不是 `--llm-sidecar-output`，请沿用现有参数名，不要为了本任务重命名现有 CLI 参数。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 给已有单文件 LLM sidecar 流程新增 provider 选择参数；
2. 推荐参数名为 `--llm-provider`；
3. 支持 `--llm-provider mock`；
4. 支持 `--llm-provider pydantic-ai-testmodel`；
5. 通过 `create_llm_reviewer()` 创建 reviewer；
6. 保持未显式传入 `--llm-provider` 时的既有 sidecar 行为；
7. unsupported provider 返回清晰错误；
8. unsupported provider 不 fallback；
9. 更新单文件 sidecar 相关测试；
10. 更新 CLI 相关测试；
11. 更新 provider factory 相关回归测试；
12. 更新 CLI 文档；
13. 更新 LLM provider 使用文档；
14. 更新架构文档；
15. 更新 `PROJECT_STATE.md`；
16. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许接入真实 OpenAI / Anthropic / Gemini / DeepSeek / Qwen / 本地模型 API；
2. 不允许读取 `.env`；
3. 不允许要求用户提供 API key；
4. 不允许新增 secret resolver；
5. 不允许新增真实 provider 配置；
6. 不允许新增 batch LLM sidecar provider selection；
7. 不允许新增 `content-review batch --llm-provider`；
8. 不允许新增正式 `--enable-llm` 审计模式；
9. 不允许让 `content-review review` 默认启用 LLM；
10. 不允许修改 `content-review review` 在未启用 LLM sidecar 时的默认行为；
11. 不允许修改 `content-review batch` 默认行为；
12. 不允许修改 `content-review llm-check` 用户可见行为；
13. 不允许把 LLM 结果合并进主 `ReviewResult`；
14. 不允许把 LLM findings 合并进 Markdown report；
15. 不允许修改 JSON report schema；
16. 不允许修改 Markdown report 结构；
17. 不允许修改 quality gate 行为；
18. 不允许修改 deterministic review 输出结构；
19. 不允许新增 API / MCP / GUI；
20. 不允许引入 LangChain / CrewAI；
21. 不允许让测试访问外部网络；
22. 不允许让测试依赖真实模型调用；
23. 不允许把 unsupported provider 静默 fallback 到 mock。

---

## 5. 需要修改的文件

预计修改以下文件：

```text
src/content_review_engine/cli.py
src/content_review_engine/llm/runner.py
src/content_review_engine/llm/sidecar.py
tests/test_cli.py
tests/test_llm_sidecar.py
tests/test_llm_provider_factory.py
docs/CLI.md
docs/LLM_PROVIDER_USAGE.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前项目没有 `sidecar.py` 或 `test_llm_sidecar.py`，请沿用已有文件结构。

如果单文件 LLM sidecar 逻辑目前集中在 `cli.py` 或其他模块中，可以在现有结构中做最小修改，但必须避免把 provider 判断逻辑复制到 CLI 中。

CLI 层应调用 `create_llm_reviewer()`，而不是手动实例化 `MockLLMReviewer` 或 `PydanticAITestModelReviewer`。

---

## 6. 实现要求

### 6.1 CLI 参数

给单文件 `content-review review` 的已有 LLM sidecar 路径新增参数：

```bash
--llm-provider <provider-name>
```

支持的 provider name：

```text
mock
pydantic-ai-testmodel
```

该参数只用于已有 LLM sidecar output。

如果用户没有启用 LLM sidecar，却传入：

```bash
content-review review input.md --profile profile.yml --llm-provider mock
```

推荐返回清晰错误，例如：

```text
--llm-provider can only be used with LLM sidecar output.
```

这样可以避免用户误以为主 review 流程已经启用了 LLM。

如果项目已有更一致的 CLI 参数校验方式，请沿用现有风格。

---

### 6.2 默认行为

未显式传入 `--llm-provider` 时，已有单文件 LLM sidecar 行为必须保持兼容。

也就是说：

```bash
content-review review input.md --profile profile.yml --llm-sidecar-output llm.json
```

在本任务前后的用户可见行为应保持一致。

如果当前 sidecar 默认使用 config-driven provider，则继续保持 config-driven provider。

如果当前 sidecar 默认使用 mock provider，则继续保持 mock provider。

本任务只新增显式 provider name 路径，不改变默认路径。

---

### 6.3 Provider 创建

显式传入 `--llm-provider` 时，必须通过 TASK-0055 中已有的 factory 创建 reviewer：

```python
create_llm_reviewer(provider_name)
```

不允许在 CLI 中写：

```python
if provider == "mock":
    reviewer = MockLLMReviewer()
elif provider == "pydantic-ai-testmodel":
    reviewer = PydanticAITestModelReviewer()
```

provider 选择逻辑必须集中在 `create_llm_reviewer()`。

---

### 6.4 LLM Sidecar Output

LLM 结果仍然只写入 sidecar output。

不得改变主审计输出。

不得改变现有 `ReviewResult` schema。

不得改变现有 JSON / Markdown report 输出。

本任务只允许让 sidecar 使用不同 provider 产生 LLM sidecar result。

---

### 6.5 Unsupported Provider

如果用户运行：

```bash
content-review review input.md --profile profile.yml --llm-sidecar-output llm.json --llm-provider openai
```

或：

```bash
content-review review input.md --profile profile.yml --llm-sidecar-output llm.json --llm-provider pydantic-ai
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

不允许 fallback 到 mock。

---

### 6.6 不改变正式审计主流程

以下命令的默认行为不能改变：

```bash
content-review review input.md --profile profile.yml
content-review batch input_dir --profile profile.yml
content-review llm-check
```

本任务只允许扩展：

```bash
content-review review input.md --profile profile.yml --<existing-llm-sidecar-output-option> llm.json --llm-provider <provider>
```

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

需要新增或更新测试，至少覆盖以下内容。

### 7.1 单文件 sidecar 默认行为

测试已有单文件 sidecar 命令在不传 `--llm-provider` 时仍然成功运行，并保持当前默认行为。

示例：

```bash
content-review review input.md --profile profile.yml --llm-sidecar-output llm.json
```

具体命令参数以当前项目已有 sidecar 参数为准。

### 7.2 显式 mock provider

测试：

```bash
content-review review input.md --profile profile.yml --llm-sidecar-output llm.json --llm-provider mock
```

应成功运行。

需要验证：

1. exit code 为 0；
2. sidecar 文件被创建；
3. sidecar 内容是合法 LLM result；
4. provider 路径使用 factory；
5. 不需要 API key；
6. 不访问外部网络；
7. 主 `ReviewResult` 输出不包含 LLM findings。

### 7.3 显式 pydantic-ai-testmodel provider

测试：

```bash
content-review review input.md --profile profile.yml --llm-sidecar-output llm.json --llm-provider pydantic-ai-testmodel
```

应成功运行。

需要验证：

1. exit code 为 0；
2. sidecar 文件被创建；
3. sidecar 内容是合法 LLM result；
4. 不需要 API key；
5. 不访问外部网络；
6. 主 `ReviewResult` 输出不包含 LLM findings。

### 7.4 unsupported provider

测试：

```bash
content-review review input.md --profile profile.yml --llm-sidecar-output llm.json --llm-provider openai
```

应失败。

需要验证：

1. exit code 非 0；
2. 错误信息包含 `openai`；
3. 错误信息包含 `mock`；
4. 错误信息包含 `pydantic-ai-testmodel`；
5. 不创建 sidecar 文件，或不写入成功结果；
6. 不发生真实网络请求；
7. 不 fallback 到 mock。

### 7.5 provider without sidecar

测试：

```bash
content-review review input.md --profile profile.yml --llm-provider mock
```

应失败或返回清晰错误。

推荐错误信息：

```text
--llm-provider can only be used with LLM sidecar output.
```

如果项目已有统一参数校验风格，请沿用现有风格。

### 7.6 不影响 review 默认行为

测试：

```bash
content-review review input.md --profile profile.yml
```

默认行为不变，输出中不包含 LLM sidecar 内容，也不包含 LLM findings。

### 7.7 不影响 batch

测试：

```bash
content-review batch input_dir --profile profile.yml
```

默认行为不变。

本任务不新增 batch provider selection。

### 7.8 不影响 llm-check

运行已有测试，确保：

```bash
uv run pytest tests/test_llm_smoke_check.py
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

补充单文件 LLM sidecar provider 用法。

示例：

```bash
content-review review input.md --profile profile.yml --llm-sidecar-output llm.json --llm-provider mock
content-review review input.md --profile profile.yml --llm-sidecar-output llm.json --llm-provider pydantic-ai-testmodel
```

如果当前 sidecar output 参数不是 `--llm-sidecar-output`，请使用项目实际参数名。

文档中必须明确：

1. `--llm-provider` 只影响 LLM sidecar output；
2. 它不会让主 `ReviewResult` 合并 LLM findings；
3. 它不会改变 Markdown report；
4. 它不会改变 quality gate；
5. 当前只支持测试 provider；
6. 真实 provider 仍未接入。

### 8.2 docs/LLM_PROVIDER_USAGE.md

补充：

1. 单文件 sidecar 如何选择 provider；
2. `mock` 的用途；
3. `pydantic-ai-testmodel` 的用途；
4. 二者都不需要真实 API key；
5. unsupported provider 会明确失败；
6. 真实 provider 仍未接入；
7. batch sidecar provider selection 仍属于后续任务。

### 8.3 docs/ARCHITECTURE.md

补充单文件 sidecar 当前调用路径：

```text
CLI review with LLM sidecar
        ↓
create_llm_reviewer(provider)
        ↓
LLMReviewer
        ↓
LLMReviewRequest
        ↓
LLMReviewResult
        ↓
sidecar JSON output
```

并明确：

1. 这是 sidecar 路径；
2. 不是主 ReviewResult 合并路径；
3. `review` 默认不启用 LLM；
4. `batch` provider selection 仍属于后续任务；
5. API / MCP / GUI 仍未接入。

### 8.4 PROJECT_STATE.md

更新当前状态：

```text
TASK-0057 completed:
Added provider selection for single-file LLM sidecar output using the LLM reviewer provider factory.
```

同时明确尚未完成：

```text
No real LLM API provider.
No batch LLM sidecar provider selection.
No review/batch main LLM result merge.
No API key loading.
No LLM result merge into main ReviewResult.
No Markdown report integration.
```

### 8.5 CHANGELOG.md

新增 TASK-0057 变更记录。

---

## 9. 验收标准

本任务完成后必须满足：

1. 单文件 LLM sidecar 支持显式 provider selection；
2. 支持 `mock`；
3. 支持 `pydantic-ai-testmodel`；
4. provider 创建通过 `create_llm_reviewer()`；
5. 未传 `--llm-provider` 时保持既有 sidecar 行为；
6. unsupported provider 返回明确错误；
7. unsupported provider 不会 fallback 到 mock；
8. unsupported provider 返回非零退出码；
9. 不需要真实 API key；
10. 不读取 `.env`；
11. 不访问外部网络；
12. 不修改 `content-review review` 默认行为；
13. 不修改 `content-review batch` 默认行为；
14. 不修改 `content-review llm-check` 用户可见行为；
15. 不新增 batch provider selection；
16. 不合并 LLM result 到主 `ReviewResult`；
17. 不修改 JSON / Markdown report；
18. 不修改 quality gate；
19. 不新增 API / MCP / GUI；
20. 文档同步更新；
21. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

本任务最容易出现的风险是 Agent 顺手把 provider 选择扩展成正式 LLM 审计模式。

必须避免以下问题：

1. 不要新增 `review --enable-llm`；
2. 不要让 `review` 默认启用 LLM；
3. 不要新增 batch provider selection；
4. 不要读取 API key；
5. 不要读取 `.env`；
6. 不要接真实 provider；
7. 不要修改主 `ReviewResult`；
8. 不要修改 Markdown report；
9. 不要修改 quality gate；
10. 不要把 LLM findings 混入 deterministic findings；
11. 不要复制 factory provider 判断逻辑；
12. 不要把 unsupported provider fallback 到 mock。

本任务的本质是：

```text
让已有单文件 LLM sidecar 输出可以通过 factory 选择测试 provider。
```

而不是：

```text
让正式内容审计流程支持 LLM provider。
```

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_pydantic_ai_provider.py
uv run pytest tests/test_llm_smoke_check.py
uv run pytest
```

如果项目中存在更具体的 sidecar 测试文件，也请运行，例如：

```bash
uv run pytest tests/test_llm_sidecar.py
```

如果项目中存在 lint / format 命令，也可以运行，但不得因此引入大范围无关格式化改动。

---

