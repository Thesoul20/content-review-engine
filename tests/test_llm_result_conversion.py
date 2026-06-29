from __future__ import annotations

import os
import socket

import pytest

from content_review_engine.llm import (
    LLM_REVIEW_RESULT_SCHEMA_VERSION,
    LLM_SEMANTIC_OUTPUT_SCHEMA_METADATA_KEY,
    LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION,
    LLM_SEMANTIC_REVIEW_PROMPT_VERSION,
    LLMReviewRequest,
    LLMReviewResult,
    PydanticAIReviewer,
    ValidatedLLMSemanticReviewOutput,
    convert_validated_semantic_output_to_llm_review_result,
)


def _build_request() -> LLMReviewRequest:
    return LLMReviewRequest(
        content="This article says the treatment is always safe.",
        profile_name="wechat-strict",
        content_path="articles/example.md",
        review_goal="semantic_review",
    )


def _build_output(
    findings: list[dict[str, object]] | None = None,
    *,
    summary: str = "发现一处风险。",
) -> ValidatedLLMSemanticReviewOutput:
    return ValidatedLLMSemanticReviewOutput(
        schema_version=LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION,
        summary=summary,
        findings=tuple(findings or ()),
    )


def test_convert_empty_findings_preserves_summary_and_metadata() -> None:
    result = convert_validated_semantic_output_to_llm_review_result(
        _build_output(findings=[], summary="未发现明显风险。"),
        _build_request(),
        provider="pydanticai",
        model="gpt-4o-mini",
    )

    assert result.schema_version == LLM_REVIEW_RESULT_SCHEMA_VERSION
    assert result.provider == "pydanticai"
    assert result.model == "gpt-4o-mini"
    assert result.prompt_version == LLM_SEMANTIC_REVIEW_PROMPT_VERSION
    assert result.profile_name == "wechat-strict"
    assert result.findings == ()
    assert result.summary is not None
    assert result.summary.summary == "未发现明显风险。"
    assert result.metadata == {
        LLM_SEMANTIC_OUTPUT_SCHEMA_METADATA_KEY: LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION,
    }


def test_convert_single_finding_maps_all_supported_fields() -> None:
    result = convert_validated_semantic_output_to_llm_review_result(
        _build_output(
            findings=[
                {
                    "rule_id": "llm.semantic.overclaim",
                    "severity": "warning",
                    "line": 12,
                    "column": 3,
                    "message": "表述过于绝对。",
                    "evidence": "本产品绝对安全",
                    "suggestion": "改为更审慎的表达。",
                    "confidence": 0.82,
                }
            ]
        ),
        _build_request(),
        provider="pydanticai",
        model="gpt-4o-mini",
    )

    finding = result.findings[0]
    assert finding.rule_id == "llm.semantic.overclaim"
    assert finding.severity == "warning"
    assert finding.line == 12
    assert finding.column == 3
    assert finding.message == "表述过于绝对。"
    assert finding.matched_text == "本产品绝对安全"
    assert finding.suggestion == "改为更审慎的表达。"
    assert finding.confidence == 0.82


def test_convert_multiple_findings_preserves_order_and_severity() -> None:
    result = convert_validated_semantic_output_to_llm_review_result(
        _build_output(
            findings=[
                {
                    "rule_id": "llm.semantic.overclaim",
                    "severity": "warning",
                    "line": 2,
                    "column": 1,
                    "message": "第一处风险。",
                    "evidence": "always safe",
                    "suggestion": "降低绝对化程度。",
                    "confidence": 0.71,
                },
                {
                    "rule_id": "llm.semantic.risky_advice",
                    "severity": "critical",
                    "line": 8,
                    "column": 5,
                    "message": "第二处风险。",
                    "evidence": "stop medication immediately",
                    "suggestion": "加入专业建议与免责声明。",
                    "confidence": 0.94,
                },
            ]
        ),
        _build_request(),
    )

    assert [finding.rule_id for finding in result.findings] == [
        "llm.semantic.overclaim",
        "llm.semantic.risky_advice",
    ]
    assert [finding.severity for finding in result.findings] == ["warning", "critical"]


def test_convert_keeps_null_confidence_as_none() -> None:
    result = convert_validated_semantic_output_to_llm_review_result(
        _build_output(
            findings=[
                {
                    "rule_id": "llm.semantic.needs_human_review",
                    "severity": "info",
                    "line": None,
                    "column": None,
                    "message": "需要人工复核。",
                    "evidence": "建议咨询专业人士",
                    "suggestion": "补充适用范围。",
                    "confidence": None,
                }
            ]
        ),
        _build_request(),
    )

    finding = result.findings[0]
    assert finding.line is None
    assert finding.column is None
    assert finding.confidence is None


def test_convert_does_not_modify_input_objects() -> None:
    request = _build_request()
    output = _build_output(
        findings=[
            {
                "rule_id": "llm.semantic.misleading",
                "severity": "error",
                "line": 4,
                "column": 2,
                "message": "可能误导读者。",
                "evidence": "guaranteed result",
                "suggestion": "补充限制条件。",
                "confidence": 0.67,
            }
        ]
    )
    request_before = request.model_dump()
    output_before = output.model_dump()

    convert_validated_semantic_output_to_llm_review_result(output, request)

    assert request.model_dump() == request_before
    assert output.model_dump() == output_before


def test_convert_does_not_read_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class GuardedEnviron(dict[str, str]):
        def __getitem__(self, key: str) -> str:
            raise AssertionError(f"Unexpected environ access: {key}")

        def get(self, key: str, default: object = None) -> object:
            raise AssertionError(f"Unexpected environ access: {key}")

    monkeypatch.setattr(os, "environ", GuardedEnviron(), raising=False)

    result = convert_validated_semantic_output_to_llm_review_result(
        _build_output(findings=[]),
        _build_request(),
    )

    assert result.findings == ()


def test_convert_does_not_make_network_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    result = convert_validated_semantic_output_to_llm_review_result(
        _build_output(findings=[]),
        _build_request(),
    )

    assert result.summary is not None


def test_convert_does_not_call_provider_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_provider(*args: object, **kwargs: object) -> None:
        raise AssertionError("conversion should not call provider code")

    monkeypatch.setattr(PydanticAIReviewer, "run_semantic_review", fail_provider)

    result = convert_validated_semantic_output_to_llm_review_result(
        _build_output(findings=[]),
        _build_request(),
    )

    assert isinstance(result, LLMReviewResult)
