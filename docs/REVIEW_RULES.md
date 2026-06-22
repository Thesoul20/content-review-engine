# Review Rules

## Purpose

This document records all deterministic review rules.

Each rule must have a stable `rule_id`.

Each rule must be connected to:

- Code implementation
- Documentation
- Test cases
- Review output

---

## Rule ID Format

Recommended format:

```text
PLATFORM_CATEGORY_NUMBER
```

Examples:

```text
WECHAT_TITLE_001
WECHAT_PARAGRAPH_001
SAFETY_RISK_001
READABILITY_001
STYLE_TONE_001
```

---

## Current Rules

No rules implemented yet.

---

## Planned Rules

### WECHAT_TITLE_001

Purpose:

Check whether a WeChat article title is too long.

Status:

Planned.

---

### WECHAT_PARAGRAPH_001

Purpose:

Check whether a paragraph is too long for mobile reading.

Status:

Planned.

---

## Rule Documentation Template

```markdown
## RULE_ID: Rule Name

### Description

Explain what this rule checks.

### Trigger

Explain when this rule is triggered.

### Severity

low / medium / high / critical

### Example

Bad:

Example bad text.

Good:

Example improved text.

### Implementation

Path to implementation file.

### Tests

Path to test file.
```
