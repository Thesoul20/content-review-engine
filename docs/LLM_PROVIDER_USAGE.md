# LLM Provider Usage

## Overview

This project supports an optional LLM sidecar review path that is separate from
the deterministic review pipeline.

- Deterministic review remains the canonical `ReviewResult` and
  `BatchReviewResult` output.
- LLM review writes separate `LLMSidecarResult` JSON and optional Markdown
  sidecar reports.
- LLM findings do not change deterministic JSON, deterministic Markdown
  reports, or `--fail-on` quality-gate behavior.

## Supported Providers

- `mock`: safe for local tests and CI, requires no API key, performs no
  network calls.
- `pydantic-ai-testmodel`: package-level testing provider built on
  `pydantic_ai.models.test.TestModel`, requires no API key, performs no
  network calls, and is available to `llm-check --provider` through the
  package reviewer factory.
- `pydanticai`: real runtime provider, requires an API key through an
  environment variable, can call an external OpenAI-compatible endpoint, and
  should be used only for explicit manual verification.

## Reviewer Provider Factory

The package now exposes a reviewer-provider factory for internal code paths
that want a concrete `LLMReviewer` from a stable provider name without
constructing CLI config.

Current reviewer provider names:

- `mock`
- `pydantic-ai-testmodel`

Example:

```python
from content_review_engine.llm import create_llm_reviewer

reviewer = create_llm_reviewer("mock")
testmodel_reviewer = create_llm_reviewer("pydantic-ai-testmodel")
```

Factory behavior:

- `create_llm_reviewer("mock")` returns `MockLLMReviewer`
- `create_llm_reviewer("pydantic-ai-testmodel")` returns
  `PydanticAITestModelReviewer`
- unsupported provider names raise a clear error and do not silently fall back
- this factory path does not read `.env`, does not require an API key, and
  does not access the network for the supported reviewer providers above

This is a package boundary for future adapters. `llm-check --provider` now
reuses it for the safe local reviewer providers above. It still does not
change the default behavior of `review`, `batch`, or `llm-check`.

## PydanticAI TestModel Provider

`PydanticAITestModelReviewer` exists to test the project's `LLMReviewer`
boundary without real provider credentials or runtime network access.

Use it when you need:

- a provider implementation that accepts `LLMReviewRequest`
- stable prompt/request construction through the existing PydanticAI mapping
- a returned `LLMReviewResult` instead of raw PydanticAI output
- local unit tests that do not depend on `.env`, shell secrets, or remote APIs

Current limitations:

- it is a Python package provider only, available through the package-level
  reviewer provider factory, not as a CLI-selectable provider
- it does not read `LLMProviderConfig`
- it does not participate in `content-review review`, `batch`, or
  `llm-check`
- it should not be treated as a production LLM integration

## LLM Check Command

Use `llm-check` when you want to validate provider setup without mixing that
verification into `review` or `batch`.

Examples:

```bash
uv run content-review llm-check
uv run content-review llm-check --provider mock --runtime
uv run content-review llm-check --provider pydantic-ai-testmodel --runtime
uv run content-review llm-check --llm-config examples/llm/mock/llm-provider.yml
uv run content-review llm-check --llm-config examples/llm/pydanticai/llm-provider.yml
uv run content-review llm-check --llm-config examples/llm/pydanticai/llm-provider.yml --runtime
```

Default behavior:

- config check
- secret check when the provider requires one
- no runtime call

`--provider` behavior:

- supports only `mock` and `pydantic-ai-testmodel`
- uses `create_llm_reviewer()` directly instead of config-driven provider construction
- does not require an API key
- does not read `.env`
- does not access the network for the supported factory providers
- fails explicitly for unsupported values and does not fall back to config or `mock`

`--runtime` behavior:

- adds a synthetic minimal `LLMReviewRequest`
- does not read a real article or review profile
- does not write sidecars or deterministic review output
- may access the real provider for `pydanticai`
- may incur provider cost for `pydanticai`

Use `llm-check --runtime` only for explicit manual verification.

## PydanticAI Provider

Use `--llm-provider pydanticai` only when you intentionally want a real LLM
sidecar review.

Provider parameters covered by the current CLI:

- `--llm-config examples/llm/pydanticai/llm-provider.yml`
- `--llm-provider pydanticai`
- `--llm-model openai:gpt-4o-mini`
- `--llm-api-key-env OPENAI_API_KEY`
- `--llm-base-url https://your-openai-compatible-endpoint.example/v1`
- `--llm-timeout-seconds 30`
- `--llm-retry-attempts 2`
- `--llm-retry-backoff-seconds 1.0`
- `--llm-min-request-interval-seconds 2.0`

`--llm-model` is required for `pydanticai`.
`--llm-api-key-env` stores only the environment variable name, not the secret
value itself.
`--llm-config` can load the same provider fields from a YAML file, and any
explicit CLI flag overrides the same field from that file.
`--llm-base-url` is optional and is only for OpenAI-compatible endpoints.
`--llm-timeout-seconds` is optional and affects only the provider runtime.
`--llm-retry-attempts` is optional, defaults to `0`, and means extra retry
attempts after the initial runtime call.
`--llm-retry-backoff-seconds` is optional, defaults to `0.0`, and is the fixed
sleep before each retryable retry.
`--llm-min-request-interval-seconds` is optional, defaults to `0.0`, and is
the minimum spacing between consecutive real runtime call start times on the
same `pydanticai` reviewer instance.
The same fields can also be used with `content-review llm-check`.

## Required Environment Variables

Use the placeholder example at
`examples/llm/pydanticai/.env.example`.

Example:

```dotenv
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE
OPENAI_BASE_URL=https://your-openai-compatible-endpoint.example/v1
```

Load real values only in your shell or local secret manager. Do not commit real
keys, paste them into CLI arguments, or put them into profile files.

## Manual Verification Fixtures

This repository includes safe local fixtures for manual verification:

- `examples/llm/pydanticai/manual-review.md`
- `examples/llm/pydanticai/manual-profile.yml`
- `examples/llm/pydanticai/llm-provider.yml`
- `examples/llm/mock/llm-provider.yml`
- `examples/llm/pydanticai/batch/article-a.md`
- `examples/llm/pydanticai/batch/article-b.md`

These files are intentionally short and contain no real credentials.

## Single-file Manual Verification

Set your secret in the shell first:

```bash
export OPENAI_API_KEY="replace-with-your-real-key"
```

Optional for OpenAI-compatible endpoints:

```bash
export OPENAI_BASE_URL="https://your-openai-compatible-endpoint.example/v1"
```

Run:

```bash
uv run content-review review \
  examples/llm/pydanticai/manual-review.md \
  --profile examples/llm/pydanticai/manual-profile.yml \
  --format markdown \
  --enable-llm \
  --llm-config examples/llm/pydanticai/llm-provider.yml \
  --llm-base-url "$OPENAI_BASE_URL" \
  --llm-output /tmp/content-review-single.llm.json \
  --llm-markdown-output /tmp/content-review-single.llm.md \
  --include-llm-report
```

CLI override example:

```bash
uv run content-review review \
  examples/llm/pydanticai/manual-review.md \
  --profile examples/llm/pydanticai/manual-profile.yml \
  --enable-llm \
  --llm-config examples/llm/pydanticai/llm-provider.yml \
  --llm-model openai:gpt-4.1-mini \
  --llm-output /tmp/content-review-single.llm.json
```

What to verify:

1. The main command still returns deterministic review output.
2. `/tmp/content-review-single.llm.json` is written as a separate sidecar.
3. `/tmp/content-review-single.llm.md` is written as a separate LLM report.
4. The deterministic quality gate still depends only on deterministic
   findings.

## Batch Manual Verification

```bash
uv run content-review batch \
  examples/llm/pydanticai/batch \
  --profile examples/llm/pydanticai/manual-profile.yml \
  --recursive \
  --enable-llm \
  --llm-config examples/llm/pydanticai/llm-provider.yml \
  --llm-base-url "$OPENAI_BASE_URL" \
  --llm-output-dir /tmp/content-review-batch-llm \
  --llm-markdown-output /tmp/content-review-batch-llm.md
```

What to verify:

1. One sidecar JSON file is written per Markdown file.
2. `/tmp/content-review-batch-llm/llm-review-manifest.json` exists.
3. `/tmp/content-review-batch-llm.md` exists.
4. A failed LLM file, if any, is recorded in the sidecar output without
   changing deterministic batch quality-gate semantics.

## Sidecar JSON Output

Single-file and batch LLM sidecars use `LLMSidecarResult`.

Check:

- top-level `schema_version` is `llm-sidecar-result.v1`
- `summary.file_count`, `summary.succeeded_count`, `summary.failed_count`,
  `summary.skipped_count`, and `summary.finding_count` are present
- each `files[]` entry has `path`, `status`, and either `review` or `error`
- successful `review` entries include provider/model metadata plus findings
- failed entries expose only stable `error_type` and message fields

Useful inspection commands:

```bash
uv run python -m json.tool /tmp/content-review-single.llm.json
uv run python -m json.tool /tmp/content-review-batch-llm/llm-review-manifest.json
```

## Sidecar Markdown Output

The optional LLM Markdown sidecar report is separate from the deterministic
Markdown report.

Check:

- the top-level summary section matches the JSON sidecar summary
- per-file status rows match the JSON sidecar manifest
- failed files show `error_type` and message
- successful files show LLM findings
- the report structure stays on the existing sidecar-report path and does not
  replace the main deterministic report

## Quality Gate Boundary

Quality Gate behavior does not read LLM findings or LLM sidecar failures.

- `--fail-on` still evaluates only deterministic findings
- LLM findings are not merged into `ReviewResult`
- LLM sidecar JSON and Markdown outputs are separate artifacts
- a provider runtime failure does not become a deterministic quality-gate
  failure
- command/config/secret errors can still fail the command with exit code `2`
- `llm-check` does not produce a deterministic quality-gate result at all

## Config File

`--llm-config` accepts a YAML mapping with these fields only:

- `provider`
- `model`
- `api_key_env`
- `base_url`
- `timeout_seconds`
- `retry_attempts`
- `retry_backoff_seconds`
- `min_request_interval_seconds`

Constraints:

- unknown fields are rejected
- secret-like fields such as `api_key`, `secret`, `token`, or `password` are rejected
- the loader reads YAML only; it does not read environment variables
- the loader does not instantiate provider runtimes or make network calls
- priority is `explicit CLI flags > --llm-config file > built-in defaults`
- `llm-check` reuses the same config merge behavior as `review` and `batch`

## Timeout Configuration

`--llm-timeout-seconds` applies only to the LLM provider runtime.

- omit it to use the provider runtime default
- set it to a value greater than `0`
- use a small explicit value during manual debugging if you want quicker
  timeout feedback

## Retry Configuration

`pydanticai` keeps the underlying SDK client at `max_retries=0`.
If you want retries, configure the explicit project-level retry loop instead.

- `--llm-retry-attempts 0` means no retry
- `--llm-retry-attempts 1` means one initial call plus one retry
- `--llm-retry-backoff-seconds 0.0` means no sleep between retries
- `--llm-min-request-interval-seconds 0.0` means no local pacing
- only timeout, network, and rate-limit failures are retryable
- auth, secret, config, model, and response-validation failures are not retryable
- when retryable failures still exceed the configured limit, sidecars record
  `LLMProviderRetryExhaustedError`
- retry backoff sleeps first after a retryable failure; the following pacing
  check then sleeps only any remaining time needed before the next runtime
  call starts
- in batch review, the same reviewer instance is reused across files, so this
  pacing also applies naturally between consecutive files

## OpenAI-compatible Base URL

Use `--llm-base-url` only when the target endpoint is OpenAI-compatible.

Examples:

- hosted proxy endpoint
- self-hosted OpenAI-compatible gateway
- vendor endpoint that exposes the OpenAI chat/completions contract

Do not assume every model endpoint is compatible. If the provider rejects the
endpoint or model, verify the base URL and model format together.

## Troubleshooting

Runtime and validation errors to check:

- `LLMProviderSecretError`: `--llm-api-key-env` is missing, unset, or empty.
- `LLMProviderTimeoutError`: the provider call exceeded the configured or
  runtime default timeout.
- `LLMProviderAuthError`: the API key is invalid or not accepted by the
  provider.
- `LLMProviderNetworkError`: DNS, TCP, TLS, proxy, or connectivity failure.
- `LLMProviderRateLimitError`: the provider rejected the request because of
  rate limiting or quota pressure.
- `LLMProviderRetryExhaustedError`: retryable provider failures exceeded the
  configured retry budget.
- `LLMProviderModelError`: the configured model name or endpoint/model pairing
  is invalid.
- `LLMProviderRuntimeError`: uncategorized provider runtime failure.
- `LLMResponseValidationError`: the provider responded, but the structured
  payload did not match the expected schema.

Troubleshooting steps:

1. Confirm `--llm-provider pydanticai` and `--llm-model` are both present, or
   confirm the same values are available through `--llm-config`.
2. Confirm `--llm-api-key-env` points to a non-empty environment variable.
3. If using `--llm-base-url`, confirm the endpoint is OpenAI-compatible.
4. Use `content-review llm-check` before `review` or `batch` if you only want
   to isolate config, secret, or runtime setup problems.
5. If you hit `LLMProviderTimeoutError`, retry manually with a larger
   `--llm-timeout-seconds` value or a small explicit retry budget.
6. If you hit `LLMProviderRetryExhaustedError`, inspect whether the last
   retryable failure was timeout, network, or rate-limit related before
   increasing retry settings.
7. If you hit frequent rate limits in manual verification, increase
   `--llm-min-request-interval-seconds` before increasing retry volume.
8. If you hit `LLMProviderAuthError`, rotate or replace the secret outside the
   repository.
9. If you hit `LLMProviderModelError`, verify the model string against your
   endpoint contract.
10. If you hit `LLMResponseValidationError`, inspect the sidecar error and keep
   the failing output for local debugging; do not change deterministic review
   expectations based on it.

Real `pydanticai` provider calls must not run in default `pytest` or CI.

## Manual Verification Checklist

1. Confirm the chosen Markdown fixture loads locally before enabling LLM.
2. Confirm the profile fixture loads through the normal profile loader.
3. Export the API key in your shell and keep it out of command history when
   possible.
4. Run the single-file command and inspect sidecar JSON and Markdown outputs.
5. Run the batch command and inspect per-file sidecars plus the manifest.
6. Confirm deterministic output and `--fail-on` behavior are unchanged.
7. Remove temporary output files after verification if they contain sensitive
   content.

## Security Notes

- Never pass a real API key through a plaintext CLI flag.
- Never commit real API keys, copied shell exports, `.env` files, sidecars, or
  logs that include secret values.
- Keep `.env.example` files placeholder-only.
- Prefer local shell exports or a local secret manager over repository files.
- Treat sidecar outputs as content artifacts; they should not contain secrets,
  but they may contain reviewable article text and model-generated findings.

## CI Notes

Real `pydanticai` provider calls must not run in default `pytest` or CI.

- CI should keep using deterministic review commands for gating.
- CI can use `--llm-provider mock` for no-network sidecar coverage if needed.
- CI can use `content-review llm-check --llm-config examples/llm/mock/llm-provider.yml`
  for no-network provider-wiring checks if desired.
- CI should not require a real API key.
- CI should not run `content-review llm-check --runtime` for real providers.
- This repository's automated tests only validate docs, fixtures, and no-network
  fake-runtime coverage for the provider path.
