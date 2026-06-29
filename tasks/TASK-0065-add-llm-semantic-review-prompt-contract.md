# TASK-0065: Add LLM Semantic Review Prompt Contract

## 1. 背景

当前项目已经完成：

```text
TASK-0061: Add LLM Provider Secret Resolver
TASK-0062: Wire LLM Secret Resolver into LLM Check
TASK-0063: Enable Real PydanticAI Provider Construction
TASK-0064: Add Optional Live PydanticAI Runtime Smoke Check
```

目前 LLM provider 基础设施已经具备：

1. `LLMProviderConfig.api_key_env` 作为 secret reference；
2. `resolve_llm_provider_secret(config, env=None)`；
3. `redact_secret_value()`；
4. `content-review llm-check` 的 secret preflight；
5. `provider="pydanticai"` 可以通过 factory 构造；
6. `PydanticAIReviewer.run_construction_check()`；
7. `PydanticAIReviewer.run_live_check()`；
8. `content-review llm-check --live` 可以显式执行 live runtime smoke check；
9. 默认 `llm-check` 仍不执行 live call；
10. 普通测试不依赖真实 API key；
11. 普通测试不访问外部网络；
12. 主 `review` / `batch` 流程仍未接入 LLM；
13. `ReviewResult`、`BatchReviewResult`、`LLMReviewResult` schema 均未改变。

上一阶段完成的是 LLM provider 是否可用的基础设施检查。

接下来需要进入真正的 LLM 语义审计能力设计。但在接入主 `review` 命令之前，必须先定义清楚：

1. LLM 语义审计到底审什么；
2. 输入给 LLM 的内容结构是什么；
3. 期望 LLM 返回什么 JSON；
4. severity、rule_id、line、suggestion 等字段如何约束；
5. 模型输出不合规时后续如何校验。

因此，本任务只定义 **LLM Semantic Review Prompt Contract**，不执行真实审计、不调用真实 provider、不接入 CLI 主流程、不修改主报告 schema。

---

## 2. 任务目标

本任务需要完成：

1. 新增 LLM 语义审计 prompt contract；
2. 定义稳定的 system prompt / user prompt 构建逻辑；
3. 明确 LLM 语义审计的输入字段；
4. 明确 LLM 语义审计的输出 JSON contract；
5. 明确 LLM finding 的字段要求；
6. 明确 severity 枚举约束；
7. 明确 rule_id 命名规则；
8. 明确 line / column / evidence / suggestion 的返回要求；
9. 明确模型不得返回非 JSON 自由文本；
10. 增加 prompt contract 的单元测试；
11. 增加文档说明；
12. 更新项目状态和 changelog。

完成后，项目应该具备一套可测试、可复用、可文档化的 LLM 语义审计 prompt contract，为后续 `TASK-0066: Add LLM Output Validation and Recovery` 打基础。

---

## 3. 本任务允许做什么

本任务允许：

1. 新增 LLM prompt contract 模块；
2. 新增 prompt builder helper；
3. 新增 LLM semantic review prompt 文本；
4. 新增 prompt contract 数据结构；
5. 新增输出 JSON schema 描述；
6. 新增 prompt contract 测试；
7. 更新 LLM 数据模型文档；
8. 更新 LLM provider usage 文档；
9. 更新架构文档；
10. 更新项目状态；
11. 更新 changelog。

---

## 4. 本任务不允许做什么

本任务不允许：

1. 不允许调用真实 LLM API；
2. 不允许访问外部网络；
3. 不允许修改 `content-review review` 主流程；
4. 不允许修改 `content-review batch` 主流程；
5. 不允许新增 `review` 或 `batch` 的 LLM CLI 开关；
6. 不允许生成真实 `LLMReviewResult`；
7. 不允许把 LLM finding 合并进 `ReviewResult`；
8. 不允许修改 `ReviewResult` schema；
9. 不允许修改 `BatchReviewResult` schema；
10. 不允许修改 `LLMReviewResult` schema，除非当前已有模型无法表达 contract 且必须小范围补充；
11. 不允许修改 sidecar metadata；
12. 不允许修改 deterministic review engine 行为；
13. 不允许修改 `llm-check` 的 live / construction 行为；
14. 不允许新增 plaintext API key 参数；
15. 不允许读取 `.env`；
16. 不允许让 provider factory 读取环境变量；
17. 不允许让 reserved providers 变成可创建；
18. 不允许新增 API、MCP、Skill、GUI、Supabase、用户系统或商业化能力；
19. 不允许引入 LangChain、CrewAI 或其他大型框架。

---

## 5. 需要修改的文件

预计会新增或修改以下文件：

```text
src/content_review_engine/llm/prompt_contract.py
src/content_review_engine/llm/models.py
src/content_review_engine/llm/__init__.py

tests/test_llm_prompt_contract.py
tests/test_llm_provider_usage_docs.py

docs/LLM_PROVIDER_USAGE.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前仓库已有更合适的 prompt / contract 模块命名，应优先遵守现有结构。

如果 `src/content_review_engine/llm/models.py` 中已有足够的数据结构，本任务应尽量不修改模型，只新增 prompt contract helper。

---

## 6. 实现要求

### 6.1 prompt contract 模块要求

新增模块建议命名为：

```text
src/content_review_engine/llm/prompt_contract.py
```

该模块应提供稳定的 prompt contract 构建能力。

建议包含：

```python
build_llm_semantic_review_system_prompt()
build_llm_semantic_review_user_prompt(request)
build_llm_semantic_review_prompt_contract(request)
```

或当前项目风格下的等价命名。

其中：

1. system prompt 负责定义模型角色、审计目标、输出格式、禁止事项；
2. user prompt 负责注入待审计内容、文件名、profile 信息、deterministic findings 摘要等；
3. contract builder 负责返回结构化 prompt parts，便于后续 provider 使用。

本任务不要求 provider 真正调用这些 prompt。

---

### 6.2 输入 contract 要求

prompt contract 应基于现有 `LLMReviewRequest` 或等价结构构建。

输入信息应至少包括：

1. 待审计文本内容；
2. 文件路径或文件名；
3. profile name 或 profile metadata；
4. 目标审计语言，默认为中文；
5. deterministic findings 摘要，如果已有；
6. 需要 LLM 关注的语义风险类型；
7. 输出格式要求。

如果当前 `LLMReviewRequest` 中暂时没有全部字段，可以：

1. 使用已有字段；
2. 在 prompt builder 中对缺失字段给出稳定 fallback；
3. 不要为了本任务大规模扩展数据模型。

---

### 6.3 审计范围要求

LLM semantic review prompt 应明确要求模型重点审计：

1. 夸大或绝对化表达；
2. 可能误导读者的表达；
3. 不当营销承诺；
4. 医学、法律、金融等高风险建议；
5. 逻辑跳跃或证据不足；
6. 表达歧义；
7. 平台发布前可能需要人工确认的内容；
8. 与 deterministic findings 相关的上下文风险。

同时应明确模型不负责：

1. 重新写整篇文章；
2. 直接删除用户内容；
3. 生成营销文案；
4. 判断法律合规最终结论；
5. 替代专业人士意见；
6. 输出非结构化长篇解释。

---

### 6.4 输出 JSON contract 要求

prompt 中必须要求模型只返回 JSON。

推荐输出结构：

```json
{
  "schema_version": "llm-semantic-review-output.v1",
  "summary": "string",
  "findings": [
    {
      "rule_id": "llm.semantic.overclaim",
      "severity": "warning",
      "line": 12,
      "column": 1,
      "message": "string",
      "evidence": "string",
      "suggestion": "string",
      "confidence": 0.82
    }
  ]
}
```

字段要求：

1. `schema_version` 必须固定；
2. `summary` 是简短总结；
3. `findings` 必须是数组；
4. `rule_id` 必须以 `llm.` 开头；
5. `severity` 只能是 `info`、`warning`、`error`、`critical`；
6. `line` 可以为整数或 null；
7. `column` 可以为整数或 null；
8. `message` 必须说明问题；
9. `evidence` 必须引用原文中的短片段；
10. `suggestion` 必须给出可执行修改建议；
11. `confidence` 必须在 0 到 1 之间；
12. 没有问题时必须返回空 findings。

注意：本任务只定义 prompt 输出 contract，不实现模型输出 parser / validator。parser / validator 应留到后续任务。

---

### 6.5 rule_id 要求

prompt 中应约束 LLM 使用稳定 rule_id。

建议初始 rule_id 包括：

```text
llm.semantic.overclaim
llm.semantic.misleading
llm.semantic.unsupported_claim
llm.semantic.risky_advice
llm.semantic.ambiguous_expression
llm.semantic.inappropriate_tone
llm.semantic.needs_human_review
```

本任务不需要实现所有规则的复杂逻辑，只需要在 prompt contract 中定义这些类型。

---

### 6.6 severity 要求

prompt 中应定义 severity 使用规则：

```text
info
  轻微表达建议，不影响发布

warning
  可能需要修改或人工确认

error
  明显不适合直接发布，建议发布前修改

critical
  高风险内容，强烈建议阻止发布或人工审核
```

LLM 不应自由创造其他 severity。

---

### 6.7 prompt 稳定性要求

prompt builder 输出应稳定、可测试。

测试中应断言：

1. system prompt 包含 JSON-only 要求；
2. system prompt 包含 schema version；
3. system prompt 包含 severity 枚举；
4. system prompt 包含 rule_id 前缀要求；
5. user prompt 包含待审计文本；
6. user prompt 包含文件名；
7. user prompt 包含 profile 信息；
8. user prompt 不包含 secret；
9. prompt builder 不访问网络；
10. prompt builder 不读取环境变量。

---

### 6.8 安全与隐私要求

prompt contract 不应包含：

1. API key；
2. secret value；
3. 环境变量值；
4. provider runtime diagnostic；
5. 用户系统信息；
6. 本机路径中的敏感信息，除非 request 本身明确包含相对文件路径。

prompt builder 不允许：

1. 读取 `.env`；
2. 读取 `os.environ`；
3. 访问外部网络；
4. 调用 provider；
5. 修改全局状态。

---

## 7. 测试要求

### 7.1 新增 prompt contract 测试

新增：

```text
tests/test_llm_prompt_contract.py
```

覆盖：

1. 可以从 `LLMReviewRequest` 构建 prompt contract；
2. system prompt 包含 JSON-only 要求；
3. system prompt 包含 `llm-semantic-review-output.v1`；
4. system prompt 包含 severity 枚举；
5. system prompt 包含 `llm.` rule_id 前缀约束；
6. system prompt 包含 no free-form prose 要求；
7. user prompt 包含待审计文本；
8. user prompt 包含 file / profile 信息；
9. prompt 包含 semantic risk categories；
10. prompt 不包含 secret；
11. prompt builder 不读取环境变量；
12. prompt builder 不访问网络；
13. prompt output 稳定，可重复构建；
14. 空 deterministic findings 时仍可构建；
15. 有 deterministic findings 摘要时可注入上下文。

---

### 7.2 模型兼容性测试

如果当前 `LLMReviewRequest` 已有测试，应补充：

```text
tests/test_llm_provider_config.py
tests/test_llm_pydanticai_provider.py
```

或当前对应测试文件，确保新增 prompt contract 不破坏已有 LLM 模型和 provider 测试。

但本任务不要求 provider 调用 prompt。

---

### 7.3 文档测试

更新：

```text
tests/test_llm_provider_usage_docs.py
```

确保文档中包含：

1. LLM semantic review prompt contract；
2. JSON-only 输出要求；
3. schema version；
4. severity 枚举；
5. `llm.` rule_id 前缀；
6. 本任务不接入主 `review`；
7. 本任务不执行真实 LLM 调用。

---

## 8. 文档更新要求

### 8.1 `docs/LLM_PROVIDER_USAGE.md`

补充：

1. LLM provider 基础设施已经可以 smoke check；
2. LLM semantic review prompt contract 的目的；
3. prompt contract 的输入；
4. prompt contract 的输出 JSON 示例；
5. JSON-only 要求；
6. severity 枚举；
7. rule_id 约束；
8. 本任务不执行真实审计；
9. 本任务不接入 `review` / `batch`。

---

### 8.2 `docs/DATA_MODELS.md`

补充：

1. LLM semantic review prompt contract；
2. `llm-semantic-review-output.v1`；
3. expected output fields；
4. `rule_id` 命名规范；
5. severity 枚举；
6. confidence 范围；
7. 说明这是 prompt output contract，不等于已验证的内部模型；
8. parser / validator 是后续任务。

---

### 8.3 `docs/ARCHITECTURE.md`

补充：

1. LLM prompt contract 在架构中的位置；
2. provider 层与 prompt contract 的关系；
3. prompt contract 不调用 provider；
4. prompt contract 不访问网络；
5. prompt contract 与后续 output validation 的关系；
6. 说明当前仍未接入主 review / batch 流程。

---

### 8.4 `PROJECT_STATE.md`

更新：

1. 标记 `TASK-0065` 完成后新增 LLM semantic review prompt contract；
2. 说明当前具备 provider smoke check + prompt contract；
3. 说明 output validation、provider execution、review integration、report integration 仍是后续任务。

---

### 8.5 `CHANGELOG.md`

新增 `TASK-0065` 记录。

---

## 9. 验收标准

本任务完成后应满足：

1. 新增稳定的 LLM semantic review prompt contract；
2. 可以基于 `LLMReviewRequest` 构建 system / user prompt；
3. prompt 明确要求 JSON-only 输出；
4. prompt 明确 schema version；
5. prompt 明确 severity 枚举；
6. prompt 明确 `llm.` rule_id 前缀；
7. prompt 明确 findings 字段要求；
8. prompt 明确无 findings 时返回空数组；
9. prompt builder 不读取环境变量；
10. prompt builder 不访问网络；
11. prompt builder 不调用 provider；
12. prompt 不泄露 secret；
13. 不修改主 `review` / `batch` 流程；
14. 不修改公开 review result schema；
15. 不修改 sidecar metadata；
16. 不执行真实 LLM API 调用；
17. 文档已同步；
18. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 不要在本任务中实现 parser / validator，那是后续任务。
2. 不要在本任务中调用 PydanticAI provider。
3. 不要把 prompt contract 接进 `review` CLI。
4. 不要修改主审计结果 schema。
5. 不要让 prompt 输出 contract 和内部数据模型混淆。
6. 不要让 prompt builder 读取环境变量或 secret。
7. 不要过度设计复杂规则系统，先定义稳定 contract。
8. 不要让 LLM 返回 Markdown 或自然语言解释，必须要求 JSON-only。
9. prompt 中不要承诺法律、医学、金融等高风险判断的最终准确性。
10. prompt 的目标是“发布前语义风险提示”，不是“自动合规裁决”。

---

## 11. 完成后需要运行的命令

可以先运行局部测试：

```bash
uv run pytest tests/test_llm_prompt_contract.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest tests/test_llm_pydanticai_provider.py
```

最后必须运行全量测试：

```bash
uv run pytest
```

---
