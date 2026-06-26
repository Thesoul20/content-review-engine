from __future__ import annotations

from content_review_engine.llm.models import LLMReviewRequest, LLMReviewResult


class MockLLMReviewer:
    def __init__(self, result: LLMReviewResult | None = None):
        self._result = result

    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        del request
        if self._result is not None:
            return self._result
        return LLMReviewResult()


__all__ = ["MockLLMReviewer"]
