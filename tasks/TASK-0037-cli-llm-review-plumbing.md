# TASK-0037: Add CLI LLM Review Plumbing

## 1. 背景

当前项目已经完成以下 LLM 语义审计基础层：

```text
TASK-0035: Add LLM provider interface and mock reviewer
  ✅ 已完成

TASK-0036: Add LLM semantic review runner
  ✅ 已完成
```

当前 LLM 层的数据流已经具备：

```text
LLMReviewRequest
        ↓
LLMReviewRunner
        ↓
LLMReviewer provider interface
        ↓
LLMReviewResult
```

但是目前该 LLM runner 还没有被 CLI 使用。

因此，本任务需要为现有单文件 `review` CLI 增加一个 **显式 opt-in 的 LLM review plumbing**，让 CLI 能够在用户明确开启时调用 `LLMReviewRunner`。

本任务只允许使用已有 `MockLLMReviewer`，不接入真实 LLM provider。

---

## 2. 任务目标

为现有单文件 CLI review 流程增加最小 LLM 接入能力。

本任务完成后，应支持：

1. 用户通过显式 CLI 参数启用 LLM review；
2. CLI 使用已有 `LLMReviewRunner`；
3. CLI 使用已有 `MockLLMReviewer`；
4. CLI 根据当前 review 输入构造 `LLMReviewRequest`；
5. CLI 运行 LLM review 后得到 `LLMReviewResult`；
6. CLI 可将 `LLMReviewResult` 写入独立 JSON sidecar 文件；
7. 当前默认 CLI 行为完全不变；
8. 当前 deterministic `ReviewResult` JSON 输出结构不变；
9. 当前 Markdown report 结构不变；
10. 当前 quality gate 行为不变。

本任务的核心目标是：

> 让 CLI 能够 opt-in 调用 LLM runner，但不把 LLM result 合并进现有 deterministic review result 或 report。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 给单文件 `review` command 增加 LLM opt-in 参数；
2. 使用 `LLMReviewRunner` 调用 LLM 审计流程；
3. 使用 `MockLLMReviewer` 作为当前唯一 provider；
4. 根据当前输入构造 `LLMReviewRequest`；
5. 将 `LLMReviewResult` 序列化为独立 JSON 文件；
6. 增加 CLI 层测试；
7. 更新 CLI 文档；
8. 更新架构文档；
9. 更新数据模型文档；
10. 更新 `PROJECT_STATE.md`；
11. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许接入真实 LLM provider；
2. 不允许引入 PydanticAI；
3. 不允许引入 OpenAI SDK；
4. 不允许引入 Anthropic SDK；
5. 不允许新增外部运行时依赖；
6. 不允许读取 API key；
7. 不允许读取 LLM 相关环境变量；
8. 不允许执行网络请求；
9. 不允许新增真实模型名配置；
10. 不允许把 LLM findings 合并进当前 deterministic `ReviewResult`；
11. 不允许改变当前 review JSON 输出结构；
12. 不允许改变当前 Markdown report 输出结构；
13. 不允许让 quality gate 统计 LLM findings；
14. 不允许修改 batch review 行为；
15. 不允许给 batch command 增加 LLM 参数；
16. 不允许新增 API、MCP、GUI 相关能力；
17. 不允许实现 retry、cache、streaming、token accounting、cost tracking、telemetry 等高级能力。

---

## 5. 需要修改的文件

预计需要修改或新增以下文件：

```text
src/content_review_engine/cli.py
tests/test_cli_llm.py
docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

如果现有 CLI 测试集中在 `tests/test_cli.py`，也可以选择更新该文件，而不是新增 `tests/test_cli_llm.py`。

如果为了避免 `cli.py` 变得过重，可以新增一个轻量 helper 文件，例如：

```text
src/content_review_engine/llm/cli.py
```

或：

```text
src/content_review_engine/llm/integration.py
```

但该 helper 只能负责 CLI 与 LLM runner 的轻量接线，不允许实现真实 provider 选择、网络请求或复杂 provider routing。

---

## 6. 实现要求

### 6.1 CLI 参数设计

只给单文件 `review` command 增加 LLM 参数。

建议新增以下参数：

```text
--enable-llm
--llm-provider mock
--llm-output <path>
```

含义如下：

#### `--enable-llm`

显式启用 LLM review plumbing。

默认不启用。

如果用户不传该参数，现有 CLI 行为必须完全不变。

#### `--llm-provider mock`

指定 LLM provider。

当前只允许：

```text
mock
```

如果用户传入其他值，应返回清晰错误信息，并以非零状态退出。

#### `--llm-output <path>`

指定 `LLMReviewResult` 的 JSON sidecar 输出路径。

本任务不把 LLM result 合并进当前 review JSON，也不加入 Markdown report，因此启用 LLM 时需要通过独立文件输出 LLM result。

推荐规则：

1. 如果传入 `--enable-llm`，则必须传入 `--llm-output`；
2. 如果传入 `--llm-output` 但没有传入 `--enable-llm`，应报错；
3. 如果传入 `--llm-provider` 但没有传入 `--enable-llm`，应报错；
4. `--llm-output` 输出 JSON 文件，编码为 UTF-8；
5. JSON 内容应使用已有 `LLMReviewResult` serialization helper；
6. 不要发明新的 LLM result schema。

---

### 6.2 CLI 行为要求

当用户没有启用 LLM 时：

```bash
content-review review input.md --profile profile.yml
```

现有行为必须完全不变。

当用户显式启用 LLM 时：

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider mock \
  --llm-output llm-review.json
```

CLI 应该：

1. 正常执行当前 deterministic review；
2. 根据当前输入构造 `LLMReviewRequest`；
3. 使用 `MockLLMReviewer`；
4. 创建 `LLMReviewRunner`；
5. 调用 runner；
6. 得到 `LLMReviewResult`；
7. 将 `LLMReviewResult` 写入 `--llm-output` 指定的 JSON 文件；
8. 保持当前主输出格式不变。

也就是说：

* 当前 `--format text` 输出不应被 LLM 内容污染；
* 当前 `--format json` 输出不应新增 `llm_review` 字段；
* 当前 `--format markdown` 输出不应新增 LLM section；
* quality gate 仍然只基于 deterministic findings 判断。

---

### 6.3 LLMReviewRequest 构造要求

CLI 应根据当前 review 输入构造 `LLMReviewRequest`。

要求：

1. 使用现有 `LLMReviewRequest` model；
2. 不新增重复的数据模型；
3. 不绕过现有 profile / input 读取逻辑；
4. 尽量复用当前已经读取的 Markdown 内容；
5. 不重复实现 Markdown reader；
6. 不重复实现 profile loader；
7. 不改变当前 deterministic review runner 的输入输出。

如果 `LLMReviewRequest` 当前需要字段包括：

```text
content
profile
file_path
metadata
```

则应按照现有 model 定义填充。

如果字段名称不同，以当前代码中的 `LLMReviewRequest` 为准。

---

### 6.4 Provider 选择规则

当前只允许 mock provider。

推荐实现：

```text
if provider == "mock":
    reviewer = MockLLMReviewer()
else:
    fail with unsupported provider error
```

不允许提前实现：

```text
openai
anthropic
pydanticai
local
custom
```

如果需要为未来保留扩展点，可以保留非常轻量的内部函数，例如：

```python
def build_llm_reviewer(provider: str) -> LLMReviewer:
    ...
```

但当前只能返回 `MockLLMReviewer`。

---

### 6.5 LLM 输出文件规则

`--llm-output` 应输出独立 JSON 文件。

输出内容应来自现有 `LLMReviewResult` serialization helper。

要求：

1. JSON 包含 `schema_version`；
2. 默认 mock result 应为 `llm-review-result.v1`；
3. 默认 mock result findings 为空；
4. JSON 应稳定可测试；
5. 不要把 deterministic review result 写入该文件；
6. 不要把 LLM result 合并回 deterministic review result。

---

### 6.6 错误处理规则

需要对以下情况给出清晰错误：

1. `--enable-llm` 但没有 `--llm-output`；
2. `--llm-output` 但没有 `--enable-llm`；
3. `--llm-provider` 但没有 `--enable-llm`；
4. `--llm-provider` 不是 `mock`；
5. LLM runner 或 provider 抛出 `LLMReviewError` / `LLMProviderError`。

错误处理要求：

1. 不要输出 Python traceback 给普通 CLI 用户；
2. 不要吞掉错误；
3. 不要静默成功；
4. 不要影响未启用 LLM 的默认 CLI 行为；
5. 退出码应与现有 CLI 错误处理风格一致。

---

### 6.7 与 batch command 的关系

本任务不支持 batch LLM review。

如果当前 CLI 有：

```bash
content-review batch ...
```

则本任务不应给 batch command 添加 LLM 参数。

batch LLM review 可以作为后续单独任务处理。

---

## 7. 测试要求

新增或更新 CLI 测试。

推荐新增：

```text
tests/test_cli_llm.py
```

如果现有项目习惯集中在 `tests/test_cli.py`，也可以在其中新增相关测试。

至少覆盖以下场景：

### 7.1 默认 CLI 行为不变

测试不传 LLM 参数时：

```bash
content-review review input.md --profile profile.yml
```

现有输出结构和退出行为不变。

尤其要确认：

1. 不生成 LLM sidecar 文件；
2. JSON 输出中不出现 `llm_review`；
3. Markdown 输出中不出现 LLM section；
4. quality gate 行为不变。

---

### 7.2 启用 mock LLM review 并写入 sidecar

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider mock \
  --llm-output llm-review.json
```

应验证：

1. 命令成功；
2. `llm-review.json` 被创建；
3. 文件为合法 JSON；
4. JSON 中包含 `schema_version`；
5. `schema_version` 等于 `llm-review-result.v1`；
6. mock 默认 findings 为空；
7. 主 review 输出仍保持原结构。

---

### 7.3 `--enable-llm` 缺少 `--llm-output` 应失败

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm
```

应验证：

1. 命令失败；
2. 退出码非零；
3. 错误信息说明启用 LLM 时必须提供 `--llm-output`。

---

### 7.4 `--llm-output` 未配合 `--enable-llm` 应失败

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --llm-output llm-review.json
```

应验证：

1. 命令失败；
2. 退出码非零；
3. 错误信息说明 `--llm-output` 需要配合 `--enable-llm` 使用。

---

### 7.5 不支持的 provider 应失败

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider openai \
  --llm-output llm-review.json
```

应验证：

1. 命令失败；
2. 退出码非零；
3. 错误信息说明当前只支持 `mock` provider；
4. 不创建 LLM output 文件。

---

### 7.6 `--llm-provider` 未配合 `--enable-llm` 应失败

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --llm-provider mock
```

应验证：

1. 命令失败；
2. 退出码非零；
3. 错误信息说明 `--llm-provider` 需要配合 `--enable-llm` 使用。

---

### 7.7 完整测试

最终运行：

```bash
uv run pytest
```

确保所有现有测试继续通过。

---

## 8. 文档更新要求

### 8.1 更新 docs/CLI.md

新增 LLM review experimental / mock-only 用法说明。

需要明确：

1. LLM CLI 当前是 experimental；
2. 必须显式传入 `--enable-llm`；
3. 当前只支持 `--llm-provider mock`；
4. 启用后必须传入 `--llm-output`；
5. LLM result 写入独立 JSON sidecar；
6. 当前不会改变主 review 输出；
7. 当前不会改变 Markdown report；
8. 当前不会影响 quality gate；
9. 当前没有真实 LLM provider，也不会调用网络。

示例：

```bash
content-review review input.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider mock \
  --llm-output llm-review.json
```

---

### 8.2 更新 docs/ARCHITECTURE.md

补充 CLI 与 LLM runner 的关系：

```text
CLI review command
        ↓
deterministic review flow
        ↓
optional --enable-llm
        ↓
LLMReviewRequest
        ↓
LLMReviewRunner
        ↓
MockLLMReviewer
        ↓
LLMReviewResult sidecar JSON
```

并明确：

1. 默认 CLI 不运行 LLM；
2. LLM 当前只支持 mock provider；
3. LLM result 不合并进 deterministic ReviewResult；
4. real provider 将在后续任务实现；
5. report integration 将在后续任务实现；
6. batch LLM review 不在本任务范围。

---

### 8.3 更新 docs/DATA_MODELS.md

补充说明：

1. `LLMReviewResult` 可以通过 CLI sidecar JSON 输出；
2. sidecar JSON 与当前 deterministic review JSON 是两个独立输出；
3. 当前 `ReviewResult` schema 不变；
4. 当前 Markdown report schema 不变；
5. 当前 quality gate 不读取 LLM result。

---

### 8.4 更新 PROJECT_STATE.md

记录：

1. `TASK-0037` 已完成；
2. 单文件 CLI 可以 opt-in 调用 LLM runner；
3. 当前 provider 仍然只支持 mock；
4. LLM result 通过独立 JSON sidecar 输出；
5. 默认 CLI 行为不变；
6. 真实 provider、report integration、batch LLM review 尚未实现。

---

### 8.5 更新 CHANGELOG.md

记录：

1. 新增 CLI LLM opt-in 参数；
2. 新增 mock-only LLM CLI plumbing；
3. 新增 LLM sidecar JSON 输出；
4. 新增 CLI LLM 测试；
5. 更新 CLI / architecture / data model 文档；
6. 明确未引入真实 provider、PydanticAI、JSON review schema 变化、Markdown report 变化或 quality gate 变化。

---

## 9. 验收标准

本任务完成后应满足：

1. 单文件 `review` command 支持 `--enable-llm`；
2. 单文件 `review` command 支持 `--llm-provider mock`；
3. 单文件 `review` command 支持 `--llm-output <path>`；
4. 默认不传 LLM 参数时，CLI 行为完全不变；
5. 启用 LLM 时，CLI 使用 `LLMReviewRunner`；
6. 启用 LLM 时，CLI 使用 `MockLLMReviewer`；
7. 启用 LLM 时，CLI 输出独立 `LLMReviewResult` JSON sidecar；
8. 当前主 JSON review output 不新增 `llm_review` 字段；
9. 当前 Markdown report 不新增 LLM section；
10. 当前 quality gate 不统计 LLM findings；
11. unsupported provider 会失败；
12. 参数组合错误会失败；
13. batch command 不支持 LLM；
14. 新增或更新 CLI LLM 测试；
15. `docs/CLI.md` 已更新；
16. `docs/ARCHITECTURE.md` 已更新；
17. `docs/DATA_MODELS.md` 已更新；
18. `PROJECT_STATE.md` 已更新；
19. `CHANGELOG.md` 已更新；
20. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

### 10.1 防止把 mock plumbing 误写成真实 LLM 集成

本任务只允许 mock provider。

不要添加：

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
PydanticAI Agent
OpenAI client
Anthropic client
model name
base_url
temperature
max_tokens
prompt template registry
```

这些属于后续真实 provider 任务。

---

### 10.2 防止污染当前输出 schema

本任务不应改变当前 deterministic review output。

不要在当前 review JSON 中添加：

```json
{
  "llm_review": {}
}
```

不要在 Markdown report 中添加：

```md
## LLM Review
```

这些属于后续 report integration 任务。

---

### 10.3 防止影响 quality gate

LLM result 当前只是 sidecar 输出，不参与 quality gate。

不要让 LLM findings 影响：

```text
exit code
fail-on
matched gate findings
severity counts
rule counts
batch summary
```

---

### 10.4 防止 batch 范围膨胀

本任务只处理单文件 review command。

batch LLM review 应作为后续独立任务。

---

## 11. 完成后需要运行的命令

建议先运行 CLI LLM 相关测试：

```bash
uv run pytest tests/test_cli_llm.py
```

如果相关测试写在 `tests/test_cli.py`，则运行：

```bash
uv run pytest tests/test_cli.py
```

最后必须运行完整测试：

```bash
uv run pytest
```

---

