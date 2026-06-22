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
- Added validation tests for core data models.
- Added data model documentation.
- Added `pydantic` as a project dependency.
- Added `pytest` as a dev dependency for the test run.
- Added Markdown reader helper in `content_review_engine.parser`.
- Added YAML profile loader in `content_review_engine.config`.
- Added `profiles/wechat.yaml` as the initial review profile sample.
- Added tests for Markdown parsing and profile loading.

### Changed

- Updated project state for the core data model foundation.
- Configured pytest to resolve the `src/` layout without manual `sys.path` edits.
- Updated architecture docs to describe the input layer.
- Added `pyyaml` as a project dependency.

### Fixed

- Removed manual `sys.path` mutation from `tests/test_models.py`.

### Removed

- Nothing yet.
