# TASK-0067: Wire Prompt Contract and Output Validation into PydanticAI Provider

## 1. 背景

当前项目已经完成：

```text
TASK-0061: Add LLM Provider Secret Resolver
TASK-0062: Wire LLM Secret Resolver into LLM Check
TASK-0063: Enable Real PydanticAI Provider Construction
TASK-0064: Add Optional Live PydanticAI Runtime Smoke Check
TASK-0065: Add LLM Semantic Review Prompt Contract
TASK-0066: Add LLM Semantic Review Output Validation
```

目前 LLM 层已经具备：

1. secret resolver；
2. `llm-check` secret preflight；
3. PydanticAI provider construction check；
4. optional live runtime smoke check；
5. LLM semantic review prompt contract；
6. `llm-semantic-review-output.v1` 输出约定；
7. LLM semantic review output parser / validator；
8. `ValidatedLLMSemanticReviewOutput` / `ValidatedLLMSemanticFinding`；
9. parse error / validation error；
10. prompt contract 与 output validation 都还没有接入 PydanticAI provider execution。

上一任务只完成了 raw output 的解析与校验。

本任务的目标是把下面这条链路接起来：

```text
LLMReviewRequest
  ↓
prompt contract
  ↓
PydanticAI provider execution
  ↓
raw model output
  ↓
output validation
  ↓
ValidatedLLMSemanticReviewOutput
```

本任务只在 PydanticAI provider 层完成 semantic review execution wiring。

本任务不接入 `content-review review`，不接入 `content-review batch`，不生成正式 `LLMReviewResult`，不修改主审计结果 schema，不修改 sidecar metadata。

---

## 2. 任务目标

本任务需要完成：

1. 让 `PydanticAIReviewer` 可以基于 `LLMReviewRequest` 构建 semantic review prompt；
2. 让 `PydanticAIReviewer` 调用 PydanticAI agent / model 得到 raw output；
3. 让 `PydanticAIReviewer` 将 raw output 交给 output validation layer；
4. 返回 `ValidatedLLMSemanticReviewOutput`；
5. 通过 fake / stub / monkeypatch 测试 provider execution；
6. 覆盖 provider 返回合法 JSON 的成功路径；
7. 覆盖 provider 返回 fenced JSON 的成功路径；
8. 覆盖 provider 返回非法 JSON 的 parse failure；
9. 覆盖 provider 返回字段不合法 JSON 的 validation failure；
10. 确保错误信息不泄露 secret；
11. 确保普通测试不访问真实网络；
12. 确保普通测试不要求真实 API key；
13. 更新文档、项目状态和 changelog。

完成后，PydanticAI provider 应该具备一条可测试的 semantic review execution pipeline，但该 pipeline 仍然只返回 validated semantic output，不进入主审计流程。

---

## 3. 本任务允许做什么

本任务允许：

1. 修改 `src/content_review_engine/llm/pydanticai.py`；
2. 修改或新增 PydanticAI provider 的 semantic review execution 方法；
3. 调用 `build_llm_semantic_review_prompt_contract()` 或当前项目已有等价 prompt builder；
4. 调用 `parse_llm_semantic_review_output()` 或当前项目已有等价 output validator；
5. 新增 provider-level semantic review result helper；
6. 增加 provider execution 测试；
7. 通过 fake / stub / monkeypatch 模拟 PydanticAI 返回；
8. 小范围更新 `llm/models.py`，仅限必要的 provider-level validated execution 类型；
9. 小范围更新 `llm/errors.py`，仅限必要的 provider execution error；
10. 更新 `llm/__init__.py` 导出；
11. 更新 PydanticAI provider 测试；
12. 更新 output validation / prompt contract 回归测试；
13. 更新 provider usage 文档；
14. 更新 data models 文档；
15. 更新 architecture 文档；
16. 更新 `PROJECT_STATE.md`；
17. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许：

1. 不允许接入 `content-review review` 主流程；
2. 不允许接入 `content-review batch` 主流程；
3. 不允许新增 `review` 或 `batch` 的 LLM CLI 开关；
4. 不允许生成正式 `LLMReviewResult`；
5. 不允许把 validated semantic output 转换成 `LLMReviewResult`；
6. 不允许把 LLM finding 合并进 `ReviewResult`；
7. 不允许修改 `ReviewResult` schema；
8. 不允许修改 `BatchReviewResult` schema；
9. 不允许修改 `LLMReviewResult` schema，除非当前接口无法维持类型兼容且必须做极小范围调整；
10. 不允许修改 sidecar metadata；
11. 不允许修改 deterministic review engine 行为；
12. 不允许修改 `llm-check` live / construction 行为；
13. 不允许新增 plaintext API key 参数；
14. 不允许读取 `.env`；
15. 不允许读取 `os.environ`；
16. 不允许让 provider factory 读取环境变量；
17. 不允许让 reserved providers 变成可创建；
18. 不允许让普通测试访问真实网络；
19. 不允许让普通测试依赖真实 API key；
20. 不允许新增 API、MCP、Skill、GUI、Supabase、用户系统或商业化能力；
21. 不允许引入 LangChain、CrewAI 或其他大型框架。

---

## 5. 需要修改的文件

预计会新增或修改以下文件：

```text
src/content_review_engine/llm/pydanticai.py
src/content_review_engine/llm/prompt_contract.py
src/content_review_engine/llm/output_validation.py
src/content_review_engine/llm/models.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/__init__.py

tests/test_llm_pydanticai_provider.py
tests/test_llm_prompt_contract.py
tests/test_llm_output_validation.py
tests/test_llm_provider_usage_docs.py

docs/LLM_PROVIDER_USAGE.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前仓库已有更合适的文件名或模块结构，应优先遵守现有结构，不要为了本任务大规模重命名文件。

---

## 6. 实现要求

### 6.1 provider execution 方法要求

在 `PydanticAIReviewer` 中新增 semantic review execution 方法。

推荐命名：

```python
run_semantic_review(request: LLMReviewRequest) -> ValidatedLLMSemanticReviewOutput
```

或遵守当前项目已有命名风格。

该方法应完成：

```text
LLMReviewRequest
  ↓
build prompt contract
  ↓
call PydanticAI
  ↓
get raw output string
  ↓
parse / validate output
  ↓
return ValidatedLLMSemanticReviewOutput
```

注意：

1. 本方法不返回正式 `LLMReviewResult`；
2. 本方法不写入 sidecar；
3. 本方法不接入 CLI；
4. 本方法不修改 deterministic review result；
5. 本方法不应读取环境变量；
6. 本方法不应读取 `.env`；
7. 本方法不应输出 secret。

---

### 6.2 prompt contract 接入要求

provider execution 必须复用 `TASK-0065` 中新增的 prompt contract。

推荐调用：

```python
build_llm_semantic_review_prompt_contract(request)
```

或当前项目已有等价 helper。

要求：

1. 不在 provider 内部重复拼接另一套 prompt；
2. 不绕过 prompt contract；
3. system prompt / user prompt 应来自统一 builder；
4. provider execution 不应改变 prompt contract 的 schema version；
5. provider execution 不应把 secret 注入 prompt；
6. provider execution 不应把 provider diagnostic 信息注入 prompt。

---

### 6.3 output validation 接入要求

provider execution 必须复用 `TASK-0066` 中新增的 output validation layer。

推荐调用：

```python
parse_llm_semantic_review_output(raw_output)
```

或当前项目已有等价 helper。

要求：

1. 不在 provider 中重复实现 JSON parsing；
2. 不在 provider 中重复实现字段校验；
3. validator 抛出的 parse / validation error 应保持原有语义；
4. provider 可以包装错误，但不得丢失 parse / validation 的核心原因；
5. 错误信息不得包含完整 raw output；
6. 错误信息不得泄露 secret-like value。

---

### 6.4 PydanticAI 调用边界要求

provider execution 可以调用 PydanticAI agent / model，但普通测试必须通过 fake / stub / monkeypatch 隔离。

实现时应支持测试注入，例如：

1. 注入 fake agent；
2. 注入 fake run callable；
3. 注入 test model；
4. monkeypatch PydanticAI call；
5. 使用当前项目已有 PydanticAI TestModel 封装。

普通测试不得真实访问网络。

如果当前 `PydanticAIReviewer` 已经有 internal agent / model wrapper，应复用它，不要新增并行 provider implementation。

---

### 6.5 raw output 提取要求

PydanticAI 返回对象可能不是纯字符串。

provider execution 应集中处理 raw text extraction。

要求：

1. 如果 PydanticAI 返回字符串，直接使用；
2. 如果返回对象有 `output`、`data`、`content` 或当前项目已使用的字段，应按当前依赖版本的实际返回结构处理；
3. 如果无法提取文本，应返回稳定 provider execution error；
4. 错误信息不得包含 secret；
5. 不要把这个逻辑散落在多个模块。

如当前项目已有 `run_live_check()` 的返回提取逻辑，应复用或抽出 helper，避免重复。

---

### 6.6 错误处理要求

如果需要新增错误类型，可以在 `llm/errors.py` 中新增：

```python
LLMProviderExecutionError
LLMSemanticReviewExecutionError
```

或使用当前 error hierarchy 中已有合适类型。

要求：

1. provider execution error 与 output parse / validation error 可区分；
2. PydanticAI 调用失败时返回 provider execution error；
3. output parse 失败时返回 parse error；
4. output validation 失败时返回 validation error；
5. 错误消息稳定；
6. 错误消息不得包含完整 secret；
7. 错误消息不得包含完整 raw output；
8. 不应输出 traceback 到普通测试输出或文档示例。

---

### 6.7 secret 安全要求

provider 中已经可以持有 in-memory secret。

本任务必须继续保证：

1. secret 不进入 prompt；
2. secret 不进入 raw output；
3. secret 不进入 error message；
4. secret 不进入 validated output；
5. secret 不进入 docs 示例；
6. secret 不进入 stdout / stderr；
7. tests 中必须断言 secret 不泄露。

---

### 6.8 测试隔离要求

普通测试不得访问真实网络。

必须使用以下方式之一：

1. fake PydanticAI agent；
2. fake async / sync run function；
3. monkeypatch；
4. stub reviewer dependency；
5. PydanticAI TestModel；
6. 当前项目已有测试封装。

普通测试不得依赖：

1. 真实 OpenAI API key；
2. 真实 Anthropic API key；
3. 真实 Gemini API key；
4. 真实 DeepSeek API key；
5. 真实 Qwen API key；
6. 开发者本机环境变量；
7. 外部网络。

---

### 6.9 async / sync 要求

如果 PydanticAI 调用是 async，应避免在本任务中引入不稳定事件循环行为。

可选策略：

1. provider execution 暴露 sync wrapper；
2. provider execution 使用当前项目已有 async 处理方式；
3. 测试中使用 stub 避免真实 event loop 复杂性。

不建议为修复第三方 `DeprecationWarning` 大规模重写事件循环逻辑。

---

## 7. 测试要求

### 7.1 PydanticAI provider 测试

更新：

```text
tests/test_llm_pydanticai_provider.py
```

覆盖：

1. provider 可以从 `LLMReviewRequest` 构建 prompt；
2. provider 调用 prompt contract builder；
3. provider 将 raw JSON output 交给 output validator；
4. provider 返回 `ValidatedLLMSemanticReviewOutput`；
5. provider 支持合法纯 JSON output；
6. provider 支持合法 fenced JSON output；
7. provider 处理非法 JSON parse failure；
8. provider 处理字段非法 validation failure；
9. provider execution failure 返回稳定 error；
10. provider error 不泄露 secret；
11. provider prompt 不包含 secret；
12. provider execution 不读取 env；
13. provider execution 不访问真实网络；
14. construction check 仍不执行 semantic review；
15. live check 仍与 semantic review execution 分离。

---

### 7.2 prompt contract 回归测试

更新或保持：

```text
tests/test_llm_prompt_contract.py
```

确保：

1. provider execution 使用的 prompt contract 与 standalone prompt contract 一致；
2. schema version 仍是 `llm-semantic-review-output.v1`；
3. severity 枚举没有漂移；
4. rule_id prefix 没有漂移；
5. prompt builder 仍不读取 env；
6. prompt builder 仍不访问网络。

---

### 7.3 output validation 回归测试

更新或保持：

```text
tests/test_llm_output_validation.py
```

确保：

1. validator 仍可独立使用；
2. provider execution 没有绕过 validator；
3. parse / validation error 类型仍稳定；
4. error message 仍不泄露 raw output / secret-like value。

---

### 7.4 文档测试

更新：

```text
tests/test_llm_provider_usage_docs.py
```

确保文档中包含：

1. provider execution wiring；
2. prompt contract；
3. output validation；
4. PydanticAI provider semantic review pipeline；
5. 仍未接入 `review` / `batch`；
6. 仍不生成正式 `LLMReviewResult`；
7. 普通测试不访问真实网络；
8. secret 不进入 prompt / output / errors。

---

## 8. 文档更新要求

### 8.1 `docs/LLM_PROVIDER_USAGE.md`

补充：

1. PydanticAI provider semantic review execution pipeline；
2. prompt contract 如何接入 provider；
3. raw output 如何进入 validator；
4. validated semantic output 与 `LLMReviewResult` 的区别；
5. provider execution 仍未接入 `review` / `batch`；
6. provider execution 测试使用 fake / stub；
7. secret 不进入 prompt / output / errors。

---

### 8.2 `docs/DATA_MODELS.md`

补充：

1. `ValidatedLLMSemanticReviewOutput` 的 provider-level 使用方式；
2. 说明它仍不是正式 `LLMReviewResult`；
3. 说明后续任务会负责转换为 `LLMReviewResult`；
4. 说明公开 review schemas 未改变。

---

### 8.3 `docs/ARCHITECTURE.md`

补充：

1. PydanticAI provider semantic execution 在 LLM 架构中的位置；
2. prompt contract、provider execution、output validation 三层关系；
3. 为什么本任务不接入 main review；
4. 为什么本任务不生成 `LLMReviewResult`；
5. 后续任务如何把 validated output 转换为 `LLMReviewResult`。

---

### 8.4 `PROJECT_STATE.md`

更新：

1. 标记 `TASK-0067` 完成后新增 provider-level semantic execution wiring；
2. 说明当前 PydanticAI provider 可以执行 prompt contract 并校验 raw output；
3. 说明 `LLMReviewResult` generation、review/batch integration、report integration 仍是后续任务。

---

### 8.5 `CHANGELOG.md`

新增 `TASK-0067` 记录。

---

## 9. 验收标准

本任务完成后应满足：

1. `PydanticAIReviewer` 可以基于 `LLMReviewRequest` 执行 semantic review pipeline；
2. provider execution 复用 prompt contract；
3. provider execution 复用 output validation；
4. 合法 raw JSON output 可以返回 `ValidatedLLMSemanticReviewOutput`；
5. 合法 fenced JSON output 可以返回 `ValidatedLLMSemanticReviewOutput`；
6. 非法 JSON output 返回 parse error；
7. 字段不合法 output 返回 validation error；
8. PydanticAI execution failure 返回稳定 provider execution error；
9. 错误信息不泄露 secret；
10. prompt 不包含 secret；
11. 普通测试不访问真实网络；
12. 普通测试不依赖真实 API key；
13. construction check 不执行 semantic review；
14. live check 与 semantic review execution 保持分离；
15. 不生成正式 `LLMReviewResult`；
16. 不接入 `review` / `batch`；
17. 不修改公开 review result schema；
18. 不修改 sidecar metadata；
19. 文档已同步；
20. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 不要把 provider semantic execution 接入 CLI 主命令。
2. 不要在这个任务中生成 `LLMReviewResult`。
3. 不要绕过 prompt contract 另写一套 prompt。
4. 不要绕过 output validator 手动解析 JSON。
5. 不要让测试访问真实网络。
6. 不要让测试依赖真实 API key。
7. 不要把 live check 和 semantic review execution 混在一起。
8. 不要把 secret 放进 prompt。
9. 不要把 raw output 原样写入错误信息。
10. 不要修改主审计 schema。

---

## 11. 完成后需要运行的命令

可以先运行局部测试：

```bash
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_prompt_contract.py
uv run pytest tests/test_llm_output_validation.py
uv run pytest tests/test_llm_provider_usage_docs.py
```

最后必须运行全量测试：

```bash
uv run pytest
```

---

