# TASK-0002: Define Core Data Models

## Goal

Define the initial core data models for the content review engine.

The goal of this task is to create the first stable structure for structured content review results.

This task only focuses on data models. It must not implement CLI, MCP, Skill, API, database, frontend, PydanticAI integration, Markdown parser, or review rules.

---

## Background

This project follows a Python package-first architecture.

All future interfaces, including CLI, Skill, MCP, API, and frontend, should depend on the same core data models.

The first core models are:

* `ReviewIssue`
* `ReviewResult`
* `ReviewProfile`

These models will become the foundation for:

* deterministic review rules
* AI review output
* CLI JSON output
* MCP tool schema
* API response schema
* frontend display structure

Therefore, this task must keep the model design simple, explicit, and testable.

---

## Architecture Context

The project uses this principle:

```text
Core package first.
Adapters later.
```

The core package should live under:

```text
src/content_review_engine/
```

Current task should create:

```text
src/content_review_engine/core/
  __init__.py
  models.py
```

The implementation source of truth for data models should be:

```text
src/content_review_engine/core/models.py
```

The documentation explanation should be updated in:

```text
docs/DATA_MODELS.md
```

---

## Scope

Implement only the initial core data models.

Create or update:

```text
src/content_review_engine/core/__init__.py
src/content_review_engine/core/models.py
tests/test_models.py
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

---

## Do Not Modify

Do not add or modify the following in this task:

```text
CLI code
MCP server code
Skill files
FastAPI code
Supabase code
Frontend code
PydanticAI integration
Markdown parser
Review rules
Prompt templates
Database models
```

Do not create abstractions that are not required by the current data model task.

---

## Required Dependencies

Use Pydantic for data models.

If Pydantic is not already installed, add it using the project's package manager.

Expected dependency:

```text
pydantic
```

Do not add PydanticAI in this task.

---

## Data Model Requirements

### 1. Severity Type

Create a severity type with the following allowed values:

```text
low
medium
high
critical
```

Suggested implementation:

```python
Severity = Literal["low", "medium", "high", "critical"]
```

---

### 2. ReviewIssue

`ReviewIssue` represents one review issue found in a document.

Required fields:

```text
id
severity
category
title
description
suggestion
```

Optional fields:

```text
original_text
start_line
end_line
```

Field meanings:

| Field           | Meaning                                                         |
| --------------- | --------------------------------------------------------------- |
| `id`            | Stable issue or rule identifier, such as `WECHAT_TITLE_001`     |
| `severity`      | Issue severity: `low`, `medium`, `high`, or `critical`          |
| `category`      | Issue category, such as `wechat_title`, `readability`, `safety` |
| `title`         | Short issue title                                               |
| `description`   | Explanation of the issue                                        |
| `suggestion`    | Suggested fix                                                   |
| `original_text` | Original text related to the issue                              |
| `start_line`    | Start line number in the source document                        |
| `end_line`      | End line number in the source document                          |

Suggested model shape:

```python
class ReviewIssue(BaseModel):
    id: str
    severity: Severity
    category: str
    title: str
    description: str
    suggestion: str
    original_text: str | None = None
    start_line: int | None = None
    end_line: int | None = None
```

---

### 3. ReviewResult

`ReviewResult` represents the full review result of a document.

Required fields:

```text
document_id
profile_name
overall_score
summary
issues
```

Optional fields:

```text
rewritten_markdown
diff
```

Field meanings:

| Field                | Meaning                                              |
| -------------------- | ---------------------------------------------------- |
| `document_id`        | Identifier of the reviewed document                  |
| `profile_name`       | Name of the review profile used                      |
| `overall_score`      | Overall score from 0 to 100                          |
| `summary`            | Short summary of the review result                   |
| `issues`             | List of `ReviewIssue`                                |
| `rewritten_markdown` | Optional rewritten Markdown content                  |
| `diff`               | Optional diff between original and rewritten content |

Requirements:

* `issues` must be `list[ReviewIssue]`.
* `overall_score` must be constrained between 0 and 100.

Suggested model shape:

```python
class ReviewResult(BaseModel):
    document_id: str
    profile_name: str
    overall_score: float = Field(ge=0, le=100)
    summary: str
    issues: list[ReviewIssue]
    rewritten_markdown: str | None = None
    diff: str | None = None
```

---

### 4. ReviewProfile

`ReviewProfile` represents a review configuration for a target platform or writing scenario.

Required fields:

```text
name
target_platform
```

Optional fields with defaults:

```text
tone
max_title_length
max_paragraph_length
```

Field meanings:

| Field                  | Meaning                                               |
| ---------------------- | ----------------------------------------------------- |
| `name`                 | Profile name, such as `wechat`                        |
| `target_platform`      | Target platform, such as `wechat`, `blog`, `academic` |
| `tone`                 | Expected writing tone                                 |
| `max_title_length`     | Maximum suggested title length                        |
| `max_paragraph_length` | Maximum suggested paragraph length                    |

Suggested model shape:

```python
class ReviewProfile(BaseModel):
    name: str
    target_platform: str
    tone: str = "clear and professional"
    max_title_length: int = 32
    max_paragraph_length: int = 220
```

---

## Suggested Implementation

Create:

```text
src/content_review_engine/core/models.py
```

Suggested implementation:

```python
from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["low", "medium", "high", "critical"]


class ReviewIssue(BaseModel):
    id: str
    severity: Severity
    category: str
    title: str
    description: str
    suggestion: str
    original_text: str | None = None
    start_line: int | None = None
    end_line: int | None = None


class ReviewResult(BaseModel):
    document_id: str
    profile_name: str
    overall_score: float = Field(ge=0, le=100)
    summary: str
    issues: list[ReviewIssue]
    rewritten_markdown: str | None = None
    diff: str | None = None


class ReviewProfile(BaseModel):
    name: str
    target_platform: str
    tone: str = "clear and professional"
    max_title_length: int = 32
    max_paragraph_length: int = 220
```

Create:

```text
src/content_review_engine/core/__init__.py
```

Suggested implementation:

```python
from content_review_engine.core.models import (
    ReviewIssue,
    ReviewProfile,
    ReviewResult,
    Severity,
)

__all__ = [
    "ReviewIssue",
    "ReviewProfile",
    "ReviewResult",
    "Severity",
]
```

---

## Test Requirements

Create:

```text
tests/test_models.py
```

Test cases should include:

1. Can create a valid `ReviewIssue`.
2. Can create a valid `ReviewResult` with issues.
3. Can create a valid `ReviewProfile`.
4. Invalid severity should fail.
5. Invalid score below 0 should fail.
6. Invalid score above 100 should fail.

Suggested tests:

```python
import pytest
from pydantic import ValidationError

from content_review_engine.core.models import (
    ReviewIssue,
    ReviewProfile,
    ReviewResult,
)


def test_create_review_issue():
    issue = ReviewIssue(
        id="WECHAT_TITLE_001",
        severity="medium",
        category="wechat_title",
        title="标题过长",
        description="标题长度超过建议上限。",
        suggestion="建议缩短标题。",
        original_text="这是一个非常长的标题",
        start_line=1,
        end_line=1,
    )

    assert issue.id == "WECHAT_TITLE_001"
    assert issue.severity == "medium"
    assert issue.start_line == 1


def test_create_review_result_with_issues():
    issue = ReviewIssue(
        id="WECHAT_TITLE_001",
        severity="medium",
        category="wechat_title",
        title="标题过长",
        description="标题长度超过建议上限。",
        suggestion="建议缩短标题。",
    )

    result = ReviewResult(
        document_id="doc-001",
        profile_name="wechat",
        overall_score=88,
        summary="发现 1 个问题。",
        issues=[issue],
    )

    assert result.document_id == "doc-001"
    assert result.profile_name == "wechat"
    assert result.overall_score == 88
    assert len(result.issues) == 1
    assert result.issues[0].id == "WECHAT_TITLE_001"


def test_create_review_profile():
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
    )

    assert profile.name == "wechat"
    assert profile.target_platform == "wechat"
    assert profile.max_title_length == 32
    assert profile.max_paragraph_length == 220


def test_invalid_severity_should_fail():
    with pytest.raises(ValidationError):
        ReviewIssue(
            id="WECHAT_TITLE_001",
            severity="invalid",
            category="wechat_title",
            title="标题过长",
            description="标题长度超过建议上限。",
            suggestion="建议缩短标题。",
        )


def test_score_below_zero_should_fail():
    with pytest.raises(ValidationError):
        ReviewResult(
            document_id="doc-001",
            profile_name="wechat",
            overall_score=-1,
            summary="Invalid score.",
            issues=[],
        )


def test_score_above_100_should_fail():
    with pytest.raises(ValidationError):
        ReviewResult(
            document_id="doc-001",
            profile_name="wechat",
            overall_score=101,
            summary="Invalid score.",
            issues=[],
        )
```

---

## Documentation Requirements

Update:

```text
docs/DATA_MODELS.md
```

The document should include:

```markdown
# Data Models

## Purpose

This document records the core data models used by the content review engine.

The implementation source of truth is:

`src/content_review_engine/core/models.py`

---

## ReviewIssue

`ReviewIssue` represents one review issue found in a document.

Fields:

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

## ReviewResult

`ReviewResult` represents the full review result of a document.

Fields:

| Field | Required | Description |
|---|---|---|
| `document_id` | Yes | Identifier of the reviewed document |
| `profile_name` | Yes | Review profile name |
| `overall_score` | Yes | Score from 0 to 100 |
| `summary` | Yes | Review summary |
| `issues` | Yes | List of `ReviewIssue` |
| `rewritten_markdown` | No | Optional rewritten Markdown |
| `diff` | No | Optional diff |

---

## ReviewProfile

`ReviewProfile` represents a review configuration.

Fields:

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Profile name |
| `target_platform` | Yes | Target platform |
| `tone` | No | Expected writing tone |
| `max_title_length` | No | Maximum suggested title length |
| `max_paragraph_length` | No | Maximum suggested paragraph length |

---

## Change Rules

1. Any change to `ReviewIssue` must update this document.
2. Any change to `ReviewResult` must update this document.
3. Any change to `ReviewProfile` must update this document.
4. After v0.1.0, breaking changes to these models require an ADR.
```

---

## PROJECT_STATE Update Requirements

After completing this task, update `PROJECT_STATE.md`.

Add or update the handoff section:

```markdown
## Last Handoff

### Completed

- Defined initial core data models.
- Added `ReviewIssue`.
- Added `ReviewResult`.
- Added `ReviewProfile`.
- Added validation tests for model creation.
- Added validation tests for invalid severity and invalid score.
- Updated data model documentation.

### Changed Files

- src/content_review_engine/core/__init__.py
- src/content_review_engine/core/models.py
- tests/test_models.py
- docs/DATA_MODELS.md
- PROJECT_STATE.md
- CHANGELOG.md

### Test Result

`uv run pytest` passed.

### Next Recommended Task

TASK-0003: Add Markdown reader and profile loading.

### Notes

No CLI, MCP, Skill, API, database, frontend, PydanticAI, Markdown parser, or review rule code was added.
```

Also update the current phase if appropriate:

```markdown
## Current Phase

M1: Core data model foundation.
```

---

## CHANGELOG Update Requirements

Update `CHANGELOG.md` under `Unreleased`:

```markdown
## Unreleased

### Added

- Added initial core data models:
  - `ReviewIssue`
  - `ReviewResult`
  - `ReviewProfile`
- Added validation tests for core data models.
- Added data model documentation.
```

---

## Acceptance Criteria

This task is complete only if:

* `src/content_review_engine/core/models.py` exists.
* `ReviewIssue` is implemented as a Pydantic model.
* `ReviewResult` is implemented as a Pydantic model.
* `ReviewProfile` is implemented as a Pydantic model.
* `ReviewResult.issues` uses `list[ReviewIssue]`.
* `overall_score` is constrained between 0 and 100.
* Invalid severity fails validation.
* Invalid score below 0 fails validation.
* Invalid score above 100 fails validation.
* `tests/test_models.py` exists.
* `uv run pytest` passes.
* `docs/DATA_MODELS.md` is updated.
* `PROJECT_STATE.md` is updated with handoff.
* `CHANGELOG.md` is updated.
* No CLI, MCP, Skill, API, database, frontend, PydanticAI, Markdown parser, or review rule code is added.

