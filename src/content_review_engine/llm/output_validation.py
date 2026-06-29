from __future__ import annotations

import json
import re
import textwrap
from typing import Any

from content_review_engine.llm.errors import (
    LLMSemanticReviewOutputParseError,
    LLMSemanticReviewOutputValidationError,
)
from content_review_engine.llm.models import (
    LLM_SEMANTIC_ALLOWED_SEVERITIES,
    LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION,
    ValidatedLLMSemanticFinding,
    ValidatedLLMSemanticReviewOutput,
)

_FENCED_JSON_BLOCK_RE = re.compile(
    r"^```json[ \t]*\r?\n(?P<body>[\s\S]*?)\r?\n```$",
    re.IGNORECASE,
)


def _raise_parse_error(message: str) -> None:
    raise LLMSemanticReviewOutputParseError(f"raw_output: {message}")


def _raise_validation_error(path: str, message: str) -> None:
    raise LLMSemanticReviewOutputValidationError(f"{path}: {message}")


def _require_object(value: object, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _raise_validation_error(path, "must be an object")
    return value


def _require_non_empty_string(value: object, path: str) -> str:
    if not isinstance(value, str):
        _raise_validation_error(path, "must be a non-empty string")
    normalized = value.strip()
    if normalized == "":
        _raise_validation_error(path, "must be a non-empty string")
    return normalized


def _require_findings_array(value: object) -> list[object]:
    if not isinstance(value, list):
        _raise_validation_error("findings", "must be an array")
    return value


def _validate_rule_id(value: object, path: str) -> str:
    normalized = _require_non_empty_string(value, path)
    if not normalized.startswith("llm."):
        _raise_validation_error(path, "must start with 'llm.'")
    return normalized


def _validate_severity(value: object, path: str) -> str:
    normalized = _require_non_empty_string(value, path)
    if normalized not in LLM_SEMANTIC_ALLOWED_SEVERITIES:
        allowed = ", ".join(LLM_SEMANTIC_ALLOWED_SEVERITIES)
        _raise_validation_error(path, f"must be one of: {allowed}")
    return normalized


def _validate_optional_position(value: object, path: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        _raise_validation_error(path, "must be an integer greater than or equal to 1 or null")
    if value < 1:
        _raise_validation_error(path, "must be greater than or equal to 1")
    return value


def _validate_optional_confidence(value: object, path: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _raise_validation_error(path, "must be a number between 0 and 1 or null")
    normalized = float(value)
    if normalized < 0.0 or normalized > 1.0:
        _raise_validation_error(path, "must be between 0 and 1 inclusive")
    return normalized


def extract_llm_semantic_review_json(raw_output: str) -> str:
    stripped = textwrap.dedent(raw_output).strip()
    if stripped == "":
        _raise_parse_error("must not be empty")

    if stripped.startswith("```"):
        if stripped.count("```") != 2:
            _raise_parse_error("must be pure JSON or a single fenced JSON block")
        fenced_match = _FENCED_JSON_BLOCK_RE.fullmatch(stripped)
        if fenced_match is not None:
            return fenced_match.group("body").strip()
        _raise_parse_error("must be pure JSON or a single fenced JSON block")

    fenced_match = _FENCED_JSON_BLOCK_RE.fullmatch(stripped)
    if fenced_match is not None:
        return fenced_match.group("body").strip()

    if "```" in raw_output:
        _raise_parse_error("must be pure JSON or a single fenced JSON block")

    return stripped


def validate_llm_semantic_review_output(
    data: object,
) -> ValidatedLLMSemanticReviewOutput:
    payload = _require_object(data, "root")

    if "schema_version" not in payload:
        _raise_validation_error("schema_version", "is required")
    schema_version = _require_non_empty_string(payload["schema_version"], "schema_version")
    if schema_version != LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION:
        _raise_validation_error(
            "schema_version",
            f"must be '{LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION}'",
        )

    if "summary" not in payload:
        _raise_validation_error("summary", "is required")
    summary = _require_non_empty_string(payload["summary"], "summary")

    if "findings" not in payload:
        _raise_validation_error("findings", "is required")

    findings_data = _require_findings_array(payload["findings"])
    findings: list[ValidatedLLMSemanticFinding] = []
    for index, item in enumerate(findings_data):
        path_prefix = f"findings[{index}]"
        finding_payload = _require_object(item, path_prefix)

        if "rule_id" not in finding_payload:
            _raise_validation_error(f"{path_prefix}.rule_id", "is required")
        if "severity" not in finding_payload:
            _raise_validation_error(f"{path_prefix}.severity", "is required")
        if "message" not in finding_payload:
            _raise_validation_error(f"{path_prefix}.message", "is required")
        if "evidence" not in finding_payload:
            _raise_validation_error(f"{path_prefix}.evidence", "is required")
        if "suggestion" not in finding_payload:
            _raise_validation_error(f"{path_prefix}.suggestion", "is required")

        findings.append(
            ValidatedLLMSemanticFinding(
                rule_id=_validate_rule_id(finding_payload["rule_id"], f"{path_prefix}.rule_id"),
                severity=_validate_severity(
                    finding_payload["severity"],
                    f"{path_prefix}.severity",
                ),
                line=_validate_optional_position(
                    finding_payload.get("line"),
                    f"{path_prefix}.line",
                ),
                column=_validate_optional_position(
                    finding_payload.get("column"),
                    f"{path_prefix}.column",
                ),
                message=_require_non_empty_string(
                    finding_payload["message"],
                    f"{path_prefix}.message",
                ),
                evidence=_require_non_empty_string(
                    finding_payload["evidence"],
                    f"{path_prefix}.evidence",
                ),
                suggestion=_require_non_empty_string(
                    finding_payload["suggestion"],
                    f"{path_prefix}.suggestion",
                ),
                confidence=_validate_optional_confidence(
                    finding_payload.get("confidence"),
                    f"{path_prefix}.confidence",
                ),
            )
        )

    return ValidatedLLMSemanticReviewOutput(
        schema_version=schema_version,
        summary=summary,
        findings=tuple(findings),
    )


def parse_llm_semantic_review_output(raw_output: str) -> ValidatedLLMSemanticReviewOutput:
    extracted_json = extract_llm_semantic_review_json(raw_output)
    try:
        parsed = json.loads(extracted_json)
    except json.JSONDecodeError as exc:
        _raise_parse_error(f"invalid JSON at line {exc.lineno} column {exc.colno}")
    return validate_llm_semantic_review_output(parsed)


__all__ = [
    "extract_llm_semantic_review_json",
    "parse_llm_semantic_review_output",
    "validate_llm_semantic_review_output",
]
