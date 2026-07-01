from __future__ import annotations

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


def test_mcp_example_docs_cover_client_configs() -> None:
    readme = Path("examples/mcp_server/README.md").read_text(encoding="utf-8")
    codex_config = Path("examples/mcp_server/codex-config.example.json").read_text(
        encoding="utf-8"
    )
    claude_config = Path(
        "examples/mcp_server/claude-desktop-config.example.json"
    ).read_text(encoding="utf-8")

    assert "uv run content-review-mcp" in readme
    assert "content_review_file" in readme
    assert "content_review_batch" in readme
    assert "content-review-mcp" in codex_config
    assert "content-review-mcp" in claude_config
    assert "/ABSOLUTE/PATH/TO/content-review-engine" in codex_config
    assert "/ABSOLUTE/PATH/TO/content-review-engine" in claude_config
