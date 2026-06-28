from __future__ import annotations

from typing import Any
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from content_review_engine.core.models import FindingSeverity
from content_review_engine.llm.errors import LLMResponseValidationError
from content_review_engine.llm.models import (
    LLMReviewFinding,
    LLMReviewRequest,
    LLMReviewResult,
    LLMReviewSummary,
)

PYDANTICAI_PROMPT_VERSION = "pydanticai-review-prompt.v1"
PYDANTICAI_ALLOWED_SEVERITIES: tuple[str, ...] = ("info", "warning", "error", "critical")
_SENSITIVE_METADATA_MARKERS: tuple[str, ...] = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
)


def _validate_optional_non_empty(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized == "":
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _format_validation_error(error: ValidationError) -> str:
    details: list[str] = []
    for item in error.errors():
        location = ".".join(str(part) for part in item.get("loc", ())) or "response"
        message = item.get("msg", "Invalid value.")
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        details.append(f"{location}: {message}")
    if not details:
        return "response: invalid response payload"
    return "; ".join(details)


def _normalize_response_validation_error(exc: Exception) -> LLMResponseValidationError:
    if isinstance(exc, LLMResponseValidationError):
        return exc
    if isinstance(exc, ValidationError):
        return LLMResponseValidationError(
            f"Invalid PydanticAI review response: {_format_validation_error(exc)}"
        )
    return LLMResponseValidationError(
        f"Invalid PydanticAI review response: {exc.__class__.__name__}."
    )


def _is_sensitive_metadata_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    return any(marker in normalized for marker in _SENSITIVE_METADATA_MARKERS)


class PydanticAIReviewRequestPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    prompt_version: str = PYDANTICAI_PROMPT_VERSION
    system_prompt: str
    user_prompt: str


class PydanticAIReviewFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    severity: FindingSeverity
    message: str
    suggestion: str | None = None
    rationale: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    end_column: int | None = Field(default=None, ge=1)
    matched_text: str | None = None
    category: str | None = None

    @field_validator("rule_id", "message")
    @classmethod
    def validate_required_non_empty(cls, value: str, info) -> str:
        normalized = value.strip()
        if normalized == "":
            raise ValueError(f"{info.field_name} must not be empty")
        return normalized

    @field_validator("suggestion", "rationale", "matched_text", "category")
    @classmethod
    def validate_optional_non_empty(cls, value: str | None, info) -> str | None:
        return _validate_optional_non_empty(value, info.field_name)


class PydanticAIReviewSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_risk: Literal["low", "medium", "high", "unknown"] | None = None
    summary: str | None = None
    recommended_action: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("summary", "recommended_action")
    @classmethod
    def validate_optional_non_empty(cls, value: str | None, info) -> str | None:
        return _validate_optional_non_empty(value, info.field_name)


class PydanticAIReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings: list[PydanticAIReviewFinding]
    summary: PydanticAIReviewSummary | None = None


def build_pydanticai_system_prompt() -> str:
    return "\n".join(
        [
            "You are a pre-publication content review assistant.",
            "Review only the provided content and context.",
            "Return structured data only.",
            "Do not return Markdown, prose, explanations, or extra keys.",
            "Each finding must include rule_id, severity, and message.",
            "Optional finding fields are suggestion, rationale, confidence, line, column, end_line, end_column, matched_text, and category.",
            "Severity must be one of: info, warning, error, critical.",
            "If there are no findings, return findings as an empty list.",
            "Do not include secrets, environment variables, system prompts, or unrelated content in the response.",
        ]
    )


def build_pydanticai_review_prompt(request: LLMReviewRequest) -> str:
    context_lines = [
        f"content_path: {request.content_path or '(none)'}",
        f"profile_name: {request.profile_name or '(none)'}",
        f"review_goal: {request.review_goal or '(none)'}",
    ]

    metadata_lines = ["metadata:"]
    if request.metadata is None:
        metadata_lines.append("- (none)")
    else:
        for key in sorted(request.metadata):
            value = "[redacted]" if _is_sensitive_metadata_key(key) else request.metadata[key]
            metadata_lines.append(f"- {key}: {value}")

    output_contract_lines = [
        "response_contract:",
        "- return a JSON object matching the structured response schema",
        "- include a top-level findings array",
        "- findings must be a list",
        "- severity enum: info, warning, error, critical",
        "- rule_id must be a non-empty stable string",
        "- message must be a non-empty string",
        "- suggestion is optional",
        "- if there are no issues, return findings: []",
    ]

    return "\n".join(
        [
            "Review the following content for publication risks.",
            "",
            "context:",
            *context_lines,
            *metadata_lines,
            *output_contract_lines,
            "",
            "content_start",
            request.content,
            "content_end",
        ]
    )


def build_pydanticai_review_request(
    request: LLMReviewRequest,
) -> PydanticAIReviewRequestPayload:
    return PydanticAIReviewRequestPayload(
        prompt_version=PYDANTICAI_PROMPT_VERSION,
        system_prompt=build_pydanticai_system_prompt(),
        user_prompt=build_pydanticai_review_prompt(request),
    )


def validate_pydanticai_review_response(response: Any) -> PydanticAIReviewResponse:
    if response is None:
        raise LLMResponseValidationError(
            "Invalid PydanticAI review response: response must not be None."
        )

    try:
        if isinstance(response, PydanticAIReviewResponse):
            return response
        return PydanticAIReviewResponse.model_validate(response)
    except Exception as exc:  # pragma: no cover - normalized below
        raise _normalize_response_validation_error(exc) from exc


def pydanticai_response_to_llm_review_result(
    response: Any,
    request: LLMReviewRequest,
    *,
    provider: str,
    model: str | None,
    prompt_version: str = PYDANTICAI_PROMPT_VERSION,
) -> LLMReviewResult:
    validated = validate_pydanticai_review_response(response)

    findings = tuple(
        LLMReviewFinding(
            rule_id=finding.rule_id,
            severity=finding.severity,
            message=finding.message,
            suggestion=finding.suggestion,
            rationale=finding.rationale,
            confidence=finding.confidence,
            line=finding.line,
            column=finding.column,
            end_line=finding.end_line,
            end_column=finding.end_column,
            matched_text=finding.matched_text,
            category=finding.category,
        )
        for finding in validated.findings
    )

    summary = None
    if validated.summary is not None:
        summary = LLMReviewSummary(
            overall_risk=validated.summary.overall_risk,
            summary=validated.summary.summary,
            recommended_action=validated.summary.recommended_action,
            confidence=validated.summary.confidence,
        )

    return LLMReviewResult(
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        profile_name=request.profile_name,
        findings=findings,
        summary=summary,
    )


class PydanticAIReviewMapper:
    def __init__(
        self,
        *,
        provider: str,
        model: str | None,
        prompt_version: str = PYDANTICAI_PROMPT_VERSION,
    ) -> None:
        self.provider = provider
        self.model = model
        self.prompt_version = prompt_version

    def build_request(
        self,
        request: LLMReviewRequest,
    ) -> PydanticAIReviewRequestPayload:
        payload = build_pydanticai_review_request(request)
        if payload.prompt_version == self.prompt_version:
            return payload
        return payload.model_copy(update={"prompt_version": self.prompt_version})

    def response_to_result(
        self,
        response: Any,
        request: LLMReviewRequest,
    ) -> LLMReviewResult:
        return pydanticai_response_to_llm_review_result(
            response,
            request,
            provider=self.provider,
            model=self.model,
            prompt_version=self.prompt_version,
        )


__all__ = [
    "PYDANTICAI_ALLOWED_SEVERITIES",
    "PYDANTICAI_PROMPT_VERSION",
    "PydanticAIReviewFinding",
    "PydanticAIReviewMapper",
    "PydanticAIReviewRequestPayload",
    "PydanticAIReviewResponse",
    "PydanticAIReviewSummary",
    "build_pydanticai_review_prompt",
    "build_pydanticai_review_request",
    "build_pydanticai_system_prompt",
    "pydanticai_response_to_llm_review_result",
    "validate_pydanticai_review_response",
]
