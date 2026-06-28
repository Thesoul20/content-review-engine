from __future__ import annotations

import os
import socket

import pytest

from content_review_engine.llm import (
    LLMProviderConfig,
    LLMProviderConfigError,
    LLMProviderNotImplementedError,
    LLM_RESERVED_REAL_PROVIDER_NAMES,
    LLM_TEST_PROVIDER_NAMES,
    UnsupportedLLMProviderError,
    validate_llm_provider_config,
)


def test_validate_llm_provider_config_accepts_mock_provider() -> None:
    config = validate_llm_provider_config(LLMProviderConfig(provider="mock"))

    assert config.provider == "mock"


def test_validate_llm_provider_config_accepts_testmodel_provider() -> None:
    config = validate_llm_provider_config(
        LLMProviderConfig.model_construct(provider="pydantic-ai-testmodel"),
        supported_provider_names=LLM_TEST_PROVIDER_NAMES,
    )

    assert config.provider == "pydantic-ai-testmodel"


def test_validate_llm_provider_config_rejects_blank_provider_name() -> None:
    with pytest.raises(LLMProviderConfigError) as exc_info:
        validate_llm_provider_config(LLMProviderConfig.model_construct(provider="   "))

    assert str(exc_info.value) == "LLM provider name must not be empty."


def test_validate_llm_provider_config_rejects_unsupported_provider() -> None:
    with pytest.raises(UnsupportedLLMProviderError) as exc_info:
        validate_llm_provider_config(LLMProviderConfig.model_construct(provider="custom-llm"))

    message = str(exc_info.value)

    assert "Unknown LLM provider 'custom-llm'." in message
    assert "'mock'" in message
    assert "'pydanticai'" in message


def test_validate_llm_provider_config_rejects_reserved_real_provider() -> None:
    with pytest.raises(LLMProviderNotImplementedError) as exc_info:
        validate_llm_provider_config(LLMProviderConfig.model_construct(provider="openai"))

    assert str(exc_info.value) == "Real LLM provider 'openai' is reserved but not implemented yet."


def test_validate_llm_provider_config_reserved_provider_error_contains_name() -> None:
    with pytest.raises(LLMProviderNotImplementedError) as exc_info:
        validate_llm_provider_config(LLMProviderConfig.model_construct(provider="anthropic"))

    assert "anthropic" in str(exc_info.value)


def test_validate_llm_provider_config_does_not_read_env_or_access_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_getenv(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected env access: {args!r} {kwargs!r}")

    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(os, "getenv", fail_getenv)
    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    config = validate_llm_provider_config(
        LLMProviderConfig.model_construct(provider="pydantic-ai-testmodel"),
        supported_provider_names=LLM_TEST_PROVIDER_NAMES,
    )

    assert config.provider == "pydantic-ai-testmodel"


def test_validate_llm_provider_config_test_providers_do_not_require_api_key() -> None:
    mock_config = validate_llm_provider_config(
        LLMProviderConfig(provider="mock"),
        supported_provider_names=LLM_TEST_PROVIDER_NAMES,
    )
    testmodel_config = validate_llm_provider_config(
        LLMProviderConfig.model_construct(provider="pydantic-ai-testmodel"),
        supported_provider_names=LLM_TEST_PROVIDER_NAMES,
    )

    assert mock_config.api_key_env is None
    assert testmodel_config.api_key_env is None


def test_validate_llm_provider_config_does_not_resolve_secret_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_getenv(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected env access: {args!r} {kwargs!r}")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    config = validate_llm_provider_config(
        LLMProviderConfig(
            provider="pydanticai",
            model="openai:gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
        )
    )

    assert config.provider == "pydanticai"
    assert config.api_key_env == "OPENAI_API_KEY"


def test_reserved_real_provider_list_is_stable() -> None:
    assert LLM_RESERVED_REAL_PROVIDER_NAMES == (
        "openai",
        "anthropic",
        "gemini",
        "deepseek",
        "qwen",
        "local",
    )
