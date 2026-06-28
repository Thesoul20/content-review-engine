# TASK-0043: Add Real LLM Provider Configuration Boundary

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计相关的 provider interface、mock reviewer、runner、sidecar JSON 输出、sidecar summary/error handling 和 sidecar Markdown report。

已完成任务包括：

```text
TASK-0040: Add Batch LLM Sidecar Output
TASK-0041: Add LLM Sidecar Summary and Error Handling
TASK-0042: Add LLM Sidecar Markdown Report
```

目前 LLM 语义审计链路已经具备：

```text
LLMReviewRequest
  -> LLMReviewer provider interface
  -> MockLLMReviewer
  -> LLMReviewResult
  -> LLMSidecarResult
  -> JSON sidecar
  -> Markdown sidecar report
```

下一阶段需要逐步接入真实 LLM provider，例如 PydanticAI / OpenAI / Anthropic / 本地模型等。

但是在真正接入真实 LLM SDK 和真实 API 调用之前，需要先建立稳定的 provider configuration boundary，避免后续把 API key、模型名、provider 选择、CLI 参数解析、provider 构造逻辑直接散落在 CLI 或 runner 中。

因此，本任务只增加真实 provider 接入前的配置边界和 provider factory / registry，不实现真实 LLM API 调用。

本任务是后续 TASK-0044 接入 PydanticAI provider 的前置任务。

---

## 2. 任务目标

实现 LLM provider 配置边界。

完成后，项目应具备：

1. 结构化的 LLM provider configuration 数据模型；
2. provider name / provider type 的稳定表达；
3. CLI 层可以解析 LLM provider 相关配置；
4. provider factory / registry 可以根据配置创建 reviewer；
5. 当前可运行 provider 仍然只有 mock provider；
6. 未实现的真实 provider 应给出清晰、结构化、可测试的错误；
7. 不泄露 API key、环境变量值或敏感配置；
8. 不接入真实 LLM SDK；
9. 不发起真实网络请求；
10. 不改变 deterministic review、sidecar JSON、sidecar Markdown report 和 Quality Gate 的行为。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 新增 LLM provider config 数据模型；
2. 新增 provider name / provider type 表达；
3. 新增 provider config loading / validation 逻辑；
4. 新增 provider factory / registry；
5. 支持 mock provider 通过 factory 创建；
6. 为未来真实 provider 预留明确 provider name，例如 `pydanticai`；
7. 对未实现 provider 返回清晰错误；
8. 为 CLI 增加或整理 LLM provider 配置参数；
9. 更新 LLM 相关错误类型；
10. 增加或更新 provider config / factory / CLI 测试；
11. 更新相关文档；
12. 更新 PROJECT_STATE.md 和 CHANGELOG.md。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不接入真实 OpenAI / Anthropic / PydanticAI SDK；
2. 不新增真实网络请求；
3. 不调用真实 LLM API；
4. 不在测试中依赖真实 API key；
5. 不读取或输出真实 API key 值；
6. 不新增外部 LLM SDK 依赖；
7. 不实现 PydanticAI provider 的真实 review 逻辑；
8. 不把 LLM findings 合并进主 ReviewResult；
9. 不改变 LLMSidecarResult JSON schema；
10. 不改变 LLM sidecar Markdown report 结构；
11. 不让 Quality Gate 根据 LLM 结果失败；
12. 不改变 deterministic review JSON schema；
13. 不改变 deterministic Markdown report 结构；
14. 不实现 API / MCP / GUI；
15. 不引入 Supabase、用户系统、SaaS、多租户、支付等能力；
16. 不重构整个 CLI；
17. 不新增 retry、timeout、rate limit 等真实 provider 运行机制。

---

## 5. 需要修改的文件

预计包括但不限于：

```text
src/content_review_engine/llm/config.py
src/content_review_engine/llm/factory.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/mock.py
src/content_review_engine/llm/provider.py
src/content_review_engine/llm/__init__.py
src/content_review_engine/cli.py
tests/test_llm_config.py
tests/test_llm_provider_factory.py
tests/test_cli.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
PROJECT_STATE.md
CHANGELOG.md
```

如果当前仓库已经有等价文件或命名风格，请优先复用已有结构，避免重复创建功能相近的模块。

如果项目中已有 `src/content_review_engine/llm/serialization.py`、`sidecar.py` 等文件，本任务不应无必要修改它们，除非 provider configuration 需要导出或文档示例需要同步。

---

## 6. 实现要求

### 6.1 Provider config 数据模型

新增结构化 LLM provider configuration。

建议新增类似模型：

```text
LLMProviderConfig
```

建议字段包括：

```text
provider
model
api_key_env
base_url
temperature
timeout_seconds
extra
```

字段设计要求：

1. `provider` 必须有明确默认值；
2. 当前默认 provider 应为 `mock`；
3. `model` 可选；
4. `api_key_env` 表示环境变量名称，不保存环境变量值；
5. `base_url` 可选，暂不用于真实请求；
6. `temperature` 可选，暂不用于 mock provider；
7. `timeout_seconds` 可选，暂不实现真实 timeout；
8. `extra` 可选，用于未来扩展，但不应滥用；
9. 配置对象不能在 `repr` / 序列化中暴露真实 secret；
10. 不要把真实 API key 作为字段值保存。

如果当前项目更偏向 dataclass，则使用 dataclass；如果当前数据模型统一使用 Pydantic 或普通 dataclass，请遵循现有项目风格。

---

### 6.2 Provider name / provider type

建议支持以下 provider name：

```text
mock
pydanticai
```

当前只有 `mock` 可以创建可运行 reviewer。

`pydanticai` 只是预留 provider name，用于后续 TASK-0044 实现真实 provider。

如果用户选择 `pydanticai`，本任务应返回明确错误，例如：

```text
LLMProviderNotImplementedError
```

或复用当前错误层级中的合适错误类型。

错误信息应说明：

```text
Provider 'pydanticai' is recognized but not implemented yet.
```

不要出现误导性行为，例如悄悄 fallback 到 mock provider。

---

### 6.3 Provider factory / registry

新增 provider factory / registry，用于根据 config 创建 `LLMReviewer`。

建议新增函数：

```text
create_llm_reviewer(config: LLMProviderConfig) -> LLMReviewer
```

行为要求：

1. `provider=mock` 返回 `MockLLMReviewer`；
2. `provider=pydanticai` 返回明确的 not implemented error；
3. 未知 provider 返回明确的 provider config error；
4. 不在 CLI 中直接实例化真实 provider；
5. 不在 runner 中读取环境变量；
6. 不在 factory 中发起网络请求；
7. factory 层不应依赖 CLI；
8. factory 应容易测试。

---

### 6.4 环境变量处理

本任务可以支持读取环境变量名称，但不要读取或输出真实 secret 值。

推荐边界：

1. CLI 可以接收 `--llm-api-key-env OPENAI_API_KEY`；
2. config 中保存的是 `api_key_env="OPENAI_API_KEY"`；
3. 本任务不需要从 `os.environ` 读取具体 key 值；
4. 如果确实需要验证环境变量是否存在，也只返回存在 / 不存在，不输出值；
5. 错误信息不能包含真实 key 值。

更推荐本任务先只保存 env var name，不做真实 secret resolution。

真实 secret resolution 留到后续真实 provider 任务中完成。

---

### 6.5 CLI 参数设计

为 CLI 增加或整理 LLM provider 配置参数。

建议参数包括：

```text
--llm-provider <provider>
--llm-model <model>
--llm-api-key-env <env-var-name>
--llm-base-url <url>
```

具体是否全部实现，以当前 CLI 结构和测试复杂度为准。

最低要求：

1. 支持 `--llm-provider mock`；
2. 默认 provider 为 `mock`；
3. `--enable-llm` 未开启时，LLM provider 配置不应影响 deterministic review；
4. `--enable-llm --llm-provider mock` 行为与当前 mock LLM sidecar 行为兼容；
5. `--enable-llm --llm-provider pydanticai` 应返回清晰错误，说明 provider 已识别但尚未实现；
6. 未知 provider 应返回清晰 CLI 错误；
7. CLI help / docs 应说明当前只有 mock provider 可运行。

不要让 `--llm-provider pydanticai` 悄悄走 mock。

---

### 6.6 错误类型

如当前错误层级已有：

```text
LLMReviewError
LLMProviderError
LLMResponseValidationError
```

可以新增或复用：

```text
LLMProviderConfigError
LLMProviderNotImplementedError
```

错误设计要求：

1. 错误类型稳定，便于测试断言；
2. 错误信息清晰；
3. 不输出 secret；
4. 不输出 traceback 到用户可见 sidecar；
5. 不改变已有 error_type / message 结构；
6. CLI 对 provider config error 应有合理退出行为。

---

### 6.7 Sidecar 行为

本任务不应改变 TASK-0041 / TASK-0042 的 sidecar 结构。

要求：

1. `mock` provider 下，现有 sidecar JSON 行为保持兼容；
2. `mock` provider 下，现有 sidecar Markdown report 行为保持兼容；
3. provider config error 可以通过现有 failed sidecar 结构表达，或按 CLI 当前错误策略处理；
4. 不修改 LLMSidecarSummary 字段；
5. 不修改 LLMSidecarFile 字段；
6. 不修改 LLM sidecar Markdown report 主结构。

如果因为 provider config error 导致 LLM review 无法开始，应保持错误路径清晰、可测试。

---

### 6.8 Quality Gate 行为

LLM provider config 不应影响 Quality Gate。

要求：

1. deterministic findings 仍然决定 Quality Gate；
2. `--enable-llm` 下 mock provider 的 sidecar 行为不影响 Quality Gate；
3. provider not implemented / config error 不应被误算为 deterministic finding；
4. 不新增 `--fail-on-llm`；
5. 不新增 LLM-based Quality Gate。

如果 CLI 当前对参数错误或 provider 创建失败会直接退出，可以保持 CLI 参数错误语义；但不要把它混同于 deterministic Quality Gate failure。

---

## 7. 测试要求

必须新增或更新测试，覆盖以下情况。

### 7.1 Provider config 测试

新增或更新测试，覆盖：

1. 默认 config 使用 `mock` provider；
2. config 可以保存 model；
3. config 可以保存 api_key_env 名称；
4. config 不保存真实 API key 值；
5. config repr / serialization 不泄露 secret；
6. unknown provider 触发 config error；
7. recognized but unimplemented provider 触发 not implemented error。

---

### 7.2 Provider factory 测试

新增或更新测试，覆盖：

1. `create_llm_reviewer(provider=mock)` 返回 `MockLLMReviewer`；
2. `create_llm_reviewer(provider=pydanticai)` 返回 not implemented error；
3. unknown provider 返回 config error；
4. factory 不读取 CLI；
5. factory 不发起网络请求；
6. factory 错误类型稳定。

---

### 7.3 CLI 测试

更新 CLI 测试，覆盖：

1. `--enable-llm --llm-provider mock` 保持现有 sidecar 输出行为；
2. 未指定 `--llm-provider` 时默认使用 mock；
3. `--llm-provider` 在未启用 `--enable-llm` 时不影响 deterministic review；
4. `--enable-llm --llm-provider pydanticai` 返回清晰 not implemented 错误；
5. unknown provider 返回清晰错误；
6. `--llm-model` 可以被解析；
7. `--llm-api-key-env` 可以被解析，但不泄露 env value；
8. deterministic output 不受 provider config 参数影响；
9. Quality Gate 不受 provider config 参数影响。

如果现有 CLI 框架不容易断言 stderr 文案，可以至少断言退出码和关键错误类型 / 关键短语。

---

### 7.4 回归测试

必须确保已有测试全部通过：

```bash
uv run pytest
```

如果新增专门测试文件，也请额外运行：

```bash
uv run pytest tests/test_llm_config.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_cli.py
```

具体测试文件名以实际仓库为准。

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

1. 在 `docs/ARCHITECTURE.md` 中说明 provider configuration boundary；
2. 在 `docs/ARCHITECTURE.md` 中说明 CLI 不直接构造真实 provider；
3. 在 `docs/DATA_MODELS.md` 中说明 LLMProviderConfig、provider name、provider factory；
4. 在 `docs/CLI.md` 中说明 `--llm-provider`、`--llm-model`、`--llm-api-key-env` 等参数；
5. 在 `docs/CLI.md` 中说明当前只有 mock provider 可运行；
6. 在 `docs/CLI.md` 中说明 `pydanticai` 是已识别但尚未实现的 provider；
7. 在 `PROJECT_STATE.md` 中记录 TASK-0043 已完成后项目状态；
8. 在 `CHANGELOG.md` 中记录本次变更。

如果 `docs/CI.md` 当前提到 LLM sidecar 与 Quality Gate 的关系，也可以补充 provider config 不影响 Quality Gate；否则本任务不强制修改 `docs/CI.md`。

---

## 9. 验收标准

本任务完成后应满足：

1. 存在结构化 LLMProviderConfig；
2. 存在 provider factory / registry；
3. mock provider 可以通过 factory 创建；
4. pydanticai provider name 被识别，但返回 not implemented error；
5. unknown provider 返回清晰 config error；
6. CLI 支持 provider 配置参数；
7. CLI 默认 provider 为 mock；
8. mock provider 下现有 LLM sidecar JSON 行为保持兼容；
9. mock provider 下现有 LLM sidecar Markdown report 行为保持兼容；
10. provider config 不影响 deterministic review；
11. provider config 不影响 Quality Gate；
12. 不接入真实 LLM SDK；
13. 不发起真实网络请求；
14. 不读取或输出真实 API key 值；
15. 不改变 ReviewResult、LLMSidecarResult、sidecar Markdown report 的主结构；
16. 新增或更新的测试通过；
17. 文档、PROJECT_STATE.md、CHANGELOG.md 已同步更新；
18. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 不要把 provider config 逻辑写死在 CLI 中；
2. 不要让 runner 直接读取环境变量；
3. 不要悄悄 fallback 到 mock provider；
4. 不要输出真实 API key；
5. 不要把 `pydanticai` 做成半成品真实调用；
6. 不要新增外部依赖；
7. 不要改变 sidecar JSON schema；
8. 不要改变 sidecar Markdown report 结构；
9. 不要让 provider config error 变成 deterministic finding；
10. 不要新增 `--fail-on-llm`；
11. 不要实现 retry / timeout / rate limit；
12. 不要把后续 TASK-0044 的真实 provider 实现提前做掉。

---

## 11. 完成后需要运行的命令

```bash
uv run pytest
```

如果新增或修改了专门测试文件，也请额外运行：

```bash
uv run pytest tests/test_llm_config.py
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_cli.py
```

具体测试文件名以实际仓库为准。

---
