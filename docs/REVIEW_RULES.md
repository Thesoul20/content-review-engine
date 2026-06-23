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

### forbidden_terms

Purpose:

Detect forbidden terms configured in the review profile.

Status:

Implemented.

### markdown_structure

Purpose:

Detect basic Markdown document structure issues such as missing H1 headings,
multiple H1 headings, heading level jumps, empty headings, and extremely long
paragraphs.

Status:

Implemented.

Implementation:

`src/content_review_engine/rules/markdown_structure.py`

Tests:

`tests/test_markdown_structure_rule.py`

### markdown_links_images

Purpose:

Detect empty Markdown link text, empty link targets, placeholder link targets,
empty image alt text, empty image targets, and placeholder image targets.
Fenced code blocks are ignored.
Inline code spans are not specially excluded in this version.

Status:

Implemented.

Implementation:

`src/content_review_engine/rules/markdown_links_images.py`

Tests:

`tests/test_markdown_links_images_rule.py`

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
