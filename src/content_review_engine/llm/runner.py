from __future__ import annotations

from typing import Any, Protocol, cast

from content_review_engine.llm.result_conversion import (
    convert_validated_semantic_output_to_llm_review_result,
)
from content_review_engine.llm.models import LLMReviewRequest, LLMReviewResult
from content_review_engine.llm.provider import LLMReviewer


class LLMReviewRunner:
    def __init__(self, reviewer: LLMReviewer) -> None:
        self._reviewer = reviewer

    def run(self, request: LLMReviewRequest) -> LLMReviewResult:
        return self._reviewer.review(request)


class LLMSemanticReviewer(Protocol):
    model: str | None

    def run_semantic_review(self, request: LLMReviewRequest) -> Any: ...


def run_single_file_llm_review(
    request: LLMReviewRequest,
    *,
    reviewer: LLMReviewer,
    provider: str | None = None,
    model: str | None = None,
) -> LLMReviewResult:
    semantic_reviewer = reviewer
    if hasattr(semantic_reviewer, "run_semantic_review"):
        semantic_output = cast(
            LLMSemanticReviewer,
            semantic_reviewer,
        ).run_semantic_review(request)
        resolved_model = model
        if resolved_model is None:
            resolved_model = getattr(semantic_reviewer, "model", None)
        return convert_validated_semantic_output_to_llm_review_result(
            semantic_output,
            request,
            provider=provider,
            model=resolved_model,
        )

    return reviewer.review(request)


__all__ = ["LLMReviewRunner", "run_single_file_llm_review"]
