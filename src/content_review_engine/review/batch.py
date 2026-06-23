from __future__ import annotations

from pathlib import Path

from content_review_engine.core.models import BatchReviewResult, ReviewProfile
from content_review_engine.parser import read_markdown
from content_review_engine.review.pipeline import review_document


def discover_markdown_files(
    input_dir: Path,
    *,
    pattern: str = "*.md",
    recursive: bool = False,
) -> list[Path]:
    directory = Path(input_dir)

    if not directory.exists():
        raise FileNotFoundError(f"Input directory not found: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {directory}")

    iterator = directory.rglob(pattern) if recursive else directory.glob(pattern)
    files = [path for path in iterator if path.is_file()]
    return sorted(files, key=lambda path: path.as_posix())


def review_markdown_directory(
    input_dir: Path,
    profile: ReviewProfile,
    *,
    pattern: str = "*.md",
    recursive: bool = False,
    profile_path: str | Path | None = None,
) -> BatchReviewResult:
    markdown_files = discover_markdown_files(
        input_dir,
        pattern=pattern,
        recursive=recursive,
    )

    results = []
    for markdown_file in markdown_files:
        markdown_text = read_markdown(markdown_file)
        results.append(
            review_document(
                markdown_text,
                profile,
                document_path=markdown_file,
                profile_path=profile_path,
            )
        )

    return BatchReviewResult.from_results(
        results,
        file_count=len(markdown_files),
    )


__all__ = ["discover_markdown_files", "review_markdown_directory"]
