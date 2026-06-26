from __future__ import annotations

from typing import Protocol
from typing import runtime_checkable

from content_review_engine.llm.models import LLMReviewRequest, LLMReviewResult


@runtime_checkable
class LLMReviewer(Protocol):
    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        ...


__all__ = ["LLMReviewer"]
