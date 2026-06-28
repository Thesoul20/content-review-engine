# TASK-0054: Add PydanticAI TestModel Reviewer Provider

## 1. 背景

当前项目已经完成确定性内容审计主链路，包括 Markdown 读取、Profile 加载、规则审计、单文件 CLI、批量 CLI、JSON / Markdown 报告输出，以及 Quality Gate / CI 门禁。

LLM 语义审计阶段目前已经完成了以下基础能力：

1. `LLMReviewRequest`
2. `LLMReviewer` provider interface
3. `MockLLMReviewer`
4. `LLMReviewResult`
5. LLM semantic review runner
6. LLM sidecar output
7. batch LLM sidecar output
8. `content-review llm-check` smoke check

其中，TASK-0053 已经新增了独立的 `content-review llm-check` 命令，用于验证 PydanticAI 测试模型链路是否可以运行。

但是当前项目仍然缺少一个真正实现 `LLMReviewer` 接口的 PydanticAI provider。

本任务的目标是在不接入真实 LLM API 的前提下，新增一个基于 PydanticAI TestModel 的 reviewer provider，使项目可以通过统一的 `LLMReviewer` 接口运行 PydanticAI 测试模型。

本任务只做测试模型 provider，不做真实 provider，不接入正式 CLI 审计流程，不修改主 ReviewResult / Markdown Report。

---

## 2. 任务目标

新增一个 PydanticAI TestModel reviewer provider，使其能够：

1. 实现现有 `LLMReviewer` interface；
2. 接收现有 `LLMReviewRequest`；
3. 使用 PydanticAI 的 TestModel / 测试模型机制运行；
4. 返回现有 `LLMReviewResult`；
5. 支持稳定、可测试、无真实 API key 依赖的 LLM provider 测试；
6. 与现有 smoke check 逻辑保持边界清晰；
7. 不影响确定性规则审计、CLI review、batch review、report、quality gate 的现有行为。

本任务完成后，项目应具备：

```text
LLMReviewRequest
        ↓
LLMReviewer interface
        ↓
PydanticAITestModelReviewer
        ↓
LLMReviewResult
```

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 新增 PydanticAI TestModel reviewer provider；
2. 让该 provider 实现已有 `LLMReviewer` interface；
3. 将 `LLMReviewRequest` 转换为 PydanticAI agent 可处理的测试输入；
4. 将 PydanticAI 测试输出转换为已有 `LLMReviewResult`；
5. 添加必要的结构化 prompt / system prompt / instruction 构造函数；
6. 添加 provider 层单元测试；
7. 添加 provider 错误处理测试；
8. 更新 LLM provider 使用文档；
9. 更新架构文档、项目状态与 changelog；
10. 根据需要从 `src/content_review_engine/llm/__init__.py` 导出新 provider。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许接入 OpenAI / Anthropic / Gemini / DeepSeek / Qwen 等真实 LLM API；
2. 不允许要求用户提供 API key；
3. 不允许读取 `.env`；
4. 不允许新增真实 provider 配置；
5. 不允许修改 `content-review review` 的默认行为；
6. 不允许新增 `--enable-llm`、`--llm-provider`、`--llm-model` 等正式 CLI 审计参数；
7. 不允许把 LLM 结果合并进主 `ReviewResult`；
8. 不允许把 LLM findings 合并进现有 Markdown report；
9. 不允许修改 deterministic review 的结果结构；
10. 不允许修改 quality gate 行为；
11. 不允许新增 API / MCP / GUI；
12. 不允许引入 LangChain / CrewAI 等额外大框架；
13. 不允许让测试依赖外部网络；
14. 不允许让测试依赖真实模型调用；
15. 不允许删除或弱化 TASK-0053 中已有的 `llm-check` smoke check 行为。

---

## 5. 需要修改的文件

预计新增或修改以下文件：

```text
src/content_review_engine/llm/pydantic_ai_provider.py
src/content_review_engine/llm/__init__.py
tests/test_llm_pydantic_ai_provider.py
docs/LLM_PROVIDER_USAGE.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前项目中已有更合适的命名，例如：

```text
src/content_review_engine/llm/pydanticai.py
src/content_review_engine/llm/providers/pydantic_ai.py
```

可以沿用现有结构，但必须保持 LLM provider 层独立，不得把 provider 代码写入 CLI、runner、report 或 core 模块。

---

## 6. 实现要求

### 6.1 Provider 命名

新增 provider 建议命名为：

```python
PydanticAITestModelReviewer
```

该命名需要明确表达：

1. 它基于 PydanticAI；
2. 它使用 TestModel；
3. 它不是生产真实 LLM provider；
4. 它实现 reviewer 行为。

不建议命名为：

```python
PydanticAIReviewer
```

因为这个名称容易让人误以为它已经是正式真实模型 provider。

---

### 6.2 Provider Interface

`PydanticAITestModelReviewer` 必须实现现有 `LLMReviewer` interface。

如果当前 interface 是同步接口，则保持同步实现。

如果当前 interface 是异步接口，则保持异步实现。

不得为了本任务修改 `LLMReviewer` interface 的既有签名，除非现有测试明确暴露接口设计缺陷，并且修改范围极小、兼容现有 mock provider。

---

### 6.3 输入转换

Provider 应接收现有 `LLMReviewRequest`。

不得新增一套与 `LLMReviewRequest` 平行的请求模型。

允许新增内部 helper，例如：

```python
build_pydantic_ai_review_prompt(request: LLMReviewRequest) -> str
```

或：

```python
build_pydantic_ai_review_messages(request: LLMReviewRequest) -> list[...]
```

但这些 helper 必须属于 provider 层，不应进入 core review engine。

---

### 6.4 输出转换

Provider 必须返回现有 `LLMReviewResult`。

不得直接返回 PydanticAI 原始响应。

不得返回裸字符串。

不得返回不受项目数据模型约束的 dict。

如果 PydanticAI TestModel 返回的是固定测试文本，provider 需要将其转换为合法的 `LLMReviewResult`。

本任务中允许 provider 默认返回空 findings 的 `LLMReviewResult`，但测试中必须证明：

1. 返回值类型正确；
2. schema version 正确；
3. request metadata 能被保留或合理映射；
4. findings 字段结构兼容现有序列化逻辑。

---

### 6.5 错误处理

如果 PydanticAI 调用失败，provider 应将异常包装为项目已有 LLM error hierarchy 中的错误类型，例如：

```python
LLMProviderError
```

或当前项目中已有的等价错误类型。

不得让 PydanticAI 的底层异常直接泄漏到 CLI 或 runner 层。

测试中需要覆盖至少一个 provider error path。

---

### 6.6 与 TASK-0053 smoke check 的关系

TASK-0053 的 `content-review llm-check` 是独立 smoke check 命令。

本任务新增的是 provider 层能力。

两者可以共享少量 helper，但必须保持边界清晰：

```text
llm-check
  用于 CLI smoke check

PydanticAITestModelReviewer
  用于 LLMReviewer provider interface
```

不要求本任务修改 `content-review llm-check` 的用户可见行为。

如果需要复用 TASK-0053 中已有的 request 构造函数，可以复用，但不得让 provider 依赖 CLI 模块。

---

### 6.7 依赖要求

本任务不得引入新的真实 LLM SDK。

如果 PydanticAI 已经在 TASK-0053 中作为依赖引入，则直接复用已有依赖。

如果当前项目尚未声明 PydanticAI 依赖，但 TASK-0053 代码已经实际使用 PydanticAI，则可以补齐最小必要依赖声明。

不得新增以下依赖：

```text
langchain
crewai
openai
anthropic
google-generativeai
litellm
```

---

### 6.8 不影响现有审计行为

本任务完成后，以下命令的默认输出和行为不应变化：

```bash
content-review review ...
content-review batch ...
content-review llm-check
```

除非文档中明确只是新增了 provider 说明。

---

## 7. 测试要求

新增测试文件：

```text
tests/test_llm_pydantic_ai_provider.py
```

测试至少覆盖以下内容：

1. `PydanticAITestModelReviewer` 实现 `LLMReviewer` interface；
2. provider 可以接收一个合法 `LLMReviewRequest`；
3. provider 返回合法 `LLMReviewResult`；
4. 返回结果包含正确 schema version；
5. 返回结果可以被现有 serializer 序列化；
6. provider 不需要真实 API key；
7. provider 不访问网络；
8. provider error path 会包装为项目已有 LLM provider error；
9. provider 不改变 `MockLLMReviewer` 行为；
10. provider 不改变现有 `llm-check` CLI 行为。

可以额外运行：

```bash
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

1. `PydanticAITestModelReviewer` 是测试模型 provider；
2. 它不需要真实 API key；
3. 它不代表真实 LLM provider 已经接入；
4. 它主要用于验证 provider interface 与 PydanticAI 集成方式；
5. 它与 `content-review llm-check` 的区别。

### 8.2 docs/ARCHITECTURE.md

需要补充 LLM provider 层当前结构：

```text
LLMReviewRequest
        ↓
LLMReviewer
        ↓
MockLLMReviewer / PydanticAITestModelReviewer
        ↓
LLMReviewResult
```

并明确：

1. 真实 provider 仍未接入；
2. CLI 正式 LLM 审计仍未接入；
3. LLM result 与主 ReviewResult 的合并仍属于后续任务。

### 8.3 docs/DATA_MODELS.md

如本任务没有新增数据模型，则只需补充 provider 如何消费现有模型。

如果新增内部辅助模型，必须说明这些模型是 provider 内部实现细节，不属于公开 schema。

### 8.4 PROJECT_STATE.md

更新当前状态，说明：

```text
TASK-0054 completed:
Added PydanticAI TestModel reviewer provider implementing LLMReviewer.
```

同时明确尚未完成：

```text
No real LLM API provider.
No CLI LLM review integration.
No LLM result merge into main ReviewResult.
No Markdown report integration.
```

### 8.5 CHANGELOG.md

新增 TASK-0054 的变更记录。

---

## 9. 验收标准

本任务完成后必须满足：

1. 存在一个明确命名的 `PydanticAITestModelReviewer`；
2. 该 reviewer 实现现有 `LLMReviewer` interface；
3. 该 reviewer 能接收 `LLMReviewRequest`；
4. 该 reviewer 能返回 `LLMReviewResult`；
5. 不需要真实 API key；
6. 不访问外部网络；
7. 单元测试覆盖正常路径和错误路径；
8. 不影响现有 deterministic review；
9. 不影响现有 batch review；
10. 不影响现有 Markdown report；
11. 不影响现有 quality gate；
12. 不影响 `content-review llm-check` 现有行为；
13. 文档明确说明该 provider 仍然是 TestModel provider，不是生产真实 LLM provider；
14. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

本任务最容易出现的风险是 Agent 顺手把 PydanticAI 接成正式真实 provider。

必须避免以下问题：

1. 不要引入 API key；
2. 不要读取环境变量；
3. 不要让 provider 访问外部网络；
4. 不要让测试依赖真实模型；
5. 不要把 provider 接进 `content-review review`；
6. 不要把 LLM findings 合并进主报告；
7. 不要把 PydanticAI 原始响应暴露给上层；
8. 不要修改确定性审计输出；
9. 不要扩大到 API / MCP / GUI；
10. 不要引入 LangChain / CrewAI。

本任务的本质是：

```text
把 TASK-0053 中验证过的 PydanticAI 测试链路，
向项目自己的 LLMReviewer provider interface 前进一步。
```

而不是：

```text
完成真实 LLM 审计产品能力。
```

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_pydantic_ai_provider.py
uv run pytest tests/test_llm_smoke_check.py
uv run pytest tests/test_cli.py
uv run pytest
```

如果项目中存在 lint / format 命令，也可以运行，但不得因此引入大范围无关格式化改动。

---
