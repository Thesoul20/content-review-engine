from __future__ import annotations

import os
import socket

import pytest

from content_review_engine.llm import (
    LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION,
    LLMSemanticReviewOutputParseError,
    LLMSemanticReviewOutputValidationError,
    extract_llm_semantic_review_json,
    parse_llm_semantic_review_output,
    validate_llm_semantic_review_output,
)


def _valid_payload() -> dict[str, object]:
    return {
        "schema_version": LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION,
        "summary": "发现一处需要人工复核的表述。",
        "findings": [
            {
                "rule_id": "llm.semantic.overclaim",
                "severity": "warning",
                "line": 12,
                "column": 1,
                "message": "表述过于绝对。",
                "evidence": "本产品绝对安全",
                "suggestion": "改为更审慎的表达。",
                "confidence": 0.82,
            }
        ],
    }


def test_parse_valid_plain_json_output() -> None:
    raw_output = """
    {
      "schema_version": "llm-semantic-review-output.v1",
      "summary": "发现一处需要人工复核的表述。",
      "findings": [
        {
          "rule_id": "llm.semantic.overclaim",
          "severity": "warning",
          "line": 12,
          "column": 1,
          "message": "表述过于绝对。",
          "evidence": "本产品绝对安全",
          "suggestion": "改为更审慎的表达。",
          "confidence": 0.82
        }
      ]
    }
    """

    result = parse_llm_semantic_review_output(raw_output)

    assert result.schema_version == LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION
    assert result.summary == "发现一处需要人工复核的表述。"
    assert len(result.findings) == 1
    assert result.findings[0].rule_id == "llm.semantic.overclaim"
    assert result.findings[0].confidence == 0.82


def test_parse_valid_fenced_json_output() -> None:
    raw_output = """
    ```json
    {
      "schema_version": "llm-semantic-review-output.v1",
      "summary": "无明显语义风险。",
      "findings": []
    }
    ```
    """

    result = parse_llm_semantic_review_output(raw_output)

    assert result.summary == "无明显语义风险。"
    assert result.findings == ()


def test_extract_fenced_json_block_returns_json_body() -> None:
    raw_output = """
    ```json
    {"schema_version":"llm-semantic-review-output.v1","summary":"ok","findings":[]}
    ```
    """

    extracted = extract_llm_semantic_review_json(raw_output)

    assert extracted.startswith("{")
    assert extracted.endswith("}")


def test_validate_accepts_empty_findings() -> None:
    result = validate_llm_semantic_review_output(
        {
            "schema_version": LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION,
            "summary": "未发现问题。",
            "findings": [],
        }
    )

    assert result.findings == ()


def test_validate_accepts_finding_with_null_position_and_confidence() -> None:
    result = validate_llm_semantic_review_output(
        {
            "schema_version": LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION,
            "summary": "发现一处表述风险。",
            "findings": [
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
            ],
        }
    )

    assert result.findings[0].line is None
    assert result.findings[0].column is None
    assert result.findings[0].confidence is None


@pytest.mark.parametrize(
    ("payload", "expected_message"),
    [
        (
            {"summary": "x", "findings": []},
            "schema_version: is required",
        ),
        (
            {
                "schema_version": "wrong-schema",
                "summary": "x",
                "findings": [],
            },
            "schema_version: must be 'llm-semantic-review-output.v1'",
        ),
        (
            {
                "schema_version": LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION,
                "findings": [],
            },
            "summary: is required",
        ),
        (
            {
                "schema_version": LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION,
                "summary": "x",
            },
            "findings: is required",
        ),
        (
            {
                "schema_version": LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION,
                "summary": "x",
                "findings": {},
            },
            "findings: must be an array",
        ),
    ],
)
def test_validate_top_level_contract_errors(
    payload: dict[str, object],
    expected_message: str,
) -> None:
    with pytest.raises(LLMSemanticReviewOutputValidationError) as exc_info:
        validate_llm_semantic_review_output(payload)

    assert str(exc_info.value) == expected_message


def test_validate_rejects_invalid_rule_id_with_field_path() -> None:
    payload = _valid_payload()
    payload["findings"] = [dict(payload["findings"][0], rule_id="semantic.overclaim")]  # type: ignore[index]

    with pytest.raises(LLMSemanticReviewOutputValidationError) as exc_info:
        validate_llm_semantic_review_output(payload)

    assert str(exc_info.value) == "findings[0].rule_id: must start with 'llm.'"


def test_validate_rejects_invalid_severity_with_field_path() -> None:
    payload = _valid_payload()
    payload["findings"] = [dict(payload["findings"][0], severity="medium")]  # type: ignore[index]

    with pytest.raises(LLMSemanticReviewOutputValidationError) as exc_info:
        validate_llm_semantic_review_output(payload)

    assert str(exc_info.value) == "findings[0].severity: must be one of: info, warning, error, critical"


@pytest.mark.parametrize(
    ("field_name", "field_value", "expected_message"),
    [
        ("line", 0, "findings[0].line: must be greater than or equal to 1"),
        ("column", -1, "findings[0].column: must be greater than or equal to 1"),
        (
            "line",
            "12",
            "findings[0].line: must be an integer greater than or equal to 1 or null",
        ),
        (
            "column",
            "1",
            "findings[0].column: must be an integer greater than or equal to 1 or null",
        ),
    ],
)
def test_validate_rejects_invalid_position_fields(
    field_name: str,
    field_value: object,
    expected_message: str,
) -> None:
    payload = _valid_payload()
    payload["findings"] = [dict(payload["findings"][0], **{field_name: field_value})]  # type: ignore[index]

    with pytest.raises(LLMSemanticReviewOutputValidationError) as exc_info:
        validate_llm_semantic_review_output(payload)

    assert str(exc_info.value) == expected_message


@pytest.mark.parametrize(("field_name",), [("message",), ("evidence",), ("suggestion",)])
def test_validate_rejects_empty_required_finding_strings(field_name: str) -> None:
    payload = _valid_payload()
    payload["findings"] = [dict(payload["findings"][0], **{field_name: "   "})]  # type: ignore[index]

    with pytest.raises(LLMSemanticReviewOutputValidationError) as exc_info:
        validate_llm_semantic_review_output(payload)

    assert str(exc_info.value) == f"findings[0].{field_name}: must be a non-empty string"


@pytest.mark.parametrize(
    ("confidence", "expected_message"),
    [
        (1.2, "findings[0].confidence: must be between 0 and 1 inclusive"),
        (-0.1, "findings[0].confidence: must be between 0 and 1 inclusive"),
        ("0.82", "findings[0].confidence: must be a number between 0 and 1 or null"),
    ],
)
def test_validate_rejects_invalid_confidence(
    confidence: object,
    expected_message: str,
) -> None:
    payload = _valid_payload()
    payload["findings"] = [dict(payload["findings"][0], confidence=confidence)]  # type: ignore[index]

    with pytest.raises(LLMSemanticReviewOutputValidationError) as exc_info:
        validate_llm_semantic_review_output(payload)

    assert str(exc_info.value) == expected_message


@pytest.mark.parametrize(
    ("raw_output", "expected_message"),
        [
            ("not json", "raw_output: invalid JSON at line 1 column 1"),
            ('{"schema_version": ', "raw_output: invalid JSON at line 1 column 19"),
            (
                "```json\n{}\n```\n```json\n{}\n```",
                "raw_output: must be pure JSON or a single fenced JSON block",
            ),
    ],
)
def test_parse_rejects_non_json_or_incomplete_json(
    raw_output: str,
    expected_message: str,
) -> None:
    with pytest.raises(LLMSemanticReviewOutputParseError) as exc_info:
        parse_llm_semantic_review_output(raw_output)

    assert str(exc_info.value) == expected_message


def test_parse_error_message_does_not_include_full_raw_output_or_secret_like_value() -> None:
    raw_output = 'not json sk-test-secret-1234567890'

    with pytest.raises(LLMSemanticReviewOutputParseError) as exc_info:
        parse_llm_semantic_review_output(raw_output)

    message = str(exc_info.value)
    assert "sk-test-secret-1234567890" not in message
    assert raw_output not in message


def test_validation_error_message_does_not_include_secret_like_value() -> None:
    payload = _valid_payload()
    payload["findings"] = [
        dict(
            payload["findings"][0],  # type: ignore[index]
            confidence="sk-test-secret-1234567890",
        )
    ]

    with pytest.raises(LLMSemanticReviewOutputValidationError) as exc_info:
        validate_llm_semantic_review_output(payload)

    message = str(exc_info.value)
    assert "sk-test-secret-1234567890" not in message
    assert "findings[0].confidence" in message


def test_parser_does_not_read_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_getenv(*args: object, **kwargs: object) -> str:
        raise AssertionError("output parser should not read environment variables")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    result = parse_llm_semantic_review_output(
        '{"schema_version":"llm-semantic-review-output.v1","summary":"ok","findings":[]}'
    )

    assert result.summary == "ok"


def test_parser_does_not_access_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*args: object, **kwargs: object) -> socket.socket:
        raise AssertionError("output parser should not access the network")

    monkeypatch.setattr(socket, "create_connection", fail_network)

    result = parse_llm_semantic_review_output(
        '{"schema_version":"llm-semantic-review-output.v1","summary":"ok","findings":[]}'
    )

    assert result.findings == ()
