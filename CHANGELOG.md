# CHANGELOG.md

All notable changes to this project will be documented in this file.

This project follows a staged development process.

---

## Unreleased

## TASK-0032

### Added

- Added a runnable demo workspace under `examples/demo/` with:
  - short demo articles for WeChat-style and technical-blog content
  - committed stable demo profiles
  - deterministic `regex_rules`
  - committed single-file Markdown demo reports
  - a demo README with commands for profile validation, single-file review,
    batch review, Markdown report output, JSON output, quality gates, and
    inline suppression
- Added `tests/test_demo_project.py` covering demo file presence, profile
  validation, regex-rule presence, findings, suppression, Markdown reports,
  JSON serialization, batch review, quality gates, and documentation links.

### Changed

- Updated `README.md`, `docs/QUICKSTART.md`, `docs/CLI.md`, and
  `docs/PROFILES.md` to point users to the runnable demo workspace.
- Updated `PROJECT_STATE.md` to record the new end-to-end demo project.
- Kept deterministic rule behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept JSON output schema unchanged.

### Not Added

- No LLM-based review.
- No PydanticAI integration.
- No API, MCP, or GUI behavior.
- No new rule types.
- No compliance guarantees.

## TASK-0031

### Added

- Added five practical built-in example/template profiles:
  `general-publishing`, `wechat-article`, `marketing-copy`,
  `technical-blog`, and `health-content`.
- Added profile-specific `regex_rules` to those templates for placeholders,
  exaggerated claims, guarantee-like wording, pressure tactics, unresolved
  draft markers, treatment guarantees, and self-diagnosis risks.
- Added `tests/test_profile_templates.py` to cover template discovery,
  validation, regex-rule presence, and conservative limitation wording.

### Changed

- Updated `src/content_review_engine/config/templates.py` so the new example
  profiles are discoverable through the existing built-in template registry.
- Updated CLI, profile, quickstart, README, project-state, and changelog
  documentation for the expanded template set and their intended use cases.
- Extended existing example-profile, CLI, quickstart, and serialization tests
  to include the new templates.
- Kept deterministic rule behavior unchanged.
- Kept `regex_rules` behavior unchanged.
- Kept suppression behavior unchanged.
- Kept quality-gate semantics unchanged.
- Kept Markdown report structure unchanged.
- Kept JSON output schema unchanged.

### Not Added

- No LLM-based review.
- No PydanticAI integration.
- No API, MCP, or GUI behavior.
- No compliance guarantees.

## TASK-0030

### Added

- Added optional profile-configured `regex_rules` to `ReviewProfile`.
- Added `RegexRuleConfig` validation for regex rule ID format, regex pattern
  compilation, required message content, optional suggestion normalization,
  and default `case_sensitive: false`.
- Added deterministic regex rule execution in
  `src/content_review_engine/rules/regex_rules.py`.
- Added regex rule tests in `tests/test_regex_rules.py` covering loading,
  validation, execution, suppression, summaries, reports, batch aggregation,
  and quality-gate participation.

### Changed

- Updated the rule runner so configured regex rules execute alongside the
  existing built-in deterministic rules and emit normal `ReviewFinding`
  objects.
- Updated profile validation summaries to include configured regex rule IDs and
  severities.
- Updated `docs/RULES.md`, `docs/PROFILES.md`, `docs/DATA_MODELS.md`,
  `docs/CLI.md`, `docs/ARCHITECTURE.md`, and `PROJECT_STATE.md` to document
  regex rule configuration, validation behavior, suppression, runtime
  participation, registry boundaries, and limitations.
- Kept existing built-in rule behavior unchanged.
- Kept suppression syntax unchanged.
- Kept Markdown report structure unchanged beyond normal inclusion of regex
  findings.
- Kept JSON output shape unchanged beyond normal inclusion of regex findings.
- Kept quality-gate semantics unchanged.

### Not Added

- No LLM-based review.
- No PydanticAI integration.
- No API, MCP, or GUI behavior.
- No cross-line regex matching.
- No compliance guarantees.

## TASK-0029

### Added

- Added documentation coverage in `tests/test_rule_registry_boundaries.py` for
  the metadata-registry versus execution-registry boundary.
- Added concise module docstrings to
  `src/content_review_engine/core/rule_registry.py` and
  `src/content_review_engine/rules/registry.py` so the separation is visible in
  the code.

### Changed

- Updated `docs/ARCHITECTURE.md` to explain the boundary between the
  descriptive rule metadata registry and the deterministic execution registry.
- Updated `docs/RULES.md` to clarify that
  `src/content_review_engine/core/rule_registry.py` is metadata-focused while
  `src/content_review_engine/rules/registry.py` remains execution-focused.
- Updated `docs/DATA_MODELS.md` to state that registry metadata does not change
  the JSON output schema and that future LLM findings should remain compatible
  with the existing finding model or a later compatible extension.
- Updated `docs/PROFILES.md` to clarify that the metadata registry does not
  replace profile configuration or profile parsing.
- Updated `PROJECT_STATE.md` to record the completed boundary documentation
  task.
- Kept runtime rule matching behavior unchanged.
- Kept suppression behavior unchanged.
- Kept CLI behavior unchanged.
- Kept Markdown report format unchanged.
- Kept JSON schema unchanged.
- Kept profile parsing behavior unchanged.
- Kept exit-code behavior unchanged.

### Not Added

- No regex rule support.
- No new review rule types.
- No LLM-based review behavior.
- No merged registry implementation.
- No review-pipeline refactor.

## TASK-0028

### Added

- Added `RuleDefinition` as a small internal rule metadata model.
- Added a centralized deterministic built-in rule registry in
  `src/content_review_engine/core/rule_registry.py`.
- Registered the current built-in rule IDs:
  `forbidden_terms`, `absolute_claims`, `markdown_structure`, and
  `markdown_links_images`.
- Added registry tests covering completeness, uniqueness, deterministic
  ordering, metadata lookup, unknown-rule handling, and metadata presence.

### Changed

- Updated `docs/RULES.md`, `docs/DATA_MODELS.md`, `docs/PROFILES.md`, and
  `PROJECT_STATE.md` to describe the centralized rule metadata registry.
- Kept runtime rule matching behavior unchanged.
- Kept suppression behavior unchanged.
- Kept CLI behavior unchanged.
- Kept Markdown report format unchanged.
- Kept JSON schema unchanged.
- Kept exit-code behavior unchanged.

### Not Added

- No new review rules.
- No new rule types.
- No regex rule support.
- No profile format changes.
- No LLM-based review.

## TASK-0027

### Added

- Added documentation coverage that verifies `docs/RULES.md` is identified as
  the canonical rule system reference.
- Added documentation coverage that verifies `docs/REVIEW_RULES.md` is only a
  compatibility stub pointing to `docs/RULES.md`.

### Changed

- Consolidated legacy rule documentation into `docs/RULES.md` and made its
  canonical status explicit.
- Migrated the remaining useful legacy details into `docs/RULES.md`,
  including the legacy top-level `forbidden_terms` profile input note and the
  current implementation/test path references for built-in rules.
- Replaced `docs/REVIEW_RULES.md` with a short compatibility stub.
- Updated `README.md`, `docs/QUICKSTART.md`, `docs/CLI.md`, `docs/PROFILES.md`,
  and `docs/CI.md` to consistently point readers to `docs/RULES.md` as the
  canonical rule reference.

### Not Added

- No new review rules.
- No rule-matching changes.
- No suppression changes.
- No CLI contract changes.
- No Markdown report structure changes.
- No JSON schema changes.
- No exit-code changes.
- No LLM-based review.

## TASK-0026

### Added

- Added `docs/RULES.md` as a dedicated rule system reference for the current
  deterministic review model.
- Documented the current built-in rule IDs:
  `forbidden_terms`, `absolute_claims`, `markdown_structure`, and
  `markdown_links_images`.
- Documented finding fields, severity levels, severity ordering, quality-gate
  behavior, `--fail-on` examples, rule counts, severity counts, suppression
  comments, batch aggregation behavior, reports, and current limitations.
- Added a documentation test that verifies the rule reference exists and covers
  the durable rule-system concepts.

### Changed

- Updated `README.md`, `docs/QUICKSTART.md`, `docs/CLI.md`, `docs/PROFILES.md`,
  and `docs/CI.md` to link the rule-system reference.
- Kept rule matching behavior, suppression behavior, CLI behavior, Markdown
  report format, JSON schema, and exit code behavior unchanged.

### Not Added

- No new review rules.
- No rule-matching changes.
- No suppression changes.
- No CLI contract changes.
- No JSON schema changes.
- No Markdown report structure changes.
- No exit-code changes.
- No LLM-based review.
- No compliance guarantees.

## TASK-0025

### Added

- Added `docs/QUICKSTART.md` with a command-driven first-run workflow covering
  dependency installation, `profile list`, `profile init`, `profile validate`,
  single-file review, batch review, `--fail-on`, Markdown report output,
  inline suppression, profile customization, exit codes, and CI handoff.
- Added a lightweight quickstart documentation test that verifies the document
  exists and includes the key CLI commands, report output example, suppression
  example, exit codes, doc links, and compliance limitation note.

### Changed

- Updated `docs/CLI.md` to link the quickstart from the main CLI reference.
- Updated `docs/PROFILES.md` and `docs/CI.md` to point readers to the
  quickstart for the end-to-end setup flow.
- Updated `README.md` and `PROJECT_STATE.md` to record the new onboarding
  documentation.
- Kept `profile list`, `profile init`, `profile validate`, `review`, `batch`,
  suppression behavior, `forbidden_terms`, `absolute_claims`, text/JSON/Markdown
  output, and `--fail-on` exit-code rules unchanged.

### Not Added

- No new review rules.
- No LLM review.
- No auto-fix behavior.
- No new CLI commands.
- No new output formats.
- No GitHub PR comments.
- No GitHub annotations.
- No SARIF output.
- No HTML report.
- No PDF report.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0024

### Added

- Added structured Markdown report sections for both `review` and `batch`:
  summary, severity counts, rule counts, findings tables, and detailed
  findings.
- Added quality-gate reporting to Markdown output when `--fail-on` is used,
  including gate status, threshold, and matched-gate count.
- Added deterministic batch Markdown sections for files with findings and
  per-file findings details.
- Added Markdown renderer and CLI tests for quality-gate sections, clear
  no-finding states, and writing report files before exit code `1`.

### Changed

- Improved Markdown empty states to use clear `No findings.` messaging while
  keeping suppressed findings excluded from reports.
- Kept single-file and batch JSON output schemas unchanged.
- Kept existing text output behavior unchanged.
- Kept `profile list`, `profile init`, `profile validate`, `review`, `batch`,
  suppression behavior, `forbidden_terms`, `absolute_claims`, and `--fail-on`
  exit-code rules unchanged.
- Updated `docs/CLI.md`, `docs/CI.md`, and `PROJECT_STATE.md` for the improved
  Markdown report behavior.

### Not Added

- No new review rules.
- No LLM review.
- No auto-fix behavior.
- No HTML report.
- No PDF report.
- No DOCX report.
- No SARIF output.
- No GitHub PR comments.
- No GitHub annotations.
- No GitHub Checks API integration.
- No new JSON schema.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0023

### Added

- Added a copyable GitHub Actions CI example at
  `docs/examples/github-actions/content-review.yml`.
- Added `docs/CI.md` describing profile validation, batch review,
  `--fail-on error`, path customization, CI exit codes, and workflow
  limitations.
- Added lightweight tests to ensure the CI example and CI documentation exist
  and contain the key automation commands.

### Changed

- Updated `docs/CLI.md` with CI-oriented usage, profile validation as a first
  CI step, and exit-code behavior for automation.
- Updated `docs/PROFILES.md` with CI-oriented profile usage, profile path and
  articles path customization guidance, and compliance limitations.
- Kept `profile list`, `profile init`, `profile validate`, `review`, `batch`,
  `--fail-on`, suppression, `forbidden_terms`, and `absolute_claims` behavior
  unchanged.

### Not Added

- No new review rules.
- No LLM review.
- No auto-fix behavior.
- No GitHub PR comments.
- No GitHub annotations.
- No SARIF output.
- No GitHub Checks API integration.
- No Marketplace Action.
- No remote profile loading.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0022

### Added

- Added `content-review profile list [--format text|json]`.
- Added canonical `profile-template-list.v1` JSON output for built-in template
  discovery.
- Added deterministic template descriptions for `general-basic`,
  `wechat-basic`, and `wechat-strict`.
- Added CLI tests for profile-list text output, JSON output, help output, and
  template-registry consistency with generated-profile validation.

### Changed

- Reused the same built-in template registry for both `profile list` and
  `profile init` so the supported template set stays consistent.
- Kept `profile init`, `profile validate`, `review`, `batch`, `--fail-on`,
  suppression, `forbidden_terms`, and `absolute_claims` behavior unchanged.
- Updated CLI, profile, architecture, data model, project state, and
  changelog documentation.

### Not Added

- No new review rules.
- No LLM review.
- No natural-language profile generation.
- No interactive wizard.
- No remote template loading.
- No user-defined template directories.
- No template marketplace.
- No profile aliases for `review` or `batch`.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0021

### Added

- Added `content-review profile init --template <name> --output <path>`.
- Added built-in template support for `general-basic`, `wechat-basic`, and
  `wechat-strict` by reusing the committed example profile YAML files.
- Added CLI tests for successful profile initialization, generated-profile
  validation, unknown templates, overwrite conflicts, `--force` overwrite,
  missing parent directories, and help output.

### Changed

- Kept generated profiles on the existing `load_profile()` validation path so
  initialized YAML files stay compatible with
  `content-review profile validate`.
- Updated CLI and profile documentation with the initialization workflow,
  template list, validation steps, and overwrite behavior.
- Updated project state documentation to record the new command and test
  coverage.

### Not Added

- No new review rules.
- No LLM review.
- No natural-language profile generation.
- No interactive wizard.
- No remote template loading.
- No user-defined template directories.
- No template marketplace.
- No `content-review profile list`.
- No profile aliases for `review` or `batch`.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0020

### Added

- Added built-in example profiles under `profiles/examples/`:
  `general-basic.yaml`, `wechat-basic.yaml`, and `wechat-strict.yaml`.
- Added example-profile tests for profile loading, CLI validation, and review
  integration coverage.
- Added `docs/PROFILES.md` describing profile structure, example profile
  purposes, validation, customization, and usage.

### Changed

- Updated CLI documentation with example-profile validation, review, and batch
  commands.
- Updated project state documentation to record the new example profiles and
  related test coverage.

### Not Added

- No new review rules.
- No LLM review.
- No automatic fixing.
- No profile generation, auto-formatting, or interactive wizard.
- No remote profile loading or runtime profile aliases.
- No `content-review profile list` or `content-review profile init`.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0019

### Added

- Added the `content-review profile validate <profile_path>` CLI command group
  and subcommand.
- Added canonical `profile-validation-result.v1` text and JSON outputs for
  profile validation.
- Added CLI tests for valid profiles, invalid profiles, invalid YAML, unknown
  rules, help output, and JSON output.

### Changed

- Reused the existing profile loader for CLI profile validation instead of
  introducing a second validation pipeline.
- Updated profile loading to report invalid YAML as a command/configuration
  error with a readable message.
- Updated CLI, architecture, data model, project state, and changelog
  documentation.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting or fixing.
- No profile generation, formatting, or wizard flow.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0018

### Added

- Added the deterministic `absolute_claims` rule with rule ID
  `absolute_claims`.
- Added rule-style YAML support for `absolute_claims.terms`,
  `absolute_claims.allow_terms`, and `absolute_claims.severity`.
- Added rule-specific suggestion text for `absolute_claims` findings.
- Added tests for profile loading, rule behavior, registry and runner
  integration, review pipeline integration, batch summaries, CLI output, and
  CLI quality-gate behavior.

### Changed

- Extended `ReviewFinding.severity` to support the canonical quality-gate
  severities `info`, `warning`, `error`, and `critical`.
- Added optional `suggestion` support to `ReviewFinding` and surfaced it in
  text, JSON, and Markdown output when present.
- Registered `absolute_claims` as an opt-in deterministic rule in the default
  registry.
- Updated architecture, data model, rule, CLI, project state, and schema
  documentation.

### Not Added

- No LLM review.
- No semantic claim detection.
- No regex, wildcard, or fuzzy matching.
- No automatic rewriting or fixing.
- No new output formats.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0017

### Added

- Added `allow_terms` support for `forbidden_terms` in rule-style YAML
  configuration.
- Added Markdown inline suppression comments:
  `content-review-disable-line <rule_id>` and
  `content-review-disable-next-line <rule_id>`.
- Added suppression filtering before `ReviewResult` creation so default text,
  JSON, and Markdown outputs only include unsuppressed findings.
- Added tests for allowlist behavior, suppression parsing and filtering, review
  pipeline integration, batch summary aggregation, and CLI quality-gate behavior.

### Changed

- Suppressed findings are excluded from single-file summaries, batch summaries,
  and `--fail-on` quality-gate checks.
- Updated architecture, data model, rule, CLI, project state, and changelog
  documentation.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting.
- No block-level, file-level, reason, or expiration suppression.
- No external allowlist files, regex allowlists, or wildcard allowlists.
- No `.gitignore` support.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.
- No publishing integration.

## TASK-0016

### Added

- Added `--fail-on` to `content-review review`.
- Added `--fail-on` to `content-review batch`.
- Added centralized quality-gate helpers with canonical severity ordering:
  `info < warning < error < critical`.
- Added CI-friendly exit-code behavior for quality gates.
- Added unit tests for severity threshold comparison and CLI tests for
  quality-gate exit codes.

### Changed

- Updated CLI command errors to consistently return exit code `2`.
- Preserved existing text, JSON, and Markdown output schemas and behavior.
- Updated `docs/ARCHITECTURE.md`, `docs/CLI.md`, `PROJECT_STATE.md`, and this
  changelog.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting.
- No inline suppression.
- No `.gitignore` support.
- No API server.
- No MCP server.
- No frontend.
- No database persistence.

## TASK-0015

### Added

- Added a minimal `content-review batch` command for deterministic Markdown directory review.
- Added deterministic file discovery helpers with `--recursive` and `--pattern` support.
- Added `BatchReviewSummary` and `BatchReviewResult` core models.
- Added batch JSON serialization helpers and a batch Markdown report renderer.
- Added batch fixtures, batch examples, discovery tests, summary tests, serialization tests, Markdown report tests, and CLI tests.

### Changed

- Reused the existing single-file `review_document()` pipeline for each batch file without duplicating rule logic.
- Preserved the canonical single-file `ReviewResult` contract and existing `content-review review` behavior.
- Updated `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, `docs/CLI.md`, `docs/REPORTS.md`, `docs/TESTING.md`, `docs/schemas/README.md`, `PROJECT_STATE.md`, and this changelog.

### Not Added

- No new review rules.
- No new rule behavior.
- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No Markdown auto-fix.
- No watch mode.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.
- No HTML/PDF report generation.
- No parallel execution.

## TASK-0014

### Added

- Added the deterministic `markdown_links_images` rule.
- Added Markdown fixture coverage for empty link text, empty link target,
  placeholder link target, empty image alt text, empty image target,
  placeholder image target, and fenced code block handling.
- Added `tests/fixtures/profiles/markdown_links_images.yml` and matching
  example files for manual CLI usage.
- Added tests for the new rule, registry and runner integration, review
  pipeline integration, and CLI JSON output.

### Changed

- Extended the rule registry to register `markdown_links_images` as opt-in so
  existing default profiles keep the same behavior.
- Preserved the default forbidden-terms behavior, the markdown_structure
  behavior, and the CLI contract.
- Updated `docs/ARCHITECTURE.md`, `docs/RULES.md`, `docs/REVIEW_RULES.md`,
  `docs/CLI.md`, `docs/TESTING.md`, `PROJECT_STATE.md`, and this changelog.

### Not Added

- No network link checking.
- No HTTP status validation.
- No local file existence checking.
- No image download.
- No image alt text quality scoring.
- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No Markdown auto-fix.
- No batch review.
- No watch mode.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.

## TASK-0013

### Added

- Added the deterministic `markdown_structure` rule.
- Added fixtures for missing H1, multiple H1, heading jumps, empty headings,
  long paragraphs, and fenced code block handling.
- Added `tests/fixtures/profiles/markdown_structure.yml` and matching example
  files for manual CLI usage.
- Added tests for the new rule, registry and runner integration, review
  pipeline integration, and CLI JSON output.

### Changed

- Extended the rule registry to track default-enabled rules so
  `markdown_structure` can be registered without changing the legacy implicit
  review path.
- Preserved the default forbidden-terms behavior and CLI contract.
- Updated `docs/ARCHITECTURE.md`, `docs/RULES.md`, `docs/REVIEW_RULES.md`,
  `docs/CLI.md`, `docs/TESTING.md`, `PROJECT_STATE.md`, and this changelog.

### Not Added

- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No Markdown auto-fix.
- No batch review.
- No watch mode.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.

## TASK-0012

### Added

- Added an internal rule interface, rule registry, and rule runner.
- Added a default rule registry containing the existing forbidden-terms rule.
- Added an optional `enabled_rules` field on `ReviewProfile` for explicit rule selection.
- Added tests for registry registration, duplicate rules, unknown rules, default registry behavior, rule runner behavior, review pipeline integration, and unknown-rule CLI handling.
- Added `docs/RULES.md`.

### Changed

- Updated the review pipeline to execute rules through the rule runner.
- Preserved canonical `ReviewResult` output.
- Preserved existing forbidden-terms behavior.
- Updated `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, `docs/CLI.md`, `PROJECT_STATE.md`, and this changelog.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No batch review.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.

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
