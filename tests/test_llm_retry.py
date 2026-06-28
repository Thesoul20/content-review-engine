from __future__ import annotations

from content_review_engine.llm import (
    LLMProviderConfig,
    LLMProviderRetryExhaustedError,
    LLMProviderTimeoutError,
    LLMReviewRequest,
    MockLLMReviewer,
    PydanticAIReviewer,
    ResolvedLLMSecret,
    build_llm_sidecar_file_failed,
)
from pydantic import SecretStr


def _build_request() -> LLMReviewRequest:
    return LLMReviewRequest(
        content="This article claims it is always safe.",
        profile_name="wechat-strict",
        content_path="articles/example.md",
        review_goal="semantic_review",
    )


def reviewer_secret(api_key_env: str) -> ResolvedLLMSecret:
    return ResolvedLLMSecret(api_key_env=api_key_env, api_key=SecretStr("test-secret-value"))


def test_mock_provider_retry_config_does_not_change_behavior() -> None:
    reviewer = MockLLMReviewer()
    config = LLMProviderConfig(
        provider="mock",
        retry_attempts=3,
        retry_backoff_seconds=2.0,
        min_request_interval_seconds=1.5,
    )

    result = reviewer.review(_build_request())

    assert config.retry_attempts == 3
    assert config.retry_backoff_seconds == 2.0
    assert config.min_request_interval_seconds == 1.5
    assert result.findings == ()


def test_retry_exhausted_error_serializes_stably_in_sidecar() -> None:
    error = LLMProviderRetryExhaustedError(
        "PydanticAI runtime retry attempts exhausted after 2 attempts due to LLMProviderTimeoutError."
    )

    sidecar_file = build_llm_sidecar_file_failed(path="article.md", exc=error)

    assert sidecar_file.error is not None
    assert sidecar_file.error.error_type == "LLMProviderRetryExhaustedError"
    assert (
        sidecar_file.error.message
        == "PydanticAI runtime retry attempts exhausted after 2 attempts due to LLMProviderTimeoutError."
    )


def test_pydanticai_retry_zero_does_not_sleep() -> None:
    sleep_calls: list[float] = []

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            retry_attempts=0,
            retry_backoff_seconds=3.0,
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=lambda _agent, _payload: (_ for _ in ()).throw(TimeoutError("hidden")),
        sleep_func=lambda seconds: sleep_calls.append(seconds),
    )

    try:
        reviewer.review(_build_request())
    except LLMProviderTimeoutError as exc:
        assert str(exc) == "PydanticAI runtime request timed out."
    else:
        raise AssertionError("Expected timeout error")

    assert sleep_calls == []


def test_timeout_error_remains_retryable_type_before_exhaustion() -> None:
    assert isinstance(
        LLMProviderTimeoutError("timeout"),
        LLMProviderTimeoutError,
    )
