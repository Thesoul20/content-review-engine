# Architecture

## Architecture Style

This project follows a Python package-first architecture.

The core package is the center of the system.

External interfaces such as CLI, Skill, MCP, API, and frontend are adapters.

---

## Target Architecture

```text
Frontend / Web / Tauri
        ↓
FastAPI Backend
        ↓
MCP Server / CLI / Skill
        ↓
Python Core Package
        ↓
Review Rules / AI Adapter / Diff / Reports
```

---

## Current Architecture

Current phase only includes:

```text
Python Core Package
CLI
Docs
Tasks
Tests
```

MCP, Skill, API, and frontend are planned but not implemented yet.

The current core package input layer includes:

```text
src/content_review_engine/parser/
src/content_review_engine/config/
src/content_review_engine/review/
src/content_review_engine/rules/
src/content_review_engine/reports/
profiles/
```

---

## Core Package Responsibility

The core package should handle:

- Markdown input processing
- Review profile loading
- Review pipeline coordination
- Rule execution
- Structured review findings and results
- Report generation
- Diff generation
- AI review adapter in later versions

Current implemented input helpers:

- `content_review_engine.parser.read_markdown`
- `content_review_engine.config.load_profile`
- `content_review_engine.core.quality_gate`
- `content_review_engine.core.suppression`
- `content_review_engine.rules.check_forbidden_terms`
- `content_review_engine.rules.check_absolute_claims`
- `content_review_engine.rules.check_markdown_structure`
- `content_review_engine.rules.check_markdown_links_images`
- `content_review_engine.rules.build_default_rule_registry`
- `content_review_engine.rules.run_rules`
- `content_review_engine.review.review_document`
- `content_review_engine.reports.render_markdown_report`

Current CLI adapter:

```text
content-review review <markdown_file> --profile <profile_file>
content-review batch <input_dir> --profile <profile_file>
content-review llm-check [LLM config flags]
content-review profile validate <profile_file>
content-review profile init --template <template_name> --output <profile_file>
content-review profile list [--format text|json]
```

Current CLI flow:

```text
CLI
 ↓
Markdown Reader
 ↓
Profile Loader
 ↓
Review Pipeline
 ↓
Rule Runner
 ↓
Rule Registry
 ↓
Deterministic Rules
 ↓
Inline Suppression Filtering
 ↓
Review Result
```

For batch review, the CLI adds a deterministic directory discovery step before the Markdown Reader.

The CLI currently supports reviewing one Markdown file with one YAML profile, reviewing a directory of Markdown files with one YAML profile, validating a YAML profile independently before a review run, initializing a local profile from a built-in template, and listing the built-in templates exposed by the same registry.
It prints simple human-readable summaries, supports JSON output, and can export Markdown review reports for both single-file and batch review.
It also supports a CLI quality gate through `--fail-on`, using canonical severity ordering in the core package to choose automation-friendly exit codes.
It does not yet support HTML, watch mode, or report persistence beyond the optional Markdown output file.

Current deterministic rules:

- `forbidden_terms`
- `absolute_claims`
- `markdown_structure`
- `markdown_links_images`

## Rule Registry Boundaries

The current architecture intentionally keeps two rule registries with separate
responsibilities.

- `src/content_review_engine/core/rule_registry.py` is the metadata registry.
  It describes known built-in `rule_id` values and small internal metadata
  through `RuleDefinition`.
- `src/content_review_engine/rules/registry.py` is the deterministic execution
  registry. It registers runtime rule implementations, controls default
  enablement, and participates in the review pipeline.

Why both exist:

- the metadata registry gives docs, tests, future CLI metadata display, and
  profile guidance a stable descriptive source
- the execution registry keeps runtime rule wiring explicit and operational
- separating them avoids coupling user-facing rule descriptions to the runtime
  rule objects too early

The metadata registry is descriptive only. It does not execute rules, parse
Markdown, match content, apply suppression, compute quality gates, or change
JSON output schemas.

The execution registry is operational. It decides which deterministic rule
implementations run during review, but it is not the primary user-facing
metadata source for docs or profile guidance.

Profile-configured `regex_rules` are a separate runtime profile-driven path.
Their individual rule IDs are dynamic, so they are not pre-registered as
built-in metadata definitions or built-in execution-registry entries.
Instead, the review runner executes configured regex rules directly from the
loaded `ReviewProfile` and emits normal `ReviewFinding` objects.

They should not be merged yet. The project only has one current deterministic
execution path, but it already has multiple descriptive use cases for stable
rule metadata. Keeping the registries separate preserves a clean boundary while
the rule system grows.

Future deterministic rules should register stable metadata in the metadata
registry and register executable rule implementations in the execution
registry. Adding one does not replace the responsibility of the other.

Future LLM semantic review belongs as a separate later layer beside the
deterministic execution path. It should not be mixed into
`src/content_review_engine/rules/registry.py`. If added later, it should
produce compatible findings so reports, quality gates, and other downstream
consumers can keep a coherent result model.

Current boundary in flow form:

```text
Markdown Input
  ↓
Profile Loading
  ↓
Deterministic Rule Execution Registry
  ↓
Rule Findings
  ↓
Optional Future LLM Semantic Review
  ↓
Merged Findings
  ↓
Reports / Quality Gate / Exit Codes
```

Metadata stays on a separate descriptive path:

```text
Rule Metadata Registry
  ↓
Docs / Tests / Future CLI metadata display / Profile guidance
```

## Future LLM Review Layer

TASK-0034 adds only foundational future-facing LLM review data models under
`src/content_review_engine/llm/`.

Current status:

- the review engine remains deterministic for the main review pipeline
- `src/content_review_engine/llm/config.py` now defines a structured
  `LLMProviderConfig`
- `src/content_review_engine/llm/config_loader.py` now loads YAML LLM provider
  config files into `LLMProviderConfig`
- `src/content_review_engine/llm/smoke_check.py` now runs standalone provider
  config/secret/runtime smoke checks without entering the deterministic review
  pipeline
- `src/content_review_engine/llm/factory.py` now owns two creation boundaries:
  config-driven runtime provider selection for the existing CLI sidecar path,
  and name-driven reviewer construction for package-local reviewer providers
  such as `mock` and `pydantic-ai-testmodel`
- for config-driven `pydanticai`, that factory can now also accept a resolved
  in-memory secret value for construction-only checks without resolving the
  secret itself
- `src/content_review_engine/llm/config.py` now also owns the provider-name
  contract boundary that distinguishes current test providers, reserved real
  provider names, and unsupported provider names before any `.env` read,
  secret lookup, or network call
- `content-review llm-check --provider` now uses that name-driven factory path
  for safe local smoke checks, while the existing config-driven `llm-check`
  path remains available for `mock` and `pydanticai`
- single-file sidecar review now has two explicit paths:
  omitted `--llm-provider` keeps the existing config-driven boundary, while
  explicit `--llm-provider mock|pydantic-ai-testmodel` uses the name-driven
  `create_llm_reviewer()` boundary
- batch sidecar review now follows that same split:
  omitted `--llm-provider` keeps the existing config-driven boundary, while
  explicit `--llm-provider mock|pydantic-ai-testmodel` uses the name-driven
  `create_llm_reviewer()` boundary
- single-file and batch sidecar envelopes now also record `llm_provider` plus
  `llm_provider_source` at the top level, so sidecar consumers can tell which
  provider ran and whether the selection was `explicit`, `default`, or
  `config`
- the CLI can optionally write a separate LLM sidecar Markdown report for
  single-file or batch sidecar output through `--llm-markdown-output`
- the single-file Markdown report can now optionally append a separate
  `LLMReviewResult` section when `--format markdown`, `--enable-llm`, and
  `--include-llm-report` are all enabled
- no LLM output is merged into the current `ReviewResult`
- no LLM output is merged into deterministic severity counts, rule counts, or
  quality-gate evaluation
- batch review now supports per-file `LLMSidecarResult` JSON sidecars, an
  aggregate `llm-review-manifest.json`, and an optional separate batch LLM
  sidecar Markdown report
- `src/content_review_engine/llm/prompt_contract.py` now defines a separate
  semantic-review prompt contract builder that produces stable system/user
  prompt text from `LLMReviewRequest` without calling any provider
- `src/content_review_engine/llm/result_conversion.py` now defines a separate
  conversion helper that maps `ValidatedLLMSemanticReviewOutput` into
  `LLMReviewResult` without calling a provider, reading environment
  variables, or changing sidecar or deterministic-review behavior
- the canonical deterministic JSON output schema remains unchanged

Current provider-contract boundary:

```text
raw provider name or LLMProviderConfig
  ↓
validate_llm_provider_name / validate_llm_provider_config
  ↓
test provider
  -> local factory path may create reviewer

reserved real provider
  -> fail as reserved but not implemented

unsupported provider
  -> fail as unknown provider
```

Current categories:

- test providers: `mock`, `pydantic-ai-testmodel`
- reserved real providers: `openai`, `anthropic`, `gemini`, `deepseek`,
  `qwen`, `local`
- existing config-driven runtime adapter: `pydanticai`

This contract layer is intentionally local-only in the current task. It does
not read `.env`, does not resolve API keys, does not access the network, and
does not add new real-provider classes.

The intended future boundary is:

```text
Markdown Input
  ↓
Deterministic Rule Review
  ↓
Rule Findings
  ↓
Future Optional LLM Semantic Review
  ↓
LLMReviewResult
  ↓
Future Merge Layer
  ↓
Combined Report
```

Current prompt-contract boundary:

```text
LLMReviewRequest
  ↓
build_llm_semantic_review_prompt_contract()
  ↓
system_prompt + user_prompt + output schema version
  ↓
future provider execution
  ↓
future output validation
  ↓
ValidatedLLMSemanticReviewOutput
```

Current validated-output conversion boundary:

```text
ValidatedLLMSemanticReviewOutput
  ↓
convert_validated_semantic_output_to_llm_review_result()
  ↓
LLMReviewResult
```

Current prompt-contract guarantees:

- prompt construction is separate from provider construction and provider
  execution
- prompt construction does not read `.env`
- prompt construction does not read `os.environ`
- prompt construction does not access the network
- prompt construction does not resolve secrets
- prompt construction does not create `LLMReviewResult`
- prompt construction does not integrate into `content-review review` or
  `content-review batch` yet
- prompt construction can include optional deterministic-finding context from
  `LLMReviewRequest`, but it does not execute deterministic rules itself
- prompt construction redacts metadata values for sensitive keys before they
  enter the prompt text

Current output-validation boundary:

```text
raw LLM output text
  ↓
extract_llm_semantic_review_json()
  ↓
parse_llm_semantic_review_output()
  ↓
validate_llm_semantic_review_output()
  ↓
ValidatedLLMSemanticReviewOutput
```

Current output-validation guarantees:

- output parsing and validation are separate from provider construction and
  provider execution
- the parser accepts only pure JSON or a single fenced `json` block
- the parser does not auto-repair malformed JSON
- the validator enforces the `llm-semantic-review-output.v1` contract
- the validator returns a validated semantic-review output model, not
  `LLMReviewResult`
- the parser and validator do not read `.env`
- the parser and validator do not read `os.environ`
- the parser and validator do not resolve secrets
- the parser and validator do not access the network
- the parser and validator do not integrate into `content-review review` or
  `content-review batch` yet

This keeps prompt design, output validation, provider execution, and future
result conversion as separate layers.

Current PydanticAI semantic-review execution boundary:

```text
LLMReviewRequest
  ↓
build_llm_semantic_review_prompt_contract()
  ↓
PydanticAIReviewer.run_semantic_review()
  ↓
raw text output
  ↓
parse_llm_semantic_review_output()
  ↓
ValidatedLLMSemanticReviewOutput
```

This provider path now reuses the shared prompt builder and shared output
validator, but it still does not integrate into `content-review review`,
`content-review batch`, sidecar generation, or deterministic result merging.

Current single-file Markdown report boundary:

```text
ReviewResult
  ↓

Current provider-construction boundary:

```text
package-local reviewer provider name
  ↓
create_llm_reviewer("mock" | "pydantic-ai-testmodel")
  ↓
MockLLMReviewer / PydanticAITestModelReviewer

CLI/config-driven runtime provider config
  ↓
create_llm_reviewer(LLMProviderConfig, secret_value=None)
  ↓
MockLLMReviewer / PydanticAIReviewer
```

The reviewer-provider factory is construction only. It does not execute
review, read `.env`, load YAML config files, resolve secrets, or merge LLM
findings into the deterministic review pipeline.
Deterministic Markdown report sections

LLMSidecarResult sidecar
  ↓ optional explicit CLI opt-in
  -> success entries can include nested LLMReviewResult
LLM Markdown section

Current LLM config boundary:

```text
--llm-config YAML file
  ↓
load_llm_provider_config_file()
  ↓
LLMProviderConfig
  ↓ overridden by explicit CLI flags only
merge_llm_provider_config()
  ↓
Provider Factory / Reviewer
```

The LLM config loader is intentionally narrow:

- it validates only the LLM provider adapter fields
- it rejects unknown fields
- it rejects secret-like fields such as `api_key`, `secret`, `token`, or
  `password`
- it stores only `api_key_env`, not secret values
- it does not read environment variables
- it does not instantiate provider runtimes
- it does not make network calls

Current LLM smoke-check boundary:

```text
content-review llm-check
  ↓
optional --provider mock|pydantic-ai-testmodel
  ↓
create_llm_reviewer("<provider-name>")
  ↓
Synthetic minimal LLMReviewRequest
  ↓
Provider runtime smoke call

or

content-review llm-check
  ↓
LLMProviderConfig load + CLI override merge
  ↓
Optional secret resolution
  ↓
Provider Factory
  ↓
PydanticAIReviewer.run_construction_check()
  ↓ optional only when --live/--runtime
PydanticAIReviewer.run_live_check()
  ↓
Provider runtime smoke call
```

The smoke-check command is intentionally separate from `review` and `batch`:

- it does not load a review profile
- it does not read a Markdown article
- it does not generate sidecars
- it does not generate deterministic review output
- it does not affect quality-gate semantics
- `--provider` supports only `mock` and `pydantic-ai-testmodel`, fails
  explicitly for unsupported values, and does not fall back

Deterministic Markdown report + optional appended LLM section
```

Independent LLM sidecar Markdown report boundary:

```text
LLMSidecarResult
  ↓ optional explicit CLI opt-in
render_llm_sidecar_markdown_report
  ↓
Standalone LLM sidecar Markdown report
```

The optional Markdown integrations are presentation-only adapter boundaries:

Current batch sidecar boundary:

```text
Batch Markdown discovery
  ↓
Deterministic batch review
  ↓
BatchReviewResult
  = canonical deterministic batch output

Per reviewed Markdown file:
  Markdown content
    ↓
  LLMReviewRequest
    ↓
  LLMReviewRunner
    ↓
  explicit --llm-provider mock|pydantic-ai-testmodel
    ↓
  create_llm_reviewer("<provider-name>")
    or
  omitted --llm-provider
    ↓
  create_llm_reviewer(LLMProviderConfig)
    ↓
  LLMReviewResult
    ↓
  LLMSidecarResult per-file JSON under --llm-output-dir

Batch manifest:
  LLMSidecarResult summary under
  --llm-output-dir/llm-review-manifest.json
```

Current batch path guarantees:

- batch LLM sidecars are opt-in and generated only when `--enable-llm` is set
- each reviewed Markdown file gets an independent `LLMSidecarResult` JSON
  sidecar
- explicit batch `--llm-provider` supports only `mock` and
  `pydantic-ai-testmodel`, fails explicitly for unsupported values, and does
  not fall back
- explicit batch `--llm-provider` without batch sidecar output fails clearly
- omitted batch `--llm-provider` keeps the existing config-driven runtime path
- the sidecar path preserves the file path relative to the batch input
  directory and appends `.llm-review.json`
- each batch run also writes `llm-review-manifest.json` with aggregate status
  counts, per-file status entries, and success-entry nested `review` payloads
- the batch CLI can also render that manifest into a separate Markdown sidecar
  report through `--llm-markdown-output`
- a failed LLM review for one file is recorded in sidecar JSON and does not
  stop LLM sidecar generation for other files
- the canonical `BatchReviewResult` schema is unchanged
- deterministic batch Markdown reports remain deterministic-only
- batch quality gates still read only deterministic findings

- `render_markdown_report` can accept `llm_result: LLMReviewResult | None`
- `None` preserves the existing deterministic Markdown output exactly
- a provided `LLMReviewResult` appends `## LLM Review` after the deterministic
  sections
- LLM findings do not mutate `ReviewResult`
- LLM findings do not affect deterministic summary counts, rule counts, or
  `--fail-on`
- the separate `LLMSidecarResult` JSON sidecar is still written and remains
  the machine-readable contract
- the separate LLM sidecar Markdown report is derived from
  `LLMSidecarResult` and does not alter deterministic report structure

The current `LLMReviewFinding`, `LLMReviewSummary`, and `LLMReviewResult`
models exist so later tasks can add provider adapters, prompt versioning, and
conversion logic without changing the current deterministic review contract.

TASK-0035 adds the next provider-facing boundary:

```text
Markdown content
  ↓
LLMReviewRequest
  ↓
LLMReviewer
  ↓
LLMReviewResult
```

Current LLM provider-boundary status:

- `src/content_review_engine/llm/models.py` defines `LLMReviewRequest`
- `src/content_review_engine/llm/provider.py` defines a small synchronous
  `LLMReviewer` protocol
- `src/content_review_engine/llm/config.py` defines `LLMProviderConfig`,
  including provider name, optional model, optional `api_key_env`, optional
  `base_url`, optional runtime `timeout_seconds`, optional `retry_attempts`,
  optional `retry_backoff_seconds`, and optional
  `min_request_interval_seconds`
- `src/content_review_engine/llm/factory.py` defines the provider registry and
  `create_llm_reviewer(config, secret_value=None)`
- `src/content_review_engine/llm/secrets.py` defines the secret-resolution
  boundary; `resolve_llm_provider_secret(config, env=None)` resolves a secret
  string from `LLMProviderConfig.api_key_env`, while `resolve_llm_api_key(...)`
  wraps that value in a redacted `ResolvedLLMSecret`
- `src/content_review_engine/llm/smoke_check.py` now owns config-driven
  `llm-check` secret preflight by calling that shared resolver directly and
  rendering only the secret reference plus a redacted secret state; it then
  passes the resolved in-memory secret into the factory for local provider
  construction checks
- `src/content_review_engine/llm/mock.py` defines `MockLLMReviewer`, a
  deterministic adapter for tests and future wiring work
- `src/content_review_engine/llm/pydantic_ai_provider.py` defines
  `PydanticAITestModelReviewer`, a package-level `TestModel` adapter that
  reuses the existing request/response mapping boundary and returns normal
  `LLMReviewResult` values without API keys or network access
- `src/content_review_engine/llm/pydanticai.py` now implements the real
  provider adapter boundary for `pydanticai`; it can accept a pre-resolved
  secret for local construction checks or resolve one later during explicit
  runtime review, builds provider-local request payloads through the mapping
  layer, executes the PydanticAI runtime, passes optional timeout config to
  the underlying OpenAI-compatible client, keeps that client at
  `max_retries=0`, applies explicit project-level retry logic around the
  runtime call, applies optional instance-local request pacing before each
  real runtime call, maps structured responses back into `LLMReviewResult`,
  and normalizes runtime failures into stable provider error subclasses
- `src/content_review_engine/llm/pydanticai_errors.py` now defines the
  PydanticAI runtime classification boundary for timeout, auth, network,
  rate-limit, model, retry-exhausted, and unknown runtime failures
- `src/content_review_engine/llm/pydanticai_mapping.py` now defines the
  provider-local request builder, system/user prompt construction, structured
  response schema, response validation, and conversion back into
  `LLMReviewResult`
- the current runnable providers are `mock` and `pydanticai`
- `pydanticai` still performs CLI secret preflight before sidecar review

Secret resolver boundary:

- config validation does not resolve secrets
- reviewer factory construction does not resolve secrets
- CLI flag parsing does not resolve secrets
- smoke-check orchestration resolves secrets only through
  `resolve_llm_provider_secret(config, env=None)`
- smoke-check orchestration may then pass that resolved in-memory value into
  `create_llm_reviewer(config, secret_value=...)`
- the resolver reads only `api_key_env`
- the resolver can read from an explicit mapping for tests
- otherwise it reads the current process environment
- it does not read `.env`
- it does not read repository files
- it does not access the network
- it must not leak secret values into errors, sidecars, reports, or canonical
  result models
- config-driven `llm-check` may show the env var name and a redacted secret
  marker, but never the full secret
- config-driven `llm-check` now also reports `Construction: ok` and
  `Live call: not run` by default for construction-only verification
- reviewer-name factory execution does not fallback to `mock`

TASK-0036 adds the runner boundary:

```text
LLMReviewRequest
  ↓
LLMReviewRunner
  ↓
LLMReviewer
  ↓
LLMReviewResult
```

TASK-0037 and TASK-0038 add the first CLI plumbing for that boundary, but only
for an explicit single-file opt-in sidecar flow:

```text
content-review review
  ↓
Markdown Reader + Profile Loader
  ↓
Deterministic Review Pipeline
  ↓
ReviewResult

content-review review --enable-llm --llm-output <path>
  ↓
Reuse current Markdown input
  ↓
LLMReviewRequest
  ↓
LLMReviewRunner
  ↓
create_llm_reviewer(LLMProviderConfig)
  ↓
LLMReviewResult
  ↓
JSON sidecar file
```

Important current boundaries:

- the deterministic `ReviewResult` remains the main CLI output
- the LLM result is serialized separately as a sidecar JSON file
- the current Markdown report structure does not read the LLM sidecar
- the current quality gate does not read the LLM sidecar
- batch review does not participate in this LLM path
- provider config parsing and reviewer construction are confined to the
  sidecar adapter path
- the `pydanticai` adapter path now has an explicit dependency +
  secret-preflight boundary plus a runtime request/response mapping layer
- the runner does not read environment variables
- the deterministic review pipeline, canonical JSON schema, Markdown report,
  and batch flow do not depend on provider-specific secret resolution

Current `pydanticai` runtime boundary:

```text
LLMReviewRequest
  ↓
PydanticAIReviewMapper
  ↓
PydanticAIReviewRequestPayload
  ↓ PydanticAI runtime call
PydanticAIReviewResponse
  ↓
LLMReviewResult
```

Mapping-layer notes:

- prompt construction includes content, file path, profile name, review goal,
  sorted metadata, and explicit structured-output rules
- sensitive metadata keys such as `api_key`, `token`, `secret`, and
  `password` are redacted before entering the provider prompt
- response validation raises `LLMResponseValidationError` with stable field
  paths and without embedding full prompts, full article bodies, or secret
  values
- runtime exceptions are normalized into stable provider runtime errors such
  as `LLMProviderTimeoutError`, `LLMProviderAuthError`,
  `LLMProviderNetworkError`, `LLMProviderRateLimitError`,
  `LLMProviderModelError`, `LLMProviderRetryExhaustedError`, or fallback
  `LLMProviderRuntimeError`, without leaking secrets, full prompts, full
  article content, or tracebacks
- only timeout, network, and rate-limit failures are retryable; auth, secret,
  config, model, and response-validation failures fail immediately
- request pacing is instance-local, uses injectable monotonic clock + sleep
  functions for tests, does not create a queue, and does not coordinate across
  processes
- pacing is evaluated before every real runtime call, including retry calls
- retry backoff is applied first after a retryable failure; the next pacing
  check then sleeps only the remaining time needed to satisfy
  `min_request_interval_seconds`
- the mapping layer is provider-local; it does not change `LLMReviewResult`,
  `LLMSidecarResult`, deterministic review JSON, deterministic Markdown
  reports, or quality-gate behavior
- real provider usage is documented as a manual-verification workflow under
  `docs/LLM_PROVIDER_USAGE.md` plus committed safe fixtures under
  `examples/llm/pydanticai/`
- default automated tests and CI remain on the no-network path and do not
  require real provider secrets

TASK-0036 adds a dedicated execution boundary between request construction and
provider invocation:

```text
Markdown content
  ↓
LLMReviewRequest
  ↓
LLMReviewRunner
  ↓
LLMReviewer
  ↓
LLMReviewResult
```

Current LLM runner status:

- `src/content_review_engine/llm/runner.py` defines `LLMReviewRunner`
- the runner is intentionally small and only coordinates `run(request)` to
  `reviewer.review(request)`
- the runner receives its `LLMReviewer` dependency through constructor
  injection
- provider-layer `LLMReviewError` failures propagate unchanged
- `MockLLMReviewer` remains the deterministic test adapter for the runner
- `PydanticAITestModelReviewer` remains a separate package-level provider
  test adapter and is not registered as a CLI-selectable provider
- the runner is now wired only into the single-file CLI LLM sidecar flow
- `src/content_review_engine/llm/errors.py` defines minimal future-facing LLM
  error types

This layer is still isolated:

- no merge into the deterministic `ReviewResult`
- no Markdown report integration
- no batch review integration
- no quality-gate integration
- no API, MCP, or GUI integration
- no merged output with the current canonical `ReviewResult`

Future tasks must still decide whether LLM findings are converted into
`ReviewFinding`, whether they participate in quality gates, how suppression
works for them, and how confidence and rationale are displayed.

Current review pipeline:

- `review_document()` accepts already-loaded Markdown text and a loaded `ReviewProfile`.
- The pipeline runs deterministic rules in memory through the rule runner.
- The default registry currently registers the deterministic `forbidden_terms`
  rule as default-enabled.
- The deterministic `absolute_claims` rule is registered as opt-in through
  `ReviewProfile.enabled_rules` or rule-style YAML configuration.
- The deterministic `markdown_structure` rule is registered as opt-in through
  `ReviewProfile.enabled_rules`.
- The deterministic `markdown_links_images` rule is also registered as opt-in
  through `ReviewProfile.enabled_rules`.
- Profile-configured `regex_rules` run deterministically from the active
  profile and are not stored in the built-in metadata registry because their
  `rule_id` values are dynamic.
- The pipeline returns a canonical `ReviewResult`.
- The pipeline parses supported Markdown inline suppression comments after rule
  execution and filters suppressed findings before creating the
  `ReviewResult`.

Current report generation:

- `render_markdown_report()` accepts a `ReviewResult` and renders a Markdown report.
- `render_batch_markdown_report()` accepts a `BatchReviewResult` and renders a batch Markdown report.
- The report renderer does not run rules, read Markdown files, or write output files.

Current quality gate support:

- `content_review_engine.core.quality_gate` defines canonical severity ordering:
  `info < warning < error < critical`.
- The CLI adapter evaluates `ReviewSummary.severity_counts` or
  `BatchReviewSummary.severity_counts` after rendering succeeds.
- Because inline suppression is applied before summaries are computed, quality
  gates evaluate only unsuppressed findings.
- `ReviewResult` and `BatchReviewResult` schemas are unchanged by quality-gate
  evaluation.

Current profile validation support:

- `content_review_engine.config.validate_profile` reuses the existing
  `load_profile()` path and adds a thin validation-result wrapper for CLI use.
- The `profile validate` command does not run review rules against Markdown
  content.
- Invalid, missing, unreadable, or unparsable profiles return exit code `2`,
  which stays separate from quality-gate exit code `1`.

---

## Adapter Responsibility

Adapters should only call the core package.

Adapters include:

- CLI
- Skill
- MCP Server
- FastAPI backend
- Frontend

Adapters must not duplicate core review logic.

The CLI adapter only orchestrates existing helpers. It does not implement parsing, profile loading, or review rules itself.

---

## Forbidden Architecture

Do not do this:

```text
CLI contains review logic
MCP contains separate review prompt
API contains separate review pipeline
Skill contains business logic
```

Correct design:

```text
Markdown Reader
    ↓
Profile Loader
    ↓
Review Pipeline
    ↓
Deterministic Rules
    ↓
Review Result / Findings
```

Current adapter boundary:

```text
CLI / MCP / API / Skill
        ↓
content_review_engine core package
```

The current implementation includes a minimal CLI adapter, but still does not include LLM review, API, MCP, persistence, or frontend layers.
