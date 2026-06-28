# Data Models

## Purpose

This document records the core data models used by the content review engine.

The deterministic core model source of truth is
`src/content_review_engine/core/models.py`.
The future-facing LLM model source of truth is
`src/content_review_engine/llm/models.py`.

Canonical deterministic JSON serialization helpers live in
`src/content_review_engine/core/serialization.py`.
Future-facing LLM serialization helpers live in
`src/content_review_engine/llm/serialization.py`.

Current built-in rule metadata is centralized in
`src/content_review_engine/core/rule_registry.py`.
That registry is internal metadata only. It is not a field in the canonical
review or batch JSON output schemas unless a future task explicitly exposes it.
The deterministic execution registry in
`src/content_review_engine/rules/registry.py` also does not change the JSON
schema; it only decides which deterministic rule implementations run.

---

## ReviewIssue

`ReviewIssue` represents a higher-level issue object kept in the core model layer for future issue-based workflows.

It is not part of the canonical review result payload stabilized by TASK-0011.

| Field | Required | Description |
|---|---|---|
| `id` | Yes | Stable issue or rule identifier |
| `severity` | Yes | `low`, `medium`, `high`, or `critical` |
| `category` | Yes | Issue category |
| `title` | Yes | Short issue title |
| `description` | Yes | Explanation of the issue |
| `suggestion` | Yes | Suggested fix |
| `original_text` | No | Original text related to the issue |
| `start_line` | No | Start line number |
| `end_line` | No | End line number |

---

## SourceSpan

`SourceSpan` represents the source location metadata attached to a deterministic finding.

Line and column numbers are 1-based.
Character offsets are 0-based.
`end_offset` is exclusive.

| Field | Required | Description |
|---|---|---|
| `start_line` | Yes | Start line number |
| `start_column` | Yes | Start column number |
| `end_line` | Yes | End line number |
| `end_column` | Yes | End column number |
| `start_offset` | Yes | Start character offset |
| `end_offset` | Yes | End character offset, exclusive |
| `matched_text` | Yes | Exact matched text |
| `context` | No | Short context snippet around the match |

---

## ReviewFinding

`ReviewFinding` represents one deterministic rule match.

`rule_id` is the stable identifier for the rule that produced the finding.
For current built-in rules, descriptive metadata for that identifier is
centralized in the core rule registry.
That registry metadata does not add fields to `ReviewFinding`, `ReviewResult`,
or `BatchReviewResult`.
If a future LLM semantic review layer is added, it should map its findings into
this finding model or a compatible extension introduced by a later task.
TASK-0029 does not add an LLM-specific finding schema.

| Field | Required | Description |
|---|---|---|
| `rule_id` | Yes | Stable rule identifier |
| `severity` | Yes | `info`, `warning`, `error`, or `critical` |
| `message` | Yes | Human-readable finding summary |
| `matched_term` | Yes | Term that triggered the finding |
| `suggestion` | No | Optional remediation or safer wording guidance |
| `matched_text` | No | Original matched text |
| `location` | No | Attached `SourceSpan` with position metadata |

Example:

```python
ReviewFinding(
    rule_id="absolute_claims",
    severity="error",
    message="发现可能存在绝对化表述：绝对",
    matched_term="绝对",
    suggestion="建议改为更审慎的表述，或补充证据支持该结论。",
    matched_text="绝对",
    location=SourceSpan(
        start_line=3,
        start_column=5,
        end_line=3,
        end_column=7,
        start_offset=12,
        end_offset=14,
        matched_text="绝对",
        context="这个方法绝对有效。",
    ),
)
```

For profile-configured regex findings:

- `rule_id` is the configured regex rule `id`
- `matched_term` stores the configured regex pattern
- `matched_text` stores the exact matched substring
- `location` follows the existing 1-based line and column conventions

---

## LLMReviewFinding

`LLMReviewFinding` stores one future semantic-review finding from a later
optional LLM review layer.

It is not part of the current canonical `ReviewResult` JSON output.
TASK-0034 adds the model only. It does not execute LLM review, merge LLM
findings into deterministic results, or change current report behavior.

| Field | Required | Description |
|---|---|---|
| `rule_id` | Yes | Stable LLM finding identifier such as `llm_semantic_risk` |
| `severity` | Yes | Canonical finding severity: `info`, `warning`, `error`, or `critical` |
| `message` | Yes | Human-readable finding summary |
| `suggestion` | No | Optional rewrite or remediation guidance |
| `rationale` | No | Optional explanation for why the semantic issue was flagged |
| `confidence` | No | Optional confidence score constrained to `0.0 <= x <= 1.0` |
| `line` | No | Optional 1-based start line |
| `column` | No | Optional 1-based start column |
| `end_line` | No | Optional 1-based end line |
| `end_column` | No | Optional 1-based end column |
| `matched_text` | No | Optional text span associated with the finding |
| `category` | No | Optional semantic category label |

Notes:

- `severity` reuses the existing canonical deterministic finding severity
  values
- `rule_id` and `message` must be non-empty strings
- optional string fields, if provided, must not be empty strings
- location fields follow the existing 1-based line and column conventions

---

## LLMReviewSummary

`LLMReviewSummary` stores optional future article-level semantic review
summary data.

It is not part of the current canonical `ReviewResult` JSON output.

| Field | Required | Description |
|---|---|---|
| `overall_risk` | No | Optional summary risk bucket: `low`, `medium`, `high`, or `unknown` |
| `summary` | No | Optional short summary of the semantic review |
| `recommended_action` | No | Optional high-level follow-up recommendation |
| `confidence` | No | Optional confidence score constrained to `0.0 <= x <= 1.0` |

---

## LLMReviewResult

`LLMReviewResult` stores one future optional LLM review pass.

The stable schema version is `llm-review-result.v1`.

It is distinct from the current deterministic `ReviewResult`.
TASK-0034 does not merge it into current CLI JSON output, Markdown reports,
batch results, suppression, or quality-gate behavior.
TASK-0037 allows the single-file CLI `review` command to write it to a
separate JSON sidecar file when LLM review is explicitly enabled.
TASK-0043 adds `LLMProviderConfig` plus a provider factory boundary while
keeping `LLMReviewResult` as the same sidecar result model.
TASK-0039 also allows single-file Markdown report rendering to accept
`LLMReviewResult` as an optional additional input for human-readable output,
without changing the canonical deterministic `ReviewResult` schema.
TASK-0040 also allows the batch CLI command to emit one independent
`LLMReviewResult` sidecar per reviewed Markdown file, while keeping the batch
result schema unchanged.
TASK-0041 keeps `LLMReviewResult` as the nested success payload, but wraps CLI
sidecar output in a separate `LLMSidecarResult` envelope that records summary,
per-file status, and structured non-sensitive errors.

| Field | Required | Description |
|---|---|---|
| `schema_version` | Yes | Stable future LLM result schema version |
| `provider` | No | Optional provider label for a future adapter |
| `model` | No | Optional model identifier for a future adapter |
| `prompt_version` | No | Optional prompt or prompt-template version label |
| `profile_name` | No | Optional future semantic-review profile name |
| `findings` | Yes | Tuple of `LLMReviewFinding`, default empty |
| `summary` | No | Optional `LLMReviewSummary` |
| `metadata` | No | Optional string metadata map |

Future conversion boundary:

```text
LLMReviewFinding
  ↓ future conversion
ReviewFinding-compatible output
  ↓ future merge
ReviewResult / reports / quality gate
```

Future tasks must still decide:

- whether LLM findings are converted into `ReviewFinding`
- whether LLM findings participate in quality gates
- how inline suppression should work for LLM findings
- how confidence and rationale should appear in reports or adapters

Current CLI sidecar boundary:

```text
ReviewResult JSON
  = canonical deterministic review output

LLMSidecarResult JSON
  = separate optional sidecar file
  -> success entries can include nested LLMReviewResult
```

Current batch CLI sidecar boundary:

```text
BatchReviewResult JSON
  = canonical deterministic batch output

Each reviewed Markdown file
  = separate optional LLMSidecarResult JSON

--llm-output-dir/llm-review-manifest.json
  = aggregate LLMSidecarResult summary for the batch run
```

Current optional Markdown report boundary:

```text
ReviewResult
  = canonical deterministic report input

LLMReviewResult
  = optional appended Markdown section input only
```

Current optional sidecar Markdown report boundary:

```text
LLMSidecarResult
  = optional standalone Markdown sidecar report input
```

Current guarantees:

- `LLMReviewResult` is not embedded inside `ReviewResult`
- the main `review-result.v1` schema is unchanged
- the deterministic Markdown report sections are unchanged unless a caller
  explicitly passes `LLMReviewResult` into the renderer
- the optional Markdown LLM section is presentation-only and does not alter
  deterministic counts or finding order
- the current quality gate does not count LLM findings
- the current batch result schema is unchanged
- batch sidecars do not add an `llm_review` field to `BatchReviewResult`
- batch sidecars do not change batch summary counts, deterministic finding
  order, or batch Markdown report structure
- batch sidecar files preserve the input path relative to the batch input
  directory and append `.llm-review.json`
- batch sidecars also write `llm-review-manifest.json` with aggregate
  `file_count`, `succeeded_count`, `failed_count`, `skipped_count`, and
  `finding_count`
- successful manifest entries can include nested `LLMReviewResult` so the
  optional standalone sidecar Markdown report can render per-file findings
- provider-specific structured output is converted before serialization, so a
  successful sidecar entry can still embed an `LLMReviewResult` even when the
  provider uses PydanticAI internally

---

## LLMSidecarResult

`LLMSidecarResult` stores the CLI-facing machine-readable LLM sidecar output.

The stable schema version is `llm-sidecar-result.v1`.

It is distinct from both `ReviewResult` and `LLMReviewResult`.
It exists to let CLI callers record success, failure, and partial success
without changing the deterministic review schema or quality-gate behavior.
The same structure is also the input to the standalone LLM sidecar Markdown
report renderer.

| Field | Required | Description |
|---|---|---|
| `schema_version` | Yes | Stable sidecar envelope schema version |
| `summary` | Yes | `LLMSidecarSummary` with aggregate counts |
| `files` | Yes | Tuple of `LLMSidecarFile` entries |

`LLMSidecarSummary` fields:

| Field | Required | Description |
|---|---|---|
| `file_count` | Yes | Number of files represented in this sidecar |
| `succeeded_count` | Yes | Count of entries with `status = success` |
| `failed_count` | Yes | Count of entries with `status = failed` |
| `skipped_count` | Yes | Count of entries with `status = skipped` |
| `finding_count` | Yes | Sum of nested LLM finding counts for successful entries |

`LLMSidecarFile` fields:

| Field | Required | Description |
|---|---|---|
| `path` | Yes | Markdown file path represented by this entry |
| `status` | Yes | `success`, `failed`, or `skipped` |
| `finding_count` | Yes | Finding count for this file, `0` on failed or skipped entries |
| `review` | No | Nested `LLMReviewResult` for successful runs |
| `error` | No | `LLMSidecarError` for failed runs |

`LLMSidecarError` fields:

| Field | Required | Description |
|---|---|---|
| `error_type` | Yes | Stable exception class name such as `LLMProviderError` |
| `message` | Yes | Human-readable non-traceback error message |

---

## LLMReviewRequest

`LLMReviewRequest` stores the future provider-facing input for one semantic
review pass.

It is not part of the current deterministic `ReviewResult` JSON output.
TASK-0035 adds it only to stabilize the future provider boundary and test
shape.

| Field | Required | Description |
|---|---|---|
| `content` | Yes | Markdown or plain text content to review; must not be empty |
| `profile_name` | No | Optional semantic-review profile label |
| `content_path` | No | Optional source path for adapter context |
| `review_goal` | No | Optional short goal such as unsupported-claim review |
| `metadata` | No | Optional string-to-string metadata map for adapter context |

Notes:

- `content` is trimmed and must not be empty
- optional string fields, if provided, must not be empty strings
- metadata keys and values must not be empty after trimming
- the model does not include provider-specific options, API keys, or runtime
  transport settings

---

## LLMReviewer

`LLMReviewer` is the future provider interface for semantic review execution.

Current shape:

```python
class LLMReviewer(Protocol):
    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        ...
```

Notes:

- the initial boundary is synchronous to match the current project shape
- adapters should return `LLMReviewResult`
- the current runnable implementation is `MockLLMReviewer`
- reviewer construction now goes through `create_llm_reviewer(config)`

---

## LLMReviewRunner

`LLMReviewRunner` is the future semantic-review execution coordinator in
`src/content_review_engine/llm/runner.py`.

Current shape:

```python
class LLMReviewRunner:
    def __init__(self, reviewer: LLMReviewer) -> None:
        ...

    def run(self, request: LLMReviewRequest) -> LLMReviewResult:
        ...
```

Current boundary:

```text
LLMReviewRequest
  ↓
LLMReviewRunner
  ↓
LLMReviewer
  ↓
LLMReviewResult
```

Notes:

- the runner accepts the existing `LLMReviewRequest` model unchanged
- the runner returns the existing `LLMReviewResult` model unchanged
- the runner does not add provider selection, model configuration, API keys,
  network logic, or environment-variable loading
- the runner does not modify the current deterministic `ReviewResult` schema
- the runner does not merge LLM findings into deterministic findings
- the runner does not change the current CLI JSON output, Markdown report
  structure, suppression behavior, or quality-gate behavior

---

## LLMProviderConfig

`LLMProviderConfig` stores structured provider-selection input for the LLM
sidecar adapter boundary.

Current fields:

| Field | Required | Description |
|---|---|---|
| `provider` | Yes | Provider name, default `mock`; recognized values are `mock` and reserved `pydanticai` |
| `model` | No | Optional model identifier stored for future provider use |
| `api_key_env` | No | Optional environment variable name only; stores the variable name, not the secret |
| `base_url` | No | Optional base URL stored for future provider use |

Notes:

- the default config uses `provider = "mock"`
- `provider_type` is derived as `mock` or `real`
- config loading validates provider names and rejects unknown providers with
  `LLMProviderConfigError`
- `repr` and serialization do not contain any secret value because the model
  stores only the environment variable name

---

## ResolvedLLMSecret

`ResolvedLLMSecret` stores the result of secret resolution from
`LLMProviderConfig.api_key_env`.

Current fields:

| Field | Required | Description |
|---|---|---|
| `api_key_env` | Yes | Environment variable name used for resolution |
| `api_key` | Yes | Resolved secret value stored as a redacted secret field |

Notes:

- the resolved secret model is internal to the LLM adapter boundary
- `repr` redacts `api_key`
- `model_dump()` excludes `api_key`
- sidecar JSON, Markdown reports, deterministic review output, and CLI errors
  must not serialize the secret value

---

## PydanticAIReviewRequestPayload

`PydanticAIReviewRequestPayload` stores the internal future-facing request
payload built for the reserved `pydanticai` provider.

Current fields:

| Field | Required | Description |
|---|---|---|
| `prompt_version` | Yes | Stable mapping/prompt contract version, currently `pydanticai-review-prompt.v1` |
| `system_prompt` | Yes | Stable instruction string for structured output behavior |
| `user_prompt` | Yes | Stable request-specific prompt containing content and review context |

Notes:

- this payload is provider-local and not part of the CLI sidecar JSON schema
- the builder uses `LLMReviewRequest` only; it does not include provider
  secrets or runtime transport state
- sensitive metadata keys such as `api_key`, `token`, `secret`, and
  `password` are redacted before they enter the prompt

---

## PydanticAIReviewFinding

`PydanticAIReviewFinding` stores one structured finding expected from the
future reserved `pydanticai` provider response.

Current fields intentionally mirror `LLMReviewFinding` closely:

| Field | Required | Description |
|---|---|---|
| `rule_id` | Yes | Stable non-empty finding identifier |
| `severity` | Yes | `info`, `warning`, `error`, or `critical` |
| `message` | Yes | Human-readable non-empty finding summary |
| `suggestion` | No | Optional remediation guidance |
| `rationale` | No | Optional explanation for the finding |
| `confidence` | No | Optional confidence score constrained to `0.0 <= x <= 1.0` |
| `line` | No | Optional 1-based start line |
| `column` | No | Optional 1-based start column |
| `end_line` | No | Optional 1-based end line |
| `end_column` | No | Optional 1-based end column |
| `matched_text` | No | Optional associated text span |
| `category` | No | Optional semantic category |

Notes:

- the response model forbids extra fields
- `rule_id` and `message` must not be empty
- `severity` reuses the canonical finding severity enum

---

## PydanticAIReviewSummary

`PydanticAIReviewSummary` stores optional article-level summary data expected
from the future reserved `pydanticai` provider response.

Current fields:

| Field | Required | Description |
|---|---|---|
| `overall_risk` | No | `low`, `medium`, `high`, or `unknown` |
| `summary` | No | Optional short review summary |
| `recommended_action` | No | Optional high-level follow-up suggestion |
| `confidence` | No | Optional confidence score constrained to `0.0 <= x <= 1.0` |

---

## PydanticAIReviewResponse

`PydanticAIReviewResponse` stores the structured response contract expected by
the future reserved `pydanticai` provider.

Current fields:

| Field | Required | Description |
|---|---|---|
| `findings` | Yes | List of `PydanticAIReviewFinding`; use `[]` when there are no findings |
| `summary` | No | Optional `PydanticAIReviewSummary` |

Notes:

- the response model forbids extra fields
- invalid responses are normalized into `LLMResponseValidationError`
- validation errors report stable field paths and do not include full prompts,
  full article content, or secret values

---

## LLM Provider Factory

`src/content_review_engine/llm/factory.py` owns reviewer construction from
`LLMProviderConfig`.

Current behavior:

- `provider = "mock"` returns `MockLLMReviewer`
- `provider = "pydanticai"` returns `PydanticAIReviewer`, a future skeleton
  that still requires secret preflight, can build provider-local request
  payloads through `PydanticAIReviewMapper`, and still raises
  `LLMProviderNotImplementedError` before any real review call
- unknown providers raise `LLMProviderConfigError`
- the factory does not read environment variables, perform network requests,
  or depend on the CLI layer
- `src/content_review_engine/llm/pydanticai.py` is only a future skeleton and
  does not implement provider review logic

---

## LLM Review Errors

The future LLM adapter boundary now defines minimal error types in
`src/content_review_engine/llm/errors.py`.

| Type | Description |
|---|---|
| `LLMReviewError` | Base exception for future LLM review failures |
| `LLMProviderConfigError` | Invalid or unsupported provider configuration |
| `LLMProviderSecretError` | Missing, unset, or empty provider secret configuration |
| `LLMProviderNotImplementedError` | Recognized provider name that is not implemented yet |
| `LLMProviderError` | Provider adapter failure, such as transport or upstream execution failure |
| `LLMResponseValidationError` | Provider output could not be validated as an `LLMReviewResult` or provider-local structured response contract |

---

## MockLLMReviewer

`MockLLMReviewer` is a deterministic test adapter defined in
`src/content_review_engine/llm/mock.py`.

Current behavior:

- if constructed with `result=...`, `review()` returns that configured
  `LLMReviewResult`
- otherwise `review()` returns a new empty `LLMReviewResult`
- it does not perform network access, prompt execution, or provider-specific
  behavior

---

## RuleDefinition

`RuleDefinition` stores descriptive metadata for one current built-in rule in
the internal rule registry.

It is not part of the canonical review-result JSON schema.
It does not replace `ReviewFinding.rule_id`, and it does not appear in the
current JSON output unless a future task explicitly exposes registry metadata.
Profile-configured regex rule IDs are dynamic and are intentionally not stored
as `RuleDefinition` entries in the built-in metadata registry.

| Field | Required | Description |
|---|---|---|
| `rule_id` | Yes | Stable built-in rule identifier |
| `name` | Yes | Human-readable rule name |
| `description` | Yes | Short description of the rule's purpose |
| `category` | Yes | Small internal category label such as `terms` or `markdown` |
| `source` | Yes | Whether the rule is `built-in` or `profile-driven` |
| `supports_suppression` | Yes | Whether inline suppression comments are supported |

---

## RegexRuleConfig

`RegexRuleConfig` stores one optional profile-configured deterministic regex
rule inside `ReviewProfile.regex_rules`.

It is profile input data, not a new review-result JSON top-level section.
Regex findings still flow through the existing `ReviewFinding`,
`ReviewResult`, and `BatchReviewResult` models.

| Field | Required | Description |
|---|---|---|
| `id` | Yes | Stable profile-defined rule identifier matching `^[a-z][a-z0-9_]*$` |
| `pattern` | Yes | Python regular expression compiled during validation |
| `severity` | Yes | `info`, `warning`, `error`, or `critical` |
| `message` | Yes | Human-readable finding message |
| `suggestion` | No | Optional remediation guidance |
| `case_sensitive` | Yes | Boolean flag, default `false` |

---

## ReviewSummary

`ReviewSummary` summarizes a `ReviewResult`.

The summary is computed from the findings list and should not be assembled separately in the CLI or report layers.

| Field | Required | Description |
|---|---|---|
| `finding_count` | Yes | Total number of findings |
| `severity_counts` | Yes | Count of findings by severity |

`severity_counts` currently uses the canonical buckets:

- `info`
- `warning`
- `error`
- `critical`

Example:

```json
{
  "finding_count": 2,
  "severity_counts": {
    "info": 0,
    "warning": 2,
    "error": 0,
    "critical": 0
  }
}
```

---

## ReviewDocumentMetadata

`ReviewDocumentMetadata` stores optional document context for a `ReviewResult`.

| Field | Required | Description |
|---|---|---|
| `path` | Yes | Path to the reviewed document |

---

## ReviewProfileMetadata

`ReviewProfileMetadata` stores optional profile context for a `ReviewResult`.

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Profile name |
| `path` | No | Path to the loaded profile |

---

## ProfileValidationIssue

`ProfileValidationIssue` stores one structured validation issue for a review
profile.

| Field | Required | Description |
|---|---|---|
| `path` | Yes | Stable location such as `regex_rules[0].pattern` or `<yaml>` |
| `code` | Yes | Stable issue code such as `invalid_regex_pattern` |
| `message` | Yes | Readable validation error message |
| `suggestion` | No | Optional actionable fix suggestion |

---

## ProfileValidationRuleSummary

`ProfileValidationRuleSummary` records one rule entry in a valid profile
validation result.

| Field | Required | Description |
|---|---|---|
| `id` | Yes | Stable rule identifier |
| `enabled` | Yes | Whether the rule is enabled |
| `severity` | No | Effective finding severity when the rule exposes one |

---

## ProfileValidationProfileSummary

`ProfileValidationProfileSummary` stores the summary returned for a valid
profile validation run.

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Profile name |
| `target_platform` | Yes | Target platform |
| `enabled_rule_count` | Yes | Number of enabled rules in the summary |
| `disabled_rule_count` | Yes | Number of disabled rules in the summary |
| `rules` | Yes | Ordered list of `ProfileValidationRuleSummary` items |

---

## ProfileValidationResult

`ProfileValidationResult` is the canonical structured output for
`content-review profile validate`.

The stable schema version is `profile-validation-result.v1`.

| Field | Required | Description |
|---|---|---|
| `schema_version` | Yes | Result schema version |
| `valid` | Yes | Whether the profile is valid |
| `path` | Yes | Path that was validated |
| `profile` | No | Optional `ProfileValidationProfileSummary` for valid profiles |
| `errors` | Yes | List of `ProfileValidationIssue` items |

Example:

```json
{
  "schema_version": "profile-validation-result.v1",
  "valid": true,
  "path": "profiles/wechat.yaml",
  "profile": {
    "name": "wechat",
    "target_platform": "wechat",
    "enabled_rule_count": 1,
    "disabled_rule_count": 0,
    "rules": [
      {
        "id": "forbidden_terms",
        "enabled": true,
        "severity": "warning"
      }
    ]
  },
  "errors": []
}
```

---

## ProfileTemplateSummary

`ProfileTemplateSummary` records one built-in profile template exposed by
`content-review profile list`.

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Stable built-in template name |
| `description` | Yes | Short human-readable template description |

---

## ProfileTemplateListResult

`ProfileTemplateListResult` is the canonical structured output for
`content-review profile list --format json`.

The stable schema version is `profile-template-list.v1`.

| Field | Required | Description |
|---|---|---|
| `schema_version` | Yes | Result schema version |
| `templates` | Yes | Ordered list of `ProfileTemplateSummary` items |

Example:

```json
{
  "schema_version": "profile-template-list.v1",
  "templates": [
    {
      "name": "general-basic",
      "description": "General-purpose starter profile for public-facing content."
    },
    {
      "name": "wechat-basic",
      "description": "Basic WeChat article profile with moderate checks."
    }
  ]
}
```

---

## ReviewResult

`ReviewResult` is the canonical structured output for a reviewed document.

The stable schema version is `review-result.v1`.

| Field | Required | Description |
|---|---|---|
| `schema_version` | Yes | Result schema version |
| `summary` | Yes | `ReviewSummary` computed from findings |
| `findings` | Yes | List of `ReviewFinding` |
| `document` | No | Optional `ReviewDocumentMetadata` |
| `profile` | No | Optional `ReviewProfileMetadata` |

Example:

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
      "message": "发现风险词：绝对安全",
      "matched_term": "绝对安全",
      "matched_text": "绝对安全",
      "location": {
        "start_line": 1,
        "start_column": 8,
        "end_line": 1,
        "end_column": 12,
        "start_offset": 7,
        "end_offset": 11,
        "matched_text": "绝对安全",
        "context": "# 测试文章 绝对安全"
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

---

## BatchReviewSummary

`BatchReviewSummary` summarizes a batch review run across multiple files.

| Field | Required | Description |
|---|---|---|
| `file_count` | Yes | Number of discovered Markdown files |
| `reviewed_count` | Yes | Number of files successfully reviewed |
| `finding_count` | Yes | Total number of findings across all files |
| `files_with_findings` | Yes | Number of files with at least one finding |
| `severity_counts` | Yes | Aggregated severity counts across all file summaries |

Example:

```json
{
  "file_count": 3,
  "reviewed_count": 3,
  "finding_count": 2,
  "files_with_findings": 2,
  "severity_counts": {
    "info": 0,
    "warning": 2,
    "error": 0,
    "critical": 0
  }
}
```

---

## BatchReviewResult

`BatchReviewResult` is the canonical structured output for a batch review run.

The stable schema version is `batch-review-result.v1`.

| Field | Required | Description |
|---|---|---|
| `schema_version` | Yes | Result schema version |
| `summary` | Yes | `BatchReviewSummary` computed from the file results |
| `results` | Yes | List of canonical `ReviewResult` objects |

Example:

```json
{
  "schema_version": "batch-review-result.v1",
  "summary": {
    "file_count": 3,
    "reviewed_count": 3,
    "finding_count": 2,
    "files_with_findings": 2,
    "severity_counts": {
      "info": 0,
      "warning": 2,
      "error": 0,
      "critical": 0
    }
  },
  "results": [
    {
      "schema_version": "review-result.v1",
      "summary": {
        "finding_count": 0,
        "severity_counts": {
          "info": 0,
          "warning": 0,
          "error": 0,
          "critical": 0
        }
      },
      "findings": [],
      "document": {
        "path": "tests/fixtures/batch/articles/clean.md"
      },
      "profile": {
        "name": "batch-default",
        "path": "tests/fixtures/batch/profile.yml"
      }
    }
  ]
}
```

---

## ReviewProfile

`ReviewProfile` represents a review configuration.

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Profile name |
| `target_platform` | Yes | Target platform |
| `tone` | No | Expected writing tone |
| `max_title_length` | No | Maximum suggested title length |
| `max_paragraph_length` | No | Maximum suggested paragraph length |
| `forbidden_terms` | No | List of forbidden terms to detect |
| `forbidden_terms_allow_terms` | No | Normalized literal allowlist for `forbidden_terms`; populated from `rules[].allow_terms` when using rule-style YAML configuration |
| `absolute_claims_terms` | No | List of literal absolute-claim terms to detect |
| `absolute_claims_allow_terms` | No | Normalized literal allowlist for `absolute_claims`; populated from `rules[].allow_terms` when using rule-style YAML configuration |
| `absolute_claims_severity` | No | Severity used for `absolute_claims` findings; defaults to `warning` |
| `enabled_rules` | No | Optional ordered list of rule IDs to run |

---

## Change Rules

1. Any change to `ReviewIssue` must update this document.
2. Any change to `ReviewFinding` must update this document.
3. Any change to `ReviewSummary` must update this document.
4. Any change to `ReviewResult` must update this document.
5. Any change to `BatchReviewSummary` must update this document.
6. Any change to `BatchReviewResult` must update this document.
7. Any change to `ProfileValidationResult` must update this document.
8. Any change to `ReviewProfile` must update this document.
9. After v0.1.0, breaking changes to these models require an ADR.
