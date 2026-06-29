# CHANGELOG.md

All notable changes to this project will be documented in this file.

This project follows a staged development process.

---

## Unreleased

## TASK-0067

### Changed

- Updated `src/content_review_engine/llm/pydanticai.py` so
  `PydanticAIReviewer` now exposes `run_semantic_review(request)` that builds
  the shared semantic-review prompt contract, executes a raw text runtime
  call, reuses `parse_llm_semantic_review_output()`, and returns
  `ValidatedLLMSemanticReviewOutput`.
- Updated `src/content_review_engine/llm/errors.py` and
  `src/content_review_engine/llm/__init__.py` to expose
  `LLMSemanticReviewExecutionError` for non-text provider output while
  preserving separate runtime, parse, and validation failures.
- Updated `tests/test_llm_pydanticai_provider.py` and
  `tests/test_llm_provider_usage_docs.py` for shared prompt-builder usage,
  shared output-validator usage, plain/fenced JSON success, parse failure,
  validation failure, provider execution failure, construction/live
  separation, no-env/no-network isolation, and secret non-leakage coverage.
- Updated `docs/LLM_PROVIDER_USAGE.md`, `docs/DATA_MODELS.md`,
  `docs/ARCHITECTURE.md`, and `PROJECT_STATE.md` to document the new
  provider-execution boundary that returns validated semantic output without
  producing `LLMReviewResult` or entering the deterministic review pipeline.

### Not Added

- No `content-review review` or `content-review batch` integration, no new LLM
  CLI switches, no `LLMReviewResult` conversion, no sidecar metadata change,
  no deterministic review change, no `.env` or `os.environ` reads inside this
  semantic-review execution path when tests use pre-resolved secrets, and no
  default-test real network access or required real API key.

## TASK-0066

### Added

- Added `src/content_review_engine/llm/output_validation.py` with a separate
  semantic-review output extraction, JSON parsing, and contract validation
  layer for `llm-semantic-review-output.v1`.
- Added `tests/test_llm_output_validation.py` for pure JSON, fenced JSON,
  empty findings, finding-field validation, stable field-path errors,
  malformed JSON handling, non-leaking error messages, and no-env /
  no-network guarantees.

### Changed

- Updated `src/content_review_engine/llm/models.py` with
  `ValidatedLLMSemanticFinding` and `ValidatedLLMSemanticReviewOutput` as
  dedicated validated output models distinct from `LLMReviewResult`.
- Updated `src/content_review_engine/llm/errors.py` and
  `src/content_review_engine/llm/__init__.py` to expose stable parse and
  validation errors plus public parsing/validation helpers.
- Updated `tests/test_llm_provider_usage_docs.py`,
  `docs/LLM_PROVIDER_USAGE.md`, `docs/DATA_MODELS.md`,
  `docs/ARCHITECTURE.md`, and `PROJECT_STATE.md` to document the output
  validation layer and its separation from provider execution and
  `LLMReviewResult` generation.

### Not Added

- No real provider call, no network access, no `.env` or `os.environ` reads,
  no provider execution wiring, and no `LLMReviewResult` generation from this
  validated output layer.
- No change to `ReviewResult`, `BatchReviewResult`, `LLMReviewResult`,
  sidecar metadata, deterministic review behavior, or `llm-check` behavior.

## TASK-0065

### Added

- Added `src/content_review_engine/llm/prompt_contract.py` with a separate
  `llm-semantic-review-prompt.v1` builder for stable semantic-review system
  and user prompts plus a documented `llm-semantic-review-output.v1` output
  contract.
- Added `tests/test_llm_prompt_contract.py` for JSON-only output rules,
  schema-version coverage, severity and `llm.` rule-id constraints,
  deterministic-finding context injection, secret redaction, and no-env /
  no-network prompt-builder guarantees.

### Changed

- Updated `src/content_review_engine/llm/models.py` so `LLMReviewRequest` now
  carries `review_language` with a default of `zh-CN` plus optional
  deterministic-finding summary lines for prompt construction only.
- Updated `src/content_review_engine/llm/__init__.py` and
  `tests/test_llm_provider_usage_docs.py` to export and verify the new prompt
  contract constants and documentation boundary.
- Updated `docs/LLM_PROVIDER_USAGE.md`, `docs/DATA_MODELS.md`,
  `docs/ARCHITECTURE.md`, and `PROJECT_STATE.md` to document the prompt
  contract, its JSON-only requirements, stable severity enum, `llm.` rule-id
  prefix, and separation from provider execution and validated result models.

### Not Added

- No real provider call, no network access, no `.env` or `os.environ` reads
  in the prompt builder, no output parser or validator, and no
  `LLMReviewResult` generation.
- No change to `ReviewResult`, `BatchReviewResult`, `LLMReviewResult`,
  sidecar metadata, deterministic review behavior, `llm-check` behavior, or
  reserved real provider availability.

## TASK-0064

### Changed

- Updated `src/content_review_engine/cli.py` so `content-review llm-check`
  now exposes an explicit `--live` switch, keeps `--runtime` as a compatible
  alias, renders stable failed live-check output to stderr, and still leaves
  default `llm-check` behavior at `Live call: not run`.
- Updated `src/content_review_engine/llm/smoke_check.py` so config-driven
  `llm-check` now orchestrates secret preflight, construction, and optional
  live execution with stable `Live call: ok` / `Live call: failed` states and
  a non-sensitive failure reason.
- Updated `src/content_review_engine/llm/pydanticai.py` so
  `PydanticAIReviewer` now exposes `run_live_check()` using the already
  resolved in-memory secret plus a minimal smoke prompt separate from normal
  review execution.
- Updated `src/content_review_engine/llm/__init__.py`,
  `tests/test_llm_pydanticai_provider.py`,
  `tests/test_llm_provider_factory.py`, `tests/test_llm_smoke_check.py`,
  `tests/test_cli.py`, and `tests/test_llm_provider_usage_docs.py` for
  explicit live success/failure coverage, factory no-live guarantees,
  non-leaking failure output, and no-network/no-real-key default tests.
- Updated `docs/LLM_PROVIDER_USAGE.md`, `docs/CLI.md`,
  `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, and `PROJECT_STATE.md` to
  document the explicit live-check boundary and confirm that canonical result
  schemas remain unchanged.

### Not Added

- No default live provider call, no plaintext API-key CLI argument, no `.env`
  loading, no provider-factory env reads, and no default-test network access
  or required real API key.
- No change to `ReviewResult`, `BatchReviewResult`, `LLMReviewResult`,
  sidecar metadata, deterministic review behavior, or reserved real provider
  availability.

## TASK-0063

### Changed

- Updated `src/content_review_engine/llm/pydanticai.py` so
  `PydanticAIReviewer` can accept a pre-resolved in-memory secret, reuse that
  secret without resolver/env access during construction, and perform a local
  construction-only agent build separate from live review calls.
- Updated `src/content_review_engine/llm/factory.py` so config-driven
  `create_llm_reviewer(config, secret_value=...)` can construct the real
  `pydanticai` reviewer while keeping factory-side secret resolution out of
  scope and reserved real provider behavior unchanged.
- Updated `src/content_review_engine/llm/smoke_check.py` so config-driven
  `llm-check` now runs secret preflight, local provider construction, and
  explicit `Construction: ok` / `Live call: not run` rendering by default.
- Updated `tests/test_llm_pydanticai_provider.py`,
  `tests/test_llm_provider_factory.py`, `tests/test_llm_smoke_check.py`,
  `tests/test_cli.py`, and `tests/test_llm_provider_usage_docs.py` for
  construction-only `pydanticai` checks, no-env/no-network boundaries,
  non-leaking output, and default no-live-call CLI behavior.
- Updated `docs/LLM_PROVIDER_USAGE.md`, `docs/CLI.md`,
  `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, and `PROJECT_STATE.md` to
  document the new construction boundary and confirm that canonical result
  schemas remain unchanged.

### Not Added

- No plaintext API-key CLI argument, no `.env` loading, no provider-factory
  env reads, no `--live`, no default-test network access, and no required
  real API key.
- No change to `ReviewResult`, `BatchReviewResult`, `LLMReviewResult`,
  sidecar metadata, deterministic review behavior, or reserved real provider
  availability.

## TASK-0062

### Changed

- Updated `src/content_review_engine/llm/smoke_check.py` so config-driven
  `content-review llm-check` now resolves `LLMProviderConfig.api_key_env`
  through `resolve_llm_provider_secret(config, env=None)` and renders the
  secret reference plus a redacted secret state through
  `redact_secret_value()`.
- Updated `src/content_review_engine/llm/smoke_check.py` text rendering to
  report provider, model, `API key env`, redacted `API key`, `Secret`, and
  `Runtime` stages without printing the full secret or the synthetic request.
- Updated `tests/test_llm_smoke_check.py`, `tests/test_cli.py`, and
  `tests/test_llm_provider_usage_docs.py` for resolved/not-required secret
  paths, missing/unset/empty env-var failures, redaction checks, and
  non-leaking stdout/stderr assertions.
- Updated `docs/LLM_PROVIDER_USAGE.md`, `docs/CLI.md`,
  `docs/DATA_MODELS.md`, `docs/ARCHITECTURE.md`, and `PROJECT_STATE.md` to
  document the `llm-check` secret-preflight boundary and output contract.

### Not Added

- No plaintext API-key CLI argument, no `.env` loading, no new real provider
  class, no real SDK integration, and no network-dependent default tests.
- No change to `ReviewResult`, `BatchReviewResult`, `LLMReviewResult`, sidecar
  metadata, deterministic review behavior, or reserved real provider
  availability.

## TASK-0061

### Added

- Added a dedicated secret-resolver contract in
  `src/content_review_engine/llm/secrets.py` with
  `resolve_llm_provider_secret(config, env=None)` for direct `api_key_env`
  lookup plus new secret-resolution error subclasses for missing
  `api_key_env`, unset env vars, and empty env vars.
- Added `tests/test_llm_secret_resolver.py` for fake env mapping resolution,
  process-environment fallback, no-`.env`/no-network boundaries, non-leaking
  error messages, and optional secret redaction helper coverage.

### Changed

- Updated `resolve_llm_api_key()` to reuse the new lower-level resolver while
  keeping `ResolvedLLMSecret` redaction behavior stable for the existing
  PydanticAI adapter boundary.
- Updated `src/content_review_engine/llm/__init__.py`,
  `tests/test_llm_provider_config.py`, `tests/test_llm_provider_factory.py`,
  `tests/test_cli.py`, `tests/test_llm_pydanticai_provider.py`, and
  `tests/test_llm_provider_usage_docs.py` for the new resolver contract and
  safe secret-error messages.
- Updated `docs/LLM_PROVIDER_USAGE.md`, `docs/DATA_MODELS.md`,
  `docs/ARCHITECTURE.md`, `docs/CLI.md`, and `PROJECT_STATE.md` to document
  `api_key_env` as a secret reference, the explicit resolver boundary, and the
  continued absence of plaintext API-key CLI arguments.

### Not Added

- No new real provider class, no change to reserved real provider
  availability, no `.env` loader, no new CLI API-key argument, and no
  external-network dependency.
- No change to `LLMReviewResult`, `ReviewResult`, `BatchReviewResult`, sidecar
  metadata schema, Markdown report schema, or quality-gate behavior.

## TASK-0060

### Added

- Added provider-contract validation helpers in
  `src/content_review_engine/llm/config.py` for provider-name normalization and
  config validation across current test providers, reserved future real
  providers, and unsupported provider names.
- Added `tests/test_llm_provider_config.py` for mock/testmodel validation,
  blank-provider rejection, reserved-provider failures, unsupported-provider
  failures, and no-`.env`/no-network contract coverage.

### Changed

- Updated `src/content_review_engine/llm/config_loader.py` to apply the new
  provider-name validation boundary before constructing `LLMProviderConfig`
  from YAML.
- Updated `src/content_review_engine/llm/factory.py` so reviewer-name creation
  still succeeds for `mock` and `pydantic-ai-testmodel`, while reserved real
  provider names such as `openai` now fail clearly as reserved but not
  implemented.
- Updated `src/content_review_engine/llm/__init__.py`,
  `tests/test_llm_provider_factory.py`, `tests/test_cli.py`, and
  `tests/test_llm_provider_usage_docs.py` for the new validation contract and
  reserved-provider error boundary.
- Updated `docs/LLM_PROVIDER_USAGE.md`, `docs/DATA_MODELS.md`,
  `docs/ARCHITECTURE.md`, `docs/CLI.md`, and `PROJECT_STATE.md` to document
  current test providers, reserved future real provider names, unsupported
  provider handling, and the no-`.env`/no-network validation boundary.

### Not Added

- No direct `openai`, `anthropic`, `gemini`, `deepseek`, `qwen`, or `local`
  reviewer implementation.
- No new real-provider class, no new SDK dependency, no `.env` loading, no
  API-key reads for the new validation helper, and no external-network access.
- No change to `LLMReviewResult`, `ReviewResult`, `BatchReviewResult`, sidecar
  envelope v2 schema, Markdown report behavior, or quality-gate behavior.

## TASK-0059

### Added

- Added top-level `llm_provider` and `llm_provider_source` metadata to
  `LLMSidecarResult` for single-file sidecars, per-file batch sidecars, and
  the batch manifest.

### Changed

- Updated `src/content_review_engine/llm/models.py` and
  `src/content_review_engine/llm/sidecar.py` so the sidecar envelope schema is
  now `llm-sidecar-result.v2` and the provider metadata is validated and
  serialized centrally instead of being assembled in the CLI.
- Updated `src/content_review_engine/cli.py` so sidecar output records whether
  provider selection came from the explicit reviewer-name path or the existing
  default/config-driven path, while keeping user-visible `--llm-provider`
  behavior unchanged.
- Updated `tests/test_llm_sidecar.py`, `tests/test_llm_models.py`,
  `tests/test_cli.py`, and `tests/test_llm_provider_usage_docs.py` for
  explicit-provider metadata, default/config-driven metadata, schema-version
  changes, and deterministic-result isolation.
- Updated `docs/CLI.md`, `docs/LLM_PROVIDER_USAGE.md`,
  `docs/DATA_MODELS.md`, `docs/ARCHITECTURE.md`, and `PROJECT_STATE.md` to
  document the new sidecar envelope metadata and its boundary from canonical
  deterministic outputs.

### Not Added

- No real provider integration, no API-key requirement, no `.env` loading, no
  secret resolver changes, and no external-network test dependency.
- No change to `LLMReviewResult`, deterministic `ReviewResult` or
  `BatchReviewResult`, Markdown report schema, `llm-check` user-visible
  behavior, or quality-gate behavior.

## TASK-0058

### Added

- Added explicit batch sidecar reviewer selection for
  `content-review batch` through `--llm-provider mock` and
  `--llm-provider pydantic-ai-testmodel`.

### Changed

- Updated `src/content_review_engine/cli.py` so explicit batch
  `--llm-provider` uses `create_llm_reviewer()` directly, while omitted
  `--llm-provider` keeps the existing config-driven batch sidecar behavior.
- Updated `tests/test_cli.py`, `tests/test_llm_provider_usage_docs.py`, and
  `tests/test_llm_provider_factory.py` for explicit batch provider selection,
  unsupported-provider errors, no-fallback behavior, and clear
  `--llm-provider`-without-batch-sidecar failures.
- Updated `docs/CLI.md`, `docs/LLM_PROVIDER_USAGE.md`,
  `docs/ARCHITECTURE.md`, and `PROJECT_STATE.md` to document the batch
  sidecar provider selection boundary.

### Not Added

- No real provider integration, no API-key requirement, no `.env` loading, no
  secret resolver changes, and no external-network test dependency.
- No change to default `review`, default `batch`, `llm-check` user-visible
  behavior, sidecar JSON schema, Markdown report structure, deterministic
  `ReviewResult`/`BatchReviewResult`, or quality-gate behavior.

## TASK-0057

### Added

- Added explicit single-file sidecar reviewer selection for
  `content-review review` through `--llm-provider mock` and
  `--llm-provider pydantic-ai-testmodel`.
- Added `tests/test_llm_sidecar.py` coverage confirming the sidecar envelope
  stays stable when the nested review result comes from the TestModel
  reviewer.

### Changed

- Updated `src/content_review_engine/cli.py` so explicit single-file
  `--llm-provider` uses `create_llm_reviewer()` directly, while omitted
  `--llm-provider` keeps the existing config-driven sidecar behavior.
- Updated `tests/test_cli.py` and `tests/test_llm_provider_factory.py` for
  explicit single-file provider selection, unsupported-provider errors,
  no-fallback behavior, and clear `--llm-provider`-without-sidecar failures.
- Updated `docs/CLI.md`, `docs/LLM_PROVIDER_USAGE.md`, `docs/ARCHITECTURE.md`,
  and `PROJECT_STATE.md` to document the single-file sidecar provider
  selection boundary.

### Not Added

- No real provider integration, no API-key requirement, no `.env` loading, no
  secret resolver changes, and no external-network test dependency.
- No change to default `review`, default `batch`, `llm-check` user-visible
  behavior, sidecar JSON schema, Markdown report structure, deterministic
  `ReviewResult`, or quality-gate behavior.

## TASK-0056

### Added

- Added `--provider` to `content-review llm-check` for factory-based reviewer
  selection with `mock` and `pydantic-ai-testmodel`.
- Added `tests/test_llm_smoke_check.py` coverage for `llm-check` reviewer-name
  selection through `create_llm_reviewer()` without API keys or network
  access.

### Changed

- Updated `src/content_review_engine/cli.py` and
  `src/content_review_engine/llm/smoke_check.py` so `llm-check --provider`
  uses `create_llm_reviewer()` directly, keeps default `llm-check` behavior
  unchanged, and fails explicitly for unsupported providers without fallback.
- Updated `tests/test_cli.py` for default `llm-check` behavior,
  `--provider mock`, `--provider pydantic-ai-testmodel`, unsupported-provider
  failures, and no-config-fallback assertions.
- Updated `docs/CLI.md`, `docs/LLM_PROVIDER_USAGE.md`, `docs/ARCHITECTURE.md`,
  and `PROJECT_STATE.md` to document the new `llm-check --provider` boundary.

### Not Added

- No real provider integration, no API-key requirement, no `.env` loading, no
  secret resolver changes, and no external-network test dependency.
- No change to `review` or `batch` provider selection, deterministic review
  output, sidecar schema, Markdown report merging, or quality-gate behavior.

## TASK-0055

### Added

- Added reviewer-provider construction in
  `src/content_review_engine/llm/factory.py` for the package-level provider
  names `mock` and `pydantic-ai-testmodel`.
- Added `UnsupportedLLMProviderError` for explicit unsupported-provider
  failures with the unknown provider name and the supported provider list.
- Added `tests/test_llm_provider_factory.py` coverage for supported provider
  creation, `LLMReviewer` protocol compatibility, unsupported-provider
  failures, no-network/no-API-key boundaries, and compatibility with the
  existing config-driven factory path.

### Changed

- Updated `src/content_review_engine/llm/__init__.py` exports for the new
  reviewer-provider factory constants, registry helpers, and error type.
- Updated `docs/LLM_PROVIDER_USAGE.md`, `docs/ARCHITECTURE.md`,
  `docs/DATA_MODELS.md`, and `PROJECT_STATE.md` to document the new package
  factory boundary and confirm that `LLMReviewRequest`, `LLMReviewResult`, and
  `LLMProviderConfig` schemas remain unchanged.
- Kept `llm-check`, `review`, and `batch` default user-visible behavior
  unchanged.
- Kept `LLMProviderConfig`, `LLMReviewRequest`, `LLMReviewResult`, and
  `LLMSidecarResult` schemas unchanged.

### Not Added

- No real provider integration, no API-key requirement, no `.env` loading, no
  secret resolver changes, and no external-network test dependency.
- No new CLI provider-selection behavior, no deterministic review/report
  changes, and no LLM merge into the canonical deterministic outputs.

## TASK-0054

### Added

- Added `src/content_review_engine/llm/pydantic_ai_provider.py` with
  `PydanticAITestModelReviewer`, provider-local request helpers, and a
  `pydantic_ai.models.test.TestModel` execution path that returns
  `LLMReviewResult` without real provider credentials.
- Added `tests/test_llm_pydantic_ai_provider.py` for the TestModel provider's
  success path, serialization, request helper, wrapped runtime failure path,
  response-validation path, and `MockLLMReviewer` stability.

### Changed

- Updated `src/content_review_engine/llm/__init__.py` to export the new
  TestModel reviewer and helper functions.
- Updated `docs/LLM_PROVIDER_USAGE.md`, `docs/ARCHITECTURE.md`,
  `docs/DATA_MODELS.md`, and `PROJECT_STATE.md` to document the package-level
  TestModel provider boundary and its non-CLI, no-secret, no-network testing
  role.
- Kept `LLMProviderConfig` unchanged.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No real OpenAI, Anthropic, Gemini, DeepSeek, or Qwen provider integration.
- No `.env` loading, no API-key requirement, and no external-network test
  dependency.
- No new CLI provider flags, no default `review` or `batch` behavior change,
  no `llm-check` user-visible behavior change, and no LLM merge into
  deterministic review outputs.

## TASK-0053

### Added

- Added `content-review llm-check` as a standalone provider smoke-check
  command for config validation, secret resolution, and optional runtime
  verification.
- Added `src/content_review_engine/llm/smoke_check.py` with a synthetic
  minimal `LLMReviewRequest`, stage-aware smoke-check execution, and stable
  text rendering.
- Added `tests/test_llm_smoke_check.py` for focused smoke-check coverage
  without real API keys or real network access.

### Changed

- Updated `src/content_review_engine/cli.py` so `llm-check` reuses the
  existing `--llm-config` loader and CLI override precedence from TASK-0052,
  while keeping `review` and `batch` behavior unchanged.
- Updated `tests/test_cli.py` and `tests/test_llm_provider_usage_docs.py` for
  the new command, `--runtime`, config-file errors, override precedence,
  output-safety checks, and docs coverage.
- Updated `docs/LLM_PROVIDER_USAGE.md`, `docs/CLI.md`, `docs/CI.md`,
  `docs/ARCHITECTURE.md`, and `PROJECT_STATE.md` to document the new command,
  stage boundaries, CI limitations, and manual-runtime usage guidance.
- Kept `ReviewProfile` schema unchanged.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No new provider, no provider fallback, no multi-model fallback, no
  streaming, no batch concurrency, no rate-limit queue, and no
  `--fail-on-llm`.
- No change to PydanticAI runtime call behavior, retry behavior, timeout
  behavior, request pacing behavior, sidecar/report schemas, or deterministic
  review behavior.
- No real API-key dependency, no real-network default tests, and no CI real
  provider runtime smoke checks.

## TASK-0052

### Added

- Added `src/content_review_engine/llm/config_loader.py` with YAML-only
  `load_llm_provider_config_file()` validation for file existence, YAML
  parsing, top-level mapping shape, unknown fields, secret-like fields, and
  existing `LLMProviderConfig` numeric constraints.
- Added `merge_llm_provider_config()` so explicit CLI values can override
  loaded config-file values without mutating provider runtime behavior.
- Added committed example config files at
  `examples/llm/pydanticai/llm-provider.yml` and
  `examples/llm/mock/llm-provider.yml`.
- Added `tests/test_llm_config_loader.py` for focused config-loader coverage.

### Changed

- Updated `src/content_review_engine/cli.py` so `review` and `batch` accept
  `--llm-config`, load `LLMProviderConfig` from YAML only when LLM sidecar
  review is enabled, and keep deterministic review unchanged when LLM is
  disabled.
- Updated CLI argument defaults for retry, retry backoff, and minimum request
  interval so parser defaults no longer overwrite config-file values.
- Updated `tests/test_cli.py`, `tests/test_llm_config.py`, and
  `tests/test_llm_provider_usage_docs.py` for config loading, CLI override
  precedence, deterministic-review isolation, fake-runtime wiring, example
  config fixtures, and secret-safety checks.
- Updated `src/content_review_engine/llm/config.py` and
  `src/content_review_engine/llm/__init__.py` to expose the config merge and
  file-loading helpers while keeping the provider set unchanged.
- Updated `docs/LLM_PROVIDER_USAGE.md`, `docs/CLI.md`, `docs/CI.md`,
  `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, and `PROJECT_STATE.md` to
  document config-file support, allowed fields, forbidden fields, override
  priority, and the continued separation from deterministic review and
  quality-gate behavior.
- Kept `ReviewProfile` schema unchanged.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No new provider, no provider fallback, no multi-model fallback, no
  streaming, no batch concurrency, no rate-limit queue, and no
  `--fail-on-llm`.
- No change to PydanticAI runtime call behavior, retry behavior, timeout
  behavior, request pacing behavior, sidecar/report schemas, or deterministic
  quality-gate logic.
- No real API-key test dependency, no real-network tests, and no CI real
  provider calls.

## TASK-0051

### Added

- Added `min_request_interval_seconds` to `LLMProviderConfig`, with
  validation coverage in `tests/test_llm_config.py`.
- Added `tests/test_llm_rate_limit.py` for focused request-pacing coverage
  using fake monotonic clocks and fake sleep without real network access or
  real API keys.

### Changed

- Updated `src/content_review_engine/cli.py` so `review` and `batch` accept
  `--llm-min-request-interval-seconds`, validate it, and pass it into shared
  provider config without affecting deterministic review when LLM sidecar
  review is disabled.
- Updated `src/content_review_engine/llm/pydanticai.py` so the `pydanticai`
  runtime applies instance-local request pacing before every real runtime
  call, including retry attempts, tracks the last runtime call start time,
  and exposes injectable monotonic clock and sleep functions for tests.
- Updated `tests/test_llm_pydanticai_provider.py`, `tests/test_llm_retry.py`,
  and `tests/test_cli.py` for min-interval config propagation, mock-provider
  stability, batch reviewer reuse pacing, and continued deterministic
  quality-gate isolation.
- Updated `docs/LLM_PROVIDER_USAGE.md`, `docs/CLI.md`, `docs/CI.md`,
  `docs/ARCHITECTURE.md`, and `docs/DATA_MODELS.md` to document local request
  pacing, batch reviewer reuse, and the relationship between retry backoff
  and pacing.
- Updated `PROJECT_STATE.md` to record TASK-0051 completion.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No rate-limit queue, token bucket, leaky bucket, cross-process rate
  limiter, batch concurrency, streaming, fallback model/provider behavior, or
  `--fail-on-llm`.
- No LLM merge into deterministic review outputs or quality-gate logic.
- No real-network tests, real API-key test dependency, or CI real-provider
  smoke tests.

## TASK-0050

### Added

- Added `retry_attempts` and `retry_backoff_seconds` to
  `LLMProviderConfig`, with validation coverage in `tests/test_llm_config.py`.
- Added `LLMProviderRetryExhaustedError` plus retry helpers in
  `src/content_review_engine/llm/pydanticai_errors.py` for explicit
  retryable/non-retryable classification.
- Added `tests/test_llm_retry.py` for focused retry boundary coverage without
  real network access or real API keys.

### Changed

- Updated `src/content_review_engine/cli.py` so `review` and `batch` accept
  `--llm-retry-attempts` and `--llm-retry-backoff-seconds`, validate them,
  and pass them into shared provider config without affecting deterministic
  review when LLM sidecar review is disabled.
- Updated `src/content_review_engine/llm/pydanticai.py` so the `pydanticai`
  runtime keeps the underlying OpenAI-compatible SDK client at
  `max_retries=0`, applies an explicit retry loop only for timeout, network,
  and rate-limit failures, exposes injectable sleep for tests, and raises
  stable `LLMProviderRetryExhaustedError` when retryable failures exceed the
  configured retry budget.
- Updated `src/content_review_engine/llm/errors.py` and
  `src/content_review_engine/llm/__init__.py` to expose the new retry
  exhausted error type and retry helpers.
- Updated `tests/test_llm_pydanticai_provider.py`,
  `tests/test_llm_pydanticai_errors.py`, `tests/test_llm_provider.py`, and
  `tests/test_cli.py` for retry config propagation, timeout/network/rate-limit
  retry success, retry exhaustion, non-retryable auth/model/validation/
  secret/config failures, sidecar retry-exhausted recording, and continued
  deterministic quality-gate isolation.
- Updated `docs/LLM_PROVIDER_USAGE.md`, `docs/CLI.md`, `docs/CI.md`,
  `docs/ARCHITECTURE.md`, and `docs/DATA_MODELS.md` to document explicit
  retry config, retryable error boundaries, and the continued
  non-impact on deterministic quality gates.
- Updated `PROJECT_STATE.md` to record TASK-0050 completion.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No rate-limit queue, batch concurrency, streaming, fallback
  model/provider behavior, or `--fail-on-llm`.
- No LLM merge into deterministic review outputs or quality-gate logic.
- No real-network tests, real API-key test dependency, or CI real-provider
  smoke tests.

## TASK-0049

### Added

- Added `docs/LLM_PROVIDER_USAGE.md` with explicit `pydanticai` provider
  usage guidance, manual verification commands, sidecar inspection steps,
  troubleshooting coverage for runtime error types, secret safety notes, and
  CI boundaries.
- Added committed manual verification fixtures under
  `examples/llm/pydanticai/`, including single-file Markdown input, batch
  Markdown samples, a loadable profile fixture, and placeholder-only
  `.env.example`.
- Added `tests/test_llm_provider_usage_docs.py` to verify fixture presence,
  placeholder-only environment examples, required usage-guide coverage, local
  profile/Markdown loader compatibility, and no obvious real API key leakage.

### Changed

- Updated `docs/CLI.md` to link the new provider usage guide and clarify that
  real `pydanticai` execution is for explicit manual verification while
  deterministic quality-gate behavior stays unchanged.
- Updated `docs/CI.md` to document that default CI should not run real
  provider calls and should not require real API keys.
- Updated `docs/ARCHITECTURE.md` to document the committed manual-verification
  fixture boundary for the real provider path.
- Updated `PROJECT_STATE.md` to record TASK-0049 completion.
- Kept provider runtime behavior unchanged.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No retry, rate-limit queue, batch concurrency, streaming, fallback
  model/provider behavior, or `--fail-on-llm`.
- No LLM merge into deterministic review outputs or quality-gate logic.
- No real-network tests, real API-key test dependency, or CI real-provider
  smoke tests.

## TASK-0048

### Added

- Added `timeout_seconds` to `LLMProviderConfig` plus validation coverage in
  `tests/test_llm_config.py`.
- Added `src/content_review_engine/llm/pydanticai_errors.py` with stable
  PydanticAI runtime error classification for timeout, auth, network,
  rate-limit, model, and unknown runtime failures.
- Added `tests/test_llm_pydanticai_errors.py` for stable error-classification
  coverage without real network or real API keys.

### Changed

- Updated `src/content_review_engine/cli.py` so `review` and `batch` accept
  `--llm-timeout-seconds`, validate that it is greater than `0`, and pass it
  into shared provider config without affecting deterministic review when LLM
  sidecar review is disabled.
- Updated `src/content_review_engine/llm/pydanticai.py` so the `pydanticai`
  runtime passes optional timeout config into the underlying OpenAI-compatible
  client and maps runtime failures into stable provider runtime error
  subclasses while preserving `LLMResponseValidationError` for structured
  response validation only.
- Updated `src/content_review_engine/llm/errors.py` and
  `src/content_review_engine/llm/__init__.py` to expose stable provider
  runtime error subclasses for timeout, auth, network, rate-limit, model, and
  unknown runtime failures.
- Updated `tests/test_llm_pydanticai_provider.py`, `tests/test_llm_provider.py`,
  and `tests/test_cli.py` for timeout propagation, runtime classification,
  partial batch timeout failure recording, and continued deterministic quality
  gate isolation.
- Updated `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, `docs/CLI.md`, and
  `docs/CI.md` to document timeout config and runtime error classification.
- Updated `PROJECT_STATE.md` to record TASK-0048 completion.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No retry, rate-limit queue, streaming, batch concurrency, multi-model
  fallback, provider fallback, or `--fail-on-llm`.
- No LLM merge into deterministic review results, report structure changes, or
  quality-gate changes.
- No real-network tests or real API-key test dependency.

## TASK-0047

### Added

- Added real `pydanticai` runtime execution in
  `src/content_review_engine/llm/pydanticai.py` through the existing provider
  interface, using the already-stabilized prompt payload, structured response
  schema, and response mapper.
- Added runtime-focused `tests/test_llm_pydanticai_provider.py` coverage for
  empty findings, single finding, multiple findings, summary mapping, invalid
  structured responses, runtime exception normalization, no fallback to
  `mock`, missing-model config errors, no-network fake runtime execution, and
  secret redaction.
- Added CLI coverage in `tests/test_cli.py` for fake-runtime `pydanticai`
  single-file sidecar JSON + Markdown output and batch sidecar JSON +
  Markdown output without real network access.

### Changed

- Updated `src/content_review_engine/llm/pydanticai.py` so
  `PydanticAIReviewer.review()` now resolves secrets, builds a structured
  runtime agent with the configured model and optional base URL, executes the
  PydanticAI runtime, normalizes runtime failures into `LLMProviderError`, and
  preserves `LLMResponseValidationError` for invalid structured responses.
- Updated `src/content_review_engine/cli.py` so
  `--enable-llm --llm-provider pydanticai` still performs secret preflight but
  no longer returns `LLMProviderNotImplementedError` when the secret exists.
- Updated `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, `docs/CLI.md`, and
  `docs/CI.md` to document the runnable `pydanticai` provider boundary and
  unchanged deterministic quality-gate semantics.
- Updated `PROJECT_STATE.md` to record TASK-0047 completion.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No real-network tests or real API-key test dependency.
- No retry, timeout, rate limit, streaming, batch concurrency, or multi-model
  fallback behavior.
- No LLM merge into deterministic review results or quality-gate evaluation.

## TASK-0046

### Added

- Added `src/content_review_engine/llm/pydanticai_mapping.py` with
  `PydanticAIReviewRequestPayload`, stable prompt-building helpers,
  structured response models, response validation, and response-to-
  `LLMReviewResult` conversion for the reserved `pydanticai` boundary.
- Added `tests/test_llm_pydanticai_mapping.py` covering prompt content,
  structured output requirements, metadata secret redaction, empty finding
  mapping, single and multiple finding mapping, summary mapping, invalid
  severity, empty `rule_id`, empty `message`, missing `findings`,
  non-list `findings`, `None` responses, and non-leaking validation errors.

### Changed

- Updated `src/content_review_engine/llm/pydanticai.py` so the future
  skeleton now holds a `PydanticAIReviewMapper`, can build a stable
  request payload from `LLMReviewRequest`, and still stops at the same
  not-implemented boundary before any real provider execution.
- Updated `src/content_review_engine/llm/__init__.py` to export the new
  PydanticAI mapping components.
- Updated `tests/test_llm_pydanticai_provider.py` so the future skeleton also
  asserts prompt payload construction in addition to the existing secret,
  not-implemented, and no-network boundaries.
- Updated `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, `docs/CLI.md`, and
  `docs/CI.md` to document the new mapping contract while keeping CLI/runtime
  behavior unchanged.
- Updated `PROJECT_STATE.md` to record TASK-0046 completion.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No real PydanticAI runtime review execution or network requests.
- No fallback from `pydanticai` to `mock`.
- No CLI path that lets `pydanticai` produce a real `LLMReviewResult`.

## TASK-0045

### Added

- Reintroduced the minimal `pydantic-ai-slim[openai]` dependency in
  `pyproject.toml` and refreshed `uv.lock` for the future `pydanticai`
  provider boundary.
- Added `src/content_review_engine/llm/secrets.py` with
  `ResolvedLLMSecret` and safe `resolve_llm_api_key(config)` handling.
- Added `LLMProviderSecretError` plus dedicated
  `tests/test_llm_secrets.py` coverage for successful resolution, missing
  `api_key_env`, unset env vars, empty env vars, and secret redaction.

### Changed

- Updated `src/content_review_engine/llm/pydanticai.py` so the future skeleton
  now stores `LLMProviderConfig`, imports the minimal PydanticAI dependency,
  resolves secret availability safely, and still raises
  `LLMProviderNotImplementedError` before any real review call.
- Updated `src/content_review_engine/llm/factory.py` so
  `provider=\"pydanticai\"` now constructs the explicit future skeleton
  instead of failing inside the factory boundary.
- Updated `src/content_review_engine/cli.py` so enabling `pydanticai`
  performs secret preflight, returns structured secret errors for missing or
  invalid env configuration, and returns a clear not-implemented error when
  the secret exists.
- Updated `tests/test_llm_config.py`, `tests/test_llm_provider.py`,
  `tests/test_llm_provider_factory.py`, `tests/test_llm_pydanticai_provider.py`,
  and `tests/test_cli.py` for the new dependency + secret boundary.
- Updated `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, `docs/CLI.md`, and
  `docs/CI.md` to document the secret-resolution boundary and continued
  non-runnable `pydanticai` state.
- Updated `PROJECT_STATE.md` to record TASK-0045 completion.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No real PydanticAI review execution, prompt templates, response parsing, or
  network requests.
- No fallback from `pydanticai` to `mock`.
- No secret serialization into config dumps, sidecars, reports, logs, or
  error messages.

## TASK-0044

### Changed

- Replaced the old runnable-looking `src/content_review_engine/llm/pydanticai.py`
  implementation with an explicit future skeleton that only raises
  `LLMProviderNotImplementedError`.
- Removed the historical `pydantic-ai-slim[openai]` dependency from
  `pyproject.toml` and refreshed `uv.lock` because the reserved `pydanticai`
  path is no longer a runnable SDK-backed adapter.
- Updated `src/content_review_engine/llm/factory.py` so the reserved
  `pydanticai` path reuses the same skeleton not-implemented boundary instead
  of implying a hidden runnable adapter.
- Updated `src/content_review_engine/llm/__init__.py` to stop exporting the old
  `PydanticAIOpenAIReviewer` symbols and export only the reserved skeleton
  boundary.
- Updated `tests/test_llm_provider_factory.py` to cover mock success,
  reserved-provider not-implemented behavior, unknown-provider config errors,
  no fallback to `mock`, no required PydanticAI SDK import, and no network
  calls.
- Rewrote `tests/test_llm_pydanticai_provider.py` so it only asserts explicit
  skeleton semantics and no longer implies a runnable real provider.
- Updated `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, `docs/CLI.md`, and
  `docs/CI.md` to document that only `mock` is runnable today and
  `pydanticai` is recognized but not implemented.
- Updated `PROJECT_STATE.md` to record TASK-0044 completion.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No real PydanticAI SDK integration or imports.
- No real network requests, API-key reads, or secret resolution.
- No runnable `pydanticai` provider, no fallback to `mock`, and no LLM merge
  into deterministic review results.

## TASK-0043

### Added

- Added `src/content_review_engine/llm/config.py` with `LLMProviderConfig`,
  provider-name validation, and config-loading helpers.
- Added `src/content_review_engine/llm/factory.py` with a small provider
  registry and `create_llm_reviewer(config)`.
- Added `LLMProviderConfigError` and `LLMProviderNotImplementedError`.
- Added `tests/test_llm_config.py` and `tests/test_llm_provider_factory.py`.

### Changed

- Updated `src/content_review_engine/cli.py` so LLM sidecar review now builds
  provider config and reviewer instances through the shared LLM factory.
- Updated the CLI contract so `mock` remains the default and only runnable
  provider, while reserved `pydanticai` returns a clear not-implemented
  error.
- Updated the CLI so provider config flags can be parsed without
  `--enable-llm` and do not affect deterministic review unless LLM sidecar
  review is explicitly enabled.
- Updated `tests/test_cli.py` to cover default mock config, mock factory
  creation, config-only flags, reserved-provider errors, unknown-provider
  errors, and continued quality-gate isolation.
- Updated `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, `docs/CLI.md`, and
  `docs/CI.md` to document the provider configuration boundary.
- Updated `PROJECT_STATE.md` to record TASK-0043 completion.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No real OpenAI, Anthropic, or PydanticAI SDK execution.
- No real network requests or API-key secret resolution.
- No LLM merge into `ReviewResult` or quality-gate evaluation.
- No API, MCP, GUI, retry, timeout, rate limiting, or other real provider
  runtime behavior.

## TASK-0042

### Added

- Added `src/content_review_engine/reports/llm_markdown.py` with a stable
  standalone Markdown renderer for `LLMSidecarResult`.
- Added optional `--llm-markdown-output` to `content-review review` and
  `content-review batch`.
- Added `tests/test_llm_markdown_report.py` covering single-file success,
  empty findings, failed entries, batch success, partial failure, all failed,
  skipped entries, summary output, and Markdown table escaping.
- Added CLI tests covering single-file and batch LLM sidecar Markdown report
  output, argument validation, deterministic Markdown isolation, and quality
  gate isolation.

### Changed

- Updated `src/content_review_engine/cli.py` so single-file and batch LLM
  sidecar flows can write a separate Markdown report derived from the same
  `LLMSidecarResult` data.
- Updated batch manifest generation to retain nested successful `review`
  payloads so `llm-review-manifest.json` can be rendered directly into a
  human-readable Markdown sidecar report.
- Updated `docs/CLI.md`, `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, and
  `docs/CI.md` to document the standalone LLM sidecar Markdown report path and
  its continued separation from deterministic quality gates.
- Updated `PROJECT_STATE.md` to record TASK-0042 completion.
- Kept the canonical deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No real OpenAI, Anthropic, or new provider integration.
- No new external LLM SDK dependency.
- No LLM merge into `ReviewResult` or deterministic Markdown report sections.
- No quality-gate counting of LLM findings, LLM sidecar failures, or LLM
  sidecar Markdown reports.
- No API, MCP, GUI, streaming, retry policy, cache, token accounting, cost
  tracking, telemetry, or tracing integration.

## TASK-0041

### Added

- Added `LLMSidecarResult`, `LLMSidecarSummary`, per-file sidecar status, and
  structured `error_type` / `message` output for CLI LLM sidecars.
- Added `llm-review-manifest.json` under batch `--llm-output-dir` to record
  aggregate sidecar counts and per-file status for partial-success runs.
- Added tests covering sidecar summary serialization, failed-entry
  serialization, single-file failed sidecars, batch partial failure, and
  quality-gate isolation.

### Changed

- Updated `src/content_review_engine/cli.py` so single-file and batch LLM
  sidecars write `llm-sidecar-result.v1` envelopes instead of raw top-level
  `LLMReviewResult` payloads.
- Updated batch LLM sidecar generation to continue after per-file LLM review
  failures and serialize them as `status = failed` entries.
- Updated `docs/CLI.md`, `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, and
  `docs/CI.md` to document sidecar summary fields, per-file status/error
  fields, partial success behavior, and deterministic quality-gate isolation.
- Updated `PROJECT_STATE.md` to record TASK-0041 completion.
- Kept the canonical deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.

### Not Added

- No real OpenAI, Anthropic, or new provider integration.
- No new external LLM SDK dependency.
- No LLM merge into `ReviewResult` or `BatchReviewResult`.
- No quality-gate counting of LLM findings or LLM sidecar failures.
- No API, MCP, GUI, streaming, retry policy, cache, token accounting, cost
  tracking, telemetry, or tracing integration.

## TASK-0040

### Added

- Added `--enable-llm` support to `content-review batch`.
- Added batch `--llm-output-dir` for writing per-file `LLMReviewResult` JSON
  sidecars.
- Added batch `--llm-provider`, `--llm-model`, `--llm-api-key-env`, and
  optional `--llm-base-url`.
- Added batch CLI tests covering mock sidecar output, recursive relative path
  preservation, stable LLM schema version, default empty mock findings,
  invalid flag combinations, unsupported providers, fake
  `pydanticai-openai` success, quality-gate isolation, and friendly sidecar
  write failures.

### Changed

- Updated `src/content_review_engine/cli.py` so batch review can reuse the
  existing `LLMReviewRunner`, `LLMReviewRequest`, provider construction, and
  `llm_review_result_to_json` helper for separate per-file sidecars.
- Updated `docs/CLI.md` to document batch LLM sidecar usage, argument rules,
  output path behavior, and batch isolation guarantees.
- Updated `docs/ARCHITECTURE.md` to describe the batch
  `BatchReviewResult + per-file LLM sidecar` data flow.
- Updated `docs/DATA_MODELS.md` to clarify that batch LLM output remains one
  independent `LLMReviewResult` sidecar per reviewed file.
- Updated `PROJECT_STATE.md` to record TASK-0040 completion.
- Kept the canonical deterministic batch JSON schema unchanged.
- Kept batch Markdown report structure unchanged.
- Kept deterministic batch summary counts, rule counts, and finding order
  unchanged.
- Kept quality-gate semantics unchanged.
- Kept single-file review behavior unchanged.

### Not Added

- No `llm_review` field in batch JSON output.
- No batch LLM section in Markdown reports.
- No batch aggregate LLM report.
- No LLM findings in deterministic batch summary counts or quality gates.
- No API, MCP, or GUI behavior.
- No streaming, retry policy, cache, token accounting, cost tracking,
  telemetry, or tracing integration.

## TASK-0039

### Added

- Added `--include-llm-report` to the single-file `content-review review`
  command for explicitly appending an LLM section to `--format markdown`
  output.
- Added optional LLM Markdown section rendering with `## LLM Review`,
  schema-version display, LLM severity counts, findings, and detailed LLM
  finding output.
- Added Markdown report tests covering backward compatibility, empty and
  populated LLM sections, Markdown escaping, and deterministic-count
  isolation.
- Added CLI tests covering default Markdown stability, opt-in LLM report
  rendering, invalid `--include-llm-report` combinations, sidecar retention,
  JSON isolation, and quality-gate isolation.

### Changed

- Updated `src/content_review_engine/reports/markdown.py` so
  `render_markdown_report` accepts an optional `LLMReviewResult` input while
  preserving identical output when no LLM result is passed.
- Updated `src/content_review_engine/cli.py` to validate
  `--include-llm-report`, reuse the same LLM run for both Markdown rendering
  and the required sidecar JSON, and keep batch behavior unchanged.
- Updated `docs/CLI.md` to document `--include-llm-report`, its constraints,
  and the continued requirement for `--llm-output`.
- Updated `docs/ARCHITECTURE.md` to describe the presentation-only optional
  LLM Markdown integration boundary.
- Updated `docs/DATA_MODELS.md` to clarify that `LLMReviewResult` can be an
  optional Markdown report input without changing `ReviewResult`.
- Updated `PROJECT_STATE.md` to record TASK-0039 completion.
- Kept the canonical deterministic review JSON schema unchanged.
- Kept deterministic Markdown summary counts, rule counts, and finding order
  unchanged.
- Kept quality-gate semantics unchanged.
- Kept batch review behavior unchanged.

### Not Added

- No `llm_review` field in the main review JSON output.
- No LLM findings in deterministic quality gates, severity counts, or rule
  counts.
- No batch LLM report integration.
- No API, MCP, or GUI behavior.
- No streaming, retry policy, cache, token accounting, cost tracking,
  telemetry, or tracing integration.

## TASK-0038

### Added

- Added `pydantic-ai-slim[openai]` as the minimal PydanticAI OpenAI-compatible
  provider dependency.
- Added `src/content_review_engine/llm/pydanticai.py` with
  `PydanticAIOpenAIReviewer`, which implements `LLMReviewer` and converts
  structured provider output into `LLMReviewResult`.
- Added `tests/test_llm_pydanticai_provider.py` covering provider protocol
  compatibility, empty and populated structured output mapping, schema-version
  stability, provider failure mapping, validation failure mapping, and API-key
  non-leakage.
- Added CLI support for `--llm-provider pydanticai-openai`,
  `--llm-model`, `--llm-api-key-env`, and optional `--llm-base-url` on the
  single-file `review` command.
- Added CLI tests covering the new provider flags, missing-model failure,
  missing-API-key-env failure, mock compatibility, fake-provider success path,
  sidecar creation, and main JSON isolation from LLM data.

### Changed

- Updated `src/content_review_engine/cli.py` to keep the existing sidecar-only
  LLM flow while allowing either `MockLLMReviewer` or
  `PydanticAIOpenAIReviewer`.
- Updated `src/content_review_engine/llm/__init__.py` to export the new
  provider symbols.
- Updated `docs/CLI.md` to document `pydanticai-openai` usage, environment
  variable API-key loading, and optional OpenAI-compatible `base_url`
  configuration.
- Updated `docs/ARCHITECTURE.md` to place PydanticAI strictly inside the LLM
  provider layer and keep the deterministic review pipeline unchanged.
- Updated `docs/DATA_MODELS.md` to document the conversion of provider output
  into the existing `LLMReviewResult` sidecar model.
- Updated `PROJECT_STATE.md` to record TASK-0038 completion.
- Kept the canonical deterministic review JSON schema unchanged.
- Kept the Markdown report structure unchanged.
- Kept quality-gate semantics unchanged.
- Kept batch review behavior unchanged.

### Not Added

- No LLM merge into the current `ReviewResult`.
- No LLM section in the current Markdown report.
- No quality-gate counting of LLM findings.
- No batch LLM review.
- No API, MCP, or GUI behavior.
- No streaming, retry policy, cache, token accounting, cost tracking,
  telemetry, or tracing integration.

## TASK-0037

### Added

- Added experimental mock-only LLM plumbing to the single-file
  `content-review review` command via `--enable-llm`.
- Added `--llm-output` for writing a separate `LLMReviewResult` JSON sidecar.
- Added optional `--llm-provider mock` support, with `mock` as the only
  currently accepted provider.
- Added CLI tests covering sidecar generation, stable LLM schema version,
  default empty mock findings, request construction, and invalid argument
  combinations.

### Changed

- Updated `src/content_review_engine/cli.py` to reuse
  `LLMReviewRequest`, `LLMReviewRunner`, `MockLLMReviewer`, and
  `llm_review_result_to_json` when LLM review is explicitly enabled.
- Updated `docs/CLI.md` to document the experimental mock-only LLM sidecar
  workflow and argument rules.
- Updated `docs/ARCHITECTURE.md` to document the
  `CLI -> LLMReviewRunner -> MockLLMReviewer -> LLMReviewResult sidecar`
  data flow.
- Updated `docs/DATA_MODELS.md` to clarify that `LLMReviewResult` JSON stays
  separate from the canonical deterministic `ReviewResult` JSON.
- Updated `PROJECT_STATE.md` to record TASK-0037 completion.
- Kept default CLI behavior unchanged.
- Kept deterministic rule behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept current deterministic review JSON output schema unchanged.
- Kept batch review behavior unchanged.

### Not Added

- No real provider integration.
- No PydanticAI integration.
- No OpenAI SDK or Anthropic SDK.
- No API-key or environment-variable loading.
- No network requests.
- No merged LLM findings in the current `ReviewResult`.
- No batch LLM review.
- No API, MCP, or GUI behavior.

## TASK-0036

### Added

- Added `src/content_review_engine/llm/runner.py` with a lightweight
  synchronous `LLMReviewRunner` that delegates `LLMReviewRequest` execution to
  an injected `LLMReviewer` and returns `LLMReviewResult`.
- Added `tests/test_llm_runner.py` covering runner invocation, configured mock
  behavior, default empty mock behavior, schema-version stability, and
  provider error propagation.

### Changed

- Updated `src/content_review_engine/llm/__init__.py` to export
  `LLMReviewRunner`.
- Updated `docs/ARCHITECTURE.md` to document the
  `LLMReviewRequest -> LLMReviewRunner -> LLMReviewer -> LLMReviewResult`
  semantic-review flow.
- Updated `docs/DATA_MODELS.md` to document the runner input/output boundary
  and its separation from the deterministic `ReviewResult` schema.
- Updated `PROJECT_STATE.md` to record TASK-0036 completion.
- Kept runtime review behavior unchanged.
- Kept deterministic rule behavior unchanged.
- Kept `regex_rules` matching behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept current review JSON output schema unchanged.

### Not Added

- No real provider integration.
- No PydanticAI integration.
- No OpenAI SDK or Anthropic SDK.
- No CLI, API, MCP, or GUI LLM behavior.
- No merged LLM findings in the current `ReviewResult` output.

## TASK-0035

### Added

- Added `LLMReviewRequest` to `src/content_review_engine/llm/models.py` for
  future provider-facing semantic review input.
- Added `src/content_review_engine/llm/provider.py` with a synchronous
  `LLMReviewer` protocol returning `LLMReviewResult`.
- Added `src/content_review_engine/llm/errors.py` with
  `LLMReviewError`, `LLMProviderError`, and
  `LLMResponseValidationError`.
- Added `src/content_review_engine/llm/mock.py` with a deterministic
  `MockLLMReviewer` that returns either a configured `LLMReviewResult` or an
  empty default result.
- Added `tests/test_llm_provider.py` covering request validation, provider
  protocol compatibility, mock reviewer behavior, serialization, and the error
  hierarchy.

### Changed

- Updated `src/content_review_engine/llm/__init__.py` to export the new public
  LLM provider-boundary types.
- Updated `docs/ARCHITECTURE.md` to document the future
  `LLMReviewRequest -> LLMReviewer -> LLMReviewResult` boundary and the mock
  adapter.
- Updated `docs/DATA_MODELS.md` to document `LLMReviewRequest`,
  `LLMReviewer`, LLM error types, and `MockLLMReviewer`.
- Updated `PROJECT_STATE.md` to record TASK-0035 completion.
- Kept runtime review behavior unchanged.
- Kept deterministic rule behavior unchanged.
- Kept `regex_rules` matching behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept current review JSON output schema unchanged.

### Not Added

- No real provider integration.
- No PydanticAI integration.
- No API keys or environment-variable configuration.
- No prompt templates.
- No CLI, API, MCP, or GUI LLM behavior.
- No merged LLM findings in the current `ReviewResult` output.

## TASK-0034

### Added

- Added `src/content_review_engine/llm/models.py` with future-facing
  `LLMReviewFinding`, `LLMReviewSummary`, and `LLMReviewResult` models.
- Added the stable future LLM result schema version
  `llm-review-result.v1`.
- Added `src/content_review_engine/llm/serialization.py` with explicit LLM
  serialization helpers matching the existing project style.
- Added `tests/test_llm_models.py` covering valid and invalid LLM model data
  and stable serialization behavior.

### Changed

- Updated `docs/ARCHITECTURE.md` to document the future optional LLM review
  layer and its conversion boundary.
- Updated `docs/DATA_MODELS.md` to document the new LLM model types,
  validation rules, and their separation from the current deterministic review
  output.
- Updated `docs/RULES.md` to clarify that future LLM finding IDs should stay
  distinct from deterministic rule execution.
- Updated `PROJECT_STATE.md` to record TASK-0034 completion.
- Kept runtime review behavior unchanged.
- Kept deterministic rule behavior unchanged.
- Kept `regex_rules` matching behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept current review JSON output schema unchanged.

### Not Added

- No LLM provider integration.
- No PydanticAI integration.
- No prompt execution or prompt templates.
- No CLI, API, MCP, or GUI LLM behavior.

## TASK-0033

### Added

- Added structured profile validation issues with `path`, `code`, `message`,
  and optional `suggestion`.
- Added invalid profile fixtures under `tests/fixtures/profiles/invalid/` for
  invalid regex IDs, duplicate regex IDs, invalid regex patterns, invalid
  severities, empty regex messages, invalid `case_sensitive`, and invalid YAML.
- Added `tests/test_profile_validation_errors.py` for structured validation
  issue coverage.

### Changed

- Updated `src/content_review_engine/config/profiles.py` and
  `src/content_review_engine/config/validation.py` so profile loading and
  validation collect readable, actionable issues for common profile mistakes.
- Updated `src/content_review_engine/cli.py` so `content-review profile validate`
  renders issue counts, paths, codes, messages, and suggestions, and `review`
  and `batch` fail cleanly on invalid profiles without tracebacks for normal
  user input errors.
- Updated CLI, profile, quickstart, README, data-model, project-state, and
  changelog documentation for structured profile validation errors.
- Updated existing CLI, profile-loader, regex-rule, and model tests for the
  structured validation issue output.
- Kept runtime review behavior unchanged.
- Kept `regex_rules` matching behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept JSON review output schema unchanged.

### Not Added

- No LLM-based review.
- No PydanticAI integration.
- No API, MCP, or GUI behavior.
- No new rule types.

## TASK-0032

### Added

- Added a runnable demo workspace under `examples/demo/` with:
  - short demo articles for WeChat-style and technical-blog content
  - committed stable demo profiles
  - deterministic `regex_rules`
  - committed single-file Markdown demo reports
  - a demo README with commands for profile validation, single-file review,
    batch review, Markdown report output, JSON output, quality gates, and
    inline suppression
- Added `tests/test_demo_project.py` covering demo file presence, profile
  validation, regex-rule presence, findings, suppression, Markdown reports,
  JSON serialization, batch review, quality gates, and documentation links.

### Changed

- Updated `README.md`, `docs/QUICKSTART.md`, `docs/CLI.md`, and
  `docs/PROFILES.md` to point users to the runnable demo workspace.
- Updated `PROJECT_STATE.md` to record the new end-to-end demo project.
- Kept deterministic rule behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept JSON output schema unchanged.

### Not Added

- No LLM-based review.
- No PydanticAI integration.
- No API, MCP, or GUI behavior.
- No new rule types.
- No compliance guarantees.

## TASK-0031

### Added

- Added five practical built-in example/template profiles:
  `general-publishing`, `wechat-article`, `marketing-copy`,
  `technical-blog`, and `health-content`.
- Added profile-specific `regex_rules` to those templates for placeholders,
  exaggerated claims, guarantee-like wording, pressure tactics, unresolved
  draft markers, treatment guarantees, and self-diagnosis risks.
- Added `tests/test_profile_templates.py` to cover template discovery,
  validation, regex-rule presence, and conservative limitation wording.

### Changed

- Updated `src/content_review_engine/config/templates.py` so the new example
  profiles are discoverable through the existing built-in template registry.
- Updated CLI, profile, quickstart, README, project-state, and changelog
  documentation for the expanded template set and their intended use cases.
- Extended existing example-profile, CLI, quickstart, and serialization tests
  to include the new templates.
- Kept deterministic rule behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept JSON output schema unchanged.

### Not Added

- No LLM-based review.
- No PydanticAI integration.
- No API, MCP, or GUI behavior.
- No compliance guarantees.

## TASK-0030

### Added

- Added optional profile-configured `regex_rules` to `ReviewProfile`.
- Added `RegexRuleConfig` validation for regex rule ID format, regex pattern
  compilation, required message content, optional suggestion normalization,
  and default `case_sensitive: false`.
- Added deterministic regex rule execution in
  `src/content_review_engine/rules/regex_rules.py`.
- Added regex rule tests in `tests/test_regex_rules.py` covering loading,
  validation, execution, suppression, summaries, reports, batch aggregation,
  and quality-gate participation.

### Changed

- Updated the rule runner so configured regex rules execute alongside the
  existing built-in deterministic rules and emit normal `ReviewFinding`
  objects.
- Updated profile validation summaries to include configured regex rule IDs and
  severities.
- Updated `docs/RULES.md`, `docs/PROFILES.md`, `docs/DATA_MODELS.md`,
  `docs/CLI.md`, `docs/ARCHITECTURE.md`, and `PROJECT_STATE.md` to document
  regex rule configuration, validation behavior, suppression, runtime
  participation, registry boundaries, and limitations.
- Kept existing built-in rule behavior unchanged.
- Kept suppression syntax unchanged.
- Kept Markdown report structure unchanged beyond normal inclusion of regex
  findings.
- Kept JSON output shape unchanged beyond normal inclusion of regex findings.
- Kept quality-gate semantics unchanged.

### Not Added

- No LLM-based review.
- No PydanticAI integration.
- No API, MCP, or GUI behavior.
- No cross-line regex matching.
- No compliance guarantees.

## TASK-0029

### Added

- Added documentation coverage in `tests/test_rule_registry_boundaries.py` for
  the metadata-registry versus execution-registry boundary.
- Added concise module docstrings to
  `src/content_review_engine/core/rule_registry.py` and
  `src/content_review_engine/rules/registry.py` so the separation is visible in
  the code.

### Changed

- Updated `docs/ARCHITECTURE.md` to explain the boundary between the
  descriptive rule metadata registry and the deterministic execution registry.
- Updated `docs/RULES.md` to clarify that
  `src/content_review_engine/core/rule_registry.py` is metadata-focused while
  `src/content_review_engine/rules/registry.py` remains execution-focused.
- Updated `docs/DATA_MODELS.md` to state that registry metadata does not change
  the JSON output schema and that future LLM findings should remain compatible
  with the existing finding model or a later compatible extension.
- Updated `docs/PROFILES.md` to clarify that the metadata registry does not
  replace profile configuration or profile parsing.
- Updated `PROJECT_STATE.md` to record the completed boundary documentation
  task.
- Kept runtime rule matching behavior unchanged.
- Kept suppression behavior unchanged.
- Kept CLI behavior unchanged.
- Kept Markdown report format unchanged.
- Kept JSON schema unchanged.
- Kept profile parsing behavior unchanged.
- Kept exit-code behavior unchanged.

### Not Added

- No regex rule support.
- No new review rule types.
- No LLM-based review behavior.
- No merged registry implementation.
- No review-pipeline refactor.

## TASK-0028

### Added

- Added `RuleDefinition` as a small internal rule metadata model.
- Added a centralized deterministic built-in rule registry in
  `src/content_review_engine/core/rule_registry.py`.
- Registered the current built-in rule IDs:
  `forbidden_terms`, `absolute_claims`, `markdown_structure`, and
  `markdown_links_images`.
- Added registry tests covering completeness, uniqueness, deterministic
  ordering, metadata lookup, unknown-rule handling, and metadata presence.

### Changed

- Updated `docs/RULES.md`, `docs/DATA_MODELS.md`, `docs/PROFILES.md`, and
  `PROJECT_STATE.md` to describe the centralized rule metadata registry.
- Kept runtime rule matching behavior unchanged.
- Kept suppression behavior unchanged.
- Kept CLI behavior unchanged.
- Kept Markdown report format unchanged.
- Kept JSON schema unchanged.
- Kept exit-code behavior unchanged.

### Not Added

- No new review rules.
- No new rule types.
- No regex rule support.
- No profile format changes.
- No LLM-based review.

## TASK-0027

### Added

- Added documentation coverage that verifies `docs/RULES.md` is identified as
  the canonical rule system reference.
- Added documentation coverage that verifies `docs/REVIEW_RULES.md` is only a
  compatibility stub pointing to `docs/RULES.md`.

### Changed

- Consolidated legacy rule documentation into `docs/RULES.md` and made its
  canonical status explicit.
- Migrated the remaining useful legacy details into `docs/RULES.md`,
  including the legacy top-level `forbidden_terms` profile input note and the
  current implementation/test path references for built-in rules.
- Replaced `docs/REVIEW_RULES.md` with a short compatibility stub.
- Updated `README.md`, `docs/QUICKSTART.md`, `docs/CLI.md`, `docs/PROFILES.md`,
  and `docs/CI.md` to consistently point readers to `docs/RULES.md` as the
  canonical rule reference.

### Not Added

- No new review rules.
- No rule-matching changes.
- No suppression changes.
- No CLI contract changes.
- No Markdown report structure changes.
- No JSON schema changes.
- No exit-code changes.
- No LLM-based review.

## TASK-0026

### Added

- Added `docs/RULES.md` as a dedicated rule system reference for the current
  deterministic review model.
- Documented the current built-in rule IDs:
  `forbidden_terms`, `absolute_claims`, `markdown_structure`, and
  `markdown_links_images`.
- Documented finding fields, severity levels, severity ordering, quality-gate
  behavior, `--fail-on` examples, rule counts, severity counts, suppression
  comments, batch aggregation behavior, reports, and current limitations.
- Added a documentation test that verifies the rule reference exists and covers
  the durable rule-system concepts.

### Changed

- Updated `README.md`, `docs/QUICKSTART.md`, `docs/CLI.md`, `docs/PROFILES.md`,
  and `docs/CI.md` to link the rule-system reference.
- Kept rule matching behavior, suppression behavior, CLI behavior, Markdown
  report format, JSON schema, and exit code behavior unchanged.

### Not Added

- No new review rules.
- No rule-matching changes.
- No suppression changes.
- No CLI contract changes.
- No JSON schema changes.
- No Markdown report structure changes.
- No exit-code changes.
- No LLM-based review.
- No compliance guarantees.

## TASK-0025

### Added

- Added `docs/QUICKSTART.md` with a command-driven first-run workflow covering
  dependency installation, `profile list`, `profile init`, `profile validate`,
  single-file review, batch review, `--fail-on`, Markdown report output,
  inline suppression, profile customization, exit codes, and CI handoff.
- Added a lightweight quickstart documentation test that verifies the document
  exists and includes the key CLI commands, report output example, suppression
  example, exit codes, doc links, and compliance limitation note.

### Changed

- Updated `docs/CLI.md` to link the quickstart from the main CLI reference.
- Updated `docs/PROFILES.md` and `docs/CI.md` to point readers to the
  quickstart for the end-to-end setup flow.
- Updated `README.md` and `PROJECT_STATE.md` to record the new onboarding
  documentation.
- Kept `profile list`, `profile init`, `profile validate`, `review`, `batch`,
  suppression behavior, `forbidden_terms`, `absolute_claims`, text/JSON/Markdown
  output, and `--fail-on` exit-code rules unchanged.

### Not Added

- No new review rules.
- No LLM review.
- No auto-fix behavior.
- No new CLI commands.
- No new output formats.
- No GitHub PR comments.
- No GitHub annotations.
- No SARIF output.
- No HTML report.
- No PDF report.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0024

### Added

- Added structured Markdown report sections for both `review` and `batch`:
  summary, severity counts, rule counts, findings tables, and detailed
  findings.
- Added quality-gate reporting to Markdown output when `--fail-on` is used,
  including gate status, threshold, and matched-gate count.
- Added deterministic batch Markdown sections for files with findings and
  per-file findings details.
- Added Markdown renderer and CLI tests for quality-gate sections, clear
  no-finding states, and writing report files before exit code `1`.

### Changed

- Improved Markdown empty states to use clear `No findings.` messaging while
  keeping suppressed findings excluded from reports.
- Kept single-file and batch JSON output schemas unchanged.
- Kept existing text output behavior unchanged.
- Kept `profile list`, `profile init`, `profile validate`, `review`, `batch`,
  suppression behavior, `forbidden_terms`, `absolute_claims`, and `--fail-on`
  exit-code rules unchanged.
- Updated `docs/CLI.md`, `docs/CI.md`, and `PROJECT_STATE.md` for the improved
  Markdown report behavior.

### Not Added

- No new review rules.
- No LLM review.
- No auto-fix behavior.
- No HTML report.
- No PDF report.
- No DOCX report.
- No SARIF output.
- No GitHub PR comments.
- No GitHub annotations.
- No GitHub Checks API integration.
- No new JSON schema.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0023

### Added

- Added a copyable GitHub Actions CI example at
  `docs/examples/github-actions/content-review.yml`.
- Added `docs/CI.md` describing profile validation, batch review,
  `--fail-on error`, path customization, CI exit codes, and workflow
  limitations.
- Added lightweight tests to ensure the CI example and CI documentation exist
  and contain the key automation commands.

### Changed

- Updated `docs/CLI.md` with CI-oriented usage, profile validation as a first
  CI step, and exit-code behavior for automation.
- Updated `docs/PROFILES.md` with CI-oriented profile usage, profile path and
  articles path customization guidance, and compliance limitations.
- Kept `profile list`, `profile init`, `profile validate`, `review`, `batch`,
  `--fail-on`, suppression, `forbidden_terms`, and `absolute_claims` behavior
  unchanged.

### Not Added

- No new review rules.
- No LLM review.
- No auto-fix behavior.
- No GitHub PR comments.
- No GitHub annotations.
- No SARIF output.
- No GitHub Checks API integration.
- No Marketplace Action.
- No remote profile loading.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0022

### Added

- Added `content-review profile list [--format text|json]`.
- Added canonical `profile-template-list.v1` JSON output for built-in template
  discovery.
- Added deterministic template descriptions for `general-basic`,
  `wechat-basic`, and `wechat-strict`.
- Added CLI tests for profile-list text output, JSON output, help output, and
  template-registry consistency with generated-profile validation.

### Changed

- Reused the same built-in template registry for both `profile list` and
  `profile init` so the supported template set stays consistent.
- Kept `profile init`, `profile validate`, `review`, `batch`, `--fail-on`,
  suppression, `forbidden_terms`, and `absolute_claims` behavior unchanged.
- Updated CLI, profile, architecture, data model, project state, and
  changelog documentation.

### Not Added

- No new review rules.
- No LLM review.
- No natural-language profile generation.
- No interactive wizard.
- No remote template loading.
- No user-defined template directories.
- No template marketplace.
- No profile aliases for `review` or `batch`.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0021

### Added

- Added `content-review profile init --template <name> --output <path>`.
- Added built-in template support for `general-basic`, `wechat-basic`, and
  `wechat-strict` by reusing the committed example profile YAML files.
- Added CLI tests for successful profile initialization, generated-profile
  validation, unknown templates, overwrite conflicts, `--force` overwrite,
  missing parent directories, and help output.

### Changed

- Kept generated profiles on the existing `load_profile()` validation path so
  initialized YAML files stay compatible with
  `content-review profile validate`.
- Updated CLI and profile documentation with the initialization workflow,
  template list, validation steps, and overwrite behavior.
- Updated project state documentation to record the new command and test
  coverage.

### Not Added

- No new review rules.
- No LLM review.
- No natural-language profile generation.
- No interactive wizard.
- No remote template loading.
- No user-defined template directories.
- No template marketplace.
- No `content-review profile list`.
- No profile aliases for `review` or `batch`.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0020

### Added

- Added built-in example profiles under `profiles/examples/`:
  `general-basic.yaml`, `wechat-basic.yaml`, and `wechat-strict.yaml`.
- Added example-profile tests for profile loading, CLI validation, and review
  integration coverage.
- Added `docs/PROFILES.md` describing profile structure, example profile
  purposes, validation, customization, and usage.

### Changed

- Updated CLI documentation with example-profile validation, review, and batch
  commands.
- Updated project state documentation to record the new example profiles and
  related test coverage.

### Not Added

- No new review rules.
- No LLM review.
- No automatic fixing.
- No profile generation, auto-formatting, or interactive wizard.
- No remote profile loading or runtime profile aliases.
- No `content-review profile list` or `content-review profile init`.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0019

### Added

- Added the `content-review profile validate <profile_path>` CLI command group
  and subcommand.
- Added canonical `profile-validation-result.v1` text and JSON outputs for
  profile validation.
- Added CLI tests for valid profiles, invalid profiles, invalid YAML, unknown
  rules, help output, and JSON output.

### Changed

- Reused the existing profile loader for CLI profile validation instead of
  introducing a second validation pipeline.
- Updated profile loading to report invalid YAML as a command/configuration
  error with a readable message.
- Updated CLI, architecture, data model, project state, and changelog
  documentation.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting or fixing.
- No profile generation, formatting, or wizard flow.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0018

### Added

- Added the deterministic `absolute_claims` rule with rule ID
  `absolute_claims`.
- Added rule-style YAML support for `absolute_claims.terms`,
  `absolute_claims.allow_terms`, and `absolute_claims.severity`.
- Added rule-specific suggestion text for `absolute_claims` findings.
- Added tests for profile loading, rule behavior, registry and runner
  integration, review pipeline integration, batch summaries, CLI output, and
  CLI quality-gate behavior.

### Changed

- Extended `ReviewFinding.severity` to support the canonical quality-gate
  severities `info`, `warning`, `error`, and `critical`.
- Added optional `suggestion` support to `ReviewFinding` and surfaced it in
  text, JSON, and Markdown output when present.
- Registered `absolute_claims` as an opt-in deterministic rule in the default
  registry.
- Updated architecture, data model, rule, CLI, project state, and schema
  documentation.

### Not Added

- No LLM review.
- No semantic claim detection.
- No regex, wildcard, or fuzzy matching.
- No automatic rewriting or fixing.
- No new output formats.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0017

### Added

- Added `allow_terms` support for `forbidden_terms` in rule-style YAML
  configuration.
- Added Markdown inline suppression comments:
  `content-review-disable-line <rule_id>` and
  `content-review-disable-next-line <rule_id>`.
- Added suppression filtering before `ReviewResult` creation so default text,
  JSON, and Markdown outputs only include unsuppressed findings.
- Added tests for allowlist behavior, suppression parsing and filtering, review
  pipeline integration, batch summary aggregation, and CLI quality-gate behavior.

### Changed

- Suppressed findings are excluded from single-file summaries, batch summaries,
  and `--fail-on` quality-gate checks.
- Updated architecture, data model, rule, CLI, project state, and changelog
  documentation.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting.
- No block-level, file-level, reason, or expiration suppression.
- No external allowlist files, regex allowlists, or wildcard allowlists.
- No `.gitignore` support.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0016

### Added

- Added `--fail-on` to `content-review review`.
- Added `--fail-on` to `content-review batch`.
- Added centralized quality-gate helpers with canonical severity ordering:
  `info < warning < error < critical`.
- Added CI-friendly exit-code behavior for quality gates.
- Added unit tests for severity threshold comparison and CLI tests for
  quality-gate exit codes.

### Changed

- Updated CLI command errors to consistently return exit code `2`.
- Preserved existing text, JSON, and Markdown output schemas and behavior.
- Updated `docs/ARCHITECTURE.md`, `docs/CLI.md`, `PROJECT_STATE.md`, and this
  changelog.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting.
- No inline suppression.
- No `.gitignore` support.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.

## TASK-0015

### Added

- Added a minimal `content-review batch` command for deterministic Markdown directory review.
- Added deterministic file discovery helpers with `--recursive` and `--pattern` support.
- Added `BatchReviewSummary` and `BatchReviewResult` core models.
- Added batch JSON serialization helpers and a batch Markdown report renderer.
- Added batch fixtures, batch examples, discovery tests, summary tests, serialization tests, Markdown report tests, and CLI tests.

### Changed

- Reused the existing single-file `review_document()` pipeline for each batch file without duplicating rule logic.
- Preserved the canonical single-file `ReviewResult` contract and existing `content-review review` behavior.
- Updated `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, `docs/CLI.md`, `docs/REPORTS.md`, `docs/TESTING.md`, `docs/schemas/README.md`, `PROJECT_STATE.md`, and this changelog.

### Not Added

- No new review rules.
- No new rule behavior.
- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No Markdown auto-fix.
- No watch mode.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.
- No HTML/PDF report generation.
- No parallel execution.

## TASK-0014

### Added

- Added the deterministic `markdown_links_images` rule.
- Added Markdown fixture coverage for empty link text, empty link target,
  placeholder link target, empty image alt text, empty image target,
  placeholder image target, and fenced code block handling.
- Added `tests/fixtures/profiles/markdown_links_images.yml` and matching
  example files for manual CLI usage.
- Added tests for the new rule, registry and runner integration, review
  pipeline integration, and CLI JSON output.

### Changed

- Extended the rule registry to register `markdown_links_images` as opt-in so
  existing default profiles keep the same behavior.
- Preserved the default forbidden-terms behavior, the markdown_structure
  behavior, and the CLI contract.
- Updated `docs/ARCHITECTURE.md`, `docs/RULES.md`, `docs/REVIEW_RULES.md`,
  `docs/CLI.md`, `docs/TESTING.md`, `PROJECT_STATE.md`, and this changelog.

### Not Added

- No network link checking.
- No HTTP status validation.
- No local file existence checking.
- No image download.
- No image alt text quality scoring.
- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No Markdown auto-fix.
- No batch review.
- No watch mode.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.

## TASK-0013

### Added

- Added the deterministic `markdown_structure` rule.
- Added fixtures for missing H1, multiple H1, heading jumps, empty headings,
  long paragraphs, and fenced code block handling.
- Added `tests/fixtures/profiles/markdown_structure.yml` and matching example
  files for manual CLI usage.
- Added tests for the new rule, registry and runner integration, review
  pipeline integration, and CLI JSON output.

### Changed

- Extended the rule registry to track default-enabled rules so
  `markdown_structure` can be registered without changing the legacy implicit
  review path.
- Preserved the default forbidden-terms behavior and CLI contract.
- Updated `docs/ARCHITECTURE.md`, `docs/RULES.md`, `docs/REVIEW_RULES.md`,
  `docs/CLI.md`, `docs/TESTING.md`, `PROJECT_STATE.md`, and this changelog.

### Not Added

- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No Markdown auto-fix.
- No batch review.
- No watch mode.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.

## TASK-0012

### Added

- Added an internal rule interface, rule registry, and rule runner.
- Added a default rule registry containing the existing forbidden-terms rule.
- Added an optional `enabled_rules` field on `ReviewProfile` for explicit rule selection.
- Added tests for registry registration, duplicate rules, unknown rules, default registry behavior, rule runner behavior, review pipeline integration, and unknown-rule CLI handling.
- Added `docs/RULES.md`.

### Changed

- Updated the review pipeline to execute rules through the rule runner.
- Preserved canonical `ReviewResult` output.
- Preserved existing forbidden-terms behavior.
- Updated `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, `docs/CLI.md`, `PROJECT_STATE.md`, and this changelog.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No batch review.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.

### Added

- Added canonical `ReviewSummary`, `ReviewDocumentMetadata`, and `ReviewProfileMetadata` models.
- Added a canonical `ReviewResult` schema version: `review-result.v1`.
- Added explicit `review_result_to_dict()` and `review_result_to_json()` serialization helpers.
- Added `docs/schemas/review-result.schema.json` and `docs/schemas/README.md`.
- Added tests for `ReviewSummary`, `ReviewResult`, canonical serialization, the review pipeline, CLI JSON output, and Markdown report rendering.
- Added initial core data models:
  - `ReviewIssue`
  - `ReviewResult`
  - `ReviewProfile`
- Added `ReviewFinding` for deterministic rule matches.
- Added `SourceSpan` for source location metadata on review findings.
- Added validation tests for core data models.
- Added data model documentation.
- Added `pydantic` as a project dependency.
- Added `pytest` as a dev dependency for the test run.
- Added Markdown reader helper in `content_review_engine.parser`.
- Added YAML profile loader in `content_review_engine.config`.
- Added `profiles/wechat.yaml` as the initial review profile sample.
- Added tests for Markdown parsing and profile loading.
- Added deterministic forbidden terms rule support.
- Added tests for the forbidden terms rule.
- Added location metadata and context snippets to forbidden term findings.
- Added tests for location calculation, location-aware forbidden term findings, multiple findings, and CLI output.
- Added minimal in-memory review pipeline support.
- Added `review_document()` as the core review pipeline entrypoint.
- Added tests for the review pipeline.
- Added a minimal CLI entrypoint with `content-review review`.
- Added CLI tests for successful reviews, missing files, and help output.
- Added CLI JSON output support for review findings.
- Added `docs/CLI.md`.
- Added a Markdown report renderer in `content_review_engine.reports`.
- Added CLI `--format markdown` support.
- Added CLI `--output` support for writing rendered review output to a file.
- Added tests for the Markdown report renderer, CLI Markdown stdout, CLI Markdown output files, and output write failures.
- Added `docs/REPORTS.md`.
- Added packaging configuration so `uv run content-review` can install and expose the console script.
- Added a console-script smoke test for the packaged `content-review` entrypoint.

### Changed

- Updated the review pipeline to return `ReviewResult` instead of a bare findings list.
- Updated CLI JSON output to use canonical `ReviewResult` serialization.
- Updated Markdown report rendering to consume `ReviewResult`.
- Updated `docs/DATA_MODELS.md`, `docs/CLI.md`, and `docs/REPORTS.md` for the stabilized output contract.
- Updated `PROJECT_STATE.md` for TASK-0011 completion.
- Updated project state for the core data model foundation.
- Configured pytest to resolve the `src/` layout without manual `sys.path` edits.
- Updated architecture docs to describe the input layer.
- Updated architecture docs to include deterministic rules.
- Updated architecture docs to include the review pipeline layer.
- Updated review rule docs to include `forbidden_terms`.
- Extended review profile configuration with `forbidden_terms`.
- Added `pyyaml` as a project dependency.
- Updated architecture docs to include the CLI adapter and its current limits.
- Updated project state for TASK-0006 completion.
- Updated changelog for the CLI task.
- Extended `ReviewFinding` with optional `location` metadata.
- Updated data model documentation for source spans.
- Updated CLI text output to include line, column, matched text, and context when available.
- Updated CLI JSON output to include nested location objects.
- Updated project state for TASK-0007 completion.
- Updated changelog for TASK-0007.
- Updated CLI docs for Markdown report export.
- Updated architecture docs for the report renderer.
- Updated project state for TASK-0008 completion.
- Updated changelog for TASK-0008.
- Updated CLI and testing docs to prefer `uv run content-review`.
- Updated project state for TASK-0010 completion.

### Fixed

- Removed manual `sys.path` mutation from `tests/test_models.py`.

### Removed

- Nothing yet.

## TASK-0009

### Added

- Added Markdown fixture files for clean and forbidden-term review scenarios.
- Added multiline Markdown and code-block fixtures for review-path coverage.
- Added ReviewProfile fixture files for tests.
- Added example Markdown and profile files for manual CLI usage.
- Added testing documentation for fixtures and examples.

### Changed

- Updated selected CLI, review pipeline, and report tests to use committed fixtures where appropriate.
- Updated CLI and report documentation with example-file commands.
- Updated project state for the new fixture and example files.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.
