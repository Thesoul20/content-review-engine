# TASK-0049: Add PydanticAI Provider Usage Guide and Manual Verification Fixtures

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计相关的 provider interface、mock reviewer、runner、sidecar JSON、sidecar Markdown report、provider configuration boundary、PydanticAI secret resolution、PydanticAI request / response mapping、PydanticAI runtime call、timeout 配置和 runtime error classification。

已完成任务包括：

```text id="l92yqf"
TASK-0040: Add Batch LLM Sidecar Output
TASK-0041: Add LLM Sidecar Summary and Error Handling
TASK-0042: Add LLM Sidecar Markdown Report
TASK-0043: Add Real LLM Provider Configuration Boundary
TASK-0044: Normalize PydanticAI Provider Adapter Boundary
TASK-0045: Add PydanticAI Provider Dependency and Secret Resolution
TASK-0046: Add PydanticAI Provider Request and Response Mapping
TASK-0047: Add PydanticAI Provider Runtime Call
TASK-0048: Add PydanticAI Runtime Timeout and Error Classification
```

当前 provider 状态是：

```text id="y1gklk"
provider="mock"
  -> 可运行，生成 mock LLMReviewResult。

provider="pydanticai"
  -> 可运行；
  -> 支持 secret resolution；
  -> 支持真实 runtime call；
  -> 支持 OpenAI-compatible base_url；
  -> 支持 timeout_seconds；
  -> 支持 runtime error classification；
  -> 输出仍走 LLM sidecar JSON / LLM sidecar Markdown report；
  -> 不影响 deterministic ReviewResult / Quality Gate。
```

现在已经具备真实 provider 能力，但还缺少面向开发者和使用者的安全使用指南：

1. 如何配置 `--llm-provider pydanticai`；
2. 如何设置 `--llm-api-key-env`；
3. 如何使用 `--llm-model`；
4. 如何使用 `--llm-base-url`；
5. 如何使用 `--llm-timeout-seconds`；
6. 如何进行单文件真实 provider 手动验证；
7. 如何进行 batch 真实 provider 手动验证；
8. 如何检查 sidecar JSON / Markdown 输出；
9. 如何确认 Quality Gate 不受 LLM 影响；
10. 如何排查 timeout、auth、network、rate limit、model、validation 等错误；
11. 如何避免 API key 泄露；
12. 如何避免真实 API 调用进入自动化测试和 CI。

因此，本任务不新增 provider 功能，而是补齐真实 PydanticAI provider 的使用文档、手动验证夹具和安全验证流程。

本任务是生产化前的文档与手动验证任务，不做 retry、rate limit、batch concurrency、streaming、Quality Gate 集成或主报告合并。

---

## 2. 任务目标

新增真实 PydanticAI provider 的使用指南和手动验证夹具。

完成后应满足：

1. 有独立文档说明如何使用 PydanticAI provider；
2. 有明确的单文件 review 手动验证命令；
3. 有明确的 batch review 手动验证命令；
4. 有明确的 OpenAI-compatible `base_url` 配置说明；
5. 有明确的 `--llm-timeout-seconds` 使用说明；
6. 有明确的 secret 配置方式；
7. 有明确的安全注意事项，避免 API key 泄露；
8. 有明确的 sidecar JSON / Markdown 输出检查方法；
9. 有明确的 Quality Gate 边界说明；
10. 有明确的 runtime error troubleshooting guide；
11. 有可复用的手动验证 fixture；
12. 自动化测试不得依赖真实 API key 或真实网络；
13. 不改变 runtime 行为；
14. 不改变 sidecar schema；
15. 不改变 report 结构；
16. 不改变 Quality Gate 语义。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 新增 PydanticAI provider 使用文档；
2. 新增手动验证用 Markdown fixture；
3. 新增手动验证用 profile fixture，或复用现有 profile fixture；
4. 新增 `.env.example` 或等价示例文件，但只允许包含占位符；
5. 新增手动验证 checklist；
6. 新增 single-file provider 验证命令示例；
7. 新增 batch provider 验证命令示例；
8. 新增 sidecar JSON 检查说明；
9. 新增 LLM Markdown report 检查说明；
10. 新增 Quality Gate 边界说明；
11. 新增 runtime error troubleshooting guide；
12. 新增安全注意事项；
13. 新增不访问真实网络的 fixture / docs 测试；
14. 更新 `docs/CLI.md`；
15. 更新 `docs/CI.md`；
16. 更新 `docs/ARCHITECTURE.md`；
17. 更新 `PROJECT_STATE.md` 和 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不新增 retry；
2. 不新增 rate limit queue；
3. 不新增 batch 并发；
4. 不新增 streaming；
5. 不新增多模型 fallback；
6. 不新增 provider fallback；
7. 不新增 `--fail-on-llm`；
8. 不让 Quality Gate 根据 LLM 结果失败；
9. 不把 LLM findings 合并进主 ReviewResult；
10. 不改变 LLMSidecarResult JSON schema；
11. 不改变 LLM sidecar Markdown report 结构；
12. 不改变 deterministic ReviewResult schema；
13. 不改变 deterministic JSON 输出结构；
14. 不改变 deterministic Markdown report 默认结构；
15. 不改变 batch manifest schema；
16. 不实现 API / MCP / GUI；
17. 不引入 Supabase、用户系统、SaaS、多租户、支付等能力；
18. 不直接新增 OpenAI / Anthropic 官方 SDK provider；
19. 不绕过 `LLMReviewer` provider interface；
20. 不让 tests 依赖真实 API key 或真实网络；
21. 不把 API key 写入 repo、fixture、docs、sidecar、report、日志或错误信息；
22. 不在 CI 中运行真实 provider 调用；
23. 不新增真实 API smoke test 到默认 pytest；
24. 不重构 CLI；
25. 不重构 LLM runner；
26. 不重构 provider runtime。

---

## 5. 需要修改的文件

预计新增：

```text id="l6k411"
docs/LLM_PROVIDER_USAGE.md
examples/llm/pydanticai/manual-review.md
examples/llm/pydanticai/batch/article-a.md
examples/llm/pydanticai/batch/article-b.md
examples/llm/pydanticai/.env.example
```

如果当前仓库已有 examples 目录结构，请遵循现有结构。
如果仓库没有 examples 目录，也可以使用：

```text id="qq7sg5"
docs/examples/llm/pydanticai/
```

预计修改：

```text id="hp93bp"
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

可选新增测试：

```text id="m6uqae"
tests/test_llm_provider_usage_docs.py
```

或如果项目已有 docs/fixture 测试模式，复用现有测试文件。

---

## 6. 实现要求

### 6.1 新增 PydanticAI provider 使用文档

新增文档：

```text id="qtw65c"
docs/LLM_PROVIDER_USAGE.md
```

文档应包含以下章节：

```text id="ve5wj1"
# LLM Provider Usage

## Overview
## Supported Providers
## PydanticAI Provider
## Required Environment Variables
## Single-file Manual Verification
## Batch Manual Verification
## Sidecar JSON Output
## Sidecar Markdown Output
## Quality Gate Boundary
## Timeout Configuration
## OpenAI-compatible Base URL
## Troubleshooting
## Security Notes
## CI Notes
```

文档必须明确：

```text id="ua5xov"
mock provider:
  - safe for tests and CI
  - no network
  - no API key

pydanticai provider:
  - real runtime provider
  - requires API key through env var
  - can call external model endpoint
  - should not run in default tests or CI
  - outputs through sidecar JSON / Markdown
  - does not affect deterministic Quality Gate
```

---

### 6.2 单文件手动验证命令

文档中必须提供单文件验证命令。

示例：

```bash id="ukvo88"
export OPENAI_API_KEY="replace-with-your-real-key"

uv run content-review review \
  examples/llm/pydanticai/manual-review.md \
  --profile examples/llm/pydanticai/manual-profile.yml \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-timeout-seconds 30 \
  --llm-output /tmp/content-review-llm.json \
  --llm-markdown-output /tmp/content-review-llm.md
```

如果项目没有 `examples/llm/pydanticai/manual-profile.yml`，可以改为复用现有测试 profile fixture，并在文档中使用实际存在的 profile 路径。

要求：

1. 示例中不能包含真实 API key；
2. 示例必须使用 env var；
3. 示例必须展示 JSON sidecar output；
4. 示例必须展示 Markdown sidecar output；
5. 示例必须说明 deterministic review 和 LLM sidecar 是分离的；
6. 示例必须说明 Quality Gate 不读取 LLM findings。

---

### 6.3 batch 手动验证命令

文档中必须提供 batch 验证命令。

示例：

```bash id="45z44y"
export OPENAI_API_KEY="replace-with-your-real-key"

uv run content-review batch \
  examples/llm/pydanticai/batch \
  --profile examples/llm/pydanticai/manual-profile.yml \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-timeout-seconds 30 \
  --llm-output-dir /tmp/content-review-llm-sidecars \
  --llm-markdown-output /tmp/content-review-llm-batch.md
```

要求：

1. 示例必须说明会生成 per-file `.llm-review.json`；
2. 示例必须说明会生成 `llm-review-manifest.json`；
3. 示例必须说明 batch LLM Markdown report 的位置；
4. 示例必须说明 batch 中单个 LLM failure 不应改变 deterministic batch review 结果；
5. 示例必须说明 Quality Gate 仍只由 deterministic findings 决定。

---

### 6.4 手动验证 fixture

新增手动验证 Markdown fixture。

建议文件：

```text id="s5q0rg"
examples/llm/pydanticai/manual-review.md
```

内容应包含一些适合 LLM 语义审计的文本，例如：

```text id="bs6r11"
- 夸大表达
- 不确定事实
- 可能误导的营销说法
- 需要建议改写的句子
```

但不要包含：

```text id="cl28ep"
- 真实个人隐私
- 真实 API key
- 真实医疗诊断建议
- 真实金融投资建议
- 真实法律建议
- 违法或高风险内容
```

新增 batch fixture：

```text id="85zij7"
examples/llm/pydanticai/batch/article-a.md
examples/llm/pydanticai/batch/article-b.md
```

要求：

1. 文件内容短小；
2. 适合真实 provider 快速验证；
3. 不需要大量 token；
4. 不包含敏感信息；
5. 不包含真实 secret；
6. 不用于默认真实 API 测试。

---

### 6.5 profile fixture

如果当前仓库已有可复用 profile fixture，应优先复用。
如果没有适合手动验证的 profile，可以新增：

```text id="qryxc8"
examples/llm/pydanticai/manual-profile.yml
```

要求：

1. 必须符合当前 ReviewProfile schema；
2. 应包含少量 deterministic rules；
3. 应适合配合 LLM sidecar 观察 hybrid review；
4. 不应引入复杂规则；
5. 不应改变测试 profile；
6. 不应影响现有测试。

如果新增该 profile，应添加测试确保它能被 profile loader 正常加载。

---

### 6.6 `.env.example`

新增：

```text id="udfc90"
examples/llm/pydanticai/.env.example
```

内容只能包含占位符：

```bash id="ra572k"
# Copy this file to a local .env file if you want to run manual provider checks.
# Never commit real API keys.

OPENAI_API_KEY=replace-with-your-real-key
```

要求：

1. 不包含真实 key；
2. 不包含看起来像真实 key 的值；
3. 明确提醒不要提交真实 `.env`；
4. 如果仓库没有 `.gitignore` 覆盖 `.env`，不要在本任务中大改 `.gitignore`，只在文档中提醒用户避免提交 secret；
5. 如果已有 `.gitignore` 结构适合补充 examples `.env`，可以小范围补充，但不是必需。

---

### 6.7 sidecar JSON 检查说明

文档中必须说明如何检查 sidecar JSON。

至少包括：

```text id="c27m1g"
schema_version
status
summary
review.provider
review.model
review.findings
error.error_type
error.message
```

示例说明：

```bash id="ou3n8w"
cat /tmp/content-review-llm.json
```

如果项目允许使用 `jq`，可以给出可选命令：

```bash id="rdph5h"
jq '.status, .summary, .review.findings' /tmp/content-review-llm.json
```

但不要把 `jq` 作为项目依赖。

---

### 6.8 sidecar Markdown 检查说明

文档中必须说明如何检查 LLM Markdown report。

示例：

```bash id="o2j77v"
cat /tmp/content-review-llm.md
```

说明应包括：

1. summary；
2. provider；
3. status；
4. findings；
5. failed entry；
6. timeout / runtime error 展示；
7. 该 report 不是 deterministic report；
8. 该 report 不影响 Quality Gate。

---

### 6.9 Quality Gate 边界说明

必须明确写出：

```text id="3l3qh6"
LLM findings do not affect the deterministic Quality Gate.
LLM provider failures do not become deterministic findings.
LLM timeout / runtime errors are reported through LLM sidecar outputs or command errors, depending on where the failure occurs.
```

中文可以写：

```text id="g9ki7v"
LLM 结果不会影响当前 deterministic Quality Gate。
LLM provider 失败不会变成 deterministic finding。
LLM timeout / runtime error 只属于 LLM sidecar/provider 维度。
```

---

### 6.10 Troubleshooting guide

文档中必须说明常见错误类型和处理方式。

至少包括：

```text id="azovzo"
LLMProviderSecretError
LLMProviderConfigError
LLMProviderTimeoutError
LLMProviderAuthError
LLMProviderNetworkError
LLMProviderRateLimitError
LLMProviderModelError
LLMProviderRuntimeError
LLMResponseValidationError
```

每个错误类型建议包含：

```text id="44ibl3"
含义
常见原因
如何排查
是否影响 deterministic Quality Gate
```

示例：

```text id="nqz9jf"
LLMProviderTimeoutError:
  Meaning: The provider request exceeded the configured timeout.
  Check:
    - Increase --llm-timeout-seconds
    - Try a smaller input
    - Check provider availability
  Quality Gate:
    - Does not affect deterministic Quality Gate.
```

---

### 6.11 CI notes

文档和 `docs/CI.md` 必须说明：

1. 默认 CI 不应运行真实 provider；
2. 默认 pytest 不应依赖真实 API key；
3. mock provider 应继续作为 CI provider；
4. 真实 provider 验证是手动流程；
5. 如果未来要加入可选真实 provider smoke test，必须单独开任务；
6. 不要把真实 key 存入 repo；
7. 不要把真实 key 输出到日志。

---

### 6.12 自动化测试要求

本任务可以新增 docs/fixture 测试，但不能使用真实 provider。

测试建议覆盖：

1. 新增 manual fixture 文件存在；
2. `.env.example` 不包含真实 API key；
3. docs 不包含明显真实 API key 模式；
4. manual profile 可以被当前 profile loader 加载；
5. manual markdown fixture 可以被当前 markdown reader 读取；
6. CLI docs 中包含 `--llm-provider pydanticai`；
7. CLI docs 中包含 `--llm-timeout-seconds`；
8. LLM provider usage docs 中包含 Quality Gate 边界说明；
9. LLM provider usage docs 中包含 troubleshooting error types。

不要新增需要真实 API key 的测试。

---

## 7. 测试要求

### 7.1 Fixture 测试

如果新增 examples fixture，需要测试：

```text id="719wpo"
manual-review.md 存在且非空
batch/article-a.md 存在且非空
batch/article-b.md 存在且非空
.env.example 存在且不包含真实 key
manual-profile.yml 符合 ReviewProfile schema
```

如果复用现有 profile fixture，则不需要新增 manual-profile 测试，但文档路径必须真实存在。

---

### 7.2 Documentation safety 测试

新增或更新测试，确保：

1. 文档中没有真实 API key；
2. `.env.example` 只有 placeholder；
3. 文档中使用 `OPENAI_API_KEY` 作为 env var name；
4. 文档中没有 `sk-` 开头的真实 key 示例；
5. 文档明确真实 provider 不应进入默认 CI；
6. 文档明确 LLM 不影响 deterministic Quality Gate。

---

### 7.3 CLI docs coverage 测试

可选测试：

1. `docs/CLI.md` 包含 `--llm-provider pydanticai`；
2. `docs/CLI.md` 包含 `--llm-api-key-env`；
3. `docs/CLI.md` 包含 `--llm-timeout-seconds`；
4. `docs/CLI.md` 包含 single-file 示例；
5. `docs/CLI.md` 包含 batch 示例。

如果项目中没有 docs coverage 测试习惯，可以不强制新增该类测试，但至少应有 fixture/safety 测试。

---

### 7.4 回归测试

必须确保已有测试全部通过：

```bash id="pzjhrz"
uv run pytest
```

如果新增 docs/fixture 测试，也请额外运行：

```bash id="y9k7ei"
uv run pytest tests/test_llm_provider_usage_docs.py
```

具体测试文件名以实际仓库为准。

---

## 8. 文档更新要求

需要新增：

```text id="1xrnjv"
docs/LLM_PROVIDER_USAGE.md
```

需要更新：

```text id="j5u94j"
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果 `docs/DATA_MODELS.md` 当前已经完整记录 0048 的 provider config / timeout / error 类型，本任务不强制修改。
如果新增 usage docs 中引入新的 fixture 或 manual verification terms，也可以同步补充 `docs/DATA_MODELS.md`，但不要重复大段内容。

更新重点：

1. `docs/CLI.md` 链接到 `docs/LLM_PROVIDER_USAGE.md`；
2. `docs/CI.md` 说明真实 provider 只做手动验证，不进入默认 CI；
3. `docs/ARCHITECTURE.md` 说明真实 provider 的使用边界和 sidecar-first 输出方式；
4. `PROJECT_STATE.md` 记录 TASK-0049 完成后项目状态；
5. `CHANGELOG.md` 记录新增 usage guide 和 manual fixtures。

---

## 9. 验收标准

本任务完成后应满足：

1. 存在 PydanticAI provider usage guide；
2. usage guide 包含 single-file 手动验证流程；
3. usage guide 包含 batch 手动验证流程；
4. usage guide 说明 `--llm-provider pydanticai`；
5. usage guide 说明 `--llm-model`；
6. usage guide 说明 `--llm-api-key-env`；
7. usage guide 说明 `--llm-base-url`；
8. usage guide 说明 `--llm-timeout-seconds`；
9. usage guide 说明 sidecar JSON 检查方法；
10. usage guide 说明 sidecar Markdown 检查方法；
11. usage guide 说明 Quality Gate 边界；
12. usage guide 说明 troubleshooting error types；
13. usage guide 说明 secret safety；
14. usage guide 说明 CI 不运行真实 provider；
15. 存在手动验证 Markdown fixture；
16. 存在 batch 手动验证 fixture；
17. `.env.example` 不包含真实 key；
18. 自动化测试不依赖真实 API key；
19. 自动化测试不访问真实网络；
20. 不改变 provider runtime 行为；
21. 不改变 sidecar schema；
22. 不改变 report 结构；
23. 不改变 Quality Gate；
24. 文档、PROJECT_STATE.md、CHANGELOG.md 已同步更新；
25. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 本任务是文档与手动验证任务，不是 runtime feature task；
2. 不要实现 retry；
3. 不要实现 rate limit；
4. 不要实现 batch concurrency；
5. 不要实现 streaming；
6. 不要改变 sidecar schema；
7. 不要改变 report 结构；
8. 不要改变 Quality Gate；
9. 不要把真实 API key 写进 repo；
10. 不要把真实 API key 写进 docs；
11. 不要把真实 provider 测试放进默认 pytest；
12. 不要让 CI 依赖真实 API key；
13. 不要新增真实网络测试；
14. fixture 内容应短小，避免真实 provider 手动验证成本过高；
15. troubleshooting guide 应和 TASK-0048 的错误类型保持一致；
16. 后续 retry / rate limit / concurrency 应单独放到 TASK-0050 或之后。

---

## 11. 完成后需要运行的命令

```bash id="lr752p"
uv run pytest
```

如果新增 docs / fixture 测试，请额外运行：

```bash id="zfqt98"
uv run pytest tests/test_llm_provider_usage_docs.py
```

具体测试文件名以实际仓库为准。

---

