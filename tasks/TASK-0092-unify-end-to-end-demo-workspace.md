# TASK-0092: Unify End-to-End Demo Workspace

## Status

Completed

## Goal

Turn the existing example materials into one unified demo workspace that can
show the current project surface end to end from a single entrypoint.

The unified demo should cover:

- deterministic CLI review
- optional mock-LLM CLI review
- combined and report-index artifacts
- Python API workflow usage
- local MCP stdio usage
- committed demo artifacts
- one replay script that regenerates the artifacts

The default demo must stay local-first and must not require real API keys or
network access.

## Background

The repository already includes:

- a deterministic CLI demo under `examples/demo/`
- Python API examples under `examples/python_api_usage/`
- MCP examples under `examples/mcp_server/`
- committed LLM artifact examples under `examples/llm_review_artifacts/`

Those materials are useful, but they are split across several directories and
do not provide one obvious “full project demo” path.

This task adds a single demo entrypoint and committed artifact set without
changing core review behavior, public schemas, or adapter boundaries.

## Scope

This task may modify:

- `examples/demo/`
- `README.md`
- `docs/QUICKSTART.md`
- `docs/CLI.md`
- `docs/PYTHON_API.md`
- `docs/MCP_SERVER.md`
- `PROJECT_STATE.md`
- `CHANGELOG.md`
- related tests

## Non-goals

This task must not:

- change deterministic review rules
- change review schemas
- change CLI flag semantics
- change Python API signatures
- change MCP tool names or payload schemas
- add a frontend or web server
- require a real LLM provider for the default demo

## Required Work

### 1. Add One Replay Entry Point

Add a demo runner under `examples/demo/` that:

- validates the demo profiles
- runs deterministic CLI review commands
- runs mock-LLM CLI review commands
- runs Python API single-file and batch demos
- runs a real local MCP stdio initialize / list-tools / tool-call flow
- regenerates the committed demo artifacts

The runner should fail loudly when any expected step fails.

### 2. Commit Unified Demo Artifacts

Add a stable demo artifact tree under `examples/demo/artifacts/` that groups:

- CLI outputs
- Python API outputs
- MCP request / response snapshots

Artifacts should be small, readable, and reproducible.

### 3. Make `examples/demo/README.md` The Main Demo Guide

Update the demo README so it becomes the main showcase entrypoint for:

- setup
- replay command
- artifact map
- CLI walkthrough
- Python API walkthrough
- MCP walkthrough
- mock-LLM boundary notes

### 4. Cross-link The Main Docs

Update the top-level docs so the unified demo is easy to discover from:

- `README.md`
- `docs/QUICKSTART.md`
- `docs/CLI.md`
- `docs/PYTHON_API.md`
- `docs/MCP_SERVER.md`

### 5. Add Regression Coverage

Add tests that verify:

- the replay runner exists and runs successfully
- the unified artifact tree exists
- committed demo outputs stay aligned with current behavior
- MCP demo responses stay valid and structured
- the main docs link to the unified demo entrypoint

## Acceptance Criteria

- `uv run python examples/demo/run_demo.py` regenerates the committed demo
  artifacts from the repository root
- the default replay path uses the current CLI, Python API, and MCP adapter
  boundaries rather than a custom review implementation
- the default replay path uses mock LLM support only
- the main docs clearly point to `examples/demo/README.md` as the end-to-end
  demo entrypoint
- automated tests cover the new unified demo contract
