from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic import ValidationError
from pydantic import field_validator

from content_review_engine.llm.errors import LLMProviderConfigError

LLM_DEFAULT_PROVIDER_NAME = "mock"
LLM_PROVIDER_NAMES: tuple[str, ...] = ("mock", "pydanticai")
LLMProviderName = Literal["mock", "pydanticai"]
LLMProviderType = Literal["mock", "real"]


def _validate_optional_non_empty(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized == "":
        raise ValueError(f"{field_name} must not be empty")
    return normalized


class LLMProviderConfig(BaseModel):
    provider: str = LLM_DEFAULT_PROVIDER_NAME
    model: str | None = None
    api_key_env: str | None = None
    base_url: str | None = None
    timeout_seconds: float | None = None

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in LLM_PROVIDER_NAMES:
            supported = ", ".join(repr(name) for name in LLM_PROVIDER_NAMES)
            raise ValueError(
                f"Unknown LLM provider {value!r}. Supported providers: {supported}."
            )
        return normalized

    @field_validator("model", "api_key_env", "base_url")
    @classmethod
    def validate_optional_non_empty(cls, value: str | None, info) -> str | None:
        return _validate_optional_non_empty(value, field_name=info.field_name)

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout_seconds(cls, value: float | None) -> float | None:
        if value is None:
            return None
        if value <= 0:
            raise ValueError("timeout_seconds must be greater than 0")
        return value

    @property
    def provider_type(self) -> LLMProviderType:
        if self.provider == "mock":
            return "mock"
        return "real"


def load_llm_provider_config(
    *,
    provider: str | None = None,
    model: str | None = None,
    api_key_env: str | None = None,
    base_url: str | None = None,
    timeout_seconds: float | None = None,
) -> LLMProviderConfig:
    try:
        return LLMProviderConfig(
            provider=provider or LLM_DEFAULT_PROVIDER_NAME,
            model=model,
            api_key_env=api_key_env,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )
    except ValidationError as exc:
        message = exc.errors()[0]["msg"] if exc.errors() else "Invalid LLM provider config."
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        raise LLMProviderConfigError(message) from exc


__all__ = [
    "LLM_DEFAULT_PROVIDER_NAME",
    "LLM_PROVIDER_NAMES",
    "LLMProviderConfig",
    "LLMProviderName",
    "LLMProviderType",
    "load_llm_provider_config",
]
