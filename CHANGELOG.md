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

### Changed

- Updated project state for the core data model foundation.
- Configured pytest to resolve the `src/` layout without manual `sys.path` edits.

### Fixed

- Removed manual `sys.path` mutation from `tests/test_models.py`.

### Removed

- Nothing yet.
