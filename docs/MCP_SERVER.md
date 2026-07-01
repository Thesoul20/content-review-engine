# MCP Server

This project includes a local MCP server wrapper over the stable Python API
facade.

Import and execution boundary:

- MCP tools call `content_review_engine.api.review_file(...)`
- MCP tools call `content_review_engine.api.review_batch(...)`
- MCP does not shell out to the CLI
- MCP does not reimplement `workflows.py`
- MCP remains a thin local adapter over the Python API facade

## Installation

Base CLI usage does not require MCP runtime dependencies.

Install MCP support only when you want the MCP entrypoint:

```bash
uv sync --extra mcp
```

Equivalent package install:

```bash
pip install "content-review-engine[mcp]"
```

If you run `content-review-mcp` without the optional MCP dependency, the
entrypoint fails with an explicit install hint.

## Startup Entrypoints

Supported local entrypoints:

```bash
uv run content-review-mcp
uv run python -m content_review_engine.mcp_server
```

Safe non-blocking verification commands:

```bash
uv run content-review-mcp --help
uv run python -m content_review_engine.mcp_server --help
```

Current guarantees:

- importing `content_review_engine.mcp_server` does not require a real API key
- importing `content_review_engine.mcp_server` does not auto-read `.env`
- `--help` returns before the stdio server starts
- normal server startup still blocks as expected because MCP stdio servers are
  long-lived subprocesses
- the automated test suite also includes a stdio subprocess smoke that
  performs MCP initialize, tool discovery, and a real tool call over the
  JSON-RPC transport without depending on Codex or Claude Desktop

## Transport Boundary

Default and recommended transport:

```bash
uv run content-review-mcp --transport stdio
```

Current recommendation:

- prefer `stdio` for local MCP clients
- let the MCP client manage the subprocess lifecycle
- treat this server as a local tool entrypoint, not a remote deployed service

Non-stdio transports:

- `sse`
- `streamable-http`

Current boundary:

- these transports are exposed only because the MCP SDK supports them
- they are not the recommended path for this project at the current stage
- they are not documented here as REST API, remote deployment, or public
  service capabilities
- this task does not add auth, reverse proxy, multi-user hosting, or remote
  operations guidance

## Tool Names

The server exposes two tools:

- `content_review_file`
- `content_review_batch`

## Tool Input Schema

Both tools use flat JSON-compatible arguments aligned with the Python API
workflow facade rather than nested raw CLI arguments.

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

Batch discovery boundary:

- `recursive` defaults to `false`
- batch review is non-recursive by default

Security and compatibility rules:

- deterministic-only by default
- `enable_llm=False` means no LLM provider is created or called
- `combined_output_path` does not auto-enable LLM
- `llm_fail_on` does not auto-enable LLM
- tool input does not accept raw API keys
- the MCP server does not auto-read `.env`
- a real LLM provider will send article content to that provider

Exact boundary statements:

- combined_output_path does not auto-enable LLM
- llm_fail_on does not auto-enable LLM

## Tool Output Schema

`content_review_file` returns JSON-compatible serialization of
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

`content_review_batch` returns JSON-compatible serialization of
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

## Example Tool Calls

Reference JSON examples live in:

- [`examples/mcp_server/tool-call-examples/content-review-file-deterministic.json`](../examples/mcp_server/tool-call-examples/content-review-file-deterministic.json)
- [`examples/mcp_server/tool-call-examples/content-review-batch-deterministic.json`](../examples/mcp_server/tool-call-examples/content-review-batch-deterministic.json)
- [`examples/mcp_server/tool-call-examples/content-review-file-llm-mock.json`](../examples/mcp_server/tool-call-examples/content-review-file-llm-mock.json)
- [`examples/mcp_server/tool-call-examples/content-review-file-artifacts.json`](../examples/mcp_server/tool-call-examples/content-review-file-artifacts.json)

Deterministic-only example:

```json
{
  "markdown_path": "tests/fixtures/markdown/forbidden_terms_article.md",
  "profile_path": "tests/fixtures/profiles/default.yml",
  "fail_on": "warning",
  "include_combined_result": true
}
```

Optional mock LLM example:

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
- combined output remains explicit opt-in
- LLM findings remain advisory unless you explicitly set `llm_fail_on`

## Artifact Paths

All MCP tools can optionally write the same artifact families as the Python
API:

- `output_path`: deterministic output
- `llm_output_path`: raw LLM sidecar output
- `combined_output_path`: combined output

Boundary reminders:

- `combined_output_path` can be used without `enable_llm`
- when LLM is disabled, combined output records `not_run`
- `combined_output_format` supports `json` and `markdown`
- `combined_output_path` does not auto-enable LLM
- `llm_fail_on` does not auto-enable LLM

## Client Configuration Examples

Reference files:

- [`examples/mcp_server/codex-config.example.json`](../examples/mcp_server/codex-config.example.json)
- [`examples/mcp_server/claude-desktop-config.example.json`](../examples/mcp_server/claude-desktop-config.example.json)
- [`examples/mcp_server/README.md`](../examples/mcp_server/README.md)

Config example rules:

- examples are valid JSON
- examples use placeholder absolute paths only
- examples do not include real secrets
- examples use `uv run --directory /ABSOLUTE/PATH/TO/content-review-engine`
- examples default to the `content-review-mcp` console script over stdio

## Manual Smoke Checklist

Local manual smoke guidance lives in:

- [`examples/mcp_server/manual-smoke-checklist.md`](../examples/mcp_server/manual-smoke-checklist.md)

Automated coverage note:

- repository tests now also include a stdio subprocess smoke over the MCP
  Python client SDK, so startup, handshake, tool listing, and one real tool
  invocation are validated separately from direct in-process server calls

The checklist covers:

- dependency installation
- entrypoint verification
- Codex and Claude Desktop config validation
- deterministic tool-call validation
- optional mock LLM validation
- artifact writing validation
- error-sanitization checks

## Troubleshooting

`content-review-mcp: command not found`

- run `uv sync --extra mcp`
- if using a client config, make sure it launches `uv run --directory /ABSOLUTE/PATH/TO/content-review-engine content-review-mcp`

`ModuleNotFoundError: No module named 'mcp'`

- install the optional MCP dependency with `uv sync --extra mcp`
- base CLI installs do not include the MCP runtime by default

The client starts but no tools appear

- verify the client is using stdio
- verify the working directory or `--directory` path points at this repo
- verify the client command is `content-review-mcp` or
  `python -m content_review_engine.mcp_server`

Batch review misses nested files

- batch MCP calls are non-recursive by default
- set `"recursive": true` when you want nested Markdown files included

Real-provider LLM review fails

- verify `enable_llm` is `true`
- verify the provider config uses `api_key_env`, not a raw API key
- verify the environment variable is set in the client process environment
- remember that the project does not auto-read `.env`
- remember that real LLM review sends content to the configured provider

`combined_output_path` or `llm_fail_on` did not start LLM review

- this is expected
- `combined_output_path` does not auto-enable LLM
- `llm_fail_on` does not auto-enable LLM
- set `enable_llm=true` explicitly when you want the LLM path

## Release Readiness Notes

Current TASK-0091 release-readiness position:

- console script and module entrypoints are both supported
- entrypoint help paths are safe to test without blocking on stdio
- default tests do not require a real MCP client
- default tests do not require a real external LLM API
- stdio is the default recommended transport
- remote service packaging is not part of the current product scope
