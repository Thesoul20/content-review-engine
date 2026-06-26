# TASK-0035: Add LLM Provider Interface And Mock Reviewer

## Status

Planned

## Goal

Add an LLM provider interface and a deterministic mock LLM reviewer for the future semantic review layer.

TASK-0034 added foundational LLM review data models:

* `LLMReviewFinding`
* `LLMReviewSummary`
* `LLMReviewResult`

TASK-0035 should define how an LLM reviewer will be called in the future, without integrating a real model provider yet.

This task should add:

* an LLM provider protocol or interface
* a review request model if needed
* a deterministic mock reviewer
* error types for LLM review failures
* tests for the mock review flow
* documentation for the future provider boundary

This task must not call any real LLM provider.

## Background

The project direction is hybrid review:

```text
Deterministic rules + future LLM semantic review
```

The deterministic review engine already supports:

* built-in rules
* `regex_rules`
* profile templates
* demo project
* structured profile validation errors
* Markdown / JSON / text output
* batch review
* quality gates
* suppression

TASK-0034 added LLM review data models but did not define execution.

The next step is to define a stable execution boundary:

```text
Markdown content
  ↓
LLMReviewRequest
  ↓
LLMReviewer / LLMProvider interface
  ↓
LLMReviewResult
```

This allows future tasks to plug in PydanticAI, OpenAI, Anthropic, or a local model without changing the rest of the project.

## Scope

This task may modify or add:

* `src/content_review_engine/llm/`
* LLM provider interface module
* LLM mock reviewer module
* LLM error module
* LLM request model
* LLM tests
* architecture documentation
* data model documentation
* `PROJECT_STATE.md`
* `CHANGELOG.md`

Likely files:

```text
src/content_review_engine/llm/models.py
src/content_review_engine/llm/serialization.py
src/content_review_engine/llm/__init__.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
tests/test_llm_models.py
PROJECT_STATE.md
CHANGELOG.md
```

Possible new files:

```text
src/content_review_engine/llm/provider.py
src/content_review_engine/llm/mock.py
src/content_review_engine/llm/errors.py
tests/test_llm_provider.py
tests/test_llm_mock_reviewer.py
```

Exact paths should follow the repository style.

## Non-goals

This task must not:

* add PydanticAI
* call OpenAI, Anthropic, Gemini, local models, or any real provider
* add API keys
* add environment variable configuration
* add prompt templates for production use
* add CLI flags or CLI commands for LLM review
* merge LLM findings into deterministic `ReviewResult`
* add LLM findings to Markdown reports
* add LLM findings to current review JSON output
* change deterministic rule behavior
* change regex rule behavior
* change suppression behavior
* change quality gate semantics
* change Markdown report structure
* change current JSON review output schema
* add API, MCP, or GUI behavior
* introduce compliance guarantees

## Required Work

### 1. Inspect Existing LLM Models

Before making changes, inspect:

```text
src/content_review_engine/llm/models.py
src/content_review_engine/llm/serialization.py
src/content_review_engine/llm/__init__.py
tests/test_llm_models.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
```

Keep the new provider boundary consistent with the existing LLM model style.

### 2. Add LLM Review Request Model

Add a request model for future LLM review calls.

Suggested name:

```python
LLMReviewRequest
```

Suggested fields:

```python
content: str
profile_name: str | None = None
content_path: str | None = None
review_goal: str | None = None
metadata: dict[str, str] | None = None
```

Recommended validation:

* `content` must not be empty
* optional string fields should not allow empty strings if the project already enforces that style
* `metadata` should be simple string-to-string metadata only

This request model should not include API keys or provider-specific options.

### 3. Add LLM Provider Interface

Add an interface or protocol for LLM review execution.

Suggested name:

```python
LLMReviewer
```

or:

```python
LLMReviewProvider
```

Suggested shape:

```python
class LLMReviewer(Protocol):
    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        ...
```

Use the project’s preferred typing style.

Requirements:

* interface should return `LLMReviewResult`
* interface should not depend on a concrete provider
* interface should not perform network access
* interface should be easy to mock in tests
* interface should not require async unless the project already uses async patterns

Recommended initial choice:

```text
Synchronous interface
```

Reason:

The current CLI and review pipeline appear synchronous. Async provider support can be added later if needed.

### 4. Add LLM Error Types

Add minimal error types for future LLM review failures.

Suggested file:

```text
src/content_review_engine/llm/errors.py
```

Suggested errors:

```python
class LLMReviewError(Exception):
    pass

class LLMProviderError(LLMReviewError):
    pass

class LLMResponseValidationError(LLMReviewError):
    pass
```

Purpose:

* `LLMReviewError`: base error for the LLM layer
* `LLMProviderError`: provider call failure
* `LLMResponseValidationError`: provider returned malformed structured output

Do not wire these into CLI behavior yet.

### 5. Add Deterministic Mock Reviewer

Add a mock reviewer for tests and future development.

Suggested file:

```text
src/content_review_engine/llm/mock.py
```

Suggested class:

```python
class MockLLMReviewer:
    def __init__(self, result: LLMReviewResult | None = None):
        ...

    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        ...
```

Behavior:

* deterministic
* no network access
* no API keys
* returns a configured `LLMReviewResult`
* if no result is configured, returns an empty `LLMReviewResult`
* should preserve request metadata where appropriate, such as profile name
* should be useful in future integration tests

Optional helper:

```python
def create_empty_llm_review_result(...) -> LLMReviewResult:
    ...
```

Do not add keyword-matching pseudo-AI behavior unless needed for tests. Keep mock behavior predictable.

### 6. Export Public LLM Interfaces

Update:

```text
src/content_review_engine/llm/__init__.py
```

Export the new public LLM types.

Expected exports may include:

```python
LLMReviewRequest
LLMReviewer
LLMReviewError
LLMProviderError
LLMResponseValidationError
MockLLMReviewer
```

Also keep existing exports:

```python
LLMReviewFinding
LLMReviewSummary
LLMReviewResult
```

### 7. Add Tests For LLM Provider Interface

Add tests for request model and provider interface.

Suggested file:

```text
tests/test_llm_provider.py
```

Tests should cover:

* valid `LLMReviewRequest`
* empty content is rejected
* optional metadata is accepted
* mock reviewer implements the interface
* mock reviewer returns configured result
* mock reviewer returns empty result by default
* mock reviewer result uses schema version `llm-review-result.v1`
* mock reviewer does not require network access
* error classes can be raised and caught through `LLMReviewError`

### 8. Add Tests For Serialization With Mock Result

If serialization helpers already exist, add or extend tests to ensure a mock result can be serialized.

Tests should verify:

* `llm_review_result_to_dict()` works with mock result
* `llm_review_result_to_json()` works with mock result
* provider/model/prompt metadata remains stable if present

Do not integrate LLM serialization into current review JSON output.

### 9. Update Architecture Documentation

Update:

```text
docs/ARCHITECTURE.md
```

Add or extend the future LLM review section.

Document:

* `LLMReviewRequest`
* `LLMReviewer` or provider interface
* deterministic `MockLLMReviewer`
* no real provider integration yet
* no CLI integration yet
* no report integration yet
* future PydanticAI provider should implement the same interface

Suggested diagram:

```text
Markdown Content
  ↓
LLMReviewRequest
  ↓
LLMReviewer interface
  ↓
MockLLMReviewer now / PydanticAI provider later
  ↓
LLMReviewResult
  ↓
Future conversion and merge layer
```

### 10. Update Data Model Documentation

Update:

```text
docs/DATA_MODELS.md
```

Document:

* `LLMReviewRequest`
* provider interface boundary
* mock reviewer purpose
* LLM error types if appropriate

Clarify:

* request/result models are future-facing
* they are not part of current deterministic review output
* current `ReviewResult` JSON schema remains unchanged

### 11. Update Project State

Update:

```text
PROJECT_STATE.md
```

Mention:

* TASK-0035 completed
* LLM provider interface added
* deterministic mock reviewer added
* no real provider integration
* no PydanticAI
* no CLI LLM command
* no report integration
* no current review JSON output change

### 12. Update Changelog

Update:

```text
CHANGELOG.md
```

Add a TASK-0035 entry describing:

* added LLM review request model
* added provider interface
* added mock reviewer
* added LLM error types
* added tests
* updated docs
* no provider integration
* no runtime review behavior changes

## Acceptance Criteria

TASK-0035 is complete when:

* `LLMReviewRequest` or equivalent exists
* `LLMReviewer` / provider interface exists
* LLM error types exist
* deterministic `MockLLMReviewer` exists
* mock reviewer returns `LLMReviewResult`
* request validation is tested
* mock reviewer behavior is tested
* LLM serialization with mock result is tested if applicable
* architecture docs explain the provider boundary
* data model docs explain the new request/provider/mock concepts
* `PROJECT_STATE.md` is updated
* `CHANGELOG.md` is updated
* all tests pass
* no real provider integration is added
* no PydanticAI is added
* no CLI LLM behavior is added
* no current review JSON output changes
* no runtime deterministic review behavior changes

## Validation Commands

Run:

```bash
uv run pytest
```

Optional manual checks:

```bash
grep -R "LLMReviewRequest" src tests docs
grep -R "MockLLMReviewer" src tests docs
grep -R "LLMReviewer" src tests docs
```

