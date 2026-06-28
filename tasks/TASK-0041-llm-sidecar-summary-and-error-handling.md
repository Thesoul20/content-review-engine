# TASK-0041: Add LLM Sidecar Summary and Error Handling

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计相关的 provider interface、mock reviewer、runner、CLI sidecar 基础能力和 batch LLM sidecar output。

TASK-0040 已经让批量审计场景可以输出 LLM sidecar 结果。

但是当前 LLM sidecar 仍然缺少更稳定的运行摘要和失败记录能力。后续一旦接入真实 LLM provider，可能会出现：

1. 单个文件 LLM 审计失败；
2. provider 返回异常；
3. provider 输出无法解析；
4. 部分文件成功、部分文件失败；
5. 用户需要从 sidecar 中快速判断本次 LLM 审计整体状态；
6. 后续 CLI / report / CI / MCP 需要依赖更稳定的 sidecar 结构。

因此，本任务的目标是在不接入真实 LLM provider、不改变主 ReviewResult、不影响 Quality Gate 的前提下，为 LLM sidecar 增加结构化 summary 和 error handling。

本任务是 TASK-0040 之后的稳定化任务，为后续真实 LLM provider 接入做准备。

---

## 2. 任务目标

实现 LLM sidecar 的结构化运行摘要和错误记录能力。

完成后，LLM sidecar 输出应能够表达：

1. 本次 LLM sidecar 审计总共处理了多少文件；
2. 有多少文件成功生成 LLMReviewResult；
3. 有多少文件被跳过；
4. 有多少文件发生 LLM 审计错误；
5. 每个文件的 LLM 审计状态；
6. 每个失败文件的错误类型和错误信息；
7. LLM sidecar 的失败不应影响确定性审计主结果；
8. LLM sidecar 的失败不应影响 Quality Gate；
9. 原有 deterministic review JSON / Markdown report 行为保持不变。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 为 LLM sidecar 增加 summary 数据结构；
2. 为 LLM sidecar 增加 per-file status 数据结构；
3. 为 LLM sidecar 增加 per-file error 数据结构；
4. 支持 batch LLM sidecar 中记录部分成功、部分失败；
5. 支持单文件 LLM sidecar 中记录成功或失败状态；
6. 更新 LLM sidecar 序列化逻辑；
7. 更新 CLI 中生成 LLM sidecar 的错误捕获逻辑；
8. 增加或更新对应测试；
9. 更新相关文档；
10. 更新 PROJECT_STATE.md 和 CHANGELOG.md。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不接入真实 OpenAI / Anthropic / PydanticAI provider；
2. 不新增真实 LLM API key 配置；
3. 不引入新的外部 LLM SDK 依赖；
4. 不把 LLM findings 合并进主 ReviewResult；
5. 不让 Quality Gate 根据 LLM sidecar 结果失败；
6. 不改变现有 deterministic review 的 JSON schema；
7. 不改变现有 Markdown report 主结构；
8. 不实现 LLM Markdown report；
9. 不实现 API / MCP / GUI；
10. 不引入 Supabase、用户系统、SaaS、多租户、支付等能力；
11. 不重构整个 CLI；
12. 不改变已有 batch deterministic review 的行为。

---

## 5. 需要修改的文件

预计包括但不限于：

```text
src/content_review_engine/llm/models.py
src/content_review_engine/llm/serializers.py
src/content_review_engine/llm/runner.py
src/content_review_engine/cli.py
tests/test_llm_sidecar.py
tests/test_cli.py
docs/CLI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前仓库中已有更精确的 LLM sidecar 测试文件，请优先复用已有测试文件，避免无意义新增重复测试文件。

---

## 6. 实现要求

### 6.1 Sidecar summary

LLM sidecar 输出中应包含 summary 信息。

建议字段包括：

```text
file_count
succeeded_count
failed_count
skipped_count
finding_count
```

如果当前已有类似字段，应复用现有命名风格。

如果当前已有 sidecar schema version，应按项目现有 schema version 规则处理：

1. 如果只是增加兼容性字段，可以保持当前 schema version；
2. 如果项目约定新增字段必须 bump schema version，则新增对应版本；
3. 不要随意破坏已有测试期望。

---

### 6.2 Per-file status

每个文件的 LLM sidecar entry 应包含状态字段。

建议状态包括：

```text
success
failed
skipped
```

其中：

```text
success:
  LLM reviewer 正常返回 LLMReviewResult。

failed:
  LLM reviewer 抛出异常，或者 runner / serializer 捕获到 LLM 审计失败。

skipped:
  当前文件未执行 LLM 审计，例如未来可能用于空文件、非目标文件、配置跳过等情况。
```

本任务可以只实现当前实际会用到的 success / failed，但数据结构应允许 skipped 状态存在。

---

### 6.3 Error 结构

失败文件应记录结构化错误信息。

建议字段包括：

```text
error_type
message
```

可以根据当前错误层级扩展：

```text
LLMReviewError
LLMProviderError
LLMResponseValidationError
```

注意：

1. 不要输出 Python traceback 到 sidecar；
2. 不要输出敏感环境变量；
3. 不要输出 API key；
4. 错误信息应适合 CLI / JSON / 后续 report 展示；
5. error_type 应稳定，方便测试断言。

---

### 6.4 Batch partial success

batch LLM sidecar 应支持部分成功。

例如：

```text
file_a.md -> success
file_b.md -> failed
file_c.md -> success
```

sidecar summary 应能表达：

```text
file_count: 3
succeeded_count: 2
failed_count: 1
skipped_count: 0
```

即使其中一个文件 LLM 审计失败，也不应中断整个 batch deterministic review。

---

### 6.5 Single-file sidecar behavior

如果单文件 LLM sidecar 当前已经存在，本任务也应使其具备一致的 status / error 表达。

单文件场景下也应能表达：

```text
status: success
```

或：

```text
status: failed
error:
  error_type: ...
  message: ...
```

但不应改变主审计结果和主输出。

---

### 6.6 Quality Gate 行为

LLM sidecar 的错误不应影响 Quality Gate。

也就是说：

1. deterministic review 的 findings 仍然决定 Quality Gate；
2. LLM sidecar failed 不应导致 CLI 以失败码退出，除非当前 CLI 已有明确的 sidecar 写入失败行为；
3. 如果 sidecar 文件本身无法写入，可以保留当前 CLI 文件输出错误行为；
4. 不要新增 `--fail-on-llm` 或类似参数。

---

### 6.7 CLI 输出行为

如果当前 CLI 在生成 LLM sidecar 时有提示信息，可以适度更新提示。

但本任务不要求新增复杂日志系统。

CLI 行为应保持简洁：

1. 原有 deterministic 输出不变；
2. sidecar 路径行为不变；
3. sidecar 内容更完整；
4. LLM 单文件失败不应导致 batch 直接中止。

---

## 7. 测试要求

必须新增或更新测试，覆盖以下情况。

### 7.1 序列化测试

测试 LLM sidecar summary 能正确序列化。

至少覆盖：

1. 全部成功；
2. 部分失败；
3. finding_count 统计；
4. error 字段序列化；
5. schema version 或现有 schema 字段保持稳定。

---

### 7.2 Runner / sidecar 构建测试

测试构建 LLM sidecar 时：

1. 成功文件标记为 success；
2. 失败文件标记为 failed；
3. 失败文件包含 error_type 和 message；
4. batch 中某个文件失败不会阻断其他文件；
5. summary 统计正确。

可以通过 mock reviewer 抛出 LLMReviewError / LLMProviderError 来测试失败路径。

---

### 7.3 CLI 测试

更新 CLI 测试，覆盖：

1. batch LLM sidecar 输出包含 summary；
2. batch LLM sidecar 输出包含 per-file status；
3. batch LLM sidecar 在 mock failure 情况下仍能写出结构化错误；
4. deterministic review 输出保持不变；
5. Quality Gate 行为不受 LLM sidecar failed 影响。

如果当前 CLI 不方便直接注入失败 mock，可以优先在 runner / serializer 层覆盖失败路径，并在 CLI 层覆盖成功路径。

---

### 7.4 回归测试

必须确保已有测试全部通过：

```bash
uv run pytest
```

---

## 8. 文档更新要求

需要更新以下文档：

```text
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
PROJECT_STATE.md
CHANGELOG.md
```

更新重点：

1. 在 `docs/ARCHITECTURE.md` 中说明 LLM sidecar 是旁路输出，不影响 deterministic review / Quality Gate；
2. 在 `docs/DATA_MODELS.md` 中说明 LLM sidecar summary、status、error 字段；
3. 在 `docs/CLI.md` 中说明 batch / single LLM sidecar 输出中的 summary 和失败记录；
4. 在 `PROJECT_STATE.md` 中记录 TASK-0041 已完成后项目状态；
5. 在 `CHANGELOG.md` 中记录本次变更。

如果 `docs/CI.md` 当前已经提到 LLM sidecar 与 Quality Gate 的关系，也需要同步更新；否则本任务不强制修改 `docs/CI.md`。

---

## 9. 验收标准

本任务完成后应满足：

1. LLM sidecar 输出包含结构化 summary；
2. batch sidecar 能表达每个文件的 success / failed 状态；
3. failed 文件包含结构化 error 信息；
4. 部分文件 LLM 审计失败不会中断 batch deterministic review；
5. LLM sidecar 失败不影响 Quality Gate；
6. 主 ReviewResult schema 不被修改；
7. 原有 deterministic JSON / Markdown report 行为不变；
8. 不引入真实 LLM provider；
9. 不新增外部 LLM SDK 依赖；
10. 新增或更新的测试通过；
11. 文档、PROJECT_STATE.md、CHANGELOG.md 已同步更新；
12. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 不要把 LLM error 直接塞进 deterministic ReviewResult；
2. 不要让 LLM failed 影响 deterministic quality gate；
3. 不要因为一个文件 LLM failed 就让整个 batch sidecar 失败；
4. 不要输出 traceback、API key、环境变量等敏感信息；
5. 不要提前设计复杂 retry / timeout / rate limit 机制；
6. 不要引入真实 provider；
7. 不要把 sidecar summary 和 batch deterministic summary 混为一谈；
8. 不要重构 CLI 主流程，只在 sidecar 生成路径上做最小必要修改。

---

## 11. 完成后需要运行的命令

```bash
uv run pytest
```

如果新增或修改了专门测试文件，也请额外运行：

```bash
uv run pytest tests/test_llm_sidecar.py
uv run pytest tests/test_cli.py
```

具体测试文件名以实际仓库为准。

---

