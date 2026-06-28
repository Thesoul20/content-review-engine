from __future__ import annotations

from collections.abc import Callable

from pydantic_ai import Agent

from content_review_engine.llm.config import LLMProviderConfig
from content_review_engine.llm.errors import (
    LLMProviderNotImplementedError,
)
from content_review_engine.llm.models import LLMReviewRequest, LLMReviewResult
from content_review_engine.llm.secrets import ResolvedLLMSecret, resolve_llm_api_key

PYDANTICAI_PROVIDER_NAME = "pydanticai"
PYDANTICAI_NOT_IMPLEMENTED_MESSAGE = (
    "Provider 'pydanticai' dependency and secret boundary is available, "
    "but review is not implemented yet."
)


def raise_pydanticai_not_implemented() -> None:
    raise LLMProviderNotImplementedError(PYDANTICAI_NOT_IMPLEMENTED_MESSAGE)


class PydanticAIReviewer:
    """Future provider skeleton reserved for a later implementation task."""

    def __init__(
        self,
        config: LLMProviderConfig,
        *,
        secret_resolver: Callable[[LLMProviderConfig], ResolvedLLMSecret] = resolve_llm_api_key,
    ) -> None:
        self.config = config
        self.model = config.model
        self.api_key_env = config.api_key_env
        self.base_url = config.base_url
        self._secret_resolver = secret_resolver
        self._agent_type = Agent

    def resolve_secret(self) -> ResolvedLLMSecret:
        return self._secret_resolver(self.config)

    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        del request
        self.resolve_secret()
        raise_pydanticai_not_implemented()


__all__ = [
    "PYDANTICAI_NOT_IMPLEMENTED_MESSAGE",
    "PYDANTICAI_PROVIDER_NAME",
    "PydanticAIReviewer",
    "raise_pydanticai_not_implemented",
]
