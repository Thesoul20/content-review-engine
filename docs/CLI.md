# CLI

Start with [docs/QUICKSTART.md](./QUICKSTART.md) for the first-run workflow
from `uv sync` through `review`, `batch`, Markdown reports, and CI-oriented
exit codes.

For real-provider setup, manual verification fixtures, sidecar inspection, and
runtime troubleshooting, see [docs/LLM_PROVIDER_USAGE.md](./LLM_PROVIDER_USAGE.md).

For a committed runnable demo workspace using the current CLI contract, see
[`examples/demo/README.md`](../examples/demo/README.md).

For rule-system details such as supported `rule_id` values, severity ordering,
suppression comments, counts, and quality gates, see
[docs/RULES.md](./RULES.md), the canonical rule reference.

## Current Command

```bash
uv run content-review review <markdown_file> --profile <profile_file> [--format text|json|markdown] [--output <file>] [--fail-on info|warning|error|critical] [--enable-llm --llm-output <file> [--llm-markdown-output <file>] [--llm-provider mock|pydanticai] [--llm-model <name>] [--llm-api-key-env <env>] [--llm-base-url <url>] [--llm-timeout-seconds <seconds>] [--llm-retry-attempts <count>] [--llm-retry-backoff-seconds <seconds>] [--llm-min-request-interval-seconds <seconds>] [--include-llm-report]]
uv run content-review batch <input_dir> --profile <profile_file> [--format text|json|markdown] [--output <file>] [--recursive] [--pattern "*.md"] [--fail-on info|warning|error|critical] [--enable-llm --llm-output-dir <dir> [--llm-markdown-output <file>] [--llm-provider mock|pydanticai] [--llm-model <name>] [--llm-api-key-env <env>] [--llm-base-url <url>] [--llm-timeout-seconds <seconds>] [--llm-retry-attempts <count>] [--llm-retry-backoff-seconds <seconds>] [--llm-min-request-interval-seconds <seconds>]]
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

## Experimental LLM Sidecar Review

Single-file `review` now supports an explicit experimental LLM sidecar flow:

```bash
uv run content-review review article.md --profile profile.yaml --enable-llm --llm-output article.llm.json
uv run content-review review article.md --profile profile.yaml --enable-llm --llm-provider mock --llm-output article.llm.json
uv run content-review review article.md --profile profile.yaml --enable-llm --llm-output article.llm.json --llm-markdown-output article.llm.md
uv run content-review review article.md --profile profile.yaml --format markdown --enable-llm --llm-output article.llm.json --include-llm-report
uv run content-review review article.md --profile profile.yaml --enable-llm --llm-provider pydanticai --llm-model gpt-4o-mini --llm-api-key-env OPENAI_API_KEY --llm-timeout-seconds 30 --llm-retry-attempts 2 --llm-retry-backoff-seconds 1.0 --llm-min-request-interval-seconds 2.0 --llm-output article.llm.json
```

Single-file `review` constraints:

- this path is opt-in and disabled by default
- only the single-file `review` command supports it
- `--llm-provider` supports `mock` and `pydanticai`
- `--enable-llm` requires `--llm-output`
- `--llm-output` without `--enable-llm` fails
- `--llm-markdown-output` without `--enable-llm` fails
- `--include-llm-report` without `--enable-llm` fails
- `--include-llm-report` requires `--format markdown`
- `--include-llm-report` fails for `--format json`
- `--include-llm-report` fails for `--format text`
- `--llm-provider`, `--llm-model`, `--llm-api-key-env`, `--llm-base-url`, and
  `--llm-timeout-seconds` can still be parsed without `--enable-llm`, but they
  do not affect the deterministic review path
- `--llm-provider mock` is the default provider
- `--llm-provider pydanticai` performs secret preflight and then executes a
  real PydanticAI runtime call through the provider interface
- `--llm-model` is required for `--llm-provider pydanticai`
- `--llm-model`, `--llm-api-key-env`, `--llm-base-url`, and
  `--llm-timeout-seconds`, `--llm-retry-attempts`, and
  `--llm-retry-backoff-seconds`, and
  `--llm-min-request-interval-seconds` are stored in `LLMProviderConfig`
- the `pydanticai` path reuses the tested request/prompt/response mapping
  layer from the provider adapter
- `--llm-api-key-env` stores the environment variable name in config; when
  `pydanticai` is selected, the CLI resolves that env var only to verify the
  secret exists and never prints its value
- if `--llm-provider pydanticai` omits `--llm-api-key-env`, points to an
  unset env var, or points to an empty env var, the command exits with a
  structured secret error
- `--llm-base-url` is optional and, when provided, is passed to the
  OpenAI-compatible runtime provider used by `pydanticai`
- `--llm-timeout-seconds` is optional, must be greater than `0`, is ignored by
  deterministic review when LLM is not enabled, and is passed only to the LLM
  provider runtime boundary
- `--llm-retry-attempts` is optional, must be an integer greater than or equal
  to `0`, is ignored by deterministic review when LLM is not enabled, and
  means extra retry attempts after the initial provider call
- `--llm-retry-backoff-seconds` is optional, must be greater than or equal to
  `0`, is ignored by deterministic review when LLM is not enabled, and is used
  as the fixed delay before each retryable provider retry
- `--llm-min-request-interval-seconds` is optional, must be greater than or
  equal to `0`, is ignored by deterministic review when LLM is not enabled,
  and sets an instance-local minimum spacing between consecutive real
  `pydanticai` runtime call start times
- the CLI does not support a plaintext `--llm-api-key` argument
- the LLM result is written as a separate UTF-8 JSON sidecar file in
  `LLMSidecarResult` format
- `--llm-markdown-output` optionally writes a separate UTF-8 Markdown sidecar
  report rendered from the same `LLMSidecarResult`
- `--include-llm-report` only affects single-file Markdown report rendering and
  does not replace the required `--llm-output` sidecar JSON

Single-file sidecar shape:

- top-level `schema_version` is `llm-sidecar-result.v1`
- top-level `summary` includes `file_count`, `succeeded_count`,
  `failed_count`, `skipped_count`, and `finding_count`
- `files[0].status` is `success` or `failed` in the current implementation
- successful entries include nested `review` with the original
  `LLMReviewResult`
- failed entries include `error.error_type` and `error.message`
- LLM sidecar failure does not change deterministic review output or
  quality-gate evaluation
- the optional sidecar Markdown report shows the same summary, per-file
  status, structured errors, and successful-file findings without changing
  the main deterministic Markdown report

Current behavior guarantees:

- default CLI behavior is unchanged when LLM flags are omitted
- the main deterministic review output remains the canonical `ReviewResult`
- `--format json` does not add an `llm_review` field
- `--format markdown` does not add an LLM section unless
  `--enable-llm` and `--include-llm-report` are both enabled
- when enabled, the optional LLM Markdown section is appended after the
  deterministic report and does not change deterministic counts or finding
  order
- quality-gate evaluation still reads only deterministic findings
- batch review behavior is unchanged and does not accept LLM flags

Provider notes:

- `mock` keeps the deterministic sidecar behavior from TASK-0037 and remains
  the default provider
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

## Experimental Batch LLM Sidecar Review

Batch `review` also supports an explicit experimental per-file LLM sidecar
flow:

```bash
uv run content-review batch articles --profile profile.yaml --recursive --enable-llm --llm-output-dir llm-sidecars
uv run content-review batch articles --profile profile.yaml --recursive --enable-llm --llm-provider mock --llm-output-dir llm-sidecars
uv run content-review batch articles --profile profile.yaml --recursive --enable-llm --llm-output-dir llm-sidecars --llm-markdown-output llm-sidecars.md
uv run content-review batch articles --profile profile.yaml --recursive --enable-llm --llm-provider pydanticai --llm-model gpt-4o-mini --llm-api-key-env OPENAI_API_KEY --llm-timeout-seconds 30 --llm-retry-attempts 2 --llm-retry-backoff-seconds 1.0 --llm-min-request-interval-seconds 2.0 --llm-output-dir llm-sidecars
```

Batch constraints:

- this path is opt-in and disabled by default
- `--enable-llm` requires `--llm-output-dir`
- `--llm-output-dir` without `--enable-llm` fails
- `--llm-markdown-output` without `--enable-llm` fails
- `--llm-provider` supports `mock` and `pydanticai`
- `--llm-provider mock` does not require `--llm-model`
- `--llm-provider mock` does not read any API key
- `--llm-provider pydanticai` resolves `--llm-api-key-env` as a secret
  preflight and then executes a real runtime call for each file
- `--llm-model` is required for `--llm-provider pydanticai`
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
- the `pydanticai` path reuses the same internal request/prompt/response
  mapping contract used in single-file review
- the CLI does not support a plaintext `--llm-api-key` argument
- the batch command writes one separate UTF-8 `LLMSidecarResult` JSON sidecar
  per reviewed Markdown file
- the batch command also writes
  `--llm-output-dir/llm-review-manifest.json` as an aggregate
  `LLMSidecarResult` summary
- `--llm-markdown-output` optionally writes one separate UTF-8 Markdown sidecar
  report rendered from the aggregate manifest

Sidecar path rule:

```text
articles/post-a.md
  -> llm-sidecars/post-a.md.llm-review.json

articles/nested/post-b.md
  -> llm-sidecars/nested/post-b.md.llm-review.json
```

The path is computed relative to the batch input directory. Parent
directories are created automatically under `--llm-output-dir`.

Batch sidecar behavior:

- per-file sidecars use `summary.file_count = 1` and record that file's
  `status`, `finding_count`, optional nested `review`, and optional `error`
- `llm-review-manifest.json` aggregates the full run with `file_count`,
  `succeeded_count`, `failed_count`, `skipped_count`, and `finding_count`
- successful manifest entries can include nested `review` payloads so the
  optional batch Markdown sidecar report can show per-file LLM findings
- batch LLM review supports partial success; one file with `status = failed`
  does not block other files from generating sidecars
- failed entries expose only `error_type` and `message`, not tracebacks or
  secrets

Batch behavior guarantees:

- default batch behavior is unchanged when LLM flags are omitted
- the main batch JSON output remains the canonical `BatchReviewResult`
- `--format json` does not add an `llm_review` field
- `--format markdown` does not add a `## LLM Review` section
- batch summary counts do not include LLM findings
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
