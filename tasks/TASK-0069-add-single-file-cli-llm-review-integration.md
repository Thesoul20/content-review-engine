# TASK-0069: Add Single-file CLI LLM Review Integration

## 1. 背景

当前项目已经完成：

```text
TASK-0061: Add LLM Provider Secret Resolver
TASK-0062: Wire LLM Secret Resolver into LLM Check
TASK-0063: Enable Real PydanticAI Provider Construction
TASK-0064: Add Optional Live PydanticAI Runtime Smoke Check
TASK-0065: Add LLM Semantic Review Prompt Contract
TASK-0066: Add LLM Semantic Review Output Validation
TASK-0067: Wire Prompt Contract and Output Validation into PydanticAI Provider
TASK-0068: Convert Validated LLM Semantic Output to LLMReviewResult
```

目前 LLM 层已经具备完整的内部能力链路：

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
  ↓
result conversion
  ↓
LLMReviewResult
```

但这些能力目前还没有接入用户实际使用的 `content-review review` 单文件 CLI 主命令。

本任务的目标是：为单文件 `content-review review` 增加显式 LLM 审计开关，让用户可以在审计单个 Markdown / text 文件时，选择额外执行 LLM semantic review，并将 LLM 审计结果写入独立的 LLM sidecar JSON 文件。

本任务只接入单文件 CLI，不接入 batch，不合并 Markdown report，不让 LLM findings 参与 quality gate，不改变 deterministic review 的 stdout / JSON / Markdown 输出结构。

---

## 2. 任务目标

本任务需要完成：

1. 为 `content-review review` 增加显式 LLM 审计开关；
2. 通过 CLI 参数配置 LLM provider、model、api key env；
3. 在单文件 review 流程中构建 `LLMReviewRequest`；
4. 调用现有 provider factory 创建 PydanticAI reviewer；
5. 调用 `PydanticAIReviewer.run_semantic_review(request)`；
6. 调用 `convert_validated_semantic_output_to_llm_review_result(...)`；
7. 将 `LLMReviewResult` 写入独立 sidecar JSON 文件；
8. 保持 deterministic review 输出不变；
9. LLM 失败时返回稳定错误；
10. secret 不得泄露到 stdout、stderr、sidecar、日志或错误信息；
11. 普通测试不得访问真实网络；
12. 普通测试不得依赖真实 API key；
13. 增加 CLI、single-file LLM integration、文档测试；
14. 更新文档、项目状态和 changelog。

完成后，用户应该可以通过类似命令运行单文件 LLM 审计：

```bash
content-review review examples/post.md \
  --profile examples/profile.yml \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model gpt-4.1-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-output examples/post.llm.json
```

具体参数名应优先遵守当前仓库已有 CLI 命名风格。如果已有等价参数，不要重复新增别名。

---

## 3. 本任务允许做什么

本任务允许：

1. 修改 `content-review review` CLI 参数；
2. 新增 `--enable-llm` 或当前项目已有风格下等价的显式 LLM 开关；
3. 复用已有 `--llm-provider` / `--provider`、`--llm-model`、`--llm-api-key-env` 命名约定；
4. 新增 `--llm-output` 用于指定 LLM sidecar JSON 输出路径；
5. 在单文件 review 流程中构建 `LLMReviewRequest`；
6. 复用 secret resolver；
7. 复用 provider factory；
8. 复用 `PydanticAIReviewer.run_semantic_review()`；
9. 复用 result conversion helper；
10. 新增或完善 LLMReviewResult JSON serialization；
11. 写出单文件 LLM sidecar JSON；
12. 增加 CLI 测试；
13. 增加 LLM review integration 测试；
14. 增加文档测试；
15. 更新 `docs/CLI.md`；
16. 更新 `docs/LLM_PROVIDER_USAGE.md`；
17. 更新 `docs/ARCHITECTURE.md`；
18. 更新 `docs/DATA_MODELS.md`；
19. 更新 `PROJECT_STATE.md`；
20. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许：

1. 不允许接入 `content-review batch`；
2. 不允许修改 batch 行为；
3. 不允许把 LLM findings 合并进 deterministic `ReviewResult`；
4. 不允许修改 `ReviewResult` schema；
5. 不允许修改 `BatchReviewResult` schema；
6. 不允许修改 deterministic JSON output schema；
7. 不允许修改 deterministic Markdown report 结构；
8. 不允许让 LLM findings 参与 quality gate；
9. 不允许修改 fail-on / CI gate 行为；
10. 不允许修改 sidecar metadata 的既有结构，除非当前单文件 LLM sidecar 需要极小范围补充；
11. 不允许修改 deterministic review engine 行为；
12. 不允许新增 plaintext API key 参数；
13. 不允许读取 `.env`；
14. 不允许让 provider factory 读取环境变量；
15. 不允许让 reserved providers 变成可创建；
16. 不允许让普通测试访问真实网络；
17. 不允许让普通测试依赖真实 API key；
18. 不允许在没有显式 `--enable-llm` 时执行 LLM；
19. 不允许在没有显式 `--llm-output` 时改变 stdout schema；
20. 不允许新增 API、MCP、Skill、GUI、Supabase、用户系统或商业化能力；
21. 不允许引入 LangChain、CrewAI 或其他大型框架。

---

## 5. 需要修改的文件

预计会新增或修改以下文件：

```text
src/content_review_engine/cli.py
src/content_review_engine/llm/runner.py
src/content_review_engine/llm/result_conversion.py
src/content_review_engine/llm/serialization.py
src/content_review_engine/llm/models.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/__init__.py

tests/test_cli.py
tests/test_llm_single_file_cli_integration.py
tests/test_llm_result_conversion.py
tests/test_llm_provider_usage_docs.py

docs/CLI.md
docs/LLM_PROVIDER_USAGE.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前仓库已经有 LLM runner、serialization 或 sidecar 模块，应优先复用现有结构，不要为了本任务大规模重命名文件。

---

## 6. 实现要求

### 6.1 CLI 参数要求

为单文件 `content-review review` 增加显式 LLM 参数。

推荐参数：

```bash
--enable-llm
--llm-provider pydanticai
--llm-model gpt-4.1-mini
--llm-api-key-env OPENAI_API_KEY
--llm-output path/to/result.llm.json
```

如果当前项目已有命名约定，应优先复用。

要求：

1. 不传 `--enable-llm` 时，单文件 review 行为完全不变；
2. 传 `--enable-llm` 时，才执行 LLM semantic review；
3. LLM 输出必须写入独立 sidecar JSON；
4. 不允许把 LLM result 混进现有 stdout JSON；
5. 不允许把 LLM result 混进现有 Markdown report；
6. 如果 `--enable-llm` 但没有 `--llm-output`，推荐返回清晰错误，避免隐式修改 stdout 或生成意外文件；
7. 不允许新增 plaintext API key 参数，例如 `--llm-api-key sk-...`。

---

### 6.2 单文件 LLM runner 要求

如果当前项目已有 LLM runner，应扩展它。
如果没有，可以新增轻量 runner，例如：

```text
src/content_review_engine/llm/runner.py
```

推荐 helper：

```python
run_single_file_llm_review(
    *,
    content: str,
    file_path: str | None,
    profile_name: str | None,
    provider_config: LLMProviderConfig,
    secret_value: str | None,
) -> LLMReviewResult
```

或遵守当前项目已有命名风格。

runner 应负责：

1. 构建 `LLMReviewRequest`；
2. 调用 provider factory；
3. 调用 provider semantic review；
4. 调用 conversion helper；
5. 返回 `LLMReviewResult`。

runner 不应负责：

1. 解析 CLI 参数；
2. 读取 `.env`；
3. 读取环境变量；
4. 生成 deterministic ReviewResult；
5. 生成 Markdown report；
6. 处理 quality gate；
7. 调用 batch 逻辑。

---

### 6.3 secret 解析要求

secret 解析应继续遵守当前边界：

```text
LLMProviderConfig.api_key_env
  ↓
resolve_llm_provider_secret(config, env=None)
  ↓
secret value
  ↓
create_llm_reviewer(config, secret_value=...)
```

要求：

1. CLI 不接收 plaintext secret；
2. provider factory 不读取 env；
3. provider factory 不调用 resolver；
4. resolver 不读取 `.env`；
5. secret value 不写入 sidecar JSON；
6. secret value 不写入 stdout / stderr；
7. secret value 不写入 error message；
8. 测试中必须断言 secret 不泄露。

---

### 6.4 LLMReviewRequest 构建要求

单文件 CLI 接入时，应从当前 review 输入构建 `LLMReviewRequest`。

至少包括：

1. 文件内容；
2. 文件路径或文件名；
3. profile name；
4. review language，默认可使用当前模型默认值；
5. deterministic findings 摘要，如果当前流程已经能方便传入；
6. metadata 中不得包含 secret。

如果 deterministic findings 摘要难以在本任务中稳定注入，可以先不注入，但应在文档或 TODO 中说明后续可增强。

注意：不要为了注入 deterministic findings 大幅改 deterministic review pipeline。

---

### 6.5 执行顺序要求

推荐单文件 review 执行顺序：

```text
1. 按现有逻辑执行 deterministic review
2. 按现有逻辑输出 deterministic result
3. 如果 --enable-llm:
     3.1 构建 LLMProviderConfig
     3.2 resolve secret
     3.3 run single-file LLM semantic review
     3.4 convert to LLMReviewResult
     3.5 write --llm-output sidecar JSON
```

要求：

1. 不启用 LLM 时，原逻辑完全不变；
2. 启用 LLM 时，deterministic review 仍然正常执行；
3. LLM 失败时 exit code 应非 0，除非当前项目已有 partial-success 策略；
4. 不要让 LLM result 影响 deterministic quality gate；
5. 不要让 LLM result 改变 deterministic report。

---

### 6.6 sidecar JSON 要求

LLM sidecar JSON 应基于 `LLMReviewResult` serialization。

如果已有 serializer，应复用。
如果没有，可以新增最小 serializer，但不要修改主 deterministic serializer。

sidecar JSON 应包含：

1. LLMReviewResult schema version；
2. provider；
3. model；
4. profile name；
5. summary；
6. findings；
7. finding rule_id；
8. finding severity；
9. line；
10. column；
11. message；
12. matched_text / evidence；
13. suggestion；
14. confidence；
15. metadata 中的 semantic output schema version。

sidecar JSON 不得包含：

1. secret value；
2. api key env value；
3. raw model output，除非已有设计明确允许且已脱敏；
4. full prompt；
5. environment variables；
6. local absolute paths中的敏感信息，除非当前项目已有 file path 约定。

---

### 6.7 错误处理要求

需要稳定处理：

1. `--enable-llm` 但缺少 `--llm-output`；
2. `--enable-llm` 但缺少 provider；
3. `--enable-llm` 但缺少 model；
4. `--enable-llm` 但缺少 api key env；
5. api key env 不存在；
6. api key env 为空；
7. provider construction failure；
8. provider execution failure；
9. output parse failure；
10. output validation failure；
11. sidecar 写入失败。

错误要求：

1. exit code 非 0；
2. 错误信息清晰；
3. 错误信息不泄露 secret；
4. 错误信息不包含完整 raw output；
5. 普通 CLI 不输出 traceback；
6. 保持当前 CLI 错误风格。

---

### 6.8 测试隔离要求

普通测试不得访问真实网络。

必须使用：

1. fake provider；
2. monkeypatch provider factory；
3. stubbed `run_semantic_review()`；
4. fake `ValidatedLLMSemanticReviewOutput`；
5. fake `LLMReviewResult`；
6. 或当前项目已有测试工具。

普通测试不得依赖：

1. 真实 OpenAI API key；
2. 真实 Anthropic API key；
3. 真实 Gemini API key；
4. 真实 DeepSeek API key；
5. 真实 Qwen API key；
6. 开发者本机环境变量；
7. 外部网络。

---

### 6.9 stdout / output 兼容要求

本任务必须保证：

1. 不启用 LLM 时 stdout 完全不变；
2. 不启用 LLM 时 JSON output 完全不变；
3. 不启用 LLM 时 Markdown output 完全不变；
4. 启用 LLM 时 deterministic stdout / output 仍不混入 LLM result；
5. LLM result 只写入 `--llm-output`；
6. 如果 `--llm-output` 已存在，遵守当前项目已有 overwrite 行为；如果无既有约定，应直接覆盖或失败，但必须文档说明。

推荐采用当前项目已有 `--output` 行为一致的覆盖策略。

---

## 7. 测试要求

### 7.1 新增 single-file CLI LLM integration 测试

新增：

```text
tests/test_llm_single_file_cli_integration.py
```

覆盖：

1. 不传 `--enable-llm` 时单文件 review 行为不变；
2. 传 `--enable-llm` 时执行 LLM runner；
3. LLM result 写入 `--llm-output`；
4. deterministic stdout 不包含 LLM findings；
5. LLM sidecar JSON 包含 `LLMReviewResult` 字段；
6. sidecar JSON 不包含 secret；
7. missing `--llm-output` 返回稳定错误；
8. missing provider 返回稳定错误；
9. missing model 返回稳定错误；
10. missing api key env 返回稳定错误；
11. env var missing 返回稳定错误；
12. env var empty 返回稳定错误；
13. provider execution failure 返回稳定错误；
14. output parse failure 返回稳定错误；
15. output validation failure 返回稳定错误；
16. sidecar write failure 返回稳定错误；
17. 普通测试不访问真实网络；
18. 普通测试不依赖真实 API key。

---

### 7.2 CLI 回归测试

更新：

```text
tests/test_cli.py
```

覆盖：

1. `content-review review` 原有参数仍可用；
2. 原有 text/json/markdown output 不变；
3. plaintext `--llm-api-key` 参数不存在；
4. `--enable-llm` 的 help 文档可见；
5. `--llm-output` 的 help 文档可见；
6. 不启用 LLM 时不调用 LLM runner。

---

### 7.3 LLM result conversion 回归测试

更新或保持：

```text
tests/test_llm_result_conversion.py
```

确保：

1. conversion helper 仍独立；
2. CLI integration 不绕过 conversion；
3. confidence null 行为不变；
4. rule_id / severity 映射不变。

---

### 7.4 文档测试

更新：

```text
tests/test_llm_provider_usage_docs.py
```

确保文档中包含：

1. single-file `content-review review --enable-llm` 示例；
2. `--llm-output` sidecar 说明；
3. LLM result 不合并进 deterministic output；
4. LLM findings 不参与 quality gate；
5. batch integration 尚未完成；
6. secret 安全说明；
7. 普通测试不访问真实网络。

---

## 8. 文档更新要求

### 8.1 `docs/CLI.md`

补充：

1. `content-review review` 的 LLM 参数；
2. `--enable-llm`；
3. `--llm-provider` / provider 参数；
4. `--llm-model`；
5. `--llm-api-key-env`；
6. `--llm-output`；
7. 单文件 LLM sidecar 示例；
8. 错误示例；
9. 说明 LLM result 不进入 deterministic output；
10. 说明 LLM result 不参与 quality gate。

---

### 8.2 `docs/LLM_PROVIDER_USAGE.md`

补充：

1. 从 provider infrastructure 到 single-file CLI integration 的完整链路；
2. 单文件 LLM review 示例；
3. sidecar JSON 输出示例；
4. secret 安全边界；
5. 普通测试如何使用 fake / stub；
6. 当前仍未支持 batch LLM integration；
7. 当前仍未支持 report merge；
8. 当前仍未支持 quality gate merge。

---

### 8.3 `docs/DATA_MODELS.md`

补充：

1. 单文件 LLM sidecar 使用 `LLMReviewResult`；
2. `LLMReviewResult` 与 deterministic `ReviewResult` 的关系；
3. 本任务不修改 `ReviewResult` / `BatchReviewResult`；
4. LLM findings 当前不合并进 deterministic findings；
5. confidence 字段说明；
6. semantic output schema metadata 说明。

---

### 8.4 `docs/ARCHITECTURE.md`

补充：

1. single-file CLI LLM integration 在架构中的位置；
2. deterministic review 与 LLM review 的并行关系；
3. 为什么本任务使用 sidecar 而不是合并主结果；
4. 后续如何接入 batch；
5. 后续如何接入 report；
6. 后续如何接入 quality gate。

---

### 8.5 `PROJECT_STATE.md`

更新：

1. 标记 `TASK-0069` 完成后新增 single-file CLI LLM review；
2. 说明当前支持单文件 LLM sidecar；
3. 说明 batch LLM integration、report integration、quality gate integration 仍是后续任务。

---

### 8.6 `CHANGELOG.md`

新增 `TASK-0069` 记录。

---

## 9. 验收标准

本任务完成后应满足：

1. `content-review review` 支持显式 LLM 审计开关；
2. 不传 LLM 开关时原行为不变；
3. 启用 LLM 时可以运行 single-file semantic review；
4. LLM result 写入独立 `--llm-output` sidecar JSON；
5. deterministic stdout / JSON / Markdown 输出不混入 LLM result；
6. sidecar JSON 符合 `LLMReviewResult` serialization；
7. sidecar JSON 不包含 secret；
8. missing required LLM 参数时返回稳定错误；
9. provider / model / secret / execution / parse / validation / write failure 均有稳定错误；
10. 普通测试不访问真实网络；
11. 普通测试不依赖真实 API key；
12. batch 行为不变；
13. report 行为不变；
14. quality gate 行为不变；
15. deterministic review engine 行为不变；
16. `ReviewResult` / `BatchReviewResult` schema 不变；
17. 文档已同步；
18. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 不要把 LLM result 混进 deterministic stdout。
2. 不要修改现有 `ReviewResult` schema。
3. 不要在本任务中做 batch integration。
4. 不要在本任务中做 Markdown report integration。
5. 不要让 LLM findings 参与 quality gate。
6. 不要读取 `.env`。
7. 不要新增 plaintext API key 参数。
8. 不要让普通测试访问真实网络。
9. 不要为了 sidecar 输出而泄露 prompt、raw output 或 secret。
10. 不要把 CLI、provider、conversion、serialization 全部混在 `cli.py` 中；复杂逻辑应下沉到 LLM runner / helper。

---

## 11. 完成后需要运行的命令

可以先运行局部测试：

```bash
uv run pytest tests/test_llm_single_file_cli_integration.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_result_conversion.py
uv run pytest tests/test_llm_provider_usage_docs.py
```

最后必须运行全量测试：

```bash
uv run pytest
```

---
