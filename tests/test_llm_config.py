from __future__ import annotations

from content_review_engine.llm import (
    LLMProviderConfig,
    LLMProviderConfigError,
    load_llm_provider_config,
)


def test_llm_provider_config_defaults_to_mock() -> None:
    config = load_llm_provider_config()

    assert config.provider == "mock"
    assert config.provider_type == "mock"
    assert config.model is None
    assert config.api_key_env is None


def test_llm_provider_config_can_store_model() -> None:
    config = load_llm_provider_config(model="gpt-4o-mini")

    assert config.model == "gpt-4o-mini"


def test_llm_provider_config_can_store_api_key_env_name() -> None:
    config = load_llm_provider_config(api_key_env="OPENAI_API_KEY")

    assert config.api_key_env == "OPENAI_API_KEY"


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
