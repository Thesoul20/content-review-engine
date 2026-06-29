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
from content_review_engine.llm.secrets import ResolvedLLMSecret
from pydantic import SecretStr

ProviderFactory = Callable[[LLMProviderConfig, str | None], LLMReviewer]
ReviewerProviderFactory = Callable[[], LLMReviewer]

LLM_REVIEWER_PROVIDER_MOCK = "mock"
LLM_REVIEWER_PROVIDER_PYDANTIC_AI_TESTMODEL = "pydantic-ai-testmodel"
SUPPORTED_LLM_REVIEWER_PROVIDERS: tuple[str, ...] = (
    LLM_REVIEWER_PROVIDER_MOCK,
    LLM_REVIEWER_PROVIDER_PYDANTIC_AI_TESTMODEL,
)


def _create_mock_reviewer(
    config: LLMProviderConfig,
    secret_value: str | None = None,
) -> LLMReviewer:
    del config
    del secret_value
    return MockLLMReviewer()


def _build_resolved_secret(
    config: LLMProviderConfig,
    secret_value: str,
) -> ResolvedLLMSecret:
    api_key_env = config.api_key_env
    if api_key_env is None or api_key_env.strip() == "":
        raise AssertionError(
            "Resolved secret requires config.api_key_env to be populated."
        )
    return ResolvedLLMSecret(
        api_key_env=api_key_env,
        api_key=SecretStr(secret_value),
    )


def _create_pydanticai_reviewer(
    config: LLMProviderConfig,
    secret_value: str | None = None,
) -> LLMReviewer:
    resolved_secret = None
    if secret_value is not None:
        resolved_secret = _build_resolved_secret(config, secret_value)
    return PydanticAIReviewer(config, resolved_secret=resolved_secret)


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
    return _create_llm_reviewer_from_config_with_secret(config, secret_value=None)


def _create_llm_reviewer_from_config_with_secret(
    config: LLMProviderConfig,
    *,
    secret_value: str | None,
) -> LLMReviewer:
    config = validate_llm_provider_config(
        config,
        supported_provider_names=get_registered_llm_provider_names(),
    )
    factory = LLM_PROVIDER_REGISTRY.get(config.provider)
    if factory is None:
        raise AssertionError(f"Missing provider factory for {config.provider!r}.")
    return factory(config, secret_value)


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
def create_llm_reviewer(provider: str, *, secret_value: str | None = None) -> LLMReviewer: ...


@overload
def create_llm_reviewer(
    provider: LLMProviderConfig,
    *,
    secret_value: str | None = None,
) -> LLMReviewer: ...


def create_llm_reviewer(
    provider: str | LLMProviderConfig,
    *,
    secret_value: str | None = None,
) -> LLMReviewer:
    if isinstance(provider, LLMProviderConfig):
        return _create_llm_reviewer_from_config_with_secret(
            provider,
            secret_value=secret_value,
        )
    if secret_value is not None:
        raise ValueError("secret_value is supported only for config-based provider construction.")
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
