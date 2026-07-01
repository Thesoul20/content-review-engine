from __future__ import annotations

import json
from pathlib import Path


def test_mcp_server_docs_cover_tools_and_boundaries() -> None:
    content = Path("docs/MCP_SERVER.md").read_text(encoding="utf-8")

    assert "content_review_file" in content
    assert "content_review_batch" in content
    assert "review_file(...)" in content
    assert "review_batch(...)" in content
    assert "deterministic-only by default" in content
    assert "combined_output_path does not auto-enable LLM" in content
    assert "llm_fail_on does not auto-enable LLM" in content
    assert "does not accept raw API keys" in content
    assert "does not auto-read `.env`" in content
    assert "prefer `stdio`" in content
    assert "batch review is non-recursive by default" in content
    assert "real LLM provider will send article content to that provider" in content
    assert "not documented here as REST API" in content


def test_mcp_example_docs_cover_client_configs() -> None:
    readme = Path("examples/mcp_server/README.md").read_text(encoding="utf-8")
    codex_config = json.loads(
        Path("examples/mcp_server/codex-config.example.json").read_text(
            encoding="utf-8"
        )
    )
    claude_config = json.loads(
        Path("examples/mcp_server/claude-desktop-config.example.json").read_text(
            encoding="utf-8"
        )
    )

    assert "uv run content-review-mcp" in readme
    assert "uv run python -m content_review_engine.mcp_server" in readme
    assert "content_review_file" in readme
    assert "content_review_batch" in readme
    assert "manual-smoke-checklist.md" in readme
    assert codex_config["mcpServers"]["content-review-engine"]["args"][-1] == (
        "content-review-mcp"
    )
    assert claude_config["mcpServers"]["content-review-engine"]["args"][-1] == (
        "content-review-mcp"
    )
    assert (
        codex_config["mcpServers"]["content-review-engine"]["args"][2]
        == "/ABSOLUTE/PATH/TO/content-review-engine"
    )
    assert (
        claude_config["mcpServers"]["content-review-engine"]["args"][2]
        == "/ABSOLUTE/PATH/TO/content-review-engine"
    )


def test_mcp_manual_smoke_and_tool_call_examples_are_documented() -> None:
    readme = Path("examples/mcp_server/README.md").read_text(encoding="utf-8")
    checklist = Path("examples/mcp_server/manual-smoke-checklist.md").read_text(
        encoding="utf-8"
    )

    assert "tool-call-examples/" in readme
    assert "content-review-file-deterministic.json" in readme
    assert "content-review-file-llm-mock.json" in readme
    assert "content-review-batch-deterministic.json" in readme
    assert "content-review-file-artifacts.json" in readme
    assert "uv run content-review-mcp --help" in checklist
    assert "uv run python -m content_review_engine.mcp_server --help" in checklist
    assert "recursive" in checklist
