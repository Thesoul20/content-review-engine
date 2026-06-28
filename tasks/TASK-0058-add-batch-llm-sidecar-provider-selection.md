# TASK-0058: Add Batch LLM Sidecar Provider Selection

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

TASK-0057 已经让单文件 review 的 LLM sidecar 输出流程支持 `--llm-provider`，可以通过 `create_llm_reviewer()` 显式选择：

1. `mock`
2. `pydantic-ai-testmodel`

但是当前 batch LLM sidecar 输出流程还没有显式 provider selection。为了让单文件与批量 sidecar 行为保持一致，并为后续 API / MCP / 真实 provider 接入保留统一边界，本任务需要给 batch LLM sidecar 流程也新增 `--llm-provider` 支持。

本任务只扩展 batch LLM sidecar 路径，不接入真实 LLM API，不合并主 `ReviewResult`，不修改 JSON / Markdown Report，不修改 Quality Gate，不新增 API / MCP / GUI。

---

## 2. 任务目标

为已有的 batch LLM sidecar 输出流程新增 provider selection。

本任务完成后，batch review 在启用已有 LLM sidecar 输出时，应可以指定 provider。

示例形式如下，具体参数名以当前项目已有 batch LLM sidecar CLI 命名为准：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output llm.json --llm-provider mock
```

以及：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output llm.json --llm-provider pydantic-ai-testmodel
```

其中：

1. `mock` 使用 `MockLLMReviewer`；
2. `pydantic-ai-testmodel` 使用 `PydanticAITestModelReviewer`；
3. provider 创建必须通过 `create_llm_reviewer()`；
4. unsupported provider 必须返回清晰错误；
5. 不允许访问真实 LLM API；
6. 不允许要求 API key；
7. LLM 结果仍然只写入 batch sidecar output；
8. 不允许合并进主 `ReviewResult`；
9. 不允许影响 Markdown Report；
10. 不允许影响 Quality Gate；
11. 不允许改变 batch 在未启用 LLM sidecar 时的默认行为。

如果当前项目中 batch LLM sidecar 的参数名不是 `--enable-llm` / `--llm-output`，请沿用现有参数名，不要为了本任务重命名已有 CLI 参数。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 给已有 batch LLM sidecar 流程新增 provider 选择参数；
2. 参数名应与单文件 sidecar 保持一致，优先使用 `--llm-provider`；
3. 支持 `--llm-provider mock`；
4. 支持 `--llm-provider pydantic-ai-testmodel`；
5. 通过 `create_llm_reviewer()` 创建 reviewer；
6. 保持未显式传入 `--llm-provider` 时的既有 batch sidecar 行为；
7. unsupported provider 返回清晰错误；
8. unsupported provider 不 fallback；
9. 如果未启用 batch LLM sidecar 却传入 `--llm-provider`，返回清晰错误；
10. 更新 batch sidecar 相关测试；
11. 更新 CLI 相关测试；
12. 更新 provider factory 回归测试；
13. 更新 CLI 文档；
14. 更新 LLM provider 使用文档；
15. 更新架构文档；
16. 更新 `PROJECT_STATE.md`；
17. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许接入真实 OpenAI / Anthropic / Gemini / DeepSeek / Qwen / 本地模型 API；
2. 不允许读取 `.env`；
3. 不允许要求用户提供 API key；
4. 不允许新增 secret resolver；
5. 不允许新增真实 provider 配置；
6. 不允许修改单文件 sidecar 的用户可见行为；
7. 不允许修改 `content-review llm-check` 用户可见行为；
8. 不允许新增正式 LLM 主审计合并模式；
9. 不允许让 `content-review review` 默认启用 LLM；
10. 不允许让 `content-review batch` 默认启用 LLM；
11. 不允许修改 `content-review batch` 在未启用 LLM sidecar 时的默认行为；
12. 不允许把 LLM 结果合并进主 `ReviewResult`；
13. 不允许把 LLM findings 合并进 Markdown report；
14. 不允许修改 JSON report schema；
15. 不允许修改 Markdown report 结构；
16. 不允许修改 Quality Gate 行为；
17. 不允许修改 deterministic review 输出结构；
18. 不允许新增 API / MCP / GUI；
19. 不允许引入 LangChain / CrewAI；
20. 不允许让测试访问外部网络；
21. 不允许让测试依赖真实模型调用；
22. 不允许把 unsupported provider 静默 fallback 到 mock；
23. 不允许复制 factory 的 provider 判断逻辑。

---

## 5. 需要修改的文件

预计修改以下文件：

```text
src/content_review_engine/cli.py
tests/test_cli.py
tests/test_llm_sidecar.py
tests/test_llm_provider_factory.py
docs/CLI.md
docs/LLM_PROVIDER_USAGE.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前项目已经有 batch sidecar 专用测试文件，例如：

```text
tests/test_batch_llm_sidecar.py
tests/test_batch_cli.py
tests/test_batch_llm_output.py
```

请优先沿用现有测试结构。

如果 batch LLM sidecar 逻辑分散在其他模块中，可以做最小必要修改，但必须避免把 provider 判断逻辑写死在 CLI 中。

CLI 层应调用 `create_llm_reviewer()`，而不是手动实例化 `MockLLMReviewer` 或 `PydanticAITestModelReviewer`。

---

## 6. 实现要求

### 6.1 CLI 参数

给 batch LLM sidecar 路径新增参数：

```bash
--llm-provider <provider-name>
```

支持的 provider name：

```text
mock
pydantic-ai-testmodel
```

该参数只用于已有 batch LLM sidecar output。

如果用户没有启用 batch LLM sidecar，却传入：

```bash
content-review batch input_dir --profile profile.yml --llm-provider mock
```

应返回清晰错误。

推荐错误信息：

```text
--llm-provider can only be used with --enable-llm and --llm-output.
```

如果项目中单文件 sidecar 已经使用了类似错误信息，请与单文件保持一致。

---

### 6.2 默认行为

未显式传入 `--llm-provider` 时，已有 batch LLM sidecar 行为必须保持兼容。

也就是说：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output llm.json
```

在本任务前后的用户可见行为应保持一致。

如果当前 batch sidecar 默认使用 config-driven provider，则继续保持 config-driven provider。

如果当前 batch sidecar 默认使用 mock provider，则继续保持 mock provider。

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

### 6.4 Batch LLM Sidecar Output

LLM 结果仍然只写入 batch sidecar output。

不得改变主 batch review 输出。

不得改变现有 batch result schema。

不得改变现有 JSON / Markdown report 输出。

不得改变 quality gate 判断。

本任务只允许让 batch sidecar 使用不同 provider 产生 LLM sidecar result。

---

### 6.5 Unsupported Provider

如果用户运行：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output llm.json --llm-provider openai
```

或：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output llm.json --llm-provider pydanticai
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
content-review batch input_dir --profile profile.yml --enable-llm --llm-output llm.json --llm-provider <provider>
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

### 7.1 Batch sidecar 默认行为

测试已有 batch sidecar 命令在不传 `--llm-provider` 时仍然成功运行，并保持当前默认行为。

示例：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output llm.json
```

具体命令参数以当前项目已有 batch sidecar 参数为准。

### 7.2 显式 mock provider

测试：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output llm.json --llm-provider mock
```

应成功运行。

需要验证：

1. exit code 为 0；
2. batch sidecar 文件被创建；
3. sidecar 内容是合法 LLM batch sidecar result；
4. provider 路径使用 factory；
5. 不需要 API key；
6. 不访问外部网络；
7. 主 batch review result 不包含 LLM findings；
8. Markdown report 不包含 LLM findings；
9. Quality Gate 行为不受影响。

### 7.3 显式 pydantic-ai-testmodel provider

测试：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output llm.json --llm-provider pydantic-ai-testmodel
```

应成功运行。

需要验证：

1. exit code 为 0；
2. batch sidecar 文件被创建；
3. sidecar 内容是合法 LLM batch sidecar result；
4. 不需要 API key；
5. 不访问外部网络；
6. 主 batch review result 不包含 LLM findings；
7. Markdown report 不包含 LLM findings；
8. Quality Gate 行为不受影响。

### 7.4 Unsupported provider

测试：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output llm.json --llm-provider openai
```

应失败。

需要验证：

1. exit code 非 0；
2. 错误信息包含 `openai`；
3. 错误信息包含 `mock`；
4. 错误信息包含 `pydantic-ai-testmodel`；
5. 不创建 sidecar 成功结果；
6. 不发生真实网络请求；
7. 不 fallback 到 mock。

### 7.5 Provider without batch sidecar

测试：

```bash
content-review batch input_dir --profile profile.yml --llm-provider mock
```

应失败或返回清晰错误。

推荐错误信息：

```text
--llm-provider can only be used with --enable-llm and --llm-output.
```

如果项目已有统一参数校验风格，请沿用现有风格。

### 7.6 不影响 batch 默认行为

测试：

```bash
content-review batch input_dir --profile profile.yml
```

默认行为不变，输出中不包含 LLM sidecar 内容，也不包含 LLM findings。

### 7.7 不影响 single review

测试：

```bash
content-review review input.md --profile profile.yml
```

默认行为不变。

已有单文件 sidecar `--llm-provider` 行为仍然通过。

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

补充 batch LLM sidecar provider 用法。

示例：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output llm.json --llm-provider mock
content-review batch input_dir --profile profile.yml --enable-llm --llm-output llm.json --llm-provider pydantic-ai-testmodel
```

如果当前 batch sidecar output 参数不是 `--enable-llm` / `--llm-output`，请使用项目实际参数名。

文档中必须明确：

1. `--llm-provider` 只影响 LLM sidecar output；
2. 它不会让主 batch result 合并 LLM findings；
3. 它不会改变 Markdown report；
4. 它不会改变 quality gate；
5. 当前只支持测试 provider；
6. 真实 provider 仍未接入。

### 8.2 docs/LLM_PROVIDER_USAGE.md

补充：

1. batch sidecar 如何选择 provider；
2. `mock` 的用途；
3. `pydantic-ai-testmodel` 的用途；
4. 二者都不需要真实 API key；
5. unsupported provider 会明确失败；
6. 真实 provider 仍未接入；
7. 主 ReviewResult / BatchReviewResult 合并仍属于后续任务。

### 8.3 docs/ARCHITECTURE.md

补充 batch sidecar 当前调用路径：

```text
CLI batch with LLM sidecar
        ↓
create_llm_reviewer(provider)
        ↓
LLMReviewer
        ↓
LLMReviewRequest per reviewed file
        ↓
LLMReviewResult
        ↓
batch sidecar JSON output
```

并明确：

1. 这是 batch sidecar 路径；
2. 不是主 BatchReviewResult 合并路径；
3. `batch` 默认不启用 LLM；
4. API / MCP / GUI 仍未接入；
5. 真实 provider 仍未接入。

### 8.4 PROJECT_STATE.md

更新当前状态：

```text
TASK-0058 completed:
Added provider selection for batch LLM sidecar output using the LLM reviewer provider factory.
```

同时明确尚未完成：

```text
No real LLM API provider.
No review/batch main LLM result merge.
No API key loading.
No LLM result merge into main ReviewResult or BatchReviewResult.
No Markdown report integration.
No API / MCP / GUI integration.
```

### 8.5 CHANGELOG.md

新增 TASK-0058 变更记录。

---

## 9. 验收标准

本任务完成后必须满足：

1. batch LLM sidecar 支持显式 provider selection；
2. 支持 `mock`；
3. 支持 `pydantic-ai-testmodel`；
4. provider 创建通过 `create_llm_reviewer()`；
5. 未传 `--llm-provider` 时保持既有 batch sidecar 行为；
6. unsupported provider 返回明确错误；
7. unsupported provider 不会 fallback 到 mock；
8. unsupported provider 返回非零退出码；
9. `--llm-provider` without batch sidecar 返回清晰错误；
10. 不需要真实 API key；
11. 不读取 `.env`；
12. 不访问外部网络；
13. 不修改 `content-review review` 默认行为；
14. 不修改 `content-review batch` 默认行为；
15. 不修改 `content-review llm-check` 用户可见行为；
16. 不合并 LLM result 到主 `ReviewResult`；
17. 不合并 LLM result 到主 `BatchReviewResult`;
18. 不修改 JSON / Markdown report；
19. 不修改 quality gate；
20. 不新增 API / MCP / GUI；
21. 文档同步更新；
22. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

本任务最容易出现的风险是 Agent 顺手把 batch provider selection 扩展成正式 LLM 审计模式。

必须避免以下问题：

1. 不要让 batch 默认启用 LLM；
2. 不要读取 API key；
3. 不要读取 `.env`；
4. 不要接真实 provider；
5. 不要修改主 `BatchReviewResult`；
6. 不要修改主 `ReviewResult`；
7. 不要修改 Markdown report；
8. 不要修改 quality gate；
9. 不要把 LLM findings 混入 deterministic findings；
10. 不要复制 factory provider 判断逻辑；
11. 不要把 unsupported provider fallback 到 mock；
12. 不要改动单文件 sidecar 已有行为；
13. 不要改动 llm-check 已有行为。

本任务的本质是：

```text
让已有 batch LLM sidecar 输出可以通过 factory 选择测试 provider。
```

而不是：

```text
让正式 batch 审计结果合并 LLM provider。
```

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_pydantic_ai_provider.py
uv run pytest tests/test_llm_smoke_check.py
uv run pytest tests/test_llm_sidecar.py
uv run pytest
```

如果存在 batch sidecar 专用测试文件，也请运行，例如：

```bash
uv run pytest tests/test_batch_llm_sidecar.py
```

如果项目中存在 lint / format 命令，也可以运行，但不得因此引入大范围无关格式化改动。

---

