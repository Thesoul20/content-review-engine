# TASK-0050: Add PydanticAI Provider Retry Configuration

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计相关的 provider interface、mock reviewer、runner、sidecar JSON、sidecar Markdown report、provider configuration boundary、PydanticAI secret resolution、PydanticAI request / response mapping、PydanticAI runtime call、timeout 配置、runtime error classification，以及真实 PydanticAI provider 使用文档和手动验证夹具。

已完成任务包括：

```text id="fs7fa7"
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
```

当前 provider 状态是：

```text id="toqjj7"
provider="mock"
  -> 可运行；
  -> 不访问网络；
  -> 不需要 API key；
  -> 适合测试和 CI。

provider="pydanticai"
  -> 可运行；
  -> 支持 secret resolution；
  -> 支持真实 runtime call；
  -> 支持 OpenAI-compatible base_url；
  -> 支持 timeout_seconds；
  -> 支持 runtime error classification；
  -> 支持 manual verification docs；
  -> 输出仍走 LLM sidecar JSON / LLM sidecar Markdown report；
  -> 不影响 deterministic ReviewResult / Quality Gate。
```

TASK-0048 已经显式设置底层 OpenAI-compatible client 的 `max_retries=0`，避免 SDK 隐式重试。
因此，如果项目需要 retry，应该在项目自己的 provider boundary 中显式实现、显式配置、显式测试，而不是依赖 SDK 默认行为。

本任务目标是为 PydanticAI provider 增加**可控的显式 retry 配置**：

1. 用户可以配置 retry 次数；
2. 用户可以配置 retry backoff；
3. 只有明确可重试的错误才会 retry；
4. 不可重试错误应立即失败；
5. retry 不改变 sidecar schema；
6. retry 不改变 report 结构；
7. retry 不影响 deterministic Quality Gate；
8. 测试不依赖真实 API key 或真实网络。

本任务不做 rate limit queue、不做 batch concurrency、不做 streaming、不做 provider fallback、不做 Quality Gate 集成、不做主报告合并。

---

## 2. 任务目标

实现 PydanticAI provider 的显式 retry configuration。

完成后应满足：

1. `LLMProviderConfig` 支持 retry 配置；
2. CLI 支持配置 LLM retry；
3. PydanticAI provider 在 retryable runtime error 下可以按配置重试；
4. PydanticAI provider 对 non-retryable error 不重试；
5. retry 行为由项目代码控制，不依赖 SDK 隐式 retry；
6. 底层 OpenAI-compatible client 仍应保持 `max_retries=0`；
7. retry exhausted 后返回稳定 provider error；
8. retry 期间不泄露 API key、完整 prompt、完整文章内容或 traceback；
9. sidecar failed entry 仍使用既有 `error_type` / `message` schema；
10. mock provider 行为不变；
11. deterministic review 输出不变；
12. Quality Gate 语义不变；
13. 测试不依赖真实 API key 或真实网络。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 为 `LLMProviderConfig` 增加 retry 配置字段；
2. 为 CLI 增加 retry 参数；
3. 校验 retry 参数合法性；
4. 在 PydanticAI provider runtime call 外层增加显式 retry loop；
5. 明确 retryable error 类型；
6. 明确 non-retryable error 类型；
7. 新增 retry exhausted 错误类型，或复用稳定 provider error 层级；
8. 保持底层 client `max_retries=0`；
9. 增加可测试的 backoff / sleep 注入点，避免测试真实等待；
10. 更新 PydanticAI provider 测试；
11. 更新 CLI 测试；
12. 更新 provider config 测试；
13. 更新 sidecar failed entry 相关测试；
14. 更新 usage docs / CLI docs / CI docs；
15. 更新 PROJECT_STATE.md 和 CHANGELOG.md。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不实现 rate limit queue；
2. 不实现 batch concurrency；
3. 不实现 streaming；
4. 不实现多模型 fallback；
5. 不实现 provider fallback；
6. 不新增 `--fail-on-llm`；
7. 不让 Quality Gate 根据 LLM 结果失败；
8. 不把 LLM findings 合并进主 ReviewResult；
9. 不改变 LLMSidecarResult JSON schema；
10. 不改变 LLM sidecar Markdown report 结构；
11. 不改变 deterministic ReviewResult schema；
12. 不改变 deterministic JSON 输出结构；
13. 不改变 deterministic Markdown report 默认结构；
14. 不改变 batch manifest schema；
15. 不实现 API / MCP / GUI；
16. 不引入 Supabase、用户系统、SaaS、多租户、支付等能力；
17. 不新增 OpenAI / Anthropic 官方 SDK 独立 provider；
18. 不绕过 `LLMReviewer` provider interface；
19. 不让 tests 依赖真实 API key 或真实网络；
20. 不把 API key 写入 config、sidecar、report、日志或错误信息；
21. 不在 CI 中运行真实 provider 调用；
22. 不新增真实 API smoke test 到默认 pytest；
23. 不重构整个 CLI；
24. 不重构整个 LLM runner；
25. 不重构整个 provider runtime；
26. 不依赖 SDK 隐式 retry；
27. 不通过长时间 sleep 造成不稳定测试。

---

## 5. 需要修改的文件

预计包括但不限于：

```text id="m1t2st"
src/content_review_engine/llm/config.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/pydanticai.py
src/content_review_engine/llm/pydanticai_errors.py
src/content_review_engine/llm/__init__.py
src/content_review_engine/cli.py
tests/test_llm_config.py
tests/test_llm_pydanticai_provider.py
tests/test_llm_pydanticai_errors.py
tests/test_llm_provider.py
tests/test_cli.py
docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

如果 retry 逻辑较独立，可以新增：

```text id="vcttlh"
src/content_review_engine/llm/retry.py
tests/test_llm_retry.py
```

是否新增独立模块由实际复杂度决定。
如果逻辑较短，可以放在 `pydanticai.py` 中，但不要让 provider 文件过于臃肿。

---

## 6. 实现要求

### 6.1 LLMProviderConfig retry 字段

为 `LLMProviderConfig` 增加 retry 配置。

建议字段：

```text id="u5py1w"
retry_attempts: int = 0
retry_backoff_seconds: float = 0.0
```

字段语义：

```text id="tzcuy8"
retry_attempts
  -> 失败后的额外重试次数。
  -> 0 表示不重试。
  -> 1 表示最多执行 1 次初始调用 + 1 次重试。
  -> 2 表示最多执行 1 次初始调用 + 2 次重试。

retry_backoff_seconds
  -> 每次 retry 前等待的基础秒数。
  -> 0.0 表示不等待。
```

校验要求：

1. `retry_attempts` 必须为整数；
2. `retry_attempts >= 0`；
3. `retry_backoff_seconds` 必须为数字；
4. `retry_backoff_seconds >= 0`；
5. 非法值抛 `LLMProviderConfigError` 或 CLI 参数错误；
6. 不新增 retry jitter；
7. 不新增 retry max delay；
8. 不新增 retry budget；
9. 不新增 rate limit 配置；
10. 不新增 concurrency 配置。

说明：

```text id="fm9cds"
retry_attempts 是“额外重试次数”，不是总尝试次数。
```

---

### 6.2 CLI 参数

新增 CLI 参数：

```text id="ybshk5"
--llm-retry-attempts <count>
--llm-retry-backoff-seconds <seconds>
```

适用于：

```text id="mdajqi"
content-review review ...
content-review batch ...
```

要求：

1. 只有启用 `--enable-llm` 时才会实际影响 LLM provider；
2. 未启用 `--enable-llm` 时，不应影响 deterministic review；
3. 对 mock provider 可以解析但不实际改变行为；
4. 对 pydanticai provider 应传递到 `LLMProviderConfig`；
5. `--llm-retry-attempts` 非法值应给出清晰错误；
6. `--llm-retry-backoff-seconds` 非法值应给出清晰错误；
7. 错误信息不包含 secret；
8. 不新增 `--llm-rate-limit`；
9. 不新增 `--llm-concurrency`；
10. 不新增 `--fail-on-llm`。

示例：

```bash id="wa467l"
uv run content-review review article.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-timeout-seconds 30 \
  --llm-retry-attempts 2 \
  --llm-retry-backoff-seconds 1.0 \
  --llm-output article.llm.json
```

batch 示例：

```bash id="atr46d"
uv run content-review batch docs/ \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-timeout-seconds 30 \
  --llm-retry-attempts 2 \
  --llm-retry-backoff-seconds 1.0 \
  --llm-output-dir llm-sidecars \
  --llm-markdown-output llm-report.md
```

---

### 6.3 Retryable error 类型

只对明确可重试的 runtime error retry。

推荐 retryable：

```text id="5e2wg2"
LLMProviderTimeoutError
LLMProviderNetworkError
LLMProviderRateLimitError
```

可选 retryable：

```text id="bbn2m6"
LLMProviderRuntimeError
```

是否 retry `LLMProviderRuntimeError` 由实现判断。为了保守，推荐本任务先不 retry unknown runtime error，除非测试和文档明确说明。

推荐 non-retryable：

```text id="b7chd3"
LLMProviderSecretError
LLMProviderConfigError
LLMProviderAuthError
LLMProviderModelError
LLMResponseValidationError
```

原因：

```text id="t0q2j7"
secret/config/auth/model/validation 错误通常不是短暂故障，retry 不能解决。
```

要求：

1. retryable 类型必须在代码中集中定义或清晰表达；
2. non-retryable 类型不得 retry；
3. retry exhausted 后返回最后一个稳定 provider error，或包装为 retry exhausted error；
4. error message 不包含 secret；
5. error message 不包含完整 prompt；
6. error message 不包含完整文章内容；
7. error message 不包含 traceback。

---

### 6.4 Retry exhausted 表达

可以选择两种实现方式。

#### 方案 A：返回最后一个 classified error

例如：

```text id="gwpzga"
LLMProviderTimeoutError("PydanticAI runtime request timed out.")
```

优点：

```text id="id28ls"
sidecar error_type 仍是原始错误类型；
用户容易理解最终失败原因；
不新增错误类型。
```

#### 方案 B：新增 LLMProviderRetryExhaustedError

例如：

```text id="pjx2lq"
LLMProviderRetryExhaustedError("PydanticAI runtime retry attempts exhausted after 3 attempts.")
```

优点：

```text id="hg9k0y"
能明确表达 retry 已经发生并耗尽。
```

如果使用方案 B，错误中可以包含：

```text id="zzq3gu"
attempt_count
last_error_type
```

但不要改变 sidecar schema。
这些信息只能进入 message，或保留在异常对象内部，不能要求 sidecar schema 增加字段。

优先推荐方案 A，保持 sidecar error_type 简洁稳定。
如果团队希望更明确诊断 retry exhausted，也可以使用方案 B，但必须更新测试和文档。

---

### 6.5 Retry loop 行为

PydanticAI provider runtime call 应遵循：

```text id="je1swh"
total_attempts = 1 + retry_attempts
```

执行逻辑：

```text id="wx6g11"
for attempt in total_attempts:
    try:
        runtime call
        validate response
        map response
        return LLMReviewResult
    except retryable provider error:
        if attempts remain:
            sleep/backoff
            continue
        raise last error
    except non-retryable error:
        raise immediately
```

要求：

1. response validation error 不 retry；
2. secret error 不 retry；
3. config error 不 retry；
4. auth error 不 retry；
5. model error 不 retry；
6. timeout/network/rate limit 可以 retry；
7. 每次 retry 应重新执行 runtime call；
8. 不要重新解析 secret 多次，除非当前实现天然如此且不会泄露 secret；
9. 不要重新构造不必要的大对象，除非当前 runtime builder 设计要求；
10. 不要 fallback 到 mock；
11. 不要吞掉错误后返回空 findings；
12. 不要把 retry 过程写入 deterministic finding；
13. 不要把 retry 过程写入主 report。

---

### 6.6 Backoff / sleep 可测试性

为了避免测试真实等待，retry sleep 必须可测试。

可选方案：

#### 方案 A：dependency injection

在 `PydanticAIReviewer` 或 retry helper 中注入：

```text id="g1ie6h"
sleep: Callable[[float], None] = time.sleep
```

测试中传入 fake sleep。

#### 方案 B：retry helper 参数

```text id="my6dm8"
run_with_retries(..., sleep_func=time.sleep)
```

测试中传入 fake sleep。

要求：

1. 测试不得真实 sleep 很久；
2. backoff 逻辑可断言；
3. `retry_backoff_seconds=0` 时不 sleep 或 sleep 0；
4. 错误信息不包含 secret；
5. 不引入 async runtime 重构。

---

### 6.7 PydanticAI runtime client retry

TASK-0048 中底层 client 已经设置：

```text id="gn70ek"
max_retries=0
```

本任务必须保持：

```text id="smr69y"
SDK implicit retry disabled.
Project-level explicit retry controls all retry behavior.
```

要求：

1. 不把 `retry_attempts` 直接传给 SDK `max_retries`；
2. 不依赖 SDK 隐式 retry；
3. 底层 client 仍保持 `max_retries=0`；
4. retry 逻辑在项目 provider boundary 中实现；
5. 文档说明这一点。

---

### 6.8 Sidecar failed entry

本任务不改变 sidecar schema。

失败时仍然使用：

```text id="hj3ygk"
status: failed
error:
  error_type: ...
  message: ...
```

要求：

1. retryable error 最终失败后，sidecar error_type 稳定；
2. retry exhausted 不新增 sidecar 字段；
3. 不把 retry attempt details 作为新字段写入 sidecar；
4. 可以在 message 中简短说明 attempts exhausted；
5. message 不包含 secret；
6. message 不包含完整 prompt；
7. message 不包含完整文章内容；
8. message 不包含 traceback；
9. batch partial failure 语义不变；
10. LLM Markdown report 结构不变。

---

### 6.9 CLI 行为

CLI 行为要求：

1. `--enable-llm --llm-provider mock` 行为不变；
2. `--enable-llm --llm-provider pydanticai` 支持 retry 参数；
3. 未启用 `--enable-llm` 时 retry 参数不影响 deterministic review；
4. invalid retry 参数返回清晰 CLI/config error；
5. retry failure 不应变成 deterministic finding；
6. Quality Gate 仍只看 deterministic findings；
7. 不新增 `--fail-on-llm`；
8. 不新增 rate limit 参数；
9. 不新增 concurrency 参数。

对于 batch：

1. 每个文件的 LLM review 可独立 retry；
2. batch 中某个文件 retry exhausted 后应尽量复用 existing partial failure sidecar；
3. 不改变 batch manifest schema；
4. 不新增 batch 并发；
5. 不新增全局 retry budget。

---

### 6.10 Mock provider 行为

mock provider 不需要实现 retry。

要求：

1. mock provider 继续返回 mock result；
2. retry 参数对 mock provider 不产生行为变化；
3. CLI 可以解析 retry 参数；
4. mock provider 测试不应因为 retry 字段失败；
5. mock provider 不模拟真实 retry，除非已有测试机制需要。

---

### 6.11 Quality Gate 行为

Quality Gate 不应改变。

要求：

1. deterministic findings 仍然是 Quality Gate 唯一依据；
2. LLM retry failure 不应直接导致 Quality Gate failure；
3. LLM retry exhausted 不应变成 deterministic finding；
4. LLM retry attempts 不应影响 deterministic exit code 语义，除非当前 CLI provider initialization error 已有命令错误策略；
5. 不新增 LLM-based gate；
6. 不新增 `--fail-on-llm`。

文档中必须说明：

```text id="hfyf46"
LLM retry behavior only affects LLM provider runtime attempts.
Retry failures are reported through LLM provider/sidecar error paths and do not affect deterministic Quality Gate decisions.
```

---

## 7. 测试要求

所有测试必须避免真实 API key 和真实网络。

### 7.1 Config 测试

更新 `tests/test_llm_config.py`，覆盖：

1. 默认 `retry_attempts` 为 0；
2. 默认 `retry_backoff_seconds` 为 0.0；
3. 合法 `retry_attempts`；
4. 合法 `retry_backoff_seconds`；
5. `retry_attempts < 0` 非法；
6. `retry_backoff_seconds < 0` 非法；
7. 非整数 retry attempts 在 CLI 或 config 层非法；
8. retry 配置可序列化；
9. retry 配置不影响 secret 安全；
10. retry 配置不影响 mock 默认行为。

---

### 7.2 Retry helper / provider 测试

更新或新增测试，覆盖：

1. retry_attempts=0 时不 retry；
2. retry_attempts=1 时最多执行 2 次 runtime call；
3. retry_attempts=2 时最多执行 3 次 runtime call；
4. timeout error 后 retry 成功；
5. network error 后 retry 成功；
6. rate limit error 后 retry 成功；
7. retry exhausted 后返回稳定 error；
8. auth error 不 retry；
9. model error 不 retry；
10. response validation error 不 retry；
11. secret error 不 retry；
12. config error 不 retry；
13. unknown runtime error 是否 retry 与实现文档一致；
14. 不 fallback 到 mock；
15. 不发起真实网络；
16. 不泄露 secret；
17. fake sleep 被调用正确次数；
18. retry_backoff_seconds 被传给 fake sleep。

建议新增：

```text id="ktdoxd"
tests/test_llm_retry.py
```

或者放在：

```text id="yd2gaw"
tests/test_llm_pydanticai_provider.py
```

如果 retry 逻辑被抽成独立模块，推荐新增 `tests/test_llm_retry.py`。

---

### 7.3 Error classification 回归测试

更新 `tests/test_llm_pydanticai_errors.py`，覆盖：

1. timeout 仍分类为 `LLMProviderTimeoutError`；
2. network 仍分类为 `LLMProviderNetworkError`；
3. rate limit 仍分类为 `LLMProviderRateLimitError`；
4. auth 仍分类为 `LLMProviderAuthError`；
5. model 仍分类为 `LLMProviderModelError`；
6. unknown 仍分类为 `LLMProviderRuntimeError`；
7. retry 不改变 error classification；
8. error message 不泄露 secret、prompt、文章内容或 traceback。

---

### 7.4 CLI 测试

更新 `tests/test_cli.py`，覆盖：

1. review 命令可解析 `--llm-retry-attempts`；
2. review 命令可解析 `--llm-retry-backoff-seconds`；
3. batch 命令可解析 `--llm-retry-attempts`；
4. batch 命令可解析 `--llm-retry-backoff-seconds`；
5. invalid retry attempts 返回清晰错误；
6. invalid retry backoff 返回清晰错误；
7. 未启用 `--enable-llm` 时 retry 参数不影响 deterministic review；
8. mock provider 下 retry 参数不改变行为；
9. pydanticai fake timeout first attempt + success second attempt；
10. pydanticai fake retry exhausted 进入 failed sidecar；
11. batch 中某文件 retry exhausted 可记录 partial failure；
12. Quality Gate 不受 LLM retry failure 影响；
13. CLI stderr / sidecar / report 不包含 secret。

---

### 7.5 Sidecar / report 测试

如果现有 sidecar tests 已覆盖 failed entry，可补充 retry exhausted case。

至少覆盖：

1. retry exhausted 的 `error_type` 稳定；
2. retry exhausted 的 `message` 稳定；
3. batch manifest partial failure 中可记录 retry exhausted；
4. LLM Markdown report 可以展示 retry exhausted failed entry；
5. 不改变 sidecar schema；
6. 不改变 Markdown report 结构。

---

### 7.6 回归测试

必须确保已有测试全部通过：

```bash id="4fwtoy"
uv run pytest
```

如果新增或修改了专门测试文件，也请额外运行：

```bash id="c9mzol"
uv run pytest tests/test_llm_config.py
uv run pytest tests/test_llm_retry.py
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_pydanticai_errors.py
uv run pytest tests/test_llm_provider.py
uv run pytest tests/test_cli.py
```

具体测试文件名以实际仓库为准。

---

## 8. 文档更新要求

需要更新以下文档：

```text id="t1pat0"
docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

更新重点：

1. 在 `docs/LLM_PROVIDER_USAGE.md` 中说明 retry 配置；
2. 在 `docs/LLM_PROVIDER_USAGE.md` 中说明哪些错误会 retry；
3. 在 `docs/LLM_PROVIDER_USAGE.md` 中说明哪些错误不会 retry；
4. 在 `docs/LLM_PROVIDER_USAGE.md` 中说明底层 SDK implicit retry 仍关闭；
5. 在 `docs/CLI.md` 中说明 `--llm-retry-attempts`；
6. 在 `docs/CLI.md` 中说明 `--llm-retry-backoff-seconds`；
7. 在 `docs/CI.md` 中说明 retry tests 仍使用 fake runtime，不需要真实 API key；
8. 在 `docs/ARCHITECTURE.md` 中说明 retry 属于 provider runtime boundary；
9. 在 `docs/DATA_MODELS.md` 中说明 `LLMProviderConfig.retry_attempts` 和 `retry_backoff_seconds`；
10. 在 `PROJECT_STATE.md` 中记录 TASK-0050 已完成后项目状态；
11. 在 `CHANGELOG.md` 中记录本次变更。

---

## 9. 验收标准

本任务完成后应满足：

1. `LLMProviderConfig` 支持 retry 配置；
2. CLI 支持 `--llm-retry-attempts`；
3. CLI 支持 `--llm-retry-backoff-seconds`；
4. invalid retry 参数会返回清晰错误；
5. retry_attempts 默认 0；
6. retry_backoff_seconds 默认 0.0；
7. pydanticai runtime 对 retryable error 可重试；
8. pydanticai runtime 对 non-retryable error 不重试；
9. retry exhausted 后返回稳定错误；
10. 底层 SDK implicit retry 仍关闭；
11. retry 不泄露 secret、完整 prompt、完整文章内容或 traceback；
12. sidecar JSON schema 不变；
13. LLM sidecar Markdown report 结构不变；
14. deterministic JSON / Markdown report 行为不变；
15. Quality Gate 语义不变；
16. mock provider 行为不变；
17. 不新增 rate limit queue；
18. 不新增 batch concurrency；
19. 不新增 streaming；
20. 不新增 provider fallback；
21. 测试不依赖真实 API key；
22. 测试不发起真实网络；
23. 文档、PROJECT_STATE.md、CHANGELOG.md 已同步更新；
24. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 本任务只做 retry configuration；
2. 不要顺手做 rate limit queue；
3. 不要顺手做 batch concurrency；
4. 不要顺手做 streaming；
5. 不要顺手做 provider fallback；
6. 不要改变 sidecar schema；
7. 不要改变 report 结构；
8. 不要改变 Quality Gate；
9. 不要把 retry exhausted 当成 Quality Gate failure；
10. 不要把 retry failure 写成 deterministic finding；
11. 不要把 secret value 写入任何输出；
12. 不要把完整 prompt 或完整文章内容写入错误信息；
13. 不要用真实网络测试 retry；
14. 不要通过长时间 sleep 制造不稳定测试；
15. 不要依赖 SDK implicit retry；
16. 如果 backoff 逻辑需要等待，测试中必须使用 fake sleep；
17. 后续 rate limit / concurrency 应单独放到 TASK-0051 或之后。

---

## 11. 完成后需要运行的命令

```bash id="f68vau"
uv run pytest
```

如果涉及专门测试文件，请额外运行：

```bash id="t6vb6x"
uv run pytest tests/test_llm_config.py
uv run pytest tests/test_llm_retry.py
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_pydanticai_errors.py
uv run pytest tests/test_llm_provider.py
uv run pytest tests/test_cli.py
```

具体测试文件名以实际仓库为准。

---

