from __future__ import annotations

import pytest

from content_review_engine.llm import (
    LLMProviderConfig,
    LLMProviderConfigError,
    load_llm_provider_config,
    merge_llm_provider_config,
)


def test_llm_provider_config_defaults_to_mock() -> None:
    config = load_llm_provider_config()

    assert config.provider == "mock"
    assert config.provider_type == "mock"
    assert config.model is None
    assert config.api_key_env is None
    assert config.timeout_seconds is None
    assert config.retry_attempts == 0
    assert config.retry_backoff_seconds == 0.0
    assert config.min_request_interval_seconds == 0.0


def test_llm_provider_config_can_store_model() -> None:
    config = load_llm_provider_config(model="gpt-4o-mini")

    assert config.model == "gpt-4o-mini"


def test_llm_provider_config_can_store_api_key_env_name() -> None:
    config = load_llm_provider_config(api_key_env="OPENAI_API_KEY")

    assert config.api_key_env == "OPENAI_API_KEY"


def test_llm_provider_config_can_store_timeout_seconds() -> None:
    config = load_llm_provider_config(timeout_seconds=30.5)

    assert config.timeout_seconds == 30.5


def test_llm_provider_config_can_store_retry_fields() -> None:
    config = load_llm_provider_config(retry_attempts=2, retry_backoff_seconds=1.5)

    assert config.retry_attempts == 2
    assert config.retry_backoff_seconds == 1.5


def test_llm_provider_config_can_store_min_request_interval_seconds() -> None:
    config = load_llm_provider_config(min_request_interval_seconds=2.5)

    assert config.min_request_interval_seconds == 2.5


def test_llm_provider_config_repr_and_serialization_do_not_leak_secret_value() -> None:
    config = LLMProviderConfig(
        provider="mock",
        model="mock-model",
        api_key_env="OPENAI_API_KEY",
        base_url="https://example.com/v1",
    )

    serialized = config.model_dump()
    rendered = repr(config)

    assert serialized["api_key_env"] == "OPENAI_API_KEY"
    assert "secret-key" not in rendered
    assert "secret-key" not in str(serialized)


def test_load_llm_provider_config_rejects_unknown_provider() -> None:
    try:
        load_llm_provider_config(provider="openai")
    except LLMProviderConfigError as exc:
        assert str(exc) == "Unknown LLM provider 'openai'. Supported providers: 'mock', 'pydanticai'."
    else:
        raise AssertionError("Expected LLMProviderConfigError")


def test_load_llm_provider_config_rejects_empty_api_key_env() -> None:
    with pytest.raises(LLMProviderConfigError) as exc_info:
        load_llm_provider_config(provider="pydanticai", api_key_env="   ")

    assert str(exc_info.value) == "api_key_env must not be empty"


def test_load_llm_provider_config_rejects_non_positive_timeout() -> None:
    with pytest.raises(LLMProviderConfigError) as exc_info:
        load_llm_provider_config(timeout_seconds=0)

    assert str(exc_info.value) == "timeout_seconds must be greater than 0"


def test_load_llm_provider_config_rejects_negative_retry_attempts() -> None:
    with pytest.raises(LLMProviderConfigError) as exc_info:
        load_llm_provider_config(retry_attempts=-1)

    assert str(exc_info.value) == "retry_attempts must be greater than or equal to 0"


def test_load_llm_provider_config_rejects_negative_retry_backoff_seconds() -> None:
    with pytest.raises(LLMProviderConfigError) as exc_info:
        load_llm_provider_config(retry_backoff_seconds=-0.5)

    assert (
        str(exc_info.value)
        == "retry_backoff_seconds must be greater than or equal to 0"
    )


def test_load_llm_provider_config_rejects_negative_min_request_interval_seconds() -> None:
    with pytest.raises(LLMProviderConfigError) as exc_info:
        load_llm_provider_config(min_request_interval_seconds=-0.5)

    assert (
        str(exc_info.value)
        == "min_request_interval_seconds must be greater than or equal to 0"
    )


def test_merge_llm_provider_config_prefers_explicit_cli_values() -> None:
    base_config = load_llm_provider_config(
        provider="pydanticai",
        model="openai:gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        timeout_seconds=30.0,
        retry_attempts=2,
        retry_backoff_seconds=1.0,
        min_request_interval_seconds=2.0,
    )

    merged = merge_llm_provider_config(
        base_config,
        model="openai:gpt-4.1-mini",
        retry_attempts=3,
    )

    assert merged.provider == "pydanticai"
    assert merged.model == "openai:gpt-4.1-mini"
    assert merged.api_key_env == "OPENAI_API_KEY"
    assert merged.timeout_seconds == 30.0
    assert merged.retry_attempts == 3
    assert merged.retry_backoff_seconds == 1.0
    assert merged.min_request_interval_seconds == 2.0


def test_merge_llm_provider_config_keeps_file_values_when_cli_values_missing() -> None:
    base_config = load_llm_provider_config(
        provider="pydanticai",
        model="openai:gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        timeout_seconds=30.0,
        retry_attempts=2,
        retry_backoff_seconds=1.0,
        min_request_interval_seconds=2.0,
    )

    merged = merge_llm_provider_config(base_config)

    assert merged == base_config
