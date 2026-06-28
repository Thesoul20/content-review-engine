from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from content_review_engine.llm.config import LLMProviderConfig, validate_llm_provider_name
from content_review_engine.llm.errors import LLMProviderConfigError

_ALLOWED_CONFIG_FIELDS = {
    "provider",
    "model",
    "api_key_env",
    "base_url",
    "timeout_seconds",
    "retry_attempts",
    "retry_backoff_seconds",
    "min_request_interval_seconds",
}
_SECRET_LIKE_FIELDS = {
    "api_key",
    "secret",
    "token",
    "password",
    "access_token",
    "client_secret",
}


def _validate_config_mapping(data: object) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise LLMProviderConfigError(
            "LLM provider config file must contain a top-level mapping."
        )

    normalized: dict[str, Any] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            raise LLMProviderConfigError(
                "LLM provider config file keys must be strings."
            )
        if key in _SECRET_LIKE_FIELDS:
            raise LLMProviderConfigError(
                f"LLM provider config file must not contain secret-like field {key!r}."
            )
        if key not in _ALLOWED_CONFIG_FIELDS:
            raise LLMProviderConfigError(
                f"Unknown LLM provider config field {key!r}."
            )
        normalized[key] = value

    return normalized


def load_llm_provider_config_file(path: str | Path) -> LLMProviderConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise LLMProviderConfigError(
            f"LLM provider config file not found: {config_path}."
        )

    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LLMProviderConfigError(
            f"Failed to read LLM provider config file: {config_path}."
        ) from exc

    try:
        raw_data = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise LLMProviderConfigError(
            f"Invalid YAML in LLM provider config file: {config_path}."
        ) from exc

    validated_data = _validate_config_mapping(raw_data)
    if "provider" in validated_data:
        validated_data["provider"] = validate_llm_provider_name(validated_data["provider"])
    try:
        return LLMProviderConfig.model_validate(validated_data)
    except ValidationError as exc:
        message = exc.errors()[0]["msg"] if exc.errors() else "Invalid LLM provider config."
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        raise LLMProviderConfigError(message) from exc


__all__ = ["load_llm_provider_config_file"]
