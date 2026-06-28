from __future__ import annotations

from content_review_engine.llm.errors import LLMProviderNotImplementedError
from content_review_engine.llm.models import LLMReviewRequest, LLMReviewResult

PYDANTICAI_PROVIDER_NAME = "pydanticai"
PYDANTICAI_NOT_IMPLEMENTED_MESSAGE = (
    "Provider 'pydanticai' is recognized but not implemented yet."
)


def raise_pydanticai_not_implemented() -> None:
    raise LLMProviderNotImplementedError(PYDANTICAI_NOT_IMPLEMENTED_MESSAGE)


class PydanticAIReviewer:
    """Future provider skeleton reserved for a later implementation task."""

    def __init__(
        self,
        *,
        model: str | None = None,
        api_key_env: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.model = model
        self.api_key_env = api_key_env
        self.base_url = base_url

    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        del request
        raise_pydanticai_not_implemented()


__all__ = [
    "PYDANTICAI_NOT_IMPLEMENTED_MESSAGE",
    "PYDANTICAI_PROVIDER_NAME",
    "PydanticAIReviewer",
    "raise_pydanticai_not_implemented",
]
