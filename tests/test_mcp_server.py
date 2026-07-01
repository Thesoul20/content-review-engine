from __future__ import annotations

import asyncio
import json
from importlib.metadata import entry_points
from pathlib import Path

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from content_review_engine.api import review_batch, review_file
from content_review_engine.llm import LLMProviderConfig, ValidatedLLMSemanticReviewOutput
from content_review_engine.mcp_server import create_mcp_server


class _SemanticReviewer:
    def __init__(
        self,
        output: ValidatedLLMSemanticReviewOutput,
        *,
        provider: str = "pydanticai",
        model: str = "openai:gpt-4o-mini",
    ) -> None:
        self.output = output
        self.model = model
        self.config = type("Config", (), {"provider": provider})()
        self.calls: list[object] = []

    def run_semantic_review(
        self,
        request: object,
    ) -> ValidatedLLMSemanticReviewOutput:
        self.calls.append(request)
        return self.output


def _semantic_output() -> ValidatedLLMSemanticReviewOutput:
    return ValidatedLLMSemanticReviewOutput.model_validate(
        {
            "schema_version": "llm-semantic-review-output.v1",
            "summary": "One semantic issue found.",
            "findings": [
                {
                    "rule_id": "llm.semantic.overclaim",
                    "severity": "warning",
                    "line": 1,
                    "column": 1,
                    "message": "Possible overclaim.",
                    "evidence": "绝对安全",
                    "suggestion": "Use a softer claim.",
                    "confidence": 0.84,
                }
            ],
        }
    )


def _tool_result_structured_payload(result: object) -> dict[str, object]:
    assert isinstance(result, tuple)
    assert len(result) == 2
    return result[1]


async def _call_tool(name: str, arguments: dict[str, object]) -> dict[str, object]:
    server = create_mcp_server()
    result = await server.call_tool(name, arguments)
    return _tool_result_structured_payload(result)


def test_mcp_server_registers_expected_tools() -> None:
    server = create_mcp_server()

    async def run() -> list[object]:
        return await server.list_tools()

    tools = asyncio.run(run())
    tool_names = {tool.name for tool in tools}
    tool_map = {tool.name: tool for tool in tools}

    assert tool_names == {"content_review_file", "content_review_batch"}
    assert "markdown_path" in tool_map["content_review_file"].inputSchema["properties"]
    assert "enable_llm" in tool_map["content_review_file"].inputSchema["properties"]
    assert "input_dir" in tool_map["content_review_batch"].inputSchema["properties"]
    assert "recursive" in tool_map["content_review_batch"].inputSchema["properties"]
    assert tool_map["content_review_file"].outputSchema is not None
    assert tool_map["content_review_batch"].outputSchema is not None


def test_mcp_console_script_entrypoint_is_exposed() -> None:
    console_scripts = entry_points(group="console_scripts")
    mcp_entrypoints = [
        entry_point
        for entry_point in console_scripts
        if entry_point.name == "content-review-mcp"
    ]

    assert mcp_entrypoints, "content-review-mcp console script is missing"
    assert mcp_entrypoints[0].value == "content_review_engine.mcp_server:main"


def test_mcp_single_file_deterministic_matches_python_api() -> None:
    tool_payload = asyncio.run(
        _call_tool(
            "content_review_file",
            {
                "markdown_path": "tests/fixtures/markdown/forbidden_terms_article.md",
                "profile_path": "tests/fixtures/profiles/default.yml",
                "fail_on": "warning",
                "include_combined_result": True,
            },
        )
    )
    api_payload = review_file(
        "tests/fixtures/markdown/forbidden_terms_article.md",
        "tests/fixtures/profiles/default.yml",
        fail_on="warning",
        include_combined_result=True,
    ).model_dump(mode="json")

    assert tool_payload == api_payload
    assert tool_payload["llm_status"] == "not_run"
    assert tool_payload["review_result"]["summary"]["finding_count"] == 1
    assert tool_payload["combined_result"]["llm_status"] == "not_run"


def test_mcp_batch_deterministic_matches_python_api() -> None:
    tool_payload = asyncio.run(
        _call_tool(
            "content_review_batch",
            {
                "input_dir": "tests/fixtures/batch/articles",
                "profile_path": "tests/fixtures/batch/profile.yml",
                "recursive": True,
                "fail_on": "warning",
                "include_combined_result": True,
            },
        )
    )
    api_payload = review_batch(
        "tests/fixtures/batch/articles",
        "tests/fixtures/batch/profile.yml",
        recursive=True,
        fail_on="warning",
        include_combined_result=True,
    ).model_dump(mode="json")

    assert tool_payload == api_payload
    assert tool_payload["batch_result"]["summary"]["finding_count"] == 2
    assert tool_payload["combined_result"]["llm_summary"]["not_run_count"] == 3


def test_mcp_optional_llm_path_returns_llm_and_preserves_deterministic_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reviewer = _SemanticReviewer(_semantic_output())
    monkeypatch.setattr(
        "content_review_engine.workflows.create_llm_reviewer",
        lambda *args, **kwargs: reviewer,
    )

    payload = asyncio.run(
        _call_tool(
            "content_review_file",
            {
                "markdown_path": "tests/fixtures/markdown/clean_article.md",
                "profile_path": "tests/fixtures/profiles/default.yml",
                "enable_llm": True,
                "llm_provider_config": {"provider": "mock"},
                "llm_fail_on": "warning",
                "include_combined_result": True,
            },
        )
    )

    assert payload["llm_status"] == "succeeded"
    assert payload["llm_result"]["findings"][0]["rule_id"] == "llm.semantic.overclaim"
    assert payload["llm_quality_gate"]["failed"] is True
    assert payload["review_result"]["summary"]["severity_counts"]["warning"] == 0
    assert payload["review_result"]["findings"] == []
    assert reviewer.calls


def test_mcp_output_paths_write_artifacts_and_combined_output_does_not_enable_llm(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "review.json"
    combined_output_path = tmp_path / "review.combined.json"

    payload = asyncio.run(
        _call_tool(
            "content_review_file",
            {
                "markdown_path": "tests/fixtures/markdown/clean_article.md",
                "profile_path": "tests/fixtures/profiles/default.yml",
                "output_format": "json",
                "output_path": str(output_path),
                "combined_output_path": str(combined_output_path),
                "combined_output_format": "json",
            },
        )
    )

    deterministic_payload = json.loads(output_path.read_text(encoding="utf-8"))
    combined_payload = json.loads(combined_output_path.read_text(encoding="utf-8"))

    assert payload["artifacts"]["output_path"] == str(output_path)
    assert payload["artifacts"]["combined_output_path"] == str(combined_output_path)
    assert payload["llm_result"] is None
    assert payload["llm_status"] == "not_run"
    assert deterministic_payload["schema_version"] == "review-result.v1"
    assert combined_payload["llm"]["status"] == "not_run"


def test_mcp_llm_fail_on_does_not_auto_enable_llm() -> None:
    payload = asyncio.run(
        _call_tool(
            "content_review_file",
            {
                "markdown_path": "tests/fixtures/markdown/clean_article.md",
                "profile_path": "tests/fixtures/profiles/default.yml",
                "llm_fail_on": "warning",
                "include_combined_result": True,
            },
        )
    )

    assert payload["llm_result"] is None
    assert payload["llm_status"] == "not_run"
    assert payload["llm_quality_gate"]["enabled"] is True
    assert payload["llm_quality_gate"]["evaluation_status"] == "not_run"


def test_mcp_batch_artifact_outputs_work(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "batch.json"
    combined_output_path = tmp_path / "batch.combined.json"

    payload = asyncio.run(
        _call_tool(
            "content_review_batch",
            {
                "input_dir": "tests/fixtures/batch/articles",
                "profile_path": "tests/fixtures/batch/profile.yml",
                "recursive": True,
                "output_format": "json",
                "output_path": str(output_path),
                "combined_output_path": str(combined_output_path),
                "combined_output_format": "json",
            },
        )
    )

    deterministic_payload = json.loads(output_path.read_text(encoding="utf-8"))
    combined_payload = json.loads(combined_output_path.read_text(encoding="utf-8"))

    assert payload["artifacts"]["output_path"] == str(output_path)
    assert payload["artifacts"]["combined_output_path"] == str(combined_output_path)
    assert deterministic_payload["schema_version"] == "batch-review-result.v1"
    assert combined_payload["llm"]["summary"]["not_run_count"] == 3


def test_mcp_errors_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom(*args, **kwargs):
        raise RuntimeError("provider failed with Bearer sk-secret-123 token")

    monkeypatch.setattr("content_review_engine.mcp_server.review_file", _boom)

    with pytest.raises(ToolError) as exc_info:
        asyncio.run(
            _call_tool(
                "content_review_file",
                {
                    "markdown_path": "tests/fixtures/markdown/clean_article.md",
                    "profile_path": "tests/fixtures/profiles/default.yml",
                },
            )
        )

    message = str(exc_info.value)
    assert "sk-secret-123" not in message
    assert "Bearer [REDACTED]" in message


def test_mcp_default_tests_do_not_require_real_llm_api() -> None:
    payload = asyncio.run(
        _call_tool(
            "content_review_file",
            {
                "markdown_path": "tests/fixtures/markdown/clean_article.md",
                "profile_path": "tests/fixtures/profiles/default.yml",
                "enable_llm": True,
                "llm_provider_config": {"provider": "mock"},
            },
        )
    )

    assert payload["llm_status"] == "succeeded"
    assert payload["llm_result"]["schema_version"] == "llm-review-result.v1"
    assert payload["llm_quality_gate"]["enabled"] is False
