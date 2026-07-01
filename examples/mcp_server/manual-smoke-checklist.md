# MCP Manual Smoke Checklist

Use this checklist for local MCP client validation without depending on a real
external LLM API.

## 1. Prepare The Repo

```bash
uv sync --extra mcp
```

Expected result:

- the MCP optional dependency is installed
- the base CLI remains unchanged

## 2. Verify Entrypoints

Run:

```bash
uv run content-review-mcp --help
uv run python -m content_review_engine.mcp_server --help
```

Check:

- both commands exit successfully
- help text shows `--transport`
- neither command requires a real API key
- neither command blocks on the stdio server in help mode

## 3. Validate Client Config JSON

Check these files:

- `codex-config.example.json`
- `claude-desktop-config.example.json`

Confirm:

- JSON parses successfully
- `/ABSOLUTE/PATH/TO/content-review-engine` is still a placeholder
- no real secret values are present

## 4. Configure A Local Client

Use one of the example config files and replace the placeholder repository
path with your local absolute path.

Spawn command:

```bash
uv run --directory /ABSOLUTE/PATH/TO/content-review-engine content-review-mcp
```

Confirm:

- transport is stdio
- the client shows `content_review_file`
- the client shows `content_review_batch`

## 5. Run A Deterministic File Review

Tool:

- `content_review_file`

Payload:

```json
{
  "markdown_path": "tests/fixtures/markdown/forbidden_terms_article.md",
  "profile_path": "tests/fixtures/profiles/default.yml",
  "fail_on": "warning",
  "include_combined_result": true
}
```

Confirm:

- deterministic findings are returned
- `llm_status` is `not_run`
- deterministic counts match local expectations

## 6. Run A Deterministic Batch Review

Tool:

- `content_review_batch`

Payload:

```json
{
  "input_dir": "tests/fixtures/batch/articles",
  "profile_path": "tests/fixtures/batch/profile.yml",
  "pattern": "*.md",
  "recursive": false,
  "include_combined_result": true
}
```

Confirm:

- only top-level files are included
- nested files are skipped when `recursive` is `false`

## 7. Run Optional Mock LLM Review

Tool:

- `content_review_file`

Payload:

```json
{
  "markdown_path": "tests/fixtures/markdown/clean_article.md",
  "profile_path": "tests/fixtures/profiles/default.yml",
  "enable_llm": true,
  "llm_provider_config": {
    "provider": "mock"
  },
  "include_combined_result": true
}
```

Confirm:

- the review succeeds without a real provider
- `llm_status` is `succeeded`
- deterministic findings remain unchanged

## 8. Validate Artifact Writing

Use a payload that writes:

- `output_path`
- `combined_output_path`

Confirm:

- files are written to the requested paths
- `combined_output_path` alone does not enable LLM

## 9. Validate Error Sanitization

Trigger one controlled error such as an invalid path or invalid config.

Confirm:

- the MCP client receives a readable error
- no raw secret appears in the surfaced error message

## 10. Real-Provider Boundary Check

Before any real-provider run, confirm:

- the project does not auto-read `.env`
- tool input still does not accept a raw API key
- provider config must use `api_key_env`
- real LLM review sends content to the configured provider

## 11. Transport Boundary Check

Confirm the final local client setup still follows these rules:

- stdio is the default recommended transport
- this setup is a local subprocess integration
- `sse` and `streamable-http` are not being treated as REST API or remote
  deployment guidance
