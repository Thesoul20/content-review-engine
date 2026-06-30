# LLM Provider Usage

## Overview

This project supports an optional LLM sidecar review path that is separate from
the deterministic review pipeline.

- Deterministic review remains the canonical `ReviewResult` and
  `BatchReviewResult` output.
- Single-file `content-review review --enable-llm --llm-output ...` now writes
  separate raw `LLMReviewResult` JSON.
- Batch sidecars still use `LLMSidecarResult` envelopes and are unchanged by
  TASK-0069.
- `--report-index` can summarize deterministic output plus optional LLM output,
  but it remains a separate Markdown guide and not a schema-bearing result.
- LLM findings do not change deterministic JSON, deterministic Markdown
  reports, or `--fail-on` quality-gate behavior.
- LLM findings are advisory semantic review suggestions from the LLM layer.
- LLM advisory severity is display-only and does not change deterministic
  hard-rule outcomes.
- LLM report presentation normalizes advisory severity to
  `critical`, `error`, `warning`, `info`, or `unknown`.
- missing or blank LLM `rule_id` is displayed as `llm.semantic_review`.
- confidence is optional in presentation; missing values display as
  `not provided`.
- LLM Markdown reports now also render a `Manual Review Checklist` with
  stable IDs such as `LLM-001`, default `needs_review` status, default
  `pending` decision, and default `quality gate = no`.
- Batch partial-failure LLM Markdown reports now also render an
  `LLM Execution Review Checklist` with stable IDs such as `LLM-ERR-001`,
  default `needs_rerun` status, and default suggested action
  `rerun_llm_review`.
- The core package now also includes an internal LLM-to-core finding adapter
  that can normalize `LLMReviewResult` into `LLMCoreFindingCandidate` values
  for future merge work, while keeping provider behavior, sidecar JSON, CLI
  defaults, and quality-gate behavior unchanged.
- The core package now also includes a separate single-file combined-review
  envelope builder that can package deterministic `ReviewResult`, optional raw
  `LLMReviewResult`, adapter-derived candidates, and explicit LLM status/error
  metadata for future integration work without changing CLI default output or
  existing sidecar schemas.
- The repository also includes committed artifact examples under
  `examples/llm_review_artifacts/` for single-file output, batch output,
  partial failure, advisory policy, manual review checklist output, and report
  index interpretation.

## LLM semantic review prompt contract

The repository now also includes an internal LLM semantic review prompt
contract in `src/content_review_engine/llm/prompt_contract.py`.

Purpose:

- define stable system prompt and user prompt text before review-path
  integration
- define a stable JSON-only output contract for future semantic review
- keep prompt construction separate from provider construction, provider
  execution, and output validation

Current boundaries:

- this contract does not execute a real provider call
- this contract does not itself call the CLI adapter; single-file CLI
  integration now happens later through the dedicated LLM runner
- prompt construction remains separate from output parsing, output validation,
  and `LLMReviewResult` generation
- Prompt construction does not read `.env`, does not read `os.environ`, and does not access the network.

Current prompt output contract:

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

Prompt rules:

- Return JSON only.
- `schema_version` must be `llm-semantic-review-output.v1`.
- `findings` must always be an array and must be `[]` when there are no issues.
- each finding `rule_id` must start with `llm.`
- `severity` is restricted to `info, warning, error, critical`
- `evidence` must quote a short source snippet
- `suggestion` must be actionable

The prompt contract currently asks the model to focus on semantic risk areas
such as exaggeration, misleading wording, unsupported claims, risky advice,
ambiguity, inappropriate tone, and cases that need human review.

## LLM semantic review output validation

The repository now also includes an internal semantic-review output validation
layer in `src/content_review_engine/llm/output_validation.py`.

Purpose:

- parse raw model output without calling a provider
- accept either pure JSON or a single fenced `json` block
- validate `schema_version`, `summary`, and `findings`
- validate each finding field with stable path-based error messages

Current helpers:

- `extract_llm_semantic_review_json(raw_output)`
- `parse_llm_semantic_review_output(raw_output)`
- `validate_llm_semantic_review_output(data)`

Current validation rules:

- `schema_version` must be `llm-semantic-review-output.v1`
- `summary` must be a non-empty string
- `findings` must be an array and may be empty
- `findings[].rule_id` must start with `llm.`
- `findings[].severity` must be one of `info`, `warning`, `error`, `critical`
- `findings[].line` and `findings[].column` must be integers greater than or
  equal to `1`, or `null`
- `findings[].message`, `findings[].evidence`, and
  `findings[].suggestion` must be non-empty strings
- `findings[].confidence` must be a number in the inclusive range `0..1`, or
  `null`

Current guarantees:

- the parser and validator do not call a provider
- the parser and validator do not read `.env`
- the parser and validator do not read `os.environ`
- the parser and validator do not resolve secrets
- the parser and validator do not access the network
- the parser and validator do not auto-fix malformed JSON
- the parser and validator do not auto-fill missing fields
- the parser and validator do not coerce string confidence values
- the validated output is not the same thing as `LLMReviewResult`
- parse and validation errors do not include the full raw output or secret-like values

## PydanticAI semantic review execution

`PydanticAIReviewer` now also exposes `run_semantic_review(request)`.

Execution flow:

```text
LLMReviewRequest
  ↓
build_llm_semantic_review_prompt_contract()
  ↓
PydanticAIReviewer.run_semantic_review()
  ↓
raw model output
  ↓
parse_llm_semantic_review_output()
  ↓
ValidatedLLMSemanticReviewOutput
```

Current guarantees:

- provider execution reuses the shared prompt contract and does not build a
  second prompt format inside the provider
- provider execution reuses `parse_llm_semantic_review_output()` and does not
  duplicate JSON parsing or schema validation inside the provider
- success accepts either pure JSON or a single fenced `json` block
- provider execution errors remain separate from output parse and validation
  errors
- `run_semantic_review()` returns `ValidatedLLMSemanticReviewOutput`, not
  `LLMReviewResult`
- `run_semantic_review()` is now reused by both `content-review review` and `content-review batch`
- `run_semantic_review()` still does not change deterministic quality-gate
  behavior
- provider execution does not inject the API secret into the prompt, the
  validated output, or stable error messages
- default tests for this path use fake/stub runtime calls and must not access
  the real network or require a real API key

## Validated LLM semantic output to LLMReviewResult conversion

The repository now also includes a separate conversion helper in
`src/content_review_engine/llm/result_conversion.py`.

Current helper:

- `convert_validated_semantic_output_to_llm_review_result(output, request, *, provider=None, model=None)`

Execution flow:

```text
ValidatedLLMSemanticReviewOutput
  ↓
convert_validated_semantic_output_to_llm_review_result()
  ↓
LLMReviewResult
```

Current mapping rules:

- `rule_id` is copied as-is and the `llm.` prefix is preserved
- `severity` is copied as-is and is not rewritten
- `line` and `column` are copied as-is and are not inferred when missing
- `message` is copied to `LLMReviewFinding.message`
- `evidence` is copied to `LLMReviewFinding.matched_text`
- `suggestion` is copied to `LLMReviewFinding.suggestion`
- numeric `confidence` is copied as-is
- `confidence: null stays null`
- validated output `summary` is copied to `LLMReviewSummary.summary`
- `provider`, `model`, and `profile_name` stay on the existing
  `LLMReviewResult` fields
- the validated output schema version is stored in result metadata as
  `semantic_output_schema_version`

Current guarantees:

- the conversion helper does not call a provider
- The conversion helper does not call a provider, does not read `os.environ`, and does not access the network.
- the conversion helper does not read `.env`
- the conversion helper does not modify the validated input object or the
  request object
- the conversion helper does not output secrets
- `run_semantic_review()` still returns `ValidatedLLMSemanticReviewOutput`
  and does not directly return `LLMReviewResult`
- this conversion layer is now reused by both `content-review review` and
  `content-review batch`
- this conversion layer still does not change deterministic Quality Gate
  behavior

## LLMReviewResult to core finding candidate adaptation

The repository now also includes a separate adapter layer in
`src/content_review_engine/llm/finding_adapter.py`.

Current helpers:

- `adapt_llm_review_result_to_core_finding_candidates(result)`
- `adapt_llm_finding_to_core_finding_candidate(finding, *, original_index=None)`
- `build_llm_core_rule_id(value, *, fallback_value=None)`
- `normalize_llm_core_finding_severity(value)`

Execution flow:

```text
LLMReviewResult
  ↓
adapt_llm_review_result_to_core_finding_candidates()
  ↓
list[LLMCoreFindingCandidate]
```

Current mapping rules:

- provider output remains `LLMReviewResult`
- the adapter can normalize that `LLMReviewResult` into internal candidates
- candidate `source` is always `llm`
- candidate `advisory` is always `True`
- candidate `rule_id` always starts with `llm.`
- canonical severities stay the same
- `high -> error`
- `medium -> warning`
- `low -> info`
- unknown, blank, or missing severity falls back to `warning`
- `message`, `suggestion`, `line`, `column`, `matched_text`, `category`, and
  original finding order are preserved when present
- current adapter context is copied from `LLMReviewFinding.rationale`

Current guarantees:

- the adapter is a pure conversion layer
- the adapter does not call a provider
- the adapter does not change the provider contract
- the adapter does not change raw `LLMReviewResult` JSON sidecars
- the adapter does not change `LLMSidecarResult`
- the adapter does not change deterministic JSON or deterministic Markdown
  reports
- the adapter does not merge LLM findings into `ReviewResult.findings`
- the adapter does not make LLM findings participate in deterministic
  `severity_counts`, `rule_counts`, quality gate, or exit code
- mock and real-provider integration behavior stays unchanged

## Single-file combined review result envelope

The repository now also includes a separate internal single-file combined
review envelope in `src/content_review_engine/llm/combined_result.py`.

Current helpers:

- `build_single_file_combined_review_result(...)`
- `single_file_combined_review_result_to_dict(...)`

Execution flow:

```text
ReviewResult
  + optional LLMReviewResult
  + optional structured LLM error
  ↓
build_single_file_combined_review_result()
  ↓
SingleFileCombinedReviewResult
  ↓
single_file_combined_review_result_to_dict()
```

Current schema and status rules:

- top-level schema version is `single-file-combined-review-result.v1`
- `llm.status` is one of `not_run`, `skipped`, `succeeded`, or `failed`
- `llm.advisory` is always `true`
- `succeeded` requires raw `LLMReviewResult`
- `failed` requires structured `llm_error` and keeps
  `llm.finding_candidates = []`
- failed `llm_error` can include `type`, `message`, `provider`, and
  `retryable`
- the error payload must not include secrets, API keys, or raw sensitive config

Current serialization guarantees:

- nested deterministic data reuses `review_result_to_dict(...)`
- nested raw LLM data reuses `llm_review_result_to_dict(...)`
- each candidate is derived through
  `adapt_llm_review_result_to_core_finding_candidates(...)`
- candidate `source` is always `llm`
- candidate `advisory` is always `True`
- the combined envelope is JSON-compatible
- deterministic result payloads are preserved unchanged
- raw single-file `LLMReviewResult` JSON sidecars are unchanged
- batch `LLMSidecarResult` JSON sidecars are unchanged
- deterministic JSON and Markdown reports do not include LLM findings
- quality gate still uses deterministic review only

Current boundary guarantees:

- this envelope is not CLI default output
- this envelope does not change `ReviewResult.findings`
- this envelope does not let LLM findings participate in deterministic
  `severity_counts`, `rule_counts`, quality gates, or exit codes
- this envelope does not call a provider, does not read `os.environ`, and
  does not access the network
- this envelope does not read or write files

## Single-file CLI LLM integration

Single-file `content-review review` now has a dedicated LLM runner path:

```text
CLI flags
  ↓
LLMProviderConfig
  ↓
resolve_llm_provider_secret(config, env=None)
  ↓
create_llm_reviewer(config, secret_value=...)
  ↓
run_semantic_review(request)
  ↓
convert_validated_semantic_output_to_llm_review_result()
  ↓
LLMReviewResult JSON sidecar
```

Current guarantees:

- `--enable-llm` is required before any single-file LLM call happens
- `--llm-output` writes raw `LLMReviewResult` JSON, not `LLMSidecarResult`
- `--llm-report` writes a separate Markdown report rendered from the same
  `LLMReviewResult`
- `--report-index` may be written with or without LLM enabled, but it never
  enables LLM review by itself
- `--report-index` does not replace `--llm-output` or `--llm-report`
- `--llm-output` and `--llm-report` can be used together
- `--llm-report` can also be used without `--llm-output`
- the sidecar JSON does not include secrets, prompt text, or raw provider output
- deterministic stdout does not include LLM findings
- deterministic JSON and Markdown reports do not include LLM findings
- the report index states explicitly that quality gate still uses deterministic
  review only
- the committed examples in `examples/llm_review_artifacts/` are reference
  artifacts only; they do not add fields to `LLMReviewResult`,
  `LLMSidecarResult`, `ReviewResult`, or `BatchReviewResult`
- quality gate still uses deterministic review only
- the separate LLM Markdown report now marks each finding with
  `source = llm`, `advisory = yes`, and `quality gate participation = no`
- the separate LLM Markdown report now also includes `## Manual Review Checklist`
  with stable report-local checklist IDs, severity-derived priority, default
  `needs_review` status, default `pending` decision, and default
  `quality gate = no`
- LLM `critical` or `error` findings remain advisory and do not become
  deterministic hard-rule failures
- `--include-llm-report` is not supported for single-file review
- `--llm-provider pydanticai` requires `--llm-model` and `--llm-api-key-env`
- missing, unset, or empty env vars fail before any real provider call
- provider execution failures, parse failures, validation failures, and sidecar write failures return exit code `2`
- ordinary tests for this path use fake/stub reviewers and must not access the real network or require a real API key

## Provider Classes

Current test providers:

- `mock`: safe for local tests and CI, requires no API key, performs no
  network calls.
- `pydantic-ai-testmodel`: package-level testing provider built on
  `pydantic_ai.models.test.TestModel`, requires no API key, performs no
  network calls, and is available to `llm-check --provider` through the
  package reviewer factory.

Current config-driven runtime provider:

- `pydanticai`: existing adapter-backed runtime path, requires an API key
  through an environment variable, can call an external OpenAI-compatible
  endpoint, and should be used only for explicit manual verification.

## Report Index Boundary

`content-review review` and `content-review batch` now also support
`--report-index`.

Current guarantees:

- report index rendering is presentation-only Markdown
- report index does not change deterministic JSON output
- report index does not change raw `LLMReviewResult` JSON
- report index does not change aggregate `LLMSidecarResult` JSON
- report index does not merge LLM findings into deterministic findings
- report index does not make LLM findings participate in quality gate
- report index repeats that LLM findings are advisory semantic review
  suggestions and that deterministic review remains the only gate source
- when LLM is disabled, the index renders a stable `LLM not enabled` summary
- when batch LLM review has partial failures, the index records an LLM file
  status summary plus a compact LLM error summary
- report index now also includes a `Manual Review Workflow` section that
  explains checklist-only semantics, non-persistence of checklist status and
  decision values, and rerun-oriented handling for batch execution failures

Current reserved real providers:

- `openai`
- `anthropic`
- `gemini`
- `deepseek`
- `qwen`
- `local`

Reserved real provider names such as `openai` or `anthropic` must not be used
yet. They are reserved but not implemented yet. Unsupported provider names are
handled separately and still fail as unknown providers.

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
config_reviewer = create_llm_reviewer(config, secret_value="replace-with-your-real-key")
```

Factory behavior:

- `create_llm_reviewer("mock")` returns `MockLLMReviewer`
- `create_llm_reviewer("pydantic-ai-testmodel")` returns
  `PydanticAITestModelReviewer`
- `create_llm_reviewer(config, secret_value=...)` can now construct the real
  config-driven `PydanticAIReviewer` without asking the factory to resolve the
  secret itself
- reserved real provider names such as `openai` raise a clear
  not-implemented error and do not silently fall back
- unsupported provider names raise a clear unknown-provider error and do not
  silently fall back
- this factory path does not read `.env`, does not require an API key, and
  does not access the network for the supported reviewer providers above
- for config-driven `pydanticai`, provider construction also stays local and
  does not access the network; the live call remains a separate later step

In short: provider construction also stays local and does not access the network.

Current provider validation contract:

- test providers validate without API keys
- reserved real providers fail before any `.env` read, API-key lookup, or
  network access
- unsupported provider names fail as unknown providers

This is a package boundary for future adapters. `llm-check --provider` now
reuses it for the safe local reviewer providers above. Single-file
`content-review review --enable-llm --llm-output ... --llm-provider <name>`
and batch `content-review batch --enable-llm --llm-output ...
--llm-provider <name>` now also reuse it for those same safe local reviewer
providers. It still does not change the default behavior of `review`,
`batch`, or `llm-check` when `--llm-provider` is omitted.

## PydanticAI TestModel Provider

`PydanticAITestModelReviewer` exists to test the project's `LLMReviewer`
boundary without real provider credentials or runtime network access.

Use it when you need:

- a provider implementation that accepts `LLMReviewRequest`
- stable prompt/request construction through the existing PydanticAI mapping
- a returned `LLMReviewResult` instead of raw PydanticAI output
- local unit tests that do not depend on `.env`, shell secrets, or remote APIs

Current limitations:

- it is available only through the package-level reviewer provider factory and
  CLI paths that explicitly opt into that reviewer-name factory boundary:
  `llm-check --provider` and single-file `review --enable-llm --llm-output ...
  --llm-provider pydantic-ai-testmodel`, plus batch
  `batch --enable-llm --llm-output ... --llm-provider pydantic-ai-testmodel`
- it does not read `LLMProviderConfig`
- omitted `--llm-provider` still leaves batch sidecar review on the
  config-driven path
- it should not be treated as a production LLM integration

## LLM Check Command

Use `llm-check` when you want to validate provider setup without mixing that
verification into `review` or `batch`.

Examples:

```bash
uv run content-review llm-check
uv run content-review llm-check --provider mock --live
uv run content-review llm-check --provider pydantic-ai-testmodel --live
uv run content-review llm-check --llm-config examples/llm/mock/llm-provider.yml
uv run content-review llm-check --llm-config examples/llm/pydanticai/llm-provider.yml
uv run content-review llm-check --llm-config examples/llm/pydanticai/llm-provider.yml --live
uv run content-review llm-check --llm-provider pydanticai --llm-model openai:gpt-4o-mini --llm-api-key-env OPENAI_API_KEY
```

Default behavior:

- config check
- secret check when the provider requires one
- local provider construction check when the provider supports it
- no live provider call
- successful secret checks print `API key env: ...`, `API key: <redacted>`,
  and `Secret: resolved`
- providers that do not require a secret print `Secret: not required`
- successful construction checks print `Construction: ok`
- default output also prints `Live call: not run`
- live failures print `Live call: failed` plus a stable `Reason: ...`
- failures may name the missing env var reference, but they do not print the
  secret value

`--provider` behavior:

- supports only `mock` and `pydantic-ai-testmodel`
- uses `create_llm_reviewer()` directly instead of config-driven provider construction
- does not require an API key
- does not read `.env`
- does not access the network for the supported factory providers
- reserved real provider names fail as reserved-but-not-implemented and do not
  fall back to config or `mock`
- unsupported provider names fail explicitly as unknown providers and do not
  fall back to config or `mock`

`--live` behavior:

- `--live` is the explicit opt-in live runtime smoke switch; `--runtime` is
  kept as a compatible alias
- for `mock` and `pydantic-ai-testmodel`, it still runs the existing local
  synthetic `LLMReviewRequest`
- for config-driven `pydanticai`, it runs a provider-specific minimal smoke
  prompt: `Reply with exactly: ok`
- does not read a real article or review profile
- does not write sidecars or deterministic review output
- may access the real provider for `pydanticai`
- may incur provider cost for `pydanticai`

Use `--live` only for explicit manual verification.

## PydanticAI Provider

Use config-driven `pydanticai` only when you intentionally want a real LLM
sidecar review through the shared config-driven provider path.

Provider parameters covered by the current CLI:

- `--llm-config examples/llm/pydanticai/llm-provider.yml`
- `--llm-model openai:gpt-4o-mini`
- `--llm-api-key-env OPENAI_API_KEY`
- `--llm-base-url https://your-openai-compatible-endpoint.example/v1`
- `--llm-timeout-seconds 30`
- `--llm-retry-attempts 2`
- `--llm-retry-backoff-seconds 1.0`
- `--llm-min-request-interval-seconds 2.0`

`--llm-model` is required for `pydanticai`.
`--llm-api-key-env` stores only the environment variable name, not the secret
value itself. `api_key_env` is a secret reference, not a secret value.
In short: api_key_env is a secret reference.
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
For `review` and `batch`, explicit `--llm-provider` is reserved for the
reviewer-factory names `mock` and `pydantic-ai-testmodel`; real `pydanticai`
stays on the existing omitted-`--llm-provider` config-driven path.
Direct CLI provider names for future real providers such as `openai`,
`anthropic`, `gemini`, `deepseek`, `qwen`, and `local` are still not
supported.

## Secret Resolver Contract

Future real-provider secret lookup is centralized in the shared secret
resolver boundary in `src/content_review_engine/llm/secrets.py`.
This secret resolver contract is internal-only.

Current helper surface:

- `resolve_llm_provider_secret(config, env=None) -> str`
- `resolve_llm_api_key(config, env=None) -> ResolvedLLMSecret`

Contract:

- the resolver reads `LLMProviderConfig.api_key_env`
- `api_key_env` is a secret reference, not a secret value
- when `env` is provided, resolution reads only that mapping
- when `env` is omitted, resolution reads the current process environment
- it does not read `.env`
- it does not read repository files
- it does not access the network
- it does not print or serialize secret values
- missing `api_key_env` raises a structured secret-reference error
- unset env vars raise a structured secret error
- empty env vars raise a structured secret error

Missing `api_key_env` fails before any real provider call.
Empty env vars also fail before any real provider call.
Reserved real provider names such as `openai` or `anthropic` still remain
unavailable after this task; the resolver contract only prepares the future
boundary.

Current `llm-check` behavior on top of that resolver:

- `llm-check` reuses `resolve_llm_provider_secret(config, env=None)` directly
  for config-driven secret preflight
- after secret preflight, `llm-check` passes the resolved in-memory secret to
  `create_llm_reviewer(config, secret_value=...)`
- the provider factory does not resolve the secret, does not read `.env`, and
  does not read `os.environ`
- config-driven `pydanticai` then performs a local construction-only agent
  build that does not execute a live model call unless `--live` is explicitly
  enabled
- `llm-check` reuses `redact_secret_value()` for the displayed secret state
- `llm-check` prints the env var name and `<redacted>`, never the full secret
- `llm-check` does not read `.env` and does not fallback to a plaintext
  `--api-key` or `--llm-api-key` flag

## Single-file Sidecar Provider Selection

Use explicit single-file `--llm-provider` only with the single-file
`--enable-llm --llm-output ...` path:

```bash
uv run content-review review article.md --profile profile.yml --enable-llm --llm-output article.llm.json --llm-provider mock
uv run content-review review article.md --profile profile.yml --enable-llm --llm-output article.llm.json --llm-provider pydanticai --llm-model openai:gpt-4o-mini --llm-api-key-env OPENAI_API_KEY
uv run content-review review article.md --profile profile.yml --enable-llm --llm-output article.llm.json --llm-provider pydantic-ai-testmodel
```

Behavior:

- explicit single-file `--llm-provider mock` and
  `--llm-provider pydantic-ai-testmodel` use the safe local reviewer path
- explicit single-file `--llm-provider pydanticai` uses config-driven
  provider construction plus secret resolution and semantic review execution
- reserved real provider names fail clearly as reserved but not implemented
- unsupported explicit provider names fail clearly as unknown providers and do
  not fall back
- `--llm-provider` without the sidecar path fails clearly
- omitting explicit `--llm-provider` keeps the existing single-file default
  provider behavior unchanged
- explicit single-file local test providers do not require an API key, do not
  read `.env`, and do not access the network
- explicit single-file `pydanticai` requires `--llm-model` and
  `--llm-api-key-env`

## Batch Sidecar Provider Selection

Use explicit batch `--llm-provider` only with the batch sidecar path:

```bash
uv run content-review batch articles --profile profile.yml --recursive --enable-llm --llm-output batch.llm.json --llm-provider mock
uv run content-review batch articles --profile profile.yml --recursive --enable-llm --llm-output batch.llm.json --llm-provider pydantic-ai-testmodel
uv run content-review batch articles --profile profile.yml --recursive --enable-llm --llm-output batch.llm.json --llm-provider pydanticai --llm-model openai:gpt-4o-mini --llm-api-key-env OPENAI_API_KEY
```

Behavior:

- explicit batch `--llm-provider` supports `mock`, `pydanticai`, and `pydantic-ai-testmodel`
- explicit batch `--llm-provider` reuses the same reviewer construction path as single-file review
- reserved real provider names fail clearly as reserved but not implemented
- unsupported explicit provider names fail clearly as unknown providers and do
  not fall back
- `--llm-provider` without the batch sidecar path fails clearly
- omitting explicit batch `--llm-provider` keeps the config-driven batch sidecar behavior unchanged
- explicit batch `--llm-provider mock` and `--llm-provider pydantic-ai-testmodel`
  do not require an API key, do not read `.env`, and do not access the network
- explicit batch `--llm-provider pydanticai` requires `--llm-model` and `--llm-api-key-env`
- explicit sidecar writes `llm_provider_source: explicit`
- omitted `--llm-provider` writes `llm_provider_source: default` or `config`
  and still records the concrete `llm_provider` name in the sidecar envelope

## Sidecar Provider Metadata

`LLMSidecarResult` JSON now uses schema version `llm-sidecar-result.v2` and
adds two top-level envelope fields:

- `llm_provider`: the provider name used for this sidecar run, such as
  `mock`, `pydantic-ai-testmodel`, or `pydanticai`
- `llm_provider_source`: how that provider was selected

Current `llm_provider_source` values:

- `explicit`: the user passed `--llm-provider`
- `default`: the user omitted `--llm-provider` and the sidecar used the
  built-in default provider path
- `config`: the user omitted `--llm-provider` and the sidecar provider came
  from `--llm-config`

These fields belong only to the sidecar envelope. They do not appear in
`ReviewResult`, `BatchReviewResult`, or the deterministic Markdown report.

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
  --llm-report /tmp/content-review-single.llm.md
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
  --llm-output /tmp/content-review-batch-llm.json \
  --llm-report /tmp/content-review-batch-llm.md
```

What to verify:

1. `/tmp/content-review-batch-llm.json` exists.
2. `/tmp/content-review-batch-llm.md` exists.
3. The JSON sidecar contains one `files[]` entry per Markdown file.
4. A failed LLM file, if any, is recorded in the sidecar output without
   changing deterministic batch quality-gate semantics.

## Sidecar JSON Output

Single-file and batch LLM sidecars now differ:

- single-file `--llm-output` writes raw `LLMReviewResult`
- Batch `--llm-output` writes one aggregate `LLMSidecarResult` JSON sidecar

Check:

- single-file top-level `schema_version` is `llm-review-result.v1`
- batch top-level `schema_version` is `llm-sidecar-result.v2`
- `summary.file_count`, `summary.succeeded_count`, `summary.failed_count`,
  `summary.skipped_count`, and `summary.finding_count` are present
- each `files[]` entry has `path`, `status`, and either `review` or `error`
- successful `review` entries include provider/model metadata plus findings
- failed entries expose only stable `error_type` and message fields

Useful inspection commands:

```bash
uv run python -m json.tool /tmp/content-review-single.llm.json
uv run python -m json.tool /tmp/content-review-batch-llm.json
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
