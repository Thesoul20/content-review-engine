
# TASK-0013: Add Markdown Structure Rule

## 1. Task Title

`TASK-0013: Add Markdown Structure Rule`

## 2. Task Status

Draft

## 3. Depends On

This task depends on:

* `TASK-0011: Stabilize ReviewResult Model and JSON Schema`
* `TASK-0012: Add Rule Registry and Rule Runner`

Do not start this task unless TASK0012 has been completed and the existing test suite passes.

## 4. Goal

Add the first additional deterministic review rule after the rule registry was introduced.

This task adds a minimal `markdown_structure` rule that checks basic Markdown document structure.

The rule should detect a small set of structural issues:

1. Missing top-level H1 title.
2. Multiple H1 titles.
3. Heading level jumps, such as jumping from `##` to `####`.
4. Empty headings, such as `##`.
5. Extremely long paragraphs.

This task should prove that the rule registry and rule runner can support new rule types without changing the review pipeline, CLI output contract, or report renderer.

## 5. Background

Before TASK0013, the project already supports:

* Reading Markdown files.
* Loading `ReviewProfile`.
* Running deterministic review rules through `RuleRunner`.
* Registering rules through `RuleRegistry`.
* Running the existing `forbidden_terms` rule.
* Returning canonical `ReviewResult`.
* Serializing review results to JSON.
* Rendering Markdown reports.
* Running the packaged `content-review` CLI command.

However, the project still only has one actual review rule.

TASK0013 adds the first new rule category: Markdown structure review.

This rule is intentionally simple and deterministic. It should not parse the full Markdown AST, and it should not attempt to fix Markdown content.

## 6. Non-Goals

This task must not implement any of the following:

* LLM-based review.
* Automatic rewriting.
* Diff tracking.
* Markdown auto-fix.
* Full Markdown AST parser.
* HTML rendering.
* Markdown lint compatibility.
* Batch review.
* Watch mode.
* MCP server.
* REST API.
* GUI.
* Database persistence.
* New report format.
* New CLI command.
* Full markdownlint rule coverage.
* Code block aware heading parsing beyond simple safe handling if already easy.
* Complex style rules.
* Platform-specific rules.

This task is only about adding one minimal deterministic `markdown_structure` rule.

## 7. Required Reading Before Coding

Before making any code changes, read:

```text
AGENTS.md
PROJECT_STATE.md
ROADMAP.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
docs/REPORTS.md
docs/TESTING.md
docs/RULES.md
docs/schemas/review-result.schema.json
pyproject.toml
tasks/TASK-0011-stabilize-review-result-and-json-schema.md
tasks/TASK-0012-rule-registry-and-runner.md
tasks/TASK-0013-markdown-structure-rule.md
```

If older historical task files are missing, do not recreate them in this task.

Instead:

1. Inspect the current implementation.
2. Use existing docs, tests, fixtures, and project state as the source of truth.
3. Mention missing historical task files in the final summary only if relevant.

## 8. Allowed Scope

This task may modify or add files related to the new Markdown structure rule, fixtures, tests, and documentation.

Likely allowed files:

```text
src/content_review_engine/rules/markdown_structure.py
src/content_review_engine/rules/registry.py
src/content_review_engine/rules/__init__.py
src/content_review_engine/core/models.py
tests/test_markdown_structure_rule.py
tests/test_rule_registry.py
tests/test_rule_runner.py
tests/test_review_pipeline.py
tests/test_cli.py
tests/fixtures/markdown/markdown_structure_issues.md
tests/fixtures/profiles/markdown_structure.yml
examples/markdown-structure-article.md
examples/markdown-structure-profile.yml
docs/RULES.md
docs/CLI.md
docs/TESTING.md
PROJECT_STATE.md
CHANGELOG.md
```

Optional, only if necessary:

```text
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
```

Do not modify unrelated modules.

## 9. Forbidden Scope

Do not change the canonical `ReviewResult` contract.

Do not change `ReviewFinding` semantics.

Do not change `SourceSpan` semantics.

Do not change `forbidden_terms` behavior.

Do not add LLM logic.

Do not add third-party Markdown parsing dependencies.

Do not introduce a full markdownlint clone.

Do not rewrite the CLI.

Do not rewrite the report renderer.

Do not change existing example outputs unless the profile explicitly enables the new rule.

Do not enable the new rule by default if that changes existing behavior unexpectedly.

## 10. Rule ID

The new rule ID should be:

```text
markdown_structure
```

Every finding produced by this rule should use this `rule_id`.

If the project already uses a namespaced convention, adapt to the existing convention, but keep the ID stable and documented.

## 11. Rule Enablement

The new rule should be registered in the rule registry.

However, it should not unexpectedly change existing review behavior.

Preferred behavior:

1. The default behavior for existing profiles remains unchanged.
2. Existing examples that only expect forbidden-term findings should continue to produce the same findings.
3. The `markdown_structure` rule should run when explicitly enabled through `ReviewProfile.enabled_rules`.

Example profile:

```yaml
name: markdown-structure
enabled_rules:
  - markdown_structure
```

If the current rule runner runs all registered rules when `enabled_rules` is absent, update it minimally so that the default enabled rule set remains backward compatible.

Do not silently change existing default review output.

## 12. Rule Behavior

The `markdown_structure` rule should inspect raw Markdown text line by line.

It should produce `ReviewFinding` objects with location metadata when possible.

### 12.1 Missing H1

If the document contains no H1 heading, emit one finding.

Example:

```markdown
## Introduction

Content here.
```

Expected finding:

```text
rule_id: markdown_structure
severity: warning
message: Missing top-level H1 heading.
location: optional
```

For a missing H1 finding, if there is no exact source span, location may be `None`.

### 12.2 Multiple H1 Headings

If the document contains more than one H1 heading, emit a finding for each extra H1 after the first.

Example:

```markdown
# Title

# Another Title
```

Expected finding for the second H1.

The finding should include line and column metadata for the extra H1 line.

### 12.3 Heading Level Jumps

If heading levels jump by more than one level, emit a finding.

Example:

```markdown
# Title

### Skipped H2
```

This jumps from H1 to H3, so it should produce a finding.

Expected finding should include:

```text
message: Heading level jumps from H1 to H3.
location: source span for the problematic heading line
```

Allowed transitions:

```text
H1 -> H2
H2 -> H3
H3 -> H4
same level
going back to a lower level
```

Problematic transitions:

```text
H1 -> H3
H2 -> H4
H1 -> H4
```

### 12.4 Empty Headings

If a heading marker has no text after it, emit a finding.

Examples:

```markdown
#
##
###
```

Also treat headings with only spaces as empty:

```markdown
##    
```

Expected finding should include line and column metadata.

### 12.5 Extremely Long Paragraphs

If a paragraph exceeds a configurable character threshold, emit a finding.

Default threshold:

```text
300 characters
```

A paragraph is a continuous block of non-empty lines that is not a heading and not a fenced code block.

For this task, keep the paragraph logic simple and deterministic.

Expected finding should include the start line and column of the paragraph.

## 13. Code Block Handling

At minimum, the rule should avoid treating headings inside fenced code blocks as real headings.

Example:

````markdown
```markdown
# This is code, not a heading
````

````

Requirements:

1. Track fenced code blocks using lines starting with triple backticks.
2. Do not check headings inside fenced code blocks.
3. Do not count headings inside fenced code blocks as H1/H2/H3.
4. Do not include code block text in long paragraph checks.

Do not attempt full CommonMark parsing.

## 14. Source Location Requirements

For findings tied to a specific line, include `SourceSpan` or the existing location model.

Rules:

1. Line numbers should be 1-based.
2. Column numbers should be 1-based.
3. Character offsets should be 0-based if practical.
4. `matched_text` should contain the relevant heading line or paragraph start text.
5. `context` should include a short snippet around the problematic line.

For missing H1, location may be `None`.

Use existing location helpers where possible.

Do not duplicate location calculation logic if reusable helpers already exist.

## 15. Severity Requirements

Use `warning` severity for all initial `markdown_structure` findings.

Do not introduce new severity levels.

Future tasks can make severity configurable.

## 16. Message Requirements

Finding messages should be stable and testable.

Suggested messages:

```text
Missing top-level H1 heading.
Multiple top-level H1 headings found.
Heading level jumps from H1 to H3.
Empty heading found.
Paragraph is too long.
````

Messages may be Chinese if the existing project has standardized Chinese rule messages.

If the project already uses Chinese messages for user-facing findings, use Chinese consistently.

Example Chinese messages:

```text
缺少一级标题 H1。
发现多个一级标题 H1。
标题层级从 H1 跳到了 H3。
发现空标题。
段落过长。
```

Choose one language style and keep it consistent with the current project.

## 17. Profile Configuration

If the current `ReviewProfile` supports rule-specific configuration, add optional support for long paragraph threshold.

If not, keep the threshold constant in the rule for this task.

Do not design a large nested configuration system in TASK0013.

Acceptable minimal profile shape only if already supported or easy:

```yaml
name: markdown-structure
enabled_rules:
  - markdown_structure
markdown_structure:
  max_paragraph_chars: 300
```

If this would require significant schema changes, skip configurable threshold and document the fixed default.

## 18. Registry Integration

Update the default rule registry so it knows about `markdown_structure`.

Important:

* The rule can be registered without being default-enabled.
* Existing profiles without `enabled_rules` should preserve previous behavior.
* Explicit profiles with `enabled_rules: [markdown_structure]` should run only this rule.
* Explicit profiles with `enabled_rules: [forbidden_terms, markdown_structure]` should run both rules in deterministic order.

## 19. Runner Integration

The existing `run_rules()` function should work without major changes.

It should be able to execute the new rule through the existing rule interface.

Do not add special-case logic for Markdown structure in the review pipeline.

The pipeline should remain:

```text
review_document()
→ run_rules()
→ ReviewResult.from_findings()
```

## 20. CLI Behavior

No new CLI flags are required.

The user should be able to run the rule by using a profile that enables it:

```bash
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format text
```

Also verify:

```bash
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format json
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format markdown
```

Existing CLI commands with `examples/article.md` and `examples/profile.yml` should continue to work.

## 21. Fixture Requirements

Add Markdown fixtures for the new rule.

Suggested file:

```text
tests/fixtures/markdown/markdown_structure_issues.md
```

This file should include:

1. Missing or problematic heading structure.
2. An empty heading.
3. A heading level jump.
4. A long paragraph.
5. A fenced code block containing a heading-like line that should be ignored.

Add a profile fixture:

```text
tests/fixtures/profiles/markdown_structure.yml
```

Example:

```yaml
name: markdown-structure
enabled_rules:
  - markdown_structure
```

Add example files only if useful:

```text
examples/markdown-structure-article.md
examples/markdown-structure-profile.yml
```

Do not add a large article corpus.

## 22. Tests Required

Add or update tests for the new rule.

### 22.1 Missing H1 Test

Given Markdown without an H1.

When running the `markdown_structure` rule.

Then it returns a finding for missing H1.

### 22.2 Multiple H1 Test

Given Markdown with two H1 headings.

Then it returns a finding for the extra H1.

### 22.3 Heading Jump Test

Given Markdown that jumps from H1 to H3.

Then it returns a heading jump finding.

### 22.4 Empty Heading Test

Given Markdown with `##` and no heading text.

Then it returns an empty heading finding.

### 22.5 Long Paragraph Test

Given a paragraph longer than the threshold.

Then it returns a long paragraph finding.

### 22.6 Code Block Ignore Test

Given a fenced code block containing `# Fake Heading`.

Then that line should not count as an H1.

### 22.7 Rule Registry Test

The default registry should include the `markdown_structure` rule.

### 22.8 Rule Runner Test

Given a profile with:

```yaml
enabled_rules:
  - markdown_structure
```

The runner should execute the Markdown structure rule.

Given a profile with:

```yaml
enabled_rules:
  - forbidden_terms
```

The runner should not execute the Markdown structure rule.

### 22.9 Review Pipeline Test

Given Markdown structure issues and a profile enabling `markdown_structure`.

`review_document()` should return a canonical `ReviewResult` with structure findings.

### 22.10 CLI Test

Using fixture files or temp files, verify:

```bash
uv run content-review review <markdown> --profile <markdown_structure_profile> --format json
```

The JSON output should include:

```text
schema_version
summary
findings
rule_id: markdown_structure
```

### 22.11 Existing Behavior Regression Test

Existing forbidden-term tests and example CLI tests should continue to pass.

Existing default profile behavior should not unexpectedly add `markdown_structure` findings.

## 23. Documentation Required

Update or add:

```text
docs/RULES.md
docs/CLI.md
docs/TESTING.md
PROJECT_STATE.md
CHANGELOG.md
```

Optional:

```text
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
```

### 23.1 `docs/RULES.md`

Add a section for `markdown_structure`.

Document:

1. Rule ID.
2. What it checks.
3. Severity.
4. How to enable it through `ReviewProfile.enabled_rules`.
5. Current limitations.
6. Code block handling.
7. Long paragraph threshold.

### 23.2 `docs/CLI.md`

Add example usage:

```bash
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format text
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format json
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format markdown
```

### 23.3 `docs/TESTING.md`

Mention the new fixture files and how Markdown structure rule tests are organized.

### 23.4 `PROJECT_STATE.md`

Update project state to mention:

* TASK0013 completed.
* Added deterministic `markdown_structure` rule.
* Rule checks H1 presence, multiple H1s, heading jumps, empty headings, and long paragraphs.
* Rule is integrated through `RuleRegistry` and `RuleRunner`.
* Existing default forbidden-term behavior remains backward compatible.
* No LLM, rewriting, diff, batch, API, MCP, GUI, or database support was added.

### 23.5 `CHANGELOG.md`

Suggested entry:

```markdown
## TASK-0013

### Added

- Added deterministic `markdown_structure` review rule.
- Added checks for missing H1, multiple H1 headings, heading level jumps, empty headings, and long paragraphs.
- Added code-block-aware handling for heading checks inside fenced code blocks.
- Registered `markdown_structure` in the rule registry.
- Added Markdown structure fixtures and tests.
- Added CLI examples for running Markdown structure review through an explicit profile.

### Changed

- Extended rules documentation with the new `markdown_structure` rule.
- Updated selected CLI and testing documentation.

### Not Added

- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No batch review.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.
```

## 24. Validation Commands

After implementation, run:

```bash
uv sync
uv run pytest
```

Run manual CLI smoke tests for existing behavior:

```bash
uv run content-review --help
uv run content-review review examples/article.md --profile examples/profile.yml --format text
uv run content-review review examples/article.md --profile examples/profile.yml --format json
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
```

Run manual CLI smoke tests for the new rule:

```bash
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format text
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format json
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format markdown
```

If output file behavior should be checked:

```bash
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format markdown --output /tmp/markdown-structure-review-report.md
```

Do not commit generated files under `/tmp`.

## 25. Completion Criteria

This task is complete only when:

* `markdown_structure` rule exists.
* The rule implements missing H1 detection.
* The rule implements multiple H1 detection.
* The rule implements heading jump detection.
* The rule implements empty heading detection.
* The rule implements long paragraph detection.
* The rule ignores heading-like lines inside fenced code blocks.
* The rule returns `ReviewFinding` objects.
* Findings include location metadata when possible.
* The rule is registered in `RuleRegistry`.
* The rule can be enabled through `ReviewProfile.enabled_rules`.
* Existing forbidden-terms behavior is preserved.
* Existing default profile behavior is preserved.
* CLI works with a profile that enables `markdown_structure`.
* Tests are added or updated.
* `uv run pytest` passes.
* Manual CLI smoke tests pass.
* `docs/RULES.md` is updated.
* `docs/CLI.md` is updated.
* `docs/TESTING.md` is updated.
* `PROJECT_STATE.md` is updated.
* `CHANGELOG.md` is updated.
* No out-of-scope features are implemented.

## 26. Known Limitations To Preserve

Do not try to solve these in TASK0013:

* No full Markdown AST parsing.
* No markdownlint compatibility.
* No automatic fixes.
* No custom rule severity configuration.
* No custom paragraph threshold unless already easy and minimal.
* No nested rule configuration system.
* No heading slug generation.
* No table structure analysis.
* No link validation.
* No image alt validation.
* No batch review.
* No LLM review.
* No API/MCP integration.

## 27. Final Agent Response Requirements

When the Agent finishes this task, it must report:

1. Files changed.
2. Markdown structure rule added.
3. Checks implemented.
4. How code block handling works.
5. How findings include location metadata.
6. How the rule is registered.
7. How the rule is enabled through profile configuration.
8. Whether existing default behavior changed.
9. Tests added or updated.
10. Result of `uv sync`.
11. Result of `uv run pytest`.
12. Manual CLI smoke test results.
13. Whether `docs/RULES.md` was updated.
14. Whether `docs/CLI.md` was updated.
15. Whether `docs/TESTING.md` was updated.
16. Whether `PROJECT_STATE.md` was updated.
17. Whether `CHANGELOG.md` was updated.
18. Known limitations.

The final response must be concise and must not claim unsupported functionality.
