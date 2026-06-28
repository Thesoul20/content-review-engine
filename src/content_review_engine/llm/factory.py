from __future__ import annotations

from collections.abc import Callable

from content_review_engine.llm.config import LLMProviderConfig
from content_review_engine.llm.errors import (
    LLMProviderConfigError,
    LLMProviderNotImplementedError,
)
from content_review_engine.llm.mock import MockLLMReviewer
from content_review_engine.llm.provider import LLMReviewer

ProviderFactory = Callable[[LLMProviderConfig], LLMReviewer]


def _create_mock_reviewer(config: LLMProviderConfig) -> LLMReviewer:
    del config
    return MockLLMReviewer()


def _create_pydanticai_reviewer(config: LLMProviderConfig) -> LLMReviewer:
    raise LLMProviderNotImplementedError(
        f"Provider {config.provider!r} is recognized but not implemented yet."
    )


LLM_PROVIDER_REGISTRY: dict[str, ProviderFactory] = {
    "mock": _create_mock_reviewer,
    "pydanticai": _create_pydanticai_reviewer,
}


def create_llm_reviewer(config: LLMProviderConfig) -> LLMReviewer:
    factory = LLM_PROVIDER_REGISTRY.get(config.provider)
    if factory is None:
        raise LLMProviderConfigError(
            f"Unknown LLM provider {config.provider!r}. Supported providers: "
            "'mock', 'pydanticai'."
        )
    return factory(config)


def get_registered_llm_provider_names() -> tuple[str, ...]:
    return tuple(LLM_PROVIDER_REGISTRY.keys())


__all__ = [
    "LLM_PROVIDER_REGISTRY",
    "ProviderFactory",
    "create_llm_reviewer",
    "get_registered_llm_provider_names",
]
