# Python API

This project now exposes a stable Python facade for review workflows:

- `review_file(...)`
- `review_batch(...)`

Import from:

```python
from content_review_engine.api import review_batch, review_file
```

The local MCP server wrapper in `content_review_engine.mcp_server` calls these
same entrypoints and does not bypass the API facade.

## Scope

The Python API is a programmatic adapter over the same core workflow used by
the CLI.

- deterministic-only by default
- returns structured result objects
- can optionally write deterministic output, raw LLM output, and combined output
- can optionally run LLM review when `enable_llm=True`
- does not auto-enable LLM
- combined output remains explicit opt-in
- `llm_fail_on` does not auto-enable LLM
- does not read `.env` automatically
- does not accept raw API keys
- does not shell out to the CLI

Boundary rules:

- `enable_llm=False` means no LLM provider is created or called
- LLM findings do not enter deterministic `ReviewResult.findings`
- LLM findings do not change deterministic severity counts or rule counts
- deterministic quality gate and explicit LLM quality gate remain separate

## Main Entrypoints

### `review_file(...)`

Use for one Markdown file and one profile.

```python
from content_review_engine.api import review_file

result = review_file(
    "tests/fixtures/markdown/clean_article.md",
    "tests/fixtures/profiles/default.yml",
)

print(result.review_result.summary.finding_count)
```

### `review_batch(...)`

Use for one directory and one profile.

```python
from content_review_engine.api import review_batch

result = review_batch(
    "tests/fixtures/batch/articles",
    "tests/fixtures/batch/profile.yml",
    recursive=True,
)

print(result.batch_result.summary.file_count)
```

## Result Models

Single-file:

- `ReviewFileWorkflowResult`
- `review_result: ReviewResult`
- `llm_result: LLMReviewResult | None`
- `combined_result: SingleFileCombinedReviewResult | None`
- `deterministic_quality_gate: DeterministicQualityGateResult`
- `llm_quality_gate: LLMQualityGateResult`
- `artifacts: ReviewArtifactPaths`

Batch:

- `ReviewBatchWorkflowResult`
- `batch_result: BatchReviewResult`
- `llm_sidecar_result: LLMSidecarResult | None`
- `combined_result: BatchCombinedReviewResult | None`
- `deterministic_quality_gate: DeterministicQualityGateResult`
- `llm_quality_gate: LLMQualityGateResult`
- `artifacts: ReviewArtifactPaths`

## Deterministic-Only Usage

```python
from content_review_engine.api import review_file

result = review_file(
    "article.md",
    "profile.yml",
    fail_on="warning",
    include_combined_result=True,
)

if result.deterministic_quality_gate.failed:
    print("deterministic gate failed")
```

## Optional LLM Usage

Pass either:

- `llm_provider_config=LLMProviderConfig(...)`
- `llm_config_path="path/to/llm-provider.yml"`

Current API contract:

- no raw API key argument
- use `api_key_env` inside `LLMProviderConfig` or YAML config
- `pydanticai` still requires model configuration

Example:

```python
from content_review_engine.api import review_file
from content_review_engine.llm import LLMProviderConfig

result = review_file(
    "article.md",
    "profile.yml",
    enable_llm=True,
    llm_provider_config=LLMProviderConfig(provider="mock"),
    llm_fail_on="warning",
    include_combined_result=True,
)

print(result.llm_result)
print(result.llm_quality_gate.failed)
```

## Output Writing

The API can return structured objects without writing files, or it can also
write artifacts.

Supported artifact families:

- deterministic output via `output_path`
- raw LLM sidecar via `llm_output_path`
- combined output via `combined_output_path`

Example:

```python
from content_review_engine.api import review_file
from content_review_engine.llm import LLMProviderConfig

result = review_file(
    "article.md",
    "profile.yml",
    output_format="json",
    output_path="artifacts/review.json",
    enable_llm=True,
    llm_provider_config=LLMProviderConfig(provider="mock"),
    llm_output_path="artifacts/review.llm.json",
    combined_output_path="artifacts/review.combined.json",
    combined_output_format="json",
)

print(result.artifacts.output_path)
```

Compatibility rules:

- `combined_output_path` does not auto-enable LLM
- when LLM is disabled, combined output records `not_run`
- raw sidecar schema is unchanged
- combined output schema is unchanged

## CLI Reuse Boundary

The CLI and Python API reuse the same workflow helpers for:

- deterministic review orchestration
- optional LLM execution
- raw sidecar writing
- combined envelope building
- deterministic gate evaluation
- explicit LLM gate evaluation

The CLI keeps its existing argument parsing, user-facing command contract, and
exit-code behavior.

## Examples

- `examples/python_api_usage/README.md`
- `examples/python_api_usage/single_file_review.py`
- `examples/python_api_usage/batch_review.py`
