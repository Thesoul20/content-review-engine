# TASK-0011: Stabilize ReviewResult Model and JSON Schema

## 1. Task Title

`TASK-0011: Stabilize ReviewResult Model and JSON Schema`

## 2. Task Status

Draft

## 3. Depends On

This task depends on:

* `TASK-0005: Add Minimal Review Pipeline`
* `TASK-0006: Add Minimal CLI Review Command`
* `TASK-0007: Add Finding Location and Context Snippets`
* `TASK-0008: Add Markdown Review Report Export`
* `TASK-0009: Add Markdown Fixtures and Example Review Files`
* `TASK-0010: Enable Packaged CLI Entrypoint`

Do not start this task unless TASK0010 has been completed and the existing test suite passes.

## 4. Goal

Stabilize the project's structured review output by introducing or finalizing a canonical `ReviewResult` model and JSON serialization contract.

After this task, the project should have one stable review result shape used by:

1. The review pipeline.
2. CLI JSON output.
3. Markdown report rendering.
4. Future API output.
5. Future MCP tool responses.
6. Future diff/rewrite workflows.

The project should also include a documented JSON Schema for the review result payload.

This task does not add new review behavior. It only stabilizes the output contract.

## 5. Background

Before TASK0011, the project already supports:

* Reading Markdown files.
* Loading YAML `ReviewProfile`.
* Running the minimal review pipeline.
* Returning review findings.
* Adding location metadata to findings.
* Running review through CLI.
* Rendering Markdown reports.
* Using committed test fixtures and examples.
* Running the packaged `content-review` CLI entrypoint.

However, the output contract is not yet fully stable.

Known limitations from earlier tasks include:

* CLI JSON output is a lightweight payload, not necessarily a full `ReviewResult` serialization.
* Markdown report rendering may operate directly on a list of `ReviewFinding` objects.
* Summary data may be assembled in the CLI layer instead of being owned by the review result model.
* Future API/MCP integration will need a stable response schema.

TASK0011 fixes this by making `ReviewResult` the canonical structured output.

## 6. Non-Goals

This task must not implement any of the following:

* New review rules.
* New forbidden terms behavior.
* LLM-based review.
* Automatic rewriting.
* Diff tracking.
* Markdown auto-fix.
* Batch review.
* Watch mode.
* MCP server.
* REST API.
* GUI.
* Database persistence.
* HTML/PDF report generation.
* Full OpenAPI generation.
* External schema validation dependency.
* Breaking CLI command semantics.

This task is only about stabilizing the review result model, JSON serialization, and documentation.

## 7. Required Reading Before Coding

Before making any code changes, read:

```text
AGENTS.md
PROJECT_STATE.md
ROADMAP.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
docs/REPORTS.md
docs/TESTING.md
pyproject.toml
tasks/TASK-0007-finding-location-and-context-snippets.md
tasks/TASK-0008-markdown-review-report-export.md
tasks/TASK-0009-markdown-fixtures-and-examples.md
tasks/TASK-0010-enable-packaged-cli-entrypoint.md
tasks/TASK-0011-stabilize-review-result-and-json-schema.md
```

If historical task files such as TASK0003-TASK0006 are missing, do not recreate them in this task.

Instead:

1. Inspect the current implementation.
2. Use existing docs, tests, fixtures, and project state as the source of truth.
3. Mention missing historical task files in the final summary only if relevant.

## 8. Allowed Scope

This task may modify or add only files related to review result modeling, serialization, schema documentation, tests, and documentation.

Likely allowed files:

```text
src/content_review_engine/core/models.py
src/content_review_engine/core/review.py
src/content_review_engine/core/serialization.py
src/content_review_engine/reports/markdown.py
src/content_review_engine/cli.py
tests/test_models.py
tests/test_review_pipeline.py
tests/test_cli.py
tests/test_markdown_report.py
tests/test_serialization.py
tests/fixtures/expected_reports/*.md
docs/DATA_MODELS.md
docs/CLI.md
docs/REPORTS.md
docs/schemas/review-result.schema.json
docs/schemas/README.md
PROJECT_STATE.md
CHANGELOG.md
```

If the current repository uses different file names, follow the existing structure.

## 9. Forbidden Scope

Do not rewrite the review pipeline.

Do not rewrite the CLI.

Do not change the meaning of existing findings.

Do not change forbidden term matching behavior.

Do not add new rule types.

Do not add new dependencies unless absolutely necessary.

Do not introduce Pydantic or JSON Schema validation libraries just for this task.

Do not generate schemas dynamically unless the project already has a schema generation convention.

Prefer simple Python data models and explicit serialization helpers.

## 10. Canonical ReviewResult Requirements

Introduce or finalize a canonical `ReviewResult` model.

If `ReviewResult` already exists, extend or normalize it carefully.

If it does not exist, add it in the existing core model layer.

The model should include at least:

```python
schema_version: str
summary: ReviewSummary
findings: list[ReviewFinding]
document: ReviewDocumentMetadata | None = None
profile: ReviewProfileMetadata | None = None
```

Suggested default:

```python
schema_version = "review-result.v1"
```

## 11. ReviewSummary Requirements

Add or finalize a `ReviewSummary` model.

Suggested fields:

```python
finding_count: int
severity_counts: dict[str, int]
```

Example:

```json
{
  "finding_count": 2,
  "severity_counts": {
    "info": 0,
    "warning": 2,
    "error": 0,
    "critical": 0
  }
}
```

If the current severity model only supports some levels, include only supported levels or document the behavior.

The summary should be computed from findings, not manually duplicated in multiple layers.

Suggested helper:

```python
def build_review_summary(findings: list[ReviewFinding]) -> ReviewSummary:
    ...
```

## 12. Document Metadata Requirements

Add a small optional document metadata model if useful.

Suggested model:

```python
class ReviewDocumentMetadata:
    path: str | None = None
```

Optional fields may include:

```python
name: str | None = None
```

Do not add unstable fields such as absolute paths unless necessary.

Prefer storing the path exactly as provided by the CLI.

## 13. Profile Metadata Requirements

Add a small optional profile metadata model if useful.

Suggested model:

```python
class ReviewProfileMetadata:
    path: str | None = None
    name: str | None = None
```

If the current `ReviewProfile` already has a name field, preserve it in metadata.

If not, use the profile path only.

Do not invent unsupported profile fields.

## 14. Review Pipeline Requirements

Update the review pipeline so it returns the canonical `ReviewResult`.

Expected behavior:

```python
result = review_document(markdown_text, profile)
```

The returned result should contain:

```text
schema_version
summary
findings
```

If the pipeline currently returns `list[ReviewFinding]`, update it to return `ReviewResult`.

If this is too disruptive, provide a transitional helper and update all internal callers in this task.

Do not keep two competing output contracts unless backward compatibility requires it.

If compatibility helpers are needed, name them clearly and document them.

## 15. Serialization Requirements

Add explicit JSON serialization helpers.

Preferred module:

```text
src/content_review_engine/core/serialization.py
```

Suggested functions:

```python
def review_result_to_dict(result: ReviewResult) -> dict:
    ...

def review_result_to_json(result: ReviewResult, *, indent: int = 2) -> str:
    ...
```

Serialization should:

1. Return stable field names.
2. Include `schema_version`.
3. Include `summary`.
4. Include `findings`.
5. Include `location` for findings when available.
6. Include `document` metadata when available.
7. Include `profile` metadata when available.
8. Omit optional fields only if the current project already follows that style.
9. Produce deterministic JSON suitable for tests.

Do not rely on object `__dict__` if it produces unstable or internal fields.

## 16. Canonical JSON Shape

The CLI JSON output should use the canonical `ReviewResult` serialization.

Expected shape:

```json
{
  "schema_version": "review-result.v1",
  "summary": {
    "finding_count": 2,
    "severity_counts": {
      "warning": 2
    }
  },
  "document": {
    "path": "examples/article.md"
  },
  "profile": {
    "path": "examples/profile.yml"
  },
  "findings": [
    {
      "rule_id": "forbidden_terms",
      "severity": "warning",
      "message": "发现风险词：保证赚钱",
      "location": {
        "start_line": 3,
        "start_column": 9,
        "end_line": 3,
        "end_column": 13,
        "start_offset": 12,
        "end_offset": 16,
        "matched_text": "保证赚钱",
        "context": "..."
      }
    }
  ]
}
```

The exact field order does not matter unless tests intentionally check deterministic JSON strings.

The field names should remain stable after this task.

## 17. JSON Schema Requirements

Add a JSON Schema file:

```text
docs/schemas/review-result.schema.json
```

The schema should document the canonical `ReviewResult` payload.

Minimum required top-level fields:

```text
schema_version
summary
findings
```

Optional top-level fields:

```text
document
profile
```

The schema should define:

```text
ReviewResult
ReviewSummary
ReviewFinding
SourceSpan
ReviewDocumentMetadata
ReviewProfileMetadata
```

Do not add a runtime dependency on a JSON Schema validator.

The schema is documentation and future integration groundwork.

If the project already has a schema directory, follow the existing structure.

## 18. Markdown Report Renderer Requirements

Update the Markdown report renderer so it accepts the canonical `ReviewResult`.

Preferred signature:

```python
def render_markdown_report(result: ReviewResult) -> str:
    ...
```

If document/profile metadata is needed, read it from `result.document` and `result.profile`.

Do not make the report renderer run review rules.

Do not make the report renderer read files.

Do not make the report renderer write files.

If a compatibility wrapper is needed for old tests, keep it small and document it.

## 19. CLI Requirements

Update the CLI so all output formats use the canonical `ReviewResult`.

Expected behavior:

```text
review command
→ read Markdown
→ load ReviewProfile
→ run review_document()
→ attach document/profile metadata if needed
→ render output
```

Output formats:

```text
text
json
markdown
```

Requirements:

1. `--format json` must use `review_result_to_json()`.
2. `--format markdown` must use `render_markdown_report(result)`.
3. Text output may either use `ReviewResult` directly or a small text renderer.
4. Existing CLI behavior should remain user-compatible.
5. Exit code behavior should remain unchanged.

## 20. Tests Required

Add or update tests for the canonical review result model.

### 20.1 ReviewSummary Test

Given a list of findings with severities.

When building a summary.

Then:

* `finding_count` is correct.
* `severity_counts` is correct.

### 20.2 ReviewResult Model Test

Given findings and metadata.

When constructing a `ReviewResult`.

Then:

* `schema_version` is present.
* `summary` is present.
* `findings` are preserved.
* `document` metadata is preserved.
* `profile` metadata is preserved.

### 20.3 Serialization Test

Given a `ReviewResult` with a finding and location.

When serializing to dict and JSON.

Then output contains:

```text
schema_version
summary.finding_count
summary.severity_counts
findings[0].rule_id
findings[0].severity
findings[0].message
findings[0].location.matched_text
document.path
profile.path
```

### 20.4 Review Pipeline Test

Given Markdown with forbidden terms.

When calling `review_document()`.

Then it returns a canonical `ReviewResult`.

The result should include:

```text
summary
findings
schema_version
```

### 20.5 CLI JSON Test

When running:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format json
```

Then stdout should parse as JSON and include:

```text
schema_version
summary
findings
document
profile
```

### 20.6 Markdown Report Test

When rendering a Markdown report.

Then it should accept `ReviewResult`, not just a raw findings list.

The report should still include:

```text
# Content Review Report
Findings:
Line:
Column:
Matched:
Context:
```

### 20.7 Backward Compatibility Test, If Needed

If old helpers are kept temporarily, add a small test showing they still behave as expected.

Do not preserve old behavior if it causes duplicate contracts.

## 21. Documentation Required

Update:

```text
docs/DATA_MODELS.md
docs/CLI.md
docs/REPORTS.md
docs/schemas/README.md
PROJECT_STATE.md
CHANGELOG.md
```

### 21.1 `docs/DATA_MODELS.md`

Document:

1. `ReviewResult`.
2. `ReviewSummary`.
3. `ReviewFinding`.
4. `SourceSpan`.
5. Document metadata.
6. Profile metadata.
7. Schema versioning.

### 21.2 `docs/CLI.md`

Document that `--format json` returns the canonical `ReviewResult` payload.

Include a small example:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format json
```

### 21.3 `docs/REPORTS.md`

Document that Markdown reports are rendered from `ReviewResult`.

Mention that reports are presentation-layer output and do not run review logic.

### 21.4 `docs/schemas/README.md`

Explain:

1. What `review-result.schema.json` is for.
2. That it describes the current v1 result contract.
3. That it is intended for future API/MCP integrations.
4. That runtime schema validation is not implemented yet.

## 22. PROJECT_STATE Update

Update `PROJECT_STATE.md`.

Mention:

* TASK0011 completed.
* Canonical `ReviewResult` model stabilized.
* Review summary added or normalized.
* CLI JSON output now uses canonical review result serialization.
* Markdown report renderer now consumes `ReviewResult`.
* JSON Schema added for review result payload.
* No review behavior changes were introduced.
* No LLM, rewrite, API, MCP, GUI, or database support was added.

## 23. CHANGELOG Update

Update `CHANGELOG.md`.

Suggested entry:

```markdown
## TASK-0011

### Added

- Added or finalized canonical `ReviewResult` model.
- Added review summary metadata for finding counts and severity counts.
- Added explicit review result serialization helpers.
- Added `review-result.schema.json` for the stable JSON output contract.
- Added tests for review result construction, summary generation, serialization, CLI JSON output, and Markdown report rendering.

### Changed

- Updated CLI JSON output to use canonical `ReviewResult` serialization.
- Updated Markdown report rendering to consume `ReviewResult`.
- Updated data model, CLI, report, and schema documentation.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.
```

## 24. Validation Commands

After implementation, run:

```bash
uv sync
uv run pytest
```

Run CLI smoke tests:

```bash
uv run content-review --help
uv run content-review review examples/article.md --profile examples/profile.yml --format text
uv run content-review review examples/article.md --profile examples/profile.yml --format json
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output /tmp/content-review-example-report.md
```

Optionally inspect JSON output:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format json
```

Confirm it contains:

```text
schema_version
summary
findings
document
profile
```

Do not commit generated files under `/tmp`.

## 25. Completion Criteria

This task is complete only when:

* A canonical `ReviewResult` model exists.
* `ReviewResult` includes or references summary information.
* Review summary includes finding count and severity counts.
* Review pipeline returns canonical `ReviewResult`.
* CLI JSON output uses canonical `ReviewResult` serialization.
* Markdown report renderer consumes canonical `ReviewResult`.
* JSON Schema exists at `docs/schemas/review-result.schema.json`.
* Tests are added or updated.
* `uv run pytest` passes.
* Manual CLI smoke tests pass.
* `docs/DATA_MODELS.md` is updated.
* `docs/CLI.md` is updated.
* `docs/REPORTS.md` is updated.
* `docs/schemas/README.md` is added or updated.
* `PROJECT_STATE.md` is updated.
* `CHANGELOG.md` is updated.
* No out-of-scope features are implemented.

## 26. Known Limitations To Preserve

Do not try to solve these in TASK0011:

* No runtime JSON Schema validation.
* No OpenAPI schema.
* No API server.
* No MCP server.
* No batch review result format.
* No persisted review history.
* No diff or rewrite output.
* No LLM-specific result fields.
* No HTML/PDF report output.

## 27. Final Agent Response Requirements

When the Agent finishes this task, it must report:

1. Files changed.
2. ReviewResult model changes.
3. ReviewSummary behavior.
4. Serialization helpers added or changed.
5. JSON Schema file added.
6. How CLI JSON output now uses ReviewResult.
7. How Markdown report rendering now uses ReviewResult.
8. Tests added or updated.
9. Result of `uv sync`.
10. Result of `uv run pytest`.
11. Manual CLI smoke test results.
12. Whether `docs/DATA_MODELS.md` was updated.
13. Whether `docs/CLI.md` was updated.
14. Whether `docs/REPORTS.md` was updated.
15. Whether `docs/schemas/README.md` was added or updated.
16. Whether `PROJECT_STATE.md` was updated.
17. Whether `CHANGELOG.md` was updated.
18. Known limitations.

The final response must be concise and must not claim unsupported functionality.
