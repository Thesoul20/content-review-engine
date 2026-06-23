from __future__ import annotations

from typing import Protocol

from content_review_engine.core.models import ReviewFinding, ReviewProfile


class ReviewRule(Protocol):
    rule_id: str

    def evaluate(self, text: str, profile: ReviewProfile) -> list[ReviewFinding]:
        ...


__all__ = ["ReviewRule"]
