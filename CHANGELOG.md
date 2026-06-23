# CHANGELOG.md

All notable changes to this project will be documented in this file.

This project follows a staged development process.

---

## Unreleased

### Added

- Added canonical `ReviewSummary`, `ReviewDocumentMetadata`, and `ReviewProfileMetadata` models.
- Added a canonical `ReviewResult` schema version: `review-result.v1`.
- Added explicit `review_result_to_dict()` and `review_result_to_json()` serialization helpers.
- Added `docs/schemas/review-result.schema.json` and `docs/schemas/README.md`.
- Added tests for `ReviewSummary`, `ReviewResult`, canonical serialization, the review pipeline, CLI JSON output, and Markdown report rendering.
- Added initial core data models:
  - `ReviewIssue`
  - `ReviewResult`
  - `ReviewProfile`
- Added `ReviewFinding` for deterministic rule matches.
- Added `SourceSpan` for source location metadata on review findings.
- Added validation tests for core data models.
- Added data model documentation.
- Added `pydantic` as a project dependency.
- Added `pytest` as a dev dependency for the test run.
- Added Markdown reader helper in `content_review_engine.parser`.
- Added YAML profile loader in `content_review_engine.config`.
- Added `profiles/wechat.yaml` as the initial review profile sample.
- Added tests for Markdown parsing and profile loading.
- Added deterministic forbidden terms rule support.
- Added tests for the forbidden terms rule.
- Added location metadata and context snippets to forbidden term findings.
- Added tests for location calculation, location-aware forbidden term findings, multiple findings, and CLI output.
- Added minimal in-memory review pipeline support.
- Added `review_document()` as the core review pipeline entrypoint.
- Added tests for the review pipeline.
- Added a minimal CLI entrypoint with `content-review review`.
- Added CLI tests for successful reviews, missing files, and help output.
- Added CLI JSON output support for review findings.
- Added `docs/CLI.md`.
- Added a Markdown report renderer in `content_review_engine.reports`.
- Added CLI `--format markdown` support.
- Added CLI `--output` support for writing rendered review output to a file.
- Added tests for the Markdown report renderer, CLI Markdown stdout, CLI Markdown output files, and output write failures.
- Added `docs/REPORTS.md`.
- Added packaging configuration so `uv run content-review` can install and expose the console script.
- Added a console-script smoke test for the packaged `content-review` entrypoint.

### Changed

- Updated the review pipeline to return `ReviewResult` instead of a bare findings list.
- Updated CLI JSON output to use canonical `ReviewResult` serialization.
- Updated Markdown report rendering to consume `ReviewResult`.
- Updated `docs/DATA_MODELS.md`, `docs/CLI.md`, and `docs/REPORTS.md` for the stabilized output contract.
- Updated `PROJECT_STATE.md` for TASK-0011 completion.
- Updated project state for the core data model foundation.
- Configured pytest to resolve the `src/` layout without manual `sys.path` edits.
- Updated architecture docs to describe the input layer.
- Updated architecture docs to include deterministic rules.
- Updated architecture docs to include the review pipeline layer.
- Updated review rule docs to include `forbidden_terms`.
- Extended review profile configuration with `forbidden_terms`.
- Added `pyyaml` as a project dependency.
- Updated architecture docs to include the CLI adapter and its current limits.
- Updated project state for TASK-0006 completion.
- Updated changelog for the CLI task.
- Extended `ReviewFinding` with optional `location` metadata.
- Updated data model documentation for source spans.
- Updated CLI text output to include line, column, matched text, and context when available.
- Updated CLI JSON output to include nested location objects.
- Updated project state for TASK-0007 completion.
- Updated changelog for TASK-0007.
- Updated CLI docs for Markdown report export.
- Updated architecture docs for the report renderer.
- Updated project state for TASK-0008 completion.
- Updated changelog for TASK-0008.
- Updated CLI and testing docs to prefer `uv run content-review`.
- Updated project state for TASK-0010 completion.

### Fixed

- Removed manual `sys.path` mutation from `tests/test_models.py`.

### Removed

- Nothing yet.

## TASK-0009

### Added

- Added Markdown fixture files for clean and forbidden-term review scenarios.
- Added multiline Markdown and code-block fixtures for review-path coverage.
- Added ReviewProfile fixture files for tests.
- Added example Markdown and profile files for manual CLI usage.
- Added testing documentation for fixtures and examples.

### Changed

- Updated selected CLI, review pipeline, and report tests to use committed fixtures where appropriate.
- Updated CLI and report documentation with example-file commands.
- Updated project state for the new fixture and example files.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.
