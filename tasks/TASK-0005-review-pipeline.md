# TASK-0005: Add Minimal Review Pipeline

## Status

Planned

## Type

Feature / Review Pipeline

## Priority

High

## Depends On

* TASK-0001: Project Skeleton
* TASK-0002: Core Data Models
* TASK-0002.5: Package Import Config
* TASK-0003: Markdown Reader and Profile Loading
* TASK-0004: Forbidden Terms Rule

## Precondition

Before starting this task, TASK-0004 must already have a dedicated Git commit.

Expected TASK-0004 commit message:

```bash
feat(task-0004): add forbidden terms review rule
```

Do not start implementing TASK-0005 if TASK-0004 changes are still uncommitted.

Before implementation, confirm:

```bash
git status
git log --oneline -5
```

If the working tree contains unrelated changes or TASK-0004 has not been committed, stop and report the issue.

## Background

The project currently has:

* A Markdown reader.
* A YAML profile loader.
* A sample WeChat review profile.
* The first deterministic review rule: `forbidden_terms`.
* Unit tests for Markdown reading, profile loading, and forbidden terms detection.

However, the project still does not have a central review pipeline.

At this stage, users or future CLI/API layers would need to manually call individual rules. This is not scalable once more rules are added.

TASK-0005 introduces the first minimal in-memory review pipeline, which connects loaded Markdown text and a loaded `ReviewProfile` to the available deterministic rules.

## Goal

Add a minimal review pipeline that accepts Markdown text and a loaded `ReviewProfile`, runs the available deterministic review rules, and returns structured review results.

The initial pipeline should run only the existing rule:

```text
forbidden_terms
```

The target flow is:

```text
Markdown text
    +
ReviewProfile
    ↓
review_document()
    ↓
Deterministic rules
    ↓
ReviewResult / findings
```

## Scope

This task includes:

1. Add a review pipeline module.
2. Add a `review_document()` function.
3. Run the existing `forbidden_terms` rule inside the pipeline.
4. Collect findings returned by deterministic rules.
5. Return structured review results using existing core models.
6. Add unit tests for the review pipeline.
7. Update architecture documentation.
8. Update project state.
9. Update changelog.
10. Run the full test suite.
11. Create a dedicated Git commit for TASK-0005.

## Non-Goals

This task must not implement:

* CLI entrypoint
* File path based review command
* LLM-based review
* Prompt templates
* PydanticAI integration
* MCP server
* FastAPI server
* Supabase integration
* Frontend
* Database persistence
* Rule registry
* Rule scheduler
* Dynamic plugin loading
* Markdown auto-rewrite
* Markdown AST parsing
* Line and column location tracking
* Streaming output
* JSON report export
* HTML report export

These should be handled by future TASK files.

## Expected Files

The implementation may create or modify:

```text
src/content_review_engine/review/__init__.py
src/content_review_engine/review/pipeline.py
tests/test_review_pipeline.py
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

The implementation may also minimally modify:

```text
src/content_review_engine/core/models.py
```

Only modify `core/models.py` if the existing result model cannot represent pipeline output.

Do not modify parser, config, CLI, API, MCP, frontend, or database-related code in this task.

## Model Review Requirement

Before implementing the pipeline, inspect:

```text
src/content_review_engine/core/models.py
```

Check whether the project already has models such as:

* `ReviewResult`
* `ReviewIssue`
* `ReviewFinding`
* `ReviewProfile`

Implementation rules:

1. Prefer reusing existing models.
2. Do not introduce duplicate result models.
3. If `ReviewResult` already exists, use it as the pipeline return type.
4. If only finding-level models exist, return `list[ReviewFinding]` for this task.
5. If a small model extension is required, keep it minimal.
6. Document any model change in `docs/DATA_MODELS.md` only if the existing project convention requires it.

## Review Module Design

Create a new review package if it does not already exist:

```text
src/content_review_engine/review/__init__.py
src/content_review_engine/review/pipeline.py
```

The review module should be responsible for coordinating review execution.

It should not read files directly.

It should not load YAML profiles directly.

It should not print to stdout.

It should only accept already-loaded inputs.

## Pipeline Function

Add a function similar to:

```python
def review_document(
    markdown_text: str,
    profile: ReviewProfile,
) -> ReviewResult:
    ...
```

If the current model layer does not support `ReviewResult`, use:

```python
def review_document(
    markdown_text: str,
    profile: ReviewProfile,
) -> list[ReviewFinding]:
    ...
```

The exact return type should follow the existing data model design.

## Pipeline Behavior

The pipeline must:

1. Accept Markdown text as `str`.
2. Accept a loaded `ReviewProfile`.
3. Run the `forbidden_terms` deterministic rule.
4. Collect findings returned by the rule.
5. Return a structured review result.
6. Return an empty result when no rule reports findings.
7. Avoid reading Markdown files directly.
8. Avoid loading profile files directly.
9. Avoid printing to stdout.
10. Avoid CLI behavior.
11. Avoid introducing dynamic rule discovery.
12. Avoid introducing plugin systems.

This task should keep the pipeline purely in-memory.

## Rule Execution

The pipeline should call the existing forbidden terms rule directly.

Expected behavior:

```text
review_document()
    ↓
check_forbidden_terms()
    ↓
collect findings
    ↓
return result
```

Do not create a generic rule registry in this task.

If multiple rules are added in the future, that should be handled in a later TASK.

## Tests

Add:

```text
tests/test_review_pipeline.py
```

The tests must cover at least the following cases.

### 1. Pipeline Returns Finding

Given Markdown text containing a configured forbidden term, `review_document()` returns a result containing at least one finding.

### 2. Pipeline Returns Empty Result

Given Markdown text with no configured forbidden terms, `review_document()` returns an empty result.

### 3. Pipeline Uses Profile Configuration

Given two profiles with different forbidden terms, the pipeline behavior changes according to the profile configuration.

### 4. Pipeline Does Not Read Files

The test should call `review_document()` using already-loaded Markdown text and an already-created or already-loaded `ReviewProfile`.

The pipeline must not require a Markdown file path or a YAML profile path.

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

Add the minimal review pipeline layer to the architecture.

Suggested architecture description:

```text
Markdown Reader
    ↓
Profile Loader
    ↓
Review Pipeline
    ↓
Deterministic Rules
    ↓
Review Result
```

Mention that the current pipeline only runs deterministic rules and currently includes only:

```text
forbidden_terms
```

Also clarify that the following features are not implemented yet:

* CLI
* API
* MCP server
* LLM review
* Persistence
* Frontend

## Project State Update

Update:

```text
PROJECT_STATE.md
```

The update should mention:

* TASK-0005 is completed.
* A minimal in-memory review pipeline has been added.
* The pipeline currently runs the `forbidden_terms` rule.
* The project still does not have CLI, API, MCP, LLM review, persistence, or frontend.

## Changelog Update

Update:

```text
CHANGELOG.md
```

Add an entry for TASK-0005.

The entry should mention:

* Added minimal review pipeline.
* Added `review_document()`.
* Connected the `forbidden_terms` rule to the pipeline.
* Added review pipeline tests.
* Updated architecture documentation.
* Updated project state.

## Git Commit Requirement

After implementation and successful tests, create a dedicated Git commit for TASK-0005.

Expected commit message:

```bash
feat(task-0005): add minimal review pipeline
```

Before committing, run:

```bash
git status
uv run pytest
```

After committing, run:

```bash
git status
git log --oneline -3
```

The working tree should be clean unless there are unrelated files.

## Acceptance Criteria

This task is complete only when all of the following are true:

1. TASK-0004 has already been committed.
2. A review pipeline module exists.
3. `review_document()` exists.
4. The pipeline accepts Markdown text and `ReviewProfile`.
5. The pipeline runs the `forbidden_terms` rule.
6. The pipeline returns structured review results.
7. The pipeline returns an empty result when no findings exist.
8. Pipeline tests exist.
9. `uv run pytest` passes.
10. `docs/ARCHITECTURE.md` is updated.
11. `PROJECT_STATE.md` is updated.
12. `CHANGELOG.md` is updated.
13. A dedicated TASK-0005 Git commit exists.
14. No unrelated changes are included in the TASK-0005 commit.

## Agent Output Required

After finishing the task, report:

1. Whether TASK-0004 had already been committed before starting.
2. Modified files.
3. New files.
4. Added or changed models.
5. Added pipeline function and behavior.
6. How the pipeline calls `forbidden_terms`.
7. Test command and result.
8. Documentation updates.
9. Git commit hash for TASK-0005.
10. Current `git status`.
11. Any unresolved issues.
12. Recommended next TASK.

## Next Task Preview

After this task, the recommended next task is:

```text
TASK-0006-cli-review-command.md
```

The goal of TASK-0006 should be to add a minimal CLI command that can review a Markdown file using a YAML profile.

TASK-0006 should still avoid LLM integration.
