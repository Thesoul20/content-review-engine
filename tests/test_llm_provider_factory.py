from __future__ import annotations

import socket

import pytest

from content_review_engine.llm import (
    LLMProviderConfig,
    LLMReviewer,
    MockLLMReviewer,
    PydanticAIReviewer,
    PydanticAITestModelReviewer,
    SUPPORTED_LLM_REVIEWER_PROVIDERS,
    UnsupportedLLMProviderError,
    create_llm_reviewer,
    get_registered_llm_provider_names,
    get_supported_llm_reviewer_provider_names,
)


def test_provider_factory_creates_mock_reviewer_from_provider_name() -> None:
    reviewer = create_llm_reviewer("mock")

    assert isinstance(reviewer, MockLLMReviewer)
    assert isinstance(reviewer, LLMReviewer)


def test_provider_factory_creates_testmodel_reviewer_from_provider_name() -> None:
    reviewer = create_llm_reviewer("pydantic-ai-testmodel")

    assert isinstance(reviewer, PydanticAITestModelReviewer)
    assert isinstance(reviewer, LLMReviewer)


def test_provider_factory_normalizes_provider_name_before_creation() -> None:
    reviewer = create_llm_reviewer("  PYDANTIC-AI-TESTMODEL  ")

    assert isinstance(reviewer, PydanticAITestModelReviewer)


def test_provider_factory_rejects_unsupported_provider_without_fallback() -> None:
    with pytest.raises(UnsupportedLLMProviderError) as exc_info:
        create_llm_reviewer("openai")

    message = str(exc_info.value)

    assert "Unknown LLM provider 'openai'." in message
    assert "'mock'" in message
    assert "'pydantic-ai-testmodel'" in message


def test_provider_factory_name_mode_rejects_pydanticai_without_fallback() -> None:
    with pytest.raises(UnsupportedLLMProviderError) as exc_info:
        create_llm_reviewer("pydanticai")

    message = str(exc_info.value)

    assert "Unknown LLM provider 'pydanticai'." in message
    assert "'mock'" in message
    assert "'pydantic-ai-testmodel'" in message


def test_provider_factory_rejects_blank_provider_without_fallback() -> None:
    with pytest.raises(UnsupportedLLMProviderError) as exc_info:
        create_llm_reviewer("   ")

    message = str(exc_info.value)

    assert "Unknown LLM provider '   '." in message
    assert "'mock'" in message
    assert "'pydantic-ai-testmodel'" in message


def test_provider_factory_name_mode_does_not_require_api_key_env_or_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    mock_reviewer = create_llm_reviewer("mock")
    testmodel_reviewer = create_llm_reviewer("pydantic-ai-testmodel")

    assert isinstance(mock_reviewer, MockLLMReviewer)
    assert isinstance(testmodel_reviewer, PydanticAITestModelReviewer)


def test_provider_factory_keeps_existing_config_based_mock_behavior() -> None:
    reviewer = create_llm_reviewer(LLMProviderConfig(provider="mock"))

    assert isinstance(reviewer, MockLLMReviewer)


def test_provider_factory_keeps_existing_config_based_pydanticai_behavior() -> None:
    config = LLMProviderConfig(
        provider="pydanticai",
        model="openai:gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
    )

    reviewer = create_llm_reviewer(config)

    assert isinstance(reviewer, PydanticAIReviewer)
    assert reviewer.config is config


def test_provider_factory_config_mode_rejects_unknown_provider_defensively() -> None:
    config = LLMProviderConfig.model_construct(provider="openai")

    with pytest.raises(UnsupportedLLMProviderError) as exc_info:
        create_llm_reviewer(config)

    message = str(exc_info.value)

    assert "Unknown LLM provider 'openai'." in message
    assert "'mock'" in message
    assert "'pydanticai'" in message


def test_supported_reviewer_provider_names_are_stable() -> None:
    assert SUPPORTED_LLM_REVIEWER_PROVIDERS == ("mock", "pydantic-ai-testmodel")
    assert get_supported_llm_reviewer_provider_names() == (
        "mock",
        "pydantic-ai-testmodel",
    )


def test_registered_config_provider_names_remain_stable() -> None:
    assert get_registered_llm_provider_names() == ("mock", "pydanticai")


def test_reviewer_provider_names_remain_distinct_from_config_provider_names() -> None:
    assert get_supported_llm_reviewer_provider_names() == (
        "mock",
        "pydantic-ai-testmodel",
    )
    assert get_registered_llm_provider_names() == ("mock", "pydanticai")
