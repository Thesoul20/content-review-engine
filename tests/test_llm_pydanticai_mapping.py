from __future__ import annotations

import pytest

from content_review_engine.llm import (
    LLMResponseValidationError,
    LLMReviewRequest,
    PydanticAIReviewMapper,
    build_pydanticai_review_prompt,
    build_pydanticai_review_request,
    build_pydanticai_system_prompt,
    pydanticai_response_to_llm_review_result,
)


def _build_request() -> LLMReviewRequest:
    return LLMReviewRequest(
        content="# Title\nThis article claims it is always safe.",
        profile_name="wechat-strict",
        content_path="articles/example.md",
        review_goal="semantic_review",
        metadata={
            "locale": "zh-CN",
            "audience": "public",
            "api_key": "sk-test-secret",
        },
    )


def test_build_pydanticai_system_prompt_contains_structured_output_rules() -> None:
    system_prompt = build_pydanticai_system_prompt()

    assert "Return structured data only." in system_prompt
    assert "Severity must be one of: info, warning, error, critical." in system_prompt
    assert "If there are no findings, return findings as an empty list." in system_prompt


def test_build_pydanticai_review_prompt_includes_request_context_and_redacts_sensitive_metadata() -> None:
    prompt = build_pydanticai_review_prompt(_build_request())

    assert "articles/example.md" in prompt
    assert "wechat-strict" in prompt
    assert "semantic_review" in prompt
    assert "# Title\nThis article claims it is always safe." in prompt
    assert "- locale: zh-CN" in prompt
    assert "- audience: public" in prompt
    assert "- api_key: [redacted]" in prompt
    assert "sk-test-secret" not in prompt


def test_build_pydanticai_review_request_contains_prompt_and_instruction() -> None:
    payload = build_pydanticai_review_request(_build_request())

    assert payload.prompt_version == "pydanticai-review-prompt.v1"
    assert "You are a pre-publication content review assistant." in payload.system_prompt
    assert "response_contract:" in payload.user_prompt
    assert "severity enum: info, warning, error, critical" in payload.user_prompt
    assert "if there are no issues, return findings: []" in payload.user_prompt


def test_pydanticai_response_to_llm_review_result_maps_empty_findings() -> None:
    result = pydanticai_response_to_llm_review_result(
        {"findings": []},
        _build_request(),
        provider="pydanticai",
        model="gpt-4o-mini",
    )

    assert result.provider == "pydanticai"
    assert result.model == "gpt-4o-mini"
    assert result.prompt_version == "pydanticai-review-prompt.v1"
    assert result.profile_name == "wechat-strict"
    assert result.findings == ()


def test_pydanticai_response_to_llm_review_result_maps_single_finding() -> None:
    result = pydanticai_response_to_llm_review_result(
        {
            "findings": [
                {
                    "rule_id": "llm_semantic_risk",
                    "severity": "warning",
                    "message": "The claim sounds absolute.",
                    "suggestion": "Add evidence or soften the wording.",
                    "rationale": "The wording implies a guarantee.",
                    "line": 2,
                    "column": 6,
                    "end_line": 2,
                    "end_column": 19,
                    "matched_text": "always safe",
                    "category": "claims",
                    "confidence": 0.8,
                }
            ]
        },
        _build_request(),
        provider="pydanticai",
        model="gpt-4o-mini",
    )

    finding = result.findings[0]
    assert len(result.findings) == 1
    assert finding.severity == "warning"
    assert finding.rule_id == "llm_semantic_risk"
    assert finding.message == "The claim sounds absolute."
    assert finding.suggestion == "Add evidence or soften the wording."
    assert finding.rationale == "The wording implies a guarantee."
    assert finding.line == 2
    assert finding.column == 6
    assert finding.end_line == 2
    assert finding.end_column == 19
    assert finding.matched_text == "always safe"
    assert finding.category == "claims"
    assert finding.confidence == 0.8


def test_pydanticai_response_to_llm_review_result_maps_multiple_findings_and_summary() -> None:
    request = _build_request()
    mapper = PydanticAIReviewMapper(provider="pydanticai", model="gpt-4o-mini")

    result = mapper.response_to_result(
        {
            "findings": [
                {
                    "rule_id": "llm_semantic_risk",
                    "severity": "warning",
                    "message": "First finding.",
                },
                {
                    "rule_id": "llm_compliance_gap",
                    "severity": "error",
                    "message": "Second finding.",
                    "suggestion": "Revise the statement.",
                },
            ],
            "summary": {
                "overall_risk": "medium",
                "summary": "Two issues were detected.",
                "recommended_action": "Revise before publishing.",
                "confidence": 0.7,
            },
        },
        request,
    )

    assert [finding.rule_id for finding in result.findings] == [
        "llm_semantic_risk",
        "llm_compliance_gap",
    ]
    assert result.summary is not None
    assert result.summary.overall_risk == "medium"
    assert result.summary.summary == "Two issues were detected."
    assert result.summary.recommended_action == "Revise before publishing."
    assert result.summary.confidence == 0.7


@pytest.mark.parametrize(
    ("response", "expected_fragment"),
    [
        ({"findings": [{"rule_id": "x", "severity": "medium", "message": "bad"}]}, "findings.0.severity"),
        ({"findings": [{"rule_id": " ", "severity": "warning", "message": "bad"}]}, "findings.0.rule_id"),
        ({"findings": [{"rule_id": "x", "severity": "warning", "message": " "}]} , "findings.0.message"),
        ({}, "findings: Field required"),
        ({"findings": "not-a-list"}, "findings: Input should be a valid list"),
        (None, "response must not be None"),
    ],
)
def test_pydanticai_response_validation_rejects_invalid_payloads(
    response: object,
    expected_fragment: str,
) -> None:
    with pytest.raises(LLMResponseValidationError) as exc_info:
        pydanticai_response_to_llm_review_result(
            response,
            _build_request(),
            provider="pydanticai",
            model="gpt-4o-mini",
        )

    assert expected_fragment in str(exc_info.value)


def test_pydanticai_response_validation_error_redacts_prompt_and_article_content() -> None:
    request = _build_request()
    payload = build_pydanticai_review_request(request)

    with pytest.raises(LLMResponseValidationError) as exc_info:
        pydanticai_response_to_llm_review_result(
            {"findings": [{"rule_id": "x", "severity": "medium", "message": "bad"}]},
            request,
            provider="pydanticai",
            model="gpt-4o-mini",
        )

    message = str(exc_info.value)

    assert "sk-test-secret" not in message
    assert request.content not in message
    assert payload.user_prompt not in message
    assert "content_start" not in message
