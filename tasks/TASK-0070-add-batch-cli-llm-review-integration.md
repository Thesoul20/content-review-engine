# TASK-0070: Add Batch CLI LLM Review Integration

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
TASK-0069: Add Single-file CLI LLM Review Integration
```

目前 LLM 单文件链路已经具备：

```text
content-review review
  ↓
--enable-llm
  ↓
LLM runner
  ↓
secret resolver
  ↓
provider factory
  ↓
run_semantic_review(request)
  ↓
convert_validated_semantic_output_to_llm_review_result(...)
  ↓
--llm-output 写出 raw LLMReviewResult JSON
```

`TASK-0069` 已经完成单文件 `content-review review` 的显式 LLM 审计接入，并且保持 deterministic stdout / JSON / Markdown / quality gate 不变。

本任务的目标是：把 LLM 审计能力扩展到 `content-review batch`，让用户可以对批量文件执行 LLM semantic review，并将批量 LLM 审计结果写入独立 sidecar JSON 文件。

本任务只做 batch CLI LLM sidecar integration。

本任务不做：

1. Markdown report merge；
2. quality gate integration；
3. LLM findings 合并进 deterministic `BatchReviewResult`；
4. 主 batch JSON schema 修改；
5. API / MCP / GUI。

---

## 2. 任务目标

本任务需要完成：

1. 为 `content-review batch` 增加显式 LLM 审计开关；
2. 为 batch LLM 增加独立 `--llm-output` sidecar 输出；
3. 批量复用现有 LLM runner / provider pipeline；
4. 对 batch 发现的每个文件执行 LLM semantic review；
5. 为每个文件生成一个 `LLMReviewResult`；
6. 将所有文件的 LLM 结果写入 batch-level LLM sidecar JSON；
7. 保持 deterministic batch stdout / JSON / Markdown 输出不变；
8. 保持 deterministic `BatchReviewResult` schema 不变；
9. 保持 quality gate / fail-on 行为不变；
10. 普通测试不得访问真实网络；
11. 普通测试不得依赖真实 API key；
12. 增加 batch LLM integration 测试；
13. 更新 CLI、数据模型、架构和 provider usage 文档；
14. 更新 `PROJECT_STATE.md` 和 `CHANGELOG.md`。

完成后，用户应该可以通过类似命令运行 batch LLM 审计：

```bash
content-review batch examples/posts \
  --profile examples/profile.yml \
  --recursive \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model gpt-4.1-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-output examples/posts.llm.batch.json
```

具体参数名应优先遵守当前仓库已有 CLI 命名风格。如果当前项目已经存在等价参数，不要重复新增别名。

---

## 3. 本任务允许做什么

本任务允许：

1. 修改 `content-review batch` CLI 参数；
2. 增加或复用 `--enable-llm`；
3. 增加或复用 `--llm-provider`；
4. 增加或复用 `--llm-model`；
5. 增加或复用 `--llm-api-key-env`；
6. 增加或复用 `--llm-output`；
7. 新增 batch LLM runner helper；
8. 复用单文件 LLM runner；
9. 复用 secret resolver；
10. 复用 provider factory；
11. 复用 `run_semantic_review(request)`；
12. 复用 result conversion helper；
13. 新增或完善 batch LLM sidecar 数据结构；
14. 新增或完善 batch LLM sidecar serialization；
15. 新增 batch LLM CLI integration 测试；
16. 更新 `tests/test_cli.py`；
17. 更新 `tests/test_llm_runner.py`；
18. 更新 provider usage 文档测试；
19. 更新 `docs/CLI.md`；
20. 更新 `docs/LLM_PROVIDER_USAGE.md`；
21. 更新 `docs/DATA_MODELS.md`;
22. 更新 `docs/ARCHITECTURE.md`;
23. 更新 `PROJECT_STATE.md`;
24. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许：

1. 不允许把 LLM findings 合并进 deterministic `BatchReviewResult`；
2. 不允许修改 `BatchReviewResult` schema；
3. 不允许修改 `ReviewResult` schema；
4. 不允许修改 deterministic JSON output schema；
5. 不允许修改 deterministic Markdown report 结构；
6. 不允许把 LLM findings 混入 batch Markdown report；
7. 不允许让 LLM findings 参与 quality gate；
8. 不允许修改 fail-on / CI gate 行为；
9. 不允许修改 deterministic review engine 行为；
10. 不允许修改 `llm-check` live / construction 行为；
11. 不允许新增 plaintext API key 参数；
12. 不允许读取 `.env`；
13. 不允许让 provider factory 读取环境变量；
14. 不允许让 reserved providers 变成可创建；
15. 不允许让普通测试访问真实网络；
16. 不允许让普通测试依赖真实 API key；
17. 不允许在没有显式 `--enable-llm` 时执行 LLM；
18. 不允许在没有显式 `--llm-output` 时改变 stdout schema；
19. 不允许新增 API、MCP、Skill、GUI、Supabase、用户系统或商业化能力；
20. 不允许引入 LangChain、CrewAI 或其他大型框架。

---

## 5. 需要修改的文件

预计会新增或修改以下文件：

```text
src/content_review_engine/cli.py
src/content_review_engine/llm/runner.py
src/content_review_engine/llm/models.py
src/content_review_engine/llm/serialization.py
src/content_review_engine/llm/__init__.py

tests/test_cli.py
tests/test_llm_runner.py
tests/test_llm_batch_cli_integration.py
tests/test_llm_provider_usage_docs.py

docs/CLI.md
docs/LLM_PROVIDER_USAGE.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前仓库已经有 batch LLM sidecar、LLM serialization、runner 或模型文件，应优先复用现有结构，不要为了本任务大规模重命名文件。

---

## 6. 实现要求

### 6.1 CLI 参数要求

为 `content-review batch` 增加显式 LLM 参数。

推荐参数：

```bash
--enable-llm
--llm-provider pydanticai
--llm-model gpt-4.1-mini
--llm-api-key-env OPENAI_API_KEY
--llm-output path/to/batch.llm.json
```

要求：

1. 不传 `--enable-llm` 时，batch 行为完全不变；
2. 传 `--enable-llm` 时，才执行 LLM semantic review；
3. 启用 LLM 时必须提供 `--llm-output`；
4. LLM 输出必须写入独立 batch LLM sidecar JSON；
5. 不允许把 LLM result 混进 deterministic batch stdout；
6. 不允许把 LLM result 混进 deterministic batch JSON output；
7. 不允许把 LLM result 混进 deterministic batch Markdown report；
8. 不允许新增 plaintext API key 参数，例如 `--llm-api-key sk-...`。

---

### 6.2 batch LLM runner 要求

如果当前已有 `src/content_review_engine/llm/runner.py`，应在其中新增或扩展 batch helper。

推荐 helper：

```python
run_batch_llm_review(
    *,
    files: list[...],
    profile_name: str | None,
    provider_config: LLMProviderConfig,
    secret_value: str | None,
) -> BatchLLMReviewSidecar
```

或遵守当前项目已有命名风格。

runner 应负责：

1. 遍历 batch 中已发现并可读取的文件；
2. 为每个文件构建 `LLMReviewRequest`；
3. 调用 provider semantic review pipeline；
4. 调用 result conversion helper；
5. 收集每个文件的 `LLMReviewResult`；
6. 记录 batch-level summary；
7. 返回 batch LLM sidecar 对象或 dict。

runner 不应负责：

1. 解析 CLI 参数；
2. 读取 `.env`；
3. 读取环境变量；
4. 生成 deterministic `BatchReviewResult`；
5. 生成 Markdown report；
6. 处理 quality gate；
7. 修改 deterministic review result。

---

### 6.3 batch LLM sidecar 结构要求

batch LLM sidecar 应是独立 JSON。

推荐结构：

```json
{
  "schema_version": "batch-llm-review-sidecar.v1",
  "provider": "pydanticai",
  "model": "gpt-4.1-mini",
  "profile_name": "default",
  "summary": {
    "file_count": 2,
    "reviewed_count": 2,
    "failed_count": 0,
    "finding_count": 3
  },
  "results": [
    {
      "file": "posts/a.md",
      "status": "reviewed",
      "result": {
        "schema_version": "llm-review-result.v1",
        "provider": "pydanticai",
        "model": "gpt-4.1-mini",
        "summary": {
          "summary": "..."
        },
        "findings": []
      }
    }
  ],
  "failures": []
}
```

具体字段名应尽量贴合项目当前已有 sidecar / batch 风格。

要求：

1. 每个成功文件包含 file path 和 `LLMReviewResult`；
2. 每个失败文件包含 file path、error type、message；
3. batch-level summary 包含 total / reviewed / failed / finding_count；
4. sidecar 不包含 secret；
5. sidecar 不包含 full prompt；
6. sidecar 不包含 raw model output；
7. sidecar 不修改 deterministic `BatchReviewResult`。

---

### 6.4 部分失败策略要求

batch LLM 可能出现部分文件失败。

本任务需要明确策略。

推荐策略：

```text
默认 fail-fast = false
尽可能处理所有文件
最后如果存在 LLM failure，CLI exit code 非 0
sidecar 中记录成功 results 和 failures
```

如果当前项目已有 batch 错误策略，应优先遵守当前策略。

要求：

1. 单个文件 LLM 失败不应导致已完成文件结果丢失；
2. sidecar 中应记录成功结果；
3. sidecar 中应记录失败文件；
4. 失败信息不泄露 secret；
5. 失败信息不包含完整 raw model output；
6. 有任何 LLM failure 时，CLI 应返回非 0，除非文档明确采用 warning 策略；
7. deterministic batch output 仍按现有逻辑生成。

---

### 6.5 secret 解析要求

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

### 6.6 provider reuse 要求

batch LLM 审计中应尽量复用 provider instance，而不是每个文件重新构造 provider。

推荐顺序：

```text
1. 构建 provider config
2. resolve secret once
3. create provider once
4. 对每个文件调用 run_semantic_review(request)
5. convert each validated output to LLMReviewResult
```

要求：

1. 不要为每个文件重复解析 secret；
2. 不要为每个文件重复创建 provider，除非当前 provider 实现不支持复用；
3. 测试应覆盖 provider factory 只被调用一次，或文档中说明当前策略；
4. 不要为了复用 provider 引入全局状态。

---

### 6.7 LLMReviewRequest 构建要求

每个文件都应构建独立 `LLMReviewRequest`。

至少包括：

1. 文件内容；
2. 文件路径或文件名；
3. profile name；
4. review language，默认使用当前模型默认值；
5. deterministic findings 摘要，如果当前 batch 流程可稳定提供；
6. metadata 不得包含 secret。

如果 deterministic findings 摘要不方便在本任务中注入，可以先不注入，但应在文档中说明后续可增强。

不要为了注入 deterministic findings 大幅改 deterministic batch pipeline。

---

### 6.8 执行顺序要求

推荐 batch 执行顺序：

```text
1. 按现有逻辑执行 deterministic batch review
2. 按现有逻辑输出 deterministic batch result
3. 如果 --enable-llm:
     3.1 构建 LLMProviderConfig
     3.2 resolve secret once
     3.3 create provider once
     3.4 对每个 discovered / reviewed 文件执行 LLM semantic review
     3.5 convert each validated output to LLMReviewResult
     3.6 write batch LLM sidecar JSON
     3.7 如有 LLM failures，返回稳定非 0 exit code
```

要求：

1. 不启用 LLM 时，原 batch 逻辑完全不变；
2. 启用 LLM 时，deterministic batch 仍正常执行；
3. LLM result 不影响 deterministic quality gate；
4. LLM result 不改变 deterministic report；
5. LLM result 只写入 `--llm-output`。

---

### 6.9 stdout / output 兼容要求

本任务必须保证：

1. 不启用 LLM 时 batch stdout 完全不变；
2. 不启用 LLM 时 batch JSON output 完全不变；
3. 不启用 LLM 时 batch Markdown output 完全不变；
4. 启用 LLM 时 deterministic stdout / output 仍不混入 LLM result；
5. LLM result 只写入 `--llm-output`；
6. batch LLM sidecar 不影响 deterministic `--output`；
7. 如果 `--llm-output` 已存在，遵守当前项目已有 overwrite 行为；如无既有约定，应与 `--output` 行为保持一致并在文档说明。

---

### 6.10 错误处理要求

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
11. file read failure；
12. sidecar write failure；
13. partial file failure。

错误要求：

1. exit code 稳定；
2. 错误信息清晰；
3. 错误信息不泄露 secret；
4. 错误信息不包含完整 raw output；
5. 普通 CLI 不输出 traceback；
6. sidecar 中记录 per-file failure；
7. deterministic batch 输出不应因为单个 LLM 文件失败而丢失。

---

### 6.11 测试隔离要求

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

## 7. 测试要求

### 7.1 新增 batch LLM CLI integration 测试

新增：

```text
tests/test_llm_batch_cli_integration.py
```

覆盖：

1. 不传 `--enable-llm` 时 batch 行为不变；
2. 传 `--enable-llm` 时执行 batch LLM runner；
3. LLM result 写入 `--llm-output`；
4. deterministic stdout 不包含 LLM findings；
5. deterministic batch JSON 不包含 LLM findings；
6. batch LLM sidecar JSON 包含 batch-level schema version；
7. batch LLM sidecar JSON 包含 summary；
8. batch LLM sidecar JSON 包含 per-file results；
9. batch LLM sidecar JSON 包含 per-file failures；
10. sidecar JSON 不包含 secret；
11. missing `--llm-output` 返回稳定错误；
12. missing provider 返回稳定错误；
13. missing model 返回稳定错误；
14. missing api-key-env 返回稳定错误；
15. env missing 返回稳定错误；
16. env empty 返回稳定错误；
17. provider construction failure 返回稳定错误；
18. provider execution failure 被记录为 per-file failure；
19. output parse failure 被记录为 per-file failure；
20. output validation failure 被记录为 per-file failure；
21. sidecar write failure 返回稳定错误；
22. partial failure 时成功文件结果仍写入 sidecar；
23. 有 LLM failure 时 exit code 非 0；
24. 普通测试不访问真实网络；
25. 普通测试不依赖真实 API key。

---

### 7.2 CLI 回归测试

更新：

```text
tests/test_cli.py
```

覆盖：

1. `content-review batch` 原有参数仍可用；
2. 原有 batch text/json/markdown output 不变；
3. plaintext `--llm-api-key` 参数不存在；
4. `--enable-llm` 的 batch help 文档可见；
5. `--llm-output` 的 batch help 文档可见；
6. 不启用 LLM 时不调用 LLM runner；
7. batch 不支持 `--include-llm-report` 或明确保持当前行为。

---

### 7.3 LLM runner 测试

更新：

```text
tests/test_llm_runner.py
```

覆盖：

1. batch runner 可以处理多个文件；
2. provider 被创建一次；
3. secret 被解析一次；
4. 每个文件生成独立 `LLMReviewRequest`；
5. 每个成功文件生成 `LLMReviewResult`；
6. 单文件 provider failure 被记录；
7. 单文件 parse failure 被记录；
8. 单文件 validation failure 被记录；
9. partial failure 不丢失成功结果；
10. sidecar summary 统计正确；
11. secret 不出现在 runner result 中；
12. runner 不访问真实网络。

---

### 7.4 文档测试

更新：

```text
tests/test_llm_provider_usage_docs.py
```

确保文档中包含：

1. batch `content-review batch --enable-llm` 示例；
2. `--llm-output` batch sidecar 说明；
3. batch LLM sidecar schema；
4. partial failure 说明；
5. LLM result 不合并进 deterministic batch output；
6. LLM findings 不参与 quality gate；
7. Markdown report integration 尚未完成；
8. secret 安全说明；
9. 普通测试不访问真实网络。

---

## 8. 文档更新要求

### 8.1 `docs/CLI.md`

补充：

1. `content-review batch` 的 LLM 参数；
2. `--enable-llm`；
3. `--llm-provider`；
4. `--llm-model`；
5. `--llm-api-key-env`；
6. `--llm-output`；
7. batch LLM sidecar 示例；
8. partial failure 示例；
9. 错误示例；
10. 说明 LLM result 不进入 deterministic batch output；
11. 说明 LLM result 不参与 quality gate。

---

### 8.2 `docs/LLM_PROVIDER_USAGE.md`

补充：

1. batch LLM integration 的完整链路；
2. batch LLM review 示例；
3. batch LLM sidecar JSON 示例；
4. partial failure 行为；
5. secret 安全边界；
6. 当前仍未支持 Markdown report merge；
7. 当前仍未支持 quality gate merge。

---

### 8.3 `docs/DATA_MODELS.md`

补充：

1. batch LLM sidecar schema；
2. batch LLM sidecar summary；
3. per-file results；
4. per-file failures；
5. `LLMReviewResult` 与 deterministic `ReviewResult` 的关系；
6. `BatchReviewResult` schema 未改变；
7. LLM findings 当前不合并进 deterministic findings。

---

### 8.4 `docs/ARCHITECTURE.md`

补充：

1. batch CLI LLM integration 在架构中的位置；
2. deterministic batch review 与 LLM batch review 的并行关系；
3. 为什么本任务使用 batch sidecar 而不是合并主结果；
4. partial failure 策略；
5. 后续如何接入 Markdown report；
6. 后续如何接入 quality gate。

---

### 8.5 `PROJECT_STATE.md`

更新：

1. 标记 `TASK-0070` 完成后新增 batch CLI LLM review；
2. 说明当前支持单文件和 batch LLM sidecar；
3. 说明 report integration、quality gate integration 仍是后续任务。

---

### 8.6 `CHANGELOG.md`

新增 `TASK-0070` 记录。

---

## 9. 验收标准

本任务完成后应满足：

1. `content-review batch` 支持显式 LLM 审计开关；
2. 不传 LLM 开关时原 batch 行为不变；
3. 启用 LLM 时可以运行 batch semantic review；
4. LLM result 写入独立 `--llm-output` batch sidecar JSON；
5. deterministic stdout / JSON / Markdown 输出不混入 LLM result；
6. batch LLM sidecar JSON 包含 summary；
7. batch LLM sidecar JSON 包含 per-file results；
8. batch LLM sidecar JSON 包含 per-file failures；
9. sidecar JSON 不包含 secret；
10. missing required LLM 参数时返回稳定错误；
11. provider / model / secret / execution / parse / validation / write failure 均有稳定错误；
12. partial failure 时成功文件结果仍保留；
13. 有 LLM failure 时 exit code 非 0；
14. 普通测试不访问真实网络；
15. 普通测试不依赖真实 API key；
16. deterministic batch review engine 行为不变；
17. `ReviewResult` / `BatchReviewResult` schema 不变；
18. Markdown report 行为不变；
19. quality gate 行为不变；
20. 文档已同步；
21. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 不要把 LLM result 混进 deterministic batch stdout。
2. 不要修改 `BatchReviewResult` schema。
3. 不要在本任务中做 Markdown report integration。
4. 不要在本任务中做 quality gate integration。
5. 不要让 LLM findings 参与 fail-on。
6. 不要读取 `.env`。
7. 不要新增 plaintext API key 参数。
8. 不要让普通测试访问真实网络。
9. 不要为了 sidecar 输出而泄露 prompt、raw output 或 secret。
10. 不要把 batch runner 逻辑全部塞进 `cli.py`。
11. 注意 partial failure 策略要文档化并测试。
12. 注意 single-file raw LLMReviewResult sidecar 与 batch sidecar envelope 的区别。

---

## 11. 完成后需要运行的命令

可以先运行局部测试：

```bash
uv run pytest tests/test_llm_batch_cli_integration.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_runner.py
uv run pytest tests/test_llm_provider_usage_docs.py
```

最后必须运行全量测试：

```bash
uv run pytest
```

---
