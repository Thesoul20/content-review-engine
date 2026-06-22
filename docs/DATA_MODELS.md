# Data Models

## Purpose

This document records the core data models used by the content review engine.

The implementation source of truth is the Python code in the core package.

This document explains the purpose and contract of those models.

---

## Planned Core Models

### ReviewIssue

Represents one review issue found in the document.

Expected fields:

```text
id
severity
category
title
description
suggestion
original_text
start_line
end_line
```

---

### ReviewResult

Represents the full review result of a document.

Expected fields:

```text
document_id
profile_name
overall_score
summary
issues
rewritten_markdown
diff
```

---

### ReviewProfile

Represents a review configuration for a specific platform or writing scenario.

Expected fields:

```text
name
target_platform
tone
rules
platform-specific thresholds
```

---

## Rules

1. Any change to ReviewIssue must update this document.
2. Any change to ReviewResult must update this document.
3. Any change to ReviewProfile must update this document.
4. Frozen data model changes require an ADR after v0.1.0.
