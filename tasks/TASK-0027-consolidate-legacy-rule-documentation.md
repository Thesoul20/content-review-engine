# TASK-0027: Consolidate Legacy Rule Documentation

## Status

Planned

## Goal

Consolidate legacy rule documentation after `docs/RULES.md` was added in TASK-0026.

TASK-0026 introduced `docs/RULES.md` as the dedicated rule system reference. The repository still contains the older `docs/REVIEW_RULES.md`. TASK-0027 should remove ambiguity between these documents by making `docs/RULES.md` the canonical rule reference.

This task is documentation-focused. It must not change review behavior.

## Background

TASK-0026 completed the new rule system reference:

```text
docs/RULES.md
```

It documents:

* rule concepts
* stable rule IDs
* current built-in rules
* finding fields
* severity levels
* severity ordering
* quality gate behavior
* suppression comments
* rule counts
* severity counts
* batch aggregation behavior
* report behavior
* limits and future rule directions

However, the repository still contains:

```text
docs/REVIEW_RULES.md
```

Having two rule-related documents may confuse users and future contributors unless their relationship is clarified.

TASK-0027 should consolidate or retire the legacy rule documentation.

## Scope

This task may modify:

* `docs/REVIEW_RULES.md`
* `docs/RULES.md`
* `docs/README` references if any exist
* `README.md`
* `docs/QUICKSTART.md`
* `docs/CLI.md`
* `docs/PROFILES.md`
* `docs/CI.md`
* documentation tests
* `PROJECT_STATE.md`
* `CHANGELOG.md`

This task may add or update tests to ensure that user-facing docs consistently point to the canonical rule reference.

## Non-goals

This task must not:

* add new review rule types
* remove existing supported rule behavior
* change rule matching behavior
* change suppression behavior
* change CLI behavior
* change Markdown report format
* change JSON output schema
* change exit code behavior
* introduce LLM-based review
* introduce platform-specific compliance checking
* rename `docs/RULES.md`
* rewrite unrelated documentation

## Required Work

### 1. Inspect Legacy Rule Documentation

Inspect:

```text
docs/REVIEW_RULES.md
docs/RULES.md
```

Determine whether `docs/REVIEW_RULES.md` contains any useful information that is missing from `docs/RULES.md`.

If useful information exists, migrate it into `docs/RULES.md`.

Do not duplicate outdated or conflicting content.

### 2. Decide How To Handle `docs/REVIEW_RULES.md`

Use one of the following approaches.

Preferred approach:

Replace `docs/REVIEW_RULES.md` with a short compatibility stub that points to `docs/RULES.md`.

Example:

```markdown
# Review Rules

This document has been superseded by [Rule System](RULES.md).

Please use `docs/RULES.md` as the canonical reference for rule IDs, severities, suppression comments, quality gates, rule counts, severity counts, and report behavior.
```

Alternative approach:

Delete `docs/REVIEW_RULES.md` only if no existing documentation, tests, or expected references depend on it.

Prefer the compatibility stub if deletion could break links or confuse existing users.

### 3. Make `docs/RULES.md` Canonical

Ensure `docs/RULES.md` clearly states that it is the canonical rule system reference.

It should include wording similar to:

```markdown
This document is the canonical reference for the content review rule system.
```

### 4. Update Cross-References

Search the repository for references to:

```text
REVIEW_RULES.md
Review Rules
docs/REVIEW_RULES.md
```

Update references so that user-facing documentation points to:

```text
docs/RULES.md
```

At minimum, check:

```text
README.md
docs/QUICKSTART.md
docs/CLI.md
docs/PROFILES.md
docs/CI.md
PROJECT_STATE.md
CHANGELOG.md
tests/
```

If `docs/REVIEW_RULES.md` is kept as a compatibility stub, references inside historical changelog entries do not need to be rewritten unless they are misleading in the current documentation section.

### 5. Update Documentation Tests

Update or add tests so that:

* `docs/RULES.md` exists
* `docs/RULES.md` is identified as the canonical rule reference
* current user-facing docs link to `docs/RULES.md`
* no current user-facing doc incorrectly treats `docs/REVIEW_RULES.md` as the primary rule reference
* if `docs/REVIEW_RULES.md` remains, it clearly points to `docs/RULES.md`

Suggested test file:

```text
tests/test_rule_doc_consolidation.py
```

Alternatively, extend:

```text
tests/test_rules_docs.py
```

Prefer focused tests. Do not overfit tests to exact prose.

### 6. Update Project State

Update `PROJECT_STATE.md`.

Mention:

* TASK-0027 completed
* `docs/RULES.md` is now the canonical rule system reference
* `docs/REVIEW_RULES.md` was either replaced by a compatibility stub or removed
* no behavior changed

### 7. Update Changelog

Update `CHANGELOG.md`.

Add a TASK-0027 entry describing:

* consolidated legacy rule documentation
* made `docs/RULES.md` canonical
* updated cross-document links
* added or updated documentation tests
* no runtime behavior changes

## Acceptance Criteria

TASK-0027 is complete when:

* `docs/RULES.md` is clearly the canonical rule reference
* `docs/REVIEW_RULES.md` no longer competes with `docs/RULES.md`
* any useful legacy content has been migrated into `docs/RULES.md`
* user-facing docs link to `docs/RULES.md`
* documentation tests cover the canonical rule reference behavior
* `PROJECT_STATE.md` is updated
* `CHANGELOG.md` is updated
* all tests pass
* no runtime behavior changed

## Validation Commands

Run:

```bash
uv run pytest
```

Optional manual checks:

```bash
grep -R "REVIEW_RULES.md" .
grep -R "Rule System" README.md docs tests
```
