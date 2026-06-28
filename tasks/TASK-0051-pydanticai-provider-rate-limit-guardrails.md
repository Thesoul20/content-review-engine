# TASK-0051: Add PydanticAI Provider Rate Limit Guardrails

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计相关的 provider interface、mock reviewer、runner、sidecar JSON、sidecar Markdown report、provider configuration boundary、PydanticAI secret resolution、PydanticAI request / response mapping、PydanticAI runtime call、timeout 配置、runtime error classification、真实 provider 使用文档，以及显式 retry configuration。

已完成任务包括：

```text id="0iv0yz"
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
```

当前 provider 状态是：

```text id="hqwofm"
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
  -> 支持显式 retry_attempts；
  -> 支持 retry_backoff_seconds；
  -> 输出仍走 LLM sidecar JSON / LLM sidecar Markdown report；
  -> 不影响 deterministic ReviewResult / Quality Gate。
```

TASK-0050 已经实现了显式 retry，但还没有项目级的 request pacing / rate limit guardrails。

在 batch 场景中，如果连续对多个 Markdown 文件执行真实 LLM review，可能会短时间内连续发起多次 provider 请求。即使没有 batch 并发，也可能触发 provider 侧 rate limit。为了让真实 provider 的使用更安全，本任务需要增加一个轻量的、本地的请求节流护栏：

> 在 PydanticAI provider 内部支持最小请求间隔，确保同一个 reviewer 实例连续发起 runtime call 时，至少间隔指定秒数。

本任务只做 request pacing / minimum interval guardrail，不做 rate limit queue、不做全局令牌桶、不做 batch 并发、不做多 worker 协调、不做 provider fallback、不改变 Quality Gate。

---

## 2. 任务目标

实现 PydanticAI provider 的本地 rate limit guardrails。

完成后应满足：

1. `LLMProviderConfig` 支持最小请求间隔配置；
2. CLI 支持配置 LLM provider 最小请求间隔；
3. PydanticAI provider 在连续 runtime call 之间按配置进行 pacing；
4. pacing 对 batch 场景有效；
5. pacing 对 retry runtime call 也应保持清晰语义；
6. mock provider 行为不变；
7. deterministic review 输出不变；
8. sidecar JSON schema 不变；
9. LLM sidecar Markdown report 结构不变；
10. Quality Gate 语义不变；
11. 测试不依赖真实 API key；
12. 测试不访问真实网络；
13. 测试不使用真实长时间 sleep。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 为 `LLMProviderConfig` 增加 request pacing / minimum interval 配置字段；
2. 为 CLI 增加对应参数；
3. 校验 pacing 参数合法性；
4. 在 PydanticAI provider runtime call 前增加 request pacing；
5. 增加可测试的 clock / sleep 注入点；
6. 确保 batch 复用同一个 provider 实例时可以执行 pacing；
7. 明确 pacing 与 retry_backoff_seconds 的关系；
8. 更新 PydanticAI provider 测试；
9. 更新 CLI 测试；
10. 更新 config 测试；
11. 更新 usage docs / CLI docs / CI docs / architecture docs / data model docs；
12. 更新 PROJECT_STATE.md 和 CHANGELOG.md。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不实现 rate limit queue；
2. 不实现 token bucket；
3. 不实现 leaky bucket；
4. 不实现全局跨进程 rate limiter；
5. 不实现 batch 并发；
6. 不实现 streaming；
7. 不实现多模型 fallback；
8. 不实现 provider fallback；
9. 不新增 `--fail-on-llm`；
10. 不让 Quality Gate 根据 LLM 结果失败；
11. 不把 LLM findings 合并进主 ReviewResult；
12. 不改变 LLMSidecarResult JSON schema；
13. 不改变 LLM sidecar Markdown report 结构；
14. 不改变 deterministic ReviewResult schema；
15. 不改变 deterministic JSON 输出结构；
16. 不改变 deterministic Markdown report 默认结构；
17. 不改变 batch manifest schema；
18. 不实现 API / MCP / GUI；
19. 不引入 Supabase、用户系统、SaaS、多租户、支付等能力；
20. 不新增 OpenAI / Anthropic 官方 SDK 独立 provider；
21. 不绕过 `LLMReviewer` provider interface；
22. 不让 tests 依赖真实 API key 或真实网络；
23. 不把 API key 写入 config、sidecar、report、日志或错误信息；
24. 不在 CI 中运行真实 provider 调用；
25. 不新增真实 API smoke test 到默认 pytest；
26. 不重构整个 CLI；
27. 不重构整个 LLM runner；
28. 不通过长时间 sleep 造成不稳定测试。

---

## 5. 需要修改的文件

预计包括但不限于：

```text id="2az4sb"
src/content_review_engine/llm/config.py
src/content_review_engine/llm/pydanticai.py
src/content_review_engine/llm/__init__.py
src/content_review_engine/cli.py
tests/test_llm_config.py
tests/test_llm_pydanticai_provider.py
tests/test_cli.py
docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

如果 pacing 逻辑适合独立模块，可以新增：

```text id="fgz1ha"
src/content_review_engine/llm/rate_limit.py
tests/test_llm_rate_limit.py
```

是否新增独立模块由实际复杂度决定。
如果逻辑很短，可以放在 `pydanticai.py` 中，但不要让 provider 文件过于臃肿。

---

## 6. 实现要求

### 6.1 LLMProviderConfig 新增字段

为 `LLMProviderConfig` 增加最小请求间隔配置。

建议字段名：

```text id="nijunb"
min_request_interval_seconds: float = 0.0
```

字段语义：

```text id="1qoev4"
min_request_interval_seconds
  -> 同一个 provider/reviewer 实例连续两次真实 runtime call 之间的最小间隔。
  -> 0.0 表示不做本地 pacing。
```

校验要求：

1. 必须是数字；
2. 必须 `>= 0`；
3. `0.0` 合法，表示不等待；
4. 负数非法；
5. 非数字非法；
6. 非法值抛 `LLMProviderConfigError` 或 CLI 参数错误；
7. 不新增 `requests_per_minute`；
8. 不新增 `tokens_per_minute`；
9. 不新增 `max_concurrency`；
10. 不新增 queue 配置；
11. 不新增 provider fallback 配置。

---

### 6.2 CLI 参数

新增 CLI 参数：

```text id="oc23t1"
--llm-min-request-interval-seconds <seconds>
```

适用于：

```text id="2hdq4b"
content-review review ...
content-review batch ...
```

要求：

1. 只有启用 `--enable-llm` 时才会实际影响 LLM provider；
2. 未启用 `--enable-llm` 时，不应影响 deterministic review；
3. 对 mock provider 可以解析但不实际改变行为；
4. 对 pydanticai provider 应传递到 `LLMProviderConfig`；
5. 非法值应给出清晰错误；
6. 错误信息不包含 secret；
7. 不新增 `--llm-rate-limit`;
8. 不新增 `--llm-requests-per-minute`;
9. 不新增 `--llm-concurrency`;
10. 不新增 `--fail-on-llm`。

示例：

```bash id="nmn7ki"
uv run content-review review article.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-timeout-seconds 30 \
  --llm-retry-attempts 2 \
  --llm-retry-backoff-seconds 1.0 \
  --llm-min-request-interval-seconds 2.0 \
  --llm-output article.llm.json
```

batch 示例：

```bash id="pg3pds"
uv run content-review batch docs/ \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-timeout-seconds 30 \
  --llm-retry-attempts 2 \
  --llm-retry-backoff-seconds 1.0 \
  --llm-min-request-interval-seconds 2.0 \
  --llm-output-dir llm-sidecars \
  --llm-markdown-output llm-report.md
```

---

### 6.3 Request pacing 行为

PydanticAI provider 应在每次真实 runtime call 前执行 pacing。

建议语义：

```text id="u386ki"
first runtime call
  -> 不等待

subsequent runtime call
  -> 如果距离上一次 runtime call started_at 小于 min_request_interval_seconds
  -> sleep remaining seconds
```

也可以使用 `last_request_finished_at`，但必须文档和测试中明确语义。
推荐使用 `last_request_started_at`，因为它更接近 provider request rate 的语义。

要求：

1. `min_request_interval_seconds = 0.0` 时不 sleep；
2. 第一次 runtime call 不 sleep；
3. 第二次及之后 runtime call 根据间隔 sleep；
4. batch 多文件 review 应复用同一个 reviewer 实例时自然生效；
5. retry 产生的额外 runtime call 也应经过 pacing；
6. pacing 不影响 mock provider；
7. pacing 不改变 runtime response mapping；
8. pacing 不改变 retryable / non-retryable error 规则；
9. pacing 不把等待过程写入 sidecar；
10. pacing 不影响 Quality Gate。

---

### 6.4 与 retry_backoff_seconds 的关系

当前已有：

```text id="1pslo0"
retry_attempts
retry_backoff_seconds
```

本任务新增：

```text id="nclfi8"
min_request_interval_seconds
```

必须明确两者关系。

推荐行为：

```text id="48vcjz"
当 runtime call 失败且需要 retry 时：

1. 先执行 retry_backoff_seconds 对应的 retry backoff；
2. 然后执行 min_request_interval_seconds pacing 检查；
3. 如果 backoff 已经让请求间隔满足 min interval，则 pacing 不再额外 sleep；
4. 如果 backoff 不足以满足 min interval，则 pacing 只 sleep remaining seconds。
```

要求：

1. retry backoff 和 request pacing 不应互相替代；
2. retry backoff 表示失败后的恢复等待；
3. min_request_interval_seconds 表示 provider 请求节流；
4. 两者都使用 fake sleep 测试；
5. 不要真实 sleep 很久；
6. 不要引入 jitter；
7. 不要引入 exponential backoff；
8. 不要引入 retry budget；
9. 不要引入 rate limit queue。

---

### 6.5 Clock / sleep 可测试性

为了避免测试真实等待，pacing 必须可测试。

建议注入：

```text id="1yoz7a"
sleep_func: Callable[[float], None] = time.sleep
monotonic_func: Callable[[], float] = time.monotonic
```

或通过独立 rate limiter/pacer 类注入：

```text id="dt9y8v"
PydanticAIRequestPacer(
    min_interval_seconds: float,
    sleep_func: Callable[[float], None],
    monotonic_func: Callable[[], float],
)
```

要求：

1. 测试不得真实 sleep 很久；
2. 测试可以断言 sleep 调用次数；
3. 测试可以断言 sleep 参数；
4. 测试可以模拟时间推进；
5. 不引入 async runtime 重构；
6. 不引入线程 / 进程 / signal hack。

---

### 6.6 Sidecar 行为

本任务不改变 sidecar schema。

要求：

1. pacing 成功时不写入额外 sidecar 字段；
2. pacing 不改变 review result；
3. pacing 不改变 finding_count；
4. pacing 不改变 failed sidecar entry；
5. pacing 不改变 batch manifest schema；
6. pacing 不改变 sidecar Markdown report 结构；
7. 如果 runtime 在 pacing 后失败，仍按现有 provider error / retry exhausted error 处理；
8. 不把 sleep duration 写入 sidecar；
9. 不把 internal timing 写入 sidecar。

---

### 6.7 CLI 行为

CLI 行为要求：

1. `--enable-llm --llm-provider mock` 行为不变；
2. `--enable-llm --llm-provider pydanticai` 支持 `--llm-min-request-interval-seconds`；
3. 未启用 `--enable-llm` 时，该参数不影响 deterministic review；
4. invalid min interval 返回清晰 CLI/config error；
5. pacing 不应变成 deterministic finding；
6. Quality Gate 仍只看 deterministic findings；
7. 不新增 `--fail-on-llm`;
8. 不新增 queue / concurrency / requests-per-minute 参数。

对于 batch：

1. 每个文件的 LLM review 可以通过同一个 pydanticai reviewer 被 pacing；
2. 不新增 batch 并发；
3. 不改变 batch manifest schema；
4. 不新增全局 worker queue；
5. 不新增跨命令或跨进程状态。

---

### 6.8 Mock provider 行为

mock provider 不需要实现 pacing。

要求：

1. mock provider 继续返回 mock result；
2. min interval 参数对 mock provider 不产生行为变化；
3. CLI 可以解析该参数；
4. mock provider 测试不应因为新增字段失败；
5. mock provider 不模拟真实 pacing，除非已有测试机制需要。

---

### 6.9 Quality Gate 行为

Quality Gate 不应改变。

要求：

1. deterministic findings 仍然是 Quality Gate 唯一依据；
2. LLM pacing 不影响 deterministic findings；
3. LLM pacing 不影响 deterministic exit code；
4. LLM runtime failure / retry exhausted 仍不变成 deterministic finding；
5. 不新增 LLM-based gate；
6. 不新增 `--fail-on-llm`。

文档中必须说明：

```text id="5hwqe4"
LLM request pacing only affects provider runtime request timing.
It does not affect deterministic review results or Quality Gate decisions.
```

---

## 7. 测试要求

所有测试必须避免真实 API key 和真实网络。

### 7.1 Config 测试

更新 `tests/test_llm_config.py`，覆盖：

1. 默认 `min_request_interval_seconds` 为 0.0；
2. 合法 `min_request_interval_seconds`；
3. `min_request_interval_seconds = 0.0` 合法；
4. `min_request_interval_seconds < 0` 非法；
5. 非数字 min interval 在 CLI 或 config 层非法；
6. config serialization 包含 min interval；
7. min interval 配置不影响 secret 安全；
8. min interval 配置不影响 mock 默认行为。

---

### 7.2 Pacer / rate limit 测试

如果新增 `rate_limit.py`，新增：

```text id="ht8jf6"
tests/test_llm_rate_limit.py
```

覆盖：

1. 第一次 call 不 sleep；
2. 第二次 call 在间隔不足时 sleep remaining；
3. 间隔已满足时不 sleep；
4. min interval 为 0 时不 sleep；
5. sleep 参数稳定；
6. monotonic 时间可注入；
7. 不真实 sleep。

如果不新增独立模块，则在 provider 测试中覆盖同等行为。

---

### 7.3 PydanticAI provider 测试

更新 `tests/test_llm_pydanticai_provider.py`，覆盖：

1. min interval 传入 provider；
2. 第一次 fake runtime call 不 sleep；
3. 连续两次 fake runtime call 会触发 fake sleep；
4. 时间间隔已满足时不 sleep；
5. retry 时 backoff 与 pacing 的顺序符合文档；
6. retry backoff 已满足 min interval 时 pacing 不额外 sleep；
7. retry backoff 不足时 pacing sleep remaining；
8. 不 fallback 到 mock；
9. 不发起真实网络；
10. 不泄露 secret；
11. runtime response mapping 不变；
12. runtime error classification 不变。

---

### 7.4 CLI 测试

更新 `tests/test_cli.py`，覆盖：

1. review 命令可解析 `--llm-min-request-interval-seconds`；
2. batch 命令可解析 `--llm-min-request-interval-seconds`；
3. invalid min interval 返回清晰错误；
4. 未启用 `--enable-llm` 时 min interval 不影响 deterministic review；
5. mock provider 下 min interval 不改变行为；
6. pydanticai fake runtime batch 中可观察 pacing；
7. pydanticai fake runtime retry 场景中 pacing 与 backoff 可观察；
8. Quality Gate 不受 min interval 影响；
9. CLI stderr / sidecar / report 不包含 secret。

---

### 7.5 Sidecar / report 回归测试

如果现有 sidecar tests 已经覆盖 schema，可只做回归确认。

至少确认：

1. min interval 不改变 sidecar JSON schema；
2. min interval 不改变 LLM Markdown report 结构；
3. min interval 不改变 batch manifest schema；
4. min interval 不写入 sidecar；
5. min interval 不影响 finding_count；
6. min interval 不影响 Quality Gate。

---

### 7.6 回归测试

必须确保已有测试全部通过：

```bash id="s5ku5v"
uv run pytest
```

如果新增或修改了专门测试文件，也请额外运行：

```bash id="wepy2y"
uv run pytest tests/test_llm_config.py
uv run pytest tests/test_llm_rate_limit.py
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_retry.py
uv run pytest tests/test_cli.py
```

具体测试文件名以实际仓库为准。

---

## 8. 文档更新要求

需要更新以下文档：

```text id="q6352j"
docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

更新重点：

1. 在 `docs/LLM_PROVIDER_USAGE.md` 中说明 request pacing / min interval；
2. 在 `docs/LLM_PROVIDER_USAGE.md` 中说明 pacing 与 retry backoff 的区别；
3. 在 `docs/LLM_PROVIDER_USAGE.md` 中说明 batch 使用建议；
4. 在 `docs/CLI.md` 中说明 `--llm-min-request-interval-seconds`；
5. 在 `docs/CI.md` 中说明 pacing tests 使用 fake clock / fake sleep，不需要真实 provider；
6. 在 `docs/ARCHITECTURE.md` 中说明 pacing 属于 provider runtime boundary；
7. 在 `docs/DATA_MODELS.md` 中说明 `LLMProviderConfig.min_request_interval_seconds`；
8. 在 `PROJECT_STATE.md` 中记录 TASK-0051 已完成后项目状态；
9. 在 `CHANGELOG.md` 中记录本次变更。

---

## 9. 验收标准

本任务完成后应满足：

1. `LLMProviderConfig` 支持 `min_request_interval_seconds`；
2. CLI 支持 `--llm-min-request-interval-seconds`；
3. invalid min interval 参数会返回清晰错误；
4. min interval 默认 0.0；
5. pydanticai provider 连续 runtime call 会按 min interval pacing；
6. batch pydanticai review 可以自然受到 pacing；
7. retry runtime call 也会经过 pacing；
8. retry_backoff_seconds 与 min_request_interval_seconds 的关系清晰且有测试；
9. pacing 不泄露 secret、完整 prompt、完整文章内容或 traceback；
10. sidecar JSON schema 不变；
11. LLM sidecar Markdown report 结构不变；
12. deterministic JSON / Markdown report 行为不变；
13. batch manifest schema 不变；
14. Quality Gate 语义不变；
15. mock provider 行为不变；
16. 不新增 queue；
17. 不新增 token bucket；
18. 不新增 batch concurrency；
19. 不新增 streaming；
20. 不新增 provider fallback；
21. 测试不依赖真实 API key；
22. 测试不发起真实网络；
23. 测试不真实长时间 sleep；
24. 文档、PROJECT_STATE.md、CHANGELOG.md 已同步更新；
25. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 本任务只做轻量 request pacing；
2. 不要顺手做 rate limit queue；
3. 不要顺手做 token bucket；
4. 不要顺手做 batch concurrency；
5. 不要顺手做 streaming；
6. 不要顺手做 provider fallback；
7. 不要改变 sidecar schema；
8. 不要改变 report 结构；
9. 不要改变 Quality Gate；
10. 不要把 pacing 信息写进 deterministic finding；
11. 不要把 pacing 作为 Quality Gate 条件；
12. 不要把 secret value 写入任何输出；
13. 不要用真实网络测试 pacing；
14. 不要通过真实长 sleep 制造慢测试；
15. 如果未来要做 requests-per-minute / token bucket / global limiter，应单独放到 TASK-0052 或之后。

---

## 11. 完成后需要运行的命令

```bash id="63vr5f"
uv run pytest
```

如果涉及专门测试文件，请额外运行：

```bash id="x8xqpo"
uv run pytest tests/test_llm_config.py
uv run pytest tests/test_llm_rate_limit.py
uv run pytest tests/test_llm_pydanticai_provider.py
uv run pytest tests/test_llm_retry.py
uv run pytest tests/test_cli.py
```

具体测试文件名以实际仓库为准。

---
