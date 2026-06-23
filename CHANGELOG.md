# CHANGELOG.md

All notable changes to this project will be documented in this file.

This project follows a staged development process.

---

## Unreleased

### Added

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

### Changed

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

### Fixed

- Removed manual `sys.path` mutation from `tests/test_models.py`.

### Removed

- Nothing yet.
