
# TASK-0015: Add Batch Review Command

## 1. Task Title

`TASK-0015: Add Batch Review Command`

## 2. Task Status

Draft

## 3. Depends On

This task depends on:

* `TASK-0011: Stabilize ReviewResult Model and JSON Schema`
* `TASK-0012: Add Rule Registry and Rule Runner`
* `TASK-0013: Add Markdown Structure Rule`
* `TASK-0014: Add Markdown Links and Images Rule`

Do not start this task unless TASK0014 has been completed and the existing test suite passes.

## 4. Goal

Add a minimal batch review command to the CLI.

After this task, users should be able to review multiple Markdown files in a directory with one command:

```bash
uv run content-review batch docs/articles --profile examples/profile.yml
```

The batch command should:

1. Discover Markdown files in a directory.
2. Load one `ReviewProfile`.
3. Run the existing review pipeline for each Markdown file.
4. Collect per-file `ReviewResult` objects.
5. Produce a simple batch summary.
6. Support text, JSON, and Markdown output formats.
7. Support writing output to a file with `--output`.
8. Preserve existing single-file `review` command behavior.

This task should not add new review rules. It only adds a batch execution layer on top of the existing review engine.

## 5. Background

Before TASK0015, the project already supports:

* Reading Markdown files.
* Loading YAML `ReviewProfile`.
* Running deterministic rules through `RuleRunner`.
* Running `forbidden_terms`.
* Running `markdown_structure` when explicitly enabled.
* Running `markdown_links_images` when explicitly enabled.
* Returning canonical `ReviewResult`.
* Serializing `ReviewResult` to JSON.
* Rendering Markdown reports.
* Running packaged CLI commands through `uv run content-review`.

However, the CLI currently reviews one Markdown file at a time.

Real content workflows often involve multiple Markdown files, such as:

* Draft article folders.
* Documentation directories.
* WeChat article collections.
* Pre-publish review folders.
* CI-style content checks.

TASK0015 adds a small batch review command without introducing database, API, MCP, parallelism, or watch mode.

## 6. Non-Goals

This task must not implement any of the following:

* New review rules.
* New rule behavior.
* LLM-based review.
* Automatic rewriting.
* Diff tracking.
* Markdown auto-fix.
* Watch mode.
* MCP server.
* REST API.
* GUI.
* Database persistence.
* HTML/PDF report generation.
* Parallel execution.
* Incremental caching.
* File watching.
* Git integration.
* CI configuration.
* Remote file loading.
* Complex glob engine.
* Recursive ignore rules similar to `.gitignore`.

This task is only about adding a minimal local batch review command.

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
tasks/TASK-0015-batch-review-command.md
```

If older historical task files are missing, do not recreate them in this task.

Instead:

1. Inspect the current implementation.
2. Use existing docs, tests, fixtures, examples, and project state as the source of truth.
3. Mention missing historical task files in the final summary only if relevant.

## 8. Allowed Scope

This task may modify or add files related to batch review execution, CLI integration, serialization, reports, tests, fixtures, examples, and documentation.

Likely allowed files:

```text
src/content_review_engine/review/batch.py
src/content_review_engine/core/models.py
src/content_review_engine/core/serialization.py
src/content_review_engine/reports/markdown.py
src/content_review_engine/cli.py
tests/test_batch_review.py
tests/test_cli.py
tests/test_serialization.py
tests/fixtures/batch/
tests/fixtures/batch/articles/
tests/fixtures/profiles/batch.yml
examples/batch/
examples/batch/articles/
examples/batch/profile.yml
docs/CLI.md
docs/REPORTS.md
docs/TESTING.md
docs/ARCHITECTURE.md
docs/schemas/batch-review-result.schema.json
docs/schemas/README.md
PROJECT_STATE.md
CHANGELOG.md
```

Optional, only if necessary:

```text
docs/DATA_MODELS.md
docs/RULES.md
```

If the current repository already has equivalent modules or directories, follow the existing structure instead of creating duplicates.

## 9. Forbidden Scope

Do not change the canonical single-file `ReviewResult` contract.

Do not change `ReviewFinding` semantics.

Do not change `SourceSpan` semantics.

Do not change existing rule behavior.

Do not enable opt-in rules by default.

Do not rewrite the CLI.

Do not rewrite the rule runner.

Do not add new dependencies.

Do not add parallel execution.

Do not add async execution.

Do not add network access.

Do not add database persistence.

Do not add full snapshot testing framework.

Do not implement file ignore patterns beyond a minimal built-in behavior.

## 10. CLI Design

Add a new CLI subcommand:

```bash
content-review batch <input_dir> --profile <profile_path>
```

Supported options:

```bash
content-review batch <input_dir> --profile <profile_path> --format text
content-review batch <input_dir> --profile <profile_path> --format json
content-review batch <input_dir> --profile <profile_path> --format markdown
content-review batch <input_dir> --profile <profile_path> --format markdown --output batch-report.md
content-review batch <input_dir> --profile <profile_path> --recursive
content-review batch <input_dir> --profile <profile_path> --pattern "*.md"
```

Required argument:

```text
input_dir
```

Required option:

```text
--profile
```

Optional options:

```text
--format text|json|markdown
--output <path>
--recursive
--pattern <glob>
```

Defaults:

```text
--format text
--pattern "*.md"
--recursive disabled
```

Do not add multiple input directories in this task.

Do not add multiple profiles in this task.

## 11. File Discovery Requirements

Add a small deterministic file discovery helper.

Suggested behavior:

```python
def discover_markdown_files(
    input_dir: Path,
    *,
    pattern: str = "*.md",
    recursive: bool = False,
) -> list[Path]:
    ...
```

Requirements:

1. `input_dir` must be a directory.
2. If `input_dir` does not exist, return CLI exit code `2`.
3. If `input_dir` is not a directory, return CLI exit code `2`.
4. Default pattern should be `*.md`.
5. Non-recursive mode should only scan the direct children of `input_dir`.
6. Recursive mode should scan nested directories.
7. Return files in sorted deterministic order.
8. Ignore directories.
9. Do not implement `.gitignore` support.
10. Do not scan hidden files specially unless current project already has a convention.

## 12. Batch Result Model Requirements

Add a minimal batch result model.

Preferred model name:

```python
BatchReviewResult
```

Suggested fields:

```python
schema_version: str
summary: BatchReviewSummary
results: list[ReviewResult]
```

Suggested default:

```python
schema_version = "batch-review-result.v1"
```

Add a summary model:

```python
BatchReviewSummary
```

Suggested fields:

```python
file_count: int
reviewed_count: int
finding_count: int
files_with_findings: int
severity_counts: dict[str, int]
```

Rules:

1. `file_count` is the number of discovered Markdown files.
2. `reviewed_count` is the number of files successfully reviewed.
3. `finding_count` is the total number of findings across all files.
4. `files_with_findings` is the number of files with at least one finding.
5. `severity_counts` aggregates severity counts across all `ReviewResult` objects.
6. Use stable severity buckets consistent with `ReviewSummary`.

Do not change the existing single-file `ReviewResult` model except if small helper methods are needed.

## 13. Batch Review Function Requirements

Add a batch review function.

Preferred module:

```text
src/content_review_engine/review/batch.py
```

Suggested function:

```python
def review_markdown_directory(
    input_dir: Path,
    profile: ReviewProfile,
    *,
    pattern: str = "*.md",
    recursive: bool = False,
) -> BatchReviewResult:
    ...
```

Requirements:

1. Use the existing Markdown reader if available.
2. Use the existing `review_document()` function for each file.
3. Do not duplicate review logic.
4. Attach document metadata to each per-file `ReviewResult`.
5. Preserve profile metadata where supported.
6. Return a `BatchReviewResult`.
7. Process files in deterministic sorted order.
8. If no files are found, return an empty batch result instead of crashing.
9. Do not stop the whole batch on review findings.
10. Expected file read errors should be handled clearly by the CLI.

For this task, it is acceptable to fail the whole batch with exit code `2` if one file cannot be read.

Do not implement partial success reporting in TASK0015 unless already easy.

## 14. Batch Serialization Requirements

Add explicit serialization helpers.

Preferred functions:

```python
def batch_review_result_to_dict(result: BatchReviewResult) -> dict:
    ...

def batch_review_result_to_json(result: BatchReviewResult, *, indent: int = 2) -> str:
    ...
```

Requirements:

1. Include `schema_version`.
2. Include `summary`.
3. Include `results`.
4. Each item in `results` should use the canonical `ReviewResult` serialization shape.
5. Deterministic JSON suitable for tests.
6. Do not use raw `__dict__` if it exposes internal fields.

## 15. Batch Markdown Report Requirements

Add or extend Markdown report rendering for batch results.

Preferred function:

```python
def render_batch_markdown_report(result: BatchReviewResult) -> str:
    ...
```

Suggested output:

```markdown
# Batch Content Review Report

## Summary

- Files discovered: 3
- Files reviewed: 3
- Files with findings: 2
- Findings: 5

## Files

### 1. `articles/a.md`

- Findings: 2

#### forbidden_terms

- Severity: warning
- Message: 发现风险词：保证赚钱
- Line: 3
- Column: 9
- Matched: `保证赚钱`
- Context: ...

### 2. `articles/b.md`

- Findings: 0

No issues found.
```

Requirements:

1. Include batch summary.
2. Include one section per file.
3. Include findings for each file.
4. Include “No issues found.” for clean files.
5. Use existing location information when available.
6. Do not write files inside the renderer.
7. File writing should remain in the CLI layer.
8. Keep output deterministic and testable.

## 16. Text Output Requirements

The batch text output should be simple and human-readable.

Suggested text output:

```text
Batch review completed.

Files discovered: 3
Files reviewed: 3
Files with findings: 2
Findings: 5

[articles/a.md] Findings: 2
[warning] forbidden_terms - 发现风险词：保证赚钱
Line: 3
Column: 9
Matched: 保证赚钱

[articles/b.md] Findings: 0
No issues found.
```

The exact wording can differ, but tests should assert stable key parts rather than entire output.

## 17. JSON Output Requirements

The batch JSON output should use `BatchReviewResult` serialization.

Expected top-level shape:

```json
{
  "schema_version": "batch-review-result.v1",
  "summary": {
    "file_count": 3,
    "reviewed_count": 3,
    "finding_count": 5,
    "files_with_findings": 2,
    "severity_counts": {
      "info": 0,
      "warning": 5,
      "error": 0,
      "critical": 0
    }
  },
  "results": [
    {
      "schema_version": "review-result.v1",
      "summary": {
        "finding_count": 2,
        "severity_counts": {
          "info": 0,
          "warning": 2,
          "error": 0,
          "critical": 0
        }
      },
      "document": {
        "path": "articles/a.md"
      },
      "findings": []
    }
  ]
}
```

Do not change single-file JSON output.

## 18. JSON Schema Requirements

Add a documentation-only JSON Schema file:

```text
docs/schemas/batch-review-result.schema.json
```

The schema should describe the batch result payload.

It may reference or mirror `review-result.v1` shape.

Do not add runtime JSON Schema validation.

Update:

```text
docs/schemas/README.md
```

Mention:

1. `review-result.schema.json`.
2. `batch-review-result.schema.json`.
3. That schemas are documentation contracts, not runtime validation.

## 19. Exit Code Rules

Preserve existing CLI exit code semantics.

Batch command exit codes:

```text
0 = command executed successfully and no blocking error occurred
1 = batch review completed but at least one finding has error or critical severity
2 = CLI usage error, invalid input directory, missing profile, unknown rule, file read error, output write failure, unsupported format
```

Warnings alone should return `0`.

If the project currently has only warning findings, normal batch findings should return `0`.

## 20. Fixture Requirements

Add batch fixtures.

Suggested structure:

```text
tests/fixtures/batch/
  articles/
    clean.md
    forbidden_terms.md
    markdown_quality.md
```

Add a profile fixture:

```text
tests/fixtures/profiles/batch.yml
```

Suggested profile:

```yaml
name: batch
enabled_rules:
  - forbidden_terms
  - markdown_structure
  - markdown_links_images
forbidden_terms:
  terms:
    - 保证赚钱
    - 绝对安全
```

Adapt the profile shape to the current `ReviewProfile` schema.

Do not invent unsupported fields.

## 21. Example Requirements

Add manual examples:

```text
examples/batch/
  articles/
    clean.md
    risky.md
    markdown-quality.md
  profile.yml
```

The following command should work:

```bash
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --format text
```

Also:

```bash
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --format json
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --format markdown
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --format markdown --output /tmp/content-review-batch-report.md
```

Do not commit generated report files.

## 22. Tests Required

Add or update tests for batch review.

### 22.1 File Discovery Test

Given a fixture directory with Markdown and non-Markdown files.

Then file discovery should return only Markdown files in sorted order.

### 22.2 Recursive Discovery Test

Given nested Markdown files.

When `recursive=True`.

Then nested Markdown files are included.

When `recursive=False`.

Then nested Markdown files are not included.

### 22.3 Empty Directory Test

Given an empty directory.

Then batch review returns a valid `BatchReviewResult` with zero files and zero findings.

### 22.4 Batch Review Result Test

Given multiple Markdown files and a profile.

When running batch review.

Then:

* A `BatchReviewResult` is returned.
* `summary.file_count` is correct.
* `summary.reviewed_count` is correct.
* `summary.finding_count` is correct.
* `results` contains per-file `ReviewResult` objects.

### 22.5 Batch Serialization Test

Given a `BatchReviewResult`.

When serializing to dict and JSON.

Then output includes:

```text
schema_version
summary.file_count
summary.finding_count
results
results[0].schema_version
results[0].findings
```

### 22.6 Batch Markdown Report Test

Given a `BatchReviewResult`.

When rendering Markdown report.

Then output includes:

```text
# Batch Content Review Report
Files discovered
Files reviewed
Files with findings
Findings
No issues found.
```

### 22.7 CLI Batch Text Test

When running:

```bash
content-review batch <fixtures/batch/articles> --profile <profile> --format text
```

Then:

* Exit code is valid.
* stdout contains batch summary.
* stdout contains per-file sections.

### 22.8 CLI Batch JSON Test

When running:

```bash
content-review batch <fixtures/batch/articles> --profile <profile> --format json
```

Then:

* stdout is valid JSON.
* JSON includes `schema_version = batch-review-result.v1`.
* JSON includes `summary`.
* JSON includes `results`.

### 22.9 CLI Batch Markdown Test

When running:

```bash
content-review batch <fixtures/batch/articles> --profile <profile> --format markdown
```

Then stdout contains:

```text
# Batch Content Review Report
```

### 22.10 CLI Batch Output File Test

When running:

```bash
content-review batch <fixtures/batch/articles> --profile <profile> --format markdown --output report.md
```

Then:

* Exit code is valid.
* Output file is created.
* Output file contains batch report content.

### 22.11 Invalid Input Directory Test

Given a missing input directory.

Then:

* Exit code is `2`.
* stderr contains a readable error message.

### 22.12 Existing CLI Regression Test

Existing single-file `review` command tests should continue to pass.

Do not break:

```bash
content-review review ...
```

## 23. Documentation Required

Update or add:

```text
docs/CLI.md
docs/REPORTS.md
docs/TESTING.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/schemas/README.md
docs/schemas/batch-review-result.schema.json
PROJECT_STATE.md
CHANGELOG.md
```

### 23.1 `docs/CLI.md`

Add a `batch` command section.

Document:

1. Basic usage.
2. Required `input_dir`.
3. Required `--profile`.
4. `--format text|json|markdown`.
5. `--output`.
6. `--recursive`.
7. `--pattern`.
8. Exit codes.
9. Example commands using `examples/batch/`.

### 23.2 `docs/REPORTS.md`

Document Markdown batch reports.

Mention:

1. Batch summary.
2. Per-file sections.
3. Findings per file.
4. Current limitations.

### 23.3 `docs/TESTING.md`

Document batch fixtures and manual smoke tests.

### 23.4 `docs/ARCHITECTURE.md`

Update architecture minimally:

```text
Directory input
→ file discovery
→ per-file review_document()
→ ReviewResult[]
→ BatchReviewResult
→ CLI text / JSON / Markdown batch report
```

### 23.5 `docs/DATA_MODELS.md`

Document:

1. `BatchReviewResult`.
2. `BatchReviewSummary`.
3. Relationship between `BatchReviewResult` and `ReviewResult`.

### 23.6 `PROJECT_STATE.md`

Update project state to mention:

* TASK0015 completed.
* Added batch review command.
* Added batch result model and summary.
* Added batch JSON serialization.
* Added batch Markdown report rendering.
* Added batch examples and fixtures.
* Existing single-file review behavior remains unchanged.
* No LLM, rewriting, diff, API, MCP, GUI, database, watch mode, or parallel execution was added.

### 23.7 `CHANGELOG.md`

Suggested entry:

```markdown
## TASK-0015

### Added

- Added `content-review batch` command for reviewing Markdown files in a directory.
- Added deterministic Markdown file discovery with optional recursive mode and pattern filtering.
- Added `BatchReviewResult` and `BatchReviewSummary`.
- Added batch JSON serialization.
- Added Markdown batch report rendering.
- Added batch fixtures and examples.
- Added tests for file discovery, batch review, serialization, reports, and CLI output.
- Added documentation for batch CLI usage and batch report output.

### Changed

- Extended CLI, reports, data model, testing, and architecture documentation.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.
- No parallel execution.
- No watch mode.
```

## 24. Validation Commands

After implementation, run:

```bash
uv sync
uv run pytest
```

Run existing single-file smoke tests:

```bash
uv run content-review --help
uv run content-review review examples/article.md --profile examples/profile.yml --format text
uv run content-review review examples/article.md --profile examples/profile.yml --format json
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
```

Run batch smoke tests:

```bash
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --format text
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --format json
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --format markdown
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --format markdown --output /tmp/content-review-batch-report.md
```

If recursive examples are added, also run:

```bash
uv run content-review batch examples/batch/articles --profile examples/batch/profile.yml --format text --recursive
```

Do not commit generated files under `/tmp`.

If the project has a check-state script, run it as well.

## 25. Completion Criteria

This task is complete only when:

* `content-review batch` command exists.
* Batch command accepts an input directory.
* Batch command requires a profile.
* Batch command supports `--format text`.
* Batch command supports `--format json`.
* Batch command supports `--format markdown`.
* Batch command supports `--output`.
* Batch command supports deterministic Markdown file discovery.
* Batch command supports optional recursive discovery.
* Batch command supports a simple `--pattern` option.
* `BatchReviewResult` exists.
* `BatchReviewSummary` exists.
* Batch JSON serialization exists.
* Batch Markdown report rendering exists.
* Batch review uses existing `review_document()` per file.
* Existing single-file review command still works.
* Tests are added or updated.
* `uv run pytest` passes.
* Manual CLI smoke tests pass.
* Batch docs are updated.
* `PROJECT_STATE.md` is updated.
* `CHANGELOG.md` is updated.
* No out-of-scope features are implemented.

## 26. Known Limitations To Preserve

Do not try to solve these in TASK0015:

* No parallel execution.
* No watch mode.
* No incremental caching.
* No database persistence.
* No CI integration files.
* No remote file loading.
* No advanced ignore rules.
* No `.gitignore` parsing.
* No per-file profile selection.
* No partial success result model unless trivial.
* No HTML/PDF report output.
* No LLM review.
* No automatic rewriting.
* No diff tracking.
* No API/MCP integration.

## 27. Final Agent Response Requirements

When the Agent finishes this task, it must report:

1. Files changed.
2. Batch command added.
3. File discovery behavior.
4. Batch result model added.
5. Batch summary behavior.
6. Batch serialization behavior.
7. Batch Markdown report behavior.
8. CLI options added.
9. How batch review uses existing `review_document()`.
10. Whether existing single-file CLI behavior changed.
11. Tests added or updated.
12. Result of `uv sync`.
13. Result of `uv run pytest`.
14. Manual single-file CLI smoke test results.
15. Manual batch CLI smoke test results.
16. Whether `docs/CLI.md` was updated.
17. Whether `docs/REPORTS.md` was updated.
18. Whether `docs/TESTING.md` was updated.
19. Whether `docs/DATA_MODELS.md` was updated.
20. Whether `docs/schemas/batch-review-result.schema.json` was added.
21. Whether `PROJECT_STATE.md` was updated.
22. Whether `CHANGELOG.md` was updated.
23. Known limitations.

The final response must be concise and must not claim unsupported functionality.

