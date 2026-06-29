from __future__ import annotations

import json
from importlib.metadata import entry_points
from pathlib import Path

import pytest

from content_review_engine.llm import LLMReviewResult
from content_review_engine.cli import build_parser, main
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
    assert "llm_provider" not in review_payload
    assert llm_payload == {
        "schema_version": "llm-review-result.v1",
        "findings": [],
    }


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
    assert llm_payload == {
        "schema_version": "llm-review-result.v1",
        "findings": [],
    }
    assert captured.err == ""


def test_cli_review_include_llm_report_is_not_supported(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--format",
            "markdown",
            "--enable-llm",
            "--llm-output",
            str(tmp_path / "review.llm.json"),
            "--include-llm-report",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "Error: --include-llm-report is not supported for single-file LLM review"
        in captured.err
    )


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
    assert (
        "Error: --include-llm-report is not supported for single-file LLM review"
        in captured.err
    )


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
    assert (
        "Error: --include-llm-report is not supported for single-file LLM review"
        in captured.err
    )


def test_cli_review_llm_failure_returns_error_without_writing_sidecar(
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

    assert exit_code == 2
    assert "Findings: 0" in captured.out
    assert "Error: provider temporarily unavailable" in captured.err
    assert not llm_output_path.exists()


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


def test_cli_review_enable_llm_requires_output_or_report(
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
    assert "Error: --enable-llm requires --llm-output or --llm-report" in captured.err


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


def test_cli_review_llm_report_requires_enable_llm(
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
            "--llm-report",
            str(tmp_path / "review.llm.md"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --llm-report requires --enable-llm" in captured.err


def test_cli_review_report_index_without_llm_writes_markdown_index(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report_index_path = tmp_path / "review.index.md"

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--report-index",
            str(report_index_path),
        ]
    )

    captured = capsys.readouterr()
    report = report_index_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "Review completed." in captured.out
    assert captured.err == ""
    assert "# Review Output Index" in report
    assert "| LLM Review | LLM not enabled |" in report
    assert "| Report Index | " in report


def test_cli_review_enable_llm_report_index_only_does_not_satisfy_llm_output_requirement(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--report-index",
            str(tmp_path / "review.index.md"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --enable-llm requires --llm-output or --llm-report" in captured.err


def test_cli_review_llm_provider_without_enable_llm_returns_clear_error(
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

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --llm-provider can only be used with --enable-llm" in captured.err


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


def test_cli_review_llm_retry_without_enable_llm_does_not_affect_deterministic_review(
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
            "--llm-retry-attempts",
            "2",
            "--llm-retry-backoff-seconds",
            "1.5",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 0" in captured.out
    assert captured.err == ""


def test_cli_review_llm_min_request_interval_without_enable_llm_does_not_affect_deterministic_review(
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
            "--llm-min-request-interval-seconds",
            "2.5",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 0" in captured.out
    assert captured.err == ""


def test_cli_review_llm_config_without_enable_llm_does_not_affect_deterministic_review(
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
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
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


def test_cli_review_rejects_invalid_llm_retry_attempts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--llm-retry-attempts",
            "-1",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "LLM retry attempts must be greater than or equal to 0." in captured.err


def test_cli_review_rejects_invalid_llm_retry_backoff_seconds(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--llm-retry-backoff-seconds",
            "-0.5",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "LLM retry backoff seconds must be greater than or equal to 0."
        in captured.err
    )


def test_cli_review_rejects_invalid_llm_min_request_interval_seconds(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--llm-min-request-interval-seconds",
            "-0.5",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "LLM minimum request interval seconds must be greater than or equal to 0."
        in captured.err
    )


def test_cli_review_parser_accepts_llm_retry_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "review",
            "article.md",
            "--profile",
            "profile.yml",
            "--llm-retry-attempts",
            "3",
            "--llm-retry-backoff-seconds",
            "2.5",
        ]
    )

    assert args.llm_retry_attempts == 3
    assert args.llm_retry_backoff_seconds == 2.5


def test_cli_review_parser_accepts_report_index_argument() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "review",
            "article.md",
            "--profile",
            "profile.yml",
            "--report-index",
            "review.index.md",
        ]
    )

    assert args.report_index == "review.index.md"


def test_cli_review_parser_accepts_llm_min_request_interval_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "review",
            "article.md",
            "--profile",
            "profile.yml",
            "--llm-min-request-interval-seconds",
            "2.5",
        ]
    )

    assert args.llm_min_request_interval_seconds == 2.5


def test_cli_review_parser_accepts_llm_config_argument() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "review",
            "article.md",
            "--profile",
            "profile.yml",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
        ]
    )

    assert args.llm_config == "examples/llm/pydanticai/llm-provider.yml"
    assert args.llm_retry_attempts is None
    assert args.llm_retry_backoff_seconds is None
    assert args.llm_min_request_interval_seconds is None


def test_cli_review_parser_accepts_single_file_sidecar_provider_argument() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "review",
            "article.md",
            "--profile",
            "profile.yml",
            "--llm-provider",
            "pydantic-ai-testmodel",
        ]
    )

    assert args.llm_provider == "pydantic-ai-testmodel"


def test_cli_batch_parser_accepts_sidecar_provider_argument() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "batch",
            "articles",
            "--profile",
            "profile.yml",
            "--llm-provider",
            "pydantic-ai-testmodel",
        ]
    )

    assert args.llm_provider == "pydantic-ai-testmodel"


def test_cli_llm_check_parser_accepts_live_and_llm_config_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "llm-check",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--live",
        ]
    )

    assert args.command == "llm-check"
    assert args.llm_config == "examples/llm/pydanticai/llm-provider.yml"
    assert args.live is True
    assert args.llm_retry_attempts is None
    assert args.llm_retry_backoff_seconds is None
    assert args.llm_min_request_interval_seconds is None


def test_cli_llm_check_parser_accepts_provider_argument() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "llm-check",
            "--provider",
            "pydantic-ai-testmodel",
            "--runtime",
        ]
    )

    assert args.command == "llm-check"
    assert args.provider == "pydantic-ai-testmodel"
    assert args.live is True


def test_cli_review_llm_report_flag_requires_enable_llm(
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
            "--llm-report",
            str(tmp_path / "review.llm.md"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --llm-report requires --enable-llm" in captured.err


def test_cli_review_rejects_reserved_real_llm_provider(
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
        "Error: Real LLM provider 'openai' is reserved but not implemented yet."
        in captured.err
    )
    assert not (tmp_path / "review.llm.json").exists()


def test_cli_review_pydanticai_requires_model_when_selected_explicitly(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-output",
            str(tmp_path / "review.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "Error: LLM provider 'pydanticai' requires --llm-model or llm-config model."
        in captured.err
    )
    assert not (tmp_path / "review.llm.json").exists()


def test_cli_review_mock_provider_still_works_without_llm_model(
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
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()
    llm_payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.err == ""
    assert llm_payload == {
        "schema_version": "llm-review-result.v1",
        "findings": [],
    }


def test_cli_review_explicit_provider_uses_create_llm_reviewer_name_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from content_review_engine.llm import LLMReviewResult

    captured_provider: dict[str, object] = {}

    class DummyReviewer:
        def review(self, request):  # type: ignore[no-untyped-def]
            del request
            return LLMReviewResult(provider="mock")

    def fake_create_llm_reviewer(provider):  # type: ignore[no-untyped-def]
        captured_provider["value"] = provider
        return DummyReviewer()

    monkeypatch.setattr("content_review_engine.cli.create_llm_reviewer", fake_create_llm_reviewer)

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
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
    assert captured_provider == {"value": "mock"}


def test_cli_review_pydantic_ai_testmodel_provider_writes_sidecar_without_api_key_or_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    llm_output_path = tmp_path / "review.llm.json"

    import socket

    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    exit_code = main(
        [
            "review",
            markdown_path,
            "--profile",
            profile_path,
            "--enable-llm",
            "--llm-provider",
            "pydantic-ai-testmodel",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()
    llm_payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.err == ""
    assert llm_payload["schema_version"] == "llm-review-result.v1"
    assert llm_payload["provider"] == "pydanticai-testmodel"
    assert llm_payload["model"] == "test"


def test_cli_review_llm_config_file_can_drive_pydanticai_sidecar_json_and_markdown_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    review_output_path = tmp_path / "review.json"
    llm_output_path = tmp_path / "review.llm.json"
    llm_markdown_output_path = tmp_path / "review.llm.md"
    from content_review_engine.llm import ValidatedLLMSemanticReviewOutput

    monkeypatch.setenv("CONTENT_REVIEW_TEST_LLM_API_KEY", "test-secret-value")
    captured_values: dict[str, object] = {}

    def fake_run_semantic_review(self, request):  # type: ignore[no-untyped-def]
        del request
        captured_values["timeout_seconds"] = self.timeout_seconds
        return ValidatedLLMSemanticReviewOutput.model_validate(
            {
                "schema_version": "llm-semantic-review-output.v1",
                "summary": "One issue was detected.",
                "findings": [
                    {
                        "rule_id": "llm.semantic.overclaim",
                        "severity": "warning",
                        "line": 2,
                        "column": 1,
                        "message": "Possible unsupported claim.",
                        "evidence": "绝对安全",
                        "suggestion": "Add evidence.",
                        "confidence": 0.91,
                    }
                ],
            }
        )

    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.PydanticAIReviewer.run_semantic_review",
        fake_run_semantic_review,
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
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "CONTENT_REVIEW_TEST_LLM_API_KEY",
            "--llm-timeout-seconds",
            "21",
            "--llm-output",
            str(llm_output_path),
            "--llm-report",
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
    assert llm_payload["provider"] == "pydanticai"
    assert llm_payload["model"] == "openai:gpt-4o-mini"
    assert llm_payload["summary"]["summary"] == "One issue was detected."
    assert llm_payload["findings"][0]["rule_id"] == "llm.semantic.overclaim"
    assert markdown_report.startswith("# LLM Review Report\n")
    assert "llm.semantic.overclaim" in markdown_report
    assert "Possible unsupported claim." in markdown_report
    assert "test-secret-value" not in markdown_report
    assert captured_values["timeout_seconds"] == 21.0


def test_cli_review_pydanticai_config_path_passes_retry_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("CONTENT_REVIEW_TEST_LLM_API_KEY", "test-secret-value")
    llm_output_path = tmp_path / "review.llm.json"
    from content_review_engine.llm import ValidatedLLMSemanticReviewOutput

    captured = {"retry_attempts": None, "retry_backoff_seconds": None}

    def fake_run_semantic_review(self, request):  # type: ignore[no-untyped-def]
        del request
        captured["retry_attempts"] = self.retry_attempts
        captured["retry_backoff_seconds"] = self.retry_backoff_seconds
        return ValidatedLLMSemanticReviewOutput(
            summary="No issues.",
            findings=(),
        )

    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.PydanticAIReviewer.run_semantic_review",
        fake_run_semantic_review,
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "CONTENT_REVIEW_TEST_LLM_API_KEY",
            "--llm-retry-attempts",
            "2",
            "--llm-retry-backoff-seconds",
            "1.25",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured_io = capsys.readouterr()

    assert exit_code == 0
    assert captured_io.err == ""
    assert captured["retry_attempts"] == 2
    assert captured["retry_backoff_seconds"] == 1.25


def test_cli_review_pydanticai_config_path_passes_min_request_interval_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("CONTENT_REVIEW_TEST_LLM_API_KEY", "test-secret-value")
    llm_output_path = tmp_path / "review.llm.json"
    from content_review_engine.llm import ValidatedLLMSemanticReviewOutput

    captured = {"min_request_interval_seconds": None}

    def fake_run_semantic_review(self, request):  # type: ignore[no-untyped-def]
        del request
        captured["min_request_interval_seconds"] = self.min_request_interval_seconds
        return ValidatedLLMSemanticReviewOutput(
            summary="No issues.",
            findings=(),
        )

    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.PydanticAIReviewer.run_semantic_review",
        fake_run_semantic_review,
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "CONTENT_REVIEW_TEST_LLM_API_KEY",
            "--llm-min-request-interval-seconds",
            "2.5",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured_io = capsys.readouterr()

    assert exit_code == 0
    assert captured_io.err == ""
    assert captured["min_request_interval_seconds"] == 2.5


def test_cli_review_llm_config_file_rejects_empty_api_key_env_override(
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
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: api_key_env must not be empty" in captured.err


def test_cli_review_llm_config_file_not_found_returns_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            str(tmp_path / "missing.yml"),
            "--llm-output",
            str(tmp_path / "review.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: LLM provider config file not found:" in captured.err


def test_cli_review_llm_config_file_can_drive_mock_sidecar(
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
            "--llm-config",
            "examples/llm/mock/llm-provider.yml",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.err == ""
    assert payload == {
        "schema_version": "llm-review-result.v1",
        "findings": [],
    }


def test_cli_review_llm_config_file_can_drive_pydanticai_fake_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "review.llm.json"
    captured_values: dict[str, object] = {}
    from content_review_engine.llm import ValidatedLLMSemanticReviewOutput
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    class DummyReviewer:
        def __init__(self, config) -> None:  # type: ignore[no-untyped-def]
            captured_values["provider"] = config.provider
            captured_values["model"] = config.model
            captured_values["api_key_env"] = config.api_key_env
            captured_values["timeout_seconds"] = config.timeout_seconds
            captured_values["retry_attempts"] = config.retry_attempts
            captured_values["retry_backoff_seconds"] = config.retry_backoff_seconds
            captured_values["min_request_interval_seconds"] = (
                config.min_request_interval_seconds
            )

        model = "openai:gpt-4o-mini"

        def run_semantic_review(self, request):  # type: ignore[no-untyped-def]
            del request
            return ValidatedLLMSemanticReviewOutput(summary="No issues.", findings=())

    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda config, *, secret_value=None: DummyReviewer(config),
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert captured_values == {
        "provider": "pydanticai",
        "model": "openai:gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
        "timeout_seconds": 30.0,
        "retry_attempts": 2,
        "retry_backoff_seconds": 1.0,
        "min_request_interval_seconds": 2.0,
    }


def test_cli_review_explicit_arguments_override_llm_config_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "review.llm.json"
    captured_values: dict[str, object] = {}
    from content_review_engine.llm import ValidatedLLMSemanticReviewOutput
    monkeypatch.setenv("OVERRIDE_OPENAI_API_KEY", "test-secret-value")

    class DummyReviewer:
        def __init__(self, config) -> None:  # type: ignore[no-untyped-def]
            captured_values["provider"] = config.provider
            captured_values["model"] = config.model
            captured_values["api_key_env"] = config.api_key_env
            captured_values["timeout_seconds"] = config.timeout_seconds
            captured_values["retry_attempts"] = config.retry_attempts
            captured_values["retry_backoff_seconds"] = config.retry_backoff_seconds
            captured_values["min_request_interval_seconds"] = (
                config.min_request_interval_seconds
            )

        model = "openai:gpt-4.1-mini"

        def run_semantic_review(self, request):  # type: ignore[no-untyped-def]
            del request
            return ValidatedLLMSemanticReviewOutput(summary="No issues.", findings=())

    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda config, *, secret_value=None: DummyReviewer(config),
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-model",
            "openai:gpt-4.1-mini",
            "--llm-api-key-env",
            "OVERRIDE_OPENAI_API_KEY",
            "--llm-timeout-seconds",
            "9",
            "--llm-retry-attempts",
            "5",
            "--llm-retry-backoff-seconds",
            "0.25",
            "--llm-min-request-interval-seconds",
            "4.5",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert captured_values == {
        "provider": "pydanticai",
        "model": "openai:gpt-4.1-mini",
        "api_key_env": "OVERRIDE_OPENAI_API_KEY",
        "timeout_seconds": 9.0,
        "retry_attempts": 5,
        "retry_backoff_seconds": 0.25,
        "min_request_interval_seconds": 4.5,
    }


def test_cli_review_parser_defaults_do_not_override_llm_config_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "review.llm.json"
    captured_values: dict[str, object] = {}
    from content_review_engine.llm import ValidatedLLMSemanticReviewOutput
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    class DummyReviewer:
        def __init__(self, config) -> None:  # type: ignore[no-untyped-def]
            captured_values["retry_attempts"] = config.retry_attempts
            captured_values["retry_backoff_seconds"] = config.retry_backoff_seconds
            captured_values["min_request_interval_seconds"] = (
                config.min_request_interval_seconds
            )

        model = "openai:gpt-4o-mini"

        def run_semantic_review(self, request):  # type: ignore[no-untyped-def]
            del request
            return ValidatedLLMSemanticReviewOutput(summary="No issues.", findings=())

    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda config, *, secret_value=None: DummyReviewer(config),
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert captured_values == {
        "retry_attempts": 2,
        "retry_backoff_seconds": 1.0,
        "min_request_interval_seconds": 2.0,
    }


def test_cli_review_llm_config_file_pydanticai_rejects_missing_environment_variable(
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
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
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
        "Error: LLM provider secret environment variable "
        "'CONTENT_REVIEW_TEST_LLM_API_KEY' is not set."
        in captured.err
    )
    assert not llm_output_path.exists()


def test_cli_review_llm_report_writes_single_file_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    llm_output_path = tmp_path / "review.llm.json"
    llm_report_path = tmp_path / "review.llm.md"

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
            "--llm-report",
            str(llm_report_path),
        ]
    )

    captured = capsys.readouterr()
    markdown_report = llm_report_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert captured.err == ""
    assert markdown_report.startswith("# LLM Review Report\n")
    assert "| File | tests/fixtures/markdown/clean_article.md |" in markdown_report
    assert "| Total Findings | 1 |" in markdown_report
    assert "Possible unsupported claim." in markdown_report
    assert "Add evidence." in markdown_report


def test_cli_review_llm_report_does_not_change_deterministic_markdown_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    llm_output_path = tmp_path / "review.llm.json"
    llm_report_path = tmp_path / "review.llm.md"

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
            "--llm-report",
            str(llm_report_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "# Content Review Report" in captured.out
    assert "## LLM Review" not in captured.out
    assert "LLM Review Report" in llm_report_path.read_text(encoding="utf-8")


def test_cli_review_quality_gate_ignores_llm_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = "tests/fixtures/markdown/clean_article.md"
    profile_path = "tests/fixtures/profiles/default.yml"
    llm_output_path = tmp_path / "review.llm.json"
    llm_report_path = tmp_path / "review.llm.md"

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
            "--llm-report",
            str(llm_report_path),
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


def test_cli_batch_parser_accepts_llm_output_argument() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "batch",
            "articles",
            "--profile",
            "profile.yml",
            "--llm-output",
            "batch.llm.json",
        ]
    )

    assert args.llm_output == "batch.llm.json"


def test_cli_batch_parser_accepts_report_index_argument() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "batch",
            "articles",
            "--profile",
            "profile.yml",
            "--report-index",
            "batch.index.md",
        ]
    )

    assert args.report_index == "batch.index.md"


def test_cli_batch_enable_llm_requires_output_or_report(
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
    assert "Error: --enable-llm requires --llm-output or --llm-report" in captured.err


def test_cli_batch_report_index_without_llm_writes_markdown_index(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report_index_path = tmp_path / "batch.index.md"

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--report-index",
            str(report_index_path),
        ]
    )

    captured = capsys.readouterr()
    report = report_index_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "Batch review completed." in captured.out
    assert captured.err == ""
    assert "# Review Output Index" in report
    assert "| Mode | batch |" in report
    assert "| LLM Review | LLM not enabled |" in report


def test_cli_batch_enable_llm_report_index_only_does_not_satisfy_llm_output_requirement(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--enable-llm",
            "--report-index",
            str(tmp_path / "batch.index.md"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --enable-llm requires --llm-output or --llm-report" in captured.err


def test_cli_batch_llm_output_requires_enable_llm(
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
            "--llm-output",
            str(tmp_path / "batch.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --llm-output requires --enable-llm" in captured.err


def test_cli_batch_llm_provider_requires_enable_llm(
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

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --llm-provider can only be used with --enable-llm" in captured.err


def test_cli_batch_llm_provider_config_flags_require_provider_or_config(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--enable-llm",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-output",
            str(tmp_path / "batch.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: LLM provider config flags require --llm-provider or --llm-config." in captured.err


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


def test_cli_batch_llm_retry_without_enable_llm_does_not_affect_deterministic_review(
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
            "--llm-retry-attempts",
            "2",
            "--llm-retry-backoff-seconds",
            "0.75",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Batch review completed." in captured.out
    assert captured.err == ""


def test_cli_batch_llm_min_request_interval_without_enable_llm_does_not_affect_deterministic_review(
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
            "--llm-min-request-interval-seconds",
            "1.75",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Batch review completed." in captured.out
    assert captured.err == ""


def test_cli_batch_llm_config_without_enable_llm_does_not_affect_deterministic_review(
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
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
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
            "--llm-report",
            str(tmp_path / "batch.llm.md"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --llm-report requires --enable-llm" in captured.err


def test_cli_review_llm_retry_exhausted_does_not_change_quality_gate_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "review.llm.json"

    from content_review_engine.llm import LLMProviderRetryExhaustedError

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self, request
        raise LLMProviderRetryExhaustedError(
            "PydanticAI runtime retry attempts exhausted after 2 attempts due to LLMProviderTimeoutError."
        )

    monkeypatch.setattr("content_review_engine.llm.mock.MockLLMReviewer.review", fake_review)

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/forbidden_terms_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--fail-on",
            "warning",
            "--enable-llm",
            "--llm-provider",
            "mock",
            "--llm-retry-attempts",
            "2",
            "--llm-retry-backoff-seconds",
            "0.2",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Findings: 1" in captured.out
    assert "PydanticAI runtime retry attempts exhausted after 2 attempts" in captured.err
    assert not llm_output_path.exists()


def test_cli_batch_llm_report_does_not_change_deterministic_markdown_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_dir = "tests/fixtures/batch/articles"
    profile_path = "tests/fixtures/batch/profile.yml"
    llm_output_path = tmp_path / "batch.llm.json"
    llm_report_path = tmp_path / "batch.llm.md"

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
            "--llm-output",
            str(llm_output_path),
            "--llm-report",
            str(llm_report_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "# Batch Content Review Report" in captured.out
    assert "## LLM Review" not in captured.out
    assert "Batch LLM Review Report" in llm_report_path.read_text(encoding="utf-8")


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
        if self.name.endswith(".llm.json"):
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
            "--llm-output",
            str(tmp_path / "batch.llm.json"),
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


def test_cli_llm_check_mock_config_succeeds(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "llm-check",
            "--llm-config",
            "examples/llm/mock/llm-provider.yml",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "LLM check passed." in captured.out
    assert "Provider: mock" in captured.out
    assert "Model: mock-model" in captured.out
    assert "Config: ok" in captured.out
    assert "Secret: not required" in captured.out
    assert "Construction: ok" in captured.out
    assert "Live call: not run" in captured.out
    assert captured.err == ""


def test_cli_llm_check_default_behavior_stays_unchanged(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["llm-check"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "LLM check passed." in captured.out
    assert "Provider: mock" in captured.out
    assert "Model: <not configured>" in captured.out
    assert "Config: ok" in captured.out
    assert "Secret: not required" in captured.out
    assert "Construction: ok" in captured.out
    assert "Live call: not run" in captured.out
    assert captured.err == ""


def test_cli_llm_check_mock_runtime_succeeds_without_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import socket

    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    exit_code = main(
        [
            "llm-check",
            "--llm-provider",
            "mock",
            "--live",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Live call: ok" in captured.out
    assert captured.err == ""


def test_cli_llm_check_provider_mock_runtime_succeeds_without_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import socket

    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    exit_code = main(
        [
            "llm-check",
            "--provider",
            "mock",
            "--live",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Provider: mock" in captured.out
    assert "Secret: not required" in captured.out
    assert "Live call: ok" in captured.out
    assert captured.err == ""


def test_cli_llm_check_provider_testmodel_runtime_succeeds_without_api_key_or_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import socket

    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    exit_code = main(
        [
            "llm-check",
            "--provider",
            "pydantic-ai-testmodel",
            "--live",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Provider: pydantic-ai-testmodel" in captured.out
    assert "Secret: not required" in captured.out
    assert "Live call: ok" in captured.out
    assert captured.err == ""


def test_cli_llm_check_provider_rejects_reserved_real_provider_without_fallback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "llm-check",
            "--provider",
            "openai",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "Error: Real LLM provider 'openai' is reserved but not implemented yet."
        in captured.err
    )


def test_cli_llm_check_provider_rejects_reserved_real_provider_without_config_fallback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "llm-check",
            "--provider",
            "openai",
            "--llm-config",
            "examples/llm/mock/llm-provider.yml",
            "--live",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "Error: Real LLM provider 'openai' is reserved but not implemented yet."
        in captured.err
    )


def test_cli_llm_check_pydanticai_construction_succeeds_without_live_call_or_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import socket

    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    def fail_review(self, request):  # type: ignore[no-untyped-def]
        del self, request
        raise AssertionError("Live call should not run during default llm-check.")

    monkeypatch.setenv("OPENAI_API_KEY", "super-secret-value")
    monkeypatch.setattr(socket, "create_connection", fail_create_connection)
    monkeypatch.setattr("content_review_engine.llm.pydanticai.PydanticAIReviewer.review", fail_review)

    exit_code = main(
        [
            "llm-check",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Provider: pydanticai" in captured.out
    assert "API key env: OPENAI_API_KEY" in captured.out
    assert "API key: <redacted>" in captured.out
    assert "Secret: resolved" in captured.out
    assert "Construction: ok" in captured.out
    assert "Live call: not run" in captured.out
    assert "super-secret-value" not in captured.out
    assert captured.err == ""


def test_cli_llm_check_pydanticai_secret_missing_returns_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exit_code = main(
        [
            "llm-check",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "Error: LLM provider secret environment variable 'OPENAI_API_KEY' is not set."
        in captured.err
    )
    assert "OPENAI_API_KEY" not in captured.out


def test_cli_llm_check_pydanticai_empty_api_key_env_var_returns_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "   ")

    exit_code = main(
        [
            "llm-check",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "Error: LLM provider secret environment variable 'OPENAI_API_KEY' is empty."
        in captured.err
    )
    assert "super-secret-value" not in captured.err


def test_cli_llm_check_pydanticai_missing_api_key_env_returns_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "llm-check",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "Error: LLM provider secret reference is missing: "
        "api_key_env is required for secret resolution."
        in captured.err
    )


def test_cli_llm_check_missing_config_file_returns_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "llm-check",
            "--llm-config",
            str(tmp_path / "missing.yml"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: LLM provider config file not found:" in captured.err


def test_cli_llm_check_invalid_config_file_returns_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "invalid.yml"
    config_path.write_text("provider: [mock\n", encoding="utf-8")

    exit_code = main(
        [
            "llm-check",
            "--llm-config",
            str(config_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert f"Error: Invalid YAML in LLM provider config file: {config_path}." in captured.err


def test_cli_llm_check_uses_cli_override_precedence(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from content_review_engine.llm.smoke_check import LLMSmokeCheckResult

    captured_config: dict[str, object] = {}

    def fake_run_llm_smoke_check(config, *, live):  # type: ignore[no-untyped-def]
        captured_config["provider"] = config.provider
        captured_config["model"] = config.model
        captured_config["api_key_env"] = config.api_key_env
        captured_config["timeout_seconds"] = config.timeout_seconds
        captured_config["retry_attempts"] = config.retry_attempts
        captured_config["retry_backoff_seconds"] = config.retry_backoff_seconds
        captured_config["min_request_interval_seconds"] = config.min_request_interval_seconds
        captured_config["live"] = live
        return LLMSmokeCheckResult(
            success=True,
            provider=config.provider,
            model=config.model,
            config_status="ok",
            secret_status="resolved",
            api_key_env=config.api_key_env,
            redacted_secret="<redacted>",
            construction_status="ok",
            live_call_status="not run",
        )

    monkeypatch.setattr("content_review_engine.cli.run_llm_smoke_check", fake_run_llm_smoke_check)

    exit_code = main(
        [
            "llm-check",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-model",
            "openai:gpt-4.1-mini",
            "--llm-api-key-env",
            "OVERRIDE_OPENAI_API_KEY",
            "--llm-timeout-seconds",
            "9",
            "--llm-retry-attempts",
            "5",
            "--llm-retry-backoff-seconds",
            "0.25",
            "--llm-min-request-interval-seconds",
            "4.5",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert captured_config == {
        "provider": "pydanticai",
        "model": "openai:gpt-4.1-mini",
        "api_key_env": "OVERRIDE_OPENAI_API_KEY",
        "timeout_seconds": 9.0,
        "retry_attempts": 5,
        "retry_backoff_seconds": 0.25,
        "min_request_interval_seconds": 4.5,
        "live": False,
    }


def test_cli_llm_check_output_does_not_leak_secret_value_or_full_prompt(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from content_review_engine.llm.smoke_check import LLMSmokeCheckResult

    monkeypatch.setenv("OPENAI_API_KEY", "super-secret-value")

    def fake_run_llm_smoke_check(config, *, live):  # type: ignore[no-untyped-def]
        del config, live
        return LLMSmokeCheckResult(
            success=True,
            provider="pydanticai",
            model="openai:gpt-4o-mini",
            config_status="ok",
            secret_status="resolved",
            api_key_env="OPENAI_API_KEY",
            redacted_secret="<redacted>",
            construction_status="ok",
            live_call_status="ok",
        )

    monkeypatch.setattr("content_review_engine.cli.run_llm_smoke_check", fake_run_llm_smoke_check)

    exit_code = main(
        [
            "llm-check",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--live",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "super-secret-value" not in captured.out
    assert "API key env: OPENAI_API_KEY" in captured.out
    assert "API key: <redacted>" in captured.out
    assert "Secret: resolved" in captured.out
    assert "Construction: ok" in captured.out
    assert "Live call: ok" in captured.out
    assert "LLM smoke check synthetic request." not in captured.out
    assert captured.err == ""


def test_cli_llm_check_live_failure_returns_stable_failed_status(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from content_review_engine.llm.smoke_check import LLMSmokeCheckResult

    def fake_run_llm_smoke_check(config, *, live):  # type: ignore[no-untyped-def]
        del config, live
        return LLMSmokeCheckResult(
            success=False,
            provider="pydanticai",
            model="openai:gpt-4o-mini",
            config_status="ok",
            secret_status="resolved",
            api_key_env="OPENAI_API_KEY",
            redacted_secret="<redacted>",
            construction_status="ok",
            live_call_status="failed",
            failure_message="PydanticAI runtime request timed out.",
        )

    monkeypatch.setattr("content_review_engine.cli.run_llm_smoke_check", fake_run_llm_smoke_check)

    exit_code = main(
        [
            "llm-check",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--live",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "LLM check failed." in captured.err
    assert "Construction: ok" in captured.err
    assert "Live call: failed" in captured.err
    assert "Reason: PydanticAI runtime request timed out." in captured.err
