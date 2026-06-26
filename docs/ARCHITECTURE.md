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
- `content_review_engine.core.quality_gate`
- `content_review_engine.core.suppression`
- `content_review_engine.rules.check_forbidden_terms`
- `content_review_engine.rules.check_absolute_claims`
- `content_review_engine.rules.check_markdown_structure`
- `content_review_engine.rules.check_markdown_links_images`
- `content_review_engine.rules.build_default_rule_registry`
- `content_review_engine.rules.run_rules`
- `content_review_engine.review.review_document`
- `content_review_engine.reports.render_markdown_report`

Current CLI adapter:

```text
content-review review <markdown_file> --profile <profile_file>
content-review batch <input_dir> --profile <profile_file>
content-review profile validate <profile_file>
content-review profile init --template <template_name> --output <profile_file>
content-review profile list [--format text|json]
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
Inline Suppression Filtering
 ↓
Review Result
```

For batch review, the CLI adds a deterministic directory discovery step before the Markdown Reader.

The CLI currently supports reviewing one Markdown file with one YAML profile, reviewing a directory of Markdown files with one YAML profile, validating a YAML profile independently before a review run, initializing a local profile from a built-in template, and listing the built-in templates exposed by the same registry.
It prints simple human-readable summaries, supports JSON output, and can export Markdown review reports for both single-file and batch review.
It also supports a CLI quality gate through `--fail-on`, using canonical severity ordering in the core package to choose automation-friendly exit codes.
It does not yet support HTML, watch mode, or report persistence beyond the optional Markdown output file.

Current deterministic rules:

- `forbidden_terms`
- `absolute_claims`
- `markdown_structure`
- `markdown_links_images`

## Rule Registry Boundaries

The current architecture intentionally keeps two rule registries with separate
responsibilities.

- `src/content_review_engine/core/rule_registry.py` is the metadata registry.
  It describes known built-in `rule_id` values and small internal metadata
  through `RuleDefinition`.
- `src/content_review_engine/rules/registry.py` is the deterministic execution
  registry. It registers runtime rule implementations, controls default
  enablement, and participates in the review pipeline.

Why both exist:

- the metadata registry gives docs, tests, future CLI metadata display, and
  profile guidance a stable descriptive source
- the execution registry keeps runtime rule wiring explicit and operational
- separating them avoids coupling user-facing rule descriptions to the runtime
  rule objects too early

The metadata registry is descriptive only. It does not execute rules, parse
Markdown, match content, apply suppression, compute quality gates, or change
JSON output schemas.

The execution registry is operational. It decides which deterministic rule
implementations run during review, but it is not the primary user-facing
metadata source for docs or profile guidance.

Profile-configured `regex_rules` are a separate runtime profile-driven path.
Their individual rule IDs are dynamic, so they are not pre-registered as
built-in metadata definitions or built-in execution-registry entries.
Instead, the review runner executes configured regex rules directly from the
loaded `ReviewProfile` and emits normal `ReviewFinding` objects.

They should not be merged yet. The project only has one current deterministic
execution path, but it already has multiple descriptive use cases for stable
rule metadata. Keeping the registries separate preserves a clean boundary while
the rule system grows.

Future deterministic rules should register stable metadata in the metadata
registry and register executable rule implementations in the execution
registry. Adding one does not replace the responsibility of the other.

Future LLM semantic review belongs as a separate later layer beside the
deterministic execution path. It should not be mixed into
`src/content_review_engine/rules/registry.py`. If added later, it should
produce compatible findings so reports, quality gates, and other downstream
consumers can keep a coherent result model.

Current boundary in flow form:

```text
Markdown Input
  ↓
Profile Loading
  ↓
Deterministic Rule Execution Registry
  ↓
Rule Findings
  ↓
Optional Future LLM Semantic Review
  ↓
Merged Findings
  ↓
Reports / Quality Gate / Exit Codes
```

Metadata stays on a separate descriptive path:

```text
Rule Metadata Registry
  ↓
Docs / Tests / Future CLI metadata display / Profile guidance
```

## Future LLM Review Layer

TASK-0034 adds only foundational future-facing LLM review data models under
`src/content_review_engine/llm/`.

Current status:

- the review engine remains deterministic for the main review pipeline
- `src/content_review_engine/llm/pydanticai.py` now provides an optional real
  `PydanticAIOpenAIReviewer` adapter
- PydanticAI exists only in the LLM provider layer
- the CLI can optionally route single-file and batch sidecar review to `mock`
  or `pydanticai-openai`
- the single-file Markdown report can now optionally append a separate
  `LLMReviewResult` section when `--format markdown`, `--enable-llm`, and
  `--include-llm-report` are all enabled
- no LLM output is merged into the current `ReviewResult`
- no LLM output is merged into deterministic severity counts, rule counts, or
  quality-gate evaluation
- batch review now supports per-file `LLMReviewResult` sidecars only and still
  has no LLM report integration
- the canonical deterministic JSON output schema remains unchanged

The intended future boundary is:

```text
Markdown Input
  ↓
Deterministic Rule Review
  ↓
Rule Findings
  ↓
Future Optional LLM Semantic Review
  ↓
LLMReviewResult
  ↓
Future Merge Layer
  ↓
Combined Report
```

Current single-file Markdown report boundary:

```text
ReviewResult
  ↓
Deterministic Markdown report sections

LLMReviewResult sidecar
  ↓ optional explicit CLI opt-in
LLM Markdown section

Deterministic Markdown report + optional appended LLM section
```

The optional Markdown integration is a presentation-only adapter boundary:

Current batch sidecar boundary:

```text
Batch Markdown discovery
  ↓
Deterministic batch review
  ↓
BatchReviewResult
  = canonical deterministic batch output

Per reviewed Markdown file:
  Markdown content
    ↓
  LLMReviewRequest
    ↓
  LLMReviewRunner
    ↓
  MockLLMReviewer or PydanticAIOpenAIReviewer
    ↓
  LLMReviewResult
    ↓
  Separate sidecar JSON under --llm-output-dir
```

Current batch path guarantees:

- batch LLM sidecars are opt-in and generated only when `--enable-llm` is set
- each reviewed Markdown file gets an independent `LLMReviewResult` JSON
  sidecar
- the sidecar path preserves the file path relative to the batch input
  directory and appends `.llm-review.json`
- the canonical `BatchReviewResult` schema is unchanged
- batch Markdown reports remain deterministic-only
- batch quality gates still read only deterministic findings

- `render_markdown_report` can accept `llm_result: LLMReviewResult | None`
- `None` preserves the existing deterministic Markdown output exactly
- a provided `LLMReviewResult` appends `## LLM Review` after the deterministic
  sections
- LLM findings do not mutate `ReviewResult`
- LLM findings do not affect deterministic summary counts, rule counts, or
  `--fail-on`
- the separate `LLMReviewResult` JSON sidecar is still written and remains the
  machine-readable contract

The current `LLMReviewFinding`, `LLMReviewSummary`, and `LLMReviewResult`
models exist so later tasks can add provider adapters, prompt versioning, and
conversion logic without changing the current deterministic review contract.

TASK-0035 adds the next provider-facing boundary:

```text
Markdown content
  ↓
LLMReviewRequest
  ↓
LLMReviewer
  ↓
LLMReviewResult
```

Current LLM provider-boundary status:

- `src/content_review_engine/llm/models.py` defines `LLMReviewRequest`
- `src/content_review_engine/llm/provider.py` defines a small synchronous
  `LLMReviewer` protocol
- `src/content_review_engine/llm/mock.py` defines `MockLLMReviewer`, a
  deterministic adapter for tests and future wiring work
- `src/content_review_engine/llm/pydanticai.py` defines
  `PydanticAIOpenAIReviewer`, which maps structured PydanticAI output into the
  existing `LLMReviewResult`

TASK-0036 adds the runner boundary:

```text
LLMReviewRequest
  ↓
LLMReviewRunner
  ↓
LLMReviewer
  ↓
LLMReviewResult
```

TASK-0037 and TASK-0038 add the first CLI plumbing for that boundary, but only
for an explicit single-file opt-in sidecar flow:

```text
content-review review
  ↓
Markdown Reader + Profile Loader
  ↓
Deterministic Review Pipeline
  ↓
ReviewResult

content-review review --enable-llm --llm-output <path>
  ↓
Reuse current Markdown input
  ↓
LLMReviewRequest
  ↓
LLMReviewRunner
  ↓
MockLLMReviewer or PydanticAIOpenAIReviewer
  ↓
LLMReviewResult
  ↓
JSON sidecar file
```

Important current boundaries:

- the deterministic `ReviewResult` remains the main CLI output
- the LLM result is serialized separately as a sidecar JSON file
- the current Markdown report structure does not read the LLM sidecar
- the current quality gate does not read the LLM sidecar
- batch review does not participate in this LLM path
- PydanticAI, OpenAI-compatible model configuration, and API-key environment
  variable loading are confined to the provider-selection path for this sidecar
- the deterministic review pipeline, canonical JSON schema, Markdown report,
  and batch flow do not import PydanticAI

TASK-0036 adds a dedicated execution boundary between request construction and
provider invocation:

```text
Markdown content
  ↓
LLMReviewRequest
  ↓
LLMReviewRunner
  ↓
LLMReviewer
  ↓
LLMReviewResult
```

Current LLM runner status:

- `src/content_review_engine/llm/runner.py` defines `LLMReviewRunner`
- the runner is intentionally small and only coordinates `run(request)` to
  `reviewer.review(request)`
- the runner receives its `LLMReviewer` dependency through constructor
  injection
- provider-layer `LLMReviewError` failures propagate unchanged
- `MockLLMReviewer` remains the deterministic test adapter for the runner
- the runner is now wired only into the single-file CLI LLM sidecar flow
- `src/content_review_engine/llm/errors.py` defines minimal future-facing LLM
  error types

This layer is still isolated:

- no merge into the deterministic `ReviewResult`
- no Markdown report integration
- no batch review integration
- no quality-gate integration
- no API, MCP, or GUI integration
- no merged output with the current canonical `ReviewResult`

Future tasks must still decide whether LLM findings are converted into
`ReviewFinding`, whether they participate in quality gates, how suppression
works for them, and how confidence and rationale are displayed.

Current review pipeline:

- `review_document()` accepts already-loaded Markdown text and a loaded `ReviewProfile`.
- The pipeline runs deterministic rules in memory through the rule runner.
- The default registry currently registers the deterministic `forbidden_terms`
  rule as default-enabled.
- The deterministic `absolute_claims` rule is registered as opt-in through
  `ReviewProfile.enabled_rules` or rule-style YAML configuration.
- The deterministic `markdown_structure` rule is registered as opt-in through
  `ReviewProfile.enabled_rules`.
- The deterministic `markdown_links_images` rule is also registered as opt-in
  through `ReviewProfile.enabled_rules`.
- Profile-configured `regex_rules` run deterministically from the active
  profile and are not stored in the built-in metadata registry because their
  `rule_id` values are dynamic.
- The pipeline returns a canonical `ReviewResult`.
- The pipeline parses supported Markdown inline suppression comments after rule
  execution and filters suppressed findings before creating the
  `ReviewResult`.

Current report generation:

- `render_markdown_report()` accepts a `ReviewResult` and renders a Markdown report.
- `render_batch_markdown_report()` accepts a `BatchReviewResult` and renders a batch Markdown report.
- The report renderer does not run rules, read Markdown files, or write output files.

Current quality gate support:

- `content_review_engine.core.quality_gate` defines canonical severity ordering:
  `info < warning < error < critical`.
- The CLI adapter evaluates `ReviewSummary.severity_counts` or
  `BatchReviewSummary.severity_counts` after rendering succeeds.
- Because inline suppression is applied before summaries are computed, quality
  gates evaluate only unsuppressed findings.
- `ReviewResult` and `BatchReviewResult` schemas are unchanged by quality-gate
  evaluation.

Current profile validation support:

- `content_review_engine.config.validate_profile` reuses the existing
  `load_profile()` path and adds a thin validation-result wrapper for CLI use.
- The `profile validate` command does not run review rules against Markdown
  content.
- Invalid, missing, unreadable, or unparsable profiles return exit code `2`,
  which stays separate from quality-gate exit code `1`.

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
