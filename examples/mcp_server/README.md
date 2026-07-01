# MCP Server Examples

This directory contains reference-only MCP client configuration examples for
the local `content-review-engine` MCP server.

## Start The Server

Run from the repository root:

```bash
uv run content-review-mcp
```

The default transport is `stdio`, which is the recommended transport for local
agent clients such as Codex and Claude Code / Claude Desktop.

## Example Files

- `codex-config.example.json`
- `claude-desktop-config.example.json`

Both examples assume the client will spawn:

```bash
uv run --directory /ABSOLUTE/PATH/TO/content-review-engine content-review-mcp
```

Replace `/ABSOLUTE/PATH/TO/content-review-engine` with the real repository
path on your machine.

## Deterministic-Only Example

Tool: `content_review_file`

```json
{
  "markdown_path": "tests/fixtures/markdown/forbidden_terms_article.md",
  "profile_path": "tests/fixtures/profiles/default.yml",
  "fail_on": "warning",
  "include_combined_result": true
}
```

## Optional LLM Example

Tool: `content_review_batch`

```json
{
  "input_dir": "tests/fixtures/batch/articles",
  "profile_path": "tests/fixtures/batch/profile.yml",
  "recursive": true,
  "enable_llm": true,
  "llm_provider_config": {
    "provider": "mock"
  },
  "llm_output_path": "/tmp/batch.llm.json",
  "combined_output_path": "/tmp/batch.combined.json",
  "combined_output_format": "json"
}
```

## Boundaries

- the MCP server calls the Python API directly
- it does not shell out to `content-review`
- it does not auto-load `.env`
- it does not accept raw API keys in tool input
