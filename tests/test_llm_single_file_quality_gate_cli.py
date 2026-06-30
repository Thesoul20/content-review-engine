from __future__ import annotations

from pathlib import Path

import pytest

from content_review_engine.cli import build_parser, main
from content_review_engine.llm import LLMReviewFinding, LLMReviewResult


def test_cli_review_parser_accepts_llm_fail_on() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "review",
            "article.md",
            "--profile",
            "profile.yml",
            "--llm-fail-on",
            "error",
        ]
    )

    assert args.llm_fail_on == "error"


def test_cli_review_llm_fail_on_requires_enable_llm(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--llm-fail-on",
            "warning",
            "--combined-output",
            str(tmp_path / "combined.json"),
            "--combined-output-format",
            "json",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --llm-fail-on requires --enable-llm" in captured.err


def test_cli_review_llm_fail_on_rejects_invalid_severity(
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
            "--llm-output",
            str(tmp_path / "review.llm.json"),
            "--llm-fail-on",
            "high",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Invalid severity: 'high'" in captured.err


def test_cli_review_default_quality_gate_ignores_llm_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "review.llm.json"

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self, request
        return LLMReviewResult(
            findings=(
                LLMReviewFinding(
                    rule_id="llm.semantic.critical_issue",
                    severity="critical",
                    message="Critical semantic issue.",
                ),
            )
        )

    monkeypatch.setattr("content_review_engine.llm.mock.MockLLMReviewer.review", fake_review)

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 0" in captured.out
    assert captured.err == ""


def test_cli_review_llm_fail_on_returns_exit_code_one_for_matching_llm_finding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "review.llm.json"

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self, request
        return LLMReviewResult(
            findings=(
                LLMReviewFinding(
                    rule_id="llm.semantic.risky_advice",
                    severity="error",
                    message="Error semantic issue.",
                ),
            )
        )

    monkeypatch.setattr("content_review_engine.llm.mock.MockLLMReviewer.review", fake_review)

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
            "--llm-fail-on",
            "error",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Findings: 0" in captured.out
    assert captured.err == ""
