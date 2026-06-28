from __future__ import annotations

import pytest

from content_review_engine.llm import (
    LLMProviderConfig,
    LLMProviderConfigError,
    LLMProviderNotImplementedError,
    MockLLMReviewer,
    create_llm_reviewer,
    load_llm_provider_config,
)


def test_provider_factory_creates_mock_reviewer() -> None:
    reviewer = create_llm_reviewer(load_llm_provider_config())

    assert isinstance(reviewer, MockLLMReviewer)


def test_provider_factory_rejects_reserved_pydanticai_provider() -> None:
    config = load_llm_provider_config(provider="pydanticai")

    with pytest.raises(LLMProviderNotImplementedError) as exc_info:
        create_llm_reviewer(config)

    assert str(exc_info.value) == "Provider 'pydanticai' is recognized but not implemented yet."


def test_provider_factory_rejects_unknown_provider_defensively() -> None:
    config = LLMProviderConfig.model_construct(provider="openai")

    with pytest.raises(LLMProviderConfigError) as exc_info:
        create_llm_reviewer(config)

    assert str(exc_info.value) == "Unknown LLM provider 'openai'. Supported providers: 'mock', 'pydanticai'."
