from __future__ import annotations

from content_review_engine.llm.models import LLMReviewRequest, LLMReviewResult
from content_review_engine.llm.provider import LLMReviewer


class LLMReviewRunner:
    def __init__(self, reviewer: LLMReviewer) -> None:
        self._reviewer = reviewer

    def run(self, request: LLMReviewRequest) -> LLMReviewResult:
        return self._reviewer.review(request)


__all__ = ["LLMReviewRunner"]
