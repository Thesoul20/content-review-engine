import pytest
from pydantic import ValidationError

from content_review_engine.llm import (
    LLMProviderAuthError,
    LLMProviderConfigError,
    LLMProviderModelError,
    LLMProviderNetworkError,
    LLMProviderNotImplementedError,
    LLMProviderError,
    LLMProviderRateLimitError,
    LLMProviderRetryExhaustedError,
    LLMProviderRuntimeError,
    LLMProviderSecretError,
    LLMProviderTimeoutError,
    LLMResponseValidationError,
    LLMReviewError,
    LLMReviewFinding,
    LLMReviewRequest,
    LLMReviewResult,
    LLMReviewSummary,
    LLMReviewer,
    MockLLMReviewer,
    llm_review_result_to_dict,
)


def test_llm_review_request_accepts_valid_input() -> None:
    request = LLMReviewRequest(
        content="Article content for semantic review.",
        profile_name="semantic-risk",
        content_path="docs/article.md",
        review_goal="Flag unsupported claims.",
        metadata={"run_mode": "test", "locale": "en-US"},
    )

    assert request.content == "Article content for semantic review."
    assert request.profile_name == "semantic-risk"
    assert request.metadata == {"run_mode": "test", "locale": "en-US"}


def test_llm_review_request_rejects_empty_content() -> None:
    with pytest.raises(ValidationError):
        LLMReviewRequest(content="   ")


def test_llm_review_request_accepts_metadata() -> None:
    request = LLMReviewRequest(
        content="Example content.",
        metadata={" source ": " fixture ", "mode": "mock"},
    )

    assert request.metadata == {"source": "fixture", "mode": "mock"}


def test_mock_llm_reviewer_satisfies_provider_protocol() -> None:
    reviewer = MockLLMReviewer()

    assert isinstance(reviewer, LLMReviewer)


def test_mock_llm_reviewer_returns_configured_result() -> None:
    configured_result = LLMReviewResult(
        provider="mock",
        model="deterministic-mock",
        profile_name="semantic-risk",
        findings=(
            LLMReviewFinding(
                rule_id="llm_semantic_risk",
                severity="warning",
                message="Possible unsupported claim.",
            ),
        ),
        summary=LLMReviewSummary(
            overall_risk="medium",
            summary="One semantic finding returned by the mock reviewer.",
        ),
        metadata={"mode": "configured"},
    )
    reviewer = MockLLMReviewer(result=configured_result)

    result = reviewer.review(LLMReviewRequest(content="Configured mock request."))

    assert result is configured_result


def test_mock_llm_reviewer_returns_empty_result_by_default() -> None:
    reviewer = MockLLMReviewer()

    result = reviewer.review(LLMReviewRequest(content="Default mock request."))

    assert result == LLMReviewResult()
    assert result.schema_version == "llm-review-result.v1"
    assert result.findings == ()


def test_mock_llm_result_can_be_serialized() -> None:
    reviewer = MockLLMReviewer(
        result=LLMReviewResult(
            provider="mock",
            model="deterministic-mock",
            findings=(
                LLMReviewFinding(
                    rule_id="llm_semantic_risk",
                    severity="error",
                    message="This needs evidence.",
                    confidence=0.9,
                ),
            ),
        )
    )

    payload = llm_review_result_to_dict(
        reviewer.review(LLMReviewRequest(content="Serialize this request."))
    )

    assert payload == {
        "schema_version": "llm-review-result.v1",
        "provider": "mock",
        "model": "deterministic-mock",
        "findings": [
            {
                "rule_id": "llm_semantic_risk",
                "severity": "error",
                "message": "This needs evidence.",
                "confidence": 0.9,
            }
        ],
    }


def test_llm_error_hierarchy_is_stable() -> None:
    config_error = LLMProviderConfigError("config invalid")
    not_implemented_error = LLMProviderNotImplementedError("not implemented")
    provider_error = LLMProviderError("provider failed")
    runtime_error = LLMProviderRuntimeError("runtime failed")
    timeout_error = LLMProviderTimeoutError("timeout")
    auth_error = LLMProviderAuthError("auth")
    network_error = LLMProviderNetworkError("network")
    rate_limit_error = LLMProviderRateLimitError("rate limit")
    model_error = LLMProviderModelError("model")
    retry_exhausted_error = LLMProviderRetryExhaustedError("retry exhausted")
    secret_error = LLMProviderSecretError("secret missing")
    response_error = LLMResponseValidationError("response invalid")

    assert isinstance(config_error, LLMReviewError)
    assert isinstance(not_implemented_error, LLMProviderConfigError)
    assert isinstance(provider_error, LLMReviewError)
    assert isinstance(runtime_error, LLMProviderError)
    assert isinstance(timeout_error, LLMProviderRuntimeError)
    assert isinstance(auth_error, LLMProviderRuntimeError)
    assert isinstance(network_error, LLMProviderRuntimeError)
    assert isinstance(rate_limit_error, LLMProviderRuntimeError)
    assert isinstance(model_error, LLMProviderRuntimeError)
    assert isinstance(retry_exhausted_error, LLMProviderRuntimeError)
    assert isinstance(secret_error, LLMProviderConfigError)
    assert isinstance(response_error, LLMReviewError)
    assert not isinstance(provider_error, LLMResponseValidationError)
