
# TASK-0017: Add Forbidden Terms Allowlist and Inline Suppression

## Status

Planned

## Goal

Add explicit suppression support for false positives in content review results.

After TASK-0016, the CLI can fail when findings meet or exceed a configured severity threshold. This is useful for CI and publishing gates, but it also means false positives can block a publishing workflow.

This task adds two lightweight suppression mechanisms:

1. `allow_terms` support for the `forbidden_terms` rule.
2. Markdown inline suppression comments for line-level findings.

The goal is to make the review engine practical for real publishing workflows without weakening the quality gate globally.

## Background

The project currently supports:

* Markdown reading
* YAML `ReviewProfile` loading
* `forbidden_terms` review rule
* Single-file review command
* Batch review command
* Text / JSON / Markdown output
* CLI quality gate via `--fail-on`
* CI-friendly exit codes

However, the current behavior treats every finding as active.

This creates a problem:

```text
A term may be configured as forbidden globally,
but in one specific article it may be intentionally used,
quoted, explained, or used as a negative example.
```

For example:

```markdown
不要在标题中使用“全网最强”这样的绝对化表达。
```

If `全网最强` is configured as a forbidden term, the line above may still be flagged even though the article is warning against using that phrase.

This task introduces explicit suppression so users can mark such cases intentionally.

## Scope

This task includes:

1. Add optional `allow_terms` support to the `forbidden_terms` rule configuration.
2. Add inline Markdown suppression comment parsing.
3. Support `content-review-disable-line <rule_id>` comments.
4. Support `content-review-disable-next-line <rule_id>` comments.
5. Suppress matching findings before output rendering.
6. Ensure suppressed findings do not affect quality gate decisions.
7. Ensure suppressed findings do not affect batch severity counts.
8. Add unit tests for allowlist behavior.
9. Add unit tests for inline suppression behavior.
10. Add CLI tests showing that suppressed findings do not fail `--fail-on`.
11. Update documentation.
12. Update `PROJECT_STATE.md`.
13. Update `CHANGELOG.md`.

## Non-goals

This task must not implement:

* New review rules
* LLM-based review
* Auto-fix behavior
* Block-level suppression
* File-level suppression
* Suppression reason fields
* Suppression expiration dates
* External allowlist files
* Regex allowlist
* Wildcard allowlist
* `.gitignore` support
* API server
* MCP server
* Frontend UI
* Database persistence
* Publishing integration

## Profile Design

The `forbidden_terms` rule should support an optional `allow_terms` field.

Example:

```yaml
rules:
  - id: forbidden_terms
    enabled: true
    severity: error
    terms:
      - 全网最强
      - 永久有效
      - 绝对安全
    allow_terms:
      - 永久有效
```

Expected behavior:

* `全网最强` should still be flagged.
* `绝对安全` should still be flagged.
* `永久有效` should not be flagged.
* If `allow_terms` is omitted, existing behavior should remain unchanged.
* If `allow_terms` is empty, existing behavior should remain unchanged.

## Allow Terms Behavior

For this task, `allow_terms` should be simple and deterministic.

Rules:

1. `allow_terms` only applies to the `forbidden_terms` rule.
2. `allow_terms` is a list of literal strings.
3. If a forbidden term exactly matches an item in `allow_terms`, it should not produce a finding.
4. Matching behavior should follow the current `forbidden_terms` matching behavior as much as possible.
5. Do not implement regex matching.
6. Do not implement wildcard matching.
7. Do not implement fuzzy matching.
8. Do not implement case normalization unless the existing `forbidden_terms` rule already does so.

Invalid example:

```yaml
rules:
  - id: forbidden_terms
    enabled: true
    severity: error
    terms:
      - 全网最强
    allow_terms: "全网最强"
```

Expected behavior:

* The profile loader should reject invalid `allow_terms` values.
* `allow_terms` must be a list of strings.

## Inline Suppression Design

The review engine should support Markdown HTML comments for line-level suppression.

### Disable Current Line

Syntax:

```markdown
This line contains 全网最强. <!-- content-review-disable-line forbidden_terms -->
```

Expected behavior:

* Findings from `forbidden_terms` on the same physical line should be suppressed.
* Findings from other rules should not be suppressed.

### Disable Next Line

Syntax:

```markdown
<!-- content-review-disable-next-line forbidden_terms -->
This line contains 全网最强.
```

Expected behavior:

* Findings from `forbidden_terms` on the next physical line should be suppressed.
* Findings from other rules should not be suppressed.

## Supported Inline Comment Forms

The following forms should be supported:

```markdown
<!-- content-review-disable-line forbidden_terms -->
<!-- content-review-disable-next-line forbidden_terms -->
```

Optional whitespace should be tolerated:

```markdown
<!--content-review-disable-line forbidden_terms-->
<!--  content-review-disable-line forbidden_terms  -->
```

Multiple rule IDs may be supported if implementation is simple:

```markdown
<!-- content-review-disable-line forbidden_terms absolute_claims -->
```

However, this task only needs to test `forbidden_terms`, because it is currently the active content rule.

## Unsupported Inline Comment Forms

The following are out of scope for this task:

```markdown
<!-- content-review-disable forbidden_terms -->
<!-- content-review-enable forbidden_terms -->
<!-- content-review-disable-file forbidden_terms -->
<!-- content-review-disable-block forbidden_terms -->
<!-- content-review-disable-line all -->
```

Do not implement block-level enable / disable behavior in this task.

## Suppression Rules

A finding should be suppressed when all conditions are true:

1. The finding has a line number.
2. A matching suppression directive exists for that line.
3. The finding's `rule_id` matches the directive's rule id.

Suppressed findings should:

* Not appear in default text output.
* Not appear in default JSON output.
* Not appear in default Markdown output.
* Not count toward `severity_counts`.
* Not count toward batch `finding_count`.
* Not cause `--fail-on` quality gate failure.

## Output Behavior

Existing output behavior should remain stable.

This task should not introduce a new output format.

Default behavior:

```text
Only active, unsuppressed findings are included in output.
```

This means suppressed findings should be filtered before serialization and rendering.

Do not add `--show-suppressed` in this task.

## Suggested Internal Design

Add a small helper module if appropriate:

```text
src/content_review_engine/core/suppression.py
```

Suggested model:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class SuppressionDirective:
    line: int
    rule_ids: tuple[str, ...]
```

Suggested helper functions:

```python
def parse_inline_suppressions(markdown: str) -> list[SuppressionDirective]:
    """Parse inline suppression comments from Markdown text."""
    ...


def finding_is_suppressed(
    finding: ReviewFinding,
    directives: list[SuppressionDirective],
) -> bool:
    """Return whether a finding should be suppressed."""
    ...


def filter_suppressed_findings(
    findings: list[ReviewFinding],
    directives: list[SuppressionDirective],
) -> list[ReviewFinding]:
    """Return findings after removing suppressed findings."""
    ...
```

The exact names may differ based on the current codebase.

## Integration Point

Suppression should be applied after rule execution and before output serialization.

Recommended flow:

```text
Markdown input
  ↓
ReviewProfile loading
  ↓
Rule execution
  ↓
Inline suppression parsing
  ↓
Suppression filtering
  ↓
ReviewResult creation / serialization
  ↓
Quality gate evaluation
  ↓
CLI output and exit code
```

The key requirement is:

```text
The quality gate must evaluate only unsuppressed findings.
```

## Batch Behavior

For batch review:

* Each Markdown file should apply its own inline suppressions.
* Suppressed findings should not appear in that file's review result.
* Batch summary should aggregate only unsuppressed findings.
* Batch quality gate should evaluate only unsuppressed findings.

Example:

```markdown
<!-- content-review-disable-next-line forbidden_terms -->
This line contains 全网最强.
```

If this is the only finding in the file, then batch summary should report:

```text
finding_count = 0
files_with_findings = 0
severity_counts.error = 0
```

## CLI Behavior

No new CLI flag is required for this task.

Existing commands should automatically respect suppression behavior:

```bash
content-review review article.md --profile profile.yaml
content-review review article.md --profile profile.yaml --fail-on error
content-review batch ./articles --profile profile.yaml
content-review batch ./articles --profile profile.yaml --fail-on error
```

Expected behavior:

* Suppressed findings do not appear in output.
* Suppressed findings do not fail the quality gate.
* Existing CLI options remain compatible.

## Testing Requirements

Add tests for `allow_terms`.

Suggested cases:

```text
forbidden term not in allow_terms produces finding
forbidden term in allow_terms does not produce finding
missing allow_terms preserves existing behavior
empty allow_terms preserves existing behavior
invalid allow_terms type is rejected
```

Add tests for inline suppression parsing.

Suggested cases:

```text
disable-line suppresses finding on same line
disable-next-line suppresses finding on next line
disable-line does not suppress findings on other lines
disable-next-line does not suppress findings two lines later
suppression for another rule id does not suppress forbidden_terms
optional whitespace in suppression comment is tolerated
```

Add tests for quality gate integration.

Suggested cases:

```text
review with suppressed error finding exits 0 when --fail-on error
review with unsuppressed error finding exits 1 when --fail-on error
batch with suppressed error finding exits 0 when --fail-on error
batch with unsuppressed error finding exits 1 when --fail-on error
```

Add tests for batch summary.

Suggested cases:

```text
suppressed findings are not counted in finding_count
suppressed findings are not counted in files_with_findings
suppressed findings are not counted in severity_counts
```

## Documentation Updates

Update CLI documentation with examples.

### Inline Suppression Example

```markdown
This sentence intentionally mentions 全网最强. <!-- content-review-disable-line forbidden_terms -->
```

### Next Line Suppression Example

```markdown
<!-- content-review-disable-next-line forbidden_terms -->
This sentence intentionally mentions 全网最强.
```

### Allow Terms Example

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

Explain that:

* `allow_terms` suppresses configured forbidden terms globally for the profile.
* Inline comments suppress findings only for specific lines.
* Suppressed findings do not affect `--fail-on`.

Update `PROJECT_STATE.md` with:

* TASK-0017 completed
* `forbidden_terms.allow_terms` support added
* Inline suppression comments added
* Quality gate now ignores explicitly suppressed findings

Update `CHANGELOG.md` with:

* Added `allow_terms` for `forbidden_terms`
* Added line-level inline suppression comments
* Suppressed findings are excluded from output, batch summary, and quality gate checks

## Acceptance Criteria

This task is complete when:

1. `forbidden_terms` supports optional `allow_terms`.
2. Invalid `allow_terms` values are rejected.
3. `content-review-disable-line forbidden_terms` suppresses findings on the same line.
4. `content-review-disable-next-line forbidden_terms` suppresses findings on the next line.
5. Suppressed findings do not appear in default output.
6. Suppressed findings do not count toward batch summaries.
7. Suppressed findings do not trigger `--fail-on`.
8. Existing single-file review behavior remains compatible when no suppression is used.
9. Existing batch review behavior remains compatible when no suppression is used.
10. Existing quality gate behavior remains compatible when no suppression is used.
11. Unit tests are added for allowlist behavior.
12. Unit tests are added for inline suppression behavior.
13. CLI integration tests are added for suppression with `--fail-on`.
14. Documentation is updated.
15. `PROJECT_STATE.md` is updated.
16. `CHANGELOG.md` is updated.
17. `uv run pytest` passes.

## Suggested Test Command

```bash
uv run pytest
```

## Implementation Notes

Recommended implementation order:

1. Inspect current `ReviewProfile` and rule configuration models.
2. Add optional `allow_terms` to the `forbidden_terms` rule configuration.
3. Update YAML profile loading validation.
4. Update `forbidden_terms` rule behavior.
5. Add tests for `allow_terms`.
6. Add `core/suppression.py`.
7. Add inline suppression parser tests.
8. Integrate suppression filtering into the review pipeline.
9. Add CLI tests for review + `--fail-on`.
10. Add CLI tests for batch + `--fail-on`.
11. Update documentation, `PROJECT_STATE.md`, and `CHANGELOG.md`.
12. Run the full test suite.

