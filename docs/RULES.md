# Rules

## Purpose

A review rule is a deterministic check that inspects Markdown text and returns a list of `ReviewFinding` objects.

Each rule has a stable `rule_id`. That ID is how the registry stores, retrieves, and enables the rule.

Rules do not create `ReviewResult`, render reports, write files, or print CLI output.

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

When a profile does not explicitly select rules, the runner uses the default registry order.

The runner returns only `list[ReviewFinding]`.

It does not build `ReviewResult`.

---

## Default Registry

The default registry currently includes one deterministic rule:

- `forbidden_terms`

This is the existing profile-driven forbidden-term check, now executed through the registry and runner.

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

