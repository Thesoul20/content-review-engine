# Content Review Engine

Content Review Engine is a Python package-first Markdown review toolkit.
It reviews Markdown content against configurable profiles and returns
structured results that can be used from the CLI, Python API, or a local MCP
server.

The project is built around one rule: core review logic lives in
`src/content_review_engine/`, while CLI, API, and MCP are thin adapters over
the same workflow.

## Highlights

- Deterministic Markdown review with structured findings and source locations
- YAML review profiles with built-in templates and validation
- Built-in rules for forbidden terms, absolute claims, Markdown structure,
  and link/image hygiene
- Profile-defined `regex_rules` with stable `rule_id` values
- Single-file and batch review workflows
- Text, JSON, Markdown, and combined output artifacts
- Optional LLM sidecar review with explicit artifact and quality-gate
  boundaries
- Stable Python API facade for in-process integrations
- Local MCP server wrapper over the same Python API
- Unified end-to-end demo workspace with committed CLI, API, and MCP artifacts

## Current Status

The repository has moved beyond initialization. The current implemented
surface includes:

- core Markdown parser, profile loader, rule runner, and report layer
- `content-review review`, `batch`, `profile`, and `llm-check` CLI commands
- stable Python workflow entrypoints in `content_review_engine.api`
- optional local MCP server entrypoint in `content_review_engine.mcp_server`
- mock and real-provider LLM adapter paths that stay separate from the
  deterministic review result

This is still an actively evolving project. The deterministic review layer is
the canonical output contract today.

## Installation

Requirements:

- Python 3.13+
- `uv`

Install dependencies from the repository root:

```bash
uv sync
```

If you also want the MCP server entrypoint:

```bash
uv sync --extra mcp
```

Verify the CLI is available:

```bash
uv run content-review --help
```

## Quick Start

List available built-in profile templates:

```bash
uv run content-review profile list
```

Create a local profile from a template:

```bash
mkdir -p profiles
uv run content-review profile init \
  --template wechat-article \
  --output profiles/my-wechat.yaml
```

Validate the profile:

```bash
uv run content-review profile validate profiles/my-wechat.yaml
```

Review one Markdown file:

```bash
uv run content-review review \
  examples/demo/articles/wechat-demo.md \
  --profile profiles/my-wechat.yaml
```

Write a Markdown report:

```bash
uv run content-review review \
  examples/demo/articles/wechat-demo.md \
  --profile profiles/my-wechat.yaml \
  --format markdown \
  --output /tmp/review-report.md
```

Run batch review:

```bash
uv run content-review batch \
  examples/demo/articles \
  --profile profiles/my-wechat.yaml \
  --recursive
```

For the complete first-run workflow, see
[docs/QUICKSTART.md](docs/QUICKSTART.md).

## What The Project Reviews

Current deterministic review checks include:

- configured forbidden or risky literal terms
- configured absolute or exaggerated claims
- profile-defined regex patterns
- missing or malformed Markdown structure signals
- obvious Markdown link and image placeholder issues

Profiles can also tune:

- enabled rules
- severity thresholds
- allowlists
- paragraph/title length limits
- custom regex rules

Built-in example profiles live under
[profiles/examples](profiles/examples).

## Output Model

The project intentionally keeps deterministic, LLM, and combined artifacts as
separate output families.

- Deterministic output: canonical `ReviewResult` or `BatchReviewResult`
- Raw LLM sidecar: canonical `LLMReviewResult` or `LLMSidecarResult`
- Combined output: explicit integration artifact that preserves both layers

Important boundaries:

- deterministic output remains the primary automation contract
- LLM review is explicit opt-in
- LLM findings do not merge into deterministic findings
- deterministic `--fail-on` and LLM `--llm-fail-on` are separate gates
- combined output does not auto-enable LLM review

## CLI Surface

Main commands:

```bash
uv run content-review review <markdown_file> --profile <profile_file>
uv run content-review batch <input_dir> --profile <profile_file>
uv run content-review profile validate <profile_file>
uv run content-review profile init --template <template_name> --output <file>
uv run content-review profile list
uv run content-review llm-check
```

Useful examples:

```bash
uv run content-review review article.md --profile profile.yaml --format json
uv run content-review review article.md --profile profile.yaml --fail-on error
uv run content-review batch articles --profile profile.yaml --recursive
uv run content-review review article.md --profile profile.yaml --format markdown --output review.md
```

For the full command contract, including `--combined-output`,
`--report-index`, `--llm-output`, `--llm-report`, and `--llm-fail-on`, see
[docs/CLI.md](docs/CLI.md).

## Python API

The stable in-process entrypoints are:

```python
from content_review_engine.api import review_batch, review_file
```

Example:

```python
from content_review_engine.api import review_file

result = review_file(
    "examples/demo/articles/wechat-demo.md",
    "examples/demo/profiles/wechat-demo.yaml",
)

print(result.review_result.summary.finding_count)
```

The Python API can also write deterministic, raw LLM, and combined artifacts
without shelling out through the CLI.

See [docs/PYTHON_API.md](docs/PYTHON_API.md) for details.

## MCP Server

The repository also includes a local MCP server wrapper over the same Python
API facade.

Startup entrypoints:

```bash
uv run content-review-mcp
uv run python -m content_review_engine.mcp_server
```

The MCP server is intended as a local tool adapter, not a hosted web service.

See [docs/MCP_SERVER.md](docs/MCP_SERVER.md) for tool names, JSON schemas,
and client setup notes.

## Optional LLM Review

The LLM layer is designed as an adapter around the deterministic pipeline, not
as a replacement for it.

Current behavior:

- deterministic review works without any LLM setup
- LLM review must be explicitly enabled
- safe local test providers include `mock` and `pydantic-ai-testmodel`
- real-provider usage currently goes through the `pydanticai` path
- the CLI does not auto-read `.env`
- raw API keys are not accepted directly in CLI flags

Local mock example:

```bash
uv run content-review review article.md \
  --profile profile.yaml \
  --enable-llm \
  --llm-provider mock \
  --llm-output /tmp/article.llm.json
```

For real-provider setup and troubleshooting, see
[docs/LLM_PROVIDER_USAGE.md](docs/LLM_PROVIDER_USAGE.md).

## Demo Workspace

The main end-to-end demo lives in [examples/demo](examples/demo).

It includes:

- demo articles and demo profiles
- a replay script that regenerates committed artifacts
- CLI deterministic and mock-LLM artifacts
- Python API workflow artifacts
- MCP request and response snapshots

Replay the demo:

```bash
uv run python examples/demo/run_demo.py
```

Write demo output to a custom directory:

```bash
uv run python examples/demo/run_demo.py --output-root /tmp/content-review-demo
```

See [examples/demo/README.md](examples/demo/README.md) for the walkthrough.

## Repository Layout

```text
src/content_review_engine/   core package, CLI, API, MCP, rules, reports
docs/                        user-facing documentation
profiles/examples/           built-in example profile templates
examples/demo/               unified end-to-end demo workspace
examples/llm_review_artifacts/ committed reference LLM artifacts
tests/                       automated test suite
tasks/                       task-based project workflow records
decisions/                   architecture decision records
```

## Architecture

Current adapter stack:

```text
CLI / Python API / MCP
        ↓
Shared workflow helpers
        ↓
Core review package
        ↓
Rules / Reports / Optional LLM adapter
```

The core package owns:

- Markdown input handling
- profile loading and validation
- deterministic review execution
- quality-gate evaluation
- structured result models
- report rendering

Adapters should not duplicate review logic.

For more detail, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Limitations

- The project reviews Markdown only.
- Deterministic rules are intentionally explicit and profile-driven.
- LLM review is advisory unless you explicitly enable its separate gate.
- The project does not guarantee legal, medical, advertising, regulatory, or
  platform compliance.
- MCP support is local-first and currently documented primarily for `stdio`
  usage.

## Development

Install development dependencies:

```bash
uv sync --extra mcp --group dev
```

Run tests:

```bash
uv run pytest
```

Project workflow and contribution context live in:

- [AGENTS.md](AGENTS.md)
- [PROJECT_STATE.md](PROJECT_STATE.md)
- [ROADMAP.md](ROADMAP.md)

## Documentation Map

- [docs/QUICKSTART.md](docs/QUICKSTART.md)
- [docs/CLI.md](docs/CLI.md)
- [docs/PYTHON_API.md](docs/PYTHON_API.md)
- [docs/MCP_SERVER.md](docs/MCP_SERVER.md)
- [docs/RULES.md](docs/RULES.md)
- [docs/DATA_MODELS.md](docs/DATA_MODELS.md)
- [docs/LLM_PROVIDER_USAGE.md](docs/LLM_PROVIDER_USAGE.md)
- [examples/demo/README.md](examples/demo/README.md)
