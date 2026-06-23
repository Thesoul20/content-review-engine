# Rules

## Purpose

A review rule is a deterministic check that inspects Markdown text and returns a list of `ReviewFinding` objects.

Each rule has a stable `rule_id`. That ID is how the registry stores, retrieves, and enables the rule.

Rules do not create `ReviewResult`, render reports, write files, or print CLI output.

## Relationship With `docs/REVIEW_RULES.md`

This file describes the rule system architecture and runtime behavior:

- how rules are executed
- how the registry works
- how the runner selects enabled rules
- how default-enabled rules behave

`docs/REVIEW_RULES.md` is the rule catalog. It records the individual rules by
name, purpose, implementation path, and test path.

Use `docs/RULES.md` to understand the mechanics of rule execution.
Use `docs/REVIEW_RULES.md` to see which rules exist or are planned.

---

## Rule Registry

The rule registry is the internal lookup layer for deterministic rules.

It provides:

- Registering rules by `rule_id`
- Retrieving a rule by `rule_id`
- Checking whether a rule exists
- Listing registered rule IDs in deterministic order

The registry rejects duplicate rule IDs and raises a clear error for unknown rule IDs.

---

## Rule Runner

The rule runner executes enabled rules for a Markdown document and a `ReviewProfile`.

When a profile does not explicitly select rules, the runner uses the registry's
default-enabled rule order.

The runner returns only `list[ReviewFinding]`.

It does not build `ReviewResult`.

---

## Default Registry

The default registry currently registers three deterministic rules:

- `forbidden_terms`
- `markdown_structure`
- `markdown_links_images`

`forbidden_terms` is default-enabled so existing profiles keep the same behavior.
`markdown_structure` is registered but only runs when a profile explicitly
includes it in `ReviewProfile.enabled_rules`.
`markdown_links_images` is registered but only runs when a profile explicitly
includes it in `ReviewProfile.enabled_rules`.

---

## Current Rule

### forbidden_terms

Purpose:

Detect forbidden terms configured in the review profile.

Status:

Implemented.

Implementation:

`src/content_review_engine/rules/forbidden_terms.py`

Tests:

`tests/test_forbidden_terms_rule.py`

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

## Adding Future Rules

Future deterministic rules should:

1. Define a stable `rule_id`.
2. Implement the internal rule interface.
3. Return `list[ReviewFinding]`.
4. Register in the default registry when they are meant to run by default.
5. Add tests for matching behavior and registry behavior.

---

## Current Limitations

- No external plugin loading.
- No filesystem rule discovery.
- No remote rule loading.
- No parallel execution.
- No rule dependency graph.
- No LLM rules.
