from __future__ import annotations

import json
from importlib.metadata import entry_points
from pathlib import Path

import pytest

from content_review_engine.cli import main
from content_review_engine.config import (
    get_profile_template,
    list_profile_template_names,
    list_profile_templates,
    load_profile,
    validate_profile,
)


def test_cli_review_with_findings_prints_finding_details(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/forbidden_terms_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(["review", markdown_path, "--profile", profile_path])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Review completed." in captured.out
    assert "Findings: 1" in captured.out
    assert "[warning] forbidden_terms: 发现风险词：绝对安全" in captured.out
    assert "Line: 1" in captured.out
    assert "Column: 8" in captured.out
    assert "Matched: 绝对安全" in captured.out
    assert "Context: # 测试文章 绝对安全" in captured.out
    assert captured.err == ""


def test_cli_review_preserves_success_exit_code_without_fail_on(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/forbidden_terms_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(["review", markdown_path, "--profile", profile_path])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 1" in captured.out
    assert captured.err == ""


def test_cli_review_fail_on_exits_zero_when_findings_are_below_threshold(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/forbidden_terms_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--fail-on",
            "error",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 1" in captured.out
    assert captured.err == ""


def test_cli_review_fail_on_exits_one_when_finding_meets_threshold(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/forbidden_terms_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--fail-on",
            "warning",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Findings: 1" in captured.out
    assert captured.err == ""


def test_cli_review_suppressed_finding_does_not_fail_quality_gate(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = tmp_path / "suppressed.md"
    markdown_path.write_text(
        "这里写着绝对安全。 <!-- content-review-disable-line forbidden_terms -->",
        encoding="utf-8",
    )
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            str(markdown_path),
            "--profile",
            profile_path,
            "--fail-on",
            "warning",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 0" in captured.out
    assert "绝对安全" not in captured.out
    assert captured.err == ""


def test_cli_review_fail_on_rejects_invalid_severity(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/forbidden_terms_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--fail-on",
            "high",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Invalid severity: 'high'" in captured.err
    assert captured.out == ""


def test_cli_review_without_findings_prints_zero_findings(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(["review", markdown_path, "--profile", profile_path])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Review completed." in captured.out
    assert "Findings: 0" in captured.out
    assert "No issues found." in captured.out
    assert captured.err == ""


def test_cli_review_markdown_default_output_does_not_include_llm_section(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "markdown",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "## LLM Review" not in captured.out
    assert "# Content Review Report" in captured.out
    assert captured.err == ""


def test_cli_review_enable_llm_writes_mock_sidecar_without_changing_main_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    review_output_path = tmp_path / "review.json"
    llm_output_path = tmp_path / "review.llm.json"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "json",
            "--output",
            str(review_output_path),
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()
    review_payload = json.loads(review_output_path.read_text(encoding="utf-8"))
    llm_payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert review_payload["schema_version"] == "review-result.v1"
    assert "llm_review" not in review_payload
    assert llm_payload["schema_version"] == "llm-sidecar-result.v1"
    assert llm_payload["summary"] == {
        "file_count": 1,
        "succeeded_count": 1,
        "failed_count": 0,
        "skipped_count": 0,
        "finding_count": 0,
    }
    assert llm_payload["files"] == [
        {
            "path": markdown_path,
            "status": "success",
            "finding_count": 0,
            "review": {
                "schema_version": "llm-review-result.v1",
                "findings": [],
            },
        }
    ]


def test_cli_review_markdown_enable_llm_without_include_report_keeps_report_unchanged(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    llm_output_path = tmp_path / "review.llm.json"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "markdown",
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()
    llm_payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "## LLM Review" not in captured.out
    assert llm_payload["schema_version"] == "llm-sidecar-result.v1"
    assert llm_payload["files"][0]["status"] == "success"
    assert llm_payload["files"][0]["review"] == {
        "schema_version": "llm-review-result.v1",
        "findings": [],
    }
    assert captured.err == ""


def test_cli_review_markdown_include_llm_report_appends_llm_section(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    llm_output_path = tmp_path / "review.llm.json"

    from content_review_engine.llm import LLMReviewFinding, LLMReviewResult

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self, request
        return LLMReviewResult(
            findings=(
                LLMReviewFinding(
                    rule_id="llm_semantic_risk",
                    severity="warning",
                    message="Possible unsupported claim.",
                    suggestion="Add evidence.",
                ),
            )
        )

    monkeypatch.setattr("content_review_engine.llm.mock.MockLLMReviewer.review", fake_review)

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "markdown",
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
            "--include-llm-report",
        ]
    )

    captured = capsys.readouterr()
    llm_payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "## LLM Review" in captured.out
    assert "| Total Findings | 1 |" in captured.out
    assert "llm_semantic_risk" in captured.out
    assert "Possible unsupported claim." in captured.out
    assert "Add evidence." in captured.out
    assert llm_payload["files"][0]["status"] == "success"
    assert llm_payload["files"][0]["review"]["findings"][0]["rule_id"] == "llm_semantic_risk"
    assert captured.err == ""


def test_cli_review_include_llm_report_requires_enable_llm(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "markdown",
            "--include-llm-report",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --include-llm-report requires --enable-llm" in captured.err


def test_cli_review_include_llm_report_requires_markdown_format_json_fails(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "json",
            "--enable-llm",
            "--llm-output",
            str(tmp_path / "review.llm.json"),
            "--include-llm-report",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --include-llm-report requires --format markdown" in captured.err


def test_cli_review_include_llm_report_requires_markdown_format_text_fails(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "text",
            "--enable-llm",
            "--llm-output",
            str(tmp_path / "review.llm.json"),
            "--include-llm-report",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --include-llm-report requires --format markdown" in captured.err


def test_cli_review_quality_gate_ignores_llm_findings_when_report_is_included(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    llm_output_path = tmp_path / "review.llm.json"

    from content_review_engine.llm import LLMReviewFinding, LLMReviewResult

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self, request
        return LLMReviewResult(
            findings=(
                LLMReviewFinding(
                    rule_id="llm_critical_issue",
                    severity="critical",
                    message="Critical semantic issue.",
                ),
            )
        )

    monkeypatch.setattr("content_review_engine.llm.mock.MockLLMReviewer.review", fake_review)

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "markdown",
            "--fail-on",
            "warning",
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
            "--include-llm-report",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "| Quality Gate | Passed |" in captured.out
    assert "| Matched Gate Findings | 0 |" in captured.out
    assert "llm_critical_issue" in captured.out
    assert captured.err == ""


def test_cli_review_llm_failure_writes_failed_sidecar_and_keeps_deterministic_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    llm_output_path = tmp_path / "review.llm.json"

    from content_review_engine.llm import LLMProviderError

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self, request
        raise LLMProviderError("provider temporarily unavailable")

    monkeypatch.setattr("content_review_engine.llm.mock.MockLLMReviewer.review", fake_review)

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--fail-on",
            "warning",
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()
    llm_payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "Findings: 0" in captured.out
    assert captured.err == ""
    assert llm_payload["summary"] == {
        "file_count": 1,
        "succeeded_count": 0,
        "failed_count": 1,
        "skipped_count": 0,
        "finding_count": 0,
    }
    assert llm_payload["files"] == [
        {
            "path": markdown_path,
            "status": "failed",
            "finding_count": 0,
            "error": {
                "error_type": "LLMProviderError",
                "message": "provider temporarily unavailable",
            },
        }
    ]


def test_cli_review_enable_llm_builds_request_from_current_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    llm_output_path = tmp_path / "review.llm.json"
    captured_request: dict[str, object] = {}

    from content_review_engine.llm import LLMReviewResult

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self
        captured_request["content"] = request.content
        captured_request["profile_name"] = request.profile_name
        captured_request["content_path"] = request.content_path
        captured_request["review_goal"] = request.review_goal
        return LLMReviewResult()

    monkeypatch.setattr("content_review_engine.llm.mock.MockLLMReviewer.review", fake_review)

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--enable-llm",
            "--llm-provider",
            "mock",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert captured_request == {
        "content": (
            "# 内容审核工作流\n\n"
            "内容审核帮助团队保持表达一致。\n\n"
            "## 复核流程\n\n"
            "先写草稿，再检查措辞和结构。"
        ),
        "profile_name": "default",
        "content_path": markdown_path,
        "review_goal": "semantic_review",
    }


def test_cli_review_enable_llm_requires_llm_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--enable-llm",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --enable-llm requires --llm-output" in captured.err


def test_cli_review_llm_output_requires_enable_llm(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--llm-output",
            str(tmp_path / "review.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --llm-output requires --enable-llm" in captured.err


def test_cli_review_llm_provider_without_enable_llm_does_not_affect_deterministic_review(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--llm-provider",
            "mock",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 0" in captured.out
    assert captured.err == ""


def test_cli_review_llm_model_without_enable_llm_does_not_affect_deterministic_review(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--llm-model",
            "gpt-4o-mini",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 0" in captured.out
    assert captured.err == ""


def test_cli_review_llm_api_key_env_without_enable_llm_does_not_affect_deterministic_review(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--llm-api-key-env",
            "OPENAI_API_KEY",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 0" in captured.out
    assert captured.err == ""


def test_cli_review_llm_base_url_without_enable_llm_does_not_affect_deterministic_review(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--llm-base-url",
            "https://example.com/v1",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 0" in captured.out
    assert captured.err == ""


def test_cli_review_llm_timeout_without_enable_llm_does_not_affect_deterministic_review(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--llm-timeout-seconds",
            "15",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 0" in captured.out
    assert captured.err == ""


def test_cli_review_rejects_invalid_llm_timeout(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--llm-timeout-seconds",
            "0",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "LLM timeout seconds must be greater than 0." in captured.err


def test_cli_review_llm_markdown_output_requires_enable_llm(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--llm-markdown-output",
            str(tmp_path / "review.llm.md"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --llm-markdown-output requires --enable-llm" in captured.err


def test_cli_review_rejects_unsupported_llm_provider(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--enable-llm",
            "--llm-provider",
            "openai",
            "--llm-output",
            str(tmp_path / "review.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "Error: Unknown LLM provider 'openai'. Supported providers: 'mock', 'pydanticai'."
        in captured.err
    )


def test_cli_review_mock_provider_still_works_without_llm_model(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--enable-llm",
            "--llm-provider",
            "mock",
            "--llm-output",
            str(tmp_path / "review.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""


def test_cli_review_mock_provider_accepts_llm_model_and_api_key_env_config(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    llm_output_path = tmp_path / "review.llm.json"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--enable-llm",
            "--llm-provider",
            "mock",
            "--llm-model",
            "mock-model",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-base-url",
            "https://example.com/v1",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()
    llm_payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.err == ""
    assert llm_payload["files"][0]["status"] == "success"


def test_cli_review_pydanticai_provider_writes_sidecar_json_and_markdown_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    review_output_path = tmp_path / "review.json"
    llm_output_path = tmp_path / "review.llm.json"
    llm_markdown_output_path = tmp_path / "review.llm.md"

    monkeypatch.setenv("CONTENT_REVIEW_TEST_LLM_API_KEY", "test-secret-value")
    captured_agent_kwargs: dict[str, object] = {}
    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.build_pydanticai_runtime_agent",
        lambda **kwargs: captured_agent_kwargs.update(kwargs) or object(),
    )
    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.run_pydanticai_runtime_agent",
        lambda _agent, _payload: {
            "findings": [
                {
                    "rule_id": "llm_semantic_risk",
                    "severity": "warning",
                    "message": "Possible unsupported claim.",
                    "suggestion": "Add evidence.",
                }
            ],
            "summary": {
                "overall_risk": "medium",
                "summary": "One issue was detected.",
                "recommended_action": "Revise before publishing.",
            },
        },
    )

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "json",
            "--output",
            str(review_output_path),
            "--fail-on",
            "warning",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "gpt-4o-mini",
            "--llm-api-key-env",
            "CONTENT_REVIEW_TEST_LLM_API_KEY",
            "--llm-timeout-seconds",
            "21",
            "--llm-output",
            str(llm_output_path),
            "--llm-markdown-output",
            str(llm_markdown_output_path),
        ]
    )

    captured = capsys.readouterr()
    review_payload = json.loads(review_output_path.read_text(encoding="utf-8"))
    llm_payload = json.loads(llm_output_path.read_text(encoding="utf-8"))
    markdown_report = llm_markdown_output_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert review_payload["schema_version"] == "review-result.v1"
    assert "llm_review" not in review_payload
    assert llm_payload["summary"] == {
        "file_count": 1,
        "succeeded_count": 1,
        "failed_count": 0,
        "skipped_count": 0,
        "finding_count": 1,
    }
    assert llm_payload["files"][0]["status"] == "success"
    assert llm_payload["files"][0]["review"]["provider"] == "pydanticai"
    assert llm_payload["files"][0]["review"]["model"] == "gpt-4o-mini"
    assert llm_payload["files"][0]["review"]["findings"][0]["rule_id"] == "llm_semantic_risk"
    assert markdown_report.startswith("# LLM Sidecar Review Report\n")
    assert "llm_semantic_risk" in markdown_report
    assert "Possible unsupported claim." in markdown_report
    assert "test-secret-value" not in markdown_report
    assert captured_agent_kwargs["timeout_seconds"] == 21.0


def test_cli_review_pydanticai_provider_requires_api_key_env(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "review.llm.json"

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "gpt-4o-mini",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: LLM provider 'pydanticai' requires api_key_env to be configured." in captured.err
    assert not llm_output_path.exists()


def test_cli_review_pydanticai_provider_rejects_missing_environment_variable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "review.llm.json"
    monkeypatch.delenv("CONTENT_REVIEW_TEST_LLM_API_KEY", raising=False)

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "gpt-4o-mini",
            "--llm-api-key-env",
            "CONTENT_REVIEW_TEST_LLM_API_KEY",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "Error: LLM API key environment variable 'CONTENT_REVIEW_TEST_LLM_API_KEY' is not set."
        in captured.err
    )
    assert not llm_output_path.exists()


def test_cli_review_llm_markdown_output_writes_single_file_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    llm_output_path = tmp_path / "review.llm.json"
    llm_markdown_output_path = tmp_path / "review.llm.md"

    from content_review_engine.llm import LLMReviewFinding, LLMReviewResult

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self, request
        return LLMReviewResult(
            findings=(
                LLMReviewFinding(
                    rule_id="llm_semantic_risk",
                    severity="warning",
                    message="Possible unsupported claim.",
                    suggestion="Add evidence.",
                ),
            )
        )

    monkeypatch.setattr("content_review_engine.llm.mock.MockLLMReviewer.review", fake_review)

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
            "--llm-markdown-output",
            str(llm_markdown_output_path),
        ]
    )

    captured = capsys.readouterr()
    markdown_report = llm_markdown_output_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert captured.err == ""
    assert markdown_report.startswith("# LLM Sidecar Review Report\n")
    assert "| File | Status | Findings | Error |" in markdown_report
    assert "| tests/fixtures/markdown/clean_article.md | success | 1 | - |" in markdown_report
    assert "Possible unsupported claim." in markdown_report
    assert "Add evidence." in markdown_report


def test_cli_review_llm_markdown_output_does_not_change_deterministic_markdown_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    llm_output_path = tmp_path / "review.llm.json"
    llm_markdown_output_path = tmp_path / "review.llm.md"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "markdown",
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
            "--llm-markdown-output",
            str(llm_markdown_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "# Content Review Report" in captured.out
    assert "## LLM Review" not in captured.out
    assert "LLM Sidecar Review Report" in llm_markdown_output_path.read_text(
        encoding="utf-8"
    )


def test_cli_review_quality_gate_ignores_llm_markdown_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    llm_output_path = tmp_path / "review.llm.json"
    llm_markdown_output_path = tmp_path / "review.llm.md"

    from content_review_engine.llm import LLMReviewFinding, LLMReviewResult

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self, request
        return LLMReviewResult(
            findings=(
                LLMReviewFinding(
                    rule_id="llm_critical_issue",
                    severity="critical",
                    message="Critical semantic issue.",
                ),
            )
        )

    monkeypatch.setattr("content_review_engine.llm.mock.MockLLMReviewer.review", fake_review)

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--fail-on",
            "warning",
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
            "--llm-markdown-output",
            str(llm_markdown_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 0" in captured.out
    assert captured.err == ""


def test_cli_missing_markdown_file_returns_non_zero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            str(tmp_path / "missing.md"),
            "--profile",
            profile_path,
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Markdown file not found" in captured.err


def test_cli_missing_profile_file_returns_non_zero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/forbidden_terms_article.md"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            str(tmp_path / "missing.yaml"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Profile file not found" in captured.err


def test_cli_root_help_shows_usage(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--help"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out.lower()
    assert "content-review" in captured.out


def test_cli_review_help_shows_usage(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["review", "--help"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out.lower()
    assert "--profile" in captured.out


def test_cli_profile_help_shows_validate_subcommand(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["profile", "--help"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out.lower()
    assert "validate" in captured.out
    assert "init" in captured.out
    assert "list" in captured.out


def test_cli_profile_validate_help_shows_profile_path(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["profile", "validate", "--help"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out.lower()
    assert "profile_path" in captured.out


def test_cli_profile_init_help_shows_template_output_and_force(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["profile", "init", "--help"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out.lower()
    assert "--template" in captured.out
    assert "--output" in captured.out
    assert "--force" in captured.out
    assert "Create a new review profile from a built-in template." in captured.out


def test_cli_profile_list_help_shows_format(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["profile", "list", "--help"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out.lower()
    assert "--format" in captured.out
    assert "List available built-in review profile templates." in captured.out


def test_cli_profile_list_text_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["profile", "list"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert "Available profile templates:" in captured.out
    assert "- general-basic" in captured.out
    assert "General-purpose starter profile for public-facing content." in captured.out
    assert "- general-publishing" in captured.out
    assert "Conservative publishing profile with placeholder and overclaim checks." in captured.out
    assert "- health-content" in captured.out
    assert "Cautious health-content profile for risky treatment wording review." in captured.out
    assert "- marketing-copy" in captured.out
    assert "Marketing copy profile for pressure tactics and guarantee-like wording." in captured.out
    assert "- technical-blog" in captured.out
    assert "Technical blog profile for unresolved draft markers and absolute claims." in captured.out
    assert "- wechat-basic" in captured.out
    assert "Basic WeChat article profile with moderate checks." in captured.out
    assert "- wechat-article" in captured.out
    assert "WeChat article profile with cautious regex checks for public-facing drafts." in captured.out
    assert "- wechat-strict" in captured.out
    assert "Stricter WeChat profile intended for batch checks and CI gates." in captured.out
    assert (
        "content-review profile init --template wechat-basic --output profile.yaml"
        in captured.out
    )


def test_cli_profile_list_json_output_uses_canonical_schema(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["profile", "list", "--format", "json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert captured.err == ""
    assert payload == {
        "schema_version": "profile-template-list.v1",
        "templates": [
            {
                "name": "general-basic",
                "description": "General-purpose starter profile for public-facing content.",
            },
            {
                "name": "general-publishing",
                "description": "Conservative publishing profile with placeholder and overclaim checks.",
            },
            {
                "name": "health-content",
                "description": "Cautious health-content profile for risky treatment wording review.",
            },
            {
                "name": "marketing-copy",
                "description": "Marketing copy profile for pressure tactics and guarantee-like wording.",
            },
            {
                "name": "technical-blog",
                "description": "Technical blog profile for unresolved draft markers and absolute claims.",
            },
            {
                "name": "wechat-basic",
                "description": "Basic WeChat article profile with moderate checks.",
            },
            {
                "name": "wechat-article",
                "description": "WeChat article profile with cautious regex checks for public-facing drafts.",
            },
            {
                "name": "wechat-strict",
                "description": "Stricter WeChat profile intended for batch checks and CI gates.",
            },
        ],
    }
    for template in payload["templates"]:
        assert set(template.keys()) == {"name", "description"}


@pytest.mark.parametrize(
    ("template_name", "expected_name", "expected_platform"),
    [
        ("general-basic", "general-basic", "general"),
        ("general-publishing", "general-publishing", "general"),
        ("health-content", "health-content", "health"),
        ("marketing-copy", "marketing-copy", "marketing"),
        ("technical-blog", "technical-blog", "technical"),
        ("wechat-basic", "wechat-basic", "wechat"),
        ("wechat-article", "wechat-article", "wechat"),
        ("wechat-strict", "wechat-strict", "wechat"),
    ],
)
def test_cli_profile_init_creates_valid_profile(
    template_name: str,
    expected_name: str,
    expected_platform: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_path = tmp_path / f"{template_name}.yaml"

    exit_code = main(
        [
            "profile",
            "init",
            "--template",
            template_name,
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert output_path.exists()
    assert "Profile created." in captured.out
    assert f"Template: {template_name}" in captured.out
    assert f"Output: {output_path}" in captured.out
    assert captured.err == ""

    profile = load_profile(output_path)
    assert profile.name == expected_name
    assert profile.target_platform == expected_platform

    validate_exit_code = main(["profile", "validate", str(output_path)])
    validate_captured = capsys.readouterr()

    assert validate_exit_code == 0
    assert "Profile validation passed." in validate_captured.out
    assert f"Path: {output_path}" in validate_captured.out
    assert validate_captured.err == ""


def test_cli_profile_init_unknown_template_returns_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_path = tmp_path / "profile.yaml"

    exit_code = main(
        [
            "profile",
            "init",
            "--template",
            "unknown",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "invalid choice" in captured.err
    assert "general-basic" in captured.err
    assert "general-publishing" in captured.err
    assert "health-content" in captured.err
    assert "marketing-copy" in captured.err
    assert "technical-blog" in captured.err
    assert "wechat-basic" in captured.err
    assert "wechat-article" in captured.err
    assert "wechat-strict" in captured.err
    assert captured.out == ""
    assert not output_path.exists()


def test_profile_template_registry_matches_init_and_templates_validate(
    tmp_path: Path,
) -> None:
    templates = list_profile_templates()

    assert [template.name for template in templates] == list_profile_template_names()

    for template in templates:
        fetched_template = get_profile_template(template.name)
        assert fetched_template == template

        output_path = tmp_path / f"{template.name}.yaml"
        exit_code = main(
            [
                "profile",
                "init",
                "--template",
                template.name,
                "--output",
                str(output_path),
            ]
        )

        assert exit_code == 0
        profile = load_profile(output_path)
        assert profile.name == template.name
        assert validate_profile(output_path).valid is True


def test_cli_profile_init_existing_file_fails_without_force(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_path = tmp_path / "existing.yaml"
    output_path.write_text("original", encoding="utf-8")

    exit_code = main(
        [
            "profile",
            "init",
            "--template",
            "wechat-basic",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Output file already exists" in captured.err
    assert "Use --force to overwrite." in captured.err
    assert captured.out == ""
    assert output_path.read_text(encoding="utf-8") == "original"


def test_cli_profile_init_force_overwrites_existing_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_path = tmp_path / "existing.yaml"
    output_path.write_text("original", encoding="utf-8")

    exit_code = main(
        [
            "profile",
            "init",
            "--template",
            "wechat-strict",
            "--output",
            str(output_path),
            "--force",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Profile created." in captured.out
    assert captured.err == ""
    assert "name: wechat-strict" in output_path.read_text(encoding="utf-8")


def test_cli_profile_init_missing_parent_directory_returns_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_path = tmp_path / "missing-dir" / "profile.yaml"

    exit_code = main(
        [
            "profile",
            "init",
            "--template",
            "wechat-basic",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Parent directory does not exist" in captured.err
    assert captured.out == ""
    assert not output_path.exists()


def test_cli_profile_validate_valid_profile_returns_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile_path = "tests/fixtures/profiles/absolute_claims.yml"

    exit_code = main(["profile", "validate", profile_path])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Profile validation passed." in captured.out
    assert f"Path: {profile_path}" in captured.out
    assert "Name: absolute-claims" in captured.out
    assert "Target Platform: wechat" in captured.out
    assert "Enabled Rules: 1" in captured.out
    assert "Disabled Rules: 0" in captured.out
    assert "- absolute_claims" in captured.out
    assert captured.err == ""


def test_cli_profile_validate_valid_profile_json_output_returns_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile_path = "tests/fixtures/profiles/absolute_claims.yml"

    exit_code = main(["profile", "validate", profile_path, "--format", "json"])

    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["schema_version"] == "profile-validation-result.v1"
    assert payload["valid"] is True
    assert payload["path"] == profile_path
    assert payload["profile"]["name"] == "absolute-claims"
    assert payload["profile"]["target_platform"] == "wechat"
    assert payload["profile"]["enabled_rule_count"] == 1
    assert payload["profile"]["disabled_rule_count"] == 0
    assert payload["profile"]["rules"] == [
        {
            "id": "absolute_claims",
            "enabled": True,
            "severity": "error",
        }
    ]
    assert payload["errors"] == []
    assert captured.err == ""


@pytest.mark.parametrize(
    ("profile_path", "profile_name"),
    [
        ("profiles/examples/general-basic.yaml", "general-basic"),
        ("profiles/examples/wechat-basic.yaml", "wechat-basic"),
        ("profiles/examples/wechat-strict.yaml", "wechat-strict"),
    ],
)
def test_cli_profile_validate_example_profiles_return_zero(
    profile_path: str,
    profile_name: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["profile", "validate", profile_path])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Profile validation passed." in captured.out
    assert f"Path: {profile_path}" in captured.out
    assert f"Name: {profile_name}" in captured.out
    assert "Enabled Rules: 2" in captured.out
    assert "- forbidden_terms" in captured.out
    assert "- absolute_claims" in captured.out
    assert captured.err == ""


def test_cli_profile_validate_missing_profile_returns_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_path = tmp_path / "missing.yaml"

    exit_code = main(["profile", "validate", str(missing_path)])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert f"Profile validation failed: {missing_path}" in captured.out
    assert "Issues: 1" in captured.out
    assert "1. <file>" in captured.out
    assert "Code: file_not_found" in captured.out
    assert "Profile file not found" in captured.out
    assert captured.err == ""


def test_cli_profile_validate_invalid_yaml_returns_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile_path = tmp_path / "invalid.yaml"
    profile_path.write_text("name: [wechat", encoding="utf-8")

    exit_code = main(["profile", "validate", str(profile_path)])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert f"Profile validation failed: {profile_path}" in captured.out
    assert "Issues: 1" in captured.out
    assert "1. <yaml>" in captured.out
    assert "Code: invalid_yaml" in captured.out
    assert "Failed to parse YAML profile:" in captured.out
    assert "Suggestion: Check indentation, quoting, and list structure." in captured.out
    assert captured.err == ""


def test_cli_profile_validate_unknown_rule_returns_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile_path = tmp_path / "unknown-rule.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: custom",
                "target_platform: wechat",
                "rules:",
                "  - id: unknown_rule",
                "    enabled: true",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["profile", "validate", str(profile_path)])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert f"Profile validation failed: {profile_path}" in captured.out
    assert "Issues: 1" in captured.out
    assert "1. rules[0].id" in captured.out
    assert "Code: unknown_rule_id" in captured.out
    assert "Unknown rule ID: unknown_rule." in captured.out
    assert captured.err == ""


def test_cli_profile_validate_invalid_terms_returns_two_and_json_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile_path = tmp_path / "invalid-terms.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: custom",
                "target_platform: wechat",
                "rules:",
                "  - id: absolute_claims",
                "    enabled: true",
                "    terms: 全网最强",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["profile", "validate", str(profile_path), "--format", "json"])

    captured = capsys.readouterr()

    assert exit_code == 2
    payload = json.loads(captured.out)
    assert payload["schema_version"] == "profile-validation-result.v1"
    assert payload["valid"] is False
    assert payload["path"] == str(profile_path)
    assert payload["profile"] is None
    assert payload["errors"] == [
        {
            "path": "absolute_claims.terms",
            "code": "invalid_string_list",
            "message": "absolute_claims.terms must be a list of strings.",
            "suggestion": "Use a YAML list of strings.",
        }
    ]
    assert captured.err == ""


def test_cli_profile_validate_renders_structured_issue_list(
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile_path = "tests/fixtures/profiles/invalid/invalid-regex-pattern.yaml"

    exit_code = main(["profile", "validate", profile_path])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert f"Profile validation failed: {profile_path}" in captured.out
    assert "Issues: 1" in captured.out
    assert "1. regex_rules[0].pattern" in captured.out
    assert "Code: invalid_regex_pattern" in captured.out
    assert "Error: Invalid regex pattern:" in captured.out
    assert "Suggestion: Check the regex syntax or escape special characters." in captured.out
    assert "Traceback" not in captured.out
    assert captured.err == ""


def test_cli_profile_validate_renders_multiple_issues_without_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile_path = tmp_path / "multiple-issues.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: multi-issue",
                "target_platform: wechat",
                "regex_rules:",
                "  - id: 123_rule",
                '    pattern: "["',
                "    severity: warn",
                '    message: "   "',
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["profile", "validate", str(profile_path)])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert f"Profile validation failed: {profile_path}" in captured.out
    assert "Issues: 4" in captured.out
    assert "regex_rules[0].id" in captured.out
    assert "regex_rules[0].pattern" in captured.out
    assert "regex_rules[0].severity" in captured.out
    assert "regex_rules[0].message" in captured.out
    assert "Traceback" not in captured.out
    assert captured.err == ""


def test_cli_review_with_invalid_profile_fails_cleanly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/invalid/invalid-regex-pattern.yaml"

    exit_code = main(["review", markdown_path, "--profile", profile_path])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert f"Profile validation failed: {profile_path}" in captured.err
    assert "Code: invalid_regex_pattern" in captured.err
    assert "Traceback" not in captured.err


def test_cli_batch_with_invalid_profile_fails_cleanly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile_path = "tests/fixtures/profiles/invalid/invalid-case-sensitive.yaml"

    exit_code = main(
        [
            "batch",
            "examples/batch/articles",
            "--profile",
            profile_path,
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert f"Profile validation failed: {profile_path}" in captured.err
    assert "Code: invalid_boolean" in captured.err
    assert "Traceback" not in captured.err


def test_cli_review_json_output_uses_canonical_review_result(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/forbidden_terms_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["schema_version"] == "review-result.v1"
    assert payload["summary"]["finding_count"] == 1
    assert payload["summary"]["severity_counts"] == {
        "info": 0,
        "warning": 1,
        "error": 0,
        "critical": 0,
    }
    assert payload["document"]["path"] == markdown_path
    assert payload["profile"] == {
        "name": "default",
        "path": profile_path,
    }
    finding = payload["findings"][0]
    assert finding["rule_id"] == "forbidden_terms"
    location = finding["location"]
    assert location["start_line"] == 1
    assert location["start_column"] == 8
    assert location["matched_text"] == "绝对安全"
    assert "Context:" not in captured.out
    assert captured.err == ""


def test_cli_review_json_output_supports_markdown_structure_rule(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/markdown_structure_issues.md"
    profile_path = "tests/fixtures/profiles/markdown_structure.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["schema_version"] == "review-result.v1"
    assert payload["summary"]["finding_count"] == 4
    assert payload["summary"]["severity_counts"] == {
        "info": 0,
        "warning": 4,
        "error": 0,
        "critical": 0,
    }
    assert payload["profile"] == {
        "name": "markdown-structure",
        "path": profile_path,
    }
    assert {finding["rule_id"] for finding in payload["findings"]} == {
        "markdown_structure"
    }
    assert payload["findings"][0]["message"] == "Heading level jumps from H1 to H3."
    assert payload["findings"][0]["location"]["start_line"] == 3
    assert payload["findings"][1]["message"] == "Empty heading detected."
    assert payload["findings"][1]["location"]["start_line"] == 5
    assert payload["findings"][3]["message"].startswith(
        "Paragraph exceeds maximum length ("
    )
    assert captured.err == ""


def test_cli_review_json_output_supports_markdown_links_images_rule(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/markdown_links_images_issues.md"
    profile_path = "tests/fixtures/profiles/markdown_links_images.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["schema_version"] == "review-result.v1"
    assert payload["summary"]["finding_count"] == 6
    assert payload["summary"]["severity_counts"] == {
        "info": 0,
        "warning": 6,
        "error": 0,
        "critical": 0,
    }
    assert payload["profile"] == {
        "name": "markdown-links-images",
        "path": profile_path,
    }
    assert {finding["rule_id"] for finding in payload["findings"]} == {
        "markdown_links_images"
    }
    assert payload["findings"][0]["message"] == "链接文本为空。"
    assert payload["findings"][0]["location"]["start_line"] == 1
    assert payload["findings"][1]["message"] == "链接目标为空。"
    assert payload["findings"][2]["message"] == "链接目标仍是占位符。"
    assert payload["findings"][3]["message"] == "图片 alt 文本为空。"
    assert payload["findings"][4]["message"] == "图片目标为空。"
    assert payload["findings"][5]["message"] == "图片目标仍是占位符。"
    assert captured.err == ""


def test_cli_review_json_output_supports_absolute_claims_rule(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/absolute_claims_article.md"
    profile_path = "tests/fixtures/profiles/absolute_claims.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["summary"]["finding_count"] == 1
    assert payload["summary"]["severity_counts"] == {
        "info": 0,
        "warning": 0,
        "error": 1,
        "critical": 0,
    }
    finding = payload["findings"][0]
    assert finding["rule_id"] == "absolute_claims"
    assert finding["severity"] == "error"
    assert finding["message"] == "发现可能存在绝对化表述：全网最强"
    assert "suggestion" in finding
    assert finding["location"]["start_line"] == 1
    assert captured.err == ""


def test_cli_review_markdown_stdout_includes_report_sections(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/forbidden_terms_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "markdown",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.startswith("# Content Review Report\n")
    assert "| File | `tests/fixtures/markdown/forbidden_terms_article.md` |" in captured.out
    assert "| Profile | `tests/fixtures/profiles/default.yml` |" in captured.out
    assert "| Total Findings | 1 |" in captured.out
    assert "| warning | 1 |" in captured.out
    assert "| forbidden_terms | 1 |" in captured.out
    assert "| warning | forbidden_terms | 1 | 8 | 发现风险词：绝对安全 | - |" in captured.out
    assert "- Context: # 测试文章 绝对安全" in captured.out
    assert "- Matched Text: `绝对安全`" in captured.out
    assert captured.err == ""


def test_cli_review_markdown_output_file_writes_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/forbidden_terms_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    output_path = tmp_path / "review-report.md"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "markdown",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    output_text = output_path.read_text(encoding="utf-8")
    assert output_text.startswith("# Content Review Report\n")
    assert "| File | `tests/fixtures/markdown/forbidden_terms_article.md` |" in output_text
    assert "| Profile | `tests/fixtures/profiles/default.yml` |" in output_text
    assert "| Total Findings | 1 |" in output_text
    assert "- Context: # 测试文章 绝对安全" in output_text
    assert "- Matched Text: `绝对安全`" in output_text


def test_cli_review_markdown_output_includes_quality_gate_section(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/forbidden_terms_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "markdown",
            "--fail-on",
            "warning",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "| Quality Gate | Failed |" in captured.out
    assert "| Fail On | `warning` |" in captured.out
    assert "| Matched Gate Findings | 1 |" in captured.out
    assert captured.err == ""


def test_cli_review_markdown_output_file_is_written_before_quality_gate_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/forbidden_terms_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    output_path = tmp_path / "review-report.md"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "markdown",
            "--fail-on",
            "warning",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == ""
    output_text = output_path.read_text(encoding="utf-8")
    assert "| Quality Gate | Failed |" in output_text
    assert "| Matched Gate Findings | 1 |" in output_text


def test_cli_review_output_write_failure_returns_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/forbidden_terms_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    output_path = tmp_path / "missing" / "review-report.md"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--format",
            "markdown",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error:" in captured.err


def test_cli_review_unknown_rule_returns_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/forbidden_terms_article.md"
    profile_path = tmp_path / "unknown-rule.yml"
    profile_path.write_text(
        "\n".join(
            [
                "name: custom",
                "target_platform: wechat",
                "enabled_rules:",
                "  - missing_rule",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["review", markdown_path, "--profile", str(profile_path)])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: Unknown rule ID: missing_rule" in captured.err
    assert captured.out == ""


def test_cli_batch_text_output_prints_summary_and_file_sections(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Batch review completed." in captured.out
    assert "Files discovered: 3" in captured.out
    assert "Files reviewed: 3" in captured.out
    assert "Files with findings: 2" in captured.out
    assert "Findings: 2" in captured.out
    assert "[tests/fixtures/batch/articles/clean.md] Findings: 0" in captured.out
    assert "[tests/fixtures/batch/articles/forbidden.md] Findings: 1" in captured.out
    assert "[tests/fixtures/batch/articles/nested/nested_forbidden.md] Findings: 1" in captured.out
    assert "No issues found." in captured.out
    assert "[warning] forbidden_terms - 发现风险词：绝对安全" in captured.out
    assert captured.err == ""


def test_cli_batch_preserves_success_exit_code_without_fail_on(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 2" in captured.out
    assert captured.err == ""


def test_cli_review_absolute_claims_fail_on_exits_one(
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/absolute_claims_article.md"
    profile_path = "tests/fixtures/profiles/absolute_claims.yml"

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--fail-on",
            "error",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "[error] absolute_claims: 发现可能存在绝对化表述：全网最强" in captured.out
    assert "Suggestion:" in captured.out
    assert captured.err == ""


def test_cli_review_suppressed_absolute_claims_does_not_fail_quality_gate(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = tmp_path / "suppressed-absolute-claims.md"
    markdown_path.write_text(
        "这是一款全网最强的工具。 <!-- content-review-disable-line absolute_claims -->",
        encoding="utf-8",
    )
    profile_path = "tests/fixtures/profiles/absolute_claims.yml"

    exit_code = main(
        [
            "review",
            str(markdown_path),
            "--profile",
            profile_path,
            "--fail-on",
            "error",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 0" in captured.out
    assert "全网最强" not in captured.out
    assert captured.err == ""


def test_cli_batch_fail_on_exits_zero_when_findings_are_below_threshold(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--fail-on",
            "error",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 2" in captured.out
    assert captured.err == ""


def test_cli_batch_fail_on_exits_one_when_findings_meet_threshold(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--fail-on",
            "warning",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Findings: 2" in captured.out
    assert captured.err == ""


def test_cli_batch_suppressed_finding_does_not_fail_quality_gate(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = tmp_path / "articles"
    input_dir.mkdir()
    (input_dir / "suppressed.md").write_text(
        "\n".join(
            [
                "<!-- content-review-disable-next-line forbidden_terms -->",
                "这里写着绝对安全。",
            ]
        ),
        encoding="utf-8",
    )
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            str(input_dir),
            "--profile",
            profile_path,
            "--fail-on",
            "warning",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Files with findings: 0" in captured.out
    assert "Findings: 0" in captured.out
    assert "绝对安全" not in captured.out
    assert captured.err == ""


def test_cli_batch_absolute_claims_fail_on_exits_one(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = tmp_path / "articles"
    input_dir.mkdir()
    (input_dir / "claims.md").write_text("这是一款全网最强的工具。", encoding="utf-8")
    profile_path = "tests/fixtures/profiles/absolute_claims.yml"

    exit_code = main(
        [
            "batch",
            str(input_dir),
            "--profile",
            profile_path,
            "--fail-on",
            "error",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Files with findings: 1" in captured.out
    assert "[error] absolute_claims - 发现可能存在绝对化表述：全网最强" in captured.out
    assert captured.err == ""


def test_cli_batch_suppressed_absolute_claims_does_not_fail_quality_gate(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = tmp_path / "articles"
    input_dir.mkdir()
    (input_dir / "suppressed.md").write_text(
        "\n".join(
            [
                "<!-- content-review-disable-next-line absolute_claims -->",
                "这是一款全网最强的工具。",
            ]
        ),
        encoding="utf-8",
    )
    profile_path = "tests/fixtures/profiles/absolute_claims.yml"

    exit_code = main(
        [
            "batch",
            str(input_dir),
            "--profile",
            profile_path,
            "--fail-on",
            "error",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Files with findings: 0" in captured.out
    assert "Findings: 0" in captured.out
    assert "全网最强" not in captured.out
    assert captured.err == ""


def test_cli_batch_fail_on_rejects_invalid_severity(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--fail-on",
            "high",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Invalid severity: 'high'" in captured.err
    assert captured.out == ""


def test_cli_batch_json_output_uses_canonical_batch_result(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["schema_version"] == "batch-review-result.v1"
    assert payload["summary"] == {
        "file_count": 3,
        "reviewed_count": 3,
        "finding_count": 2,
        "files_with_findings": 2,
        "severity_counts": {
            "info": 0,
            "warning": 2,
            "error": 0,
            "critical": 0,
        },
    }
    assert [item["document"]["path"] for item in payload["results"]] == [
        "tests/fixtures/batch/articles/clean.md",
        "tests/fixtures/batch/articles/forbidden.md",
        "tests/fixtures/batch/articles/nested/nested_forbidden.md",
    ]
    assert payload["results"][1]["findings"][0]["location"]["matched_text"] == "绝对安全"
    assert captured.err == ""


def test_cli_batch_enable_llm_writes_mock_sidecars_without_changing_batch_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"
    review_output_path = tmp_path / "batch.json"
    llm_output_dir = tmp_path / "llm-sidecars"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--format",
            "json",
            "--output",
            str(review_output_path),
            "--enable-llm",
            "--llm-output-dir",
            str(llm_output_dir),
        ]
    )

    captured = capsys.readouterr()
    review_payload = json.loads(review_output_path.read_text(encoding="utf-8"))
    clean_sidecar = llm_output_dir / "clean.md.llm-review.json"
    forbidden_sidecar = llm_output_dir / "forbidden.md.llm-review.json"
    nested_sidecar = llm_output_dir / "nested" / "nested_forbidden.md.llm-review.json"
    manifest_sidecar = llm_output_dir / "llm-review-manifest.json"

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert review_payload["schema_version"] == "batch-review-result.v1"
    assert "llm_review" not in review_payload
    assert clean_sidecar.exists()
    assert forbidden_sidecar.exists()
    assert nested_sidecar.exists()
    assert manifest_sidecar.exists()
    assert json.loads(clean_sidecar.read_text(encoding="utf-8")) == {
        "schema_version": "llm-sidecar-result.v1",
        "summary": {
            "file_count": 1,
            "succeeded_count": 1,
            "failed_count": 0,
            "skipped_count": 0,
            "finding_count": 0,
        },
        "files": [
            {
                "path": "tests/fixtures/batch/articles/clean.md",
                "status": "success",
                "finding_count": 0,
                "review": {
                    "schema_version": "llm-review-result.v1",
                    "findings": [],
                },
            }
        ],
    }
    assert json.loads(forbidden_sidecar.read_text(encoding="utf-8")) == {
        "schema_version": "llm-sidecar-result.v1",
        "summary": {
            "file_count": 1,
            "succeeded_count": 1,
            "failed_count": 0,
            "skipped_count": 0,
            "finding_count": 0,
        },
        "files": [
            {
                "path": "tests/fixtures/batch/articles/forbidden.md",
                "status": "success",
                "finding_count": 0,
                "review": {
                    "schema_version": "llm-review-result.v1",
                    "findings": [],
                },
            }
        ],
    }
    assert json.loads(nested_sidecar.read_text(encoding="utf-8")) == {
        "schema_version": "llm-sidecar-result.v1",
        "summary": {
            "file_count": 1,
            "succeeded_count": 1,
            "failed_count": 0,
            "skipped_count": 0,
            "finding_count": 0,
        },
        "files": [
            {
                "path": "tests/fixtures/batch/articles/nested/nested_forbidden.md",
                "status": "success",
                "finding_count": 0,
                "review": {
                    "schema_version": "llm-review-result.v1",
                    "findings": [],
                },
            }
        ],
    }
    assert json.loads(manifest_sidecar.read_text(encoding="utf-8")) == {
        "schema_version": "llm-sidecar-result.v1",
        "summary": {
            "file_count": 3,
            "succeeded_count": 3,
            "failed_count": 0,
            "skipped_count": 0,
            "finding_count": 0,
        },
        "files": [
            {
                "path": "tests/fixtures/batch/articles/clean.md",
                "status": "success",
                "finding_count": 0,
                "review": {
                    "schema_version": "llm-review-result.v1",
                    "findings": [],
                },
            },
            {
                "path": "tests/fixtures/batch/articles/forbidden.md",
                "status": "success",
                "finding_count": 0,
                "review": {
                    "schema_version": "llm-review-result.v1",
                    "findings": [],
                },
            },
            {
                "path": "tests/fixtures/batch/articles/nested/nested_forbidden.md",
                "status": "success",
                "finding_count": 0,
                "review": {
                    "schema_version": "llm-review-result.v1",
                    "findings": [],
                },
            },
        ],
    }


def test_cli_batch_enable_llm_preserves_relative_sidecar_paths_for_recursive_input(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"
    llm_output_dir = tmp_path / "llm-sidecars"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--enable-llm",
            "--llm-output-dir",
            str(llm_output_dir),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert (llm_output_dir / "clean.md.llm-review.json").exists()
    assert (llm_output_dir / "forbidden.md.llm-review.json").exists()
    assert (llm_output_dir / "nested" / "nested_forbidden.md.llm-review.json").exists()


def test_cli_batch_markdown_output_does_not_include_llm_section_when_llm_is_enabled(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"
    llm_output_dir = tmp_path / "llm-sidecars"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--format",
            "markdown",
            "--enable-llm",
            "--llm-output-dir",
            str(llm_output_dir),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "## LLM Review" not in captured.out
    assert captured.err == ""


def test_cli_batch_enable_llm_requires_llm_output_dir(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--enable-llm",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --enable-llm requires --llm-output-dir" in captured.err


def test_cli_batch_llm_output_dir_requires_enable_llm(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--llm-output-dir",
            str(tmp_path / "llm-sidecars"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --llm-output-dir requires --enable-llm" in captured.err


def test_cli_batch_llm_provider_without_enable_llm_does_not_affect_deterministic_review(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--llm-provider",
            "mock",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Batch review completed." in captured.out
    assert captured.err == ""


def test_cli_batch_llm_model_without_enable_llm_does_not_affect_deterministic_review(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--llm-model",
            "gpt-4o-mini",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Batch review completed." in captured.out
    assert captured.err == ""


def test_cli_batch_llm_api_key_env_without_enable_llm_does_not_affect_deterministic_review(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--llm-api-key-env",
            "OPENAI_API_KEY",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Batch review completed." in captured.out
    assert captured.err == ""


def test_cli_batch_llm_base_url_without_enable_llm_does_not_affect_deterministic_review(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--llm-base-url",
            "https://example.com/v1",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Batch review completed." in captured.out
    assert captured.err == ""


def test_cli_batch_llm_timeout_without_enable_llm_does_not_affect_deterministic_review(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--llm-timeout-seconds",
            "9",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Batch review completed." in captured.out
    assert captured.err == ""


def test_cli_batch_llm_markdown_output_requires_enable_llm(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--llm-markdown-output",
            str(tmp_path / "batch.llm.md"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --llm-markdown-output requires --enable-llm" in captured.err


def test_cli_batch_rejects_unsupported_llm_provider(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--enable-llm",
            "--llm-provider",
            "openai",
            "--llm-output-dir",
            str(tmp_path / "llm-sidecars"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "Error: Unknown LLM provider 'openai'. Supported providers: 'mock', 'pydanticai'."
        in captured.err
    )


def test_cli_batch_mock_provider_accepts_llm_model_and_api_key_env_config(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"
    llm_output_dir = tmp_path / "llm-sidecars"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--enable-llm",
            "--llm-provider",
            "mock",
            "--llm-model",
            "mock-model",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-base-url",
            "https://example.com/v1",
            "--llm-output-dir",
            str(llm_output_dir),
        ]
    )

    captured = capsys.readouterr()
    llm_payload = json.loads(
        (llm_output_dir / "clean.md.llm-review.json").read_text(encoding="utf-8")
    )

    assert exit_code == 0
    assert captured.err == ""
    assert llm_payload["files"][0]["status"] == "success"


def test_cli_batch_pydanticai_provider_writes_sidecars_and_markdown_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"
    batch_output_path = tmp_path / "batch.json"
    llm_output_dir = tmp_path / "llm-sidecars"
    llm_markdown_output_path = tmp_path / "batch.llm.md"

    monkeypatch.setenv("CONTENT_REVIEW_TEST_LLM_API_KEY", "test-secret-value")
    captured_agent_kwargs: dict[str, object] = {}
    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.build_pydanticai_runtime_agent",
        lambda **kwargs: captured_agent_kwargs.update(kwargs) or object(),
    )
    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.run_pydanticai_runtime_agent",
        lambda _agent, _payload: {
            "findings": [
                {
                    "rule_id": "llm_semantic_risk",
                    "severity": "warning",
                    "message": "Possible unsupported claim.",
                }
            ]
        },
    )

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--format",
            "json",
            "--output",
            str(batch_output_path),
            "--fail-on",
            "error",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "gpt-4o-mini",
            "--llm-api-key-env",
            "CONTENT_REVIEW_TEST_LLM_API_KEY",
            "--llm-timeout-seconds",
            "18",
            "--llm-output-dir",
            str(llm_output_dir),
            "--llm-markdown-output",
            str(llm_markdown_output_path),
        ]
    )

    captured = capsys.readouterr()
    batch_payload = json.loads(batch_output_path.read_text(encoding="utf-8"))
    clean_payload = json.loads(
        (llm_output_dir / "clean.md.llm-review.json").read_text(encoding="utf-8")
    )
    manifest_payload = json.loads(
        (llm_output_dir / "llm-review-manifest.json").read_text(encoding="utf-8")
    )
    markdown_report = llm_markdown_output_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert batch_payload["schema_version"] == "batch-review-result.v1"
    assert manifest_payload["summary"]["succeeded_count"] == 3
    assert manifest_payload["summary"]["finding_count"] == 3
    assert clean_payload["files"][0]["status"] == "success"
    assert clean_payload["files"][0]["review"]["provider"] == "pydanticai"
    assert markdown_report.startswith("# Batch LLM Sidecar Review Report\n")
    assert "llm_semantic_risk" in markdown_report
    assert "test-secret-value" not in markdown_report
    assert captured_agent_kwargs["timeout_seconds"] == 18.0


def test_cli_batch_llm_markdown_output_writes_batch_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"
    llm_output_dir = tmp_path / "llm-sidecars"
    llm_markdown_output_path = tmp_path / "batch.llm.md"

    from content_review_engine.llm import LLMProviderError, LLMReviewFinding, LLMReviewResult

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self
        if Path(request.content_path).name == "forbidden.md":
            raise LLMProviderError("mock provider failure")
        return LLMReviewResult(
            findings=(
                LLMReviewFinding(
                    rule_id="llm_semantic_risk",
                    severity="warning",
                    message=f"Finding for {Path(request.content_path).name}.",
                ),
            )
        )

    monkeypatch.setattr("content_review_engine.llm.mock.MockLLMReviewer.review", fake_review)

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--enable-llm",
            "--llm-output-dir",
            str(llm_output_dir),
            "--llm-markdown-output",
            str(llm_markdown_output_path),
        ]
    )

    captured = capsys.readouterr()
    markdown_report = llm_markdown_output_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert captured.err == ""
    assert markdown_report.startswith("# Batch LLM Sidecar Review Report\n")
    assert "| Files | 3 |" in markdown_report
    assert "| Succeeded | 2 |" in markdown_report
    assert "| Failed | 1 |" in markdown_report
    assert "| tests/fixtures/batch/articles/forbidden.md | failed | 0 | LLMProviderError: mock provider failure |" in markdown_report
    assert "Finding for clean.md." in markdown_report
    assert "Finding for nested_forbidden.md." in markdown_report
    assert "LLM review failed." in markdown_report


def test_cli_batch_quality_gate_ignores_llm_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = tmp_path / "articles"
    input_dir.mkdir()
    (input_dir / "clean.md").write_text("正常内容。", encoding="utf-8")
    profile_path = "tests/fixtures/batch/profile.yml"
    llm_output_dir = tmp_path / "llm-sidecars"

    from content_review_engine.llm import LLMReviewFinding, LLMReviewResult

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self, request
        return LLMReviewResult(
            findings=(
                LLMReviewFinding(
                    rule_id="llm_critical_issue",
                    severity="critical",
                    message="Critical semantic issue.",
                ),
            )
        )

    monkeypatch.setattr("content_review_engine.llm.mock.MockLLMReviewer.review", fake_review)

    exit_code = main(
        [
            "batch",
            str(input_dir),
            "--profile",
            profile_path,
            "--fail-on",
            "warning",
            "--enable-llm",
            "--llm-output-dir",
            str(llm_output_dir),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Files with findings: 0" in captured.out
    assert "Findings: 0" in captured.out
    assert captured.err == ""


def test_cli_batch_llm_partial_failure_writes_manifest_and_keeps_deterministic_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"
    llm_output_dir = tmp_path / "llm-sidecars"

    from content_review_engine.llm import LLMProviderError, LLMReviewResult

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self
        if Path(request.content_path).name == "forbidden.md":
            raise LLMProviderError("mock provider failure")
        return LLMReviewResult()

    monkeypatch.setattr("content_review_engine.llm.mock.MockLLMReviewer.review", fake_review)

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--enable-llm",
            "--llm-output-dir",
            str(llm_output_dir),
        ]
    )

    captured = capsys.readouterr()
    manifest_payload = json.loads(
        (llm_output_dir / "llm-review-manifest.json").read_text(encoding="utf-8")
    )
    failed_sidecar_payload = json.loads(
        (llm_output_dir / "forbidden.md.llm-review.json").read_text(encoding="utf-8")
    )

    assert exit_code == 0
    assert "Files discovered: 3" in captured.out
    assert "Files with findings: 2" in captured.out
    assert "Findings: 2" in captured.out
    assert captured.err == ""
    assert manifest_payload["summary"] == {
        "file_count": 3,
        "succeeded_count": 2,
        "failed_count": 1,
        "skipped_count": 0,
        "finding_count": 0,
    }
    assert manifest_payload["files"] == [
        {
            "path": "tests/fixtures/batch/articles/clean.md",
            "status": "success",
            "finding_count": 0,
            "review": {
                "schema_version": "llm-review-result.v1",
                "findings": [],
            },
        },
        {
            "path": "tests/fixtures/batch/articles/forbidden.md",
            "status": "failed",
            "finding_count": 0,
            "error": {
                "error_type": "LLMProviderError",
                "message": "mock provider failure",
            },
        },
        {
            "path": "tests/fixtures/batch/articles/nested/nested_forbidden.md",
            "status": "success",
            "finding_count": 0,
            "review": {
                "schema_version": "llm-review-result.v1",
                "findings": [],
            },
        },
    ]
    assert failed_sidecar_payload["files"] == [
        {
            "path": "tests/fixtures/batch/articles/forbidden.md",
            "status": "failed",
            "finding_count": 0,
            "error": {
                "error_type": "LLMProviderError",
                "message": "mock provider failure",
            },
        }
    ]


def test_cli_batch_llm_partial_timeout_failure_is_recorded_in_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"
    llm_output_dir = tmp_path / "llm-sidecars"

    from content_review_engine.llm import LLMProviderTimeoutError, LLMReviewResult

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self
        if Path(request.content_path).name == "forbidden.md":
            raise LLMProviderTimeoutError("PydanticAI runtime request timed out.")
        return LLMReviewResult()

    monkeypatch.setattr("content_review_engine.llm.mock.MockLLMReviewer.review", fake_review)

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--enable-llm",
            "--llm-output-dir",
            str(llm_output_dir),
            "--llm-timeout-seconds",
            "7",
        ]
    )

    captured = capsys.readouterr()
    manifest_payload = json.loads(
        (llm_output_dir / "llm-review-manifest.json").read_text(encoding="utf-8")
    )

    assert exit_code == 0
    assert "Batch review completed." in captured.out
    assert captured.err == ""
    assert manifest_payload["files"][1]["error"] == {
        "error_type": "LLMProviderTimeoutError",
        "message": "PydanticAI runtime request timed out.",
    }


def test_cli_batch_llm_markdown_output_does_not_change_deterministic_markdown_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"
    llm_output_dir = tmp_path / "llm-sidecars"
    llm_markdown_output_path = tmp_path / "batch.llm.md"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--format",
            "markdown",
            "--enable-llm",
            "--llm-output-dir",
            str(llm_output_dir),
            "--llm-markdown-output",
            str(llm_markdown_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "# Batch Content Review Report" in captured.out
    assert "## LLM Review" not in captured.out
    assert "Batch LLM Sidecar Review Report" in llm_markdown_output_path.read_text(
        encoding="utf-8"
    )


def test_cli_batch_sidecar_write_failure_returns_friendly_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"
    output_path = tmp_path / "batch.txt"
    original_write_text = Path.write_text

    def fail_write_text(self, data: str, encoding: str | None = None) -> int:
        if self.name.endswith(".llm-review.json"):
            raise OSError("disk full")
        return original_write_text(self, data, encoding=encoding)

    monkeypatch.setattr(Path, "write_text", fail_write_text)

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--output",
            str(output_path),
            "--enable-llm",
            "--llm-output-dir",
            str(tmp_path / "llm-sidecars"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: Failed to write LLM sidecar:" in captured.err
    assert "disk full" in captured.err


def test_cli_batch_markdown_output_includes_report_sections(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--format",
            "markdown",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.startswith("# Batch Content Review Report\n")
    assert "## Summary" in captured.out
    assert "| Files Discovered | 3 |" in captured.out
    assert "| Files With Findings | 2 |" in captured.out
    assert "### `tests/fixtures/batch/articles/clean.md`" in captured.out
    assert "### `tests/fixtures/batch/articles/forbidden.md`" in captured.out
    assert "### `tests/fixtures/batch/articles/nested/nested_forbidden.md`" in captured.out
    assert "No findings." in captured.out
    assert captured.err == ""


def test_cli_batch_markdown_output_file_writes_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"
    output_path = tmp_path / "batch-report.md"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--format",
            "markdown",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    output_text = output_path.read_text(encoding="utf-8")
    assert output_text.startswith("# Batch Content Review Report\n")
    assert "### `tests/fixtures/batch/articles/clean.md`" in output_text
    assert "### `tests/fixtures/batch/articles/forbidden.md`" in output_text
    assert "### `tests/fixtures/batch/articles/nested/nested_forbidden.md`" in output_text
    assert "No findings." in output_text


def test_cli_batch_markdown_output_includes_quality_gate_section(
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--format",
            "markdown",
            "--fail-on",
            "warning",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "| Quality Gate | Failed |" in captured.out
    assert "| Fail On | `warning` |" in captured.out
    assert "| Matched Gate Findings | 2 |" in captured.out
    assert captured.err == ""


def test_cli_batch_markdown_output_file_is_written_before_quality_gate_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"
    output_path = tmp_path / "batch-report.md"

    exit_code = main(
        [
            "batch",
            input_dir,
            "--profile",
            profile_path,
            "--recursive",
            "--format",
            "markdown",
            "--fail-on",
            "warning",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == ""
    output_text = output_path.read_text(encoding="utf-8")
    assert "| Quality Gate | Failed |" in output_text
    assert "| Matched Gate Findings | 2 |" in output_text


def test_cli_batch_invalid_input_directory_returns_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    invalid_input = tmp_path / "not-a-directory.md"
    invalid_input.write_text("content", encoding="utf-8")

    exit_code = main(
        [
            "batch",
            str(invalid_input),
            "--profile",
            "tests/fixtures/batch/profile.yml",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: Input path is not a directory" in captured.err
    assert captured.out == ""


def test_console_script_entrypoint_is_exposed() -> None:
    console_scripts = entry_points(group="console_scripts")
    content_review_entrypoints = [
        entry_point
        for entry_point in console_scripts
        if entry_point.name == "content-review"
    ]

    assert content_review_entrypoints, "content-review console script is missing"
    assert content_review_entrypoints[0].value == "content_review_engine.cli:main"
