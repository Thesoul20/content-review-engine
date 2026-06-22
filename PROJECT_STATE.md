# PROJECT_STATE.md

## Current Phase

M1: Core input layer and minimal review pipeline.

The project currently has Markdown input handling, profile loading, deterministic review rules, and a minimal in-memory review pipeline on top of the initial data models.

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
- Initial core data models are in place.
- Markdown reader and YAML profile loading have been implemented.
- The first deterministic review rule has been implemented.
- A minimal review pipeline has been implemented.

---

## In Progress

- No active implementation task.

## Recent Completion

- TASK-0006 is complete.
- Added a minimal `content-review review` CLI command.
- The CLI can review one Markdown file with one YAML profile.
- The CLI uses the existing in-memory review pipeline and deterministic forbidden terms rule.
- The project still does not have LLM review, API, MCP, persistence, frontend, or JSON/HTML report export.

---

## Next Tasks

1. Add additional deterministic review rules.
2. Extend the review pipeline with more deterministic rules.

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
- Added Markdown reader support.
- Added YAML profile loading support.
- Added tests for Markdown parsing and profile loading.
- Added the first deterministic forbidden terms review rule.
- Added tests for the forbidden terms rule.
- Added a minimal review pipeline that runs `forbidden_terms` in memory.
- Added tests for the review pipeline.
- Added a minimal CLI entrypoint with a `review` subcommand.
- Added CLI tests for success, missing files, and help output.
- Updated architecture documentation, project state, and changelog for the CLI task.

### Changed Files

- `src/content_review_engine/core/__init__.py`
- `src/content_review_engine/core/models.py`
- `tests/test_models.py`
- `docs/DATA_MODELS.md`
- `PROJECT_STATE.md`
- `CHANGELOG.md`
- `pyproject.toml`
- `uv.lock`
- `src/content_review_engine/parser/__init__.py`
- `src/content_review_engine/parser/markdown.py`
- `src/content_review_engine/config/__init__.py`
- `src/content_review_engine/config/profiles.py`
- `profiles/wechat.yaml`
- `tests/test_markdown_parser.py`
- `tests/test_profile_loader.py`
- `docs/ARCHITECTURE.md`

### Test Result

`uv run pytest` passed.

### Next Recommended Task

TASK-0007: Add JSON Output Format.

### Notes

`tests/test_models.py` now imports `content_review_engine` normally, with pytest configured to include `src/` on the import path.
The core package now includes one deterministic rule: `forbidden_terms`.
