# TASK-0028: Add Rule Registry And Rule Metadata

## Status

Planned

## Goal

Add a centralized rule registry and rule metadata model for the content review engine.

The project already has multiple built-in rules and a canonical rule reference in `docs/RULES.md`. However, current rule IDs and rule descriptions are still spread across implementation code, profile examples, tests, and documentation.

TASK-0028 should introduce a small, deterministic rule registry so that current and future rules have a single source of truth for metadata.

This task should not change rule matching behavior.

## Background

Previous tasks established the user-facing rule documentation:

* TASK-0026 added `docs/RULES.md`
* TASK-0027 made `docs/RULES.md` the canonical rule system reference
* `docs/REVIEW_RULES.md` is now only a compatibility stub

Current documented built-in rule IDs include:

```text id="4u3eex"
forbidden_terms
absolute_claims
markdown_structure
markdown_links_images
```

These rule IDs are used by:

* findings
* suppression comments
* rule counts
* Markdown reports
* JSON output
* quality gate explanations
* documentation
* tests

Before adding new rule types such as regex rules or platform policy rules, the project should have an internal registry that describes supported rules consistently.

## Scope

This task may modify:

* `src/content_review_engine/core/`
* `src/content_review_engine/review/`
* `src/content_review_engine/reports/`
* `src/content_review_engine/cli.py`
* `tests/`
* `docs/RULES.md`
* `docs/DATA_MODELS.md`
* `docs/PROFILES.md`
* `PROJECT_STATE.md`
* `CHANGELOG.md`

Exact file paths should be confirmed from the current repository structure before editing.

## Non-goals

This task must not:

* add new review rule types
* add regex rule support
* change rule matching behavior
* change suppression behavior
* change CLI output behavior unless only exposing existing metadata in help text is already clearly required
* change Markdown report format
* change JSON output schema
* change exit code behavior
* change existing profile format
* remove legacy profile compatibility
* introduce LLM-based review
* introduce platform-specific legal, medical, advertising, regulatory, or compliance guarantees

## Required Work

### 1. Inspect Current Rule Implementation

Before making changes, inspect the current implementation, tests, fixtures, and example profiles to confirm the current built-in rule IDs.

Pay special attention to:

```text id="0vsnli"
forbidden_terms
absolute_claims
markdown_structure
markdown_links_images
```

Do not add metadata for rule IDs that are not currently supported or referenced by the implementation, tests, fixtures, or example profiles.

### 2. Add Rule Metadata Model

Add a small rule metadata model.

Suggested name:

```text id="bu40m3"
RuleDefinition
```

Suggested fields:

```python id="nhn1x3"
rule_id: str
name: str
description: str
category: str
source: str
supports_suppression: bool
```

Possible `category` values:

```text id="koas8h"
terms
claims
markdown
links
```

Possible `source` values:

```text id="c8x7nt"
built-in
profile-driven
```

Keep the model simple. Do not over-engineer the rule system.

If the project already has a better location for core models, place the model there. Otherwise, prefer a focused module such as:

```text id="o1pqmw"
src/content_review_engine/core/rule_registry.py
```

or:

```text id="aovmf8"
src/content_review_engine/core/rules.py
```

### 3. Add Central Rule Registry

Add a deterministic registry for current supported rules.

Suggested public functions:

```python id="frwvat"
get_rule_definitions() -> tuple[RuleDefinition, ...]
get_rule_definition(rule_id: str) -> RuleDefinition | None
get_rule_ids() -> tuple[str, ...]
is_known_rule_id(rule_id: str) -> bool
```

Behavior requirements:

* rule IDs must be unique
* registry ordering must be deterministic
* lookup by `rule_id` should be exact
* unknown rule IDs should return `None` or `False`
* the registry should not perform rule matching
* the registry should not decide quality gate behavior
* the registry should not replace profile configuration

### 4. Register Current Built-in Rules

Register current built-in rules after verifying them against the codebase.

Expected registry entries:

```text id="84t8rw"
forbidden_terms
absolute_claims
markdown_structure
markdown_links_images
```

Suggested metadata direction:

#### `forbidden_terms`

* category: `terms`
* source: `profile-driven`
* purpose: detects forbidden or risky terms configured by the active profile
* supports suppression: true

#### `absolute_claims`

* category: `claims`
* source: confirm from implementation
* purpose: detects absolute or overconfident language patterns
* supports suppression: true

#### `markdown_structure`

* category: `markdown`
* source: confirm from implementation
* purpose: detects Markdown structure issues
* supports suppression: true

#### `markdown_links_images`

* category: `links`
* source: confirm from implementation
* purpose: detects Markdown link and image issues
* supports suppression: true

If the implementation shows different behavior, document and encode the actual behavior instead.

### 5. Add Unit Tests For Rule Registry

Add tests for the registry.

Suggested file:

```text id="gg69ua"
tests/test_rule_registry.py
```

Tests should verify:

* all current supported rule IDs are registered
* rule IDs are unique
* registry order is deterministic
* `get_rule_definition()` returns metadata for known rule IDs
* `get_rule_definition()` returns `None` for unknown rule IDs
* `is_known_rule_id()` returns true for known rules and false for unknown rules
* every rule has non-empty name, description, category, and source
* every rule declares whether it supports suppression

Tests should avoid overfitting to exact prose.

### 6. Connect Documentation To Registry Carefully

Update `docs/RULES.md` to mention that current built-in rule metadata is now centralized in the rule registry.

Do not make docs depend on generated output unless the project already has such a pattern.

The docs should still remain readable as plain Markdown.

### 7. Optional: Use Registry In Internal Validation

If there is already code that validates rule IDs for suppression or documentation tests, it may use the registry.

However, do not change existing suppression behavior in this task.

Important:

* if unknown rule IDs are currently tolerated in suppression comments, keep that behavior
* if unknown rule IDs are currently ignored, keep that behavior
* if profile-defined rule IDs are currently possible, do not block them

The registry should be additive and descriptive, not restrictive.

### 8. Update Data Model Documentation

Update `docs/DATA_MODELS.md` if appropriate.

Document that:

* findings contain `rule_id`
* current built-in rule metadata is centralized
* the registry is not part of the JSON output schema unless already exposed

Do not claim a JSON schema change unless one is actually made.

### 9. Update Project State

Update `PROJECT_STATE.md`.

Mention:

* TASK-0028 completed
* rule metadata registry added
* current built-in rule IDs are registered
* no rule behavior changed
* no CLI behavior changed unless explicitly true
* no output schema changed

### 10. Update Changelog

Update `CHANGELOG.md`.

Add a TASK-0028 entry describing:

* added rule metadata model
* added centralized rule registry
* registered current built-in rules
* added registry tests
* updated rule documentation
* no runtime review behavior changes

## Acceptance Criteria

TASK-0028 is complete when:

* a `RuleDefinition` or equivalent rule metadata model exists
* a centralized deterministic rule registry exists
* current supported built-in rule IDs are registered
* registry lookup functions are tested
* rule IDs are unique and deterministic
* documentation mentions the registry
* `PROJECT_STATE.md` is updated
* `CHANGELOG.md` is updated
* all tests pass
* no rule matching behavior changed
* no suppression behavior changed
* no report format changed
* no JSON schema changed
* no exit code behavior changed

## Validation Commands

Run:

```bash id="1uazvq"
uv run pytest
```

Optional manual checks:

```bash id="uo9iby"
grep -R "forbidden_terms" src tests docs
grep -R "absolute_claims" src tests docs
grep -R "markdown_structure" src tests docs
grep -R "markdown_links_images" src tests docs
```

