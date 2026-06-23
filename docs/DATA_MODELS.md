# Data Models

## Purpose

This document records the core data models used by the content review engine.

The implementation source of truth is `src/content_review_engine/core/models.py`.

---

## ReviewIssue

`ReviewIssue` represents one review issue found in a document.

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

## SourceSpan

`SourceSpan` represents the source location metadata attached to a deterministic finding.

Line and column numbers are 1-based.
Character offsets are 0-based.
`end_offset` is exclusive.

| Field | Required | Description |
|---|---|---|
| `start_line` | Yes | Start line number |
| `start_column` | Yes | Start column number |
| `end_line` | Yes | End line number |
| `end_column` | Yes | End column number |
| `start_offset` | Yes | Start character offset |
| `end_offset` | Yes | End character offset, exclusive |
| `matched_text` | Yes | Exact matched text |
| `context` | No | Short context snippet around the match |

---

## ReviewFinding

`ReviewFinding` represents a deterministic rule match.

| Field | Required | Description |
|---|---|---|
| `rule_id` | Yes | Stable rule identifier |
| `severity` | Yes | `warning` |
| `message` | Yes | Human-readable finding summary |
| `matched_term` | Yes | Term that triggered the finding |
| `matched_text` | No | Original matched text |
| `location` | No | Attached `SourceSpan` with position metadata |

Example:

```python
ReviewFinding(
    rule_id="forbidden_terms",
    severity="warning",
    message="发现风险词：绝对",
    matched_term="绝对",
    matched_text="绝对",
    location=SourceSpan(
        start_line=3,
        start_column=5,
        end_line=3,
        end_column=7,
        start_offset=12,
        end_offset=14,
        matched_text="绝对",
        context="这个方法绝对有效。",
    ),
)
```

---

## ReviewResult

`ReviewResult` represents the full review result of a document.

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

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Profile name |
| `target_platform` | Yes | Target platform |
| `tone` | No | Expected writing tone |
| `max_title_length` | No | Maximum suggested title length |
| `max_paragraph_length` | No | Maximum suggested paragraph length |
| `forbidden_terms` | No | List of forbidden terms to detect |

---

## Change Rules

1. Any change to `ReviewIssue` must update this document.
2. Any change to `ReviewResult` must update this document.
3. Any change to `ReviewProfile` must update this document.
4. After v0.1.0, breaking changes to these models require an ADR.
