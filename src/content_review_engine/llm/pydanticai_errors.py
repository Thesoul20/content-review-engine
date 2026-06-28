from __future__ import annotations

import httpx
import openai

from content_review_engine.llm.errors import (
    LLMProviderAuthError,
    LLMProviderModelError,
    LLMProviderNetworkError,
    LLMProviderRateLimitError,
    LLMProviderRetryExhaustedError,
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


def is_pydanticai_retryable_error(exc: Exception) -> bool:
    return isinstance(
        exc,
        (
            LLMProviderTimeoutError,
            LLMProviderNetworkError,
            LLMProviderRateLimitError,
        ),
    )


def build_pydanticai_retry_exhausted_error(
    *,
    attempts: int,
    last_error: LLMProviderRuntimeError,
) -> LLMProviderRetryExhaustedError:
    return LLMProviderRetryExhaustedError(
        "PydanticAI runtime retry attempts exhausted after "
        f"{attempts} attempts due to {type(last_error).__name__}."
    )


__all__ = [
    "build_pydanticai_retry_exhausted_error",
    "classify_pydanticai_runtime_error",
    "is_pydanticai_retryable_error",
]
