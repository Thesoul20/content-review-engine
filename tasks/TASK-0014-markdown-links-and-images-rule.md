
# TASK-0014: Add Markdown Links and Images Rule

## 1. Task Title

`TASK-0014: Add Markdown Links and Images Rule`

## 2. Task Status

Draft

## 3. Depends On

This task depends on:

* `TASK-0011: Stabilize ReviewResult Model and JSON Schema`
* `TASK-0012: Add Rule Registry and Rule Runner`
* `TASK-0013: Add Markdown Structure Rule`

Do not start this task unless TASK0013 has been completed and the existing test suite passes.

## 4. Goal

Add a deterministic `markdown_links_images` rule that checks basic Markdown link and image hygiene.

This rule should detect common Markdown issues such as:

1. Empty link text.
2. Empty link target.
3. Empty image alt text.
4. Empty image target.
5. Placeholder link targets such as `#`, `TODO`, or `待补充`.
6. Link-like or image-like syntax inside fenced code blocks should be ignored.

This task adds the second non-forbidden-terms deterministic rule and further validates the rule registry / rule runner design.

It must not perform network requests, remote URL validation, or file existence validation.

## 5. Background

Before TASK0014, the project already supports:

* Reading Markdown files.
* Loading `ReviewProfile`.
* Running deterministic rules through `RuleRunner`.
* Registering rules through `RuleRegistry`.
* Running `forbidden_terms`.
* Running `markdown_structure` when explicitly enabled.
* Returning canonical `ReviewResult`.
* Serializing review results to JSON.
* Rendering Markdown reports.
* Running the packaged `content-review` CLI command.

TASK0014 extends the deterministic rule set with link and image checks.

This is useful because Markdown publishing workflows often fail due to broken or incomplete link/image syntax before any LLM-based content review is needed.

## 6. Non-Goals

This task must not implement any of the following:

* Network link checking.
* HTTP status validation.
* Remote URL fetching.
* Local file existence checking.
* Image dimension checking.
* Image download.
* Image alt text quality scoring.
* Full Markdown AST parsing.
* Markdown auto-fix.
* Automatic rewriting.
* Diff tracking.
* LLM-based review.
* Batch review.
* Watch mode.
* MCP server.
* REST API.
* GUI.
* Database persistence.
* HTML/PDF report generation.
* New CLI commands.
* New report formats.
* External plugin loading.
* Dynamic rule discovery.

This task is only about adding a minimal deterministic `markdown_links_images` rule.

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
tasks/TASK-0014-markdown-links-and-images-rule.md
```

If older historical task files are missing, do not recreate them in this task.

Instead:

1. Inspect the current implementation.
2. Use existing docs, tests, fixtures, and project state as the source of truth.
3. Mention missing historical task files in the final summary only if relevant.

## 8. Allowed Scope

This task may modify or add files related to the new Markdown links/images rule, fixtures, tests, examples, and documentation.

Likely allowed files:

```text
src/content_review_engine/rules/markdown_links_images.py
src/content_review_engine/rules/registry.py
src/content_review_engine/rules/__init__.py
tests/test_markdown_links_images_rule.py
tests/test_rule_registry.py
tests/test_rule_runner.py
tests/test_review_pipeline.py
tests/test_cli.py
tests/fixtures/markdown/markdown_links_images_issues.md
tests/fixtures/profiles/markdown_links_images.yml
examples/markdown-links-images-article.md
examples/markdown-links-images-profile.yml
docs/RULES.md
docs/CLI.md
docs/TESTING.md
PROJECT_STATE.md
CHANGELOG.md
```

Optional, only if necessary:

```text
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
```

Do not modify unrelated modules.

## 9. Forbidden Scope

Do not change the canonical `ReviewResult` contract.

Do not change `ReviewFinding` semantics.

Do not change `SourceSpan` semantics.

Do not change `forbidden_terms` behavior.

Do not change `markdown_structure` behavior.

Do not add new third-party dependencies.

Do not introduce a full Markdown parser.

Do not rewrite the CLI.

Do not rewrite the report renderer.

Do not perform network calls.

Do not perform filesystem checks for image/link targets.

Do not enable the new rule by default if it changes existing behavior unexpectedly.

## 10. Rule ID

The new rule ID should be:

```text
markdown_links_images
```

Every finding produced by this rule should use this `rule_id`.

If the project already uses a namespaced convention, adapt to the existing convention, but keep the ID stable and documented.

## 11. Rule Enablement

The new rule should be registered in the rule registry.

However, it should not unexpectedly change existing review behavior.

Preferred behavior:

1. The rule is registered.
2. The rule is not default-enabled.
3. Existing profiles without `enabled_rules` continue to run the same default rule set as before.
4. The rule runs only when explicitly enabled through `ReviewProfile.enabled_rules`.

Example profile:

```yaml
name: markdown-links-images
enabled_rules:
  - markdown_links_images
```

A combined profile should also work:

```yaml
name: markdown-quality
enabled_rules:
  - forbidden_terms
  - markdown_structure
  - markdown_links_images
```

Do not silently change existing example output.

## 12. Rule Behavior

The `markdown_links_images` rule should inspect raw Markdown text line by line.

It should produce `ReviewFinding` objects with location metadata when possible.

### 12.1 Empty Link Text

Detect inline links with empty link text.

Example:

```markdown
[](https://example.com)
```

Expected finding:

```text
rule_id: markdown_links_images
severity: warning
message: Empty link text.
location: span for the link syntax
```

Chinese message is acceptable if the project uses Chinese user-facing findings:

```text
链接文本为空。
```

### 12.2 Empty Link Target

Detect inline links with empty link target.

Examples:

```markdown
[文档]()
[文档](   )
```

Expected finding:

```text
rule_id: markdown_links_images
severity: warning
message: Empty link target.
location: span for the link syntax
```

Chinese message:

```text
链接目标为空。
```

### 12.3 Placeholder Link Target

Detect placeholder link targets.

Examples:

```markdown
[文档](#)
[文档](TODO)
[文档](todo)
[文档](待补充)
[文档](TBD)
```

Expected finding:

```text
rule_id: markdown_links_images
severity: warning
message: Placeholder link target.
location: span for the link syntax
```

Chinese message:

```text
链接目标仍是占位符。
```

The placeholder list should be small and deterministic.

Suggested placeholder targets:

```text
#
TODO
todo
TBD
tbd
待补充
待填写
```

Do not add a large or configurable placeholder system in this task.

### 12.4 Empty Image Alt Text

Detect Markdown images with empty alt text.

Example:

```markdown
![](image.png)
```

Expected finding:

```text
rule_id: markdown_links_images
severity: warning
message: Empty image alt text.
location: span for the image syntax
```

Chinese message:

```text
图片 alt 文本为空。
```

### 12.5 Empty Image Target

Detect Markdown images with empty image target.

Examples:

```markdown
![示例图]()
![示例图](   )
```

Expected finding:

```text
rule_id: markdown_links_images
severity: warning
message: Empty image target.
location: span for the image syntax
```

Chinese message:

```text
图片目标为空。
```

### 12.6 Placeholder Image Target

Detect image targets that are placeholders.

Examples:

```markdown
![示例图](#)
![示例图](TODO)
![示例图](待补充)
```

Expected finding:

```text
rule_id: markdown_links_images
severity: warning
message: Placeholder image target.
location: span for the image syntax
```

Chinese message:

```text
图片目标仍是占位符。
```

## 13. Code Block Handling

The rule should ignore link-like and image-like syntax inside fenced code blocks.

Example:

````markdown
```markdown
[](https://example.com)
![](image.png)
````

````

Requirements:

1. Track fenced code blocks using lines starting with triple backticks or triple tildes.
2. Do not check links inside fenced code blocks.
3. Do not check images inside fenced code blocks.
4. Do not attempt full CommonMark parsing.

## 14. Inline Code Handling

If easy and deterministic, ignore link-like syntax inside inline code spans.

Example:

```markdown
Use `[](https://example.com)` as an example.
````

If inline code handling would complicate implementation, skip it and document the limitation.

Do not implement a complex inline Markdown parser.

## 15. Reference-Style Links

Reference-style links may be ignored in this task unless the current codebase already supports them easily.

Examples that may be ignored:

```markdown
[文档][docs]

[docs]: https://example.com
```

Do not implement full reference-style link validation in TASK0014.

Document this limitation.

## 16. Source Location Requirements

For each finding tied to a concrete syntax span, include `SourceSpan` or the existing location model.

Rules:

1. Line numbers should be 1-based.
2. Column numbers should be 1-based.
3. Character offsets should be 0-based if practical.
4. `matched_text` should contain the full matched link or image syntax.
5. `context` should include a short snippet around the matched syntax.

Use existing location helpers where possible.

Do not duplicate location calculation logic if reusable helpers already exist.

## 17. Severity Requirements

Use `warning` severity for all initial `markdown_links_images` findings.

Do not introduce new severity levels.

Future tasks can make severity configurable.

## 18. Message Requirements

Finding messages should be stable and testable.

Choose the language style consistent with the current project.

If the project currently uses Chinese user-facing messages, use:

```text
链接文本为空。
链接目标为空。
链接目标仍是占位符。
图片 alt 文本为空。
图片目标为空。
图片目标仍是占位符。
```

If the project currently uses English user-facing messages, use:

```text
Empty link text.
Empty link target.
Placeholder link target.
Empty image alt text.
Empty image target.
Placeholder image target.
```

Do not mix languages within the rule messages.

## 19. Registry Integration

Update the default rule registry so it knows about `markdown_links_images`.

Important:

* The rule can be registered without being default-enabled.
* Existing profiles without `enabled_rules` should preserve previous behavior.
* Explicit profiles with `enabled_rules: [markdown_links_images]` should run only this rule.
* Explicit profiles with `enabled_rules: [forbidden_terms, markdown_structure, markdown_links_images]` should run all three in deterministic order.

## 20. Runner Integration

The existing `run_rules()` function should work without major changes.

It should be able to execute the new rule through the existing rule interface.

Do not add special-case logic for Markdown links/images in the review pipeline.

The pipeline should remain:

```text
review_document()
→ run_rules()
→ ReviewResult.from_findings()
```

## 21. CLI Behavior

No new CLI flags are required.

The user should be able to run the rule by using a profile that enables it:

```bash
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format text
```

Also verify:

```bash
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format json
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format markdown
```

Existing CLI commands with previous examples should continue to work.

## 22. Fixture Requirements

Add Markdown fixtures for the new rule.

Suggested file:

```text
tests/fixtures/markdown/markdown_links_images_issues.md
```

This file should include:

1. Empty link text.
2. Empty link target.
3. Placeholder link target.
4. Empty image alt text.
5. Empty image target.
6. Placeholder image target.
7. A fenced code block containing link/image-like syntax that should be ignored.

Add a profile fixture:

```text
tests/fixtures/profiles/markdown_links_images.yml
```

Example:

```yaml
name: markdown-links-images
enabled_rules:
  - markdown_links_images
```

Add example files:

```text
examples/markdown-links-images-article.md
examples/markdown-links-images-profile.yml
```

Do not add a large article corpus.

## 23. Tests Required

Add or update tests for the new rule.

### 23.1 Empty Link Text Test

Given Markdown containing:

```markdown
[](https://example.com)
```

The rule should return a finding for empty link text.

### 23.2 Empty Link Target Test

Given Markdown containing:

```markdown
[文档]()
```

The rule should return a finding for empty link target.

### 23.3 Placeholder Link Target Test

Given Markdown containing:

```markdown
[文档](#)
```

The rule should return a finding for placeholder link target.

### 23.4 Empty Image Alt Text Test

Given Markdown containing:

```markdown
![](image.png)
```

The rule should return a finding for empty image alt text.

### 23.5 Empty Image Target Test

Given Markdown containing:

```markdown
![示例图]()
```

The rule should return a finding for empty image target.

### 23.6 Placeholder Image Target Test

Given Markdown containing:

```markdown
![示例图](TODO)
```

The rule should return a finding for placeholder image target.

### 23.7 Code Block Ignore Test

Given a fenced code block containing problematic link/image syntax.

Then the rule should not produce findings for syntax inside the code block.

### 23.8 Valid Links and Images Test

Given Markdown with normal links and images.

Then the rule should not produce findings.

Example:

```markdown
[OpenAI](https://example.com)
![架构图](images/architecture.png)
```

### 23.9 Rule Registry Test

The default registry should include the `markdown_links_images` rule.

### 23.10 Rule Runner Test

Given a profile with:

```yaml
enabled_rules:
  - markdown_links_images
```

The runner should execute the Markdown links/images rule.

Given a profile with:

```yaml
enabled_rules:
  - forbidden_terms
```

The runner should not execute the Markdown links/images rule.

### 23.11 Review Pipeline Test

Given Markdown link/image issues and a profile enabling `markdown_links_images`.

`review_document()` should return a canonical `ReviewResult` with link/image findings.

### 23.12 CLI JSON Test

Using fixture files or temp files, verify:

```bash
uv run content-review review <markdown> --profile <markdown_links_images_profile> --format json
```

The JSON output should include:

```text
schema_version
summary
findings
rule_id: markdown_links_images
```

### 23.13 Existing Behavior Regression Test

Existing forbidden-term and markdown-structure tests should continue to pass.

Existing default profile behavior should not unexpectedly add `markdown_links_images` findings.

## 24. Documentation Required

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

### 24.1 `docs/RULES.md`

Add a section for `markdown_links_images`.

Document:

1. Rule ID.
2. What it checks.
3. Severity.
4. How to enable it through `ReviewProfile.enabled_rules`.
5. Current limitations.
6. Code block handling.
7. That it does not perform network or filesystem validation.

### 24.2 `docs/CLI.md`

Add example usage:

```bash
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format text
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format json
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format markdown
```

### 24.3 `docs/TESTING.md`

Mention the new fixture files and how Markdown links/images rule tests are organized.

### 24.4 `PROJECT_STATE.md`

Update project state to mention:

* TASK0014 completed.
* Added deterministic `markdown_links_images` rule.
* Rule checks empty link text, empty link target, placeholder link target, empty image alt text, empty image target, and placeholder image target.
* Rule is integrated through `RuleRegistry` and `RuleRunner`.
* Existing default behavior remains backward compatible.
* No network validation, filesystem validation, LLM, rewriting, diff, batch, API, MCP, GUI, or database support was added.

### 24.5 `CHANGELOG.md`

Suggested entry:

```markdown
## TASK-0014

### Added

- Added deterministic `markdown_links_images` review rule.
- Added checks for empty link text, empty link target, placeholder link target, empty image alt text, empty image target, and placeholder image target.
- Added code-block-aware handling for link/image checks inside fenced code blocks.
- Registered `markdown_links_images` in the rule registry.
- Added Markdown links/images fixtures and tests.
- Added CLI examples for running Markdown links/images review through an explicit profile.

### Changed

- Extended rules documentation with the new `markdown_links_images` rule.
- Updated selected CLI and testing documentation.

### Not Added

- No network link checking.
- No local file existence checking.
- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No batch review.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.
```

## 25. Validation Commands

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

Run manual CLI smoke tests for the Markdown structure rule:

```bash
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format text
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format json
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format markdown
```

Run manual CLI smoke tests for the new Markdown links/images rule:

```bash
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format text
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format json
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format markdown
```

If output file behavior should be checked:

```bash
uv run content-review review examples/markdown-links-images-article.md --profile examples/markdown-links-images-profile.yml --format markdown --output /tmp/markdown-links-images-review-report.md
```

Do not commit generated files under `/tmp`.

## 26. Completion Criteria

This task is complete only when:

* `markdown_links_images` rule exists.
* The rule detects empty link text.
* The rule detects empty link target.
* The rule detects placeholder link target.
* The rule detects empty image alt text.
* The rule detects empty image target.
* The rule detects placeholder image target.
* The rule ignores link/image-like syntax inside fenced code blocks.
* The rule returns `ReviewFinding` objects.
* Findings include location metadata when possible.
* The rule is registered in `RuleRegistry`.
* The rule can be enabled through `ReviewProfile.enabled_rules`.
* Existing `forbidden_terms` behavior is preserved.
* Existing `markdown_structure` behavior is preserved.
* Existing default profile behavior is preserved.
* CLI works with a profile that enables `markdown_links_images`.
* Tests are added or updated.
* `uv run pytest` passes.
* Manual CLI smoke tests pass.
* `docs/RULES.md` is updated.
* `docs/CLI.md` is updated.
* `docs/TESTING.md` is updated.
* `PROJECT_STATE.md` is updated.
* `CHANGELOG.md` is updated.
* No out-of-scope features are implemented.

## 27. Known Limitations To Preserve

Do not try to solve these in TASK0014:

* No network link checking.
* No HTTP status validation.
* No local image/file existence validation.
* No full Markdown AST parsing.
* No reference-style link validation.
* No inline code handling unless it is trivial and deterministic.
* No image alt quality scoring.
* No automatic fixes.
* No custom rule severity configuration.
* No nested rule configuration system.
* No batch review.
* No LLM review.
* No API/MCP integration.

## 28. Final Agent Response Requirements

When the Agent finishes this task, it must report:

1. Files changed.
2. Markdown links/images rule added.
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
