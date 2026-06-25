# PROJECT_STATE.md

## Current Phase

M1: Core input layer and minimal review pipeline.

The project currently has Markdown input handling, profile loading, standalone profile validation, deterministic review rules, forbidden-terms allowlists, absolute-claims rule configuration, Markdown inline suppression filtering, a minimal internal rule registry and rule runner, source location metadata on findings, a minimal in-memory review pipeline, a minimal batch CLI adapter, CLI quality-gate exit codes, and committed fixtures/examples for integration-style testing and manual CLI checks.

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
- A minimal Markdown report renderer has been implemented.
- The CLI can export Markdown review reports.
- The project is packaged so `uv run content-review` resolves the console script.
- The CLI supports automation-friendly quality gates with `--fail-on`.
- The `forbidden_terms` rule supports literal `allow_terms` in rule-style YAML configuration.
- The opt-in `absolute_claims` rule supports literal `terms`, optional `allow_terms`, and configurable finding severity in rule-style YAML configuration.
- Markdown inline comments can suppress `forbidden_terms` findings for the current line or next line.
- Markdown inline comments can also suppress `absolute_claims` findings for the current line or next line.
- The CLI can validate a YAML review profile independently through `content-review profile validate`.
- The repository includes built-in example profiles under `profiles/examples/`
  that validate through the existing profile validation command and can be used
  directly with `review` and `batch`.
- The CLI can initialize a new YAML review profile from a built-in template
  through `content-review profile init`.

---

## In Progress

- No active implementation task.

## Recent Completion

- TASK-0021 is complete.
- Added `content-review profile init` with required `--template` and
  `--output` options plus optional `--force`.
- Supported built-in templates:
  - `general-basic`
  - `wechat-basic`
  - `wechat-strict`
- Reused the committed example profiles as the template source and kept
  `review`, `batch`, and `profile validate` behavior unchanged.
- Added CLI tests for successful initialization, generated-profile validation,
  help output, unknown templates, overwrite conflicts, forced overwrite, and
  missing parent directories.
- Updated CLI and profile documentation with initialization workflow and
  overwrite rules.

- TASK-0020 is complete.
- Added built-in example profiles:
  - `profiles/examples/general-basic.yaml`
  - `profiles/examples/wechat-basic.yaml`
  - `profiles/examples/wechat-strict.yaml`
- Added tests that load the example profiles, validate them through
  `content-review profile validate`, and run review integration coverage with
  an example profile.
- Added `docs/PROFILES.md` and updated CLI documentation with example-profile
  usage and validation examples.

- TASK-0019 is complete.
- Added a new `content-review profile validate <profile_path>` CLI flow.
- Reused the existing profile loader for profile validation and kept review and
  batch behavior unchanged.
- Added canonical text and JSON outputs for profile validation results.
- Added CLI tests for valid profiles, invalid profiles, invalid YAML, unknown
  rules, and validation JSON output.

- TASK-0018 is complete.
- Added the deterministic `absolute_claims` rule with literal `terms`,
  optional literal `allow_terms`, and configurable finding severity.
- Added rule-style YAML loading for `absolute_claims` and kept existing
  `forbidden_terms` loading behavior compatible.
- Registered `absolute_claims` in the default rule registry as opt-in, and
  reused the existing review pipeline, suppression filtering, summaries, batch
  aggregation, and CLI quality gates.
- Added tests for profile loading, rule behavior, registry/runner integration,
  review pipeline behavior, batch summaries, CLI output, and quality-gate
  behavior for `absolute_claims`.

- TASK-0017 is complete.
- Added optional `allow_terms` support for the `forbidden_terms` rule through rule-style YAML configuration.
- Added Markdown inline suppression comments for `content-review-disable-line forbidden_terms` and `content-review-disable-next-line forbidden_terms`.
- Suppressed findings are filtered before `ReviewResult` creation, so they are excluded from text, JSON, and Markdown output.
- Batch summaries and quality gates now evaluate only unsuppressed findings.
- Added unit tests for allowlist behavior, suppression parsing/filtering, review pipeline filtering, batch summary behavior, and CLI quality-gate behavior.

- TASK-0016 is complete.
- Added `--fail-on` support to both `content-review review` and `content-review batch`.
- Added canonical severity ordering for quality gates: `info < warning < error < critical`.
- Added CI-friendly exit-code behavior: `0` for pass, `1` for quality-gate failure, and `2` for command errors.
- Kept `ReviewResult` and `BatchReviewResult` schemas stable.
- Added quality-gate helper tests and CLI exit-code tests.

- TASK-0015 is complete.
- Added a minimal `content-review batch` command that discovers Markdown files deterministically and reuses the existing review pipeline for each file.
- Added `BatchReviewSummary` and `BatchReviewResult` core models with canonical JSON serialization helpers.
- Added batch Markdown report rendering and batch CLI support for text, JSON, Markdown, `--output`, `--recursive`, and `--pattern`.
- Added batch fixtures, batch examples, discovery tests, summary tests, serialization tests, Markdown report tests, and CLI tests.
- Preserved the existing single-file `content-review review` behavior.

- TASK-0013 is complete.
- Added the deterministic `markdown_structure` rule.
- Kept `forbidden_terms` as the default-enabled rule.
- Added Markdown structure fixtures, example files, tests, and documentation.
- Preserved existing default forbidden-terms behavior and CLI behavior.

- TASK-0014 is complete.
- Added the deterministic `markdown_links_images` rule.
- Kept `markdown_links_images` opt-in through `ReviewProfile.enabled_rules`.
- Added Markdown links/images fixtures, example files, tests, and documentation.
- Preserved existing default forbidden-terms behavior, markdown_structure behavior, and CLI behavior.

- TASK-0012 is complete.
- Added a minimal internal rule interface, rule registry, and rule runner.
- The existing forbidden-terms rule now runs through the rule runner.
- The review pipeline still returns canonical `ReviewResult`.
- Added an optional `enabled_rules` field to `ReviewProfile` for explicit rule selection.
- Preserved existing CLI behavior for the default review path.
- Added tests for rule registry registration, duplicate rule IDs, unknown rule IDs, default registry behavior, rule runner behavior, review pipeline integration, and unknown-rule CLI handling.
- Added `docs/RULES.md` and updated architecture, data model, project state, and changelog documentation.

- TASK-0011 is complete.
- Added a canonical `ReviewResult` model with `ReviewSummary`, document metadata, and profile metadata support.
- Added explicit review result serialization helpers for dict and JSON output.
- Updated the review pipeline, CLI JSON output, and Markdown report rendering to use the canonical `ReviewResult`.
- Added a documented JSON Schema for `review-result.v1`.
- Updated the data model, CLI, report, project state, and changelog documentation for the stabilized output contract.
- Added tests for `ReviewSummary`, `ReviewResult`, serialization helpers, the review pipeline, CLI JSON output, and Markdown report rendering.

- TASK-0010 is complete.
- Added packaging configuration so the existing `content-review` console script is installable through `uv sync`.
- Updated CLI and testing docs to prefer `uv run content-review`.
- Added a console-script smoke test that checks the packaged entrypoint metadata.

- TASK-0009 is complete.
- Added committed Markdown fixtures for clean, forbidden-term, multiline, and code-block scenarios.
- Added committed ReviewProfile fixtures under `tests/fixtures/profiles/`.
- Added `examples/article.md` and `examples/profile.yml` for manual CLI usage.
- Updated selected tests to use fixture files where appropriate.
- Added `docs/TESTING.md` and updated CLI/report documentation for example-file commands.
- No review behavior changes were introduced.

- TASK-0008 is complete.
- Added a Markdown review report renderer in `content_review_engine.reports`.
- The CLI now supports `--format markdown`.
- The CLI now supports `--output` for writing rendered reports to a file.
- Added tests for the Markdown report renderer and CLI Markdown output paths.
- TASK-0007 is complete.
- Added source location metadata to review findings.
- The forbidden terms rule now reports matched text, line, column, character offsets, and a context snippet.
- The CLI now prints location-aware text output and JSON output with nested location objects.
- The project still does not have LLM review, API, MCP, persistence, frontend, diff tracking, or rewriting support.

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

- Added a minimal internal rule registry and rule runner.
- Routed the forbidden-terms rule through the runner.
- Added a default registry containing `forbidden_terms`.
- Added optional `enabled_rules` support to `ReviewProfile`.
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
- Added source location metadata for deterministic findings.
- Added CLI text and JSON output support for finding locations.
- Added tests for location calculation, location-aware forbidden term findings, and CLI JSON output.
- Added `docs/CLI.md`.
- Added `TASK-0007` completion updates.
- Updated architecture documentation, project state, and changelog for the CLI task.

### Changed Files

- `profiles/examples/general-basic.yaml`
- `profiles/examples/wechat-basic.yaml`
- `profiles/examples/wechat-strict.yaml`
- `tests/test_example_profiles.py`
- `tests/test_cli.py`
- `docs/PROFILES.md`
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

TASK-0008: Add a second deterministic review rule or expand the core review metadata further.

### Notes

`tests/test_models.py` now imports `content_review_engine` normally, with pytest configured to include `src/` on the import path.
The core package now includes one deterministic rule: `forbidden_terms`.
