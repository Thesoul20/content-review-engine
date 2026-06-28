# PROJECT_STATE.md

## Current Phase

M1: Core input layer and minimal review pipeline.

The project currently has Markdown input handling, profile loading, standalone profile validation, deterministic review rules, forbidden-terms allowlists, absolute-claims rule configuration, Markdown inline suppression filtering, a minimal internal rule registry and rule runner, centralized built-in rule metadata, source location metadata on findings, a minimal in-memory review pipeline, a minimal batch CLI adapter, CLI quality-gate exit codes, and committed fixtures/examples for integration-style testing and manual CLI checks.
It now also supports optional profile-configured deterministic `regex_rules`
that validate patterns at profile load time and emit normal findings with
profile-defined rule IDs.
It also now includes a committed end-to-end demo workspace under
`examples/demo/` with small demo articles, stable demo profiles, committed
Markdown reports, and tests that exercise review, batch review, JSON output,
quality gates, and suppression without changing runtime behavior.
Profile validation failures are now also structured with stable issue paths,
codes, readable messages, and optional suggestions for CLI and future adapter
use.

---

## Completed

- Project direction is defined as a Python package-first content review engine.
- Long-term extension targets are identified:
  - CLI
  - Skill
  - MCP
  - FastAPI backend
  - Frontend
- Development will use task-based Agent workflow.
- Repository memory will be stored in project files, not in chat history.
- Initial core data models are in place.
- Markdown reader and YAML profile loading have been implemented.
- The first deterministic review rule has been implemented.
- A minimal review pipeline has been implemented.
- A minimal Markdown report renderer has been implemented.
- The CLI can export Markdown review reports.
- The CLI can export structured Markdown review reports with summaries,
  severity counts, rule counts, detailed findings, batch per-file sections,
  and quality-gate status.
- The project is packaged so `uv run content-review` resolves the console script.
- The CLI supports automation-friendly quality gates with `--fail-on`.
- The `forbidden_terms` rule supports literal `allow_terms` in rule-style YAML configuration.
- The opt-in `absolute_claims` rule supports literal `terms`, optional `allow_terms`, and configurable finding severity in rule-style YAML configuration.
- Markdown inline comments can suppress `forbidden_terms` findings for the current line or next line.
- Markdown inline comments can also suppress `absolute_claims` findings for the current line or next line.
- The CLI can validate a YAML review profile independently through `content-review profile validate`.
- The repository includes built-in example profiles under `profiles/examples/`
  that validate through the existing profile validation command and can be used
  directly with `review` and `batch`.
- The built-in profile template system includes practical real-world
  templates for general publishing, WeChat articles, marketing copy,
  technical blogs, and health content, using existing deterministic rules and
  optional `regex_rules`.
- The CLI can initialize a new YAML review profile from a built-in template
  through `content-review profile init`.
- The CLI can list the built-in profile templates through
  `content-review profile list`.
- The repository includes a documented GitHub Actions CI example that validates
  a profile and runs batch review with `--fail-on error`.
- The repository includes a dedicated quickstart that documents the first-run
  workflow from dependency installation through profile setup, validation,
  single-file review, batch review, Markdown report output, inline
  suppression, and CI-oriented exit codes.
- The repository includes a dedicated rule system reference that documents the
  current built-in rule IDs, finding fields, severity ordering, quality-gate
  behavior, suppression comments, rule counts, severity counts, batch
  aggregation behavior, reports, and limitations.
- Review profiles can now define optional deterministic `regex_rules` with
  profile-defined rule IDs, compiled regex validation, configurable severity,
  message, optional suggestion, and optional case sensitivity.
- Regex rule findings participate in existing inline suppression, summaries,
  Markdown reports, JSON output, batch aggregation, quality gates, and exit
  code behavior through the normal review pipeline.
- The repository includes a small runnable demo project under `examples/demo/`
  that shows Markdown input, demo profiles, single-file review, batch review,
  Markdown report output, JSON output, inline suppression, and quality-gate
  behavior using the current CLI and report pipeline.

---

## In Progress

- No active implementation task.

## Recent Completion

- TASK-0059 is complete.
- Added sidecar-envelope provider metadata for single-file and batch LLM
  sidecar JSON output through top-level `llm_provider` and
  `llm_provider_source` fields.
- Updated the shared LLM sidecar builder and serializer path so single-file
  sidecars, per-file batch sidecars, and the batch manifest all record the
  concrete provider name plus whether it came from the `explicit`, `default`,
  or `config` selection path.
- Updated `tests/test_llm_sidecar.py`, `tests/test_cli.py`,
  `tests/test_llm_models.py`, and `tests/test_llm_provider_usage_docs.py`
  for explicit-provider metadata, default/config-driven metadata, sidecar
  envelope stability, and main-result isolation boundaries.
- Updated `docs/CLI.md`, `docs/LLM_PROVIDER_USAGE.md`,
  `docs/DATA_MODELS.md`, and `docs/ARCHITECTURE.md` to document the new
  sidecar envelope metadata and its boundary from deterministic outputs.
- Kept `LLMReviewResult`, `ReviewResult`, `BatchReviewResult`,
  `content-review llm-check`, deterministic Markdown reports, and
  quality-gate semantics unchanged.
- Kept real API keys, `.env` loading, and external-network access out of the
  new metadata path.

- TASK-0058 is complete.
- Added explicit batch LLM sidecar reviewer selection for
  `content-review batch` through `--llm-provider mock` and
  `--llm-provider pydantic-ai-testmodel`.
- Updated `src/content_review_engine/cli.py` so explicit batch
  `--llm-provider` uses `create_llm_reviewer()` directly, unsupported values
  fail clearly without fallback, and `--llm-provider` without batch sidecar
  output returns a clear error.
- Kept omitted batch `--llm-provider` behavior on the existing config-driven
  sidecar path, so current default batch sidecar behavior remains unchanged.
- Added and updated `tests/test_cli.py`,
  `tests/test_llm_provider_factory.py`, and
  `tests/test_llm_provider_usage_docs.py` for batch default sidecar behavior,
  `--llm-provider mock`, `--llm-provider pydantic-ai-testmodel`,
  unsupported-provider failures, no-fallback behavior, no-network/no-API-key
  boundaries, and unchanged deterministic output boundaries.
- Updated `docs/CLI.md`, `docs/LLM_PROVIDER_USAGE.md`, and
  `docs/ARCHITECTURE.md` to document the new batch sidecar provider selection
  boundary and its relationship to the existing config-driven path.
- Kept `BatchReviewResult`, single-file behavior, `llm-check` user-visible
  behavior, sidecar JSON schema, Markdown report structure, and quality-gate
  semantics unchanged.

- TASK-0057 is complete.
- Added explicit single-file LLM sidecar reviewer selection for
  `content-review review` through `--llm-provider mock` and
  `--llm-provider pydantic-ai-testmodel`.
- Updated `src/content_review_engine/cli.py` so explicit single-file
  `--llm-provider` uses `create_llm_reviewer()` directly, unsupported values
  fail clearly without fallback, and `--llm-provider` without sidecar output
  returns a clear error.
- Kept omitted single-file `--llm-provider` behavior on the existing
  config-driven sidecar path, so current default sidecar behavior remains
  unchanged.
- Added and updated `tests/test_cli.py`, `tests/test_llm_sidecar.py`, and
  `tests/test_llm_provider_factory.py` for default sidecar behavior,
  `--llm-provider mock`, `--llm-provider pydantic-ai-testmodel`,
  unsupported-provider failures, no-fallback behavior, no-network/no-API-key
  boundaries, and unchanged deterministic output boundaries.
- Updated `docs/CLI.md`, `docs/LLM_PROVIDER_USAGE.md`, and
  `docs/ARCHITECTURE.md` to document the new single-file sidecar provider
  selection boundary and its relationship to the existing config-driven path.
- Kept `ReviewResult`, batch behavior, `llm-check` user-visible behavior,
  sidecar JSON schema, Markdown report structure, and quality-gate semantics
  unchanged.

- TASK-0056 is complete.
- Added `--provider` to `content-review llm-check` for factory-based reviewer
  selection with `mock` and `pydantic-ai-testmodel`.
- Updated `src/content_review_engine/cli.py` and
  `src/content_review_engine/llm/smoke_check.py` so `llm-check --provider`
  creates reviewers through `create_llm_reviewer()` while keeping the default
  `llm-check` config-driven behavior unchanged.
- Added and updated `tests/test_llm_smoke_check.py` and `tests/test_cli.py`
  for default `llm-check` behavior, `--provider mock`,
  `--provider pydantic-ai-testmodel`, unsupported-provider failures, no
  fallback behavior, and no-network/no-API-key boundaries.
- Updated `docs/CLI.md`, `docs/LLM_PROVIDER_USAGE.md`, and
  `docs/ARCHITECTURE.md` to document `llm-check --provider`, its supported
  provider names, and the factory boundary.
- Kept `review` and `batch` default behavior unchanged.
- Kept real API keys, `.env` loading, and external-network access out of the
  new `llm-check --provider` path.

- TASK-0055 is complete.
- Added provider-name-based LLM reviewer construction in
  `src/content_review_engine/llm/factory.py` for `mock` and
  `pydantic-ai-testmodel`, while keeping the existing config-driven CLI/runtime
  factory path intact for `mock` and `pydanticai`.
- Added `UnsupportedLLMProviderError` so unsupported reviewer providers fail
  explicitly with the unknown provider name plus the supported provider names.
- Added `tests/test_llm_provider_factory.py` for provider-name creation,
  protocol conformance, unsupported-provider errors, no-network/no-API-key
  boundaries, and continued config-driven factory compatibility.
- Updated architecture, data-model, and provider-usage docs to document the
  new package-level reviewer provider factory and to record that
  `LLMReviewRequest`, `LLMReviewResult`, and `LLMProviderConfig` schemas are
  unchanged by TASK-0055.
- Kept `LLMReviewRequest` schema unchanged.
- Kept `LLMReviewResult` schema unchanged.
- Kept `LLMProviderConfig` schema unchanged.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept `llm-check`, `review`, and `batch` user-visible default behavior
  unchanged.
- Added no real API-key dependency, no `.env` loading, and no external-network
  test dependency.

- TASK-0054 is complete.
- Added `src/content_review_engine/llm/pydantic_ai_provider.py` with
  `PydanticAITestModelReviewer`, provider-local request helpers, and a
  `pydantic_ai.models.test.TestModel` execution path that returns the
  existing `LLMReviewResult`.
- Kept the TestModel provider separate from the CLI provider factory, secret
  resolution, and `llm-check` so no API key or network access is required for
  its tests.
- Added `tests/test_llm_pydantic_ai_provider.py` for provider protocol,
  request helper, serializable success path, response-validation path, wrapped
  runtime failure path, and continued `MockLLMReviewer` stability.
- Updated architecture, data-model, and provider-usage docs to document the
  package-level TestModel provider boundary and its limitations.
- Kept `LLMProviderConfig` unchanged.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no CLI provider flags, no factory registration for the TestModel
  provider, no real API-key dependency, and no real-network test dependency.

- TASK-0053 is complete.
- Added `content-review llm-check` for standalone LLM provider config, secret,
  and optional runtime smoke checks.
- Added `src/content_review_engine/llm/smoke_check.py` with a synthetic
  minimal `LLMReviewRequest`, stage-oriented smoke-check execution, and stable
  text rendering that avoids printing secrets, full prompts, or tracebacks.
- Reused the existing `LLMProviderConfig`, `--llm-config` YAML loader, CLI
  override precedence, secret resolver, and provider factory boundaries.
- Kept default `llm-check` behavior at config check plus secret check only;
  `--runtime` is now required for a real provider runtime smoke call.
- Added and updated tests for mock config/runtime smoke checks, pydanticai
  secret failures, fake-runtime success/failure paths, config-file errors,
  no-network behavior, override precedence, and output-safety boundaries.
- Updated CLI, CI, architecture, and provider-usage docs for the new
  standalone smoke-check command and its manual-verification-only runtime
  behavior.
- Kept `ReviewProfile` schema unchanged.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no new provider, no fallback behavior, no streaming, no batch
  concurrency, no rate-limit queue, and no real-network default test
  dependency.

- TASK-0052 is complete.
- Added `src/content_review_engine/llm/config_loader.py` plus example
  YAML config files under `examples/llm/pydanticai/` and
  `examples/llm/mock/`.
- Added `--llm-config` support for `content-review review` and
  `content-review batch`.
- Added config-file validation for missing files, invalid YAML, top-level
  non-mapping input, unknown fields, secret-like fields, and invalid LLM
  provider values.
- Updated CLI/provider wiring so explicit CLI flags override the same
  `LLMProviderConfig` fields from `--llm-config`, while parser defaults no
  longer overwrite config-file values.
- Added and updated tests for config-file loading, override precedence,
  mock and fake-runtime CLI wiring, deterministic review isolation when LLM
  is disabled, Quality Gate isolation, and secret-safety boundaries.
- Updated architecture, data-model, CLI, CI, and provider-usage docs for the
  new LLM config-file path and override rules.
- Kept `ReviewProfile` schema unchanged.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no provider fallback, multi-model fallback, streaming, batch
  concurrency, rate-limit queue, API/MCP/GUI, or real-network test
  dependency.

- TASK-0051 is complete.
- Added `min_request_interval_seconds` to `LLMProviderConfig` with validation
  that requires values greater than or equal to `0`.
- Updated the CLI to accept `--llm-min-request-interval-seconds` for
  single-file and batch LLM sidecar flows while keeping deterministic review
  behavior unchanged when `--enable-llm` is not used.
- Updated `src/content_review_engine/llm/pydanticai.py` so the `pydanticai`
  runtime applies instance-local request pacing before each real runtime call,
  including retry calls, with injectable monotonic clock and sleep functions
  for stable tests.
- Added and updated tests for min-interval config defaults and validation,
  CLI parsing and propagation, first-call/no-call-sleep boundaries,
  remaining-interval sleeps, retry-backoff-plus-pacing ordering, batch
  reviewer reuse pacing, continued mock-provider stability, sidecar schema
  stability, no fallback to mock, no-network behavior, and deterministic
  quality-gate isolation.
- Updated architecture, data-model, CLI, CI, and provider-usage docs for
  local request pacing and its relationship to retry backoff.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no rate-limit queue, token bucket, leaky bucket, cross-process rate
  limiter, batch concurrency, streaming, fallback model/provider behavior,
  API/MCP/GUI, or real-network test dependency.

- TASK-0050 is complete.
- Added `retry_attempts` and `retry_backoff_seconds` to
  `LLMProviderConfig` with validation that requires `retry_attempts >= 0`
  and `retry_backoff_seconds >= 0`.
- Updated the CLI to accept `--llm-retry-attempts` and
  `--llm-retry-backoff-seconds` for single-file and batch LLM sidecar flows
  while keeping deterministic review behavior unchanged when `--enable-llm`
  is not used.
- Updated `src/content_review_engine/llm/pydanticai.py` so the `pydanticai`
  runtime keeps the underlying OpenAI-compatible client at `max_retries=0`
  and applies an explicit project-level retry loop only for timeout,
  network, and rate-limit failures.
- Added `LLMProviderRetryExhaustedError` plus retry classification helpers in
  `src/content_review_engine/llm/pydanticai_errors.py`.
- Added and updated tests for retry config defaults and validation, CLI retry
  parsing, fake-runtime timeout/network/rate-limit retry success cases,
  retry exhaustion, non-retryable auth/model/validation/secret/config
  failures, sidecar retry-exhausted recording, mock-provider stability, and
  continued deterministic quality-gate isolation.
- Updated architecture, data-model, CLI, CI, and provider-usage docs for
  explicit retry config and retry classification boundaries.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no rate-limit queue, batch concurrency, streaming, fallback
  model/provider behavior, API/MCP/GUI, or real-network test dependency.

- TASK-0049 is complete.
- Added `docs/LLM_PROVIDER_USAGE.md` with explicit `pydanticai` provider setup,
  single-file and batch manual verification commands, sidecar JSON/Markdown
  inspection guidance, troubleshooting coverage for runtime error types, secret
  safety notes, and CI boundaries.
- Added committed manual verification fixtures under `examples/llm/pydanticai/`
  plus placeholder-only `.env.example`.
- Added `tests/test_llm_provider_usage_docs.py` so docs and fixtures are
  validated locally without real network access or real API keys.
- Updated `docs/CLI.md`, `docs/CI.md`, and `docs/ARCHITECTURE.md` to link the
  new usage guide and clarify that deterministic quality gates remain isolated
  from LLM provider results.
- Kept provider runtime behavior unchanged.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no retry, rate-limit queue, batch concurrency, streaming, fallback
  model/provider behavior, API/MCP/GUI, or real-network test dependency.

- TASK-0048 is complete.
- Added `timeout_seconds` to `LLMProviderConfig` with validation that accepts
  `None` or any value greater than `0`.
- Updated the CLI to accept `--llm-timeout-seconds` for single-file and batch
  LLM sidecar flows while keeping deterministic review behavior unchanged when
  `--enable-llm` is not used.
- Updated `src/content_review_engine/llm/pydanticai.py` so the `pydanticai`
  runtime passes optional timeout configuration into the underlying
  OpenAI-compatible client with no secret leakage.
- Added `src/content_review_engine/llm/pydanticai_errors.py` plus stable
  runtime error subclasses for timeout, auth, network, rate limit, model, and
  unknown runtime failures.
- Added and updated tests for timeout config defaults and validation, CLI
  timeout parsing, fake runtime timeout propagation, runtime error
  classification, partial batch timeout failures, response-validation
  boundaries, deterministic quality-gate isolation, and no-network behavior.
- Updated architecture, data-model, CLI, and CI docs for timeout config and
  runtime error classification.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no retry, rate-limit queue, batch concurrency, streaming, multi-model
  fallback, provider fallback, API/MCP/GUI, or LLM merge into deterministic
  review results.

- TASK-0047 is complete.
- Updated `src/content_review_engine/llm/pydanticai.py` so
  `PydanticAIReviewer.review()` now resolves secrets, builds the stable
  request payload, executes a real PydanticAI runtime call, validates the
  structured response, and maps it back into `LLMReviewResult`.
- Updated CLI/provider wiring so `--enable-llm --llm-provider pydanticai`
  keeps secret preflight, no longer returns not-implemented when the secret
  exists, and now attempts a real sidecar review for single-file and batch
  commands.
- Added runtime-focused PydanticAI provider tests for empty/single/multiple
  findings, summary mapping, invalid responses, runtime exception
  normalization, no fallback to `mock`, no-network fake runtime execution,
  missing-model config errors, and secret redaction.
- Added CLI coverage for fake-runtime `pydanticai` single-file sidecar JSON +
  Markdown output and batch sidecar JSON + Markdown output without real
  network access.
- Updated architecture, data-model, CLI, and CI docs for the real runtime
  boundary and continued deterministic quality-gate isolation.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no retry, timeout, rate-limit, streaming, batch concurrency, fallback
  model, API/MCP/GUI, or deterministic/LLM merge behavior.

- TASK-0046 is complete.
- Added `src/content_review_engine/llm/pydanticai_mapping.py` with a stable
  request payload builder, system/user prompt construction, structured
  response models, response validation, and response-to-`LLMReviewResult`
  conversion for the reserved `pydanticai` provider boundary.
- Updated `src/content_review_engine/llm/pydanticai.py` so the future skeleton
  now holds a mapping component and can build a stable provider-local request
  payload before stopping at the same not-implemented boundary.
- Added dedicated mapping coverage for prompt content, structured output
  requirements, secret redaction, empty/single/multiple finding mapping, and
  non-leaking validation errors.
- Updated the PydanticAI skeleton tests so they assert request-payload
  construction in addition to the existing secret-error, not-implemented, and
  no-network guarantees.
- Updated architecture, data-model, CLI, and CI docs for the new mapping
  boundary while keeping runtime behavior unchanged.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no real PydanticAI review execution, no real LLM API requests, and no
  CLI/runtime path that turns `pydanticai` into a runnable provider.

- TASK-0045 is complete.
- Reintroduced the minimal `pydantic-ai-slim[openai]` dependency and refreshed
  `uv.lock` so the future `pydanticai` provider entry can import its SDK
  boundary again without becoming runnable.
- Added `src/content_review_engine/llm/secrets.py` with structured
  `ResolvedLLMSecret` output and safe environment-variable resolution through
  `LLMProviderConfig.api_key_env`.
- Added `LLMProviderSecretError` for missing, unset, or empty provider secret
  configuration without leaking secret values.
- Updated `src/content_review_engine/llm/pydanticai.py` so the skeleton stores
  `LLMProviderConfig`, imports the minimal PydanticAI dependency, resolves the
  configured secret boundary, and still stops with
  `LLMProviderNotImplementedError` before any real review call.
- Updated the provider factory so `provider="pydanticai"` now creates the
  explicit future skeleton instead of falling back or pretending to be a real
  provider.
- Updated the CLI so `--enable-llm --llm-provider pydanticai` performs secret
  preflight, returns a structured secret error when configuration is missing,
  and returns a clear not-implemented error when the secret exists.
- Added dedicated secret-resolution tests plus updated PydanticAI skeleton,
  provider-factory, and CLI coverage for no-network behavior, secret
  redaction, and preflight errors.
- Updated architecture, data-model, CLI, and CI docs for the dependency and
  secret-resolution boundary.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no real PydanticAI review execution, no real LLM API requests, and no
  secret serialization into config, sidecars, reports, logs, or errors.

- TASK-0044 is complete.
- Normalized the reserved `pydanticai` provider boundary so provider factory,
  CLI behavior, adapter code, tests, and docs all agree that only `mock` is
  runnable today.
- Replaced the old runnable-looking `src/content_review_engine/llm/pydanticai.py`
  implementation with an explicit future skeleton that only raises
  `LLMProviderNotImplementedError`.
- Removed the historical `pydantic-ai-slim[openai]` package dependency because
  the reserved `pydanticai` path is no longer a runnable SDK-backed adapter.
- Removed top-level `llm` package exports that implied a real
  PydanticAI/OpenAI-compatible reviewer already exists.
- Updated provider-factory tests to assert no fallback to `mock`, no required
  PydanticAI SDK import, and no network behavior for the reserved provider
  path.
- Rewrote the old PydanticAI adapter tests so they only assert future-skeleton
  semantics and do not imply a runnable real provider.
- Updated architecture, data-model, CLI, and CI docs so the current runnable
  provider set is explicitly `mock` only and `pydanticai` is recognized but
  not implemented.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no real PydanticAI SDK execution, no real API requests, and no API-key
  secret resolution.

- TASK-0043 is complete.
- Added `LLMProviderConfig` plus structured provider-name validation and
  config loading under `src/content_review_engine/llm/config.py`.
- Added provider-factory and registry helpers under
  `src/content_review_engine/llm/factory.py`.
- The current runnable provider remains `mock`.
- The reserved provider name `pydanticai` is now recognized but returns a
  clear not-implemented error.
- Updated the CLI to parse provider config flags, build reviewer instances
  through the factory, and keep deterministic review behavior unchanged when
  LLM review is not enabled.
- Removed CLI-side environment-variable secret loading from the LLM runner
  path; config now stores only `api_key_env` names.
- Added provider config, provider factory, and updated CLI tests for default
  mock behavior, reserved-provider errors, unknown-provider errors, and
  deterministic quality-gate isolation.
- Updated architecture, data-model, CLI, and CI docs for the new provider
  configuration boundary.
- Kept `LLMSidecarResult` JSON schema unchanged.
- Kept standalone LLM sidecar Markdown report structure unchanged.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no real OpenAI, Anthropic, or PydanticAI SDK execution, no real API
  requests, and no LLM merge into `ReviewResult`.

- TASK-0042 is complete.
- Added `render_llm_sidecar_markdown_report` for standalone LLM sidecar
  Markdown output from `LLMSidecarResult`.
- Single-file `review` now supports optional `--llm-markdown-output` for a
  separate LLM sidecar Markdown report.
- Batch `batch` now supports optional `--llm-markdown-output` for a separate
  Markdown report rendered from `llm-review-manifest.json`.
- The standalone LLM sidecar Markdown report shows top-level summary,
  per-file status, structured errors, skipped entries, and successful-file
  LLM findings.
- Batch manifests now retain nested success `review` payloads so the optional
  batch Markdown sidecar report can render per-file findings directly from the
  manifest.
- Added dedicated LLM Markdown report tests plus CLI tests for single-file and
  batch Markdown sidecar output, deterministic Markdown isolation, and quality
  gate isolation.
- Updated CLI, architecture, data-model, and CI documentation for the new
  standalone sidecar Markdown report path.
- Kept deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no real provider integration, no new API-key configuration, no new
  external LLM SDK dependency, and no LLM merge into `ReviewResult`.

- TASK-0041 is complete.
- Added `LLMSidecarResult`, `LLMSidecarSummary`, per-file sidecar status, and
  structured sidecar errors for CLI LLM output.
- Single-file `--llm-output` now writes `llm-sidecar-result.v2` with
  `summary`, `files[0].status`, optional nested `review`, and structured
  failure output.
- Batch `--llm-output-dir` now keeps the existing per-file sidecar paths and
  also writes `llm-review-manifest.json` with aggregate
  `file_count`, `succeeded_count`, `failed_count`, `skipped_count`, and
  `finding_count`.
- Batch LLM sidecar generation now tolerates per-file LLM failures and records
  them as `status = failed` with `error_type` and `message` instead of
  aborting the whole batch run.
- Added LLM sidecar tests for summary serialization, failed-entry structure,
  single-file failure handling, batch partial failure handling, and quality
  gate isolation.
- Updated CLI, architecture, data-model, and CI documentation for the new
  sidecar envelope and the continued deterministic quality-gate boundary.
- Kept the canonical deterministic review and batch JSON schemas unchanged.
- Kept deterministic Markdown report structure unchanged.
- Kept deterministic quality-gate semantics unchanged.
- Added no real provider integration, no new API-key configuration, no new
  external LLM SDK dependency, and no LLM merge into `ReviewResult`.

- TASK-0040 is complete.
- Added explicit batch CLI LLM sidecar support behind `--enable-llm`.
- Added batch `--llm-output-dir`, `--llm-provider`, `--llm-model`,
  `--llm-api-key-env`, and optional `--llm-base-url`.
- Reused the existing `LLMReviewRunner`, `LLMReviewRequest`,
  `MockLLMReviewer`, `PydanticAIOpenAIReviewer`, and
  `llm_review_result_to_json` sidecar flow for batch review.
- Added per-file batch LLM sidecar JSON output that preserves each reviewed
  Markdown file's path relative to the batch input directory and appends
  `.llm-review.json`.
- Added CLI tests covering batch mock sidecars, recursive relative-path
  sidecars, schema-version stability, empty mock findings, unsupported and
  invalid flag combinations, fake-provider success, quality-gate isolation,
  and sidecar write failure handling.
- Updated CLI, architecture, and data-model documentation for batch LLM
  sidecar behavior and boundaries.
- Kept the canonical deterministic batch JSON schema unchanged.
- Kept batch Markdown report structure unchanged.
- Kept batch summary counts and deterministic finding order unchanged.
- Kept quality-gate semantics unchanged.
- Kept single-file review behavior unchanged.
- Added no API, MCP, GUI, streaming, retry policy, cache, token accounting,
  cost tracking, telemetry, or tracing integration.

- TASK-0039 is complete.
- Added optional single-file Markdown report integration for existing
  `LLMReviewResult` output behind explicit `--include-llm-report`.
- Extended `render_markdown_report` with a backward-compatible optional
  `llm_result` input and added a dedicated appended `## LLM Review` section.
- Added CLI validation so `--include-llm-report` only works with
  `content-review review`, `--enable-llm`, and `--format markdown`.
- Kept the required LLM sidecar JSON output through `--llm-output`.
- Added Markdown report tests for empty and populated LLM sections, Markdown
  escaping, and deterministic-count isolation.
- Added CLI tests for default Markdown stability, opt-in LLM report rendering,
  invalid argument combinations, JSON isolation, sidecar persistence, and
  quality-gate isolation.
- Updated CLI, architecture, and data-model documentation for the new
  optional Markdown LLM section.
- Kept deterministic review behavior unchanged.
- Kept the canonical deterministic review JSON schema unchanged.
- Kept quality-gate semantics unchanged.
- Kept batch review behavior unchanged and added no batch LLM integration.
- Added no API, MCP, GUI, streaming, retry policy, cache, token accounting,
  cost tracking, telemetry, or tracing integration.

- TASK-0038 is complete.
- Added `pydantic-ai-slim[openai]` and a new
  `PydanticAIOpenAIReviewer` under `src/content_review_engine/llm/`.
- Added `--llm-provider pydanticai-openai` support to the single-file
  `content-review review` CLI command.
- Added `--llm-model`, `--llm-api-key-env`, and optional `--llm-base-url`
  for the `pydanticai-openai` sidecar path.
- Kept `--llm-provider mock` behavior unchanged and still optional.
- Reused the existing `LLMReviewRequest`, `LLMReviewRunner`,
  `LLMReviewResult`, and `llm_review_result_to_json` sidecar flow.
- Added provider tests covering interface compatibility, structured-output
  mapping, empty findings, populated findings, schema-version stability,
  provider error mapping, validation error mapping, and API-key non-leakage.
- Added CLI tests covering the new provider flags, missing-model failure,
  missing-API-key-env failure, mock compatibility, fake-provider success path,
  sidecar creation, and main JSON isolation from LLM data.
- Updated CLI, architecture, and data-model documentation for the
  `pydanticai-openai` provider boundary.
- Kept deterministic review behavior unchanged.
- Kept current deterministic review JSON output schema unchanged.
- Kept Markdown report structure unchanged.
- Kept quality-gate semantics unchanged.
- Kept batch review behavior unchanged and added no batch LLM support.
- Added no LLM merge into `ReviewResult`, no API, no MCP, no GUI, no
  streaming, no retry policy, no cache, no token accounting, no cost
  tracking, no telemetry, and no tracing integration.

- TASK-0037 is complete.
- Added experimental mock-only LLM plumbing to the single-file
  `content-review review` CLI command behind explicit `--enable-llm`.
- Added `--llm-output` as a required sidecar JSON destination when LLM review
  is enabled.
- Added optional `--llm-provider mock`, with current validation that only
  `mock` is supported and only when LLM review is explicitly enabled.
- Reused the existing `LLMReviewRunner`, `LLMReviewRequest`,
  `MockLLMReviewer`, and `llm_review_result_to_json` helper to write a
  separate `LLMReviewResult` sidecar file.
- Added CLI tests covering sidecar generation, stable LLM schema version,
  default empty mock findings, main JSON isolation from LLM data, request
  construction, and invalid CLI argument combinations.
- Updated CLI, architecture, and data-model documentation for the new
  sidecar-only LLM flow.
- Kept deterministic review behavior unchanged by default.
- Kept `regex_rules` behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept current deterministic review JSON output schema unchanged.
- Kept batch review behavior unchanged and added no batch LLM support.
- Added no real provider integration, no PydanticAI, no OpenAI SDK, no
  Anthropic SDK, no environment-variable loading, and no API, MCP, or GUI
  behavior.

- TASK-0036 is complete.
- Added `src/content_review_engine/llm/runner.py` with a lightweight
  synchronous `LLMReviewRunner` that accepts an injected `LLMReviewer`,
  forwards `LLMReviewRequest`, and returns `LLMReviewResult`.
- Exported `LLMReviewRunner` from `src/content_review_engine/llm/__init__.py`
  for package-level imports.
- Added runner tests covering reviewer invocation, configured mock behavior,
  default empty mock behavior, stable schema version, and provider error
  propagation.
- Updated architecture and data-model documentation to place the runner in the
  `LLMReviewRequest -> LLMReviewRunner -> LLMReviewer -> LLMReviewResult`
  flow and to document its separation from the deterministic review result
  schema.
- Kept deterministic review behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept current review JSON output schema unchanged.
- Added no real provider integration, no PydanticAI, no API keys, no prompt
  templates, no CLI LLM behavior, and no API, MCP, or GUI behavior.

- TASK-0035 is complete.
- Added future-facing `LLMReviewRequest`, a synchronous `LLMReviewer`
  provider protocol, minimal LLM error types, and a deterministic
  `MockLLMReviewer` under `src/content_review_engine/llm/`.
- Added tests for request validation, provider protocol compatibility, mock
  reviewer default and configured behavior, serialization of mock results, and
  the LLM error hierarchy.
- Updated architecture and data-model documentation to describe the future LLM
  provider boundary and deterministic mock adapter.
- Kept deterministic review behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept current review JSON output schema unchanged.
- Added no real provider integration, no PydanticAI, no API keys, no prompt
  templates, no CLI LLM behavior, and no API, MCP, or GUI behavior.

- TASK-0034 is complete.
- Added future-facing `LLMReviewFinding`, `LLMReviewSummary`, and
  `LLMReviewResult` models under `src/content_review_engine/llm/` with the
  stable schema version `llm-review-result.v1`.
- Added LLM serialization helpers that follow the existing explicit helper
  style without changing the current deterministic JSON output schema.
- Added tests for valid and invalid LLM model construction and serialization.
- Updated architecture, data-model, and rule documentation to place a future
  LLM semantic review layer behind a separate conversion and merge boundary.
- Kept deterministic review behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept current review JSON output schema unchanged.
- Added no provider integration, no PydanticAI, no API, no MCP, and no GUI
  behavior.

- TASK-0033 is complete.
- Added structured profile validation issues with `path`, `code`, `message`,
  and optional `suggestion`.
- Added reusable profile-loading validation failures so `profile validate`,
  `review`, and `batch` fail cleanly on invalid profiles without tracebacks for
  normal user input errors.
- Improved regex-rule and YAML validation feedback for invalid rule IDs,
  duplicate rule IDs, invalid regex patterns, empty regex messages, invalid
  `case_sensitive` values, invalid severities, and invalid YAML.
- Added invalid profile fixtures plus validation and CLI rendering tests.
- Updated README, quickstart, CLI, profile, and data-model documentation for
  structured profile validation errors.
- Kept deterministic review behavior unchanged.
- Kept `regex_rules` matching behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept JSON review output schema unchanged.
- Added no LLM review, PydanticAI, API, MCP, or GUI behavior.

- TASK-0032 is complete.
- Added `examples/demo/` with short WeChat-style and technical-blog demo
  articles plus stable demo profiles that include deterministic `regex_rules`.
- Added committed demo Markdown reports for the two single-file demo runs.
- Added demo-focused tests covering file presence, profile validation, regex
  rules, findings, suppression, Markdown report rendering, JSON serialization,
  batch review, quality-gate behavior, demo README commands, doc links, and
  conservative wording.
- Updated README, quickstart, CLI, and profile documentation so users can find
  the runnable demo directly from the main references.
- Kept deterministic rule matching behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression syntax unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept JSON output schema unchanged.
- Added no LLM review, PydanticAI, API, MCP, or GUI behavior.
- Added no legal, medical, advertising, regulatory, or platform compliance
  guarantees.

- TASK-0031 is complete.
- Added five practical built-in example/template profiles:
  `general-publishing`, `wechat-article`, `marketing-copy`,
  `technical-blog`, and `health-content`.
- Reused existing built-in rules plus profile-configured `regex_rules` to flag
  common placeholders, exaggerated claims, guarantee-like wording, pressure
  tactics, unresolved draft markers, and health-related caution cases.
- Kept template discovery and initialization on the existing registry-driven
  `profile list` and `profile init` path.
- Added tests for template discovery, initialization, validation, regex rule
  presence, and conservative documentation wording.
- Updated profile, quickstart, CLI, README, project state, and changelog
  documentation for the expanded template set and their limitations.
- Kept deterministic rule matching behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression syntax unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept JSON output schema unchanged.
- Added no LLM review, PydanticAI, API, MCP, or GUI behavior.
- Added no legal, medical, advertising, regulatory, or platform compliance
  guarantees.

- TASK-0030 is complete.
- Added optional `regex_rules` support to `ReviewProfile`.
- Added regex rule ID validation, regex pattern compilation validation, and
  duplicate regex rule ID rejection during profile loading and validation.
- Added deterministic line-by-line regex rule execution that produces one
  finding per match using the configured regex rule ID as `rule_id`.
- Reused the existing suppression, summary, report, batch, and quality-gate
  pipeline so regex findings participate without changing the canonical output
  shapes.
- Updated architecture, rule, profile, CLI, and data-model documentation for
  regex rule configuration, runtime behavior, registry boundary, and current
  limitations.
- Added regex-focused tests for loading, validation, execution, suppression,
  counts, reports, batch aggregation, and quality gates.
- Kept built-in rule behavior unchanged.
- Kept suppression syntax unchanged.
- Kept quality-gate semantics unchanged.
- Kept JSON output shape unchanged.

- TASK-0029 is complete.
- Documented the architectural boundary between the descriptive built-in rule
  metadata registry in `src/content_review_engine/core/rule_registry.py` and
  the deterministic execution registry in
  `src/content_review_engine/rules/registry.py`.
- Updated architecture, rule-system, data-model, and profile documentation to
  keep metadata concerns separate from runtime rule execution and profile
  configuration.
- Positioned future LLM semantic review as a separate later layer that should
  produce compatible findings if introduced later.
- Added documentation tests that keep the registry boundary explicit.
- Kept rule matching behavior, suppression behavior, CLI behavior, report
  format, JSON schema, profile parsing, and exit code behavior unchanged.

- TASK-0028 is complete.
- Added `RuleDefinition` plus a centralized deterministic built-in rule
  metadata registry in `src/content_review_engine/core/rule_registry.py`.
- Registered the current built-in rule IDs:
  `forbidden_terms`, `absolute_claims`, `markdown_structure`, and
  `markdown_links_images`.
- Added registry tests for completeness, uniqueness, deterministic ordering,
  lookup behavior, and metadata presence.
- Updated rule, data model, and profile documentation to mention the
  centralized built-in metadata registry.
- Kept rule matching behavior, suppression behavior, CLI behavior, report
  format, JSON schema, and exit code behavior unchanged.

- TASK-0027 is complete.
- Consolidated legacy rule documentation around `docs/RULES.md` as the
  canonical rule system reference.
- Migrated the remaining useful legacy details into `docs/RULES.md`,
  specifically the legacy top-level `forbidden_terms` profile input note and
  the implementation/test path references for the current built-in rules.
- Replaced `docs/REVIEW_RULES.md` with a short compatibility stub that points
  to `docs/RULES.md`.
- Updated current user-facing docs and documentation tests so they consistently
  point to `docs/RULES.md`.
- Kept rule matching behavior, suppression behavior, CLI behavior, report
  format, JSON schema, and exit code behavior unchanged.

- TASK-0026 is complete.
- Added `docs/RULES.md` as the dedicated rule system reference.
- Documented the current built-in rule IDs:
  `forbidden_terms`, `absolute_claims`, `markdown_structure`, and
  `markdown_links_images`.
- Documented current finding fields, severity levels, severity ordering,
  `--fail-on` behavior, rule counts, severity counts, suppression comments,
  batch aggregation behavior, reports, and limitations.
- Updated `README.md`, `docs/QUICKSTART.md`, `docs/CLI.md`, `docs/PROFILES.md`,
  and `docs/CI.md` to link the new rule reference.
- Added documentation tests that verify the rule reference exists, covers the
  durable rule-system concepts, and is linked from the user-facing docs.
- Kept rule matching behavior, suppression behavior, CLI behavior, report
  format, JSON schema, and exit code behavior unchanged.

- TASK-0025 is complete.
- Added `docs/QUICKSTART.md` covering `uv sync`, `profile list`,
  `profile init`, `profile validate`, `review`, `batch`, `--fail-on`,
  Markdown report output, inline suppression, exit codes, CI handoff, and
  compliance limitations.
- Added lightweight documentation tests that verify the quickstart exists and
  includes the core CLI commands, Markdown report flow, inline suppression,
  exit codes, and detailed-doc links.
- Updated `README.md`, `docs/CLI.md`, `docs/PROFILES.md`, `docs/CI.md`, and
  `CHANGELOG.md` to link the new quickstart.
- Kept `profile list`, `profile init`, `profile validate`, `review`, `batch`,
  suppression behavior, `forbidden_terms`, `absolute_claims`, text/JSON/Markdown
  output, and `--fail-on` exit-code rules unchanged.

- TASK-0024 is complete.
- Improved `content-review review --format markdown` and
  `content-review batch --format markdown` to render structured Markdown
  reports with summary tables, severity counts, rule counts, detailed findings,
  deterministic per-file batch sections, and clear `No findings.` empty
  states.
- Markdown reports now include quality-gate status when `--fail-on` is used
  and still write to `--output` before returning exit code `1` when the gate
  fails.
- Added Markdown rendering tests and CLI Markdown output tests covering
  quality-gate sections, empty states, and report-file writes.
- Updated CLI and CI documentation for improved Markdown report usage.
- Kept `profile list`, `profile init`, `profile validate`, `review`, `batch`,
  JSON schema, text output, suppression behavior, `forbidden_terms`,
  `absolute_claims`, and `--fail-on` exit-code rules unchanged.

- TASK-0023 is complete.
- Added a documented GitHub Actions example at
  `docs/examples/github-actions/content-review.yml`.
- Added `docs/CI.md` covering profile validation, batch review, CI exit codes,
  path customization, and workflow limitations.
- Added lightweight tests that ensure the CI example and CI documentation
  exist and include the key automation commands.
- Kept `profile list`, `profile init`, `profile validate`, `review`, `batch`,
  `--fail-on`, suppression, `forbidden_terms`, and `absolute_claims` behavior
  unchanged.

- TASK-0022 is complete.
- Added `content-review profile list` with `--format text|json`.
- Reused the built-in template registry as the single source of truth for both
  `profile list` and `profile init`.
- Added deterministic template descriptions and canonical
  `profile-template-list.v1` JSON output without embedding full YAML template
  content.
- Added CLI tests for text output, JSON output, help output, and registry
  consistency including generated-profile validation.
- Updated CLI, profile, architecture, data model, project state, and
  changelog documentation for the new profile discovery command.

- TASK-0021 is complete.
- Added `content-review profile init` with required `--template` and
  `--output` options plus optional `--force`.
- Supported built-in templates:
  - `general-basic`
  - `wechat-basic`
  - `wechat-strict`
- Reused the committed example profiles as the template source and kept
  `review`, `batch`, and `profile validate` behavior unchanged.
- Added CLI tests for successful initialization, generated-profile validation,
  help output, unknown templates, overwrite conflicts, forced overwrite, and
  missing parent directories.
- Updated CLI and profile documentation with initialization workflow and
  overwrite rules.

- TASK-0020 is complete.
- Added built-in example profiles:
  - `profiles/examples/general-basic.yaml`
  - `profiles/examples/wechat-basic.yaml`
  - `profiles/examples/wechat-strict.yaml`
- Added tests that load the example profiles, validate them through
  `content-review profile validate`, and run review integration coverage with
  an example profile.
- Added `docs/PROFILES.md` and updated CLI documentation with example-profile
  usage and validation examples.

- TASK-0019 is complete.
- Added a new `content-review profile validate <profile_path>` CLI flow.
- Reused the existing profile loader for profile validation and kept review and
  batch behavior unchanged.
- Added canonical text and JSON outputs for profile validation results.
- Added CLI tests for valid profiles, invalid profiles, invalid YAML, unknown
  rules, and validation JSON output.

- TASK-0018 is complete.
- Added the deterministic `absolute_claims` rule with literal `terms`,
  optional literal `allow_terms`, and configurable finding severity.
- Added rule-style YAML loading for `absolute_claims` and kept existing
  `forbidden_terms` loading behavior compatible.
- Registered `absolute_claims` in the default rule registry as opt-in, and
  reused the existing review pipeline, suppression filtering, summaries, batch
  aggregation, and CLI quality gates.
- Added tests for profile loading, rule behavior, registry/runner integration,
  review pipeline behavior, batch summaries, CLI output, and quality-gate
  behavior for `absolute_claims`.

- TASK-0017 is complete.
- Added optional `allow_terms` support for the `forbidden_terms` rule through rule-style YAML configuration.
- Added Markdown inline suppression comments for `content-review-disable-line forbidden_terms` and `content-review-disable-next-line forbidden_terms`.
- Suppressed findings are filtered before `ReviewResult` creation, so they are excluded from text, JSON, and Markdown output.
- Batch summaries and quality gates now evaluate only unsuppressed findings.
- Added unit tests for allowlist behavior, suppression parsing/filtering, review pipeline filtering, batch summary behavior, and CLI quality-gate behavior.

- TASK-0016 is complete.
- Added `--fail-on` support to both `content-review review` and `content-review batch`.
- Added canonical severity ordering for quality gates: `info < warning < error < critical`.
- Added CI-friendly exit-code behavior: `0` for pass, `1` for quality-gate failure, and `2` for command errors.
- Kept `ReviewResult` and `BatchReviewResult` schemas stable.
- Added quality-gate helper tests and CLI exit-code tests.

- TASK-0015 is complete.
- Added a minimal `content-review batch` command that discovers Markdown files deterministically and reuses the existing review pipeline for each file.
- Added `BatchReviewSummary` and `BatchReviewResult` core models with canonical JSON serialization helpers.
- Added batch Markdown report rendering and batch CLI support for text, JSON, Markdown, `--output`, `--recursive`, and `--pattern`.
- Added batch fixtures, batch examples, discovery tests, summary tests, serialization tests, Markdown report tests, and CLI tests.
- Preserved the existing single-file `content-review review` behavior.

- TASK-0013 is complete.
- Added the deterministic `markdown_structure` rule.
- Kept `forbidden_terms` as the default-enabled rule.
- Added Markdown structure fixtures, example files, tests, and documentation.
- Preserved existing default forbidden-terms behavior and CLI behavior.

- TASK-0014 is complete.
- Added the deterministic `markdown_links_images` rule.
- Kept `markdown_links_images` opt-in through `ReviewProfile.enabled_rules`.
- Added Markdown links/images fixtures, example files, tests, and documentation.
- Preserved existing default forbidden-terms behavior, markdown_structure behavior, and CLI behavior.

- TASK-0012 is complete.
- Added a minimal internal rule interface, rule registry, and rule runner.
- The existing forbidden-terms rule now runs through the rule runner.
- The review pipeline still returns canonical `ReviewResult`.
- Added an optional `enabled_rules` field to `ReviewProfile` for explicit rule selection.
- Preserved existing CLI behavior for the default review path.
- Added tests for rule registry registration, duplicate rule IDs, unknown rule IDs, default registry behavior, rule runner behavior, review pipeline integration, and unknown-rule CLI handling.
- Added `docs/RULES.md` and updated architecture, data model, project state, and changelog documentation.

- TASK-0011 is complete.
- Added a canonical `ReviewResult` model with `ReviewSummary`, document metadata, and profile metadata support.
- Added explicit review result serialization helpers for dict and JSON output.
- Updated the review pipeline, CLI JSON output, and Markdown report rendering to use the canonical `ReviewResult`.
- Added a documented JSON Schema for `review-result.v1`.
- Updated the data model, CLI, report, project state, and changelog documentation for the stabilized output contract.
- Added tests for `ReviewSummary`, `ReviewResult`, serialization helpers, the review pipeline, CLI JSON output, and Markdown report rendering.

- TASK-0010 is complete.
- Added packaging configuration so the existing `content-review` console script is installable through `uv sync`.
- Updated CLI and testing docs to prefer `uv run content-review`.
- Added a console-script smoke test that checks the packaged entrypoint metadata.

- TASK-0009 is complete.
- Added committed Markdown fixtures for clean, forbidden-term, multiline, and code-block scenarios.
- Added committed ReviewProfile fixtures under `tests/fixtures/profiles/`.
- Added `examples/article.md` and `examples/profile.yml` for manual CLI usage.
- Updated selected tests to use fixture files where appropriate.
- Added `docs/TESTING.md` and updated CLI/report documentation for example-file commands.
- No review behavior changes were introduced.

- TASK-0008 is complete.
- Added a Markdown review report renderer in `content_review_engine.reports`.
- The CLI now supports `--format markdown`.
- The CLI now supports `--output` for writing rendered reports to a file.
- Added tests for the Markdown report renderer and CLI Markdown output paths.
- TASK-0007 is complete.
- Added source location metadata to review findings.
- The forbidden terms rule now reports matched text, line, column, character offsets, and a context snippet.
- The CLI now prints location-aware text output and JSON output with nested location objects.
- The project still does not have LLM review, API, MCP, persistence, frontend, diff tracking, or rewriting support.

---

## Next Tasks

1. Add additional deterministic review rules.
2. Extend the review pipeline with more deterministic rules.

---

## Open Questions

- Final package name has not been frozen.
- CLI command name has not been frozen.
- PydanticAI integration is planned but not part of M0.
- MCP integration is planned but not part of M0.

---

## Do Not Change Yet

- Do not add MCP server yet.
- Do not add Skill yet.
- Do not add FastAPI yet.
- Do not add Supabase yet.
- Do not add frontend yet.

---

## Last Handoff

### Completed

- Added a minimal internal rule registry and rule runner.
- Routed the forbidden-terms rule through the runner.
- Added a default registry containing `forbidden_terms`.
- Added optional `enabled_rules` support to `ReviewProfile`.
- Defined initial core data models.
- Added `ReviewIssue`.
- Added `ReviewResult`.
- Added `ReviewProfile`.
- Added validation tests for model creation.
- Added validation tests for invalid severity and invalid score.
- Updated data model documentation.
- Normalized test import configuration for the `src/` layout.
- Added Markdown reader support.
- Added YAML profile loading support.
- Added tests for Markdown parsing and profile loading.
- Added the first deterministic forbidden terms review rule.
- Added tests for the forbidden terms rule.
- Added a minimal review pipeline that runs `forbidden_terms` in memory.
- Added tests for the review pipeline.
- Added a minimal CLI entrypoint with a `review` subcommand.
- Added CLI tests for success, missing files, and help output.
- Added source location metadata for deterministic findings.
- Added CLI text and JSON output support for finding locations.
- Added tests for location calculation, location-aware forbidden term findings, and CLI JSON output.
- Added `docs/CLI.md`.
- Added `TASK-0007` completion updates.
- Updated architecture documentation, project state, and changelog for the CLI task.

### Changed Files

- `profiles/examples/general-basic.yaml`
- `profiles/examples/wechat-basic.yaml`
- `profiles/examples/wechat-strict.yaml`
- `tests/test_example_profiles.py`
- `tests/test_cli.py`
- `docs/PROFILES.md`
- `src/content_review_engine/core/__init__.py`
- `src/content_review_engine/core/models.py`
- `tests/test_models.py`
- `docs/DATA_MODELS.md`
- `PROJECT_STATE.md`
- `CHANGELOG.md`
- `pyproject.toml`
- `uv.lock`
- `src/content_review_engine/parser/__init__.py`
- `src/content_review_engine/parser/markdown.py`
- `src/content_review_engine/config/__init__.py`
- `src/content_review_engine/config/profiles.py`
- `profiles/wechat.yaml`
- `tests/test_markdown_parser.py`
- `tests/test_profile_loader.py`
- `docs/ARCHITECTURE.md`

### Test Result

`uv run pytest` passed.

### Next Recommended Task

TASK-0008: Add a second deterministic review rule or expand the core review metadata further.

### Notes

`tests/test_models.py` now imports `content_review_engine` normally, with pytest configured to include `src/` on the import path.
The core package now includes one deterministic rule: `forbidden_terms`.
