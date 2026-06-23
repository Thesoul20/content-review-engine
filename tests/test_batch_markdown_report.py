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
    assert "- Files discovered: 3" in report
    assert "- Files reviewed: 3" in report
    assert "- Files with findings: 2" in report
    assert "- Findings: 2" in report
    assert "### 1. `tests/fixtures/batch/articles/clean.md`" in report
    assert "### 2. `tests/fixtures/batch/articles/forbidden.md`" in report
    assert "### 3. `tests/fixtures/batch/articles/nested/nested_forbidden.md`" in report
    assert "No issues found." in report
    assert "- Message: 发现风险词：绝对安全" in report
    assert "- Context: # 测试文章 绝对安全" in report
