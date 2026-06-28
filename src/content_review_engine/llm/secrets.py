from __future__ import annotations

from collections.abc import Mapping
import os

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from content_review_engine.llm.config import LLMProviderConfig
from content_review_engine.llm.errors import (
    EmptyLLMProviderSecretEnvironmentVariableError,
    MissingLLMProviderSecretEnvironmentVariableError,
    MissingLLMProviderSecretReferenceError,
)

REDACTED_SECRET_TEXT = "<redacted>"


class ResolvedLLMSecret(BaseModel):
    model_config = ConfigDict(frozen=True)

    api_key_env: str
    api_key: SecretStr = Field(repr=False, exclude=True)


def redact_secret_value(_value: str) -> str:
    return REDACTED_SECRET_TEXT


def resolve_llm_provider_secret(
    config: LLMProviderConfig,
    env: Mapping[str, str] | None = None,
) -> str:
    environment = os.environ if env is None else env
    api_key_env = config.api_key_env
    if api_key_env is None or api_key_env.strip() == "":
        raise MissingLLMProviderSecretReferenceError(
            "LLM provider secret reference is missing: "
            "api_key_env is required for secret resolution."
        )

    api_key = environment.get(api_key_env)
    if api_key is None:
        raise MissingLLMProviderSecretEnvironmentVariableError(
            f"LLM provider secret environment variable {api_key_env!r} is not set."
        )
    if api_key.strip() == "":
        raise EmptyLLMProviderSecretEnvironmentVariableError(
            f"LLM provider secret environment variable {api_key_env!r} is empty."
        )
    return api_key


def resolve_llm_api_key(
    config: LLMProviderConfig,
    env: Mapping[str, str] | None = None,
) -> ResolvedLLMSecret:
    api_key_env = config.api_key_env
    if api_key_env is None or api_key_env.strip() == "":
        raise MissingLLMProviderSecretReferenceError(
            "LLM provider secret reference is missing: "
            "api_key_env is required for secret resolution."
        )
    api_key = resolve_llm_provider_secret(config, env=env)
    return ResolvedLLMSecret(
        api_key_env=api_key_env,
        api_key=SecretStr(api_key),
    )


__all__ = [
    "REDACTED_SECRET_TEXT",
    "ResolvedLLMSecret",
    "redact_secret_value",
    "resolve_llm_api_key",
    "resolve_llm_provider_secret",
]
