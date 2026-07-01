# MCP Server

This project now includes an MCP server wrapper over the stable Python API
facade.

Import boundary:

- MCP tools call `content_review_engine.api.review_file(...)`
- MCP tools call `content_review_engine.api.review_batch(...)`
- MCP does not shell out to the CLI
- MCP does not reimplement `workflows.py`

## Start The Server

Default stdio transport:

```bash
uv run content-review-mcp
```

Explicit transport selection:

```bash
uv run content-review-mcp --transport stdio
uv run content-review-mcp --transport sse
uv run content-review-mcp --transport streamable-http
```

Current recommendation:

- prefer `stdio`
- use MCP clients to manage the subprocess
- do not pass raw API keys through tool input

## Tool Names

The server exposes two tools:

- `content_review_file`
- `content_review_batch`

## Tool Input Schema

Both tools use a flat JSON-compatible argument object instead of nested raw CLI
arguments.

Shared fields:

- deterministic paths: `markdown_path` or `input_dir`, plus `profile_path`
- deterministic output controls: `output_format`, `output_path`, `fail_on`
- optional LLM controls: `enable_llm`, `llm_fail_on`
- optional raw LLM artifact path: `llm_output_path`
- optional combined artifact controls:
  `combined_output_path`, `combined_output_format`,
  `include_combined_result`
- optional provider configuration:
  `llm_provider_config`, `llm_config_path`, `llm_provider`, `llm_model`,
  `llm_api_key_env`, `llm_base_url`, `llm_timeout_seconds`,
  `llm_retry_attempts`, `llm_retry_backoff_seconds`,
  `llm_min_request_interval_seconds`

Batch-only fields:

- `pattern`
- `recursive`

Security and compatibility rules:

- deterministic-only by default
- `enable_llm=False` means no LLM provider is created or called
- `combined_output_path` does not auto-enable LLM
- `llm_fail_on` does not auto-enable LLM
- tool input does not accept raw API keys
- the MCP server does not auto-read `.env`

Exact boundary statements:

- combined_output_path does not auto-enable LLM
- llm_fail_on does not auto-enable LLM

## Tool Output Schema

`content_review_file` returns the JSON serialization of
`ReviewFileWorkflowResult`.

Top-level fields:

- `options`
- `review_result`
- `output_text`
- `deterministic_quality_gate`
- `llm_result`
- `llm_status`
- `llm_error`
- `llm_quality_gate`
- `combined_result`
- `artifacts`

`content_review_batch` returns the JSON serialization of
`ReviewBatchWorkflowResult`.

Top-level fields:

- `options`
- `batch_result`
- `output_text`
- `deterministic_quality_gate`
- `llm_sidecar_result`
- `llm_quality_gate`
- `combined_result`
- `artifacts`

Compatibility rules:

- deterministic output still uses canonical `ReviewResult` /
  `BatchReviewResult`
- raw LLM output still uses canonical `LLMReviewResult` /
  `LLMSidecarResult`
- combined output still uses canonical combined-envelope models
- LLM findings do not enter deterministic findings, counts, or deterministic
  quality-gate evaluation

## Deterministic-Only Usage

Example MCP tool call:

```json
{
  "markdown_path": "tests/fixtures/markdown/forbidden_terms_article.md",
  "profile_path": "tests/fixtures/profiles/default.yml",
  "fail_on": "warning",
  "include_combined_result": true
}
```

Expected behavior:

- only deterministic review runs
- `llm_status` is `not_run`
- `combined_result.llm_status` is `not_run` when combined output is included

## Optional LLM Usage

Example MCP tool call:

```json
{
  "markdown_path": "tests/fixtures/markdown/clean_article.md",
  "profile_path": "tests/fixtures/profiles/default.yml",
  "enable_llm": true,
  "llm_provider_config": {
    "provider": "mock"
  },
  "llm_fail_on": "warning",
  "include_combined_result": true
}
```

Current rules:

- use `llm_provider_config.api_key_env` or `llm_api_key_env` for secret
  references when a real provider needs a key
- do not send raw API keys through MCP
- default tests should use `mock`
- LLM findings remain advisory unless you explicitly set `llm_fail_on`

## Artifact Paths

All MCP tools can optionally write the same artifact families as the Python
API:

- `output_path`: deterministic output
- `llm_output_path`: raw LLM sidecar output
- `combined_output_path`: combined output

Combined-output reminder:

- `combined_output_path` can be used without `enable_llm`
- when LLM is disabled, combined output records `not_run`
- `combined_output_format` supports `json` and `markdown`

## Error Handling

Tool failures are returned as MCP tool errors.

Current guarantees:

- error messages are sanitized before being surfaced by the MCP layer
- tool input does not carry raw secrets
- the wrapper does not inject or print `.env` values

## Client Configuration Examples

Reference files:

- [`examples/mcp_server/README.md`](../examples/mcp_server/README.md)
- [`examples/mcp_server/codex-config.example.json`](../examples/mcp_server/codex-config.example.json)
- [`examples/mcp_server/claude-desktop-config.example.json`](../examples/mcp_server/claude-desktop-config.example.json)
