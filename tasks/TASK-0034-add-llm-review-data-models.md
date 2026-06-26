# TASK-0034: Add LLM Review Data Models

## Status

Planned

## Goal

Add foundational data models for a future LLM-based semantic review layer.

The project already has a stable deterministic review engine with profile validation, regex rules, real-world templates, and an end-to-end CLI demo. TASK-0034 should define how future LLM review results will be represented, validated, documented, and eventually merged with deterministic rule findings.

This task must not call any LLM provider. It must not introduce PydanticAI yet.

## Background

The project direction is hybrid content review:

```text
Deterministic rules + future LLM semantic review
```

The deterministic rule engine currently provides:

* stable `rule_id`
* severity levels
* source locations
* matched text
* suggestions
* inline suppression
* rule counts
* severity counts
* Markdown reports
* JSON output
* batch review
* quality gates
* CLI exit codes
* profile templates
* demo project

Future LLM review should add capabilities such as:

* semantic risk detection
* context-aware judgment
* rationale
* confidence scoring
* rewrite suggestions
* article-level summary
* optional LLM review mode

However, before introducing PydanticAI or any provider integration, the project needs clear data models and boundaries.

TASK-0034 should define the model layer only.

## Scope

This task may modify or add:

* core data models
* LLM review model module
* serialization helpers if needed
* tests for LLM data models
* documentation for architecture and data models
* `PROJECT_STATE.md`
* `CHANGELOG.md`

Likely files to inspect:

```text
src/content_review_engine/core/models.py
src/content_review_engine/core/__init__.py
src/content_review_engine/reports/
src/content_review_engine/review/
src/content_review_engine/rules/
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/RULES.md
PROJECT_STATE.md
CHANGELOG.md
tests/
```

Potential new module:

```text
src/content_review_engine/llm/
src/content_review_engine/llm/models.py
```

or, if the existing project prefers central models:

```text
src/content_review_engine/core/llm_models.py
```

Choose the location that best fits the current repository structure.

## Non-goals

This task must not:

* call an LLM provider
* add PydanticAI
* add OpenAI / Anthropic / local model integration
* add prompt templates
* add LLM CLI flags
* add LLM review execution
* merge LLM findings into normal review results
* change deterministic rule behavior
* change regex rule behavior
* change suppression behavior
* change quality gate semantics
* change Markdown report structure
* change existing JSON review output schema
* change batch review behavior
* add API endpoints
* add MCP support
* add GUI support
* introduce compliance guarantees
* claim that LLM review provides legal, medical, advertising, regulatory, or platform compliance

## Required Work

### 1. Inspect Existing Finding And Review Models

Before making changes, inspect the current review data models.

Pay attention to:

```text
ReviewFinding
ReviewResult
BatchReviewResult
severity representation
source span / location model
matched_text
matched_term
suggestion
serialization behavior
Markdown report behavior
JSON output behavior
```

The new LLM models should align with the existing model style.

Do not alter existing deterministic review output.

### 2. Add LLM Review Model Module

Add a focused model layer for future LLM review.

Suggested module:

```text
src/content_review_engine/llm/models.py
```

Suggested package init:

```text
src/content_review_engine/llm/__init__.py
```

If the repository does not yet have an `llm` package, create one.

The package should contain only model definitions and simple validation helpers.

It should not contain provider clients, prompt execution, model calls, API keys, or network behavior.

### 3. Add LLM Review Finding Model

Add a model to represent one LLM-generated semantic finding.

Suggested name:

```python
LLMReviewFinding
```

Suggested fields:

```python
rule_id: str
severity: Severity
message: str
suggestion: str | None = None
rationale: str | None = None
confidence: float | None = None
line: int | None = None
column: int | None = None
end_line: int | None = None
end_column: int | None = None
matched_text: str | None = None
category: str | None = None
```

Recommended constraints:

* `rule_id` must be non-empty
* `message` must be non-empty
* `severity` must use the existing canonical severity values
* `confidence`, if present, must be between `0.0` and `1.0`
* line / column values, if present, must follow existing location conventions
* `rationale` should explain why the issue was flagged
* `suggestion` should describe how the user may improve the content

Suggested future rule ID style:

```text
llm_semantic_risk
llm_rewrite_suggestion
llm_claim_support
llm_tone_risk
```

Do not register these as deterministic built-in rules in the existing rule metadata registry yet unless the architecture clearly requires it.

### 4. Add LLM Review Summary Model

Add a model for article-level LLM review summary.

Suggested name:

```python
LLMReviewSummary
```

Suggested fields:

```python
overall_risk: str | None = None
summary: str | None = None
recommended_action: str | None = None
confidence: float | None = None
```

Possible `overall_risk` values:

```text
low
medium
high
unknown
```

If adding an enum would be consistent with the project style, add one. Otherwise keep it simple and validated.

Recommended constraints:

* `overall_risk`, if present, must be one of the allowed values
* `confidence`, if present, must be between `0.0` and `1.0`
* text fields should be optional but, if provided, should not be empty strings

### 5. Add LLM Review Result Model

Add a container for a future LLM review pass.

Suggested name:

```python
LLMReviewResult
```

Suggested fields:

```python
schema_version: str
provider: str | None = None
model: str | None = None
prompt_version: str | None = None
profile_name: str | None = None
findings: tuple[LLMReviewFinding, ...]
summary: LLMReviewSummary | None = None
metadata: dict[str, str] | None = None
```

Recommended schema version:

```text
llm-review-result.v1
```

Behavior:

* default `schema_version` should be stable
* `findings` should default to an empty tuple
* provider/model/prompt_version are metadata only
* no model execution occurs in this task

### 6. Add Conversion Boundary Documentation

Do not implement full merging yet.

However, document the intended future boundary:

```text
LLMReviewFinding
  ↓ future conversion
ReviewFinding-compatible output
  ↓ future merge
ReviewResult / reports / quality gate
```

Clarify:

* deterministic findings remain the current stable review output
* LLM findings are not yet included in normal review output
* future tasks may map LLM findings into `ReviewFinding`
* future tasks must decide whether LLM findings participate in quality gates
* future tasks must decide how suppression works for LLM findings
* future tasks must decide how confidence and rationale are displayed

### 7. Add Serialization Helpers If Needed

If the project has existing serialization utilities, add minimal helpers for LLM models only if appropriate.

Suggested functions:

```python
llm_review_finding_to_dict()
llm_review_summary_to_dict()
llm_review_result_to_dict()
```

Only add these if the existing project already uses explicit serialization helper functions.

Do not integrate these into the normal review JSON output yet.

### 8. Add Tests For LLM Models

Add a focused test file.

Suggested file:

```text
tests/test_llm_models.py
```

Tests should verify:

* valid `LLMReviewFinding` can be constructed
* empty message is rejected
* invalid severity is rejected
* confidence below `0.0` is rejected
* confidence above `1.0` is rejected
* valid optional line / column values are accepted
* invalid line / column values are rejected if the current project enforces location constraints
* valid `LLMReviewSummary` can be constructed
* invalid `overall_risk` is rejected
* `LLMReviewResult` defaults to schema version `llm-review-result.v1`
* `LLMReviewResult` defaults to empty findings
* serialization helper output is stable if helpers are added
* LLM model tests do not require network access or API keys

### 9. Update Architecture Documentation

Update:

```text
docs/ARCHITECTURE.md
```

Add a short section for the future LLM review layer.

Suggested section title:

```markdown
## Future LLM Review Layer
```

Explain:

* current review engine remains deterministic
* LLM review is planned as a separate optional semantic layer
* TASK-0034 only adds data models
* no provider integration exists yet
* no LLM output is included in normal review reports yet
* future LLM review should produce structured findings compatible with the review system

Suggested diagram:

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

### 10. Update Data Model Documentation

Update:

```text
docs/DATA_MODELS.md
```

Document the new LLM model concepts:

* `LLMReviewFinding`
* `LLMReviewSummary`
* `LLMReviewResult`
* schema version
* confidence
* rationale
* prompt version
* provider / model metadata

Clarify:

* these are future-facing models
* they are not part of the current `ReviewResult` JSON output
* this task does not change current review output schema

### 11. Update Rule System Documentation If Needed

Update:

```text
docs/RULES.md
```

Add a short note that LLM semantic findings are future-facing and distinct from deterministic rule execution.

Clarify:

* deterministic rule IDs remain stable and current
* profile-defined regex rule IDs remain dynamic
* future LLM finding rule IDs should be namespaced or clearly identified
* LLM findings are not currently executed

Keep this section short.

### 12. Update Project State

Update:

```text
PROJECT_STATE.md
```

Mention:

* TASK-0034 completed
* LLM review data models added
* no provider integration added
* no PydanticAI added
* no normal review output schema changed
* deterministic review behavior unchanged
* next recommended task is LLM review prototype or prompt/provider abstraction

### 13. Update Changelog

Update:

```text
CHANGELOG.md
```

Add a TASK-0034 entry describing:

* added LLM review data models
* added LLM review result schema version
* added tests
* documented future LLM review architecture
* no provider integration
* no runtime review behavior changes

## Acceptance Criteria

TASK-0034 is complete when:

* LLM review model module exists
* `LLMReviewFinding` or equivalent exists
* `LLMReviewSummary` or equivalent exists
* `LLMReviewResult` or equivalent exists
* LLM result schema version is stable
* confidence validation exists
* severity validation uses existing canonical severities
* tests cover valid and invalid LLM model data
* architecture docs describe future LLM review layer
* data model docs document LLM models
* docs clearly state no provider integration exists yet
* docs clearly state current review JSON output is unchanged
* `PROJECT_STATE.md` is updated
* `CHANGELOG.md` is updated
* all tests pass
* no LLM provider is called
* no PydanticAI is added
* no CLI LLM command or flag is added
* no review behavior changes are introduced

## Validation Commands

Run:

```bash
uv run pytest
```

Optional manual checks:

```bash
grep -R "LLMReviewFinding" src tests docs
grep -R "llm-review-result.v1" src tests docs
```

