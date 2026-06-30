from __future__ import annotations

from typing import Any, Literal, TypeAlias

from content_review_engine.core.models import BatchReviewResult, ReviewResult
from content_review_engine.llm.batch_combined_result import (
    BatchCombinedReviewResult,
    batch_combined_review_result_to_dict,
    batch_combined_review_result_to_json,
    build_batch_combined_review_result,
)
from content_review_engine.llm.combined_result import (
    SingleFileCombinedReviewResult,
    SingleFileCombinedLLMError,
    build_single_file_combined_review_result,
    single_file_combined_review_result_to_dict,
    single_file_combined_review_result_to_json,
)
from content_review_engine.llm.models import LLMSidecarResult, LLMReviewResult

CombinedReviewEnvelope: TypeAlias = (
    SingleFileCombinedReviewResult | BatchCombinedReviewResult
)


def build_single_file_combined_review_envelope(
    *,
    review_result: ReviewResult,
    llm_result: LLMReviewResult | None = None,
    llm_status: Literal["not_run", "skipped", "succeeded", "failed"] | None = None,
    llm_error: dict[str, Any] | SingleFileCombinedLLMError | None = None,
) -> SingleFileCombinedReviewResult:
    return build_single_file_combined_review_result(
        review_result=review_result,
        llm_result=llm_result,
        llm_status=llm_status,
        llm_error=llm_error,
    )


def build_batch_combined_review_envelope(
    *,
    batch_review_result: BatchReviewResult,
    batch_llm_result: LLMSidecarResult | None = None,
    default_llm_status: Literal["not_run", "skipped", "succeeded", "failed"] = "not_run",
) -> BatchCombinedReviewResult:
    return build_batch_combined_review_result(
        batch_review_result=batch_review_result,
        batch_llm_result=batch_llm_result,
        default_llm_status=default_llm_status,
    )


def combined_review_envelope_to_dict(
    result: CombinedReviewEnvelope,
) -> dict[str, Any]:
    if isinstance(result, SingleFileCombinedReviewResult):
        return single_file_combined_review_result_to_dict(result)
    if isinstance(result, BatchCombinedReviewResult):
        return batch_combined_review_result_to_dict(result)
    raise TypeError(
        "result must be a SingleFileCombinedReviewResult or BatchCombinedReviewResult"
    )


def combined_review_envelope_to_json(result: CombinedReviewEnvelope) -> str:
    if isinstance(result, SingleFileCombinedReviewResult):
        return single_file_combined_review_result_to_json(result)
    if isinstance(result, BatchCombinedReviewResult):
        return batch_combined_review_result_to_json(result)
    raise TypeError(
        "result must be a SingleFileCombinedReviewResult or BatchCombinedReviewResult"
    )


__all__ = [
    "CombinedReviewEnvelope",
    "build_batch_combined_review_envelope",
    "build_single_file_combined_review_envelope",
    "combined_review_envelope_to_dict",
    "combined_review_envelope_to_json",
]
