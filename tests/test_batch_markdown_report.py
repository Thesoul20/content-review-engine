from __future__ import annotations

from pathlib import Path

from content_review_engine.config import load_profile
from content_review_engine.reports import render_batch_markdown_report
from content_review_engine.review.batch import review_markdown_directory

BATCH_FIXTURES_DIR = Path("tests/fixtures/batch")
BATCH_ARTICLES_DIR = BATCH_FIXTURES_DIR / "articles"
BATCH_PROFILE_PATH = BATCH_FIXTURES_DIR / "profile.yml"


def test_render_batch_markdown_report_includes_summary_and_file_sections() -> None:
    profile = load_profile(BATCH_PROFILE_PATH)
    result = review_markdown_directory(
        BATCH_ARTICLES_DIR,
        profile,
        recursive=True,
        profile_path=BATCH_PROFILE_PATH,
    )

    report = render_batch_markdown_report(result)

    assert report.startswith("# Batch Content Review Report\n")
    assert "| Files Discovered | 3 |" in report
    assert "| Files Reviewed | 3 |" in report
    assert "| Files With Findings | 2 |" in report
    assert "| Total Findings | 2 |" in report
    assert "| forbidden_terms | 2 |" in report
    assert "| `tests/fixtures/batch/articles/forbidden.md` | 1 | warning |" in report
    assert "| `tests/fixtures/batch/articles/nested/nested_forbidden.md` | 1 | warning |" in report
    assert "### `tests/fixtures/batch/articles/clean.md`" in report
    assert "### `tests/fixtures/batch/articles/forbidden.md`" in report
    assert "### `tests/fixtures/batch/articles/nested/nested_forbidden.md`" in report
    assert report.count("No findings.") >= 2
    assert "| warning | forbidden_terms | 1 | 8 | 发现风险词：绝对安全 | - |" in report
    assert "- Message: 发现风险词：绝对安全" in report
    assert "- Context: # 测试文章 绝对安全" in report


def test_render_batch_markdown_report_includes_quality_gate_summary() -> None:
    profile = load_profile(BATCH_PROFILE_PATH)
    result = review_markdown_directory(
        BATCH_ARTICLES_DIR,
        profile,
        recursive=True,
        profile_path=BATCH_PROFILE_PATH,
    )

    report = render_batch_markdown_report(result, fail_on="warning")

    assert "| Quality Gate | Failed |" in report
    assert "| Fail On | `warning` |" in report
    assert "| Matched Gate Findings | 2 |" in report


def test_render_batch_markdown_report_handles_no_findings() -> None:
    profile = load_profile("tests/fixtures/profiles/default.yml")
    result = review_markdown_directory(
        Path("tests/fixtures/markdown").parent / "markdown",
        profile,
        pattern="clean_article.md",
        profile_path="tests/fixtures/profiles/default.yml",
    )

    report = render_batch_markdown_report(result)

    assert "| Files With Findings | 0 |" in report
    assert "| Total Findings | 0 |" in report
    assert "## Files With Findings\n\nNo findings." in report
    assert "## Findings by File\n\nNo findings." in report
