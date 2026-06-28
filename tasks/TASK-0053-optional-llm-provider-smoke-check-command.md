# TASK-0053: Add Optional LLM Provider Smoke Check Command

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计相关的 provider interface、mock reviewer、runner、sidecar JSON、sidecar Markdown report、provider configuration boundary、PydanticAI secret resolution、PydanticAI request / response mapping、PydanticAI runtime call、timeout、runtime error classification、真实 provider 使用文档、retry configuration、request pacing guardrails，以及 LLM provider config file。

已完成任务包括：

```text id="t2g5g4"
TASK-0040: Add Batch LLM Sidecar Output
TASK-0041: Add LLM Sidecar Summary and Error Handling
TASK-0042: Add LLM Sidecar Markdown Report
TASK-0043: Add Real LLM Provider Configuration Boundary
TASK-0044: Normalize PydanticAI Provider Adapter Boundary
TASK-0045: Add PydanticAI Provider Dependency and Secret Resolution
TASK-0046: Add PydanticAI Provider Request and Response Mapping
TASK-0047: Add PydanticAI Provider Runtime Call
TASK-0048: Add PydanticAI Runtime Timeout and Error Classification
TASK-0049: Add PydanticAI Provider Usage Guide and Manual Verification Fixtures
TASK-0050: Add PydanticAI Provider Retry Configuration
TASK-0051: Add PydanticAI Provider Rate Limit Guardrails
TASK-0052: Add LLM Provider Config File and CLI Overrides
```

当前真实 provider 已经具备较完整的工程化能力：

```text id="e92jzv"
provider config file
secret resolution
runtime call
timeout
error classification
retry
request pacing
sidecar JSON
sidecar Markdown report
manual verification docs
```

但是，用户如果想验证一个真实 LLM provider 是否配置正确，目前仍然需要通过正式的 `review` 或 `batch` 命令间接试跑。这样有几个问题：

1. 容易把 provider 配置验证和内容审计混在一起；
2. 不方便快速判断是 config 错误、secret 错误、runtime 错误还是 response validation 错误；
3. 不方便在文档中给出一个清晰的“手动 smoke check”流程；
4. 不适合放入默认 CI；
5. 容易误解为 LLM provider 失败会影响 deterministic Quality Gate。

因此，本任务新增一个**显式、可选、手动运行**的 LLM provider smoke check 命令，用来验证 LLM provider 配置、secret resolution 和可选 runtime 调用。

本任务不改变 `review` / `batch` 的审计行为，不改变 sidecar schema，不改变 Quality Gate，不新增真实 provider CI 测试。

---

## 2. 任务目标

新增可选 LLM provider smoke check 命令。

完成后应满足：

1. CLI 提供一个独立的 LLM provider check 命令；
2. 可以验证 LLM config file 是否可加载；
3. 可以验证 CLI override 是否能合并到最终 LLMProviderConfig；
4. 可以验证 secret resolution 是否成功；
5. 可以选择执行真实 provider runtime smoke call；
6. smoke check 不读取用户正式文章；
7. smoke check 不生成 deterministic ReviewResult；
8. smoke check 不生成正式 sidecar；
9. smoke check 不影响 Quality Gate；
10. smoke check 默认不进入 CI；
11. 自动化测试不依赖真实 API key；
12. 自动化测试不访问真实网络；
13. 文档说明该命令是手动验证工具，不是审计命令。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 新增 CLI 命令，例如 `content-review llm-check`；
2. 复用现有 `LLMProviderConfig`；
3. 复用现有 `--llm-config` 加载逻辑；
4. 复用现有 CLI override 逻辑；
5. 复用现有 secret resolver；
6. 复用现有 provider factory；
7. 支持 config-only check；
8. 支持 secret check；
9. 支持可选 runtime smoke check；
10. 支持 text / json 输出格式，或先只支持稳定 text 输出；
11. 使用 synthetic minimal request 做 runtime smoke check；
12. 更新 CLI 测试；
13. 更新 provider config loader 测试或 smoke check 测试；
14. 更新文档；
15. 更新 PROJECT_STATE.md 和 CHANGELOG.md。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不改变 `review` 命令行为；
2. 不改变 `batch` 命令行为；
3. 不改变 PydanticAI provider runtime 行为；
4. 不改变 retry 行为；
5. 不改变 timeout 行为；
6. 不改变 request pacing 行为；
7. 不新增新的 provider；
8. 不新增 provider fallback；
9. 不新增 multi-model fallback；
10. 不新增 streaming；
11. 不新增 batch concurrency；
12. 不新增 rate limit queue；
13. 不新增 `--fail-on-llm`；
14. 不让 Quality Gate 根据 LLM 结果失败；
15. 不把 LLM findings 合并进主 ReviewResult；
16. 不改变 LLMSidecarResult JSON schema；
17. 不改变 LLM sidecar Markdown report 结构；
18. 不改变 deterministic ReviewResult schema；
19. 不改变 deterministic JSON 输出结构；
20. 不改变 deterministic Markdown report 默认结构；
21. 不改变 batch manifest schema；
22. 不实现 API / MCP / GUI；
23. 不引入 Supabase、用户系统、SaaS、多租户、支付等能力；
24. 不让默认 pytest 依赖真实 API key；
25. 不让默认 pytest 访问真实网络；
26. 不把真实 API key 写入 repo、fixture、docs、sidecar、report、日志或错误信息；
27. 不在 CI 中运行真实 provider runtime smoke check；
28. 不重构整个 CLI；
29. 不重构整个 LLM runner；
30. 不重构 provider runtime。

---

## 5. 需要修改的文件

预计包括但不限于：

```text id="rlxsv5"
src/content_review_engine/cli.py
src/content_review_engine/llm/config.py
src/content_review_engine/llm/config_loader.py
src/content_review_engine/llm/factory.py
tests/test_cli.py
tests/test_llm_config_loader.py
tests/test_llm_provider_usage_docs.py
docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果 smoke check 逻辑较多，建议新增：

```text id="kiir6l"
src/content_review_engine/llm/smoke_check.py
tests/test_llm_smoke_check.py
```

是否新增独立模块由实际复杂度决定。
如果 CLI 中逻辑会超过少量 glue code，优先新增 `llm/smoke_check.py`，避免 CLI 变得臃肿。

---

## 6. 实现要求

### 6.1 新增 CLI 命令

建议新增命令：

```bash id="xbun6b"
content-review llm-check
```

命令用途：

```text id="dxzivx"
验证 LLM provider 配置、secret resolution，以及可选 provider runtime smoke call。
```

建议示例：

```bash id="nwjuo6"
uv run content-review llm-check \
  --llm-config examples/llm/pydanticai/llm-provider.yml
```

也应支持不使用 config file、直接传 CLI 参数：

```bash id="44rl33"
uv run content-review llm-check \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-timeout-seconds 30 \
  --llm-retry-attempts 1 \
  --llm-retry-backoff-seconds 1.0 \
  --llm-min-request-interval-seconds 0.5
```

要求：

1. `llm-check` 不需要 `--enable-llm`；
2. `llm-check` 本身就是 LLM 相关命令；
3. `llm-check` 不需要 `--profile`；
4. `llm-check` 不读取 Markdown 输入文件；
5. `llm-check` 不生成 deterministic review；
6. `llm-check` 不生成 Quality Gate 结果；
7. `llm-check` 不写正式 sidecar；
8. `llm-check` 不改变 review / batch 行为。

---

### 6.2 Smoke check 模式

建议支持三个阶段：

```text id="0jx7z2"
config check
secret check
runtime check
```

可以通过参数控制是否执行 runtime。

推荐参数：

```text id="35gg5p"
--runtime
```

默认行为建议：

```text id="uk7veb"
默认只做 config + secret check，不发起真实 provider runtime call。
只有显式传入 --runtime 时才执行真实 provider smoke call。
```

这样更安全，避免用户误以为 `llm-check` 默认不访问网络，实际却发起模型调用。

示例：

```bash id="p2w9q0"
uv run content-review llm-check \
  --llm-config examples/llm/pydanticai/llm-provider.yml
```

执行：

```text id="0h9sxk"
config check
secret check
no runtime call
```

示例：

```bash id="47b7qd"
uv run content-review llm-check \
  --llm-config examples/llm/pydanticai/llm-provider.yml \
  --runtime
```

执行：

```text id="swatvz"
config check
secret check
runtime smoke call
```

要求：

1. 默认不做真实 runtime call；
2. `--runtime` 才允许真实 provider call；
3. mock provider 的 runtime check 可以运行，但不访问网络；
4. pydanticai provider 的 runtime check 可能访问真实 provider；
5. 文档必须明确 `--runtime` 可能产生费用；
6. 文档必须明确默认 CI 不应运行 `--runtime`。

---

### 6.3 Config loading 与 CLI override

`llm-check` 必须复用 TASK-0052 的配置合并规则：

```text id="8k1hn8"
explicit CLI args > --llm-config file > LLMProviderConfig defaults
```

支持字段：

```text id="h5t30g"
provider
model
api_key_env
base_url
timeout_seconds
retry_attempts
retry_backoff_seconds
min_request_interval_seconds
```

要求：

1. `--llm-config` 可选；
2. 单独 CLI 参数也可用；
3. config file + CLI override 可同时使用；
4. parser 默认值不得覆盖 config file；
5. invalid config file 返回清晰错误；
6. secret-like field 仍拒绝；
7. 不读取 ReviewProfile；
8. 不修改 ReviewProfile schema。

---

### 6.4 Secret check

secret check 行为：

```text id="0afkbm"
mock provider:
  -> 不需要 secret
  -> secret check 通过

pydanticai provider:
  -> 使用 api_key_env 解析 secret
  -> 缺失时报 LLMProviderSecretError
  -> env var 不存在时报 LLMProviderSecretError
  -> env var 为空时报 LLMProviderSecretError
```

要求：

1. secret value 不输出；
2. secret value 不写日志；
3. secret value 不写 JSON；
4. secret value 不写 Markdown；
5. secret value 不写 error message；
6. 成功时只显示 env var name；
7. 失败时只显示 env var name 和错误类型；
8. 不发起 runtime call，除非显式 `--runtime`。

---

### 6.5 Runtime smoke check

如果传入 `--runtime`，则执行一个最小 runtime smoke call。

建议构造 synthetic `LLMReviewRequest`：

```text id="6wx7ul"
content_path: "__llm_smoke_check__.md"
content: "This is a short LLM provider smoke check. Return no findings unless the configured policy requires otherwise."
profile_name: "llm-smoke-check"
metadata:
  smoke_check: true
```

要求：

1. 不读取用户文章；
2. 不读取 profile；
3. 不生成 deterministic review；
4. 不生成 sidecar；
5. 直接通过 provider interface 调用 reviewer；
6. mock provider 应返回稳定 mock result；
7. pydanticai provider 应执行真实 runtime call；
8. runtime 成功时返回 check passed；
9. runtime 失败时返回稳定错误；
10. 不把完整 prompt 或 synthetic content 写入错误信息；
11. 不把 secret 写入错误信息；
12. 不改变 provider runtime 行为。

---

### 6.6 输出格式

本任务可以先实现 text 输出，或同时支持 JSON 输出。

推荐先支持 text 输出，保持简单。

建议成功输出包含：

```text id="72jowo"
LLM provider check passed.
Provider: pydanticai
Model: openai:gpt-4o-mini
Config: loaded from examples/llm/pydanticai/llm-provider.yml
Secret: resolved from OPENAI_API_KEY
Runtime: skipped
```

如果带 `--runtime`：

```text id="vm0wv4"
Runtime: passed
Findings: 0
```

失败输出应包含：

```text id="9iqu90"
LLM provider check failed.
Stage: secret
Error type: LLMProviderSecretError
Message: LLM API key environment variable 'OPENAI_API_KEY' is not set.
```

要求：

1. 输出不包含 secret value；
2. 输出不包含完整 prompt；
3. 输出不包含完整 synthetic request；
4. 输出不包含 traceback；
5. 错误信息稳定，适合测试；
6. 退出码清晰。

---

### 6.7 退出码

建议退出码：

```text id="clvzsh"
0 -> check passed
2 -> config / CLI / secret / provider check failed
```

要求：

1. config invalid -> 2；
2. secret invalid -> 2；
3. runtime failed -> 2；
4. mock success -> 0；
5. pydanticai config + secret success without --runtime -> 0；
6. pydanticai runtime success with --runtime -> 0；
7. 不使用 Quality Gate exit code 语义；
8. 文档说明 `llm-check` 不是 Quality Gate。

---

### 6.8 与 review / batch 的边界

`llm-check` 不应改变：

```text id="0qogpg"
content-review review
content-review batch
```

要求：

1. 不改变 review 参数语义；
2. 不改变 batch 参数语义；
3. 不改变 sidecar 输出；
4. 不改变 Markdown report；
5. 不改变 deterministic findings；
6. 不改变 Quality Gate；
7. 不改变 batch manifest；
8. 不改变 existing tests 的预期行为，除非只是 CLI help 输出增加新命令。

---

### 6.9 CI 边界

默认 CI 不应运行真实 provider runtime。

要求：

1. 默认 pytest 不依赖真实 API key；
2. 默认 pytest 不访问真实网络；
3. `llm-check --runtime` 的测试必须使用 fake / mock provider；
4. 文档明确真实 `--runtime` 是手动验证流程；
5. 不新增真实 API smoke test 到默认 CI；
6. 如果未来要做可选 smoke CI，需要单独任务。

---

## 7. 测试要求

所有测试必须避免真实 API key 和真实网络。

### 7.1 Smoke check unit tests

如果新增 `llm/smoke_check.py`，新增：

```text id="o0bytt"
tests/test_llm_smoke_check.py
```

覆盖：

1. mock provider config check 通过；
2. mock provider runtime check 通过；
3. pydanticai secret missing 返回 secret error；
4. pydanticai secret present without runtime 不访问 provider runtime；
5. pydanticai runtime success with fake runtime；
6. pydanticai runtime failure with fake runtime；
7. output 不包含 secret；
8. output 不包含完整 prompt；
9. output 不包含 traceback；
10. exit status / result status 稳定。

---

### 7.2 CLI tests

更新 `tests/test_cli.py`，覆盖：

1. `content-review llm-check --llm-config examples/llm/mock/llm-provider.yml` 成功；
2. `content-review llm-check --llm-config examples/llm/mock/llm-provider.yml --runtime` 成功；
3. `content-review llm-check --llm-config examples/llm/pydanticai/llm-provider.yml` 在 fake env 下 config + secret check 成功，不执行 runtime；
4. `content-review llm-check --llm-config examples/llm/pydanticai/llm-provider.yml --runtime` 使用 fake runtime 成功；
5. missing config file 返回 2；
6. invalid config file 返回 2；
7. missing secret 返回 2；
8. runtime failure 返回 2；
9. CLI override 生效；
10. parser 默认值不覆盖 config file；
11. stderr / stdout 不包含 secret value；
12. 不访问真实网络。

---

### 7.3 Docs tests

更新 `tests/test_llm_provider_usage_docs.py`，覆盖：

1. usage docs 包含 `llm-check`；
2. usage docs 包含 `--runtime`；
3. usage docs 说明默认不执行 runtime；
4. usage docs 说明 `--runtime` 可能访问真实 provider；
5. usage docs 说明 `llm-check` 不影响 Quality Gate；
6. usage docs 说明默认 CI 不运行真实 `--runtime`；
7. docs 不包含真实 API key。

---

### 7.4 Regression tests

必须确保已有测试全部通过：

```bash id="fp5422"
uv run pytest
```

如果新增专门测试文件，请额外运行：

```bash id="zh8bfu"
uv run pytest tests/test_llm_smoke_check.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_provider_usage_docs.py
```

具体测试文件名以实际仓库为准。

---

## 8. 文档更新要求

需要更新：

```text id="hbo5dp"
docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

如果新增 `llm/smoke_check.py` 相关数据结构或 result model，也可以更新：

```text id="r77guz"
docs/DATA_MODELS.md
```

更新重点：

1. `docs/LLM_PROVIDER_USAGE.md` 增加 `llm-check` 使用说明；
2. 说明默认只做 config + secret check；
3. 说明 `--runtime` 才会执行真实 provider call；
4. 说明 `--runtime` 可能产生费用；
5. 说明 `llm-check` 不读取文章；
6. 说明 `llm-check` 不生成 sidecar；
7. 说明 `llm-check` 不影响 Quality Gate；
8. `docs/CLI.md` 增加 `llm-check` 命令；
9. `docs/CI.md` 说明默认 CI 不运行真实 `llm-check --runtime`；
10. `docs/ARCHITECTURE.md` 说明 smoke check 属于 provider diagnostics，不属于 review pipeline；
11. `PROJECT_STATE.md` 记录 TASK-0053 完成后状态；
12. `CHANGELOG.md` 记录本次变更。

---

## 9. 验收标准

本任务完成后应满足：

1. 存在 `content-review llm-check` 命令；
2. `llm-check` 支持 `--llm-config`；
3. `llm-check` 支持已有 LLM provider CLI override 参数；
4. `llm-check` 默认不执行真实 runtime call；
5. `llm-check --runtime` 才执行 runtime smoke call；
6. mock config check 可以通过；
7. mock runtime check 可以通过；
8. pydanticai config + secret check 可以通过；
9. pydanticai runtime check 可以通过 fake runtime 测试；
10. config error 返回清晰错误；
11. secret error 返回清晰错误；
12. runtime error 返回清晰错误；
13. 输出不包含 secret value；
14. 输出不包含完整 prompt；
15. 输出不包含 traceback；
16. 不改变 review / batch 行为；
17. 不改变 provider runtime 行为；
18. 不改变 sidecar schema；
19. 不改变 report 结构；
20. 不改变 Quality Gate；
21. 默认测试不依赖真实 API key；
22. 默认测试不访问真实网络；
23. 文档、PROJECT_STATE.md、CHANGELOG.md 已同步更新；
24. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 本任务是 diagnostics command，不是 review pipeline 变更；
2. 不要改变 review / batch 行为；
3. 不要生成 sidecar；
4. 不要把 smoke check 结果写入 ReviewResult；
5. 不要把 smoke check 结果接入 Quality Gate；
6. 不要让默认 `llm-check` 自动访问真实 provider；
7. 必须显式 `--runtime` 才允许真实 call；
8. 不要把真实 API key 写入输出；
9. 不要让默认 pytest 访问真实网络；
10. 不要新增真实 provider smoke test 到默认 CI；
11. 不要重构 provider runtime；
12. 不要新增 provider fallback；
13. 如果未来要做 optional CI smoke test，应单独放到 TASK-0054 或之后。

---

## 11. 完成后需要运行的命令

```bash id="wehhvj"
uv run pytest
```

如果新增专门测试文件，请额外运行：

```bash id="tqktvo"
uv run pytest tests/test_llm_smoke_check.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_provider_usage_docs.py
```

具体测试文件名以实际仓库为准。

---

