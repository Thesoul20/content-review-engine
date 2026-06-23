from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_review_engine.cli import main


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

    assert exit_code == 1
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

    assert exit_code == 1
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


def test_cli_review_json_output_includes_location(
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
    assert payload["summary"]["finding_count"] == 1
    location = payload["findings"][0]["location"]
    assert location["start_line"] == 1
    assert location["start_column"] == 8
    assert location["matched_text"] == "绝对安全"
    assert "Context:" not in captured.out
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
    assert "- Document: `tests/fixtures/markdown/forbidden_terms_article.md`" in captured.out
    assert "- Profile: `tests/fixtures/profiles/default.yml`" in captured.out
    assert "- Findings: 1" in captured.out
    assert "- Context: # 测试文章 绝对安全" in captured.out
    assert "- Matched: `绝对安全`" in captured.out
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
    assert "- Document: `tests/fixtures/markdown/forbidden_terms_article.md`" in output_text
    assert "- Profile: `tests/fixtures/profiles/default.yml`" in output_text
    assert "- Findings: 1" in output_text
    assert "- Context: # 测试文章 绝对安全" in output_text
    assert "- Matched: `绝对安全`" in output_text


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
