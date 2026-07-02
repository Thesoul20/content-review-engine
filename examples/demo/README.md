# Unified End-to-End Demo

This directory is the main end-to-end demo entrypoint for the repository.

It shows the current project surface through one local replay flow:

- deterministic CLI review
- optional mock-LLM CLI review
- combined and report-index artifacts
- Python API workflow usage
- local MCP stdio usage

The default demo is fully local. It does not require a real API key, `.env`
loading, or network access.

## Setup

From the repository root:

```bash
uv sync --extra mcp
```

The MCP extra is included here because the unified demo also regenerates MCP
request and response snapshots.

## Replay The Demo

Regenerate the committed demo artifacts:

```bash
uv run python examples/demo/run_demo.py
```

Write the same artifact set to a different directory:

```bash
uv run python examples/demo/run_demo.py --output-root /tmp/content-review-demo
```

The replay command validates the demo profiles, runs CLI review commands, runs
the Python API facade directly, starts the local MCP stdio server, performs
initialize and tool calls through the MCP client SDK, and then writes one
artifact tree.

## Demo Layout

```text
examples/demo/
  README.md
  run_demo.py
  articles/
    technical-demo.md
    wechat-demo.md
  profiles/
    technical-demo.yaml
    wechat-demo.yaml
  artifacts/
    cli/
    api/
    mcp/
```

## Artifact Map

### `artifacts/cli/`

- `single-file/review.txt`: stdout from deterministic single-file review.
- `single-file/review.json`: canonical deterministic `ReviewResult`.
- `single-file/review.md`: deterministic Markdown report written by the CLI.
- `single-file/llm-result.json`: raw mock-LLM sidecar.
- `single-file/llm-report.md`: advisory LLM Markdown report.
- `single-file/combined.json`: single-file combined envelope in JSON.
- `single-file/combined.md`: single-file combined Markdown report.
- `single-file/report-index.md`: navigation-oriented report index.
- `batch/*`: the same artifact families for `content-review batch`.

### `artifacts/api/`

- `single-file.workflow.json`: serialized `ReviewFileWorkflowResult`.
- `single-file.review.json`: deterministic API output file.
- `single-file.llm.json`: raw LLM sidecar written through the API facade.
- `single-file.combined.json`: combined API artifact.
- `batch.workflow.json`: serialized `ReviewBatchWorkflowResult`.
- `batch.review.json`, `batch.llm.json`, `batch.combined.json`: batch
  artifact outputs written through the same API facade.

### `artifacts/mcp/`

- `initialize.json`: MCP initialize handshake summary.
- `tools.json`: tool-name snapshot from `list_tools`.
- `single-file.request.json`: request payload passed to `content_review_file`.
- `single-file.response.json`: structured JSON response returned by the MCP tool.
- `batch.request.json`: request payload passed to `content_review_batch`.
- `batch.response.json`: structured JSON response returned by the MCP tool.

## Walkthrough

### 1. Review The Demo Inputs

- `articles/wechat-demo.md` is the public-facing article example.
- `articles/technical-demo.md` is the technical-post example.
- `profiles/wechat-demo.yaml` and `profiles/technical-demo.yaml` are stable
  demo profiles built from current deterministic rules plus `regex_rules`.

### 2. Inspect The CLI Artifacts

Start with:

- `artifacts/cli/single-file/review.txt`
- `artifacts/cli/single-file/review.json`
- `artifacts/cli/single-file/review.md`

Then inspect:

- `artifacts/cli/single-file/llm-result.json`
- `artifacts/cli/single-file/combined.json`
- `artifacts/cli/single-file/combined.md`
- `artifacts/cli/single-file/report-index.md`

Repeat the same pattern under `artifacts/cli/batch/`.

### 3. Inspect The Python API Artifacts

Read:

- `artifacts/api/single-file.workflow.json`
- `artifacts/api/batch.workflow.json`

These files show the stable wrapper models returned by
`content_review_engine.api.review_file(...)` and
`content_review_engine.api.review_batch(...)`, including deterministic gate
metadata, optional LLM metadata, combined results, and artifact paths.

### 4. Inspect The MCP Artifacts

Read:

- `artifacts/mcp/initialize.json`
- `artifacts/mcp/tools.json`
- `artifacts/mcp/single-file.request.json`
- `artifacts/mcp/single-file.response.json`
- `artifacts/mcp/batch.request.json`
- `artifacts/mcp/batch.response.json`

These files show the MCP transport boundary. The requests are flat JSON
arguments, and the responses are structured serialization of the same Python
API workflow models used by the in-process facade.

## Boundary Notes

- The demo uses only the current local adapters and the current core package.
- Deterministic output remains the canonical review layer.
- The mock LLM path is explicit opt-in and remains advisory.
- Combined output stays separate from deterministic output.
- The MCP server remains a thin local wrapper over the Python API facade.
- The demo does not claim legal, medical, advertising, regulatory, or
  platform compliance.
