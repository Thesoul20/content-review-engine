# CLI

Start with [docs/QUICKSTART.md](./QUICKSTART.md) for the first-run workflow
from `uv sync` through `review`, `batch`, Markdown reports, and CI-oriented
exit codes.

For real-provider setup, manual verification fixtures, sidecar inspection, and
runtime troubleshooting, see [docs/LLM_PROVIDER_USAGE.md](./LLM_PROVIDER_USAGE.md).

For a committed runnable demo workspace using the current CLI contract, see
[`examples/demo/README.md`](../examples/demo/README.md).

For committed single-file and batch LLM artifact examples that show
deterministic reports, LLM sidecars, LLM Markdown reports, report indexes,
advisory policy, manual review checklists, and batch partial failure
presentation, see
[`examples/llm_review_artifacts/README.md`](../examples/llm_review_artifacts/README.md).

For rule-system details such as supported `rule_id` values, severity ordering,
suppression comments, counts, and quality gates, see
[docs/RULES.md](./RULES.md), the canonical rule reference.

## Current Command

```bash
uv run content-review review <markdown_file> --profile <profile_file> [--format text|json|markdown] [--output <file>] [--report-index <file>] [--combined-output <file>] [--combined-output-format json|markdown] [--fail-on info|warning|error|critical] [--enable-llm [--llm-output <file>] [--llm-report <file>] [--llm-config <path>] [--llm-provider mock|pydanticai|pydantic-ai-testmodel] [--llm-model <name>] [--llm-api-key-env <env>] [--llm-base-url <url>] [--llm-timeout-seconds <seconds>] [--llm-retry-attempts <count>] [--llm-retry-backoff-seconds <seconds>] [--llm-min-request-interval-seconds <seconds>]]
uv run content-review batch <input_dir> --profile <profile_file> [--format text|json|markdown] [--output <file>] [--report-index <file>] [--recursive] [--pattern "*.md"] [--fail-on info|warning|error|critical] [--enable-llm [--llm-output <file>] [--llm-report <file>] [--llm-config <path>] [--llm-provider mock|pydanticai|pydantic-ai-testmodel] [--llm-model <name>] [--llm-api-key-env <env>] [--llm-base-url <url>] [--llm-timeout-seconds <seconds>] [--llm-retry-attempts <count>] [--llm-retry-backoff-seconds <seconds>] [--llm-min-request-interval-seconds <seconds>]]
uv run content-review llm-check [--provider mock|pydantic-ai-testmodel] [--llm-config <path>] [--llm-provider mock|pydanticai] [--llm-model <name>] [--llm-api-key-env <env>] [--llm-base-url <url>] [--llm-timeout-seconds <seconds>] [--llm-retry-attempts <count>] [--llm-retry-backoff-seconds <seconds>] [--llm-min-request-interval-seconds <seconds>] [--live|--runtime]
uv run content-review profile validate <profile_file> [--format text|json]
uv run content-review profile init --template <general-basic|general-publishing|health-content|marketing-copy|technical-blog|wechat-basic|wechat-article|wechat-strict> --output <profile_file> [--force]
uv run content-review profile list [--format text|json]
```

The CLI is a thin adapter over the core review pipeline.
It reads Markdown, loads a YAML profile, runs deterministic rules, and prints or exports the canonical `ReviewResult`.
The batch command reuses the same pipeline for each discovered Markdown file and returns a canonical `BatchReviewResult`.
The profile validation command reuses the existing profile loader and registry checks and returns a canonical `ProfileValidationResult`.
The profile init command creates a new editable YAML profile from one built-in template and keeps validation on the existing loader path.
The profile list command exposes the same built-in template registry used by `profile init` and returns either text output or a canonical `profile-template-list.v1` JSON payload.
The `llm-check` command validates LLM provider config, secret resolution,
provider construction, and optional runtime reachability without reading
article content, loading a review profile, or writing sidecars.
The committed files under `examples/llm_review_artifacts/` are reference
artifacts only. They do not change CLI behavior, enable LLM review, or
replace the canonical deterministic JSON schemas.
The package now also has an internal batch combined-result envelope builder,
but the batch CLI does not expose a combined-output flag and current batch
default output remains unchanged.

## Review Output Index

`review` and `batch` now also support `--report-index <path>`.

Purpose:

- write one separate Markdown navigation file that explains which deterministic
  and optional LLM outputs were produced
- summarize deterministic findings plus optional LLM findings at a glance
- explain interpretation boundaries such as canonical status and quality-gate
  source

Current guarantees:

- `--report-index` does not change `ReviewResult`, `BatchReviewResult`,
  `LLMReviewResult`, or `LLMSidecarResult`
- `--report-index` does not enable LLM review by itself
- `--report-index` does not satisfy the `--enable-llm` requirement for
  `--llm-output` or `--llm-report`
- `--report-index` does not replace `--output`, `--llm-output`, or
  `--llm-report`
- the index is a human-readable guide only and is not a full combined report
- the repository now also has a package-level combined single-file output
  path behind explicit `--combined-output`, but it does not change any CLI
  default output
- there is still no batch `--combined-output`; batch combined results remain
  internal package helpers only
- quality gate still reads deterministic findings only
- when LLM output is present, the index marks it as `source = llm`,
  `advisory = yes`, and `quality gate participation = no`
- LLM severity shown in LLM reports or the report index is advisory severity
  only and does not map to deterministic hard-rule failure
- the index now also includes a `Manual Review Workflow` section that explains
  checklist-only human follow-up semantics and, for batch partial failures,
  rerun-oriented execution review items

## LLM Smoke Check

Use `llm-check` for provider setup verification only.
It is not a review command.

Examples:

```bash
uv run content-review llm-check
uv run content-review llm-check --provider mock --live
uv run content-review llm-check --provider pydantic-ai-testmodel --live
uv run content-review llm-check --llm-config examples/llm/mock/llm-provider.yml
uv run content-review llm-check --llm-config examples/llm/pydanticai/llm-provider.yml
uv run content-review llm-check --llm-config examples/llm/pydanticai/llm-provider.yml --live
uv run content-review llm-check --llm-provider pydanticai --llm-model openai:gpt-4o-mini --llm-api-key-env OPENAI_API_KEY --live
```

Behavior:

- `llm-check` does not require `--enable-llm`
- `llm-check` does not require `--profile`
- `llm-check` does not read Markdown input files
- `llm-check` reuses the same `--llm-config` loader and CLI override rules as `review` and `batch`
- `llm-check --provider` uses `create_llm_reviewer()` directly with `mock` or `pydantic-ai-testmodel`
- `llm-check --provider` does not require an API key, does not read `.env`, and does not access the network for the supported factory providers
- config-driven `llm-check` resolves `LLMProviderConfig.api_key_env` through the shared `resolve_llm_provider_secret(config, env=None)` boundary when the selected provider requires a secret
- config-driven `llm-check` passes the resolved in-memory secret value into `create_llm_reviewer(config, secret_value=...)` and does not ask the factory to resolve secrets
- config-driven `pydanticai` then performs a local construction-only check that builds the runtime agent without executing a live provider call
- `--llm-api-key-env` is a secret reference only; it passes the environment variable name and never passes or prints a plaintext API key
- default behavior is config check plus secret check plus local construction check only
- `--live` is the explicit opt-in live runtime smoke switch; `--runtime` is kept as a compatible alias
- config-driven `pydanticai --live` uses a provider-specific minimal smoke prompt and does not run the normal content-review prompt
- `llm-check` does not write sidecars
- `llm-check` does not produce deterministic `ReviewResult` or `BatchReviewResult`
- `llm-check` does not affect deterministic quality-gate behavior
- reserved real provider names such as `openai`, `anthropic`, `gemini`,
  `deepseek`, `qwen`, and `local` fail explicitly as reserved but not
  implemented and do not fall back
- unsupported `--provider` values fail explicitly as unknown providers and do
  not fall back
- command, config, secret, or runtime failures return exit code `2`

Current text output stages:

- `Config: ok`
- `Model: <not configured>` when no model is set
- `API key env: <ENV_NAME>` plus `API key: <redacted>` when a secret is required and resolves successfully
- `Secret: resolved` or `Secret: not required`
- `Construction: ok`
- `Live call: not run` by default
- `Live call: ok` only when `--live` or `--runtime` executes the explicit smoke call
- `Live call: failed` plus `Reason: ...` when the explicit smoke call fails after construction succeeds

For real-provider setup and manual verification guidance, see
[docs/LLM_PROVIDER_USAGE.md](./LLM_PROVIDER_USAGE.md).

## Experimental LLM Sidecar Review

Single-file `review` now supports an explicit experimental LLM semantic review
flow:

```bash
uv run content-review review article.md --profile profile.yaml --enable-llm --llm-output article.llm.json
uv run content-review review article.md --profile profile.yaml --enable-llm --llm-report article.llm.md
uv run content-review review article.md --profile profile.yaml --report-index article.index.md
uv run content-review review article.md --profile profile.yaml --enable-llm --llm-provider mock --llm-output article.llm.json
uv run content-review review article.md --profile profile.yaml --enable-llm --llm-provider pydanticai --llm-model openai:gpt-4o-mini --llm-api-key-env OPENAI_API_KEY --llm-output article.llm.json
uv run content-review review article.md --profile profile.yaml --enable-llm --llm-config examples/llm/pydanticai/llm-provider.yml --llm-output article.llm.json
uv run content-review review article.md --profile profile.yaml --enable-llm --llm-output article.llm.json --llm-report article.llm.md --report-index article.index.md
uv run content-review review article.md --profile profile.yaml --combined-output article.combined.md
uv run content-review review article.md --profile profile.yaml --enable-llm --llm-output article.llm.json --combined-output article.combined.json --combined-output-format json
```

Single-file `review` constraints:

- this path is opt-in and disabled by default
- single-file `review` writes raw `LLMReviewResult` JSON and/or a separate LLM Markdown report
- `--enable-llm` requires `--llm-output` or `--llm-report`
- `--report-index` alone is allowed and keeps LLM disabled
- `--llm-output` without `--enable-llm` fails
- `--llm-report` without `--enable-llm` fails
- `--report-index` does not satisfy the `--enable-llm` output requirement
- `--include-llm-report` is not supported for single-file LLM review
- `--llm-provider` without `--enable-llm` fails
- `--llm-config` loads a YAML `LLMProviderConfig` file
- explicit CLI flags override the same field from `--llm-config`
- parser defaults do not override config-file values
- if LLM provider config flags are passed, either `--llm-provider` or `--llm-config` must also be passed
- explicit `--llm-provider mock` requires no API key and does not access the network
- explicit `--llm-provider pydantic-ai-testmodel` requires no API key and does not access the network
- explicit `--llm-provider pydanticai` is supported for single-file semantic review
- `pydanticai` requires `--llm-model` and a secret reference through `--llm-api-key-env`
- `--llm-api-key-env` is a secret reference only; there is no plaintext `--llm-api-key` flag
- the shared secret resolver does not read `.env`
- the provider factory does not read environment variables
- if `api_key_env` is missing, unset, or empty, the command exits with a secret-resolution error before any real provider call
- the single-file LLM runner builds `LLMReviewRequest`, calls `run_semantic_review(request)`, then calls `convert_validated_semantic_output_to_llm_review_result(...)`
- deterministic stdout, deterministic JSON output, deterministic Markdown output, `ReviewResult`, and quality-gate behavior stay unchanged
- provider execution failures, parse failures, validation failures, and sidecar write failures return exit code `2`

Single-file sidecar shape:

- `--llm-output` writes raw `LLMReviewResult` JSON
- the top-level `schema_version` is `llm-review-result.v1`
- the sidecar does not include secrets, prompt text, or raw provider output
- the sidecar is separate from deterministic stdout and separate from deterministic JSON / Markdown reports
- `--llm-report` writes a separate human-readable Markdown report derived from the same `LLMReviewResult`
- each LLM finding row also shows stable display-only policy fields:
  `source = llm`, `advisory = yes`, and `quality gate participation = no`
- LLM finding severity in the report is normalized to
  `critical`, `error`, `warning`, `info`, or `unknown`
- missing or blank LLM `rule_id` is displayed as `llm.semantic_review`
- confidence is optional; when missing, the report displays `not provided`
- the report now also includes `## Manual Review Checklist` with stable IDs
  such as `LLM-001`, default `status = needs_review`, default
  `decision = pending`, default `quality gate = no`, and
  severity-derived manual-review priority
- `--llm-output` and `--llm-report` can be used together
- `--llm-report` can be used without `--llm-output`
- `--combined-output` is explicit opt-in and does not enable LLM review by itself
- `--combined-output-format` supports `markdown` and `json`, and defaults to `markdown`
- `--combined-output` can be used without `--enable-llm`; in that case the
  combined result records `llm.status = not_run`
- when single-file LLM review fails and `--combined-output` is set, the
  combined file still records `llm.status = failed` plus structured
  `llm.error`, while command exit code stays `2`
- combined Markdown output reuses
  `render_single_file_combined_markdown_report(...)`
- combined JSON output reuses
  `single_file_combined_review_result_to_dict(...)` /
  `single_file_combined_review_result_to_json(...)`
- `--output`, `--llm-output`, and `--combined-output` are independent and may
  be used together
- `--report-index` writes a separate Markdown index that lists deterministic output, optional LLM output, optional LLM report, the report-index path itself, deterministic summary, optional LLM summary, canonical status, and the rule that quality gate uses deterministic review only
- the report index also repeats the LLM advisory boundary so `critical` or
  `error` LLM findings are not misread as deterministic gate failures
- the report index also states that checklist status and decision values are
  presentation-only and are not persisted anywhere

Current behavior guarantees:

- default CLI behavior is unchanged when LLM flags are omitted
- default CLI behavior is unchanged when `--combined-output` is omitted
- the main deterministic review output remains the canonical `ReviewResult`
- `--format json` does not add an `llm_review` field
- `--format markdown` does not append an LLM section for single-file review
- combined output does not replace `--output` or `--llm-output`
- quality-gate evaluation still reads only deterministic findings
- ordinary tests for this path use fake/stub reviewers and must not access the real network or require a real API key

Provider notes:

- `mock` remains the default single-file sidecar behavior when no explicit
  provider is selected
- `pydantic-ai-testmodel` is available only through explicit single-file
  `--llm-provider` reviewer selection and runs through `create_llm_reviewer()`
- direct future real-provider names such as `openai`, `anthropic`, `gemini`,
  `deepseek`, `qwen`, and `local` are reserved contract values only and do
  not create real reviewers yet
- `pydanticai` now performs a real runtime call after secret preflight
- `pydanticai` uses the shared structured prompt builder, structured response
  schema, and response mapper
- `pydanticai` uses explicit project-controlled retry logic and keeps the
  underlying SDK client at `max_retries=0`
- `pydanticai` can also apply optional instance-local request pacing through
  `--llm-min-request-interval-seconds`
- `pydanticai` normalizes timeout, auth, network, rate-limit, model, and
  unknown runtime failures into stable provider runtime errors, retries only
  timeout/network/rate-limit failures when configured, emits
  `LLMProviderRetryExhaustedError` when retryable failures exceed the configured
  limit, and keeps response-shape failures in `LLMResponseValidationError`
- when both retry backoff and minimum request interval are configured, retry
  backoff sleeps first after a retryable failure and the next pacing check
  sleeps only any remaining interval needed before the next runtime call
- `pydanticai` does not fallback to `mock`
- the CLI stores only the `api_key_env` name in config and never prints secret
  values
- real `pydanticai` usage is intended for explicit manual verification, not
  default tests or CI; use `mock` for no-network automation coverage

Batch CLI boundary:

- `content-review batch` still writes canonical `BatchReviewResult` through
  `--output`
- `content-review batch --llm-output` still writes canonical
  `LLMSidecarResult`
- no batch CLI flag writes `batch-combined-review-result.v1`
- no batch CLI flag changes `--output`, `--llm-output`, or `--format`
  semantics

## Experimental Batch LLM Sidecar Review

Batch `review` also supports an explicit experimental aggregate LLM sidecar
flow:

```bash
uv run content-review batch articles --profile profile.yaml --recursive --enable-llm --llm-output batch.llm.json
uv run content-review batch articles --profile profile.yaml --recursive --enable-llm --llm-report batch.llm.md
uv run content-review batch articles --profile profile.yaml --recursive --report-index batch.index.md
uv run content-review batch articles --profile profile.yaml --recursive --enable-llm --llm-provider mock --llm-output batch.llm.json
uv run content-review batch articles --profile profile.yaml --recursive --enable-llm --llm-provider pydantic-ai-testmodel --llm-output batch.llm.json
uv run content-review batch articles --profile profile.yaml --recursive --enable-llm --llm-config examples/llm/mock/llm-provider.yml --llm-output batch.llm.json
uv run content-review batch articles --profile profile.yaml --recursive --enable-llm --llm-output batch.llm.json --llm-report batch.llm.md --report-index batch.index.md
uv run content-review batch articles --profile profile.yaml --recursive --enable-llm --llm-config examples/llm/pydanticai/llm-provider.yml --llm-output batch.llm.json
```

Batch constraints:

- this path is opt-in and disabled by default
- `--enable-llm` requires `--llm-output` or `--llm-report`
- `--report-index` alone is allowed and keeps LLM disabled
- `--llm-output` without `--enable-llm` fails
- `--llm-report` without `--enable-llm` fails
- `--report-index` does not satisfy the `--enable-llm` output requirement
- explicit batch `--llm-provider` supports `mock`, `pydanticai`, and `pydantic-ai-testmodel`
- `--llm-provider` without `--enable-llm` fails
- `--llm-config` loads a YAML `LLMProviderConfig` file for batch review too
- batch LLM review reuses the same provider construction path as single-file review
- explicit batch `--llm-provider mock` requires no API key and does not access the network
- explicit batch `--llm-provider pydantic-ai-testmodel` requires no API key and does not access the network
- explicit batch `--llm-provider pydanticai` requires `--llm-model` and `--llm-api-key-env`
- reserved real explicit batch `--llm-provider` values such as `openai`,
  `anthropic`, `gemini`, `deepseek`, `qwen`, and `local` fail explicitly as
  reserved but not implemented
- unsupported explicit batch `--llm-provider` values fail explicitly as
  unknown providers and do not fall back
- real `pydanticai` batch sidecar usage also remains available through `--llm-config`
- `--llm-model` is required for config-driven `pydanticai`
- `--llm-base-url` is optional and is passed through for OpenAI-compatible
  endpoints when configured
- `--llm-timeout-seconds` is optional, must be greater than `0`, and is passed
  through to the PydanticAI runtime when configured
- `--llm-retry-attempts` is optional, must be an integer greater than or equal
  to `0`, and is passed through only to the PydanticAI runtime retry boundary
- `--llm-retry-backoff-seconds` is optional, must be greater than or equal to
  `0`, and is passed through only to the PydanticAI runtime retry boundary
- `--llm-min-request-interval-seconds` is optional, must be greater than or
  equal to `0`, and is passed through only to the PydanticAI runtime pacing
  boundary
- explicit CLI flags override the same fields from `--llm-config`
- the `pydanticai` path reuses the same internal request/prompt/response
  mapping contract used in single-file review
- the CLI does not support a plaintext `--llm-api-key` argument
- batch sidecar JSON uses `LLMSidecarResult` envelope metadata:
  `llm_provider` plus `llm_provider_source`
- explicit batch sidecar writes `llm_provider_source: explicit`
- omitted batch `--llm-provider` writes `llm_provider_source: default` or
  `config`
- the batch command writes one UTF-8 aggregate `LLMSidecarResult` JSON sidecar
  to `--llm-output`
- `--llm-report` optionally writes one separate UTF-8 Markdown report rendered
  from the same aggregate sidecar
- `--report-index` optionally writes one separate UTF-8 Markdown index rendered
  from deterministic batch results plus optional batch LLM sidecar summary data

Batch sidecar behavior:

- the aggregate sidecar records one `files[]` entry per reviewed Markdown file
- each file entry records `status`, `finding_count`, optional nested `review`,
  and optional `error`
- summary fields record `file_count`, `succeeded_count`, `failed_count`,
  `skipped_count`, and `finding_count`
- batch LLM review supports partial success; one file with `status = failed`
  does not block other files from being reviewed and recorded
- failed entries expose only `error_type` and `message`, not tracebacks or
  secrets
- any LLM failure makes the command return exit code `2`, even though
  deterministic quality-gate behavior stays unchanged
- batch report index includes LLM file status summary and, for partial
  failures, a separate LLM error summary

Batch behavior guarantees:

- default batch behavior is unchanged when LLM flags are omitted
- the main batch JSON output remains the canonical `BatchReviewResult`
- `--format json` does not add an `llm_review` field
- the report index explains output relationships but does not merge deterministic
  and LLM reports into a single combined report
- the package-level single-file combined Markdown renderer remains outside the
  batch CLI path and does not produce a batch combined report
- `--format markdown` does not add a `## LLM Review` section
- batch summary counts do not include LLM findings
- batch LLM report and report index use the same advisory display policy as
  single-file LLM output: `source = llm`, `advisory = yes`, and
  `quality gate participation = no`
- the batch LLM report also includes `## Manual Review Checklist` with
  globally incrementing finding IDs such as `LLM-001`
- batch partial-failure LLM reports also include
  `## LLM Execution Review Checklist` with stable IDs such as `LLM-ERR-001`,
  default `status = needs_rerun`, and default suggested action
  `rerun_llm_review`
- deterministic severity counts and rule counts are unchanged
- deterministic finding order is unchanged
- quality-gate evaluation still reads only deterministic findings
- batch review reuses one reviewer instance, so `pydanticai` request pacing
  naturally applies across consecutive per-file runtime calls
- the optional batch LLM sidecar Markdown report is independent from the
  deterministic batch Markdown report and does not affect `--fail-on`

Manual provider verification reference:

- use the committed fixtures under `examples/llm/pydanticai/`
- keep real secrets out of the repository and load them only through
  `--llm-api-key-env`
- inspect sidecar JSON and optional Markdown outputs separately from the
  deterministic review result
- see [docs/LLM_PROVIDER_USAGE.md](./LLM_PROVIDER_USAGE.md) for single-file
  and batch commands, troubleshooting, and safety notes

## Regex Rules

Profiles can define optional deterministic `regex_rules`:

```yaml
regex_rules:
  - id: exaggerated_claims
    pattern: "唯一|第一|最强|绝对|100%"
    severity: warning
    message: "Avoid absolute or exaggerated claims."
    suggestion: "Use a more cautious and evidence-based expression."
    case_sensitive: false
```

Behavior:

- regex rules are validated during `review`, `batch`, and `profile validate`
- invalid patterns and duplicate regex rule IDs are rejected before review runs
- findings use the configured regex rule `id` as `rule_id`
- matching is case-insensitive by default unless `case_sensitive: true` is set
- matching scans raw Markdown line by line and does not support cross-line
  matches in the current task
- existing suppression comments work with the configured regex rule ID

Example suppression:

```markdown
这是最强的解决方案。 <!-- content-review-disable-line exaggerated_claims -->
```

## Forbidden Terms Allowlist

The `forbidden_terms` rule supports an optional literal allowlist in rule-style
YAML configuration:

```yaml
rules:
  - id: forbidden_terms
    enabled: true
    severity: error
    terms:
      - 全网最强
      - 永久有效
    allow_terms:
      - 永久有效
```

`allow_terms` must be a list of strings. A forbidden term that exactly matches
an allowed term is not reported. Omitted or empty `allow_terms` preserves the
existing behavior.

## Absolute Claims Rule

The opt-in `absolute_claims` rule detects configured literal absolute or
over-promising expressions and supports a rule-specific severity:

```yaml
rules:
  - id: absolute_claims
    enabled: true
    severity: error
    terms:
      - 全网最强
      - 永久有效
      - 零风险
    allow_terms:
      - 永久有效
```

`terms` and `allow_terms` must both be lists of strings. `allow_terms` uses
exact literal matching. When the rule is enabled, its findings participate in
text, JSON, Markdown, summary counts, batch summary counts, and `--fail-on`
using the configured severity.

## Inline Suppression

Markdown HTML comments can suppress findings for specific physical lines:

```markdown
This sentence intentionally mentions 全网最强. <!-- content-review-disable-line forbidden_terms -->
```

```markdown
<!-- content-review-disable-next-line forbidden_terms -->
This sentence intentionally mentions 全网最强.
```

Optional whitespace inside the HTML comment is tolerated:

```markdown
<!--content-review-disable-line forbidden_terms-->
<!--  content-review-disable-line forbidden_terms  -->
```

Suppression matches by exact rule ID. Suppressed findings are excluded before
text, JSON, and Markdown output are rendered, so they do not appear in output,
do not count toward single-file or batch summaries, and do not trigger
`--fail-on`.

The same suppression directives work for `absolute_claims`, for example:

```markdown
这是一款全网最强的工具。 <!-- content-review-disable-line absolute_claims -->
```

## Profile Validation

The profile validation command checks a YAML review profile before it is used
by `review` or `batch`.

```bash
uv run content-review profile validate profiles/wechat.yaml
uv run content-review profile validate profiles/wechat.yaml --format json
uv run content-review profile validate profiles/examples/wechat-strict.yaml
```

Text output reports either `Profile validation passed.` or `Profile validation failed.`
Structured failures now include an issue count and one entry per problem with:

- `path`
- `code`
- `message`
- optional `suggestion`

Example failure output:

```text
Profile validation failed: profiles/wechat.yaml
Issues: 2

1. regex_rules[0].pattern
   Code: invalid_regex_pattern
   Error: Invalid regex pattern: unterminated character set at position 0.
   Suggestion: Check the regex syntax or escape special characters.

2. regex_rules[0].severity
   Code: invalid_severity
   Error: Unknown severity: warn.
   Suggestion: Use one of: critical, error, warning, info.
```

JSON output still uses `profile-validation-result.v1` and includes
`schema_version`, `valid`, `path`, an optional `profile` summary, and an
`errors` array. Each `errors` item is now a structured validation issue object
instead of a plain message string.

Exit codes:

```text
0 = profile is valid
2 = profile is invalid, missing, unreadable, or cannot be parsed
```

This command is a good first CI step before `review` or `batch`.
In GitHub Actions, exit code `0` passes the step and exit code `2` fails it.
The exit code semantics are unchanged.

## Profile Initialization

Create a new editable profile from a built-in template:

```bash
uv run content-review profile init --template general-basic --output profiles/general.yaml
uv run content-review profile init --template general-publishing --output profiles/publishing.yaml
uv run content-review profile init --template health-content --output profiles/health.yaml
uv run content-review profile init --template marketing-copy --output profiles/marketing.yaml
uv run content-review profile init --template technical-blog --output profiles/technical.yaml
uv run content-review profile init --template wechat-basic --output profiles/my-wechat.yaml
uv run content-review profile init --template wechat-article --output profiles/wechat-article.yaml
uv run content-review profile init --template wechat-strict --output profiles/wechat-strict.yaml --force
```

Supported templates:

```text
general-basic
general-publishing
health-content
marketing-copy
technical-blog
wechat-basic
wechat-article
wechat-strict
```

The generated file is normal YAML in the current `rules:`-based profile format.
It is intended to be edited after creation and should be validated before use:

```bash
uv run content-review profile init --template wechat-basic --output profiles/my-wechat.yaml
uv run content-review profile validate profiles/my-wechat.yaml
uv run content-review review article.md --profile profiles/my-wechat.yaml
```

Overwrite behavior:

```text
default: do not overwrite an existing file
--force: overwrite an existing file
missing parent directory: fail
```

Exit codes:

```text
0 = profile file created successfully
2 = invalid template, missing required options, output conflict, invalid path, or write error
```

## Profile Template Listing

List the available built-in templates before initialization:

```bash
uv run content-review profile list
uv run content-review profile list --format text
uv run content-review profile list --format json
```

Text output includes the template name, a short description, and a usage example:

```text
Available profile templates:

- general-basic
  General-purpose starter profile for public-facing content.

- general-publishing
  Conservative publishing profile with placeholder and overclaim checks.

- health-content
  Cautious health-content profile for risky treatment wording review.

- marketing-copy
  Marketing copy profile for pressure tactics and guarantee-like wording.

- technical-blog
  Technical blog profile for unresolved draft markers and absolute claims.

- wechat-basic
  Basic WeChat article profile with moderate checks.

- wechat-article
  WeChat article profile with cautious regex checks for public-facing drafts.

- wechat-strict
  Stricter WeChat profile intended for batch checks and CI gates.

Use a template:

  content-review profile init --template wechat-basic --output profile.yaml
```

JSON output uses `profile-template-list.v1` and includes only summary metadata:

```json
{
  "schema_version": "profile-template-list.v1",
  "templates": [
    {
      "name": "general-basic",
      "description": "General-purpose starter profile for public-facing content."
    },
    {
      "name": "general-publishing",
      "description": "Conservative publishing profile with placeholder and overclaim checks."
    },
    {
      "name": "health-content",
      "description": "Cautious health-content profile for risky treatment wording review."
    },
    {
      "name": "marketing-copy",
      "description": "Marketing copy profile for pressure tactics and guarantee-like wording."
    },
    {
      "name": "technical-blog",
      "description": "Technical blog profile for unresolved draft markers and absolute claims."
    },
    {
      "name": "wechat-basic",
      "description": "Basic WeChat article profile with moderate checks."
    },
    {
      "name": "wechat-article",
      "description": "WeChat article profile with cautious regex checks for public-facing drafts."
    },
    {
      "name": "wechat-strict",
      "description": "Stricter WeChat profile intended for batch checks and CI gates."
    }
  ]
}
```

The JSON output does not include the full YAML template content.

Exit codes:

```text
0 = templates listed successfully
2 = invalid command usage or invalid --format value
```

## Quality Gate

Both commands support `--fail-on <severity>` for CI and automation workflows.
When configured, the command exits with code `1` if any finding meets or exceeds the severity threshold.

Canonical severity ordering is:

```text
info < warning < error < critical
```

Examples:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --fail-on error
uv run content-review review tests/fixtures/markdown/absolute_claims_article.md --profile profiles/examples/wechat-basic.yaml
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --recursive --fail-on warning
uv run content-review batch examples/batch/articles --profile profiles/examples/wechat-strict.yaml --recursive --fail-on error
```

Exit codes:

```text
0 = command completed and quality gate passed
1 = command completed but quality gate failed
2 = command error, invalid input, invalid profile, file error, or invalid --fail-on value
```

If `--fail-on` is omitted, successful commands preserve the existing behavior and exit with code `0` even when findings are present.
Invalid `--fail-on` values are rejected; valid values are only `info`, `warning`, `error`, and `critical`.

## CI Usage

The repository includes a copyable GitHub Actions example at:

`docs/examples/github-actions/content-review.yml`

Typical CI flow:

```bash
uv run content-review profile validate profiles/examples/wechat-strict.yaml
uv run content-review batch articles --profile profiles/examples/wechat-strict.yaml --recursive --fail-on error
```

To customize the workflow:

- Change the profile path from `profiles/examples/wechat-strict.yaml` to your
  own file such as `profiles/my-wechat.yaml`.
- Change the articles path from `articles` to your content directory such as
  `content/posts` or `docs/articles`.

Exit code behavior in CI:

```text
profile validate: 0 = valid, 2 = invalid or unreadable
batch with --fail-on: 0 = pass, 1 = quality gate failed, 2 = command or configuration error
```

The example workflow is a deterministic automation example only. It does not
guarantee legal, advertising, medical, regulatory, or platform compliance.

## Output Formats

### Text

Text output shows a summary plus one block per finding.
When a finding has source location metadata, the CLI prints:

- `Line`
- `Column`
- `Matched`
- `Context`

If a finding includes a suggestion, the CLI also prints `Suggestion`.

Example:

```text
Review completed.

Findings: 1

[warning] forbidden_terms: 发现风险词：绝对
Line: 3
Column: 5
Matched: 绝对
Context: 这个方法绝对有效。
```

### JSON

JSON output is the canonical serialized `ReviewResult` payload.
It is produced by `review_result_to_json()` and includes:

- `schema_version`
- `summary`
- `findings`
- Optional `document` metadata
- Optional `profile` metadata

Example shape:

```json
{
  "schema_version": "review-result.v1",
  "summary": {
    "finding_count": 1,
    "severity_counts": {
      "info": 0,
      "warning": 1,
      "error": 0,
      "critical": 0
    }
  },
  "findings": [
    {
      "rule_id": "forbidden_terms",
      "severity": "warning",
      "message": "发现风险词：绝对",
      "matched_term": "绝对",
      "matched_text": "绝对",
      "location": {
        "start_line": 3,
        "start_column": 5,
        "end_line": 3,
        "end_column": 7,
        "start_offset": 12,
        "end_offset": 14,
        "matched_text": "绝对",
        "context": "这个方法绝对有效。"
      }
    }
  ],
  "document": {
    "path": "examples/article.md"
  },
  "profile": {
    "name": "example",
    "path": "examples/profile.yml"
  }
}
```

### Markdown

Markdown output is intended for human-readable review reports.
It consumes the canonical `ReviewResult` and renders a deterministic report
with:

- A summary table
- Severity counts in `critical`, `error`, `warning`, `info` order
- Rule counts sorted by rule ID
- A findings table
- A detailed findings section
- A clear `No findings.` empty state
- Quality gate status, `Fail On`, and matched-gate count when `--fail-on` is used

When `--output` is provided, the CLI writes the rendered output to the given file instead of printing it to stdout.
If the write fails, the command exits with code `2`.
If `--fail-on` causes a quality-gate failure, the Markdown report is still
written first when possible and the command then exits with code `1`.

Example shape:

```markdown
# Content Review Report

## Summary

| Field | Value |
| --- | --- |
| File | `examples/article.md` |
| Profile | `examples/profile.yml` |
| Total Findings | 1 |
| Quality Gate | Failed |
| Fail On | `warning` |
| Matched Gate Findings | 1 |

## Severity Counts

| Severity | Count |
| --- | ---: |
| critical | 0 |
| error | 0 |
| warning | 1 |
| info | 0 |

## Rule Counts

| Rule | Count |
| --- | ---: |
| forbidden_terms | 1 |

## Findings

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| warning | forbidden_terms | 3 | 5 | 发现风险词：保证赚钱 | - |

## Detailed Findings

### forbidden_terms

- Severity: warning
- Message: 发现风险词：保证赚钱
- Matched Term: `保证赚钱`
- Line: 3
- Column: 5
- Matched Text: `保证赚钱`
- Context: 这篇文章承诺保证赚钱。
```

## Notes

- The CLI does not implement review logic itself.
- The CLI runs the default internal rule registry through the review pipeline.
- The CLI automatically respects `forbidden_terms.allow_terms` and inline
  suppression comments without adding any suppression-specific flags.
- Built-in example profiles live under `profiles/examples/` and must still be
  passed by path, for example:
  `uv run content-review review article.md --profile profiles/examples/general-basic.yaml`
- Example profiles are starter templates only and do not guarantee legal,
  advertising, medical, regulatory, or platform compliance.
- The CLI does not add rewriting, diff tracking, watch mode, MCP, API, GUI, or report generation logic of its own.
- If a profile references an unknown rule ID, the CLI prints a readable error and exits with code `2`.
- Existing profiles continue to run `forbidden_terms` by default.
- Profiles can opt into additional deterministic rules, including
  `absolute_claims`, `markdown_structure`, and `markdown_links_images`,
  through `ReviewProfile.enabled_rules` or rule-style YAML configuration.
- `content-review profile validate` is a separate command group for YAML
  validation and does not run the review pipeline.
- The batch command discovers Markdown files in deterministic sorted order, supports `--recursive`, supports `--pattern`, and exits with code `2` for missing or invalid input directories.

## Batch Output Formats

### Text

Batch text output shows a summary for the directory plus one block per file.
Each file block includes the file path, finding count, and per-finding details when present.

### JSON

Batch JSON output is the canonical serialized `BatchReviewResult` payload.
It is produced by `batch_review_result_to_json()` and includes:

- `schema_version`
- `summary`
- `results`

Each item in `results` uses the canonical single-file `ReviewResult` shape.

### Markdown

Batch Markdown output is intended for human-readable directory review reports.
It consumes the canonical `BatchReviewResult` and renders:

- A batch summary table
- Severity counts in `critical`, `error`, `warning`, `info` order
- Rule counts sorted by rule ID
- A `Files With Findings` table
- A `Findings by File` section with deterministic per-file ordering
- Clear `No findings.` empty states for clean batches
- Quality gate status when `--fail-on` is used

## Example Files

You can run the CLI against the committed example files:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format text
uv run content-review review examples/article.md --profile examples/profile.yml --format json
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
uv run content-review review examples/article.md --profile examples/profile.yml --fail-on warning
```

For a saved Markdown report:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output examples/review-report.md
```

For the opt-in Markdown structure rule:

```bash
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format text
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format json
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format markdown
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format markdown --output examples/markdown-structure-report.md
```

For the opt-in Markdown links and images rule:

```bash
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format text
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format json
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format markdown
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format markdown --output examples/markdown-links-images-report.md
```

For batch review examples:

```bash
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --recursive --format text
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --recursive --format json
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --recursive --format markdown
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --recursive --format markdown --output examples/batch/batch-report.md
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --recursive --fail-on warning
```
