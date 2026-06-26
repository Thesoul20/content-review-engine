# TASK-0031: Add Real-World Profile Templates

## Status

Planned

## Goal

Add real-world review profile templates that demonstrate how to use the content review engine in practical publishing scenarios.

TASK-0030 added deterministic profile-configured `regex_rules`. TASK-0031 should use the existing built-in rules and the new `regex_rules` capability to provide practical, conservative, and well-documented profile templates.

This task should make the CLI prototype easier to demonstrate and easier for users to try.

## Background

The project now supports:

* built-in deterministic rules
* profile loading and validation
* `forbidden_terms`
* `absolute_claims`
* `markdown_structure`
* `markdown_links_images`
* inline suppression
* quality gates
* Markdown / JSON / text output
* batch review
* `regex_rules`

However, users still need good starting profile templates.

Without real-world templates, users must invent their own profile from scratch. With templates, they can run the tool immediately against common content types.

Example use cases:

* general publishing review
* WeChat / public account article review
* marketing copy review
* technical blog review
* medical or health content caution review

This task should add templates that are useful but not overclaiming compliance.

## Scope

This task may modify:

* profile template files
* profile template discovery code if needed
* profile init/list behavior if templates are already supported
* documentation for profiles and quickstart usage
* README if appropriate
* tests for template listing, validation, and initialization
* `PROJECT_STATE.md`
* `CHANGELOG.md`

Likely files or directories to inspect:

```text id="fgh6ad"
src/content_review_engine/
src/content_review_engine/config/
src/content_review_engine/profiles/
tests/
docs/PROFILES.md
docs/QUICKSTART.md
docs/CLI.md
README.md
PROJECT_STATE.md
CHANGELOG.md
```

Exact paths should be confirmed from the current repository.

## Non-goals

This task must not:

* add LLM review
* add PydanticAI
* add API endpoints
* add MCP support
* add GUI support
* change rule matching behavior
* change `regex_rules` behavior
* change suppression syntax
* change quality gate semantics
* change Markdown report structure
* change JSON output schema
* introduce legal, medical, advertising, regulatory, or platform compliance guarantees
* claim that templates guarantee platform approval or regulatory compliance
* add too many aggressive or risky rules

## Required Work

### 1. Inspect Existing Profile Template System

Before making changes, inspect the current profile template system.

Confirm:

* where profile templates currently live
* how `content-review profile list` discovers templates
* how `content-review profile init` creates a profile from a template
* how profile validation works
* which tests already cover profile templates
* current naming conventions for templates

Do not redesign the template system unless necessary.

### 2. Add Real-World Profile Templates

Add a small set of practical templates.

Recommended templates:

```text id="pou15w"
general_publishing
wechat_article
marketing_copy
technical_blog
health_content
```

If the existing template naming convention uses hyphens or file names such as `general.yml`, follow the repository convention.

Each template should be conservative and readable.

### 3. Template: `general_publishing`

Purpose:

A general-purpose publishing review profile for common Markdown content.

Should include examples of:

* forbidden or risky terms
* absolute claim patterns
* markdown structure checks if configurable
* link / image checks if configurable
* one or two `regex_rules`

Suggested focus:

```text id="9dl95e"
overconfident wording
unclear guarantees
placeholder text
unfinished notes
```

Example regex ideas:

```yaml id="tuhzpg"
regex_rules:
  - id: draft_placeholder
    pattern: "TODO|TBD|待补充|这里补充|占位"
    severity: warning
    message: "Remove placeholder text before publishing."
    suggestion: "Replace the placeholder with final content or remove it."
    case_sensitive: false
```

### 4. Template: `wechat_article`

Purpose:

A WeChat / public account article review profile.

Should focus on:

* exaggerated claims
* absolute claims
* risky promotional wording
* placeholder text
* broken or suspicious Markdown formatting
* missing image alt text if already supported

Example regex ideas:

```yaml id="pykpna"
regex_rules:
  - id: exaggerated_claims
    pattern: "唯一|第一|最强|绝对|100%|永久|彻底"
    severity: warning
    message: "Avoid absolute or exaggerated claims in public-facing articles."
    suggestion: "Use more cautious, evidence-based wording."
    case_sensitive: false
```

```yaml id="lex0ye"
regex_rules:
  - id: engagement_bait
    pattern: "不看后悔|震惊|速看|赶紧收藏|全网都在"
    severity: info
    message: "This phrase may sound like engagement bait."
    suggestion: "Consider using a clearer and more professional title or transition."
    case_sensitive: false
```

Do not claim this guarantees WeChat platform compliance.

### 5. Template: `marketing_copy`

Purpose:

A marketing copy review profile.

Should focus on:

* exaggerated product claims
* guarantee-like wording
* pressure tactics
* unverifiable superlatives
* discount or scarcity language that may need review

Example regex ideas:

```yaml id="vxof2z"
regex_rules:
  - id: guaranteed_outcome
    pattern: "保证|包过|稳赚|必然|一定有效|立刻见效"
    severity: error
    message: "This wording may imply a guaranteed outcome."
    suggestion: "Use qualified wording and provide evidence where appropriate."
    case_sensitive: false
```

```yaml id="xfptyq"
regex_rules:
  - id: unverifiable_superlative
    pattern: "行业第一|全网第一|顶级|最先进|最权威"
    severity: warning
    message: "This wording may be difficult to verify."
    suggestion: "Use specific, supportable claims instead."
    case_sensitive: false
```

Do not claim legal or advertising-law compliance.

### 6. Template: `technical_blog`

Purpose:

A technical blog review profile.

Should focus on:

* unfinished draft markers
* broken Markdown links or images through existing rules
* overly absolute technical claims
* TODO/FIXME markers
* misleading security or performance guarantees

Example regex ideas:

```yaml id="n74rdw"
regex_rules:
  - id: unresolved_draft_marker
    pattern: "TODO|FIXME|XXX|待验证|待补充"
    severity: warning
    message: "Unresolved draft marker found."
    suggestion: "Resolve the marker before publishing."
    case_sensitive: false
```

```yaml id="rqjouz"
regex_rules:
  - id: absolute_technical_claim
    pattern: "永远不会|完全避免|零风险|绝不会|百分百兼容"
    severity: warning
    message: "Avoid absolute technical claims unless they are fully verified."
    suggestion: "Use qualified wording and describe assumptions or limitations."
    case_sensitive: false
```

### 7. Template: `health_content`

Purpose:

A cautious health / medical content review profile.

Should focus on:

* cure guarantees
* treatment promises
* replacing professional care
* absolute health claims
* missing cautionary language

Example regex ideas:

```yaml id="tnol1f"
regex_rules:
  - id: medical_guarantee_claim
    pattern: "治愈|根治|彻底解决|保证有效|立刻见效|无需就医|替代治疗"
    severity: error
    message: "This wording may imply a medical guarantee or replacement for professional care."
    suggestion: "Use cautious language and avoid implying guaranteed treatment outcomes."
    case_sensitive: false
```

```yaml id="j24dau"
regex_rules:
  - id: self_diagnosis_risk
    pattern: "自己判断|不用检查|无需医生|自行诊断"
    severity: warning
    message: "This wording may encourage self-diagnosis or avoidance of professional advice."
    suggestion: "Encourage readers to consult qualified professionals where appropriate."
    case_sensitive: false
```

Important:

The template must clearly state that it does not provide medical compliance, diagnosis, treatment advice, or regulatory approval.

### 8. Validate All Templates

Every new template must pass profile validation.

Add tests to verify:

* each new template is discoverable by `profile list`
* each new template can be initialized by `profile init` if the current CLI supports this
* each generated profile validates successfully
* each template includes at least one `regex_rules` example
* each template avoids compliance guarantee language

Suggested test file:

```text id="e2n82o"
tests/test_profile_templates.py
```

or extend existing profile template tests if they already exist.

### 9. Update Profile Documentation

Update:

```text id="rgfwce"
docs/PROFILES.md
```

Document:

* available templates
* intended use case for each template
* how to list templates
* how to initialize a profile from a template
* how to customize `regex_rules`
* limitations and non-goals

Example commands:

```bash id="9sc6rt"
uv run content-review profile list
uv run content-review profile init --template wechat_article --output profiles/wechat.yml
uv run content-review profile validate profiles/wechat.yml
```

Use the actual CLI syntax from the repository.

### 10. Update Quickstart If Appropriate

Update:

```text id="k6yu47"
docs/QUICKSTART.md
```

Add a short section or note showing how to start from a real-world template.

Keep it brief. Do not duplicate all profile documentation.

### 11. Update CLI Documentation

Update:

```text id="0b8x0l"
docs/CLI.md
```

If needed, document the new template names under profile commands.

Do not change CLI behavior unless needed to expose templates through existing mechanisms.

### 12. Update README If Appropriate

Update:

```text id="9kfwfn"
README.md
```

Add a short mention that real-world profile templates are available.

Keep README concise.

### 13. Avoid Compliance Overclaims

Every template and doc section must include cautious wording.

Acceptable:

```text id="2vse0r"
This template helps flag common risky wording patterns for review.
```

Not acceptable:

```text id="a0aer5"
This template ensures compliance.
```

Acceptable:

```text id="q8od3q"
This is not legal, medical, advertising, regulatory, or platform compliance advice.
```

### 14. Update Project State

Update:

```text id="uid9la"
PROJECT_STATE.md
```

Mention:

* TASK-0031 completed
* real-world profile templates added
* templates demonstrate `regex_rules`
* templates are conservative examples
* no LLM review was added
* no runtime rule behavior changed beyond making templates available

### 15. Update Changelog

Update:

```text id="zq5jw3"
CHANGELOG.md
```

Add a TASK-0031 entry describing:

* added real-world profile templates
* documented template use cases
* added template validation tests
* updated profile / quickstart / CLI docs
* no compliance guarantees

## Acceptance Criteria

TASK-0031 is complete when:

* real-world profile templates exist
* templates include practical `regex_rules`
* templates validate successfully
* templates are discoverable through existing profile template mechanisms
* template documentation is updated
* Quickstart or README points users to templates
* tests cover template discovery and validation
* docs avoid compliance guarantees
* `PROJECT_STATE.md` is updated
* `CHANGELOG.md` is updated
* all tests pass
* no LLM review is introduced
* no unrelated runtime behavior changes are introduced

## Validation Commands

Run:

```bash id="se9f8h"
uv run pytest
```

Manual checks:

```bash id="z3c8gn"
uv run content-review profile list
uv run content-review profile init --template wechat_article --output /tmp/wechat_profile.yml
uv run content-review profile validate /tmp/wechat_profile.yml
```

Use the actual CLI syntax if different.
