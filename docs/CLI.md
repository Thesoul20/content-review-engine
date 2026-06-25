# CLI

## Current Command

```bash
uv run content-review review <markdown_file> --profile <profile_file> [--format text|json|markdown] [--output <file>] [--fail-on info|warning|error|critical]
uv run content-review batch <input_dir> --profile <profile_file> [--format text|json|markdown] [--output <file>] [--recursive] [--pattern "*.md"] [--fail-on info|warning|error|critical]
uv run content-review profile validate <profile_file> [--format text|json]
```

The CLI is a thin adapter over the core review pipeline.
It reads Markdown, loads a YAML profile, runs deterministic rules, and prints or exports the canonical `ReviewResult`.
The batch command reuses the same pipeline for each discovered Markdown file and returns a canonical `BatchReviewResult`.
The profile validation command reuses the existing profile loader and registry checks and returns a canonical `ProfileValidationResult`.

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
```

Text output reports either `Profile validation passed.` or `Profile validation failed.`
JSON output uses `profile-validation-result.v1` and includes `schema_version`,
`valid`, `path`, an optional `profile` summary, and an `errors` array.

Exit codes:

```text
0 = profile is valid
2 = profile is invalid, missing, unreadable, or cannot be parsed
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
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --recursive --fail-on warning
```

Exit codes:

```text
0 = command completed and quality gate passed
1 = command completed but quality gate failed
2 = command error, invalid input, invalid profile, file error, or invalid --fail-on value
```

If `--fail-on` is omitted, successful commands preserve the existing behavior and exit with code `0` even when findings are present.
Invalid `--fail-on` values are rejected; valid values are only `info`, `warning`, `error`, and `critical`.

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
It consumes the canonical `ReviewResult` and renders a report with a summary section and per-finding details.

When `--output` is provided, the CLI writes the rendered output to the given file instead of printing it to stdout.
If the write fails, the command exits with code `2`.

Example shape:

```markdown
# Content Review Report

## Summary

- Document: `examples/article.md`
- Profile: `examples/profile.yml`
- Findings: 1

## Findings

### forbidden_terms

- Severity: warning
- Message: 发现风险词：保证赚钱
- Line: 3
- Column: 5
- Matched: `保证赚钱`
- Context: 这篇文章承诺保证赚钱。
```

## Notes

- The CLI does not implement review logic itself.
- The CLI runs the default internal rule registry through the review pipeline.
- The CLI automatically respects `forbidden_terms.allow_terms` and inline
  suppression comments without adding any suppression-specific flags.
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
It consumes the canonical `BatchReviewResult` and renders a batch summary plus one section per reviewed file.

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
