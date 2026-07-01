# MCP Server Examples

This directory contains reference-only local MCP client configuration and tool
call examples for the `content-review-engine` MCP server.

## Install MCP Support

From the repository root:

```bash
uv sync --extra mcp
```

The base package can be used without MCP. Install the extra only when you
want the MCP entrypoint.

## Recommended Startup

Default local MCP transport:

```bash
uv run content-review-mcp
```

Equivalent module entrypoint:

```bash
uv run python -m content_review_engine.mcp_server
```

Non-blocking startup verification:

```bash
uv run content-review-mcp --help
uv run python -m content_review_engine.mcp_server --help
```

The default and recommended transport is `stdio`.

Automated validation note:

- the repository test suite also runs one stdio subprocess smoke through the
  MCP Python client SDK so protocol initialize, tool discovery, and one real
  tool call are exercised separately from direct in-process tests

Transport boundary:

- prefer `stdio` for Codex and Claude Desktop
- this repo documents a local tool subprocess, not a remote REST API
- `sse` and `streamable-http` are SDK-exposed transports, not the recommended
  release path for this task

## Client Config Files

- `codex-config.example.json`
- `claude-desktop-config.example.json`

Both examples assume the client will spawn:

```bash
uv run --directory /ABSOLUTE/PATH/TO/content-review-engine content-review-mcp
```

Replace `/ABSOLUTE/PATH/TO/content-review-engine` with the absolute path to
this repository on your machine.

Rules for both JSON config examples:

- valid JSON only
- no real secrets
- no developer-machine paths
- stdio subprocess launch only

## Tool Call Examples

JSON tool call payloads live in `tool-call-examples/`:

- `content-review-file-deterministic.json`
- `content-review-batch-deterministic.json`
- `content-review-file-llm-mock.json`
- `content-review-file-artifacts.json`

These examples are valid JSON and intentionally avoid raw API keys.

## Deterministic Example

Tool: `content_review_file`

```json
{
  "markdown_path": "tests/fixtures/markdown/forbidden_terms_article.md",
  "profile_path": "tests/fixtures/profiles/default.yml",
  "fail_on": "warning",
  "include_combined_result": true
}
```

Expected boundary:

- deterministic review only
- `llm_status` stays `not_run`
- `combined_output_path` is not required

## Optional Mock LLM Example

Tool: `content_review_file`

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

Expected boundary:

- default tests can use `mock`
- no real external LLM API is required
- `llm_fail_on` still requires explicit `enable_llm`

## Batch Example

Tool: `content_review_batch`

```json
{
  "input_dir": "tests/fixtures/batch/articles",
  "profile_path": "tests/fixtures/batch/profile.yml",
  "pattern": "*.md",
  "recursive": false,
  "include_combined_result": true
}
```

Batch reminder:

- batch review is non-recursive by default
- set `"recursive": true` only when you want nested files

## Manual Smoke Checklist

Use [`manual-smoke-checklist.md`](./manual-smoke-checklist.md) for a manual
client-validation walkthrough.

## Boundaries

- the MCP server calls the Python API directly
- it does not shell out to `content-review`
- it does not auto-load `.env`
- it does not accept raw API keys in tool input
- real LLM providers send content to the configured provider
- `combined_output_path` does not auto-enable LLM
- `llm_fail_on` does not auto-enable LLM
