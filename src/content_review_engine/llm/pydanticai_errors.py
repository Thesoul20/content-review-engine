from __future__ import annotations

import httpx
import openai

from content_review_engine.llm.errors import (
    LLMProviderAuthError,
    LLMProviderModelError,
    LLMProviderNetworkError,
    LLMProviderRateLimitError,
    LLMProviderRuntimeError,
    LLMProviderTimeoutError,
)


def classify_pydanticai_runtime_error(exc: Exception) -> LLMProviderRuntimeError:
    if isinstance(exc, (TimeoutError, httpx.TimeoutException, openai.APITimeoutError)):
        return LLMProviderTimeoutError("PydanticAI runtime request timed out.")
    if isinstance(exc, (openai.AuthenticationError, openai.PermissionDeniedError)):
        return LLMProviderAuthError("PydanticAI runtime authentication failed.")
    if isinstance(exc, (httpx.NetworkError, openai.APIConnectionError)):
        return LLMProviderNetworkError("PydanticAI runtime network request failed.")
    if isinstance(exc, openai.RateLimitError):
        return LLMProviderRateLimitError("PydanticAI runtime request was rate limited.")
    if isinstance(
        exc,
        (
            openai.BadRequestError,
            openai.NotFoundError,
            openai.UnprocessableEntityError,
        ),
    ):
        return LLMProviderModelError(
            "PydanticAI runtime rejected the configured model request."
        )
    if isinstance(exc, openai.APIStatusError) and exc.status_code in {400, 404, 422}:
        return LLMProviderModelError(
            "PydanticAI runtime rejected the configured model request."
        )
    return LLMProviderRuntimeError("PydanticAI runtime call failed unexpectedly.")


__all__ = ["classify_pydanticai_runtime_error"]
