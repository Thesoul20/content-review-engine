# Rule System

## Overview

The content review engine runs deterministic rules against Markdown content and
returns structured findings in the core `ReviewResult` and `BatchReviewResult`
models.

This document is the canonical reference for the content review rule system.

It explains the current rule model, supported built-in rule IDs, finding
fields, severities, quality gates, suppression comments, batch aggregation
behavior, reports, and current limitations.

## What Is A Rule?

A rule is a deterministic review check that can produce zero or more findings
for a Markdown document.

Rules are executed by the core package. The CLI, reports, and batch review
features consume the resulting findings; they do not re-implement rule logic.

## Rule IDs

Every finding has a stable `rule_id`.

`rule_id` is used for:

- classifying findings
- grouping rule counts
- selecting or enabling rules through profile configuration
- applying inline suppression comments
- reading report output
- understanding which findings contributed to a quality gate failure

Current built-in rule IDs are:

- `forbidden_terms`
- `absolute_claims`
- `markdown_structure`
- `markdown_links_images`

Current built-in rule metadata is centralized in
`src/content_review_engine/core/rule_registry.py`.
The registry is descriptive only. It does not run rules, validate
suppression comments, change profile parsing, or change output schemas.
Deterministic runtime execution still lives in
`src/content_review_engine/rules/registry.py`, which registers rule
implementations for the review pipeline.

Default enablement in the current registry:

- `forbidden_terms`: enabled by default
- `absolute_claims`: opt-in
- `markdown_structure`: opt-in
- `markdown_links_images`: opt-in

Opt-in rules become active through `rules:`-based profile configuration or
explicit `enabled_rules`.

`docs/RULES.md` remains the canonical user-facing rule reference.
`src/content_review_engine/core/rule_registry.py` is the internal metadata
source for current built-in rule descriptions, while
`src/content_review_engine/rules/registry.py` remains execution-focused.
If a future LLM semantic review layer is added, it should stay separate from
the deterministic execution registry and produce compatible findings later.

## Current Built-in Rules

### `forbidden_terms`

Purpose:
Detect configured forbidden or risky literal terms from the active review
profile.

Current behavior:

- reads configured terms from the active profile
- supports legacy top-level `forbidden_terms` profile input
- ignores blank entries and duplicate configured entries
- supports exact literal `allow_terms` exceptions
- returns `warning` findings
- currently reports at most one finding per configured term, using the first
  occurrence found in the document

Typical profile configuration:

```yaml
rules:
  - id: forbidden_terms
    enabled: true
    terms:
      - 违规词
      - 敏感词
    allow_terms: []
```

Suppression example:

```markdown
This line intentionally contains a configured term. <!-- content-review-disable-line forbidden_terms -->
```

Limitations:

- literal matching only
- no regex or fuzzy matching
- no per-rule severity override in the current profile format
- no repeated finding for the same configured term appearing multiple times

### `absolute_claims`

Purpose:
Detect configured literal absolute, exaggerated, or over-promising expressions
from the active review profile.

Current behavior:

- reads configured terms from the active profile; the rule is profile-driven,
  not hardcoded to a fixed vocabulary
- supports exact literal `allow_terms` exceptions
- uses the configured rule severity from the active profile
- includes a suggestion field in findings
- currently reports at most one finding per configured term, using the first
  occurrence found in the document

Typical profile configuration:

```yaml
rules:
  - id: absolute_claims
    enabled: true
    severity: warning
    terms:
      - 全网最强
      - 行业第一
      - 唯一选择
    allow_terms:
      - 唯一标识符
```

Suppression example:

```markdown
This line contains an intentional claim. <!-- content-review-disable-line absolute_claims -->
```

Limitations:

- literal matching only
- no evidence evaluation or contextual reasoning
- no compliance guarantee for advertising, legal, medical, regulatory, or
  platform policy requirements
- no repeated finding for the same configured term appearing multiple times

### `markdown_structure`

Purpose:
Detect basic Markdown structure issues in headings and paragraphs.

Current behavior:

- missing top-level H1 heading
- multiple H1 headings
- heading level jumps such as H1 to H3
- empty headings
- paragraphs longer than the profile's `max_paragraph_length`
- ignores heading-like content inside fenced code blocks

Profile interaction:

- enabled through `rules:` or `enabled_rules`
- uses `max_paragraph_length` from the active profile
- currently emits `warning` findings

Suppression example:

```markdown
##    <!-- content-review-disable-line markdown_structure -->
```

Limitations:

- checks ATX-style headings only
- does not validate broader writing quality or document intent
- some findings, such as missing H1, do not include line or column data

### `markdown_links_images`

Purpose:
Detect obvious Markdown link and image hygiene issues.

Current behavior:

- empty link text
- empty link target
- placeholder link target such as `#`, `TODO`, or `TBD`
- empty image alt text
- empty image target
- placeholder image target
- ignores matches inside fenced code blocks

Profile interaction:

- enabled through `rules:` or `enabled_rules`
- does not currently use rule-specific profile terms
- currently emits `warning` findings

Suppression example:

```markdown
[Docs](#) <!-- content-review-disable-line markdown_links_images -->
```

Limitations:

- focuses on simple Markdown syntax issues only
- does not fetch or verify remote targets
- does not inspect image content or accessibility beyond empty alt text
- inline code spans are not specially excluded in the current version

## Implementation And Tests

This document is the canonical user-facing rule reference. Implementation and
test coverage currently live here. The centralized built-in rule metadata
registry lives at `src/content_review_engine/core/rule_registry.py`:
runtime deterministic execution registry lives at
`src/content_review_engine/rules/registry.py`.

- `forbidden_terms`
  - implementation: `src/content_review_engine/rules/forbidden_terms.py`
  - tests: `tests/test_forbidden_terms_rule.py`
- `absolute_claims`
  - implementation: `src/content_review_engine/rules/absolute_claims.py`
  - tests: `tests/test_absolute_claims_rule.py`
- `markdown_structure`
  - implementation: `src/content_review_engine/rules/markdown_structure.py`
  - tests: `tests/test_markdown_structure_rule.py`
- `markdown_links_images`
  - implementation: `src/content_review_engine/rules/markdown_links_images.py`
  - tests: `tests/test_markdown_links_images_rule.py`

## Findings

A finding is one rule match in the canonical review result.

Common finding fields users will see in JSON output, text output, or Markdown
reports:

- `rule_id`: stable rule identifier for the rule that produced the finding
- `severity`: one of `info`, `warning`, `error`, or `critical`
- `message`: human-readable summary of the finding
- `suggestion`: optional remediation guidance; not every rule sets this
- `matched_term`: the configured term or internal match label associated with
  the finding
- `matched_text`: optional original matched text
- `location.start_line`: 1-based line number when location data is available
- `location.start_column`: 1-based column number when location data is available
- `location.context`: optional short context snippet when available

Report output shortens some of these names:

- `line` in reports comes from `location.start_line`
- `column` in reports comes from `location.start_column`
- `context` is shown in detailed Markdown report sections when available

Not every field is populated for every rule. For example, a missing-H1
`markdown_structure` finding does not currently include location data.

Suppressed findings are filtered out before `ReviewResult` creation, so current
outputs do not expose a `suppressed` boolean field.

## Severity Levels

The canonical finding severities are:

- `critical`
- `error`
- `warning`
- `info`

Current rule usage:

- `forbidden_terms`: `warning`
- `absolute_claims`: configurable `info|warning|error|critical`
- `markdown_structure`: `warning`
- `markdown_links_images`: `warning`

## Severity Ordering

The canonical quality-gate ordering is:

```text
critical > error > warning > info
```

The implementation also exposes the same ordering in ascending threshold form:

```text
info < warning < error < critical
```

Quality gates use this ordering to decide whether a finding meets or exceeds
the configured `--fail-on` threshold.

## Rule Counts

Rule counts are deterministic counts of findings grouped by `rule_id`.

Current behavior:

- single-file reports count findings from one reviewed file
- batch reports aggregate rule counts across all reviewed files
- findings are grouped by exact `rule_id`
- files with no findings do not create fake rule-specific entries
- Markdown report rule-count rows are sorted by `rule_id`

Because suppressed findings are removed before summaries and reports are built,
suppressed findings do not contribute to rule counts.

## Severity Counts

Severity counts are deterministic counts of findings grouped by severity.

Canonical buckets are:

- `critical`
- `error`
- `warning`
- `info`

Current behavior:

- `ReviewSummary.severity_counts` counts one reviewed file
- `BatchReviewSummary.severity_counts` aggregates across reviewed files
- the canonical result models keep all four severity buckets, including zeroes
- Markdown reports render severity counts in descending severity order:
  `critical`, `error`, `warning`, `info`

Because suppressed findings are removed before summaries are built, suppressed
findings do not contribute to severity counts.

## Quality Gates

`review` and `batch` support `--fail-on <severity>`.

When `--fail-on` is set, the command exits with code `1` if any unsuppressed
finding meets or exceeds the configured threshold. If `--fail-on` is omitted,
findings still appear in output, but successful commands continue to exit with
code `0`.

Examples:

```bash
uv run content-review review article.md --profile profile.yml --fail-on critical
```

Only `critical` findings fail the gate.

```bash
uv run content-review review article.md --profile profile.yml --fail-on error
```

`critical` and `error` findings fail the gate.

```bash
uv run content-review review article.md --profile profile.yml --fail-on warning
```

`critical`, `error`, and `warning` findings fail the gate.

```bash
uv run content-review review article.md --profile profile.yml --fail-on info
```

Any finding fails the gate.

Exit code effect for `review` and `batch`:

- `0`: command completed and the quality gate passed, or no quality gate was configured
- `1`: command completed, but at least one unsuppressed finding met the threshold
- `2`: command, input, profile, or filesystem error

Markdown reports also show:

- quality gate status
- configured `Fail On` threshold
- matched-gate finding count

## Suppression Comments

Inline suppression uses HTML comments with exact rule IDs.

Current syntax:

```markdown
This line contains an intentional claim. <!-- content-review-disable-line absolute_claims -->
```

```markdown
<!-- content-review-disable-next-line forbidden_terms -->
This line intentionally contains a configured term for documentation purposes.
```

Current behavior:

- suppression matches by exact `rule_id`
- `disable-line` affects the same physical line
- `disable-next-line` affects the next physical line
- multiple rule IDs are supported in one comment
- optional whitespace inside the HTML comment is tolerated
- only findings with location data can be suppressed
- suppressed findings are removed before summaries, reports, and quality-gate
  evaluation

Current non-goals:

- no profile-level suppression syntax
- no range-based suppression syntax
- no output field that marks a finding as suppressed after filtering

## Batch Review Behavior

Batch review reuses the same single-file review pipeline for each discovered
Markdown file, then aggregates the results.

Current aggregation behavior:

- file discovery is deterministic
- each reviewed file produces a canonical `ReviewResult`
- batch summary aggregates `finding_count`, `files_with_findings`, and
  `severity_counts` across reviewed files
- batch rule counts are computed from all findings across reviewed files
- files with no findings remain present in `results`, but they do not add
  artificial rule-count entries
- suppressed findings are already removed before batch aggregation

Batch review does not introduce different rule semantics. It reuses the same
rule execution, suppression filtering, and severity handling as single-file
review.

## Reports

Current report surfaces expose rule-system data in different forms:

- text output shows severity, `rule_id`, message, and location when available
- JSON output preserves the canonical review models and finding fields
- Markdown single-file reports include summary rows, severity counts, rule
  counts, findings tables, and detailed findings
- Markdown batch reports include aggregated severity counts, aggregated rule
  counts, per-file summaries, and per-file findings sections

Rule counts, severity counts, and quality-gate summaries are all derived from
unsuppressed findings in the canonical review results.

## Limits And Non-goals

Current limits and non-goals:

- deterministic rules only
- no LLM-based review
- no automatic rewriting or fixing
- no guarantee of legal, medical, advertising, regulatory, or platform
  compliance
- no contextual truth checking or evidence verification
- no remote link validation
- no HTML, SARIF, or annotation-specific rule output in the current rule system

This rule system helps catch configured wording and structural issues. It is not
a complete compliance or editorial assurance system.

## Future Rule Types

Possible future rule types may include additional deterministic checks such as:

- title-length rules
- paragraph-style or readability rules
- channel-specific policy heuristics
- richer Markdown structure checks

These are future possibilities only. They are not implemented by TASK-0026, and
this document does not expand the current rule behavior.
