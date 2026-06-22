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

---

## Change Rules

1. Any change to `ReviewIssue` must update this document.
2. Any change to `ReviewResult` must update this document.
3. Any change to `ReviewProfile` must update this document.
4. After v0.1.0, breaking changes to these models require an ADR.
