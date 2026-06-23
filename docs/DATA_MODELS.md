# Data Models

## Purpose

This document records the core data models used by the content review engine.

The implementation source of truth is `src/content_review_engine/core/models.py`.

Canonical JSON serialization helpers live in `src/content_review_engine/core/serialization.py`.

---

## ReviewIssue

`ReviewIssue` represents a higher-level issue object kept in the core model layer for future issue-based workflows.

It is not part of the canonical review result payload stabilized by TASK-0011.

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

`ReviewFinding` represents one deterministic rule match.

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

## ReviewSummary

`ReviewSummary` summarizes a `ReviewResult`.

The summary is computed from the findings list and should not be assembled separately in the CLI or report layers.

| Field | Required | Description |
|---|---|---|
| `finding_count` | Yes | Total number of findings |
| `severity_counts` | Yes | Count of findings by severity |

`severity_counts` currently uses the canonical buckets:

- `info`
- `warning`
- `error`
- `critical`

Example:

```json
{
  "finding_count": 2,
  "severity_counts": {
    "info": 0,
    "warning": 2,
    "error": 0,
    "critical": 0
  }
}
```

---

## ReviewDocumentMetadata

`ReviewDocumentMetadata` stores optional document context for a `ReviewResult`.

| Field | Required | Description |
|---|---|---|
| `path` | Yes | Path to the reviewed document |

---

## ReviewProfileMetadata

`ReviewProfileMetadata` stores optional profile context for a `ReviewResult`.

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Profile name |
| `path` | No | Path to the loaded profile |

---

## ReviewResult

`ReviewResult` is the canonical structured output for a reviewed document.

The stable schema version is `review-result.v1`.

| Field | Required | Description |
|---|---|---|
| `schema_version` | Yes | Result schema version |
| `summary` | Yes | `ReviewSummary` computed from findings |
| `findings` | Yes | List of `ReviewFinding` |
| `document` | No | Optional `ReviewDocumentMetadata` |
| `profile` | No | Optional `ReviewProfileMetadata` |

Example:

```json
{
  "schema_version": "review-result.v1",
  "summary": {
    "finding_count": 1,
    "severity_counts": {
      "info": 0,
      "warning": 1,
      "error": 0,
      "critical": 0
    }
  },
  "findings": [
    {
      "rule_id": "forbidden_terms",
      "severity": "warning",
      "message": "发现风险词：绝对安全",
      "matched_term": "绝对安全",
      "matched_text": "绝对安全",
      "location": {
        "start_line": 1,
        "start_column": 8,
        "end_line": 1,
        "end_column": 12,
        "start_offset": 7,
        "end_offset": 11,
        "matched_text": "绝对安全",
        "context": "# 测试文章 绝对安全"
      }
    }
  ],
  "document": {
    "path": "examples/article.md"
  },
  "profile": {
    "name": "example",
    "path": "examples/profile.yml"
  }
}
```

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
| `enabled_rules` | No | Optional ordered list of rule IDs to run |

---

## Change Rules

1. Any change to `ReviewIssue` must update this document.
2. Any change to `ReviewFinding` must update this document.
3. Any change to `ReviewSummary` must update this document.
4. Any change to `ReviewResult` must update this document.
5. Any change to `ReviewProfile` must update this document.
6. After v0.1.0, breaking changes to these models require an ADR.
