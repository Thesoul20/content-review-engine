
# TASK-0008: Add Markdown Review Report Export

## 1. Task Title

`TASK-0008: Add Markdown Review Report Export`

## 2. Task Status

Draft

## 3. Depends On

This task depends on:

* `TASK-0003: Add Markdown Reader and Profile Loading`
* `TASK-0004: Add Basic Forbidden Terms Rule`
* `TASK-0005: Add Minimal Review Pipeline`
* `TASK-0006: Add Minimal CLI Review Command`
* `TASK-0007: Add Finding Location and Context Snippets`

Do not start this task unless TASK007 has been completed and the existing test suite passes.

## 4. Goal

Add a minimal Markdown review report exporter.

After this task, users should be able to run the existing CLI review command and export a readable Markdown report file.

Example command:

```bash
content-review review path/to/article.md --profile path/to/profile.yml --format markdown --output review-report.md
```

The generated report should include:

1. Basic review summary.
2. Input document path.
3. Profile path or profile name if available.
4. Finding count.
5. Findings grouped in a readable format.
6. Rule ID.
7. Severity.
8. Message.
9. Line and column.
10. Matched text.
11. Context snippet.
12. Suggestion, when available.

This task should make the current rule-based review output easier to inspect, save, share, and use in future workflows.

## 5. Background

Before TASK008, the project already supports:

* Reading Markdown files.
* Loading YAML `ReviewProfile`.
* Running the minimal review pipeline.
* Detecting forbidden terms.
* Returning structured findings.
* Adding source location and context snippets to findings.
* Running review from CLI.
* Printing text output.
* Printing JSON output.

However, the CLI output is still mostly transient.

TASK008 adds a simple file-based report export path so users can keep audit results as a Markdown artifact.

This is also a foundation for future:

* Richer audit reports.
* Review history.
* CI integration.
* Human review workflows.
* API/MCP response formatting.
* Future diff tracking.
* Future LLM-assisted rewrite reports.

## 6. Non-Goals

This task must not implement any of the following:

* LLM-based review.
* Automatic rewriting.
* Diff tracking.
* Markdown auto-fix.
* Batch review.
* Watch mode.
* MCP server.
* REST API.
* GUI.
* Database storage.
* HTML/PDF report generation.
* Rule editing commands.
* New review strategy.
* New unrelated rule types.
* Rich terminal UI.

This task is only about adding a minimal Markdown report exporter and wiring it into the existing CLI.

## 7. Required Reading Before Coding

Before making any code changes, read:

```text
AGENTS.md
PROJECT_STATE.md
ROADMAP.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
tasks/TASK-0003-markdown-reader-and-profile-loading.md
tasks/TASK-0004-basic-forbidden-terms-rule.md
tasks/TASK-0005-minimal-review-pipeline.md
tasks/TASK-0006-minimal-cli-review-command.md
tasks/TASK-0007-finding-location-and-context-snippets.md
tasks/TASK-0008-markdown-review-report-export.md
```

If any file is missing, inspect the closest existing equivalent and mention the discrepancy in the final task summary.

## 8. Allowed Scope

This task may modify or add only the files needed for Markdown report export.

Likely allowed files:

```text
src/content_review_engine/reports/__init__.py
src/content_review_engine/reports/markdown.py
src/content_review_engine/cli.py
tests/test_markdown_report.py
tests/test_cli.py
docs/CLI.md
docs/REPORTS.md
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

If the current repository already has a reporting or output module, follow the existing structure instead of creating a new one.

## 9. Forbidden Scope

Do not rewrite the review pipeline.

Do not duplicate review logic inside the report exporter.

Do not run rules from the report module.

Do not add LLM calls.

Do not add database persistence.

Do not introduce heavy templating dependencies.

Do not add new third-party dependencies unless absolutely necessary.

Prefer simple Python string rendering for this task.

The report exporter must receive an existing `ReviewResult` or equivalent structured review output and render it.

## 10. CLI Design

Extend the existing `review` command.

Current supported formats should remain available:

```bash
content-review review article.md --profile profile.yml --format text
content-review review article.md --profile profile.yml --format json
```

TASK008 should add:

```bash
content-review review article.md --profile profile.yml --format markdown
```

TASK008 should also add an optional output file flag:

```bash
content-review review article.md --profile profile.yml --format markdown --output report.md
```

Expected behavior:

* If `--format markdown` and `--output` are provided, write the Markdown report to the given file.
* If `--format markdown` and `--output` is not provided, print the Markdown report to stdout.
* Existing `text` and `json` output behavior should remain backward compatible.
* It is acceptable for `--output` to work with `json` too, if this can be done cleanly.
* Do not force `text` output to support `--output` unless the existing CLI structure makes it trivial.

## 11. Markdown Report Format

The report should be stable, readable, and simple.

Suggested output:

```markdown
# Content Review Report

## Summary

- Document: `article.md`
- Profile: `profile.yml`
- Findings: 2

## Findings

### 1. forbidden_terms.absolute_claim

- Severity: warning
- Message: Found forbidden term: 绝对
- Line: 12
- Column: 8
- Matched: `绝对`
- Context: 这个方法绝对可以提升效率
- Suggestion: Consider replacing it with a more cautious expression.

### 2. forbidden_terms.absolute_claim

- Severity: warning
- Message: Found forbidden term: 永久
- Line: 18
- Column: 5
- Matched: `永久`
- Context: 这个服务永久可用
- Suggestion: Consider replacing it with a more cautious expression.
```

For a clean document:

```markdown
# Content Review Report

## Summary

- Document: `article.md`
- Profile: `profile.yml`
- Findings: 0

## Findings

No issues found.
```

The exact wording may differ, but the report should include the same essential information.

## 12. Report Renderer Requirements

Add a small report renderer function.

Preferred function name:

```python
render_markdown_report(...)
```

Suggested signature:

```python
def render_markdown_report(
    result: ReviewResult,
    *,
    document_path: str | None = None,
    profile_path: str | None = None,
) -> str:
    ...
```

If the existing project uses different model names, adapt to the current codebase.

The renderer should:

1. Accept existing review output.
2. Not run review rules itself.
3. Not read files itself.
4. Not write files itself.
5. Return a Markdown string.
6. Handle zero findings.
7. Handle findings without location.
8. Handle findings with location.
9. Escape or format matched text safely enough for Markdown readability.
10. Produce deterministic output suitable for tests.

## 13. File Writing Requirements

File writing should remain in the CLI layer, not the report renderer.

Suggested behavior:

```python
report = render_markdown_report(...)
if output_path:
    write_text(output_path, report)
else:
    print(report)
```

Rules:

* Parent directories do not need to be created automatically unless already standard in the project.
* If the output path cannot be written, return exit code `2`.
* Error message should be human-readable.
* Do not silently overwrite behavior beyond normal file write semantics.
* It is acceptable to overwrite the output file if the user explicitly provides the path.

## 14. Exit Code Rules

Preserve existing exit code behavior from TASK006 and TASK007.

Expected rules:

```text
0 = command executed successfully and no blocking error occurred
1 = review completed but findings include error or critical severity
2 = CLI usage error, missing file, invalid profile, unsupported format, or output write failure
```

Warnings alone should still return `0`.

Output write failure should return `2`.

## 15. Tests Required

Add or update tests for the Markdown report exporter.

### 15.1 Markdown Report With No Findings

Given a review result with no findings.

When rendering a Markdown report.

Then the report should include:

```text
# Content Review Report
Findings: 0
No issues found.
```

### 15.2 Markdown Report With Findings

Given a review result with at least one finding.

When rendering a Markdown report.

Then the report should include:

```text
rule_id
severity
message
line
column
matched text
context
suggestion
```

Use actual field names from the current data model.

### 15.3 Markdown Report Handles Missing Location

Given a finding without location.

Then the renderer should still produce a valid report.

It should not crash.

It may omit line, column, matched, and context fields when unavailable.

### 15.4 CLI Markdown Stdout

When running:

```bash
content-review review article.md --profile profile.yml --format markdown
```

Then:

* Exit code is valid.
* stdout contains `# Content Review Report`.
* stdout contains the finding details when findings exist.

### 15.5 CLI Markdown Output File

When running:

```bash
content-review review article.md --profile profile.yml --format markdown --output report.md
```

Then:

* Exit code is valid.
* stdout should be minimal or empty.
* `report.md` should be created.
* The file should contain `# Content Review Report`.
* The file should contain finding details when findings exist.

### 15.6 CLI Output Write Failure

Given an invalid or unwritable output path.

Then:

* Exit code is `2`.
* stderr contains a readable error message.

### 15.7 Existing CLI Behavior Still Works

Ensure existing CLI behavior still works:

```bash
content-review review article.md --profile profile.yml --format text
content-review review article.md --profile profile.yml --format json
```

These should not regress.

## 16. Documentation Required

Add or update:

```text
docs/CLI.md
docs/REPORTS.md
docs/ARCHITECTURE.md
```

`docs/CLI.md` should include:

* `--format markdown`
* `--output`
* Example command
* Example stdout behavior
* Example file export behavior
* Exit code behavior

`docs/REPORTS.md` should include:

* Purpose of Markdown reports.
* Current report structure.
* What information is included.
* Current limitations.

`docs/ARCHITECTURE.md` should only be updated if necessary.

If updated, keep it minimal and state that report rendering is a presentation layer on top of `ReviewResult`.

## 17. PROJECT_STATE Update

Update `PROJECT_STATE.md`.

Mention:

* TASK008 completed.
* Markdown review report renderer added.
* CLI supports `--format markdown`.
* CLI supports writing Markdown report to `--output`.
* Report includes summary and finding details.
* Report uses existing `ReviewResult` and finding location metadata.
* No LLM, rewriting, diff tracking, API, MCP, GUI, database, or batch review support was added.

## 18. CHANGELOG Update

Update `CHANGELOG.md`.

Suggested entry:

```markdown
## TASK-0008

### Added

- Added Markdown review report renderer.
- Added `--format markdown` support to the review CLI.
- Added optional `--output` support for exporting Markdown reports.
- Added report tests for clean results, findings, missing locations, and CLI export behavior.
- Added report documentation.

### Changed

- Extended CLI documentation with Markdown report examples.

### Not Added

- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.
- No batch review.
```

## 19. Validation Commands

After implementation, run:

```bash
uv run pytest
```

If the CLI entrypoint is available, also run a manual smoke test:

```bash
uv run content-review review path/to/sample.md --profile path/to/profile.yml --format markdown
```

And:

```bash
uv run content-review review path/to/sample.md --profile path/to/profile.yml --format markdown --output review-report.md
```

Use temporary files for smoke tests if the repository does not contain examples.

Do not commit unnecessary temporary artifacts.

## 20. Completion Criteria

This task is complete only when:

* A Markdown report renderer exists.
* The renderer accepts existing review results.
* The renderer does not run review logic itself.
* The renderer handles zero findings.
* The renderer handles findings with location.
* The renderer handles findings without location.
* CLI supports `--format markdown`.
* CLI supports `--output` for Markdown report export.
* Output write failures return exit code `2`.
* Existing text and JSON CLI output still works.
* Tests are added or updated.
* `uv run pytest` passes.
* `docs/CLI.md` is updated.
* `docs/REPORTS.md` is added or updated.
* `PROJECT_STATE.md` is updated.
* `CHANGELOG.md` is updated.
* No out-of-scope features are implemented.

## 21. Known Limitations To Preserve

The implementation should not try to solve these limitations in TASK008:

* Reports are Markdown only.
* Reports are generated from current in-memory review results.
* Reports are not persisted to a database.
* Reports do not include before/after diffs.
* Reports do not include automatic fixes.
* Reports do not include LLM analysis.
* Reports do not include batch summaries.
* Reports are plain Markdown, not HTML or PDF.

## 22. Final Agent Response Requirements

When the Agent finishes this task, it must report:

1. Files changed.
2. Report renderer added.
3. CLI options added or changed.
4. How the report renderer uses existing review results.
5. Tests added.
6. Result of `uv run pytest`.
7. Whether `docs/CLI.md` was updated.
8. Whether `docs/REPORTS.md` was added or updated.
9. Whether `PROJECT_STATE.md` was updated.
10. Whether `CHANGELOG.md` was updated.
11. Known limitations.

The final response must be concise and must not claim unsupported functionality.

