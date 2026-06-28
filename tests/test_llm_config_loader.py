from __future__ import annotations

from pathlib import Path

import pytest

from content_review_engine.llm import (
    LLMProviderConfigError,
    load_llm_provider_config_file,
)


def test_load_llm_provider_config_file_supports_pydanticai_example() -> None:
    config = load_llm_provider_config_file("examples/llm/pydanticai/llm-provider.yml")

    assert config.provider == "pydanticai"
    assert config.model == "openai:gpt-4o-mini"
    assert config.api_key_env == "OPENAI_API_KEY"
    assert config.base_url is None
    assert config.timeout_seconds == 30.0
    assert config.retry_attempts == 2
    assert config.retry_backoff_seconds == 1.0
    assert config.min_request_interval_seconds == 2.0


def test_load_llm_provider_config_file_supports_mock_example() -> None:
    config = load_llm_provider_config_file("examples/llm/mock/llm-provider.yml")

    assert config.provider == "mock"
    assert config.model == "mock-model"
    assert config.api_key_env is None
    assert config.base_url is None
    assert config.timeout_seconds is None
    assert config.retry_attempts == 0
    assert config.retry_backoff_seconds == 0.0
    assert config.min_request_interval_seconds == 0.0


def test_load_llm_provider_config_file_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(LLMProviderConfigError) as exc_info:
        load_llm_provider_config_file(tmp_path / "missing.yml")

    assert str(exc_info.value) == f"LLM provider config file not found: {tmp_path / 'missing.yml'}."


def test_load_llm_provider_config_file_rejects_invalid_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yml"
    config_path.write_text("provider: [pydanticai\n", encoding="utf-8")

    with pytest.raises(LLMProviderConfigError) as exc_info:
        load_llm_provider_config_file(config_path)

    assert str(exc_info.value) == f"Invalid YAML in LLM provider config file: {config_path}."


def test_load_llm_provider_config_file_rejects_top_level_non_mapping(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yml"
    config_path.write_text("- provider: mock\n", encoding="utf-8")

    with pytest.raises(LLMProviderConfigError) as exc_info:
        load_llm_provider_config_file(config_path)

    assert (
        str(exc_info.value)
        == "LLM provider config file must contain a top-level mapping."
    )


def test_load_llm_provider_config_file_rejects_unknown_field(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yml"
    config_path.write_text("provider: mock\nunexpected: true\n", encoding="utf-8")

    with pytest.raises(LLMProviderConfigError) as exc_info:
        load_llm_provider_config_file(config_path)

    assert str(exc_info.value) == "Unknown LLM provider config field 'unexpected'."


@pytest.mark.parametrize("field_name", ["api_key", "secret", "token", "password"])
def test_load_llm_provider_config_file_rejects_secret_like_fields(
    tmp_path: Path,
    field_name: str,
) -> None:
    config_path = tmp_path / "invalid.yml"
    config_path.write_text(f"provider: mock\n{field_name}: hidden\n", encoding="utf-8")

    with pytest.raises(LLMProviderConfigError) as exc_info:
        load_llm_provider_config_file(config_path)

    assert (
        str(exc_info.value)
        == f"LLM provider config file must not contain secret-like field {field_name!r}."
    )


@pytest.mark.parametrize(
    ("field_line", "expected_message"),
    [
        ("timeout_seconds: 0\n", "timeout_seconds must be greater than 0"),
        (
            "retry_attempts: -1\n",
            "retry_attempts must be greater than or equal to 0",
        ),
        (
            "retry_backoff_seconds: -1\n",
            "retry_backoff_seconds must be greater than or equal to 0",
        ),
        (
            "min_request_interval_seconds: -1\n",
            "min_request_interval_seconds must be greater than or equal to 0",
        ),
    ],
)
def test_load_llm_provider_config_file_rejects_invalid_numeric_fields(
    tmp_path: Path,
    field_line: str,
    expected_message: str,
) -> None:
    config_path = tmp_path / "invalid.yml"
    config_path.write_text(f"provider: mock\n{field_line}", encoding="utf-8")

    with pytest.raises(LLMProviderConfigError) as exc_info:
        load_llm_provider_config_file(config_path)

    assert str(exc_info.value) == expected_message


def test_load_llm_provider_config_file_does_not_leak_secret_values(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yml"
    config_path.write_text("provider: mock\napi_key: sk-secret-value\n", encoding="utf-8")

    with pytest.raises(LLMProviderConfigError) as exc_info:
        load_llm_provider_config_file(config_path)

    assert "sk-secret-value" not in str(exc_info.value)
