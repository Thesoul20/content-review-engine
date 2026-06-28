from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from content_review_engine.llm.config import LLMProviderConfig
from content_review_engine.llm.errors import LLMProviderSecretError


class ResolvedLLMSecret(BaseModel):
    model_config = ConfigDict(frozen=True)

    api_key_env: str
    api_key: SecretStr = Field(repr=False, exclude=True)


def resolve_llm_api_key(config: LLMProviderConfig) -> ResolvedLLMSecret:
    api_key_env = config.api_key_env
    if api_key_env is None:
        raise LLMProviderSecretError(
            f"LLM provider {config.provider!r} requires api_key_env to be configured."
        )

    api_key = os.environ.get(api_key_env)
    if api_key is None:
        raise LLMProviderSecretError(
            f"LLM API key environment variable {api_key_env!r} is not set."
        )
    if api_key.strip() == "":
        raise LLMProviderSecretError(
            f"LLM API key environment variable {api_key_env!r} is empty."
        )

    return ResolvedLLMSecret(
        api_key_env=api_key_env,
        api_key=SecretStr(api_key),
    )


__all__ = [
    "ResolvedLLMSecret",
    "resolve_llm_api_key",
]
