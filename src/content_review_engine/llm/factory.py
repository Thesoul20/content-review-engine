from __future__ import annotations

from collections.abc import Callable
from typing import overload

from content_review_engine.llm.config import (
    LLMProviderConfig,
    validate_llm_provider_config,
    validate_llm_provider_name,
)
from content_review_engine.llm.mock import MockLLMReviewer
from content_review_engine.llm.pydantic_ai_provider import (
    PydanticAITestModelReviewer,
)
from content_review_engine.llm.pydanticai import PydanticAIReviewer
from content_review_engine.llm.provider import LLMReviewer

ProviderFactory = Callable[[LLMProviderConfig], LLMReviewer]
ReviewerProviderFactory = Callable[[], LLMReviewer]

LLM_REVIEWER_PROVIDER_MOCK = "mock"
LLM_REVIEWER_PROVIDER_PYDANTIC_AI_TESTMODEL = "pydantic-ai-testmodel"
SUPPORTED_LLM_REVIEWER_PROVIDERS: tuple[str, ...] = (
    LLM_REVIEWER_PROVIDER_MOCK,
    LLM_REVIEWER_PROVIDER_PYDANTIC_AI_TESTMODEL,
)


def _create_mock_reviewer(config: LLMProviderConfig) -> LLMReviewer:
    del config
    return MockLLMReviewer()


def _create_pydanticai_reviewer(config: LLMProviderConfig) -> LLMReviewer:
    return PydanticAIReviewer(config)


def _create_mock_reviewer_from_name() -> LLMReviewer:
    return MockLLMReviewer()


def _create_pydantic_ai_testmodel_reviewer_from_name() -> LLMReviewer:
    return PydanticAITestModelReviewer()


LLM_PROVIDER_REGISTRY: dict[str, ProviderFactory] = {
    "mock": _create_mock_reviewer,
    "pydanticai": _create_pydanticai_reviewer,
}

LLM_REVIEWER_PROVIDER_REGISTRY: dict[str, ReviewerProviderFactory] = {
    LLM_REVIEWER_PROVIDER_MOCK: _create_mock_reviewer_from_name,
    LLM_REVIEWER_PROVIDER_PYDANTIC_AI_TESTMODEL: _create_pydantic_ai_testmodel_reviewer_from_name,
}
def _create_llm_reviewer_from_config(config: LLMProviderConfig) -> LLMReviewer:
    config = validate_llm_provider_config(
        config,
        supported_provider_names=get_registered_llm_provider_names(),
    )
    factory = LLM_PROVIDER_REGISTRY.get(config.provider)
    if factory is None:
        raise AssertionError(f"Missing provider factory for {config.provider!r}.")
    return factory(config)


def _create_llm_reviewer_from_provider_name(provider: str) -> LLMReviewer:
    normalized_provider = validate_llm_provider_name(
        provider,
        supported_provider_names=SUPPORTED_LLM_REVIEWER_PROVIDERS,
    )
    factory = LLM_REVIEWER_PROVIDER_REGISTRY.get(normalized_provider)
    if factory is None:
        raise AssertionError(f"Missing reviewer provider factory for {normalized_provider!r}.")
    return factory()


@overload
def create_llm_reviewer(provider: str) -> LLMReviewer: ...


@overload
def create_llm_reviewer(provider: LLMProviderConfig) -> LLMReviewer: ...


def create_llm_reviewer(provider: str | LLMProviderConfig) -> LLMReviewer:
    if isinstance(provider, LLMProviderConfig):
        return _create_llm_reviewer_from_config(provider)
    return _create_llm_reviewer_from_provider_name(provider)


def get_registered_llm_provider_names() -> tuple[str, ...]:
    return tuple(LLM_PROVIDER_REGISTRY.keys())


def get_supported_llm_reviewer_provider_names() -> tuple[str, ...]:
    return SUPPORTED_LLM_REVIEWER_PROVIDERS


__all__ = [
    "LLM_REVIEWER_PROVIDER_MOCK",
    "LLM_REVIEWER_PROVIDER_PYDANTIC_AI_TESTMODEL",
    "LLM_REVIEWER_PROVIDER_REGISTRY",
    "LLM_PROVIDER_REGISTRY",
    "ProviderFactory",
    "ReviewerProviderFactory",
    "SUPPORTED_LLM_REVIEWER_PROVIDERS",
    "create_llm_reviewer",
    "get_registered_llm_provider_names",
    "get_supported_llm_reviewer_provider_names",
]
