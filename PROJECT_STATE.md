# PROJECT_STATE.md

## Current Phase

M1: Core data model foundation.

The project is currently setting up its repository structure, documentation rules, and initial development workflow.

---

## Completed

- Project direction is defined as a Python package-first content review engine.
- Long-term extension targets are identified:
  - CLI
  - Skill
  - MCP
  - FastAPI backend
  - Frontend
- Development will use task-based Agent workflow.
- Repository memory will be stored in project files, not in chat history.

---

## In Progress

- Define the initial core data models.

---

## Next Tasks

1. Add Markdown reader.
2. Add profile loading.
3. Add first deterministic review rule.
4. Add basic tests for review flow.

---

## Open Questions

- Final package name has not been frozen.
- CLI command name has not been frozen.
- PydanticAI integration is planned but not part of M0.
- MCP integration is planned but not part of M0.

---

## Do Not Change Yet

- Do not add MCP server yet.
- Do not add Skill yet.
- Do not add FastAPI yet.
- Do not add Supabase yet.
- Do not add frontend yet.

---

## Last Handoff

### Completed

- Defined initial core data models.
- Added `ReviewIssue`.
- Added `ReviewResult`.
- Added `ReviewProfile`.
- Added validation tests for model creation.
- Added validation tests for invalid severity and invalid score.
- Updated data model documentation.
- Normalized test import configuration for the `src/` layout.

### Changed Files

- `src/content_review_engine/core/__init__.py`
- `src/content_review_engine/core/models.py`
- `tests/test_models.py`
- `docs/DATA_MODELS.md`
- `PROJECT_STATE.md`
- `CHANGELOG.md`
- `pyproject.toml`
- `uv.lock`

### Test Result

`uv run pytest` passed.

### Next Recommended Task

TASK-0003: Add Markdown reader and profile loading.

### Notes

No CLI, MCP, Skill, API, database, frontend, PydanticAI, Markdown parser, or review rule code was added.
`tests/test_models.py` now imports `content_review_engine` normally, with pytest configured to include `src/` on the import path.
