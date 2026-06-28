# TASK-0055: Add LLM Reviewer Provider Factory

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

TASK-0054 已经新增了 `PydanticAITestModelReviewer`，使项目可以通过现有 `LLMReviewer` interface 使用 PydanticAI TestModel，而不需要真实 API key，也不访问外部网络。

但是当前项目仍然缺少一个统一的 provider 创建入口。后续如果要让 CLI、API、MCP 或真实 provider 选择不同 LLM reviewer，就不应该在各处手动 import 和实例化具体 provider。

本任务的目标是新增一个轻量、可测试、无真实 API 依赖的 LLM reviewer provider factory / registry，用于根据 provider name 创建当前已有的 reviewer：

1. `mock`
2. `pydantic-ai-testmodel`

本任务只做 provider factory，不做 CLI 参数接入，不做真实 provider，不做主报告合并。

---

## 2. 任务目标

新增一个 LLM reviewer provider factory，使项目具备统一的 provider 创建边界。

本任务完成后，项目应支持类似以下内部调用：

```python
reviewer = create_llm_reviewer("mock")
```

以及：

```python
reviewer = create_llm_reviewer("pydantic-ai-testmodel")
```

并返回对应的 `LLMReviewer` 实现。

本任务的目标不是让用户在 CLI 中选择 provider，而是先把 provider 创建逻辑从未来 CLI / API / MCP 层中抽离出来。

本任务完成后的结构应大致为：

```text
LLM provider name
        ↓
create_llm_reviewer(...)
        ↓
MockLLMReviewer / PydanticAITestModelReviewer
        ↓
LLMReviewer interface
        ↓
LLMReviewResult
```

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 新增 LLM reviewer provider factory / registry；
2. 支持通过 provider name 创建 `MockLLMReviewer`；
3. 支持通过 provider name 创建 `PydanticAITestModelReviewer`；
4. 定义当前支持的 provider name 常量或枚举；
5. 定义 unsupported provider 的错误处理；
6. 添加 provider factory 单元测试；
7. 更新 LLM provider 使用文档；
8. 更新架构文档；
9. 更新数据模型或 provider 文档；
10. 更新 `PROJECT_STATE.md`；
11. 更新 `CHANGELOG.md`；
12. 根据需要从 `src/content_review_engine/llm/__init__.py` 导出 factory。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许接入真实 OpenAI / Anthropic / Gemini / DeepSeek / Qwen / 本地模型 API；
2. 不允许读取 `.env`；
3. 不允许要求用户提供 API key；
4. 不允许新增 secret resolver；
5. 不允许新增正式 provider 配置文件；
6. 不允许新增 `--llm-provider` CLI 参数；
7. 不允许新增 `--enable-llm` CLI 参数；
8. 不允许修改 `content-review review` 默认行为；
9. 不允许修改 `content-review batch` 默认行为；
10. 不允许修改 `content-review llm-check` 用户可见行为；
11. 不允许把 LLM 结果合并进主 `ReviewResult`；
12. 不允许把 LLM findings 合并进 Markdown report；
13. 不允许修改 quality gate 行为；
14. 不允许新增 API / MCP / GUI；
15. 不允许引入 LangChain / CrewAI；
16. 不允许让测试访问外部网络；
17. 不允许让测试依赖真实模型调用。

---

## 5. 需要修改的文件

预计新增或修改以下文件：

```text
src/content_review_engine/llm/factory.py
src/content_review_engine/llm/__init__.py
tests/test_llm_provider_factory.py
docs/LLM_PROVIDER_USAGE.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前项目中已有更合适的命名，例如：

```text
src/content_review_engine/llm/providers.py
src/content_review_engine/llm/registry.py
```

可以沿用现有结构，但必须保持 provider factory 位于 LLM 层，不得写入 CLI、core、report、serializer 或 review runner 模块。

---

## 6. 实现要求

### 6.1 Factory 命名

建议新增文件：

```text
src/content_review_engine/llm/factory.py
```

建议新增函数：

```python
create_llm_reviewer(provider: str) -> LLMReviewer
```

如果当前项目更偏好显式命名，也可以使用：

```python
create_llm_reviewer_provider(provider: str) -> LLMReviewer
```

但必须保持命名清晰，表达“创建 LLM reviewer provider”的含义。

---

### 6.2 Provider Name

建议支持以下 provider name：

```text
mock
pydantic-ai-testmodel
```

可以定义常量：

```python
LLM_PROVIDER_MOCK = "mock"
LLM_PROVIDER_PYDANTIC_AI_TESTMODEL = "pydantic-ai-testmodel"
```

也可以定义一个只包含当前支持项的集合：

```python
SUPPORTED_LLM_REVIEWER_PROVIDERS = {
    "mock",
    "pydantic-ai-testmodel",
}
```

不建议使用容易误导的名称：

```text
pydantic-ai
```

因为这会让人误以为真实 PydanticAI provider 已经完成。

---

### 6.3 创建行为

`create_llm_reviewer("mock")` 应返回：

```python
MockLLMReviewer()
```

`create_llm_reviewer("pydantic-ai-testmodel")` 应返回：

```python
PydanticAITestModelReviewer()
```

如果 provider name 前后带空格，可以选择是否 normalize。

推荐行为：

```python
provider = provider.strip().lower()
```

但必须通过测试固定下来。

---

### 6.4 Unsupported Provider Error

如果传入不支持的 provider name，例如：

```text
openai
pydantic-ai
unknown
""
```

factory 不应静默 fallback 到 mock。

必须抛出明确错误。

可以新增错误类型：

```python
UnsupportedLLMProviderError
```

该错误建议继承现有 LLM error hierarchy 中的基础错误类型，例如：

```python
LLMReviewError
```

或者当前项目已有的等价 LLM error 类型。

错误信息应包含：

1. unknown provider name；
2. currently supported provider names。

示例：

```text
Unsupported LLM reviewer provider: openai. Supported providers: mock, pydantic-ai-testmodel.
```

不得把 unsupported provider 当成真实 API provider 尝试调用。

---

### 6.5 不引入配置系统

本任务不实现配置文件、不读取环境变量、不新增 settings 对象。

如果确实需要最小化配置结构，也只能是 provider name 字符串，不允许扩展到 API key、model name、base URL、temperature、timeout 等真实 provider 参数。

这些内容应留到后续真实 provider 任务。

---

### 6.6 与现有 Provider 的关系

本任务不应修改 `MockLLMReviewer` 与 `PydanticAITestModelReviewer` 的内部行为。

factory 只负责实例化，不负责：

1. 构造 `LLMReviewRequest`；
2. 运行 review；
3. 处理 sidecar output；
4. 渲染报告；
5. 处理 CLI 参数；
6. 管理 API key。

---

### 6.7 导出要求

如项目已有 `src/content_review_engine/llm/__init__.py` 导出策略，则应导出：

```python
create_llm_reviewer
SUPPORTED_LLM_REVIEWER_PROVIDERS
UnsupportedLLMProviderError
```

具体导出项可根据实现调整，但应该让后续 CLI / API / MCP 层可以通过 LLM package 的公开入口使用 factory。

---

## 7. 测试要求

新增测试文件：

```text
tests/test_llm_provider_factory.py
```

测试至少覆盖以下内容：

1. `create_llm_reviewer("mock")` 返回 `MockLLMReviewer`；
2. `create_llm_reviewer("pydantic-ai-testmodel")` 返回 `PydanticAITestModelReviewer`；
3. 返回对象满足 `LLMReviewer` interface / protocol；
4. provider name 支持大小写或空格 normalize，如果实现了 normalize；
5. unsupported provider 会抛出明确错误；
6. unsupported provider 错误信息包含 unknown provider name；
7. unsupported provider 错误信息包含 supported providers；
8. factory 不需要 API key；
9. factory 不读取 `.env`；
10. factory 不访问外部网络；
11. factory 不改变 `MockLLMReviewer` 行为；
12. factory 不改变 `PydanticAITestModelReviewer` 行为；
13. factory 不改变 `llm-check` 现有行为；
14. factory 不改变 `review` / `batch` CLI 默认行为。

可以额外运行：

```bash
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_pydantic_ai_provider.py
uv run pytest tests/test_llm_smoke_check.py
uv run pytest tests/test_cli.py
```

最终必须运行完整测试：

```bash
uv run pytest
```

---

## 8. 文档更新要求

需要更新以下文档：

```text
docs/LLM_PROVIDER_USAGE.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

### 8.1 docs/LLM_PROVIDER_USAGE.md

需要说明：

1. 当前支持的 reviewer provider name；
2. `mock` 的含义；
3. `pydantic-ai-testmodel` 的含义；
4. `pydantic-ai-testmodel` 不需要真实 API key；
5. `pydantic-ai-testmodel` 不代表真实 PydanticAI provider 已完成；
6. `create_llm_reviewer()` 是内部 provider 创建入口；
7. 当前尚未提供 CLI provider 选择参数。

### 8.2 docs/ARCHITECTURE.md

需要补充 LLM provider 创建层：

```text
provider name
        ↓
create_llm_reviewer()
        ↓
MockLLMReviewer / PydanticAITestModelReviewer
        ↓
LLMReviewer
        ↓
LLMReviewResult
```

并明确：

1. provider factory 属于 LLM 层；
2. CLI / API / MCP 后续可以复用该入口；
3. 真实 provider 仍未接入；
4. LLM result 与主 ReviewResult 的合并仍属于后续任务。

### 8.3 docs/DATA_MODELS.md

如果本任务没有新增公开数据模型，只需说明 factory 不改变 `LLMReviewRequest` / `LLMReviewResult` schema。

如果新增 `UnsupportedLLMProviderError`，应在错误类型部分简要说明。

### 8.4 PROJECT_STATE.md

更新当前状态，说明：

```text
TASK-0055 completed:
Added LLM reviewer provider factory for mock and PydanticAI TestModel reviewers.
```

同时明确尚未完成：

```text
No real LLM API provider.
No CLI provider selection.
No API key loading.
No LLM result merge into main ReviewResult.
No Markdown report integration.
```

### 8.5 CHANGELOG.md

新增 TASK-0055 的变更记录。

---

## 9. 验收标准

本任务完成后必须满足：

1. 存在统一的 LLM reviewer provider factory；
2. factory 可以创建 `MockLLMReviewer`；
3. factory 可以创建 `PydanticAITestModelReviewer`；
4. factory 返回对象满足 `LLMReviewer` interface；
5. unsupported provider 会抛出明确错误；
6. unsupported provider 不会静默 fallback；
7. factory 不需要 API key；
8. factory 不读取 `.env`；
9. factory 不访问外部网络；
10. 不影响 `content-review review` 默认行为；
11. 不影响 `content-review batch` 默认行为；
12. 不影响 `content-review llm-check` 用户可见行为；
13. 不影响现有 sidecar output 行为；
14. 不影响 quality gate；
15. 不接入真实 LLM API；
16. 不新增 CLI LLM provider 参数；
17. 文档明确说明 factory 当前只支持 mock 与 PydanticAI TestModel provider；
18. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

本任务最容易出现的风险是 Agent 顺手把 provider factory 扩展成真实 provider 配置系统。

必须避免以下问题：

1. 不要读取 API key；
2. 不要读取 `.env`；
3. 不要新增 OpenAI / Anthropic / Gemini / DeepSeek provider；
4. 不要新增 base URL、model name、temperature、timeout 配置；
5. 不要在 CLI 中暴露 provider 选择参数；
6. 不要修改现有 CLI 默认行为；
7. 不要让 unknown provider fallback 到 mock；
8. 不要把 provider factory 写进 CLI 模块；
9. 不要把 provider factory 写进 core review engine；
10. 不要让测试访问网络；
11. 不要合并 LLM result 到主报告。

本任务的本质是：

```text
为已有 LLM reviewers 提供统一创建入口。
```

而不是：

```text
完成正式 LLM 审计配置系统。
```

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_pydantic_ai_provider.py
uv run pytest tests/test_llm_smoke_check.py
uv run pytest tests/test_cli.py
uv run pytest
```

如果项目中存在 lint / format 命令，也可以运行，但不得因此引入大范围无关格式化改动。

---

