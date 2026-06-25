from __future__ import annotations

from pathlib import Path

from content_review_engine.config import load_profile
from content_review_engine.core.models import BatchReviewResult
from content_review_engine.review.batch import (
    discover_markdown_files,
    review_markdown_directory,
)

BATCH_FIXTURES_DIR = Path("tests/fixtures/batch")
BATCH_ARTICLES_DIR = BATCH_FIXTURES_DIR / "articles"
BATCH_PROFILE_PATH = BATCH_FIXTURES_DIR / "profile.yml"


def test_discover_markdown_files_is_deterministic_without_recursion() -> None:
    files = discover_markdown_files(BATCH_ARTICLES_DIR)

    assert [path.as_posix() for path in files] == [
        "tests/fixtures/batch/articles/clean.md",
        "tests/fixtures/batch/articles/forbidden.md",
    ]


def test_discover_markdown_files_is_deterministic_with_recursion() -> None:
    files = discover_markdown_files(BATCH_ARTICLES_DIR, recursive=True)

    assert [path.as_posix() for path in files] == [
        "tests/fixtures/batch/articles/clean.md",
        "tests/fixtures/batch/articles/forbidden.md",
        "tests/fixtures/batch/articles/nested/nested_forbidden.md",
    ]


def test_review_markdown_directory_handles_empty_directories(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    profile = load_profile(BATCH_PROFILE_PATH)

    result = review_markdown_directory(empty_dir, profile)

    assert isinstance(result, BatchReviewResult)
    assert result.summary.file_count == 0
    assert result.summary.reviewed_count == 0
    assert result.summary.finding_count == 0
    assert result.summary.files_with_findings == 0
    assert result.results == []


def test_review_markdown_directory_builds_batch_summary() -> None:
    profile = load_profile(BATCH_PROFILE_PATH)

    result = review_markdown_directory(
        BATCH_ARTICLES_DIR,
        profile,
        recursive=True,
        profile_path=BATCH_PROFILE_PATH,
    )

    assert result.summary.file_count == 3
    assert result.summary.reviewed_count == 3
    assert result.summary.finding_count == 2
    assert result.summary.files_with_findings == 2
    assert result.summary.severity_counts == {
        "info": 0,
        "warning": 2,
        "error": 0,
        "critical": 0,
    }
    assert [item.document.path for item in result.results] == [
        "tests/fixtures/batch/articles/clean.md",
        "tests/fixtures/batch/articles/forbidden.md",
        "tests/fixtures/batch/articles/nested/nested_forbidden.md",
    ]
    assert result.results[0].findings == []
    assert result.results[1].summary.finding_count == 1
    assert result.results[2].summary.finding_count == 1
    assert result.results[1].profile is not None
    assert result.results[1].profile.path == "tests/fixtures/batch/profile.yml"


def test_review_markdown_directory_excludes_suppressed_findings_from_summary(
    tmp_path: Path,
) -> None:
    articles_dir = tmp_path / "articles"
    articles_dir.mkdir()
    (articles_dir / "suppressed.md").write_text(
        "\n".join(
            [
                "<!-- content-review-disable-next-line forbidden_terms -->",
                "这里写着绝对安全。",
            ]
        ),
        encoding="utf-8",
    )
    profile = load_profile(BATCH_PROFILE_PATH)

    result = review_markdown_directory(articles_dir, profile)

    assert result.summary.finding_count == 0
    assert result.summary.files_with_findings == 0
    assert result.summary.severity_counts == {
        "info": 0,
        "warning": 0,
        "error": 0,
        "critical": 0,
    }
    assert result.results[0].findings == []
