from __future__ import annotations

import socket

import pytest

from content_review_engine.llm import (
    LLMProviderError,
    LLMResponseValidationError,
    LLMReviewRequest,
    LLMReviewer,
    MockLLMReviewer,
    PydanticAITestModelReviewer,
    build_pydantic_ai_testmodel_request,
    build_pydantic_ai_testmodel_response_args,
    llm_review_result_to_dict,
)


def _build_request() -> LLMReviewRequest:
    return LLMReviewRequest(
        content="# Title\nThis article claims it is always safe.",
        profile_name="wechat-strict",
        content_path="articles/example.md",
        review_goal="semantic_review",
        metadata={"locale": "zh-CN", "mode": "testmodel"},
    )


def test_pydantic_ai_testmodel_reviewer_satisfies_provider_protocol() -> None:
    reviewer = PydanticAITestModelReviewer()

    assert isinstance(reviewer, LLMReviewer)


def test_build_pydantic_ai_testmodel_request_reuses_existing_request_mapping() -> None:
    payload = build_pydantic_ai_testmodel_request(_build_request())

    assert payload.prompt_version == "pydanticai-review-prompt.v1"
    assert "You are a pre-publication content review assistant." in payload.system_prompt
    assert "articles/example.md" in payload.user_prompt
    assert "# Title\nThis article claims it is always safe." in payload.user_prompt


def test_pydantic_ai_testmodel_reviewer_returns_serializable_llm_review_result_without_api_key_or_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    reviewer = PydanticAITestModelReviewer(
        output_args_builder=lambda _request: build_pydantic_ai_testmodel_response_args(
            findings=[
                {
                    "rule_id": "llm_semantic_risk",
                    "severity": "warning",
                    "message": "The wording sounds absolute.",
                    "matched_text": "always safe",
                    "line": 2,
                    "column": 21,
                }
            ],
            summary={
                "overall_risk": "medium",
                "summary": "One semantic issue detected.",
                "recommended_action": "Revise before publishing.",
                "confidence": 0.75,
            },
        )
    )

    result = reviewer.review(_build_request())
    payload = llm_review_result_to_dict(result)

    assert result.schema_version == "llm-review-result.v1"
    assert result.provider == "pydanticai-testmodel"
    assert result.model == "test"
    assert result.profile_name == "wechat-strict"
    assert len(result.findings) == 1
    assert result.summary is not None
    assert payload["schema_version"] == "llm-review-result.v1"
    assert payload["findings"][0]["rule_id"] == "llm_semantic_risk"
    assert payload["summary"]["overall_risk"] == "medium"


def test_pydantic_ai_testmodel_reviewer_wraps_runtime_failures_in_llm_provider_error() -> None:
    reviewer = PydanticAITestModelReviewer(
        runtime_runner=lambda _agent, _payload: (_ for _ in ()).throw(
            RuntimeError("hidden testmodel failure")
        )
    )

    with pytest.raises(LLMProviderError) as exc_info:
        reviewer.review(_build_request())

    assert str(exc_info.value) == "PydanticAI TestModel reviewer failed."


def test_pydantic_ai_testmodel_reviewer_preserves_existing_response_validation_errors() -> None:
    reviewer = PydanticAITestModelReviewer(
        runtime_runner=lambda _agent, _payload: {
            "findings": [{"rule_id": "bad", "severity": "medium"}]
        }
    )

    with pytest.raises(LLMResponseValidationError) as exc_info:
        reviewer.review(_build_request())

    assert "findings.0.severity" in str(exc_info.value)


def test_mock_llm_reviewer_remains_unchanged_after_testmodel_provider_addition() -> None:
    result = MockLLMReviewer().review(LLMReviewRequest(content="Mock request."))

    assert result.schema_version == "llm-review-result.v1"
    assert result.provider is None
    assert result.findings == ()
