from __future__ import annotations

import os
import socket

import pytest

from content_review_engine.llm import (
    LLMProviderConfig,
    LLMProviderConfigError,
    LLMProviderNotImplementedError,
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


def test_provider_factory_rejects_reserved_real_provider_without_fallback() -> None:
    with pytest.raises(LLMProviderNotImplementedError) as exc_info:
        create_llm_reviewer("openai")

    message = str(exc_info.value)

    assert message == "Real LLM provider 'openai' is reserved but not implemented yet."


def test_provider_factory_name_mode_rejects_pydanticai_without_fallback() -> None:
    with pytest.raises(UnsupportedLLMProviderError) as exc_info:
        create_llm_reviewer("pydanticai")

    message = str(exc_info.value)

    assert "Unknown LLM provider 'pydanticai'." in message
    assert "'mock'" in message
    assert "'pydantic-ai-testmodel'" in message


def test_provider_factory_rejects_blank_provider_without_fallback() -> None:
    with pytest.raises(LLMProviderConfigError) as exc_info:
        create_llm_reviewer("   ")

    assert str(exc_info.value) == "LLM provider name must not be empty."


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


def test_provider_factory_can_construct_pydanticai_with_resolved_secret_value() -> None:
    config = LLMProviderConfig(
        provider="pydanticai",
        model="openai:gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
    )

    reviewer = create_llm_reviewer(config, secret_value="test-secret-value")

    assert isinstance(reviewer, PydanticAIReviewer)
    assert reviewer.resolve_secret().api_key_env == "OPENAI_API_KEY"
    assert reviewer.resolve_secret().api_key.get_secret_value() == "test-secret-value"


def test_provider_factory_config_mode_does_not_resolve_secret_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_getenv(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected env access: {args!r} {kwargs!r}")

    monkeypatch.setattr(os, "getenv", fail_getenv)
    config = LLMProviderConfig(
        provider="pydanticai",
        model="openai:gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
    )

    reviewer = create_llm_reviewer(config)

    assert isinstance(reviewer, PydanticAIReviewer)
    assert reviewer.config is config


def test_provider_factory_config_mode_with_secret_value_does_not_read_env_or_call_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_secret_resolver(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected secret resolution: {args!r} {kwargs!r}")

    config = LLMProviderConfig(
        provider="pydanticai",
        model="openai:gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
    )

    reviewer = create_llm_reviewer(config, secret_value="test-secret-value")
    monkeypatch.setattr(reviewer, "_secret_resolver", fail_secret_resolver)

    assert isinstance(reviewer, PydanticAIReviewer)


def test_provider_factory_config_mode_does_not_execute_live_check_during_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"live": False}

    def fail_live_check(self) -> None:  # type: ignore[no-untyped-def]
        called["live"] = True
        raise AssertionError("Factory should not execute live check during construction.")

    monkeypatch.setattr(PydanticAIReviewer, "run_live_check", fail_live_check)

    reviewer = create_llm_reviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="openai:gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
        ),
        secret_value="test-secret-value",
    )

    assert isinstance(reviewer, PydanticAIReviewer)
    assert called["live"] is False


def test_provider_factory_name_mode_rejects_secret_value_argument() -> None:
    with pytest.raises(ValueError) as exc_info:
        create_llm_reviewer("mock", secret_value="test-secret-value")

    assert (
        str(exc_info.value)
        == "secret_value is supported only for config-based provider construction."
    )


def test_provider_factory_config_mode_rejects_unknown_provider_defensively() -> None:
    config = LLMProviderConfig.model_construct(provider="openai")

    with pytest.raises(LLMProviderNotImplementedError) as exc_info:
        create_llm_reviewer(config)

    assert str(exc_info.value) == "Real LLM provider 'openai' is reserved but not implemented yet."


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
