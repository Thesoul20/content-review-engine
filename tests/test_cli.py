from __future__ import annotations

import json
from importlib.metadata import entry_points
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
    assert "### 1. `tests/fixtures/batch/articles/clean.md`" in captured.out
    assert "### 2. `tests/fixtures/batch/articles/forbidden.md`" in captured.out
    assert "### 3. `tests/fixtures/batch/articles/nested/nested_forbidden.md`" in captured.out
    assert "No issues found." in captured.out
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
    assert "### 1. `tests/fixtures/batch/articles/clean.md`" in output_text
    assert "### 2. `tests/fixtures/batch/articles/forbidden.md`" in output_text
    assert "### 3. `tests/fixtures/batch/articles/nested/nested_forbidden.md`" in output_text
    assert "No issues found." in output_text


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
