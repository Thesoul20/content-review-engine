# TASK-0040: Add Batch LLM Sidecar Output

## 1. 背景

当前项目已经完成：

```text
TASK-0035: Add LLM provider interface and mock reviewer
  ✅ 已完成

TASK-0036: Add LLM semantic review runner
  ✅ 已完成

TASK-0037: Add CLI LLM review plumbing
  ✅ 已完成

TASK-0038: Add PydanticAI OpenAI-compatible LLM provider
  ✅ 已完成

TASK-0039: Add optional LLM Markdown report integration
  ✅ 已完成
```

当前单文件 `review` command 已经支持：

```text
content-review review
        ↓
deterministic ReviewResult
        ↓
optional LLMReviewResult sidecar JSON
        ↓
optional LLM Markdown report section
```

但是批量审计命令 `content-review batch` 目前还没有 LLM sidecar 输出能力。

因此，本任务需要为 batch command 增加显式 opt-in 的 LLM sidecar 输出能力，让批量审计可以对每个 Markdown 文件生成独立的 `LLMReviewResult` JSON 文件。

本任务只做 batch LLM sidecar，不做 batch LLM report integration，不改变 batch summary，不改变 batch JSON schema，不改变 quality gate。

---

## 2. 任务目标

为 `content-review batch` 增加可选 LLM sidecar 输出能力。

本任务完成后，应支持：

1. 用户通过显式参数在 batch command 中启用 LLM review；
2. batch 对每个成功 reviewed 的 Markdown 文件生成一个独立 LLM sidecar JSON；
3. sidecar JSON 使用已有 `LLMReviewResult` schema 和 serialization helper；
4. batch 可复用已有 `LLMReviewRunner`；
5. batch 可复用已有 `MockLLMReviewer`；
6. batch 可复用已有 `PydanticAIOpenAIReviewer`；
7. batch 默认行为完全不变；
8. batch 主 JSON output schema 不变；
9. batch Markdown report 结构不变；
10. batch summary 不统计 LLM findings；
11. quality gate 不读取 LLM findings；
12. 不新增 API、MCP、GUI。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 给 `batch` command 增加显式 LLM opt-in 参数；
2. 增加 batch LLM sidecar 输出目录参数；
3. batch 复用已有 `LLMReviewRunner`；
4. batch 复用已有 LLM provider 构造逻辑；
5. batch 支持 `mock` provider；
6. batch 支持 `pydanticai-openai` provider；
7. 对每个成功 reviewed 的 Markdown 文件写入一个独立 `LLMReviewResult` JSON；
8. 保持 sidecar 输出路径稳定、可预测、可测试；
9. 新增或更新 batch CLI 测试；
10. 更新 CLI 文档；
11. 更新架构文档；
12. 更新数据模型文档；
13. 更新 `PROJECT_STATE.md`；
14. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许改变 batch `BatchReviewResult` schema；
2. 不允许给 batch JSON output 新增 `llm_review` 字段；
3. 不允许给 batch summary 新增 LLM counts；
4. 不允许让 quality gate 统计 LLM findings；
5. 不允许改变 deterministic severity counts；
6. 不允许改变 deterministic rule counts；
7. 不允许改变 deterministic findings 顺序；
8. 不允许改变单文件 review command 行为；
9. 不允许改变单文件 Markdown report LLM integration 行为；
10. 不允许实现 batch Markdown report LLM section；
11. 不允许实现 batch LLM aggregate report；
12. 不允许新增 API；
13. 不允许新增 MCP；
14. 不允许新增 GUI；
15. 不允许新增 streaming；
16. 不允许新增 retry policy；
17. 不允许新增 cache；
18. 不允许新增 token accounting；
19. 不允许新增 cost tracking；
20. 不允许新增 telemetry；
21. 不允许新增 tracing / Logfire 集成；
22. 不允许新增 prompt template registry；
23. 不允许在测试中进行真实网络请求；
24. 不允许要求测试环境存在真实 API key。

---

## 5. 需要修改的文件

预计需要修改或新增以下文件：

```text
src/content_review_engine/cli.py
tests/test_cli.py
docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

如果现有测试结构适合拆分，可以新增：

```text
tests/test_batch_llm_cli.py
```

如果当前 CLI 中 provider 构造逻辑已经变重，可以新增轻量 helper，例如：

```text
src/content_review_engine/llm/factory.py
```

但该 helper 只能负责构造 provider，不允许做复杂 routing、retry、cache、telemetry、streaming 或 cost tracking。

如果任务卡文件尚不存在，也可以新增：

```text
tasks/TASK-0040-batch-llm-sidecar-output.md
```

---

## 6. 实现要求

### 6.1 CLI 参数设计

给 `batch` command 增加 LLM 参数。

推荐参数：

```text
--enable-llm
--llm-provider <provider>
--llm-output-dir <dir>
--llm-model <model>
--llm-api-key-env <env-name>
--llm-base-url <url>
```

其中：

```text
--enable-llm
```

显式启用 batch LLM review。

```text
--llm-provider
```

支持：

```text
mock
pydanticai-openai
```

```text
--llm-output-dir
```

指定 batch LLM sidecar JSON 输出目录。

```text
--llm-model
```

仅在 `--llm-provider pydanticai-openai` 时需要。

```text
--llm-api-key-env
```

指定 API key 所在环境变量名称。默认可以是：

```text
OPENAI_API_KEY
```

该参数的值是环境变量名称，不是 API key 本身。

```text
--llm-base-url
```

可选，用于 OpenAI-compatible endpoint。

---

### 6.2 参数校验规则

需要实现以下校验：

1. `--enable-llm` 必须配合 `--llm-output-dir`；
2. `--llm-output-dir` 未配合 `--enable-llm` 应失败；
3. `--llm-provider` 未配合 `--enable-llm` 应失败；
4. `--llm-model` 未配合 `--enable-llm` 应失败；
5. `--llm-api-key-env` 未配合 `--enable-llm` 应失败；
6. `--llm-base-url` 未配合 `--enable-llm` 应失败；
7. `--llm-provider mock` 不要求 `--llm-model`；
8. `--llm-provider mock` 不读取 API key；
9. `--llm-provider pydanticai-openai` 必须提供 `--llm-model`；
10. `--llm-provider pydanticai-openai` 必须能从指定环境变量读取 API key；
11. unsupported provider 应失败；
12. 参数错误应按现有 CLI 风格返回；
13. 不应向普通 CLI 用户输出 Python traceback。

---

### 6.3 Sidecar 输出路径规则

batch LLM sidecar 输出必须稳定、可预测、可测试。

推荐规则：

```text
<input_dir>/posts/a.md
        ↓
<llm-output-dir>/posts/a.md.llm-review.json
```

也就是说：

1. 以 batch input directory 为根；
2. 计算被审计 Markdown 文件的 relative path；
3. 在 `--llm-output-dir` 下保留 relative path；
4. 在原文件名后追加 `.llm-review.json`；
5. 必要时自动创建父目录；
6. 路径排序与现有 batch discovery 保持一致；
7. 不覆盖 deterministic review output；
8. 不把所有文件写到同一个 JSON；
9. 不把 LLM sidecar 写回原 Markdown 文件旁边，除非用户明确把 output dir 指到那里。

示例：

```text
content/
  a.md
  nested/b.md

--llm-output-dir llm-results
```

应生成：

```text
llm-results/
  a.md.llm-review.json
  nested/
    b.md.llm-review.json
```

---

### 6.4 Batch LLM 执行规则

当用户执行：

```bash
content-review batch content \
  --profile profile.yml \
  --enable-llm \
  --llm-provider mock \
  --llm-output-dir llm-results
```

CLI 应该：

1. 按现有 batch 逻辑发现 Markdown 文件；
2. 按现有 batch 逻辑运行 deterministic review；
3. 对每个成功 reviewed 的文件构造 `LLMReviewRequest`；
4. 使用 `LLMReviewRunner`；
5. 使用指定 provider；
6. 为每个文件生成一个 `LLMReviewResult`；
7. 将每个 result 写入对应 sidecar JSON；
8. 保持 batch 主输出不变；
9. 保持 batch exit code / quality gate 语义不变。

---

### 6.5 LLMReviewRequest 构造规则

batch 中构造 `LLMReviewRequest` 时，应与单文件 review command 尽量一致。

要求：

1. 使用已有 `LLMReviewRequest`；
2. 使用当前文件的 Markdown 内容；
3. 使用当前 profile；
4. 使用当前文件路径；
5. 不重复实现 Markdown reader；
6. 不重复实现 profile loader；
7. 不改变 deterministic review runner 输入输出；
8. 不改变 existing batch review result。

---

### 6.6 Provider 复用规则

batch 应复用单文件 review 已有 provider 构造逻辑。

如果当前 provider 构造逻辑已经在 `cli.py` 中，可以考虑抽取轻量 helper，例如：

```python
def build_llm_reviewer_from_cli_options(...) -> LLMReviewer:
    ...
```

或放入：

```text
src/content_review_engine/llm/factory.py
```

要求：

1. 不复制大量 provider 构造逻辑；
2. 不改变已有 single-file review provider 行为；
3. `mock` provider 不读取 API key；
4. `pydanticai-openai` provider 读取 API key env；
5. 不在未启用 LLM 时构造真实 provider；
6. 不在未启用 LLM 时读取 API key；
7. 不在测试中访问真实网络。

---

### 6.7 错误处理规则

如果 batch LLM 执行失败，应按现有 CLI 错误风格返回清晰错误。

推荐行为：

1. 参数错误直接失败；
2. provider 构造失败直接失败；
3. API key 缺失直接失败；
4. sidecar 输出目录无法创建直接失败；
5. sidecar 写文件失败直接失败；
6. provider 调用失败映射为已有 LLM 错误并由 CLI 转换为友好错误；
7. 不要输出 Python traceback；
8. 不要静默跳过失败文件；
9. 不要把失败的 LLM result 当作成功写入。

本任务不引入复杂 partial failure report，也不引入 retry。

---

### 6.8 与 batch summary 的关系

本任务不改变 batch summary。

不要新增：

```text
LLM Files Reviewed
LLM Findings
LLM Severity Counts
LLM Failed Files
```

这些可以后续单独规划。

---

### 6.9 与 quality gate 的关系

LLM findings 不参与 quality gate。

即使某个 LLM sidecar 中包含 `critical` finding，也不应影响：

```text
exit code
fail-on
matched gate findings
batch summary
deterministic severity counts
deterministic rule counts
```

quality gate 仍然只基于 deterministic findings。

---

### 6.10 与 Markdown report 的关系

本任务不实现 batch Markdown report LLM integration。

即使用户执行：

```bash
content-review batch content \
  --profile profile.yml \
  --format markdown \
  --enable-llm \
  --llm-provider mock \
  --llm-output-dir llm-results
```

batch Markdown report 也不应新增 LLM section。

---

## 7. 测试要求

### 7.1 Batch 默认行为不变

测试：

```bash
content-review batch content \
  --profile profile.yml
```

验证：

1. 不生成 LLM output dir；
2. batch text output 不变；
3. batch JSON output 不包含 `llm_review`；
4. batch Markdown output 不包含 `## LLM Review`；
5. quality gate 行为不变。

---

### 7.2 Batch mock LLM sidecar 输出

测试：

```bash
content-review batch content \
  --profile profile.yml \
  --enable-llm \
  --llm-provider mock \
  --llm-output-dir llm-results
```

验证：

1. 命令成功；
2. 为每个 reviewed Markdown 文件生成 sidecar JSON；
3. sidecar 路径保留 relative path；
4. sidecar 文件名追加 `.llm-review.json`；
5. sidecar JSON 包含 `schema_version`；
6. `schema_version` 等于 `llm-review-result.v1`；
7. 默认 mock findings 为空；
8. batch 主输出不包含 LLM 字段。

---

### 7.3 Recursive batch sidecar 路径

如果 batch 支持 `--recursive`，测试：

```bash
content-review batch content \
  --profile profile.yml \
  --recursive \
  --enable-llm \
  --llm-provider mock \
  --llm-output-dir llm-results
```

验证：

1. nested Markdown 文件被处理；
2. nested sidecar 路径保留相对目录；
3. 输出顺序和路径稳定。

---

### 7.4 参数校验测试

至少覆盖：

1. `--enable-llm` 缺少 `--llm-output-dir` 应失败；
2. `--llm-output-dir` 未配合 `--enable-llm` 应失败；
3. `--llm-provider` 未配合 `--enable-llm` 应失败；
4. `--llm-model` 未配合 `--enable-llm` 应失败；
5. `--llm-api-key-env` 未配合 `--enable-llm` 应失败；
6. `--llm-base-url` 未配合 `--enable-llm` 应失败；
7. unsupported provider 应失败；
8. `pydanticai-openai` 缺少 `--llm-model` 应失败；
9. `pydanticai-openai` 缺少 API key env 应失败。

---

### 7.5 PydanticAI provider batch 成功路径

使用 monkeypatch / fake provider，测试：

```bash
content-review batch content \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai-openai \
  --llm-model fake-model \
  --llm-api-key-env FAKE_API_KEY \
  --llm-output-dir llm-results
```

验证：

1. 命令成功；
2. 不访问真实网络；
3. 不要求真实 API key；
4. 每个 reviewed Markdown 文件生成 sidecar JSON；
5. sidecar JSON 包含 fake provider 返回的 findings；
6. batch 主 JSON 不包含 `llm_review`；
7. batch Markdown report 不包含 `## LLM Review`。

---

### 7.6 Quality gate 不受 LLM findings 影响

通过 fake provider 构造 LLM `critical` finding，同时 deterministic review 不触发 gate。

验证：

1. batch exit code 不受 LLM finding 影响；
2. quality gate 只基于 deterministic findings；
3. LLM finding 只出现在 sidecar JSON；
4. batch summary 不统计 LLM finding。

---

### 7.7 Sidecar 写文件失败

构造不可写 output dir 或冲突路径。

验证：

1. 命令失败；
2. 错误信息清晰；
3. 不输出 Python traceback；
4. 不静默成功。

---

### 7.8 完整测试

最终运行：

```bash
uv run pytest
```

确保所有测试通过。

---

## 8. 文档更新要求

### 8.1 更新 docs/CLI.md

补充 batch LLM sidecar 用法。

需要说明：

1. batch LLM 是 explicit opt-in；
2. 使用 `--enable-llm` 启用；
3. 使用 `--llm-output-dir` 指定 sidecar 输出目录；
4. 支持 `--llm-provider mock`；
5. 支持 `--llm-provider pydanticai-openai`；
6. `pydanticai-openai` 需要 `--llm-model`；
7. API key 通过 `--llm-api-key-env` 指定环境变量；
8. 可选 `--llm-base-url` 支持 OpenAI-compatible endpoint；
9. 每个 reviewed 文件生成一个 sidecar JSON；
10. sidecar 路径保留 input dir relative path；
11. batch summary 不统计 LLM findings；
12. batch JSON schema 不变；
13. batch Markdown report 不展示 LLM section；
14. quality gate 不受 LLM findings 影响。

示例：

```bash
content-review batch content \
  --profile profile.yml \
  --recursive \
  --enable-llm \
  --llm-provider mock \
  --llm-output-dir llm-results
```

真实 provider 示例：

```bash
content-review batch content \
  --profile profile.yml \
  --recursive \
  --enable-llm \
  --llm-provider pydanticai-openai \
  --llm-model gpt-5-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-output-dir llm-results
```

---

### 8.2 更新 docs/ARCHITECTURE.md

补充 batch LLM sidecar 数据流：

```text
Batch CLI command
        ↓
Markdown file discovery
        ↓
deterministic batch review
        ↓
optional --enable-llm
        ↓
per-file LLMReviewRequest
        ↓
LLMReviewRunner
        ↓
LLMReviewer provider
        ↓
per-file LLMReviewResult sidecar JSON
```

并说明：

1. batch LLM sidecar 是独立输出；
2. batch summary 不合并 LLM result；
3. batch JSON schema 不变；
4. batch Markdown report 不展示 LLM section；
5. quality gate 不读取 LLM result；
6. provider 仍然通过 `LLMReviewer` interface 隔离。

---

### 8.3 更新 docs/DATA_MODELS.md

补充：

1. batch LLM sidecar 使用已有 `LLMReviewResult` schema；
2. 每个 reviewed file 对应一个独立 `LLMReviewResult` JSON；
3. sidecar 路径由 input relative path 派生；
4. `BatchReviewResult` schema 不变；
5. `ReviewResult` schema 不变；
6. LLM findings 不进入 deterministic severity counts / rule counts；
7. LLM findings 不进入 quality gate。

---

### 8.4 更新 PROJECT_STATE.md

记录：

1. TASK-0040 已完成；
2. batch command 支持 optional LLM sidecar output；
3. batch 支持 mock provider；
4. batch 支持 pydanticai-openai provider；
5. 每个 reviewed Markdown 文件生成独立 sidecar JSON；
6. batch summary / JSON schema / Markdown report / quality gate 不变；
7. batch LLM aggregate report、API、MCP、GUI 尚未实现。

---

### 8.5 更新 CHANGELOG.md

记录：

1. 新增 batch LLM sidecar output；
2. 新增 `--llm-output-dir`；
3. batch 支持 `--enable-llm`；
4. batch 支持 `mock` 和 `pydanticai-openai` provider；
5. 新增 batch LLM CLI 测试；
6. 更新 CLI / architecture / data model 文档；
7. 明确未改变 batch JSON schema、Markdown report、quality gate、API、MCP、GUI。

---

## 9. 验收标准

本任务完成后应满足：

1. `content-review batch` 支持 `--enable-llm`；
2. `content-review batch` 支持 `--llm-provider mock`；
3. `content-review batch` 支持 `--llm-provider pydanticai-openai`；
4. `content-review batch` 支持 `--llm-output-dir <dir>`；
5. `pydanticai-openai` 支持 `--llm-model`；
6. `pydanticai-openai` 支持 `--llm-api-key-env`；
7. `pydanticai-openai` 支持可选 `--llm-base-url`；
8. 默认 batch 行为完全不变；
9. 启用 LLM 后，每个 reviewed Markdown 文件生成独立 sidecar JSON；
10. sidecar JSON 使用已有 `LLMReviewResult` schema；
11. sidecar 路径稳定并保留 relative path；
12. batch JSON output 不包含 `llm_review`；
13. batch Markdown report 不包含 `## LLM Review`；
14. batch summary 不统计 LLM findings；
15. quality gate 不受 LLM findings 影响；
16. 单文件 review command 行为不变；
17. 测试不访问真实网络；
18. 测试不要求真实 API key；
19. docs/CLI.md 已更新；
20. docs/ARCHITECTURE.md 已更新；
21. docs/DATA_MODELS.md 已更新；
22. PROJECT_STATE.md 已更新；
23. CHANGELOG.md 已更新；
24. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

### 10.1 防止 batch schema 膨胀

本任务只输出 sidecar 文件。

不要把 LLM result 合并进：

```text
BatchReviewResult
ReviewResult
batch JSON output
batch Markdown report
quality gate
```

---

### 10.2 防止 batch report integration 提前发生

不要在 batch Markdown report 中新增：

```md
## LLM Review
```

也不要新增 batch-level LLM summary。

---

### 10.3 防止真实 provider 测试访问网络

所有测试必须离线。

真实 provider 成功路径必须通过 fake provider、monkeypatch 或 dependency injection 测试。

---

### 10.4 防止 API key 泄露

不要：

1. 把 API key 写入 sidecar JSON；
2. 把 API key 写入 batch output；
3. 把 API key 写入异常字符串；
4. 把 API key 写入 docs 示例；
5. 把 API key 写入 tests fixture；
6. 把 API key 写入 PROJECT_STATE.md 或 CHANGELOG.md。

---

### 10.5 防止输出目录路径不稳定

sidecar 路径应可预测。

不要使用随机文件名。

不要使用绝对路径作为 sidecar 文件名的一部分。

不要在不同平台上生成不一致路径。

---

## 11. 完成后需要运行的命令

建议先运行 CLI 测试：

```bash
uv run pytest tests/test_cli.py
```

如果新增了 batch LLM 测试文件，则运行：

```bash
uv run pytest tests/test_batch_llm_cli.py
```

最后运行完整测试：

```bash
uv run pytest
```

---

