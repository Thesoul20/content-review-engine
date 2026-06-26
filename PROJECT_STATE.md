# PROJECT_STATE.md

## Current Phase

M1: Core input layer and minimal review pipeline.

The project currently has Markdown input handling, profile loading, standalone profile validation, deterministic review rules, forbidden-terms allowlists, absolute-claims rule configuration, Markdown inline suppression filtering, a minimal internal rule registry and rule runner, centralized built-in rule metadata, source location metadata on findings, a minimal in-memory review pipeline, a minimal batch CLI adapter, CLI quality-gate exit codes, and committed fixtures/examples for integration-style testing and manual CLI checks.
It now also supports optional profile-configured deterministic `regex_rules`
that validate patterns at profile load time and emit normal findings with
profile-defined rule IDs.
It also now includes a committed end-to-end demo workspace under
`examples/demo/` with small demo articles, stable demo profiles, committed
Markdown reports, and tests that exercise review, batch review, JSON output,
quality gates, and suppression without changing runtime behavior.
Profile validation failures are now also structured with stable issue paths,
codes, readable messages, and optional suggestions for CLI and future adapter
use.

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
- The CLI can export structured Markdown review reports with summaries,
  severity counts, rule counts, detailed findings, batch per-file sections,
  and quality-gate status.
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
- The built-in profile template system includes practical real-world
  templates for general publishing, WeChat articles, marketing copy,
  technical blogs, and health content, using existing deterministic rules and
  optional `regex_rules`.
- The CLI can initialize a new YAML review profile from a built-in template
  through `content-review profile init`.
- The CLI can list the built-in profile templates through
  `content-review profile list`.
- The repository includes a documented GitHub Actions CI example that validates
  a profile and runs batch review with `--fail-on error`.
- The repository includes a dedicated quickstart that documents the first-run
  workflow from dependency installation through profile setup, validation,
  single-file review, batch review, Markdown report output, inline
  suppression, and CI-oriented exit codes.
- The repository includes a dedicated rule system reference that documents the
  current built-in rule IDs, finding fields, severity ordering, quality-gate
  behavior, suppression comments, rule counts, severity counts, batch
  aggregation behavior, reports, and limitations.
- Review profiles can now define optional deterministic `regex_rules` with
  profile-defined rule IDs, compiled regex validation, configurable severity,
  message, optional suggestion, and optional case sensitivity.
- Regex rule findings participate in existing inline suppression, summaries,
  Markdown reports, JSON output, batch aggregation, quality gates, and exit
  code behavior through the normal review pipeline.
- The repository includes a small runnable demo project under `examples/demo/`
  that shows Markdown input, demo profiles, single-file review, batch review,
  Markdown report output, JSON output, inline suppression, and quality-gate
  behavior using the current CLI and report pipeline.

---

## In Progress

- No active implementation task.

## Recent Completion

- TASK-0036 is complete.
- Added `src/content_review_engine/llm/runner.py` with a lightweight
  synchronous `LLMReviewRunner` that accepts an injected `LLMReviewer`,
  forwards `LLMReviewRequest`, and returns `LLMReviewResult`.
- Exported `LLMReviewRunner` from `src/content_review_engine/llm/__init__.py`
  for package-level imports.
- Added runner tests covering reviewer invocation, configured mock behavior,
  default empty mock behavior, stable schema version, and provider error
  propagation.
- Updated architecture and data-model documentation to place the runner in the
  `LLMReviewRequest -> LLMReviewRunner -> LLMReviewer -> LLMReviewResult`
  flow and to document its separation from the deterministic review result
  schema.
- Kept deterministic review behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept current review JSON output schema unchanged.
- Added no real provider integration, no PydanticAI, no API keys, no prompt
  templates, no CLI LLM behavior, and no API, MCP, or GUI behavior.

- TASK-0035 is complete.
- Added future-facing `LLMReviewRequest`, a synchronous `LLMReviewer`
  provider protocol, minimal LLM error types, and a deterministic
  `MockLLMReviewer` under `src/content_review_engine/llm/`.
- Added tests for request validation, provider protocol compatibility, mock
  reviewer default and configured behavior, serialization of mock results, and
  the LLM error hierarchy.
- Updated architecture and data-model documentation to describe the future LLM
  provider boundary and deterministic mock adapter.
- Kept deterministic review behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept current review JSON output schema unchanged.
- Added no real provider integration, no PydanticAI, no API keys, no prompt
  templates, no CLI LLM behavior, and no API, MCP, or GUI behavior.

- TASK-0034 is complete.
- Added future-facing `LLMReviewFinding`, `LLMReviewSummary`, and
  `LLMReviewResult` models under `src/content_review_engine/llm/` with the
  stable schema version `llm-review-result.v1`.
- Added LLM serialization helpers that follow the existing explicit helper
  style without changing the current deterministic JSON output schema.
- Added tests for valid and invalid LLM model construction and serialization.
- Updated architecture, data-model, and rule documentation to place a future
  LLM semantic review layer behind a separate conversion and merge boundary.
- Kept deterministic review behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept current review JSON output schema unchanged.
- Added no provider integration, no PydanticAI, no API, no MCP, and no GUI
  behavior.

- TASK-0033 is complete.
- Added structured profile validation issues with `path`, `code`, `message`,
  and optional `suggestion`.
- Added reusable profile-loading validation failures so `profile validate`,
  `review`, and `batch` fail cleanly on invalid profiles without tracebacks for
  normal user input errors.
- Improved regex-rule and YAML validation feedback for invalid rule IDs,
  duplicate rule IDs, invalid regex patterns, empty regex messages, invalid
  `case_sensitive` values, invalid severities, and invalid YAML.
- Added invalid profile fixtures plus validation and CLI rendering tests.
- Updated README, quickstart, CLI, profile, and data-model documentation for
  structured profile validation errors.
- Kept deterministic review behavior unchanged.
- Kept `regex_rules` matching behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept JSON review output schema unchanged.
- Added no LLM review, PydanticAI, API, MCP, or GUI behavior.

- TASK-0032 is complete.
- Added `examples/demo/` with short WeChat-style and technical-blog demo
  articles plus stable demo profiles that include deterministic `regex_rules`.
- Added committed demo Markdown reports for the two single-file demo runs.
- Added demo-focused tests covering file presence, profile validation, regex
  rules, findings, suppression, Markdown report rendering, JSON serialization,
  batch review, quality-gate behavior, demo README commands, doc links, and
  conservative wording.
- Updated README, quickstart, CLI, and profile documentation so users can find
  the runnable demo directly from the main references.
- Kept deterministic rule matching behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression syntax unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept JSON output schema unchanged.
- Added no LLM review, PydanticAI, API, MCP, or GUI behavior.
- Added no legal, medical, advertising, regulatory, or platform compliance
  guarantees.

- TASK-0031 is complete.
- Added five practical built-in example/template profiles:
  `general-publishing`, `wechat-article`, `marketing-copy`,
  `technical-blog`, and `health-content`.
- Reused existing built-in rules plus profile-configured `regex_rules` to flag
  common placeholders, exaggerated claims, guarantee-like wording, pressure
  tactics, unresolved draft markers, and health-related caution cases.
- Kept template discovery and initialization on the existing registry-driven
  `profile list` and `profile init` path.
- Added tests for template discovery, initialization, validation, regex rule
  presence, and conservative documentation wording.
- Updated profile, quickstart, CLI, README, project state, and changelog
  documentation for the expanded template set and their limitations.
- Kept deterministic rule matching behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression syntax unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept JSON output schema unchanged.
- Added no LLM review, PydanticAI, API, MCP, or GUI behavior.
- Added no legal, medical, advertising, regulatory, or platform compliance
  guarantees.

- TASK-0030 is complete.
- Added optional `regex_rules` support to `ReviewProfile`.
- Added regex rule ID validation, regex pattern compilation validation, and
  duplicate regex rule ID rejection during profile loading and validation.
- Added deterministic line-by-line regex rule execution that produces one
  finding per match using the configured regex rule ID as `rule_id`.
- Reused the existing suppression, summary, report, batch, and quality-gate
  pipeline so regex findings participate without changing the canonical output
  shapes.
- Updated architecture, rule, profile, CLI, and data-model documentation for
  regex rule configuration, runtime behavior, registry boundary, and current
  limitations.
- Added regex-focused tests for loading, validation, execution, suppression,
  counts, reports, batch aggregation, and quality gates.
- Kept built-in rule behavior unchanged.
- Kept suppression syntax unchanged.
- Kept quality-gate semantics unchanged.
- Kept JSON output shape unchanged.

- TASK-0029 is complete.
- Documented the architectural boundary between the descriptive built-in rule
  metadata registry in `src/content_review_engine/core/rule_registry.py` and
  the deterministic execution registry in
  `src/content_review_engine/rules/registry.py`.
- Updated architecture, rule-system, data-model, and profile documentation to
  keep metadata concerns separate from runtime rule execution and profile
  configuration.
- Positioned future LLM semantic review as a separate later layer that should
  produce compatible findings if introduced later.
- Added documentation tests that keep the registry boundary explicit.
- Kept rule matching behavior, suppression behavior, CLI behavior, report
  format, JSON schema, profile parsing, and exit code behavior unchanged.

- TASK-0028 is complete.
- Added `RuleDefinition` plus a centralized deterministic built-in rule
  metadata registry in `src/content_review_engine/core/rule_registry.py`.
- Registered the current built-in rule IDs:
  `forbidden_terms`, `absolute_claims`, `markdown_structure`, and
  `markdown_links_images`.
- Added registry tests for completeness, uniqueness, deterministic ordering,
  lookup behavior, and metadata presence.
- Updated rule, data model, and profile documentation to mention the
  centralized built-in metadata registry.
- Kept rule matching behavior, suppression behavior, CLI behavior, report
  format, JSON schema, and exit code behavior unchanged.

- TASK-0027 is complete.
- Consolidated legacy rule documentation around `docs/RULES.md` as the
  canonical rule system reference.
- Migrated the remaining useful legacy details into `docs/RULES.md`,
  specifically the legacy top-level `forbidden_terms` profile input note and
  the implementation/test path references for the current built-in rules.
- Replaced `docs/REVIEW_RULES.md` with a short compatibility stub that points
  to `docs/RULES.md`.
- Updated current user-facing docs and documentation tests so they consistently
  point to `docs/RULES.md`.
- Kept rule matching behavior, suppression behavior, CLI behavior, report
  format, JSON schema, and exit code behavior unchanged.

- TASK-0026 is complete.
- Added `docs/RULES.md` as the dedicated rule system reference.
- Documented the current built-in rule IDs:
  `forbidden_terms`, `absolute_claims`, `markdown_structure`, and
  `markdown_links_images`.
- Documented current finding fields, severity levels, severity ordering,
  `--fail-on` behavior, rule counts, severity counts, suppression comments,
  batch aggregation behavior, reports, and limitations.
- Updated `README.md`, `docs/QUICKSTART.md`, `docs/CLI.md`, `docs/PROFILES.md`,
  and `docs/CI.md` to link the new rule reference.
- Added documentation tests that verify the rule reference exists, covers the
  durable rule-system concepts, and is linked from the user-facing docs.
- Kept rule matching behavior, suppression behavior, CLI behavior, report
  format, JSON schema, and exit code behavior unchanged.

- TASK-0025 is complete.
- Added `docs/QUICKSTART.md` covering `uv sync`, `profile list`,
  `profile init`, `profile validate`, `review`, `batch`, `--fail-on`,
  Markdown report output, inline suppression, exit codes, CI handoff, and
  compliance limitations.
- Added lightweight documentation tests that verify the quickstart exists and
  includes the core CLI commands, Markdown report flow, inline suppression,
  exit codes, and detailed-doc links.
- Updated `README.md`, `docs/CLI.md`, `docs/PROFILES.md`, `docs/CI.md`, and
  `CHANGELOG.md` to link the new quickstart.
- Kept `profile list`, `profile init`, `profile validate`, `review`, `batch`,
  suppression behavior, `forbidden_terms`, `absolute_claims`, text/JSON/Markdown
  output, and `--fail-on` exit-code rules unchanged.

- TASK-0024 is complete.
- Improved `content-review review --format markdown` and
  `content-review batch --format markdown` to render structured Markdown
  reports with summary tables, severity counts, rule counts, detailed findings,
  deterministic per-file batch sections, and clear `No findings.` empty
  states.
- Markdown reports now include quality-gate status when `--fail-on` is used
  and still write to `--output` before returning exit code `1` when the gate
  fails.
- Added Markdown rendering tests and CLI Markdown output tests covering
  quality-gate sections, empty states, and report-file writes.
- Updated CLI and CI documentation for improved Markdown report usage.
- Kept `profile list`, `profile init`, `profile validate`, `review`, `batch`,
  JSON schema, text output, suppression behavior, `forbidden_terms`,
  `absolute_claims`, and `--fail-on` exit-code rules unchanged.

- TASK-0023 is complete.
- Added a documented GitHub Actions example at
  `docs/examples/github-actions/content-review.yml`.
- Added `docs/CI.md` covering profile validation, batch review, CI exit codes,
  path customization, and workflow limitations.
- Added lightweight tests that ensure the CI example and CI documentation
  exist and include the key automation commands.
- Kept `profile list`, `profile init`, `profile validate`, `review`, `batch`,
  `--fail-on`, suppression, `forbidden_terms`, and `absolute_claims` behavior
  unchanged.

- TASK-0022 is complete.
- Added `content-review profile list` with `--format text|json`.
- Reused the built-in template registry as the single source of truth for both
  `profile list` and `profile init`.
- Added deterministic template descriptions and canonical
  `profile-template-list.v1` JSON output without embedding full YAML template
  content.
- Added CLI tests for text output, JSON output, help output, and registry
  consistency including generated-profile validation.
- Updated CLI, profile, architecture, data model, project state, and
  changelog documentation for the new profile discovery command.

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
