from __future__ import annotations

from collections.abc import Callable

from pydantic_ai import Agent

from content_review_engine.llm.config import LLMProviderConfig
from content_review_engine.llm.errors import (
    LLMProviderNotImplementedError,
)
from content_review_engine.llm.models import LLMReviewRequest, LLMReviewResult
from content_review_engine.llm.pydanticai_mapping import (
    PydanticAIReviewMapper,
    PydanticAIReviewRequestPayload,
)
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
        self.mapping = PydanticAIReviewMapper(
            provider=PYDANTICAI_PROVIDER_NAME,
            model=config.model,
        )

    def resolve_secret(self) -> ResolvedLLMSecret:
        return self._secret_resolver(self.config)

    def build_request_payload(
        self,
        request: LLMReviewRequest,
    ) -> PydanticAIReviewRequestPayload:
        return self.mapping.build_request(request)

    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        self.build_request_payload(request)
        self.resolve_secret()
        raise_pydanticai_not_implemented()


__all__ = [
    "PYDANTICAI_NOT_IMPLEMENTED_MESSAGE",
    "PYDANTICAI_PROVIDER_NAME",
    "PydanticAIReviewer",
    "raise_pydanticai_not_implemented",
]
