# TASK-0036: Add LLM Semantic Review Runner

## 1. 背景

当前项目已经完成确定性内容审计引擎、单文件与批量 CLI、JSON / Markdown 报告输出、Quality Gate / CI 能力，并且已经开始进入 LLM 语义审计层。

上一阶段 `TASK-0035` 已完成 LLM provider 边界与 mock reviewer，当前 LLM 层基础结构为：

```text
LLMReviewRequest
        ↓
LLMReviewer provider interface
        ↓
MockLLMReviewer
        ↓
LLMReviewResult
```

但是目前还缺少一个独立的 runner 层来承接“构造 / 接收 LLMReviewRequest、调用 LLMReviewer、返回 LLMReviewResult”的执行流程。

因此，本任务需要新增一个 **LLM semantic review runner**，作为后续接入 CLI、真实 LLM provider、报告输出、API / MCP 的中间层。

本任务仍然只使用已有的 `LLMReviewer` interface 和 `MockLLMReviewer`，不接入真实 LLM 框架。

---

## 2. 任务目标

新增 LLM 语义审计 runner，使项目具备一个可测试、可注入、可扩展的 LLM review 执行层。

本任务完成后，应支持：

1. 通过 runner 接收已有的 `LLMReviewRequest`；
2. 通过注入的 `LLMReviewer` 调用 LLM 审计 provider；
3. 返回结构化的 `LLMReviewResult`；
4. 在测试中使用 `MockLLMReviewer` 验证 runner 行为；
5. 保持当前确定性 review engine、CLI、JSON 输出、Markdown report 行为不变；
6. 为后续 CLI LLM 审计接入和真实 LLM provider 接入做好边界准备。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 新增 LLM semantic review runner；
2. 将 runner 放在 `src/content_review_engine/llm/` 包内；
3. runner 通过依赖注入接收 `LLMReviewer`；
4. runner 调用已有 `LLMReviewer` interface；
5. runner 返回已有 `LLMReviewResult`；
6. 根据现有模型结构补充必要的轻量 helper；
7. 在 `src/content_review_engine/llm/__init__.py` 中导出 runner；
8. 新增 runner 相关测试；
9. 更新 LLM 架构文档；
10. 更新 LLM 数据模型文档；
11. 更新 `PROJECT_STATE.md`；
12. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许接入真实 LLM provider；
2. 不允许引入 PydanticAI；
3. 不允许引入 OpenAI SDK；
4. 不允许引入 Anthropic SDK；
5. 不允许新增外部运行时依赖；
6. 不允许新增 CLI 参数，例如 `--enable-llm`；
7. 不允许修改当前 CLI review 行为；
8. 不允许修改当前 JSON review result 输出结构；
9. 不允许修改当前 Markdown report 输出结构；
10. 不允许将 LLM findings 合并进现有 deterministic `ReviewResult`；
11. 不允许改变当前确定性规则审计结果；
12. 不允许改变 quality gate 行为；
13. 不允许新增 API、MCP、GUI 相关能力；
14. 不允许把 LLM runner 写进 CLI、reports 或 core deterministic review engine 中；
15. 不允许在 runner 中硬编码任何真实 provider、模型名、API key 或网络请求逻辑。

---

## 5. 需要修改的文件

预计需要新增或修改以下文件：

```text
src/content_review_engine/llm/runner.py
src/content_review_engine/llm/__init__.py
tests/test_llm_runner.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

如果任务卡文件尚不存在，也可以新增：

```text
tasks/TASK-0036-llm-semantic-review-runner.md
```

除非测试或现有结构确实要求，否则不要修改 CLI、reports、core review engine、batch review 或 deterministic rules 相关文件。

---

## 6. 实现要求

### 6.1 Runner 位置

新增文件：

```text
src/content_review_engine/llm/runner.py
```

该文件用于承载 LLM semantic review runner。

---

### 6.2 Runner 设计

推荐实现一个轻量 runner，例如：

```python
class LLMReviewRunner:
    def __init__(self, reviewer: LLMReviewer) -> None:
        ...

    def run(self, request: LLMReviewRequest) -> LLMReviewResult:
        ...
```

实际命名可以根据现有代码风格调整，但必须满足：

1. runner 依赖已有 `LLMReviewer` interface；
2. runner 不直接依赖 `MockLLMReviewer`；
3. runner 不直接依赖真实 provider；
4. runner 不执行网络请求；
5. runner 不读取环境变量；
6. runner 不读取 API key；
7. runner 不修改输入 request；
8. runner 返回 `LLMReviewResult`；
9. runner 的行为应可通过 mock reviewer 完整测试。

---

### 6.3 Provider 调用规则

runner 应通过注入的 reviewer 完成调用。

示例逻辑：

```python
result = reviewer.review(request)
return result
```

如果现有 `LLMReviewer` 使用不同方法名，应遵循现有 interface。

不得绕过 provider interface。

---

### 6.4 错误处理规则

runner 不应吞掉 provider 层错误。

如果已有错误类型包括：

```text
LLMReviewError
LLMProviderError
LLMResponseValidationError
```

则 runner 应遵循现有错误层级。

推荐行为：

1. provider 抛出的 LLM 相关错误应原样向上传播；
2. runner 不应把所有异常粗暴转换成普通 `Exception`；
3. runner 不应隐藏失败原因；
4. runner 不应打印错误到 stdout / stderr；
5. runner 不应直接退出进程。

如果项目已有错误处理约定，应优先遵循现有约定。

---

### 6.5 类型与导出要求

需要在 LLM 包中导出 runner。

修改：

```text
src/content_review_engine/llm/__init__.py
```

导出新增的 runner 类型或函数，例如：

```python
from content_review_engine.llm.runner import LLMReviewRunner
```

并确保包级导入可用。

---

### 6.6 与当前确定性审计的关系

本任务只新增 LLM runner 层，不改变现有 deterministic review flow。

本任务完成后，现有命令仍应保持原行为，例如：

```bash
content-review review ...
content-review batch ...
```

不应出现任何 LLM 相关运行时行为变化。

---

### 6.7 与未来任务的关系

本任务完成后，后续任务可以继续推进：

```text
TASK-0037: Add CLI flags for LLM review
TASK-0038: Add real PydanticAI provider
TASK-0039: Add report integration for LLM findings
```

本任务只为这些后续能力建立 runner 边界。

---

## 7. 测试要求

新增测试文件：

```text
tests/test_llm_runner.py
```

测试至少覆盖以下场景：

### 7.1 Runner 调用 reviewer

验证 runner 能够：

1. 接收 `LLMReviewRequest`；
2. 调用注入的 `LLMReviewer`；
3. 返回 `LLMReviewResult`。

可以使用 `MockLLMReviewer` 或测试专用 fake reviewer。

---

### 7.2 返回 configured result

如果 `MockLLMReviewer` 支持配置返回值，需要测试：

1. 给 mock reviewer 提供一个预设 `LLMReviewResult`；
2. runner 调用后返回该结果；
3. 返回对象或序列化结果符合预期。

---

### 7.3 默认空结果

如果 `MockLLMReviewer` 默认返回空结果，需要测试：

1. runner 使用默认 mock reviewer；
2. 返回空 `LLMReviewResult`；
3. schema version 仍为现有 LLM result schema version，例如 `llm-review-result.v1`；
4. findings 为空。

---

### 7.4 错误传播

新增一个 fake reviewer，让它抛出已有 LLM 错误类型，例如：

```python
LLMProviderError
```

验证：

1. runner 不吞掉错误；
2. runner 不转换为无关异常；
3. 调用方可以捕获原始 LLM 错误类型。

---

### 7.5 不影响现有测试

运行完整测试：

```bash
uv run pytest
```

确保所有现有 deterministic review、CLI、batch、report、quality gate 测试仍然通过。

---

## 8. 文档更新要求

### 8.1 更新 docs/ARCHITECTURE.md

需要补充 LLM runner 在架构中的位置。

建议说明：

```text
LLMReviewRequest
        ↓
LLMReviewRunner
        ↓
LLMReviewer provider interface
        ↓
LLMReviewResult
```

并说明：

1. runner 是执行层；
2. provider 是模型边界；
3. mock reviewer 用于测试；
4. real provider 将在后续任务中实现；
5. CLI integration 将在后续任务中实现；
6. 当前 deterministic review flow 不受影响。

---

### 8.2 更新 docs/DATA_MODELS.md

需要补充或调整 LLM 相关数据流说明：

1. `LLMReviewRequest` 是 runner 输入；
2. `LLMReviewResult` 是 runner 输出；
3. `LLMReviewer` 是 provider interface；
4. `LLMReviewRunner` 负责编排调用；
5. runner 不改变当前 `ReviewResult` schema；
6. runner 不改变当前 JSON report schema。

---

### 8.3 更新 PROJECT_STATE.md

需要记录：

1. `TASK-0036` 已完成；
2. 新增 LLM semantic review runner；
3. 当前 LLM 层具备 provider boundary + mock reviewer + runner；
4. 真实 LLM provider 尚未接入；
5. CLI LLM 行为尚未接入；
6. report integration 尚未完成。

---

### 8.4 更新 CHANGELOG.md

需要在 changelog 中记录：

1. 新增 LLM semantic review runner；
2. 新增 runner 测试；
3. 更新 LLM 架构与数据模型文档；
4. 未引入真实 provider、CLI 行为变化或报告变化。

---

## 9. 验收标准

本任务完成后应满足：

1. 存在独立的 LLM semantic review runner；
2. runner 位于 `src/content_review_engine/llm/` 包内；
3. runner 使用已有 `LLMReviewer` provider interface；
4. runner 接收 `LLMReviewRequest`；
5. runner 返回 `LLMReviewResult`；
6. runner 可通过 mock reviewer 测试；
7. runner 不接入真实 LLM provider；
8. runner 不修改 CLI；
9. runner 不修改现有 deterministic review JSON 输出；
10. runner 不修改 Markdown report 输出；
11. runner 不修改 quality gate 行为；
12. 新增 `tests/test_llm_runner.py`；
13. 完整测试 `uv run pytest` 通过；
14. `docs/ARCHITECTURE.md` 已更新；
15. `docs/DATA_MODELS.md` 已更新；
16. `PROJECT_STATE.md` 已更新；
17. `CHANGELOG.md` 已更新。

---

## 10. 风险与注意事项

### 10.1 防止范围膨胀

本任务很容易被扩展成 CLI LLM integration 或真实 provider integration。

不要在本任务中实现：

```text
--enable-llm
--llm-provider
--llm-model
PydanticAI provider
OpenAI provider
Anthropic provider
LLM findings in Markdown report
LLM findings in deterministic ReviewResult
```

这些都属于后续任务。

---

### 10.2 防止破坏确定性审计

当前确定性审计结果必须保持不变。

本任务不应导致：

1. 当前 review JSON 多出 LLM 字段；
2. 当前 Markdown report 多出 LLM section；
3. 当前 CLI 默认触发 LLM；
4. 当前 quality gate 统计 LLM finding；
5. 当前 deterministic finding 顺序变化。

---

### 10.3 防止抽象过度设计

runner 应保持轻量。

不要提前设计复杂能力，例如：

1. 多 provider routing；
2. retry policy；
3. token accounting；
4. prompt template registry；
5. streaming；
6. async job queue；
7. cache；
8. tracing；
9. telemetry；
10. cost tracking。

这些能力后续可以单独建 TASK。

---

## 11. 完成后需要运行的命令

至少运行：

```bash
uv run pytest
```

如果需要单独验证 LLM runner 测试，可以先运行：

```bash
uv run pytest tests/test_llm_runner.py
```

建议最终仍运行完整测试：

```bash
uv run pytest
```

