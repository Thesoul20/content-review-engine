from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import ValidationError
from pydantic import field_validator

from content_review_engine.llm.errors import (
    LLMProviderConfigError,
    LLMProviderNotImplementedError,
    UnsupportedLLMProviderError,
)

LLM_DEFAULT_PROVIDER_NAME = "mock"
LLM_PROVIDER_NAMES: tuple[str, ...] = ("mock", "pydanticai")
LLM_TEST_PROVIDER_NAMES: tuple[str, ...] = ("mock", "pydantic-ai-testmodel")
LLM_RESERVED_REAL_PROVIDER_NAMES: tuple[str, ...] = (
    "openai",
    "anthropic",
    "gemini",
    "deepseek",
    "qwen",
    "local",
)
LLMProviderName = Literal["mock", "pydanticai"]
LLMProviderType = Literal["mock", "real"]


def _validate_optional_non_empty(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized == "":
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _format_supported_provider_names(provider_names: tuple[str, ...]) -> str:
    return ", ".join(repr(name) for name in provider_names)


def normalize_llm_provider_name(provider: str) -> str:
    return provider.strip().lower()


def validate_llm_provider_name(
    provider: str,
    *,
    supported_provider_names: tuple[str, ...] = LLM_PROVIDER_NAMES,
) -> str:
    normalized = normalize_llm_provider_name(provider)
    if normalized == "":
        raise LLMProviderConfigError("LLM provider name must not be empty.")
    if normalized in LLM_RESERVED_REAL_PROVIDER_NAMES:
        raise LLMProviderNotImplementedError(
            f"Real LLM provider {normalized!r} is reserved but not implemented yet."
        )
    if normalized not in supported_provider_names:
        raise UnsupportedLLMProviderError(
            f"Unknown LLM provider {provider!r}. Supported providers: "
            f"{_format_supported_provider_names(supported_provider_names)}."
        )
    return normalized


class LLMProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = LLM_DEFAULT_PROVIDER_NAME
    model: str | None = None
    api_key_env: str | None = None
    base_url: str | None = None
    timeout_seconds: float | None = None
    retry_attempts: int = 0
    retry_backoff_seconds: float = 0.0
    min_request_interval_seconds: float = 0.0

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        try:
            return validate_llm_provider_name(
                value,
                supported_provider_names=LLM_PROVIDER_NAMES,
            )
        except LLMProviderConfigError as exc:
            raise ValueError(str(exc)) from exc

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

    @field_validator("retry_attempts")
    @classmethod
    def validate_retry_attempts(cls, value: int) -> int:
        if value < 0:
            raise ValueError("retry_attempts must be greater than or equal to 0")
        return value

    @field_validator("retry_backoff_seconds")
    @classmethod
    def validate_retry_backoff_seconds(cls, value: float) -> float:
        if value < 0:
            raise ValueError("retry_backoff_seconds must be greater than or equal to 0")
        return value

    @field_validator("min_request_interval_seconds")
    @classmethod
    def validate_min_request_interval_seconds(cls, value: float) -> float:
        if value < 0:
            raise ValueError(
                "min_request_interval_seconds must be greater than or equal to 0"
            )
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
    retry_attempts: int = 0,
    retry_backoff_seconds: float = 0.0,
    min_request_interval_seconds: float = 0.0,
) -> LLMProviderConfig:
    normalized_provider = LLM_DEFAULT_PROVIDER_NAME
    if provider is not None:
        normalized_provider = validate_llm_provider_name(
            provider,
            supported_provider_names=LLM_PROVIDER_NAMES,
        )
    try:
        return LLMProviderConfig(
            provider=normalized_provider,
            model=model,
            api_key_env=api_key_env,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            retry_attempts=retry_attempts,
            retry_backoff_seconds=retry_backoff_seconds,
            min_request_interval_seconds=min_request_interval_seconds,
        )
    except ValidationError as exc:
        message = exc.errors()[0]["msg"] if exc.errors() else "Invalid LLM provider config."
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        raise LLMProviderConfigError(message) from exc


def validate_llm_provider_config(
    config: LLMProviderConfig,
    *,
    supported_provider_names: tuple[str, ...] = LLM_PROVIDER_NAMES,
) -> LLMProviderConfig:
    normalized_provider = validate_llm_provider_name(
        config.provider,
        supported_provider_names=supported_provider_names,
    )
    if normalized_provider == config.provider:
        return config
    return config.model_copy(update={"provider": normalized_provider})


def merge_llm_provider_config(
    base_config: LLMProviderConfig | None,
    *,
    provider: str | None = None,
    model: str | None = None,
    api_key_env: str | None = None,
    base_url: str | None = None,
    timeout_seconds: float | None = None,
    retry_attempts: int | None = None,
    retry_backoff_seconds: float | None = None,
    min_request_interval_seconds: float | None = None,
) -> LLMProviderConfig:
    data = (
        base_config.model_dump()
        if base_config is not None
        else load_llm_provider_config().model_dump()
    )

    if provider is not None:
        data["provider"] = provider
    if model is not None:
        data["model"] = model
    if api_key_env is not None:
        data["api_key_env"] = api_key_env
    if base_url is not None:
        data["base_url"] = base_url
    if timeout_seconds is not None:
        data["timeout_seconds"] = timeout_seconds
    if retry_attempts is not None:
        data["retry_attempts"] = retry_attempts
    if retry_backoff_seconds is not None:
        data["retry_backoff_seconds"] = retry_backoff_seconds
    if min_request_interval_seconds is not None:
        data["min_request_interval_seconds"] = min_request_interval_seconds

    return load_llm_provider_config(**data)


__all__ = [
    "LLM_DEFAULT_PROVIDER_NAME",
    "LLM_PROVIDER_NAMES",
    "LLM_RESERVED_REAL_PROVIDER_NAMES",
    "LLM_TEST_PROVIDER_NAMES",
    "LLMProviderConfig",
    "LLMProviderName",
    "LLMProviderType",
    "merge_llm_provider_config",
    "normalize_llm_provider_name",
    "load_llm_provider_config",
    "validate_llm_provider_config",
    "validate_llm_provider_name",
]
