
# TASK-0009: Add Markdown Fixtures and Example Review Files

## 1. Task Title

`TASK-0009: Add Markdown Fixtures and Example Review Files`

## 2. Task Status

Draft

## 3. Depends On

This task depends on:

* `TASK-0005: Add Minimal Review Pipeline`
* `TASK-0006: Add Minimal CLI Review Command`
* `TASK-0007: Add Finding Location and Context Snippets`
* `TASK-0008: Add Markdown Review Report Export`

Do not start this task unless TASK008 has been completed and the existing test suite passes.

## 4. Goal

Add a small, well-organized set of Markdown fixtures and example files for testing and manual CLI usage.

After this task, the project should have:

1. A `tests/fixtures/` directory for automated test assets.
2. An `examples/` directory for manual CLI examples.
3. Reusable Markdown fixture files for common review scenarios.
4. Reusable ReviewProfile fixture files.
5. Optional expected Markdown report fixture files.
6. Updated tests that use fixtures where appropriate.
7. Documentation explaining the difference between `tests/fixtures/` and `examples/`.

This task improves test readability and makes the CLI easier to manually verify.

## 5. Background

Before TASK009, tests mostly use:

* Inline Markdown strings.
* Temporary files created with `tmp_path`.
* Manually constructed `ReviewFinding` / `SourceSpan` objects.

This is good for small unit tests.

However, after TASK008, the project now supports a full path from Markdown input to review output and Markdown report export:

```text
Markdown file
→ ReviewProfile
→ review pipeline
→ findings with location
→ CLI output
→ Markdown report
```

At this point, the project should have a small set of committed fixture files to support integration-style tests and manual smoke tests.

## 6. Non-Goals

This task must not implement any of the following:

* New review rules.
* New forbidden terms behavior.
* LLM-based review.
* Automatic rewriting.
* Diff tracking.
* Markdown auto-fix.
* Batch review.
* Watch mode.
* MCP server.
* REST API.
* GUI.
* Database persistence.
* HTML/PDF report generation.
* Full snapshot testing framework.
* Large real-world article corpus.

This task is only about adding test fixtures, examples, and small test/documentation updates.

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
tasks/TASK-0007-finding-location-and-context-snippets.md
tasks/TASK-0008-markdown-review-report-export.md
tasks/TASK-0009-markdown-fixtures-and-examples.md
```

If historical task files such as TASK0003-TASK0006 are missing, do not recreate them in this task.

Instead:

1. Inspect the current implementation.
2. Use existing docs and tests as the source of truth.
3. Mention the missing historical task files in the final task summary.

## 8. Allowed Scope

This task may add or modify only files related to fixtures, examples, tests, and documentation.

Allowed new directories:

```text
tests/fixtures/
tests/fixtures/markdown/
tests/fixtures/profiles/
tests/fixtures/expected_reports/
examples/
```

Allowed file changes:

```text
tests/fixtures/markdown/*.md
tests/fixtures/profiles/*.yml
tests/fixtures/expected_reports/*.md
examples/*.md
examples/*.yml
examples/*.md.example
tests/test_cli.py
tests/test_markdown_report.py
tests/test_review_pipeline.py
docs/CLI.md
docs/REPORTS.md
docs/TESTING.md
PROJECT_STATE.md
CHANGELOG.md
```

If the project already has a fixture or example directory, follow the existing structure instead of creating a duplicate structure.

## 9. Forbidden Scope

Do not change core review behavior.

Do not rewrite the CLI.

Do not change the public shape of review results.

Do not change the Markdown report format unless strictly necessary to make tests stable.

Do not add new dependencies.

Do not add large or copyrighted real articles.

Do not add sensitive, private, or production content as fixtures.

Do not add generated temporary output files unless they are intentionally used as expected test fixtures.

## 10. Directory Structure

Add the following structure:

```text
tests/
  fixtures/
    markdown/
      clean_article.md
      forbidden_terms_article.md
      multiline_forbidden_terms.md
      markdown_with_code_block.md
    profiles/
      default.yml
      strict.yml
    expected_reports/
      forbidden_terms_report.md

examples/
  article.md
  profile.yml
```

If some files are not needed after inspecting existing tests, keep the fixture set smaller.

Do not add unnecessary fixture files.

## 11. Fixture File Requirements

### 11.1 `clean_article.md`

A short Markdown article with no forbidden terms.

It should include:

* One H1 title.
* One or two paragraphs.
* At least one H2 section.

Example topic can be generic, such as content review workflow.

### 11.2 `forbidden_terms_article.md`

A short Markdown article containing at least one configured forbidden term.

It should include terms already supported by the current test profile.

Example:

```markdown
# 测试文章

这个方法绝对有效。
```

The exact forbidden terms must match the profile fixture.

### 11.3 `multiline_forbidden_terms.md`

A Markdown file with forbidden terms on multiple lines.

It should help verify:

* Line calculation.
* Column calculation.
* Multiple findings.
* Context snippets.

### 11.4 `markdown_with_code_block.md`

A Markdown file that includes a fenced code block.

For this task, do not change rule behavior around code blocks.

This fixture is only preparing future tests.

If the current forbidden terms rule still scans code blocks, document that current behavior clearly.

### 11.5 Profile Fixtures

Add at least one valid ReviewProfile fixture.

Suggested file:

```text
tests/fixtures/profiles/default.yml
```

It should match the current ReviewProfile schema.

Add `strict.yml` only if the current schema supports it cleanly.

Do not invent unsupported profile fields.

### 11.6 Expected Report Fixture

Add one expected Markdown report fixture only if the current report output is stable enough.

Suggested file:

```text
tests/fixtures/expected_reports/forbidden_terms_report.md
```

If the report includes unstable absolute paths, avoid using a full snapshot fixture and test only key sections instead.

## 12. Examples Directory Requirements

Add a small manual usage example under:

```text
examples/
```

Suggested files:

```text
examples/article.md
examples/profile.yml
```

The example should allow this command to work:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
```

And this command:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output examples/review-report.md
```

Do not commit generated `examples/review-report.md` unless the project explicitly wants committed example outputs.

Prefer documenting it as a generated file.

If needed, add it to `.gitignore`.

## 13. Test Updates Required

Update tests to use fixtures where appropriate.

Do not replace every inline-string unit test.

Keep small unit tests simple.

Recommended approach:

### 13.1 Keep Inline Tests For Unit Logic

Keep inline strings in tests such as:

```text
tests/test_location.py
```

This makes low-level logic easy to read.

### 13.2 Use Fixtures For Integration-Like Tests

Use fixture files in tests such as:

```text
tests/test_cli.py
tests/test_review_pipeline.py
tests/test_markdown_report.py
```

Good candidates:

* CLI review with clean Markdown.
* CLI review with forbidden terms.
* CLI Markdown report stdout.
* CLI Markdown report output file.
* Review pipeline with multiline Markdown.

### 13.3 Add Fixture Path Helper

If useful, add a small helper inside tests.

Example:

```python
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"
MARKDOWN_FIXTURES = FIXTURES_DIR / "markdown"
PROFILE_FIXTURES = FIXTURES_DIR / "profiles"
EXPECTED_REPORTS = FIXTURES_DIR / "expected_reports"
```

Do not add a complex test utility framework.

## 14. Documentation Required

Add or update:

```text
docs/TESTING.md
docs/CLI.md
docs/REPORTS.md
```

### 14.1 `docs/TESTING.md`

This file should explain:

1. How to run tests.
2. What `tests/fixtures/` is for.
3. The difference between inline test strings and fixture files.
4. When to add a new fixture.
5. The difference between `tests/fixtures/` and `examples/`.
6. The current validation command:

```bash
uv run pytest
```

### 14.2 `docs/CLI.md`

Add a small section showing how to manually run the CLI against example files:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format text
uv run content-review review examples/article.md --profile examples/profile.yml --format json
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
```

### 14.3 `docs/REPORTS.md`

Add a short note explaining how to generate a Markdown report from the example files.

Example:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output examples/review-report.md
```

## 15. PROJECT_STATE Update

Update `PROJECT_STATE.md`.

Mention:

* TASK009 completed.
* Added test fixtures for Markdown review scenarios.
* Added profile fixtures.
* Added example files for manual CLI usage.
* Updated selected tests to use fixtures.
* Added or updated testing documentation.
* No review behavior changes were introduced.

## 16. CHANGELOG Update

Update `CHANGELOG.md`.

Suggested entry:

```markdown
## TASK-0009

### Added

- Added Markdown fixture files for clean and forbidden-term review scenarios.
- Added ReviewProfile fixture files for tests.
- Added example Markdown and profile files for manual CLI usage.
- Added testing documentation for fixtures and examples.

### Changed

- Updated selected CLI, review pipeline, and report tests to use committed fixtures where appropriate.
- Updated CLI and report documentation with example-file commands.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.
```

## 17. Validation Commands

After implementation, run:

```bash
uv run pytest
```

Also run manual smoke tests:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format text
uv run content-review review examples/article.md --profile examples/profile.yml --format json
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
```

If testing `--output`, avoid committing generated output unless intentionally documented.

Example:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output /tmp/content-review-example-report.md
```

## 18. Completion Criteria

This task is complete only when:

* `tests/fixtures/` exists.
* At least one clean Markdown fixture exists.
* At least one forbidden-term Markdown fixture exists.
* At least one ReviewProfile fixture exists.
* `examples/article.md` exists.
* `examples/profile.yml` exists.
* Selected tests use fixture files where appropriate.
* Existing inline unit tests remain readable.
* `docs/TESTING.md` is added or updated.
* `docs/CLI.md` is updated.
* `docs/REPORTS.md` is updated.
* `PROJECT_STATE.md` is updated.
* `CHANGELOG.md` is updated.
* `uv run pytest` passes.
* Manual CLI smoke commands work.
* No review behavior changes are introduced.

## 19. Known Limitations To Preserve

Do not try to solve these in TASK009:

* Fixtures do not define a complete article corpus.
* Examples are for manual local use only.
* Expected reports may be partial or minimal.
* Code block behavior is not changed.
* Snapshot testing is not required.
* Batch review is not implemented.
* LLM review is not implemented.

## 20. Final Agent Response Requirements

When the Agent finishes this task, it must report:

1. Files changed.
2. Fixture directories added.
3. Example files added.
4. Which tests were updated to use fixtures.
5. Whether docs/TESTING.md was added or updated.
6. Whether docs/CLI.md was updated.
7. Whether docs/REPORTS.md was updated.
8. Whether PROJECT_STATE.md was updated.
9. Whether CHANGELOG.md was updated.
10. Result of `uv run pytest`.
11. Manual CLI smoke test results.
12. Known limitations.

The final response must be concise and must not claim unsupported functionality.

