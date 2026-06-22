# TASK-0004: Add Forbidden Terms Rule

## Status

Planned

## Type

Feature / Deterministic Rule

## Priority

High

## Depends On

* TASK-0001: Project Skeleton
* TASK-0002: Core Data Models
* TASK-0002.5: Package Import Config
* TASK-0003: Markdown Reader and Profile Loading

## Precondition

Before starting this task, TASK-0003 must already have a dedicated Git commit.

Expected TASK-0003 commit message:

```bash
feat(task-0003): add markdown parser and profile loader
```

Do not start implementing TASK-0004 if TASK-0003 changes are still uncommitted.

## Background

The project currently has the basic input layer:

* Markdown files can be read through the parser module.
* YAML review profiles can be loaded through the config module.
* `profiles/wechat.yaml` exists as the first platform profile example.
* Unit tests for Markdown reading and profile loading are already in place.

However, the project cannot yet produce any actual review findings.

This task adds the first deterministic review rule, so the engine can move from “reading input” to “generating structured review findings”.

## Goal

Add the first deterministic review rule:

> Detect whether the Markdown content contains forbidden terms configured in the review profile.

The rule id should be:

```text
forbidden_terms
```

The rule should scan Markdown text directly and return structured review findings when configured terms are found.

## Scope

This task includes:

1. Add a new deterministic rules module.
2. Add a forbidden terms rule.
3. Add or extend profile configuration to support forbidden terms.
4. Return structured review findings.
5. Add unit tests for the rule.
6. Update architecture documentation.
7. Update project state.
8. Update changelog.
9. Run the full test suite.
10. Create a dedicated Git commit for TASK-0004.

## Non-Goals

This task must not implement:

* LLM-based review
* Full review pipeline
* CLI entrypoint
* API server
* MCP server
* Frontend
* Markdown auto-rewrite
* Markdown AST parsing
* Complex line and column location tracking
* Rule registry
* Rule scheduler
* Multi-rule orchestration

Those should be handled by future TASK files.

## Expected Files

The implementation may modify or create the following files:

```text
src/content_review_engine/rules/__init__.py
src/content_review_engine/rules/forbidden_terms.py
src/content_review_engine/core/models.py
profiles/wechat.yaml
tests/test_forbidden_terms_rule.py
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

If existing models are already sufficient, reuse them instead of introducing duplicate abstractions.

## Model Review Requirement

Before implementing the rule, inspect:

```text
src/content_review_engine/core/models.py
```

Check whether the project already has models such as:

* `ReviewProfile`
* `ReviewFinding`
* `ReviewSeverity`
* `ReviewRule`
* `RuleResult`

Implementation rules:

1. Prefer reusing existing models.
2. If a model is missing only a small field, extend it minimally.
3. If no review finding model exists, add a minimal `ReviewFinding` model.
4. Do not introduce a large rule framework in this task.

## Profile Configuration

Update `profiles/wechat.yaml` to include a simple forbidden terms configuration.

Suggested shape:

```yaml
forbidden_terms:
  - 绝对安全
  - 保证赚钱
  - 100%有效
```

If `ReviewProfile` already uses another compatible field name, follow the existing model instead of inventing a second naming style.

The profile loader should continue to use Pydantic validation.

## Rule Function

Add a function similar to:

```python
def check_forbidden_terms(
    markdown_text: str,
    profile: ReviewProfile,
) -> list[ReviewFinding]:
    ...
```

The exact function name may be adjusted to match the current code style, but it must be clear and easy to test.

## Rule Behavior

The rule must:

1. Accept Markdown text as `str`.
2. Accept a loaded `ReviewProfile`.
3. Read forbidden terms from the profile.
4. Scan the full Markdown text.
5. Return an empty list if there are no configured terms.
6. Return an empty list if no term is found.
7. Return one or more findings if terms are found.
8. Support detecting multiple forbidden terms.
9. Avoid raising errors when the forbidden terms list is empty.

Each finding should include, as far as the current model allows:

* Rule id: `forbidden_terms`
* Severity: `warning` or the closest existing severity value
* Message, for example: `发现风险词：保证赚钱`
* Matched term or matched text

Do not implement automatic replacement suggestions unless the existing model already supports it naturally.

## Tests

Add:

```text
tests/test_forbidden_terms_rule.py
```

The tests must cover at least:

### 1. Single Term Match

Given Markdown text containing one forbidden term, the rule returns one finding.

### 2. No Match

Given Markdown text containing no forbidden terms, the rule returns an empty list.

### 3. Multiple Term Matches

Given Markdown text containing multiple forbidden terms, the rule returns multiple findings.

### 4. Empty Forbidden Terms

Given a profile with an empty forbidden terms list, the rule returns an empty list and does not raise.

### 5. Full Test Suite

Run:

```bash
uv run pytest
```

All tests must pass.

## Documentation Updates

Update:

```text
docs/ARCHITECTURE.md
```

Add the deterministic rules layer to the current architecture.

Suggested architecture description:

```text
Markdown Input
    ↓
Profile Loading
    ↓
Deterministic Rules
    ↓
Review Findings
```

Mention that the first implemented deterministic rule is:

```text
forbidden_terms
```

Also clarify that LLM review, CLI, and full review pipeline are not implemented yet.

## Project State Update

Update:

```text
PROJECT_STATE.md
```

The update should mention:

* TASK-0004 is completed.
* The first deterministic rule has been added.
* The rule detects forbidden terms from the loaded profile.
* The project still does not have a full review pipeline, CLI, API, MCP interface, or LLM review.

## Changelog Update

Update:

```text
CHANGELOG.md
```

Add an entry for TASK-0004.

The entry should mention:

* Added forbidden terms deterministic review rule.
* Added profile configuration for forbidden terms.
* Added tests for forbidden terms detection.
* Updated architecture documentation.
* Updated project state.

## Git Commit Requirement

After implementation and successful tests, create a dedicated Git commit for TASK-0004.

Expected commit message:

```bash
feat(task-0004): add forbidden terms review rule
```

Before committing, run:

```bash
git status
uv run pytest
```

After committing, run:

```bash
git status
```

The working tree should be clean unless there are unrelated files.

## Acceptance Criteria

This task is complete only when all of the following are true:

1. `TASK-0003` has already been committed.
2. A forbidden terms rule exists.
3. The rule can read forbidden terms from the review profile.
4. The rule returns structured findings when terms are found.
5. The rule returns an empty list when no terms are found.
6. The rule handles empty forbidden terms configuration safely.
7. Tests for the rule exist.
8. `uv run pytest` passes.
9. `docs/ARCHITECTURE.md` is updated.
10. `PROJECT_STATE.md` is updated.
11. `CHANGELOG.md` is updated.
12. A dedicated TASK-0004 Git commit exists.
13. No unrelated changes are included in the TASK-0004 commit.

## Agent Output Required

After finishing the task, report:

1. Whether TASK-0003 had already been committed before starting.
2. Modified files.
3. New files.
4. Added or changed models.
5. Added rule function and behavior.
6. Profile configuration changes.
7. Test command and result.
8. Documentation updates.
9. Git commit hash for TASK-0004.
10. Current `git status`.
11. Any unresolved issues.
12. Recommended next TASK.

## Next Task Preview

After this task, the recommended next task is:

```text
TASK-0005-review-pipeline.md
```

The goal of TASK-0005 should be to add a minimal review pipeline that accepts Markdown text and a review profile, runs available deterministic rules, and returns review findings.

TASK-0005 should still avoid LLM integration.
