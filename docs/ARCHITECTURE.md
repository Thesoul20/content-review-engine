# Architecture

## Architecture Style

This project follows a Python package-first architecture.

The core package is the center of the system.

External interfaces such as CLI, Skill, MCP, API, and frontend are adapters.

---

## Target Architecture

```text
Frontend / Web / Tauri
        ↓
FastAPI Backend
        ↓
MCP Server / CLI / Skill
        ↓
Python Core Package
        ↓
Review Rules / AI Adapter / Diff / Reports
```

---

## Current Architecture

Current phase only includes:

```text
Python Core Package
CLI
Docs
Tasks
Tests
```

MCP, Skill, API, and frontend are planned but not implemented yet.

The current core package input layer includes:

```text
src/content_review_engine/parser/
src/content_review_engine/config/
src/content_review_engine/review/
src/content_review_engine/rules/
src/content_review_engine/reports/
profiles/
```

---

## Core Package Responsibility

The core package should handle:

- Markdown input processing
- Review profile loading
- Review pipeline coordination
- Rule execution
- Structured review findings and results
- Report generation
- Diff generation
- AI review adapter in later versions

Current implemented input helpers:

- `content_review_engine.parser.read_markdown`
- `content_review_engine.config.load_profile`
- `content_review_engine.rules.check_forbidden_terms`
- `content_review_engine.rules.check_markdown_structure`
- `content_review_engine.rules.check_markdown_links_images`
- `content_review_engine.rules.build_default_rule_registry`
- `content_review_engine.rules.run_rules`
- `content_review_engine.review.review_document`
- `content_review_engine.reports.render_markdown_report`

Current CLI adapter:

```text
content-review review <markdown_file> --profile <profile_file>
```

Current CLI flow:

```text
CLI
 ↓
Markdown Reader
 ↓
Profile Loader
 ↓
Review Pipeline
 ↓
Rule Runner
 ↓
Rule Registry
 ↓
Deterministic Rules
 ↓
Review Result
```

The CLI currently supports reviewing one Markdown file with one YAML profile.
It prints a simple human-readable summary, supports JSON output, and can export Markdown review reports.
It does not yet support HTML, batch review, or report persistence beyond the optional Markdown output file.

Current deterministic rules:

- `forbidden_terms`
- `markdown_structure`
- `markdown_links_images`

Current review pipeline:

- `review_document()` accepts already-loaded Markdown text and a loaded `ReviewProfile`.
- The pipeline runs deterministic rules in memory through the rule runner.
- The default registry currently registers the deterministic `forbidden_terms`
  rule as default-enabled and the deterministic `markdown_structure` rule as
  opt-in through `ReviewProfile.enabled_rules`.
- The deterministic `markdown_links_images` rule is also registered as opt-in
  through `ReviewProfile.enabled_rules`.
- The pipeline returns a canonical `ReviewResult`.

Current report generation:

- `render_markdown_report()` accepts a `ReviewResult` and renders a Markdown report.
- The report renderer does not run rules, read Markdown files, or write output files.

---

## Adapter Responsibility

Adapters should only call the core package.

Adapters include:

- CLI
- Skill
- MCP Server
- FastAPI backend
- Frontend

Adapters must not duplicate core review logic.

The CLI adapter only orchestrates existing helpers. It does not implement parsing, profile loading, or review rules itself.

---

## Forbidden Architecture

Do not do this:

```text
CLI contains review logic
MCP contains separate review prompt
API contains separate review pipeline
Skill contains business logic
```

Correct design:

```text
Markdown Reader
    ↓
Profile Loader
    ↓
Review Pipeline
    ↓
Deterministic Rules
    ↓
Review Result / Findings
```

Current adapter boundary:

```text
CLI / MCP / API / Skill
        ↓
content_review_engine core package
```

The current implementation includes a minimal CLI adapter, but still does not include LLM review, API, MCP, persistence, or frontend layers.
