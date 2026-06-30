from __future__ import annotations

from content_review_engine.llm.combined_envelope import CombinedReviewEnvelope
from content_review_engine.llm.batch_combined_result import BatchCombinedReviewResult
from content_review_engine.llm.combined_result import SingleFileCombinedReviewResult
from content_review_engine.reports.batch_combined_markdown import (
    render_batch_combined_markdown_report,
)
from content_review_engine.reports.combined_markdown import (
    render_single_file_combined_markdown_report,
)


def render_single_file_combined_markdown(
    result: SingleFileCombinedReviewResult,
) -> str:
    return render_single_file_combined_markdown_report(result)


def render_batch_combined_markdown(
    result: BatchCombinedReviewResult,
) -> str:
    return render_batch_combined_markdown_report(result)


def render_combined_markdown_report(result: CombinedReviewEnvelope) -> str:
    if isinstance(result, SingleFileCombinedReviewResult):
        return render_single_file_combined_markdown(result)
    if isinstance(result, BatchCombinedReviewResult):
        return render_batch_combined_markdown(result)
    raise TypeError(
        "result must be a SingleFileCombinedReviewResult or BatchCombinedReviewResult"
    )


__all__ = [
    "render_batch_combined_markdown",
    "render_combined_markdown_report",
    "render_single_file_combined_markdown",
]
