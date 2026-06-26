# TASK-0039: Add Optional LLM Markdown Report Integration

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
```

当前 LLM 层已经支持：

```text
content-review review
        ↓
optional --enable-llm
        ↓
LLMReviewRequest
        ↓
LLMReviewRunner
        ↓
LLMReviewer interface
        ↓
MockLLMReviewer / PydanticAIOpenAIReviewer
        ↓
LLMReviewResult sidecar JSON
```

目前 LLM 审计结果只会写入独立 sidecar JSON，不会进入 Markdown report。

因此，本任务需要为 **单文件 Markdown report** 增加一个显式 opt-in 的 LLM 展示能力：

```text
ReviewResult
        +
optional LLMReviewResult
        ↓
Markdown report with optional LLM Review section
```

本任务只允许把已有 `LLMReviewResult` 渲染进 Markdown report，不允许改变主 review JSON schema，不允许改变 quality gate，不允许做 batch LLM report，不允许新增 API / MCP / GUI。

---

## 2. 任务目标

为单文件 Markdown report 增加可选 LLM section。

本任务完成后，应支持：

1. 当用户没有启用 LLM report integration 时，现有 Markdown report 完全不变；
2. 当用户显式启用 LLM report integration 时，Markdown report 末尾新增 `## LLM Review` section；
3. LLM section 使用已有 `LLMReviewResult` 数据；
4. LLM section 能展示 schema version、finding count、severity counts 和 finding details；
5. 空 LLM findings 时显示明确的空结果说明；
6. CLI 可以通过显式参数控制是否把 LLM result 写入 Markdown report；
7. LLM sidecar JSON 仍然保持；
8. 主 review JSON schema 不变；
9. Markdown report 的 deterministic 部分不变；
10. quality gate 不读取 LLM findings；
11. batch review 不支持 LLM report integration；
12. API / MCP / GUI 不变。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 新增或扩展 Markdown report renderer，使其可以可选接收 `LLMReviewResult`；
2. 新增 LLM Markdown section 渲染函数；
3. 给单文件 `review` command 增加显式参数，用于控制是否把 LLM result 包含进 Markdown report；
4. 当用户启用该参数时，在 `--format markdown` 输出中附加 LLM section；
5. 继续保留 LLM sidecar JSON 输出；
6. 新增 report renderer 测试；
7. 新增 CLI 测试；
8. 更新 CLI 文档；
9. 更新架构文档；
10. 更新数据模型文档；
11. 更新 `PROJECT_STATE.md`；
12. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许改变当前 deterministic `ReviewResult` schema；
2. 不允许给主 JSON review output 新增 `llm_review` 字段；
3. 不允许让 quality gate 统计 LLM findings；
4. 不允许改变 deterministic severity counts；
5. 不允许改变 deterministic rule counts；
6. 不允许改变 deterministic findings 顺序；
7. 不允许改变 batch review 行为；
8. 不允许给 batch command 增加 LLM report integration；
9. 不允许新增 API；
10. 不允许新增 MCP；
11. 不允许新增 GUI；
12. 不允许新增 streaming；
13. 不允许新增 retry policy；
14. 不允许新增 cache；
15. 不允许新增 token accounting；
16. 不允许新增 cost tracking；
17. 不允许新增 telemetry；
18. 不允许新增 tracing / Logfire 集成；
19. 不允许新增 prompt template registry；
20. 不允许修改真实 provider 行为；
21. 不允许修改 `MockLLMReviewer` 的默认语义；
22. 不允许在未传 `--enable-llm` 时运行 LLM；
23. 不允许在未显式启用 LLM report integration 时改变 Markdown report 输出。

---

## 5. 需要修改的文件

预计需要修改或新增以下文件：

```text
src/content_review_engine/reports/markdown.py
src/content_review_engine/cli.py
tests/test_markdown_report.py
tests/test_cli.py
docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前项目已有专门的 LLM CLI 测试文件，也可以新增或更新：

```text
tests/test_cli_llm.py
```

如果当前 Markdown report 测试已经拆分，也可以根据现有结构更新对应测试文件。

如果任务卡文件尚不存在，也可以新增：

```text
tasks/TASK-0039-llm-markdown-report-integration.md
```

---

## 6. 实现要求

### 6.1 CLI 参数设计

新增一个显式 opt-in 参数。

推荐参数名：

```text
--include-llm-report
```

含义：

> 当 `--format markdown` 且 `--enable-llm` 同时启用时，把本次运行产生的 `LLMReviewResult` 附加到 Markdown report 中。

示例：

```bash
content-review review input.md \
  --profile profile.yml \
  --format markdown \
  --enable-llm \
  --llm-provider mock \
  --llm-output llm-review.json \
  --include-llm-report
```

真实 provider 示例：

```bash
content-review review input.md \
  --profile profile.yml \
  --format markdown \
  --enable-llm \
  --llm-provider pydanticai-openai \
  --llm-model gpt-5-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-output llm-review.json \
  --include-llm-report
```

---

### 6.2 参数校验规则

需要补充以下校验：

1. `--include-llm-report` 必须配合 `--enable-llm` 使用；
2. `--include-llm-report` 必须配合 `--format markdown` 使用；
3. `--include-llm-report` 不能用于 `--format json`；
4. `--include-llm-report` 不能用于 `--format text`；
5. `--include-llm-report` 不支持 batch command；
6. 启用 `--include-llm-report` 时，仍然必须满足现有 LLM 参数约束，例如 `--llm-output` 必填；
7. 参数错误应按现有 CLI 风格返回，不应抛 Python traceback。

---

### 6.3 Markdown report renderer 设计

当前 Markdown report renderer 应保持向后兼容。

推荐方式是在现有 report render function 上增加可选参数，例如：

```python
def render_markdown_report(
    result: ReviewResult,
    *,
    llm_result: LLMReviewResult | None = None,
) -> str:
    ...
```

如果现有函数签名不同，应遵循现有项目风格。

要求：

1. `llm_result` 默认为 `None`；
2. 当 `llm_result is None` 时，输出必须与当前 Markdown report 完全一致；
3. 当 `llm_result` 不为 `None` 时，在 deterministic report 后附加 `## LLM Review` section；
4. 不改变 deterministic Summary；
5. 不改变 deterministic Severity Counts；
6. 不改变 deterministic Rule Counts；
7. 不改变 deterministic Findings；
8. 不改变 deterministic Detailed Findings；
9. 不让 LLM findings 参与 deterministic counts。

如果担心主 render 函数膨胀，可以新增 helper：

```python
def render_llm_review_markdown_section(llm_result: LLMReviewResult) -> str:
    ...
```

并由主 render 函数可选调用。

---

### 6.4 LLM Markdown section 内容

新增 section 标题：

```md
## LLM Review
```

建议结构：

```md
## LLM Review

### LLM Summary

| Field | Value |
| --- | --- |
| Schema Version | llm-review-result.v1 |
| Total Findings | 0 |

### LLM Severity Counts

| Severity | Count |
| --- | --- |
| critical | 0 |
| error | 0 |
| warning | 0 |
| info | 0 |

### LLM Findings

No LLM findings.
```

当存在 findings 时，建议渲染为表格：

```md
### LLM Findings

| Severity | Rule | Message | Suggestion |
| --- | --- | --- | --- |
| warning | llm.overclaim | ... | ... |
```

如果 `LLMReviewResult` 中包含 location、line、column、context、matched_text 等字段，可以增加：

```md
### LLM Detailed Findings
```

逐条展示：

```md
#### LLM Finding 1

- Severity: warning
- Rule: llm.overclaim
- Location: line 12, column 3
- Message: ...
- Suggestion: ...
- Context: ...
```

实际字段应以当前 `LLMReviewResult` / finding model 为准，不要发明模型中不存在的数据。

---

### 6.5 Markdown escaping 要求

LLM 输出来自模型，可能包含 Markdown 特殊字符。

渲染时应注意：

1. 表格单元格中的 `|` 需要转义或替换；
2. 换行应处理为 `<br>` 或安全的单行文本；
3. 空字段应渲染为 `-`；
4. 不要让 LLM 输出破坏 Markdown 表格；
5. 不要渲染原始未处理的多行文本到表格单元格；
6. 不要把 API key、provider secret 或环境变量值写入 report。

---

### 6.6 与 sidecar JSON 的关系

本任务不取消 sidecar JSON。

当启用 LLM 时，仍然要求：

```text
--llm-output <path>
```

即使启用了：

```text
--include-llm-report
```

也仍然要写 sidecar JSON。

理由：

1. sidecar JSON 是结构化机器可读结果；
2. Markdown report 是人类可读展示；
3. 两者职责不同；
4. 后续 API / MCP / 前端可继续使用 sidecar schema。

---

### 6.7 与 JSON 输出的关系

本任务不改变 JSON review output。

以下命令输出的主 JSON 不应新增 `llm_review`：

```bash
content-review review input.md \
  --profile profile.yml \
  --format json \
  --enable-llm \
  --llm-provider mock \
  --llm-output llm-review.json
```

如果用户在 `--format json` 下使用 `--include-llm-report`，应报错，因为该参数只适用于 Markdown report。

---

### 6.8 与 quality gate 的关系

LLM findings 当前不参与 quality gate。

即使 Markdown report 展示了 LLM findings，也不应影响：

```text
exit code
fail-on
matched gate findings
severity counts
rule counts
batch summary
```

quality gate 仍然只基于 deterministic findings。

---

### 6.9 与 batch command 的关系

本任务不支持 batch LLM report。

不要给以下命令添加 LLM report 参数：

```bash
content-review batch ...
```

batch LLM report 可以作为后续独立任务。

---

## 7. 测试要求

### 7.1 Markdown report renderer 测试

更新或新增：

```text
tests/test_markdown_report.py
```

至少覆盖：

#### 默认输出不变

1. 不传 `llm_result` 时，Markdown report 输出与当前 expected report fixture 一致；
2. deterministic Summary 不变；
3. deterministic Severity Counts 不变；
4. deterministic Rule Counts 不变；
5. deterministic Findings 不变；
6. deterministic Detailed Findings 不变。

#### 空 LLM result

传入空 `LLMReviewResult` 时，应验证：

1. 输出包含 `## LLM Review`；
2. 输出包含 `Schema Version`；
3. 输出包含 `llm-review-result.v1`；
4. 输出包含 `Total Findings | 0` 或等价内容；
5. 输出包含 `No LLM findings.`；
6. deterministic 部分仍然不变。

#### 非空 LLM result

构造包含至少一个 finding 的 `LLMReviewResult`，验证：

1. 输出包含 `## LLM Review`；
2. 输出包含 finding severity；
3. 输出包含 finding rule id；
4. 输出包含 finding message；
5. 输出包含 finding suggestion；
6. 如果模型中有 context/location 字段，输出包含对应 details；
7. deterministic severity counts 不包含 LLM finding；
8. deterministic rule counts 不包含 LLM finding。

#### Markdown escaping

构造包含特殊字符的 LLM finding，例如：

```text
message: "A | B"
suggestion: "Line 1\nLine 2"
```

验证：

1. Markdown 表格不被破坏；
2. `|` 被安全处理；
3. 换行被安全处理；
4. 输出仍是稳定字符串。

---

### 7.2 CLI 测试

更新：

```text
tests/test_cli.py
```

或新增：

```text
tests/test_cli_llm_report.py
```

至少覆盖：

#### 默认 Markdown report 不变

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --format markdown
```

验证：

1. 输出不包含 `## LLM Review`；
2. 现有 Markdown report 输出结构不变。

#### 启用 LLM 但不 include report

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --format markdown \
  --enable-llm \
  --llm-provider mock \
  --llm-output llm-review.json
```

验证：

1. sidecar JSON 被创建；
2. Markdown report 不包含 `## LLM Review`；
3. 行为保持 TASK-0037 / TASK-0038 语义。

#### 启用 LLM 并 include report

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --format markdown \
  --enable-llm \
  --llm-provider mock \
  --llm-output llm-review.json \
  --include-llm-report
```

验证：

1. 命令成功；
2. sidecar JSON 被创建；
3. Markdown report 包含 `## LLM Review`；
4. Markdown report 包含 `llm-review-result.v1`；
5. Markdown report 包含 `No LLM findings.` 或 mock finding 内容；
6. deterministic report 部分保持不变。

#### `--include-llm-report` 未配合 `--enable-llm` 应失败

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --format markdown \
  --include-llm-report
```

应失败并返回清晰错误。

#### `--include-llm-report` 用于 JSON 应失败

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --format json \
  --enable-llm \
  --llm-provider mock \
  --llm-output llm-review.json \
  --include-llm-report
```

应失败并说明该参数只支持 Markdown report。

#### `--include-llm-report` 用于 text 应失败

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --format text \
  --enable-llm \
  --llm-provider mock \
  --llm-output llm-review.json \
  --include-llm-report
```

应失败并说明该参数只支持 Markdown report。

#### JSON schema 仍然不变

测试：

```bash
content-review review input.md \
  --profile profile.yml \
  --format json \
  --enable-llm \
  --llm-provider mock \
  --llm-output llm-review.json
```

验证主 JSON 仍然不包含：

```text
llm_review
```

#### quality gate 不受影响

构造一个 LLM finding，但 deterministic review 不触发 gate，验证：

1. exit code 不受 LLM finding 影响；
2. quality gate 只基于 deterministic findings；
3. LLM finding 只展示在 Markdown report 或 sidecar JSON。

可以通过 fake reviewer 或 monkeypatch 构造 LLM finding。

---

### 7.3 完整测试

最终运行：

```bash
uv run pytest
```

确保所有测试通过。

---

## 8. 文档更新要求

### 8.1 更新 docs/CLI.md

补充 `--include-llm-report` 用法。

需要说明：

1. 该参数是 explicit opt-in；
2. 仅适用于单文件 `review` command；
3. 仅适用于 `--format markdown`；
4. 必须配合 `--enable-llm` 使用；
5. 启用后仍然需要 `--llm-output`；
6. LLM result 会同时写入 sidecar JSON 和 Markdown report；
7. Markdown report 中的 LLM section 不影响 quality gate；
8. 主 JSON review output 不会新增 `llm_review`；
9. batch command 暂不支持该能力。

示例：

```bash
content-review review input.md \
  --profile profile.yml \
  --format markdown \
  --enable-llm \
  --llm-provider mock \
  --llm-output llm-review.json \
  --include-llm-report
```

真实 provider 示例：

```bash
content-review review input.md \
  --profile profile.yml \
  --format markdown \
  --enable-llm \
  --llm-provider pydanticai-openai \
  --llm-model gpt-5-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-output llm-review.json \
  --include-llm-report
```

---

### 8.2 更新 docs/ARCHITECTURE.md

补充 LLM report integration 数据流：

```text
CLI review command
        ↓
deterministic ReviewResult
        ↓
optional LLMReviewResult
        ↓
Markdown report renderer
        ↓
deterministic report sections
        +
optional LLM Review section
```

并明确：

1. LLM report section 是可选展示层；
2. LLM result 不合并进 deterministic `ReviewResult`；
3. quality gate 不读取 LLM result；
4. JSON output schema 不变；
5. batch LLM report 不在本任务范围；
6. API / MCP / GUI 不在本任务范围。

---

### 8.3 更新 docs/DATA_MODELS.md

补充：

1. `LLMReviewResult` 可以作为 Markdown report 的可选输入；
2. `ReviewResult` schema 仍然不变；
3. `LLMReviewResult` schema 仍然独立；
4. sidecar JSON 仍然是机器可读 LLM 输出；
5. Markdown LLM section 是人类可读展示；
6. LLM findings 不进入 deterministic severity counts / rule counts。

---

### 8.4 更新 PROJECT_STATE.md

记录：

1. TASK-0039 已完成；
2. 单文件 Markdown report 支持 optional LLM Review section；
3. 该能力通过显式参数启用；
4. sidecar JSON 仍然保留；
5. 主 JSON schema 不变；
6. quality gate 不受 LLM findings 影响；
7. batch LLM report 尚未实现；
8. API / MCP / GUI 尚未实现。

---

### 8.5 更新 CHANGELOG.md

记录：

1. 新增 optional LLM Markdown report integration；
2. 新增 `--include-llm-report`；
3. 新增 LLM Markdown section renderer；
4. 新增 report 和 CLI 测试；
5. 更新 CLI / architecture / data model 文档；
6. 明确未改变 review JSON schema、quality gate、batch、API、MCP、GUI。

---

## 9. 验收标准

本任务完成后应满足：

1. Markdown report renderer 支持可选 `LLMReviewResult`；
2. 默认不传 LLM result 时，Markdown report 输出完全不变；
3. 传入 LLM result 时，Markdown report 包含 `## LLM Review`；
4. 空 LLM result 能显示明确空结果；
5. 非空 LLM result 能显示 findings；
6. Markdown escaping 稳定；
7. 单文件 review command 支持 `--include-llm-report`；
8. `--include-llm-report` 必须配合 `--enable-llm`；
9. `--include-llm-report` 只支持 `--format markdown`；
10. 启用 `--include-llm-report` 时仍然写 sidecar JSON；
11. 主 JSON review output 不包含 `llm_review`；
12. deterministic `ReviewResult` schema 不变；
13. deterministic report counts 不统计 LLM findings；
14. quality gate 不统计 LLM findings；
15. batch command 不支持 LLM report integration；
16. docs/CLI.md 已更新；
17. docs/ARCHITECTURE.md 已更新；
18. docs/DATA_MODELS.md 已更新；
19. PROJECT_STATE.md 已更新；
20. CHANGELOG.md 已更新；
21. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

### 10.1 防止把 report integration 变成 schema integration

本任务只是展示层集成。

不要把 LLM result 合并进：

```text
ReviewResult
batch summary
quality gate
JSON review output
```

---

### 10.2 防止默认输出变化

默认 Markdown report 必须不变。

只有显式传入：

```text
--include-llm-report
```

并且满足 LLM 参数时，才展示 LLM section。

---

### 10.3 防止 LLM findings 影响 gate

LLM findings 可以展示，但不能影响质量门禁。

---

### 10.4 防止 batch 范围膨胀

不要做 batch LLM report。

后续可以单独规划：

```text
TASK-0040: Add batch LLM sidecar collection
```

或：

```text
TASK-0040: Add batch LLM markdown report integration
```

但不在本任务中实现。

---

## 11. 完成后需要运行的命令

建议先运行 Markdown report 测试：

```bash
uv run pytest tests/test_markdown_report.py
```

再运行 CLI 测试：

```bash
uv run pytest tests/test_cli.py
```

最后运行完整测试：

```bash
uv run pytest
```

---

