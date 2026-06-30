# TASK-0084: Add Stable Combined Review Envelope Models

## 1. 背景

当前项目已经完成 deterministic review 主线能力，包括：

1. Markdown / text 内容读取；
2. ReviewProfile 加载；
3. deterministic rule engine；
4. single-file / batch CLI；
5. JSON / Markdown 输出；
6. quality gate / CI；
7. LLM provider boundary；
8. LLM runner；
9. LLM sidecar output；
10. explicit combined output；
11. combined output 文档、reference examples 和兼容性测试。

上一张任务卡 `TASK-0083` 已经完成 combined output 的文档固化，明确了：

1. `--output` 是 deterministic 主输出；
2. `--llm-output` 是 raw LLM sidecar；
3. `--combined-output` 是 explicit opt-in 的 combined envelope / combined report；
4. 三者可以并存，互不替代；
5. `--combined-output` 不会自动启用 LLM；
6. LLM findings 不进入 deterministic findings；
7. LLM findings 不参与 `--fail-on`、quality gate 或 exit code；
8. single-file / batch 的 combined JSON 和 combined Markdown reference artifacts 已经补齐。

但是当前 combined output 仍然可能存在一个问题：

> combined output 行为虽然已经可用并被文档化，但其构建逻辑需要进一步收敛为稳定、可复用、可测试的 runtime-level envelope 构建层，避免 CLI、report、future API、future MCP 在后续各自拼接 combined 结构。

因此，本任务的目标不是改变 CLI 行为，而是把现有 combined output 的构建逻辑整理成明确的内部模型 / helper / serializer contract。

---

## 2. 任务目标

本任务目标是：

> 为 single-file 和 batch review 的 combined output 增加稳定的 runtime-level combined review envelope 构建层，并让现有 `--combined-output` 路径复用该构建层，同时保持现有行为、schema、文档边界和 quality gate 语义不变。

完成后应达到：

1. single-file combined JSON 不再由 CLI 直接临时拼接；
2. batch combined JSON 不再由 CLI 直接临时拼接；
3. combined envelope 的构建逻辑集中在明确模块中；
4. 现有 CLI 行为保持兼容；
5. 现有 reference examples 保持兼容；
6. LLM findings 仍然不进入 deterministic findings；
7. LLM findings 仍然不影响 quality gate / exit code；
8. 后续 API / MCP / GUI 可以复用 combined envelope 构建逻辑。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增或整理 combined review envelope 的内部构建模块。
2. 为 single-file review 增加 combined envelope builder / serializer。
3. 为 batch review 增加 combined envelope builder / serializer。
4. 让现有 `--combined-output` JSON 输出路径复用新的 combined envelope builder。
5. 让现有 combined Markdown report 路径在合理范围内复用 shared combined data structure。
6. 增加单元测试，验证 combined envelope 的稳定结构。
7. 增加 CLI 回归测试，验证 `--combined-output` 行为未漂移。
8. 更新文档中关于 runtime combined envelope contract 的说明。
9. 更新 `PROJECT_STATE.md` 和 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许把 LLM findings 合并进 deterministic `ReviewResult.findings`。
2. 不允许让 LLM findings 进入 deterministic `severity_counts`。
3. 不允许让 LLM findings 进入 deterministic `rule_counts`。
4. 不允许让 LLM findings 影响 `--fail-on`。
5. 不允许让 LLM findings 影响 quality gate。
6. 不允许让 LLM findings 改变 CLI exit code。
7. 不允许让 `--combined-output` 自动启用 LLM。
8. 不允许改变 `--output` 的 deterministic 主输出语义。
9. 不允许改变 `--llm-output` 的 raw LLM sidecar 语义。
10. 不允许改变现有 provider interface。
11. 不允许接入新的真实 LLM provider。
12. 不允许修改 PydanticAI provider 的真实调用逻辑。
13. 不允许新增 API / MCP / GUI。
14. 不允许引入 Supabase、数据库、用户系统或商业化能力。
15. 不允许大规模重构 deterministic review engine。
16. 不允许删除或弱化现有 combined output 文档边界。
17. 不允许为了通过测试而降低 examples 或 docs 测试的覆盖要求。

---

## 5. 预计需要修改的文件

预计包括但不限于：

```text
src/content_review_engine/reports/combined.py
src/content_review_engine/reports/__init__.py
src/content_review_engine/cli.py

tests/test_llm_combined_output_models.py
tests/test_llm_single_file_combined_cli_output.py
tests/test_llm_batch_combined_cli_output.py
tests/test_llm_artifact_examples.py
tests/test_llm_combined_output_docs.py

docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果仓库中已经存在更合适的 combined output 模块，请优先复用现有位置，不要重复创建语义相同的模块。

如果当前 combined output builder 已经存在，请不要再新增平行实现，而是补齐类型、测试、文档和复用关系。

---

## 6. 实现要求

### 6.1 Combined envelope builder

需要新增或整理清晰的 combined envelope builder。

建议提供类似以下能力，具体命名应遵循仓库现有风格：

```python
build_single_file_combined_review_envelope(...)
build_batch_combined_review_envelope(...)
combined_review_envelope_to_dict(...)
```

如果项目当前使用 dataclass / Pydantic model / plain dict helper 中的某一种风格，应遵循现有风格，不要为了本任务引入不必要的新模式。

### 6.2 Single-file combined envelope

single-file combined envelope 应复用现有 deterministic review result 和 LLM review result。

它应保持现有 combined JSON reference artifact 的结构兼容。

本任务不要求重新设计 schema。

如果现有 reference artifact 已经定义了字段名、字段层级、schema version、metadata 结构，则应保持兼容。

### 6.3 Batch combined envelope

batch combined envelope 应复用现有 batch deterministic result 和 batch LLM sidecar result。

它应保持现有 batch combined JSON reference artifact 的结构兼容。

需要特别注意：

1. batch 文件顺序应保持 deterministic；
2. 每个文件的 deterministic result 和 LLM result 应能稳定对应；
3. 不应因为某个文件没有 LLM result 就破坏 batch envelope；
4. 不应让 LLM findings 参与 batch deterministic summary；
5. 不应让 LLM findings 影响 batch quality gate。

### 6.4 CLI 复用要求

现有 CLI 中 `--combined-output` 的 JSON 输出路径应复用新的 combined envelope builder。

CLI 仍然只负责：

1. 参数解析；
2. 调用 deterministic review；
3. 可选调用 LLM review；
4. 调用 combined envelope builder；
5. 写出结果文件。

CLI 不应继续承载复杂 combined JSON 拼接逻辑。

### 6.5 Markdown combined report 要求

如果当前 combined Markdown report 已经存在，本任务只允许做轻量整理：

1. 可以让 Markdown report 复用 combined envelope 的数据；
2. 可以减少重复拼接逻辑；
3. 不允许改变用户可见的主要 report 结构；
4. 不允许引入新的 report section 语义；
5. 不允许改变 deterministic-only quality gate 边界。

### 6.6 Schema version 要求

不得随意新增不兼容 schema version。

如果当前 combined output 已经使用类似：

```text
combined-review-result.v1
batch-combined-review-result.v1
```

或其他实际存在的 schema version，应继续沿用。

如果当前没有明确常量，可以新增常量，但必须与现有 examples / docs / tests 保持一致。

### 6.7 Backward compatibility 要求

本任务必须保持以下行为不变：

1. 不传 `--combined-output` 时，不生成 combined artifact；
2. 只传 `--output` 时，只生成 deterministic output；
3. 只传 `--llm-output` 时，只生成 raw LLM sidecar；
4. 同时传 `--output`、`--llm-output`、`--combined-output` 时，三者都可以生成；
5. `--combined-output` 不自动启用 LLM；
6. 没有启用 LLM 时，combined output 中不得伪造 LLM findings；
7. LLM provider 失败时，应保持现有错误处理语义；
8. quality gate 仍然只看 deterministic findings。

---

## 7. 测试要求

本任务必须新增或更新测试。

### 7.1 新增 combined envelope unit tests

建议新增：

```text
tests/test_llm_combined_output_models.py
```

测试至少覆盖：

1. single-file combined envelope 的基本结构；
2. single-file combined envelope 包含 deterministic result；
3. single-file combined envelope 包含 LLM result；
4. single-file combined envelope 不污染 deterministic findings；
5. batch combined envelope 的基本结构；
6. batch combined envelope 保持文件顺序；
7. batch combined envelope 不污染 deterministic summary；
8. envelope serialization 输出 JSON-compatible dict；
9. schema version 与 docs / examples 保持一致。

### 7.2 更新 CLI regression tests

需要更新或确认以下测试仍然通过：

```text
tests/test_llm_single_file_combined_cli_output.py
tests/test_llm_batch_combined_cli_output.py
```

测试重点：

1. CLI `--combined-output` 仍然能生成文件；
2. 输出 JSON 仍然可解析；
3. 输出字段与 reference examples 兼容；
4. `--combined-output` 不自动启用 LLM；
5. `--output`、`--llm-output`、`--combined-output` 可以并存；
6. quality gate exit code 不受 LLM findings 影响。

### 7.3 更新 examples compatibility tests

需要确认以下测试仍然通过：

```text
tests/test_llm_artifact_examples.py
tests/test_llm_combined_output_docs.py
```

测试重点：

1. examples 中的 combined JSON 仍然可解析；
2. examples 中的 combined Markdown 仍然包含关键标题；
3. examples 不含 API key、secret、traceback；
4. docs 中的 combined output 行为说明仍然存在。

### 7.4 全量测试

完成后必须运行：

```bash
uv run pytest
```

---

## 8. 文档更新要求

本任务需要更新以下文档：

```text
docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/LLM_PROVIDER_USAGE.md
PROJECT_STATE.md
CHANGELOG.md
```

### 8.1 docs/CLI.md

需要补充或确认：

1. `--combined-output` 仍然是 explicit opt-in；
2. `--combined-output` 现在由稳定 combined envelope builder 生成；
3. `--output` / `--llm-output` / `--combined-output` 边界不变；
4. quality gate 仍然 deterministic-only。

### 8.2 docs/ARCHITECTURE.md

需要补充 combined envelope 在架构中的位置。

建议说明：

```text
deterministic review result
        +
LLM sidecar result
        ↓
combined review envelope builder
        ↓
combined JSON / combined Markdown artifact
```

并强调：

1. combined envelope 是 reporting / artifact 层能力；
2. 它不改变 deterministic review engine；
3. 它不改变 quality gate；
4. 它为未来 API / MCP / GUI 提供可复用数据结构。

### 8.3 docs/DATA_MODELS.md

需要补充 combined envelope 的数据契约说明。

重点说明：

1. single-file combined envelope；
2. batch combined envelope；
3. deterministic result 和 LLM sidecar result 的关系；
4. LLM findings 不进入 deterministic counts；
5. schema version / serialization contract。

### 8.4 docs/LLM_PROVIDER_USAGE.md

需要补充：

1. LLM provider 输出仍然是 raw sidecar；
2. combined envelope 是 provider 之后的 artifact 层组合；
3. provider 不负责 deterministic + LLM 合并；
4. `--combined-output` 不自动启用 provider。

### 8.5 PROJECT_STATE.md

记录 TASK-0084 已完成的能力和当前阶段状态。

### 8.6 CHANGELOG.md

记录本次新增的 combined envelope builder、测试和文档更新。

---

## 9. 验收标准

满足以下条件即可认为任务完成：

1. 新增或整理了稳定 combined envelope builder；
2. single-file `--combined-output` 复用该 builder；
3. batch `--combined-output` 复用该 builder；
4. existing combined output examples 保持兼容；
5. deterministic output 行为不变；
6. LLM sidecar output 行为不变；
7. quality gate 行为不变；
8. CLI exit code 行为不变；
9. 文档补充了 runtime combined envelope contract；
10. 新增或更新了必要测试；
11. 全量测试通过。

---

## 10. 风险与注意事项

### 10.1 不要把 combined envelope 误做成主 ReviewResult

本任务的目标是为 combined output 建立稳定 envelope，不是把 LLM findings 直接塞进 deterministic `ReviewResult`。

当前主线边界仍然是：

```text
ReviewResult = deterministic result
LLMReviewResult = raw LLM sidecar
CombinedReviewEnvelope = explicit artifact-layer composition
```

### 10.2 不要改变 quality gate

当前项目已经明确：

```text
quality gate = deterministic-only
```

本任务不得改变该边界。

### 10.3 不要引入真实 LLM 调用变化

本任务不需要接入新的 provider，也不需要改变 PydanticAI provider 逻辑。

### 10.4 不要制造重复模型

如果仓库里已经存在 combined output helper，应优先收敛和复用，不要新增平行实现。

### 10.5 不要过度抽象

本任务只需要让当前 single-file / batch combined output 有稳定构建层，不需要设计未来所有 API / MCP / GUI 场景。

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_llm_combined_output_models.py
uv run pytest tests/test_llm_single_file_combined_cli_output.py
uv run pytest tests/test_llm_batch_combined_cli_output.py
uv run pytest tests/test_llm_artifact_examples.py
uv run pytest tests/test_llm_combined_output_docs.py
uv run pytest tests/test_cli.py
uv run pytest
```

如果某些测试文件不存在，应根据本任务实际新增或更新后的文件名运行对应测试，并在最终输出中说明。

---

