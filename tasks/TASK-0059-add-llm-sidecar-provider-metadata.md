# TASK-0059: Add LLM Sidecar Provider Metadata

## 1. 背景

当前项目已经完成确定性内容审计主链路，包括 Markdown 读取、Profile 加载、规则审计、单文件 CLI、批量 CLI、JSON / Markdown 报告输出，以及 Quality Gate / CI 门禁。

LLM 语义审计阶段目前已经完成了以下能力：

1. `LLMReviewRequest`
2. `LLMReviewer` provider interface
3. `MockLLMReviewer`
4. `LLMReviewResult`
5. LLM semantic review runner
6. 单文件 LLM sidecar output
7. batch LLM sidecar output
8. `content-review llm-check` smoke check
9. `PydanticAITestModelReviewer`
10. `create_llm_reviewer()` provider factory
11. `UnsupportedLLMProviderError`
12. `content-review llm-check --provider`
13. 单文件 LLM sidecar `--llm-provider`
14. batch LLM sidecar `--llm-provider`

TASK-0057 已经让单文件 LLM sidecar 可以显式选择 provider。

TASK-0058 已经让 batch LLM sidecar 可以显式选择 provider。

但是当前 sidecar 输出中仍然缺少清晰的 provider metadata。也就是说，当用户拿到一个 sidecar JSON 文件时，无法稳定判断该 LLM 结果来自：

1. `mock`
2. `pydantic-ai-testmodel`
3. config-driven/default provider path

这会影响后续调试、审计、文档说明、测试 fixture 判断，以及将来真实 provider 接入后的结果追踪。

本任务的目标是：

> 在不改变主 ReviewResult / BatchReviewResult 的前提下，为 single / batch LLM sidecar envelope 增加 provider metadata。

本任务只修改 LLM sidecar 输出的 metadata，不接入真实 LLM API，不合并主审计结果，不修改 Markdown Report，不修改 Quality Gate。

---

## 2. 任务目标

为单文件和批量 LLM sidecar output 增加 provider metadata。

本任务完成后，sidecar JSON 应能表达：

1. 本次 sidecar 由哪个 provider 产生；
2. provider 是显式通过 `--llm-provider` 指定，还是走默认 / config-driven 路径；
3. single sidecar 和 batch sidecar 的 metadata 表达保持一致；
4. metadata 不污染主 `ReviewResult` / `BatchReviewResult`；
5. metadata 不改变 deterministic review 结果；
6. metadata 不要求真实 API key；
7. metadata 不访问外部网络。

建议 sidecar envelope 中新增类似字段：

```json
{
  "llm_provider": "pydantic-ai-testmodel",
  "llm_provider_source": "explicit"
}
```

或：

```json
{
  "llm_provider": "mock",
  "llm_provider_source": "default"
}
```

如果当前项目已有更合适的 envelope metadata 命名风格，请沿用现有风格，但必须保持 single / batch 一致。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 为单文件 LLM sidecar envelope 增加 provider metadata；
2. 为 batch LLM sidecar envelope 增加 provider metadata；
3. 明确记录 provider name；
4. 明确记录 provider selection source；
5. 支持显式 provider source，例如 `explicit`；
6. 支持默认 / config-driven provider source，例如 `default` 或 `config`;
7. 更新 sidecar serialization 逻辑；
8. 更新 sidecar 相关测试；
9. 更新 CLI 相关测试；
10. 更新 provider usage 文档测试；
11. 更新 CLI 文档；
12. 更新 LLM provider 使用文档；
13. 更新数据模型文档；
14. 更新架构文档；
15. 更新 `PROJECT_STATE.md`；
16. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不允许接入真实 OpenAI / Anthropic / Gemini / DeepSeek / Qwen / 本地模型 API；
2. 不允许读取 `.env`；
3. 不允许要求用户提供 API key；
4. 不允许新增 secret resolver；
5. 不允许新增真实 provider 配置；
6. 不允许修改 provider factory 支持范围；
7. 不允许新增新的 provider name；
8. 不允许修改 `content-review llm-check` 用户可见行为；
9. 不允许修改单文件 sidecar `--llm-provider` 用户可见行为；
10. 不允许修改 batch sidecar `--llm-provider` 用户可见行为；
11. 不允许让 `content-review review` 默认启用 LLM；
12. 不允许让 `content-review batch` 默认启用 LLM；
13. 不允许把 LLM 结果合并进主 `ReviewResult`；
14. 不允许把 LLM 结果合并进主 `BatchReviewResult`；
15. 不允许把 LLM findings 合并进 Markdown report；
16. 不允许修改 JSON report schema；
17. 不允许修改 Markdown report 结构；
18. 不允许修改 Quality Gate 行为；
19. 不允许修改 deterministic review 输出结构；
20. 不允许新增 API / MCP / GUI；
21. 不允许引入 LangChain / CrewAI；
22. 不允许让测试访问外部网络；
23. 不允许让测试依赖真实模型调用；
24. 不允许把 provider metadata 写入主审计结果。

---

## 5. 需要修改的文件

预计修改以下文件：

```text
src/content_review_engine/llm/sidecar.py
src/content_review_engine/cli.py
tests/test_llm_sidecar.py
tests/test_cli.py
tests/test_llm_provider_usage_docs.py
docs/CLI.md
docs/LLM_PROVIDER_USAGE.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前项目没有 `src/content_review_engine/llm/sidecar.py`，请沿用现有 sidecar serialization 所在文件。

如果 sidecar metadata 已经集中在某个模型或 serializer 中，请在该位置做最小修改，不要把 sidecar JSON 拼接逻辑散落到 CLI 中。

---

## 6. 实现要求

### 6.1 Provider Metadata 字段

建议在 sidecar envelope 中新增两个字段：

```json
{
  "llm_provider": "mock",
  "llm_provider_source": "explicit"
}
```

字段含义：

```text
llm_provider
  本次 sidecar 使用的 provider name。

llm_provider_source
  provider 的来源。
```

推荐 `llm_provider_source` 支持以下值：

```text
explicit
default
config
```

含义建议如下：

```text
explicit
  用户显式传入 --llm-provider。

default
  用户没有传入 --llm-provider，使用当前默认 sidecar provider 行为。

config
  用户没有传入 --llm-provider，sidecar 通过已有 config-driven path 创建 provider。
```

如果当前项目无法区分 `default` 和 `config`，可以只使用：

```text
explicit
default
```

但必须在测试和文档中固定语义。

---

### 6.2 Single Sidecar 行为

当用户运行：

```bash
content-review review input.md --profile profile.yml --enable-llm --llm-output llm.json --llm-provider mock
```

sidecar JSON 应包含类似：

```json
{
  "llm_provider": "mock",
  "llm_provider_source": "explicit"
}
```

当用户运行：

```bash
content-review review input.md --profile profile.yml --enable-llm --llm-output llm.json --llm-provider pydantic-ai-testmodel
```

sidecar JSON 应包含类似：

```json
{
  "llm_provider": "pydantic-ai-testmodel",
  "llm_provider_source": "explicit"
}
```

当用户省略 `--llm-provider` 时：

```bash
content-review review input.md --profile profile.yml --enable-llm --llm-output llm.json
```

sidecar JSON 也应包含 provider metadata。

如果能够稳定识别默认 provider name，则写入真实默认 provider name。

如果无法稳定识别默认 provider name，则可写入：

```json
{
  "llm_provider": "default",
  "llm_provider_source": "default"
}
```

或项目内更合适的等价表达。

但不得因为无法识别 provider name 而省略 metadata。

---

### 6.3 Batch Sidecar 行为

当用户运行：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output-dir llm-results --llm-provider mock
```

batch sidecar output 应包含类似：

```json
{
  "llm_provider": "mock",
  "llm_provider_source": "explicit"
}
```

当用户运行：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output-dir llm-results --llm-provider pydantic-ai-testmodel
```

batch sidecar output 应包含类似：

```json
{
  "llm_provider": "pydantic-ai-testmodel",
  "llm_provider_source": "explicit"
}
```

当用户省略 `--llm-provider` 时：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output-dir llm-results
```

batch sidecar output 也应包含 provider metadata。

如果 batch sidecar 是每个文件一个 sidecar JSON，则每个 sidecar JSON 都应包含 provider metadata。

如果 batch sidecar 有 batch-level index / manifest，则可以在 batch-level manifest 记录 provider metadata；但每个文件 sidecar 是否也记录，应与当前项目 sidecar envelope 结构保持一致。

---

### 6.4 不改变 LLMReviewResult Schema

本任务不应修改 `LLMReviewResult` 的核心 schema。

Provider metadata 应属于 sidecar envelope metadata，而不是 LLM review result 本体。

不得为了记录 provider 而修改 LLM finding 结构。

不得把 provider 写入每个 finding。

---

### 6.5 Sidecar Schema Version

如果当前 sidecar envelope 有独立 `schema_version`，请检查现有项目约定。

推荐处理：

1. 如果项目文档认为 sidecar envelope 添加字段是兼容变更，可以保持现有 sidecar schema version；
2. 如果项目文档认为 sidecar envelope 字段变化需要版本更新，则更新 sidecar schema version；
3. 无论是否更新 schema version，都必须更新测试和文档说明。

不得修改 `LLMReviewResult` 的 schema version，除非现有代码结构强制要求，并且必须在文档中说明原因。

---

### 6.6 CLI 责任边界

CLI 可以负责把用户是否传入 `--llm-provider` 这件事传递给 sidecar 写入逻辑。

但是 CLI 不应直接拼接 sidecar JSON metadata。

推荐设计：

```text
CLI
  解析 --llm-provider
  ↓
创建 reviewer
  ↓
传递 provider metadata 给 sidecar serializer
  ↓
sidecar serializer 写入 metadata
```

不推荐：

```text
CLI
  直接打开 JSON dict
  手动塞入 llm_provider 字段
```

sidecar 输出结构应集中在 sidecar serializer 中管理。

---

### 6.7 不改变默认审计行为

以下命令的默认行为不能改变：

```bash
content-review review input.md --profile profile.yml
content-review batch input_dir --profile profile.yml
content-review llm-check
```

本任务只改变启用 LLM sidecar 时 sidecar JSON 中的 metadata。

---

## 7. 测试要求

需要新增或更新测试，至少覆盖以下内容。

### 7.1 Single sidecar explicit mock metadata

测试：

```bash
content-review review input.md --profile profile.yml --enable-llm --llm-output llm.json --llm-provider mock
```

需要验证：

1. exit code 为 0；
2. sidecar 文件被创建；
3. sidecar JSON 包含 `llm_provider = mock`；
4. sidecar JSON 包含 `llm_provider_source = explicit`；
5. 主 `ReviewResult` 不包含 provider metadata；
6. 主 `ReviewResult` 不包含 LLM findings。

### 7.2 Single sidecar explicit pydantic-ai-testmodel metadata

测试：

```bash
content-review review input.md --profile profile.yml --enable-llm --llm-output llm.json --llm-provider pydantic-ai-testmodel
```

需要验证：

1. sidecar JSON 包含 `llm_provider = pydantic-ai-testmodel`；
2. sidecar JSON 包含 `llm_provider_source = explicit`；
3. 不需要 API key；
4. 不访问外部网络。

### 7.3 Single sidecar default metadata

测试：

```bash
content-review review input.md --profile profile.yml --enable-llm --llm-output llm.json
```

需要验证：

1. sidecar JSON 包含 provider metadata；
2. provider source 为 `default` 或 `config`；
3. 默认 sidecar 行为保持兼容。

### 7.4 Batch sidecar explicit mock metadata

测试：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output-dir llm-results --llm-provider mock
```

需要验证：

1. exit code 为 0；
2. batch sidecar 文件被创建；
3. sidecar JSON 包含 `llm_provider = mock`；
4. sidecar JSON 包含 `llm_provider_source = explicit`；
5. 主 `BatchReviewResult` 不包含 provider metadata；
6. 主 `BatchReviewResult` 不包含 LLM findings。

### 7.5 Batch sidecar explicit pydantic-ai-testmodel metadata

测试：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output-dir llm-results --llm-provider pydantic-ai-testmodel
```

需要验证：

1. sidecar JSON 包含 `llm_provider = pydantic-ai-testmodel`；
2. sidecar JSON 包含 `llm_provider_source = explicit`；
3. 不需要 API key；
4. 不访问外部网络。

### 7.6 Batch sidecar default metadata

测试：

```bash
content-review batch input_dir --profile profile.yml --enable-llm --llm-output-dir llm-results
```

需要验证：

1. sidecar JSON 包含 provider metadata；
2. provider source 为 `default` 或 `config`；
3. 默认 batch sidecar 行为保持兼容。

### 7.7 Sidecar schema compatibility

测试 sidecar envelope 仍然保留已有字段。

如果更新 sidecar schema version，需要测试新版本号。

如果不更新 sidecar schema version，需要测试添加字段是兼容扩展。

### 7.8 不影响默认 review / batch / llm-check

运行或保留测试，验证：

```bash
content-review review input.md --profile profile.yml
content-review batch input_dir --profile profile.yml
content-review llm-check
```

用户可见行为不变。

---

## 8. 文档更新要求

需要更新以下文档：

```text
docs/CLI.md
docs/LLM_PROVIDER_USAGE.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

### 8.1 docs/CLI.md

补充说明：

1. single sidecar JSON 会记录 provider metadata；
2. batch sidecar JSON 会记录 provider metadata；
3. 显式 `--llm-provider` 会记录为 explicit source；
4. 默认 / config-driven 路径也会记录 provider source；
5. provider metadata 只存在于 sidecar，不进入主 review output。

### 8.2 docs/LLM_PROVIDER_USAGE.md

补充说明：

1. sidecar output 中的 provider metadata 字段；
2. `llm_provider` 的含义；
3. `llm_provider_source` 的含义；
4. `mock` 与 `pydantic-ai-testmodel` 的当前语义；
5. 真实 provider 仍未接入；
6. metadata 只是追踪信息，不代表主结果合并。

### 8.3 docs/DATA_MODELS.md

补充说明：

1. sidecar envelope 增加 provider metadata；
2. `LLMReviewResult` schema 不变；
3. `ReviewResult` schema 不变；
4. `BatchReviewResult` schema 不变；
5. 如果 sidecar schema version 有变化，记录新旧版本差异。

### 8.4 docs/ARCHITECTURE.md

补充当前 sidecar metadata 流程：

```text
CLI provider selection
        ↓
create_llm_reviewer()
        ↓
LLMReviewResult
        ↓
sidecar serializer
        ↓
sidecar envelope with provider metadata
```

并明确：

1. provider metadata 属于 sidecar envelope；
2. provider metadata 不进入主审计结果；
3. 真实 provider 仍未接入；
4. API / MCP / GUI 仍未接入。

### 8.5 PROJECT_STATE.md

更新当前状态：

```text
TASK-0059 completed:
Added provider metadata to single and batch LLM sidecar outputs.
```

同时明确尚未完成：

```text
No real LLM API provider.
No API key loading.
No LLM result merge into main ReviewResult or BatchReviewResult.
No Markdown report integration.
No API / MCP / GUI integration.
```

### 8.6 CHANGELOG.md

新增 TASK-0059 变更记录。

---

## 9. 验收标准

本任务完成后必须满足：

1. single LLM sidecar output 包含 provider metadata；
2. batch LLM sidecar output 包含 provider metadata；
3. 显式 `--llm-provider mock` 记录 `mock`；
4. 显式 `--llm-provider pydantic-ai-testmodel` 记录 `pydantic-ai-testmodel`；
5. 显式 provider source 记录为 `explicit`；
6. 默认 / config-driven provider path 也有 provider metadata；
7. provider metadata 不进入主 `ReviewResult`；
8. provider metadata 不进入主 `BatchReviewResult`；
9. LLM findings 不进入主结果；
10. `LLMReviewResult` schema 不被无关修改；
11. JSON / Markdown report 不被修改；
12. Quality Gate 不被修改；
13. review 默认行为不变；
14. batch 默认行为不变；
15. llm-check 用户可见行为不变；
16. 不接入真实 LLM API；
17. 不读取 `.env`；
18. 不需要真实 API key；
19. 不访问外部网络；
20. 文档同步更新；
21. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

本任务最容易出现的风险是 Agent 把 provider metadata 写入主审计结果，或者顺手修改 sidecar schema 太多。

必须避免以下问题：

1. 不要修改主 `ReviewResult` schema；
2. 不要修改主 `BatchReviewResult` schema；
3. 不要修改 `LLMReviewResult` finding 结构；
4. 不要把 provider metadata 写进 Markdown Report；
5. 不要把 provider metadata 写进 quality gate；
6. 不要接真实 provider；
7. 不要读取 API key；
8. 不要读取 `.env`；
9. 不要新增 provider config 系统；
10. 不要修改 provider factory 支持项；
11. 不要改变 review / batch / llm-check 默认行为；
12. 不要让测试访问外部网络。

本任务的本质是：

```text
让 sidecar output 自带 provider provenance / metadata。
```

而不是：

```text
让正式审计结果合并 LLM 语义审计。
```

---

## 11. 完成后需要运行的命令

请至少运行：

```bash
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_sidecar.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest tests/test_llm_smoke_check.py
uv run pytest
```

如果存在 batch sidecar 专用测试文件，也请运行，例如：

```bash
uv run pytest tests/test_batch_llm_sidecar.py
```

如果项目中存在 lint / format 命令，也可以运行，但不得因此引入大范围无关格式化改动。

---

