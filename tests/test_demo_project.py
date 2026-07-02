from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from content_review_engine.config import load_profile, validate_profile
from content_review_engine.core.serialization import (
    batch_review_result_to_dict,
    review_result_to_dict,
)
from content_review_engine.reports import (
    render_batch_markdown_report,
    render_markdown_report,
)
from content_review_engine.review import review_document, review_markdown_directory

DEMO_DIR = Path("examples/demo")
DEMO_ARTICLES_DIR = DEMO_DIR / "articles"
DEMO_PROFILES_DIR = DEMO_DIR / "profiles"
DEMO_ARTIFACTS_DIR = DEMO_DIR / "artifacts"
DEMO_RUNNER = DEMO_DIR / "run_demo.py"

WECHAT_ARTICLE_PATH = DEMO_ARTICLES_DIR / "wechat-demo.md"
TECHNICAL_ARTICLE_PATH = DEMO_ARTICLES_DIR / "technical-demo.md"
WECHAT_PROFILE_PATH = DEMO_PROFILES_DIR / "wechat-demo.yaml"
TECHNICAL_PROFILE_PATH = DEMO_PROFILES_DIR / "technical-demo.yaml"

CLI_SINGLE_DIR = DEMO_ARTIFACTS_DIR / "cli" / "single-file"
CLI_BATCH_DIR = DEMO_ARTIFACTS_DIR / "cli" / "batch"
API_DIR = DEMO_ARTIFACTS_DIR / "api"
MCP_DIR = DEMO_ARTIFACTS_DIR / "mcp"


def _pythonpath_env() -> dict[str, str]:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        "src" if not existing_pythonpath else f"src{os.pathsep}{existing_pythonpath}"
    )
    return env


def test_demo_workspace_files_exist() -> None:
    expected_paths = [
        DEMO_DIR / "README.md",
        DEMO_RUNNER,
        WECHAT_ARTICLE_PATH,
        TECHNICAL_ARTICLE_PATH,
        WECHAT_PROFILE_PATH,
        TECHNICAL_PROFILE_PATH,
        CLI_SINGLE_DIR / "review.json",
        CLI_SINGLE_DIR / "review.md",
        CLI_SINGLE_DIR / "combined.json",
        CLI_BATCH_DIR / "review.json",
        CLI_BATCH_DIR / "combined.md",
        API_DIR / "single-file.workflow.json",
        API_DIR / "batch.workflow.json",
        MCP_DIR / "single-file.request.json",
        MCP_DIR / "single-file.response.json",
        MCP_DIR / "batch.response.json",
    ]

    for path in expected_paths:
        assert path.exists(), path.as_posix()


def test_demo_profiles_validate_and_include_regex_rules() -> None:
    expected = {
        WECHAT_PROFILE_PATH: ("wechat-demo", "wechat"),
        TECHNICAL_PROFILE_PATH: ("technical-demo", "technical"),
    }

    for path, (name, target_platform) in expected.items():
        validation_result = validate_profile(path)
        profile = load_profile(path)

        assert validation_result.valid is True
        assert validation_result.profile is not None
        assert profile.name == name
        assert profile.target_platform == target_platform
        assert profile.regex_rules
        assert "markdown_links_images" in (profile.enabled_rules or [])


def test_wechat_demo_review_produces_findings_and_respects_suppression() -> None:
    markdown_text = WECHAT_ARTICLE_PATH.read_text(encoding="utf-8")
    profile = load_profile(WECHAT_PROFILE_PATH)

    result = review_document(
        markdown_text,
        profile,
        document_path=WECHAT_ARTICLE_PATH,
        profile_path=WECHAT_PROFILE_PATH,
    )

    assert result.summary.finding_count == 6
    assert result.summary.severity_counts == {
        "info": 2,
        "warning": 4,
        "error": 0,
        "critical": 0,
    }

    rule_ids = [finding.rule_id for finding in result.findings]
    assert "absolute_claims" in rule_ids
    assert "article_placeholder" in rule_ids
    assert "engagement_bait" in rule_ids
    assert "exaggerated_claims" in rule_ids
    assert "markdown_links_images" in rule_ids
    assert rule_ids.count("exaggerated_claims") == 1

    matched_texts = [finding.matched_text for finding in result.findings]
    assert "唯一标识符" not in matched_texts
    assert "[下载链接](TODO)" in matched_texts


def test_technical_demo_review_produces_findings_and_respects_suppression() -> None:
    markdown_text = TECHNICAL_ARTICLE_PATH.read_text(encoding="utf-8")
    profile = load_profile(TECHNICAL_PROFILE_PATH)

    result = review_document(
        markdown_text,
        profile,
        document_path=TECHNICAL_ARTICLE_PATH,
        profile_path=TECHNICAL_PROFILE_PATH,
    )

    assert result.summary.finding_count == 6
    assert result.summary.severity_counts == {
        "info": 1,
        "warning": 5,
        "error": 0,
        "critical": 0,
    }

    rule_ids = [finding.rule_id for finding in result.findings]
    assert rule_ids.count("absolute_claims") == 2
    assert "absolute_technical_claim" in rule_ids
    assert "markdown_links_images" in rule_ids
    assert rule_ids.count("unresolved_draft_marker") == 1
    assert "unresolved_example" in rule_ids

    matched_texts = [finding.matched_text for finding in result.findings]
    assert "FIXME" not in matched_texts
    assert "[迁移步骤](#)" in matched_texts


def test_committed_cli_demo_artifacts_match_current_behavior() -> None:
    single_result = review_document(
        WECHAT_ARTICLE_PATH.read_text(encoding="utf-8"),
        load_profile(WECHAT_PROFILE_PATH),
        document_path=WECHAT_ARTICLE_PATH,
        profile_path=WECHAT_PROFILE_PATH,
    )
    batch_result = review_markdown_directory(
        DEMO_ARTICLES_DIR,
        load_profile(TECHNICAL_PROFILE_PATH),
        pattern="technical-*.md",
        profile_path=TECHNICAL_PROFILE_PATH,
    )

    single_json = json.loads((CLI_SINGLE_DIR / "review.json").read_text(encoding="utf-8"))
    batch_json = json.loads((CLI_BATCH_DIR / "review.json").read_text(encoding="utf-8"))
    single_combined = json.loads(
        (CLI_SINGLE_DIR / "combined.json").read_text(encoding="utf-8")
    )
    batch_combined = json.loads((CLI_BATCH_DIR / "combined.json").read_text(encoding="utf-8"))

    assert single_json == review_result_to_dict(single_result)
    assert batch_json == batch_review_result_to_dict(batch_result)
    assert (CLI_SINGLE_DIR / "review.md").read_text(encoding="utf-8").rstrip("\n") == (
        render_markdown_report(single_result, fail_on="warning")
    )
    assert (CLI_BATCH_DIR / "review.md").read_text(encoding="utf-8").rstrip("\n") == (
        render_batch_markdown_report(batch_result, fail_on="warning")
    )
    assert single_combined["schema_version"] == "single-file-combined-review-result.v1"
    assert single_combined["llm"]["status"] == "succeeded"
    assert single_combined["llm"]["quality_gate"]["enabled"] is True
    assert batch_combined["schema_version"] == "batch-combined-review-result.v1"
    assert batch_combined["llm"]["summary"]["succeeded_count"] == 1
    assert "| Quality Gate | Failed |" in (
        CLI_SINGLE_DIR / "review.md"
    ).read_text(encoding="utf-8")


def test_api_and_mcp_demo_artifacts_have_expected_boundaries() -> None:
    api_single = json.loads((API_DIR / "single-file.workflow.json").read_text(encoding="utf-8"))
    api_batch = json.loads((API_DIR / "batch.workflow.json").read_text(encoding="utf-8"))
    mcp_initialize = json.loads((MCP_DIR / "initialize.json").read_text(encoding="utf-8"))
    mcp_tools = json.loads((MCP_DIR / "tools.json").read_text(encoding="utf-8"))
    mcp_single = json.loads((MCP_DIR / "single-file.response.json").read_text(encoding="utf-8"))
    mcp_batch = json.loads((MCP_DIR / "batch.response.json").read_text(encoding="utf-8"))

    assert api_single["review_result"]["schema_version"] == "review-result.v1"
    assert api_single["llm_status"] == "succeeded"
    assert api_single["combined_result"]["llm_status"] == "succeeded"
    assert api_batch["batch_result"]["schema_version"] == "batch-review-result.v1"
    assert api_batch["llm_sidecar_result"]["summary"]["succeeded_count"] == 1

    assert mcp_initialize["server_name"] == "content-review-engine"
    assert set(mcp_tools["tool_names"]) == {"content_review_file", "content_review_batch"}
    assert mcp_single["llm_status"] == "succeeded"
    assert mcp_single["combined_result"]["llm_status"] == "succeeded"
    assert mcp_batch["batch_result"]["summary"]["finding_count"] == 6
    assert mcp_batch["combined_result"]["llm_summary"]["not_run_count"] == 1


def test_demo_runner_generates_artifacts_in_a_custom_output_root(tmp_path: Path) -> None:
    output_root = tmp_path / "demo-artifacts"

    result = subprocess.run(
        [sys.executable, "examples/demo/run_demo.py", "--output-root", str(output_root)],
        cwd=Path.cwd(),
        env=_pythonpath_env(),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Unified demo artifacts regenerated." in result.stdout
    assert (output_root / "cli" / "single-file" / "review.json").exists()
    assert (output_root / "api" / "single-file.workflow.json").exists()
    assert (output_root / "mcp" / "single-file.response.json").exists()

    generated_mcp_tools = json.loads(
        (output_root / "mcp" / "tools.json").read_text(encoding="utf-8")
    )
    assert set(generated_mcp_tools["tool_names"]) == {
        "content_review_file",
        "content_review_batch",
    }


def test_demo_readme_and_docs_link_to_unified_demo() -> None:
    demo_readme = (DEMO_DIR / "README.md").read_text(encoding="utf-8")
    report_demo = Path("report_demo.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    quickstart = Path("docs/QUICKSTART.md").read_text(encoding="utf-8")
    cli_doc = Path("docs/CLI.md").read_text(encoding="utf-8")
    api_doc = Path("docs/PYTHON_API.md").read_text(encoding="utf-8")
    mcp_doc = Path("docs/MCP_SERVER.md").read_text(encoding="utf-8")

    assert "uv sync --extra mcp" in demo_readme
    assert "uv run python examples/demo/run_demo.py" in demo_readme
    assert "artifacts/cli/" in demo_readme
    assert "artifacts/api/" in demo_readme
    assert "artifacts/mcp/" in demo_readme

    assert "uv sync --extra mcp" in report_demo
    assert "uv run python examples/demo/run_demo.py" in report_demo
    assert "--output-root /tmp/content-review-demo" in report_demo
    assert "examples/demo/artifacts/cli/single-file/review.md" in report_demo
    assert "examples/demo/README.md" in report_demo

    assert "examples/demo/README.md" in readme
    assert "../examples/demo/README.md" in quickstart
    assert "../examples/demo/README.md" in cli_doc
    assert "examples/demo/README.md" in api_doc
    assert "../examples/demo/README.md" in mcp_doc


def test_demo_docs_and_profiles_avoid_compliance_guarantee_language() -> None:
    paths = [
        DEMO_DIR / "README.md",
        WECHAT_PROFILE_PATH,
        TECHNICAL_PROFILE_PATH,
        Path("README.md"),
        Path("docs/QUICKSTART.md"),
        Path("docs/CLI.md"),
        Path("docs/PYTHON_API.md"),
        Path("docs/MCP_SERVER.md"),
    ]
    combined = " ".join(path.read_text(encoding="utf-8") for path in paths).lower()
    normalized = " ".join(combined.split())

    assert "compliance" in normalized
    assert "this ensures compliance" not in normalized
    assert "guarantees compliance" not in normalized
    assert "guaranteed approval" not in normalized
