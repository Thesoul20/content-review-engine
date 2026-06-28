from __future__ import annotations

import pytest

from content_review_engine.llm import (
    LLMProviderSecretError,
    ResolvedLLMSecret,
    load_llm_provider_config,
    resolve_llm_api_key,
)


def test_resolve_llm_api_key_returns_redacted_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONTENT_REVIEW_TEST_LLM_API_KEY", "test-secret-value")

    secret = resolve_llm_api_key(
        load_llm_provider_config(
            provider="pydanticai",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        )
    )

    assert isinstance(secret, ResolvedLLMSecret)
    assert secret.api_key_env == "CONTENT_REVIEW_TEST_LLM_API_KEY"
    assert secret.api_key.get_secret_value() == "test-secret-value"
    assert "test-secret-value" not in repr(secret)
    assert secret.model_dump() == {"api_key_env": "CONTENT_REVIEW_TEST_LLM_API_KEY"}


def test_resolve_llm_api_key_rejects_missing_api_key_env() -> None:
    with pytest.raises(LLMProviderSecretError) as exc_info:
        resolve_llm_api_key(load_llm_provider_config(provider="pydanticai"))

    assert (
        str(exc_info.value)
        == "LLM provider 'pydanticai' requires api_key_env to be configured."
    )


def test_resolve_llm_api_key_rejects_unset_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CONTENT_REVIEW_TEST_LLM_API_KEY", raising=False)

    with pytest.raises(LLMProviderSecretError) as exc_info:
        resolve_llm_api_key(
            load_llm_provider_config(
                provider="pydanticai",
                api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            )
        )

    assert (
        str(exc_info.value)
        == "LLM API key environment variable 'CONTENT_REVIEW_TEST_LLM_API_KEY' is not set."
    )
    assert "test-secret-value" not in str(exc_info.value)


def test_resolve_llm_api_key_rejects_empty_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONTENT_REVIEW_TEST_LLM_API_KEY", "   ")

    with pytest.raises(LLMProviderSecretError) as exc_info:
        resolve_llm_api_key(
            load_llm_provider_config(
                provider="pydanticai",
                api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            )
        )

    assert (
        str(exc_info.value)
        == "LLM API key environment variable 'CONTENT_REVIEW_TEST_LLM_API_KEY' is empty."
    )
