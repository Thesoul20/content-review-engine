# Data Models

## Purpose

This document records the core data models used by the content review engine.

The implementation source of truth is `src/content_review_engine/core/models.py`.

Canonical JSON serialization helpers live in `src/content_review_engine/core/serialization.py`.

Current built-in rule metadata is centralized in
`src/content_review_engine/core/rule_registry.py`.
That registry is internal metadata only. It is not a field in the canonical
review or batch JSON output schemas unless a future task explicitly exposes it.
The deterministic execution registry in
`src/content_review_engine/rules/registry.py` also does not change the JSON
schema; it only decides which deterministic rule implementations run.

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

`rule_id` is the stable identifier for the rule that produced the finding.
For current built-in rules, descriptive metadata for that identifier is
centralized in the core rule registry.
That registry metadata does not add fields to `ReviewFinding`, `ReviewResult`,
or `BatchReviewResult`.
If a future LLM semantic review layer is added, it should map its findings into
this finding model or a compatible extension introduced by a later task.
TASK-0029 does not add an LLM-specific finding schema.

| Field | Required | Description |
|---|---|---|
| `rule_id` | Yes | Stable rule identifier |
| `severity` | Yes | `info`, `warning`, `error`, or `critical` |
| `message` | Yes | Human-readable finding summary |
| `matched_term` | Yes | Term that triggered the finding |
| `suggestion` | No | Optional remediation or safer wording guidance |
| `matched_text` | No | Original matched text |
| `location` | No | Attached `SourceSpan` with position metadata |

Example:

```python
ReviewFinding(
    rule_id="absolute_claims",
    severity="error",
    message="发现可能存在绝对化表述：绝对",
    matched_term="绝对",
    suggestion="建议改为更审慎的表述，或补充证据支持该结论。",
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

## RuleDefinition

`RuleDefinition` stores descriptive metadata for one current built-in rule in
the internal rule registry.

It is not part of the canonical review-result JSON schema.
It does not replace `ReviewFinding.rule_id`, and it does not appear in the
current JSON output unless a future task explicitly exposes registry metadata.

| Field | Required | Description |
|---|---|---|
| `rule_id` | Yes | Stable built-in rule identifier |
| `name` | Yes | Human-readable rule name |
| `description` | Yes | Short description of the rule's purpose |
| `category` | Yes | Small internal category label such as `terms` or `markdown` |
| `source` | Yes | Whether the rule is `built-in` or `profile-driven` |
| `supports_suppression` | Yes | Whether inline suppression comments are supported |

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

## ProfileValidationError

`ProfileValidationError` stores one human-readable validation failure message.

| Field | Required | Description |
|---|---|---|
| `message` | Yes | Readable validation error message |

---

## ProfileValidationRuleSummary

`ProfileValidationRuleSummary` records one rule entry in a valid profile
validation result.

| Field | Required | Description |
|---|---|---|
| `id` | Yes | Stable rule identifier |
| `enabled` | Yes | Whether the rule is enabled |
| `severity` | No | Effective finding severity when the rule exposes one |

---

## ProfileValidationProfileSummary

`ProfileValidationProfileSummary` stores the summary returned for a valid
profile validation run.

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Profile name |
| `target_platform` | Yes | Target platform |
| `enabled_rule_count` | Yes | Number of enabled rules in the summary |
| `disabled_rule_count` | Yes | Number of disabled rules in the summary |
| `rules` | Yes | Ordered list of `ProfileValidationRuleSummary` items |

---

## ProfileValidationResult

`ProfileValidationResult` is the canonical structured output for
`content-review profile validate`.

The stable schema version is `profile-validation-result.v1`.

| Field | Required | Description |
|---|---|---|
| `schema_version` | Yes | Result schema version |
| `valid` | Yes | Whether the profile is valid |
| `path` | Yes | Path that was validated |
| `profile` | No | Optional `ProfileValidationProfileSummary` for valid profiles |
| `errors` | Yes | List of `ProfileValidationError` items |

Example:

```json
{
  "schema_version": "profile-validation-result.v1",
  "valid": true,
  "path": "profiles/wechat.yaml",
  "profile": {
    "name": "wechat",
    "target_platform": "wechat",
    "enabled_rule_count": 1,
    "disabled_rule_count": 0,
    "rules": [
      {
        "id": "forbidden_terms",
        "enabled": true,
        "severity": "warning"
      }
    ]
  },
  "errors": []
}
```

---

## ProfileTemplateSummary

`ProfileTemplateSummary` records one built-in profile template exposed by
`content-review profile list`.

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Stable built-in template name |
| `description` | Yes | Short human-readable template description |

---

## ProfileTemplateListResult

`ProfileTemplateListResult` is the canonical structured output for
`content-review profile list --format json`.

The stable schema version is `profile-template-list.v1`.

| Field | Required | Description |
|---|---|---|
| `schema_version` | Yes | Result schema version |
| `templates` | Yes | Ordered list of `ProfileTemplateSummary` items |

Example:

```json
{
  "schema_version": "profile-template-list.v1",
  "templates": [
    {
      "name": "general-basic",
      "description": "General-purpose starter profile for public-facing content."
    },
    {
      "name": "wechat-basic",
      "description": "Basic WeChat article profile with moderate checks."
    }
  ]
}
```

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

## BatchReviewSummary

`BatchReviewSummary` summarizes a batch review run across multiple files.

| Field | Required | Description |
|---|---|---|
| `file_count` | Yes | Number of discovered Markdown files |
| `reviewed_count` | Yes | Number of files successfully reviewed |
| `finding_count` | Yes | Total number of findings across all files |
| `files_with_findings` | Yes | Number of files with at least one finding |
| `severity_counts` | Yes | Aggregated severity counts across all file summaries |

Example:

```json
{
  "file_count": 3,
  "reviewed_count": 3,
  "finding_count": 2,
  "files_with_findings": 2,
  "severity_counts": {
    "info": 0,
    "warning": 2,
    "error": 0,
    "critical": 0
  }
}
```

---

## BatchReviewResult

`BatchReviewResult` is the canonical structured output for a batch review run.

The stable schema version is `batch-review-result.v1`.

| Field | Required | Description |
|---|---|---|
| `schema_version` | Yes | Result schema version |
| `summary` | Yes | `BatchReviewSummary` computed from the file results |
| `results` | Yes | List of canonical `ReviewResult` objects |

Example:

```json
{
  "schema_version": "batch-review-result.v1",
  "summary": {
    "file_count": 3,
    "reviewed_count": 3,
    "finding_count": 2,
    "files_with_findings": 2,
    "severity_counts": {
      "info": 0,
      "warning": 2,
      "error": 0,
      "critical": 0
    }
  },
  "results": [
    {
      "schema_version": "review-result.v1",
      "summary": {
        "finding_count": 0,
        "severity_counts": {
          "info": 0,
          "warning": 0,
          "error": 0,
          "critical": 0
        }
      },
      "findings": [],
      "document": {
        "path": "tests/fixtures/batch/articles/clean.md"
      },
      "profile": {
        "name": "batch-default",
        "path": "tests/fixtures/batch/profile.yml"
      }
    }
  ]
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
| `forbidden_terms_allow_terms` | No | Normalized literal allowlist for `forbidden_terms`; populated from `rules[].allow_terms` when using rule-style YAML configuration |
| `absolute_claims_terms` | No | List of literal absolute-claim terms to detect |
| `absolute_claims_allow_terms` | No | Normalized literal allowlist for `absolute_claims`; populated from `rules[].allow_terms` when using rule-style YAML configuration |
| `absolute_claims_severity` | No | Severity used for `absolute_claims` findings; defaults to `warning` |
| `enabled_rules` | No | Optional ordered list of rule IDs to run |

---

## Change Rules

1. Any change to `ReviewIssue` must update this document.
2. Any change to `ReviewFinding` must update this document.
3. Any change to `ReviewSummary` must update this document.
4. Any change to `ReviewResult` must update this document.
5. Any change to `BatchReviewSummary` must update this document.
6. Any change to `BatchReviewResult` must update this document.
7. Any change to `ProfileValidationResult` must update this document.
8. Any change to `ReviewProfile` must update this document.
9. After v0.1.0, breaking changes to these models require an ADR.
