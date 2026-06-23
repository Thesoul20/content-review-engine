from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_review_engine.cli import main


def _write_profile(path: Path, forbidden_terms: list[str] | None = None) -> None:
    terms = forbidden_terms or []
    lines = [
        "name: wechat",
        "target_platform: wechat",
        "tone: clear and professional",
        "max_title_length: 32",
        "max_paragraph_length: 220",
        "forbidden_terms:",
    ]
    lines.extend(f"  - {term}" for term in terms)
    path.write_text("\n".join(lines), encoding="utf-8")


def test_cli_review_with_findings_prints_finding_details(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = tmp_path / "article.md"
    markdown_path.write_text("这篇文章承诺保证赚钱。", encoding="utf-8")
    profile_path = tmp_path / "wechat.yaml"
    _write_profile(profile_path, ["保证赚钱", "100%有效"])

    exit_code = main(["review", str(markdown_path), "--profile", str(profile_path)])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Review completed." in captured.out
    assert "Findings: 1" in captured.out
    assert "[warning] forbidden_terms: 发现风险词：保证赚钱" in captured.out
    assert "Line: 1" in captured.out
    assert "Column: 7" in captured.out
    assert "Matched: 保证赚钱" in captured.out
    assert "Context:" in captured.out
    assert captured.err == ""


def test_cli_review_without_findings_prints_zero_findings(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = tmp_path / "article.md"
    markdown_path.write_text("这篇文章只是在说明产品特点。", encoding="utf-8")
    profile_path = tmp_path / "wechat.yaml"
    _write_profile(profile_path, ["保证赚钱"])

    exit_code = main(["review", str(markdown_path), "--profile", str(profile_path)])

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
    profile_path = tmp_path / "wechat.yaml"
    _write_profile(profile_path, ["保证赚钱"])

    exit_code = main(
        [
            "review",
            str(tmp_path / "missing.md"),
            "--profile",
            str(profile_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Markdown file not found" in captured.err


def test_cli_missing_profile_file_returns_non_zero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = tmp_path / "article.md"
    markdown_path.write_text("这篇文章承诺保证赚钱。", encoding="utf-8")

    exit_code = main(
        [
            "review",
            str(markdown_path),
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
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = tmp_path / "article.md"
    markdown_path.write_text("这篇文章承诺保证赚钱。", encoding="utf-8")
    profile_path = tmp_path / "wechat.yaml"
    _write_profile(profile_path, ["保证赚钱"])

    exit_code = main(
        [
            "review",
            str(markdown_path),
            "--profile",
            str(profile_path),
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
    assert location["start_column"] == 7
    assert location["matched_text"] == "保证赚钱"
    assert "Context:" not in captured.out
    assert captured.err == ""


def test_cli_review_markdown_stdout_includes_report_sections(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = tmp_path / "article.md"
    markdown_path.write_text("这篇文章承诺保证赚钱。", encoding="utf-8")
    profile_path = tmp_path / "wechat.yaml"
    _write_profile(profile_path, ["保证赚钱"])

    exit_code = main(
        [
            "review",
            str(markdown_path),
            "--profile",
            str(profile_path),
            "--format",
            "markdown",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "# Content Review Report" in captured.out
    assert "- Document: `" + str(markdown_path) + "`" in captured.out
    assert "- Profile: `" + str(profile_path) + "`" in captured.out
    assert "- Findings: 1" in captured.out
    assert "### forbidden_terms" in captured.out
    assert "- Matched: `保证赚钱`" in captured.out
    assert captured.err == ""


def test_cli_review_markdown_output_file_writes_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = tmp_path / "article.md"
    markdown_path.write_text("这篇文章承诺保证赚钱。", encoding="utf-8")
    profile_path = tmp_path / "wechat.yaml"
    _write_profile(profile_path, ["保证赚钱"])
    output_path = tmp_path / "review-report.md"

    exit_code = main(
        [
            "review",
            str(markdown_path),
            "--profile",
            str(profile_path),
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
    assert output_path.read_text(encoding="utf-8").startswith("# Content Review Report")
    assert "- Findings: 1" in output_path.read_text(encoding="utf-8")


def test_cli_review_output_write_failure_returns_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown_path = tmp_path / "article.md"
    markdown_path.write_text("这篇文章承诺保证赚钱。", encoding="utf-8")
    profile_path = tmp_path / "wechat.yaml"
    _write_profile(profile_path, ["保证赚钱"])
    output_path = tmp_path / "missing" / "review-report.md"

    exit_code = main(
        [
            "review",
            str(markdown_path),
            "--profile",
            str(profile_path),
            "--format",
            "markdown",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error:" in captured.err
