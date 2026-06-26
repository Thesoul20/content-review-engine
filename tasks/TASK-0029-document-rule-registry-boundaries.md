# TASK-0029: Document Rule Registry Boundaries

## Status

Planned

## Goal

Document and stabilize the boundary between the rule metadata registry and the rule execution registry.

TASK-0028 added a centralized rule metadata registry in:

```text
src/content_review_engine/core/rule_registry.py
```

The repository also already has an execution-oriented registry in:

```text
src/content_review_engine/rules/registry.py
```

These two registries serve different purposes. TASK-0029 should make that boundary explicit in documentation and tests so future work can safely add regex rules, additional deterministic rules, and LLM-based semantic review without mixing responsibilities.

This task is documentation and architecture clarification focused. It must not change runtime review behavior.

## Background

The project is moving toward a hybrid content review architecture:

```text
Deterministic rules + LLM semantic review
```

The deterministic rule engine provides:

* stable rule IDs
* predictable findings
* suppression support
* quality gates
* JSON / Markdown / text reports
* CI-friendly exit codes
* low-cost batch review

The future LLM review layer should provide:

* semantic risk detection
* contextual judgment
* rewrite suggestions
* rationale
* confidence scoring
* optional review modes

Before adding more rule capabilities or LLM review, the project needs a clear architectural boundary:

```text
Rule metadata registry:
  describes known rule IDs and metadata

Rule execution registry:
  decides which deterministic rule implementations are executed

LLM review layer:
  should produce compatible findings later, but should not be mixed into the deterministic execution registry yet
```

## Current Registry Concepts

### Metadata Registry

Current file:

```text
src/content_review_engine/core/rule_registry.py
```

Current purpose:

* describes current built-in rule IDs
* exposes metadata through `RuleDefinition`
* provides helper functions such as:

  * `get_rule_definitions()`
  * `get_rule_definition(rule_id)`
  * `get_rule_ids()`
  * `is_known_rule_id(rule_id)`

This registry is descriptive.

It should not:

* execute rules
* parse Markdown
* match content
* validate profile behavior restrictively
* change suppression behavior
* change quality gate behavior

### Execution Registry

Current file:

```text
src/content_review_engine/rules/registry.py
```

Current purpose:

* owns deterministic rule execution registration
* decides which rule implementations participate in review
* belongs to the runtime review pipeline

This registry is operational.

It should not be treated as the public rule metadata source for docs, profile help, or future CLI metadata display.

## Scope

This task may modify:

* `docs/ARCHITECTURE.md`
* `docs/RULES.md`
* `docs/DATA_MODELS.md`
* `docs/PROFILES.md`
* `src/content_review_engine/core/rule_registry.py`
* `src/content_review_engine/rules/registry.py`
* tests related to registry documentation or module boundaries
* `PROJECT_STATE.md`
* `CHANGELOG.md`

This task may add architecture-focused documentation tests.

Suggested test file:

```text
tests/test_rule_registry_boundaries.py
```

## Non-goals

This task must not:

* add regex rule support
* add new review rule types
* add LLM review behavior
* change rule matching behavior
* change suppression behavior
* change CLI behavior
* change Markdown report format
* change JSON output schema
* change exit code behavior
* change profile parsing behavior
* merge the two registries
* remove either registry
* refactor the review pipeline
* introduce platform-specific compliance guarantees

## Required Work

### 1. Inspect Both Registries

Inspect:

```text
src/content_review_engine/core/rule_registry.py
src/content_review_engine/rules/registry.py
```

Identify the current responsibilities of each module.

Do not change runtime behavior.

### 2. Update Architecture Documentation

Update:

```text
docs/ARCHITECTURE.md
```

Add a section explaining the registry boundary.

Suggested section title:

```markdown
## Rule Registry Boundaries
```

This section should explain:

* the metadata registry is descriptive
* the execution registry is operational
* why both exist
* why they should not be merged yet
* how future deterministic rules should interact with them
* how future LLM review should fit alongside them

Include a simple architecture diagram in text form:

```text
Markdown Input
  ↓
Profile Loading
  ↓
Deterministic Rule Execution Registry
  ↓
Rule Findings
  ↓
Optional Future LLM Semantic Review
  ↓
Merged Findings
  ↓
Reports / Quality Gate / Exit Codes
```

Also include the metadata side:

```text
Rule Metadata Registry
  ↓
Docs / Tests / Future CLI metadata display / Profile guidance
```

Clarify that the metadata registry does not execute rules.

### 3. Update Rule System Documentation

Update:

```text
docs/RULES.md
```

Add a short explanation that:

* `docs/RULES.md` is the canonical user-facing rule reference
* `core/rule_registry.py` is the internal metadata source for built-in rule metadata
* `rules/registry.py` remains responsible for deterministic rule execution
* LLM semantic review will be a separate future layer and should still produce compatible findings if added later

Do not over-expand the LLM section. Keep it as future architecture guidance only.

### 4. Update Data Model Documentation

Update:

```text
docs/DATA_MODELS.md
```

Clarify that:

* `rule_id` remains the stable identifier used in findings
* rule metadata is internal and does not change the JSON output schema
* future LLM findings should map into the same finding model or a compatible extension
* this task does not introduce an LLM finding schema yet

### 5. Update Profile Documentation

Update:

```text
docs/PROFILES.md
```

Clarify that:

* profiles configure deterministic rule behavior
* metadata registry does not replace profile configuration
* execution registry decides which deterministic rules run
* future LLM review configuration should be introduced separately and should not be mixed into current profile behavior in this task

### 6. Optional Code Comments

If helpful, add short module-level docstrings to:

```text
src/content_review_engine/core/rule_registry.py
src/content_review_engine/rules/registry.py
```

The docstrings should clarify the boundary between metadata and execution.

Do not change behavior.

Example direction for `core/rule_registry.py`:

```python
"""Built-in rule metadata registry.

This module describes known rule IDs and their metadata. It does not execute rules.
"""
```

Example direction for `rules/registry.py`:

```python
"""Deterministic rule execution registry.

This module owns runtime rule registration and execution wiring. It is separate from rule metadata.
"""
```

Only add comments/docstrings if they fit the existing style.

### 7. Add Boundary Tests

Add or update tests to ensure the documentation and module boundaries remain clear.

Suggested file:

```text
tests/test_rule_registry_boundaries.py
```

Tests should verify:

* `docs/ARCHITECTURE.md` documents the metadata registry
* `docs/ARCHITECTURE.md` documents the execution registry
* `docs/ARCHITECTURE.md` explains that metadata registry does not execute rules
* `docs/RULES.md` references the metadata registry
* `docs/RULES.md` distinguishes metadata from execution
* `docs/DATA_MODELS.md` says the registry does not change JSON schema
* `docs/PROFILES.md` says metadata does not replace profile configuration
* optional module docstrings mention metadata vs execution if docstrings are added

Keep tests focused on durable concepts, not exact prose.

### 8. Update Project State

Update:

```text
PROJECT_STATE.md
```

Mention:

* TASK-0029 completed
* metadata registry and execution registry boundary documented
* hybrid direction remains deterministic rules first, with future LLM semantic review as a separate layer
* no runtime behavior changed
* no output schema changed

### 9. Update Changelog

Update:

```text
CHANGELOG.md
```

Add a TASK-0029 entry describing:

* documented metadata registry vs execution registry boundary
* clarified future LLM review placement
* updated architecture, rule, data model, and profile docs
* added documentation tests
* no runtime behavior changes

## Acceptance Criteria

TASK-0029 is complete when:

* `docs/ARCHITECTURE.md` documents the metadata registry vs execution registry boundary
* `docs/RULES.md` explains the boundary clearly
* `docs/DATA_MODELS.md` clarifies that registry metadata does not change JSON schema
* `docs/PROFILES.md` clarifies that metadata does not replace profile configuration
* future LLM review is described only as a separate future layer
* tests cover the durable boundary documentation
* `PROJECT_STATE.md` is updated
* `CHANGELOG.md` is updated
* all tests pass
* no rule behavior changed
* no suppression behavior changed
* no CLI behavior changed
* no report format changed
* no JSON schema changed
* no exit code behavior changed

## Validation Commands

Run:

```bash
uv run pytest
```

Optional manual checks:

```bash
grep -R "metadata registry" docs src tests
grep -R "execution registry" docs src tests
grep -R "LLM" docs/ARCHITECTURE.md docs/RULES.md docs/DATA_MODELS.md docs/PROFILES.md
```
