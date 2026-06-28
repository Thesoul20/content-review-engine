from __future__ import annotations

import httpx
import openai

from content_review_engine.llm import (
    LLMProviderAuthError,
    LLMProviderModelError,
    LLMProviderNetworkError,
    LLMProviderRateLimitError,
    LLMProviderRuntimeError,
    LLMProviderTimeoutError,
    classify_pydanticai_runtime_error,
)


def _build_request() -> httpx.Request:
    return httpx.Request("POST", "https://example.com/v1/chat/completions")


def _build_response(status_code: int) -> httpx.Response:
    return httpx.Response(
        status_code,
        request=_build_request(),
        json={"error": {"message": "sensitive body should stay hidden"}},
    )


def test_classify_pydanticai_runtime_timeout_error() -> None:
    error = classify_pydanticai_runtime_error(openai.APITimeoutError(request=_build_request()))

    assert isinstance(error, LLMProviderTimeoutError)
    assert str(error) == "PydanticAI runtime request timed out."


def test_classify_pydanticai_runtime_auth_error() -> None:
    error = classify_pydanticai_runtime_error(
        openai.AuthenticationError(
            "secret should not leak",
            response=_build_response(401),
            body={"error": "secret should not leak"},
        )
    )

    assert isinstance(error, LLMProviderAuthError)
    assert str(error) == "PydanticAI runtime authentication failed."
    assert "secret should not leak" not in str(error)


def test_classify_pydanticai_runtime_network_error() -> None:
    error = classify_pydanticai_runtime_error(httpx.ConnectError("hidden", request=_build_request()))

    assert isinstance(error, LLMProviderNetworkError)
    assert str(error) == "PydanticAI runtime network request failed."


def test_classify_pydanticai_runtime_rate_limit_error() -> None:
    error = classify_pydanticai_runtime_error(
        openai.RateLimitError(
            "hidden",
            response=_build_response(429),
            body={"error": "hidden"},
        )
    )

    assert isinstance(error, LLMProviderRateLimitError)
    assert str(error) == "PydanticAI runtime request was rate limited."


def test_classify_pydanticai_runtime_model_error() -> None:
    error = classify_pydanticai_runtime_error(
        openai.NotFoundError(
            "model hidden",
            response=_build_response(404),
            body={"error": "model hidden"},
        )
    )

    assert isinstance(error, LLMProviderModelError)
    assert str(error) == "PydanticAI runtime rejected the configured model request."


def test_classify_pydanticai_runtime_unknown_error() -> None:
    error = classify_pydanticai_runtime_error(RuntimeError("traceback details should not leak"))

    assert isinstance(error, LLMProviderRuntimeError)
    assert type(error) is LLMProviderRuntimeError
    assert str(error) == "PydanticAI runtime call failed unexpectedly."
