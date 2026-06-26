# TASK-0026: Add Rule System Reference

## Status

Planned

## Goal

Add a dedicated rule system reference document for the content review engine.

TASK-0025 introduced a Quickstart guide that shows users how to run the tool. TASK-0026 should explain what the rule system means, how current rule IDs behave, how severities are interpreted, how quality gates are evaluated, and how findings should be read.

This task is documentation-first. It should not add new review rule types.

## Background

The project already exposes rule-related concepts through review results, Markdown reports, profile examples, suppression comments, quality gates, CLI output, and tests.

Known rule-related concepts include:

* `rule_id`
* `severity`
* `message`
* `suggestion`
* `line`
* `column`
* `matched_text`
* `matched_term`
* `context`
* `suppressed`
* `quality_gate`
* `fail_on`
* severity counts
* rule counts

TASK-0025 Quickstart already documents suppression examples for rule IDs such as:

```text
absolute_claims
forbidden_terms
```

TASK-0026 should verify the currently supported rule IDs from the implementation, tests, fixtures, and example profiles, then document them clearly.

## Scope

This task may modify:

* `docs/RULES.md`
* `docs/CLI.md`
* `docs/PROFILES.md`
* `docs/CI.md`
* `README.md`
* `tests/test_rules_docs.py`
* existing documentation tests if needed
* `PROJECT_STATE.md`
* `CHANGELOG.md`

This task may add tests that verify the new rule documentation exists and contains key concepts.

## Non-goals

This task must not:

* add new rule types
* change existing rule matching behavior
* change suppression behavior
* change CLI behavior
* change report output format
* change JSON output schema
* change Markdown report structure
* change exit code behavior
* introduce LLM-based review
* introduce platform-specific compliance checking
* claim that deterministic rules guarantee legal, medical, advertising, regulatory, or platform compliance

## Required Work

### 1. Add `docs/RULES.md`

Create a new document:

```text
docs/RULES.md
```

The document should explain the rule system used by the project.

It should include the following sections:

```markdown
# Rule System

## Overview
## What Is A Rule?
## Rule IDs
## Current Built-in Rules
## Findings
## Severity Levels
## Severity Ordering
## Rule Counts
## Severity Counts
## Quality Gates
## Suppression Comments
## Batch Review Behavior
## Reports
## Limits And Non-goals
## Future Rule Types
```

### 2. Explain What A Rule Is

Document that a rule is a deterministic review check that can produce one or more findings.

Each finding should be associated with a `rule_id`.

Explain that `rule_id` is the stable identifier used for:

* classifying findings
* grouping rule counts
* applying suppression comments
* reading report output
* understanding quality gate results

### 3. Document Current Built-in Rules

Inspect the current implementation, tests, fixtures, and example profiles.

Document the currently supported built-in rule IDs.

Expected rule IDs based on existing docs and examples include:

```text
forbidden_terms
absolute_claims
```

Do not invent rule IDs that are not supported by the current implementation.

For each current rule, document:

* purpose
* typical use case
* profile configuration if applicable
* generated finding fields
* suppression example
* limitations

For `forbidden_terms`, document that it detects configured forbidden or risky terms from the active review profile.

For `absolute_claims`, document the current behavior based on the implementation and profile examples. If the rule is example-profile-driven rather than hardcoded, explain that accurately.

### 4. Document Finding Fields

Document the key fields users may see in review output.

At minimum, explain:

```text
rule_id
severity
message
suggestion
line
column
matched_text
matched_term
context
```

Clarify that not every field is necessarily populated for every rule.

### 5. Document Severity Levels

Document the canonical severity levels:

```text
critical
error
warning
info
```

Document the severity order from most severe to least severe:

```text
critical > error > warning > info
```

Explain how this ordering is used by quality gates.

### 6. Document Quality Gate Behavior

Document how `--fail-on` works.

Examples:

```bash
uv run content-review review article.md --profile profile.yml --fail-on critical
```

Only `critical` findings should fail the quality gate.

```bash
uv run content-review review article.md --profile profile.yml --fail-on error
```

`critical` and `error` findings should fail the quality gate.

```bash
uv run content-review review article.md --profile profile.yml --fail-on warning
```

`critical`, `error`, and `warning` findings should fail the quality gate.

```bash
uv run content-review review article.md --profile profile.yml --fail-on info
```

Any finding should fail the quality gate.

Document that quality gate behavior affects process exit codes for review and batch commands.

### 7. Document Rule Counts

Document how rule counts are calculated.

Rules:

* findings are grouped by `rule_id`
* counts should be deterministic
* single-file reports count findings in one reviewed file
* batch reports aggregate rule counts across reviewed files
* files with no findings should not create fake rule count entries

### 8. Document Severity Counts

Document how severity counts are calculated.

Rules:

* findings are grouped by severity
* canonical severity buckets are `critical`, `error`, `warning`, and `info`
* counts appear in review summaries and Markdown reports
* batch severity counts aggregate across reviewed files

### 9. Document Suppression Comments

Document the current inline suppression syntax.

Include examples:

```markdown
This line contains an intentional claim. <!-- content-review-disable-line absolute_claims -->
```

```markdown
<!-- content-review-disable-next-line forbidden_terms -->
This line intentionally contains a configured term for documentation purposes.
```

Explain:

* `content-review-disable-line <rule_id>` suppresses findings for the same line
* `content-review-disable-next-line <rule_id>` suppresses findings for the next line
* suppression should be scoped to a specific rule ID
* suppression should be used sparingly and intentionally

Do not introduce new suppression syntax.

### 10. Document Batch Review Rule Behavior

Document that batch review applies the same rule system to each discovered Markdown file.

Clarify that batch review aggregates:

* total findings
* files with findings
* severity counts
* rule counts
* quality gate matched findings

### 11. Link `docs/RULES.md` From Existing Docs

Add references to `docs/RULES.md` from:

* `README.md`
* `docs/CLI.md`
* `docs/PROFILES.md`
* `docs/CI.md`
* `docs/QUICKSTART.md`

Avoid duplicating all rule details in each document. Prefer short links such as:

```markdown
For rule IDs, severity levels, suppression comments, and quality gate semantics, see [Rule System](RULES.md).
```

Use correct relative links depending on the source document location.

### 12. Add Documentation Tests

Add a new test file:

```text
tests/test_rules_docs.py
```

The tests should verify that:

* `docs/RULES.md` exists
* it documents `rule_id`
* it documents `forbidden_terms`
* it documents `absolute_claims` if currently supported or referenced by existing docs/profile examples
* it documents all canonical severities
* it documents severity ordering
* it documents `--fail-on`
* it documents `content-review-disable-line`
* it documents `content-review-disable-next-line`
* it documents rule counts
* it documents severity counts
* it documents quality gate behavior
* README and key docs link to `docs/RULES.md`

Keep tests focused on durable content. Avoid testing excessive wording.

### 13. Update Project State

Update `PROJECT_STATE.md`.

Mention:

* TASK-0026 completed
* `docs/RULES.md` added
* current rule system is now documented
* no new rule behavior was introduced
* no CLI behavior was changed
* no output schema was changed

### 14. Update Changelog

Update `CHANGELOG.md`.

Add a TASK-0026 entry describing:

* added rule system reference
* documented built-in rule IDs
* documented severity levels and ordering
* documented quality gate semantics
* documented suppression comments
* added documentation coverage tests

## Acceptance Criteria

TASK-0026 is complete when:

* `docs/RULES.md` exists
* current supported rule IDs are documented
* `forbidden_terms` is documented
* `absolute_claims` is documented if currently supported or referenced by current docs/profile examples
* finding fields are documented
* severity levels are documented
* severity ordering is documented
* quality gate behavior is documented
* rule counts are documented
* severity counts are documented
* suppression comments are documented
* batch rule aggregation behavior is documented
* existing docs link to `docs/RULES.md`
* documentation tests are added
* `PROJECT_STATE.md` is updated
* `CHANGELOG.md` is updated
* all tests pass

## Validation Commands

Run:

```bash
uv run pytest
```

Optional manual checks:

```bash
uv run content-review --help
uv run content-review review --help
uv run content-review batch --help
uv run content-review profile --help
```
