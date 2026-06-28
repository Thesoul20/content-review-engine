from __future__ import annotations

import socket

import pytest

from content_review_engine.llm import (
    EmptyLLMProviderSecretEnvironmentVariableError,
    MissingLLMProviderSecretEnvironmentVariableError,
    MissingLLMProviderSecretReferenceError,
    REDACTED_SECRET_TEXT,
    ResolvedLLMSecret,
    load_llm_provider_config,
    redact_secret_value,
    resolve_llm_api_key,
    resolve_llm_provider_secret,
)


def test_resolve_llm_provider_secret_reads_fake_env_mapping() -> None:
    config = load_llm_provider_config(
        provider="pydanticai",
        api_key_env="OPENAI_API_KEY",
    )

    secret = resolve_llm_provider_secret(
        config,
        env={"OPENAI_API_KEY": "fake-test-key"},
    )

    assert secret == "fake-test-key"


def test_resolve_llm_provider_secret_prefers_explicit_env_mapping_over_os_environ(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "wrong-process-key")
    config = load_llm_provider_config(
        provider="pydanticai",
        api_key_env="OPENAI_API_KEY",
    )

    secret = resolve_llm_provider_secret(
        config,
        env={"OPENAI_API_KEY": "fake-test-key"},
    )

    assert secret == "fake-test-key"


def test_resolve_llm_provider_secret_reads_os_environ_when_env_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONTENT_REVIEW_TEST_LLM_API_KEY", "test-secret-value")

    secret = resolve_llm_provider_secret(
        load_llm_provider_config(
            provider="pydanticai",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        )
    )

    assert secret == "test-secret-value"


def test_resolve_llm_provider_secret_rejects_missing_api_key_env() -> None:
    with pytest.raises(MissingLLMProviderSecretReferenceError) as exc_info:
        resolve_llm_provider_secret(load_llm_provider_config(provider="pydanticai"))

    assert (
        str(exc_info.value)
        == "LLM provider secret reference is missing: api_key_env is required for secret resolution."
    )


def test_resolve_llm_provider_secret_rejects_unset_environment_variable() -> None:
    config = load_llm_provider_config(
        provider="pydanticai",
        api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
    )

    with pytest.raises(MissingLLMProviderSecretEnvironmentVariableError) as exc_info:
        resolve_llm_provider_secret(config, env={})

    assert (
        str(exc_info.value)
        == "LLM provider secret environment variable 'CONTENT_REVIEW_TEST_LLM_API_KEY' is not set."
    )
    assert "fake-test-key" not in str(exc_info.value)


def test_resolve_llm_provider_secret_rejects_empty_environment_variable() -> None:
    config = load_llm_provider_config(
        provider="pydanticai",
        api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
    )

    with pytest.raises(EmptyLLMProviderSecretEnvironmentVariableError) as exc_info:
        resolve_llm_provider_secret(
            config,
            env={"CONTENT_REVIEW_TEST_LLM_API_KEY": "   "},
        )

    assert (
        str(exc_info.value)
        == "LLM provider secret environment variable 'CONTENT_REVIEW_TEST_LLM_API_KEY' is empty."
    )


def test_resolve_llm_provider_secret_does_not_read_dotenv(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    (tmp_path / ".env").write_text("OPENAI_API_KEY=dotenv-secret\n", encoding="utf-8")

    config = load_llm_provider_config(
        provider="pydanticai",
        api_key_env="OPENAI_API_KEY",
    )

    with pytest.raises(MissingLLMProviderSecretEnvironmentVariableError):
        resolve_llm_provider_secret(config)


def test_resolve_llm_provider_secret_does_not_access_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)
    config = load_llm_provider_config(
        provider="pydanticai",
        api_key_env="OPENAI_API_KEY",
    )

    secret = resolve_llm_provider_secret(
        config,
        env={"OPENAI_API_KEY": "fake-test-key"},
    )

    assert secret == "fake-test-key"


def test_resolve_llm_api_key_returns_redacted_secret_model() -> None:
    secret = resolve_llm_api_key(
        load_llm_provider_config(
            provider="pydanticai",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        env={"CONTENT_REVIEW_TEST_LLM_API_KEY": "test-secret-value"},
    )

    assert isinstance(secret, ResolvedLLMSecret)
    assert secret.api_key_env == "CONTENT_REVIEW_TEST_LLM_API_KEY"
    assert secret.api_key.get_secret_value() == "test-secret-value"
    assert "test-secret-value" not in repr(secret)
    assert secret.model_dump() == {"api_key_env": "CONTENT_REVIEW_TEST_LLM_API_KEY"}


def test_secret_redaction_helper_returns_constant_redaction() -> None:
    assert redact_secret_value("test-secret-value") == REDACTED_SECRET_TEXT
    assert redact_secret_value("another-secret") == REDACTED_SECRET_TEXT

