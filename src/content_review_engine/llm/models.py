from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic import field_validator
from pydantic import model_validator

from content_review_engine.core.models import FindingSeverity

LLM_REVIEW_RESULT_SCHEMA_VERSION = "llm-review-result.v1"
LLM_SIDECAR_RESULT_SCHEMA_VERSION = "llm-sidecar-result.v2"
LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION = "llm-semantic-review-output.v1"
LLM_OVERALL_RISK_VALUES: tuple[str, ...] = ("low", "medium", "high", "unknown")
LLM_SIDECAR_STATUS_VALUES: tuple[str, ...] = ("success", "failed", "skipped")
LLM_SIDECAR_PROVIDER_SOURCE_VALUES: tuple[str, ...] = (
    "explicit",
    "default",
    "config",
)
LLM_SEMANTIC_ALLOWED_SEVERITIES: tuple[str, ...] = (
    "info",
    "warning",
    "error",
    "critical",
)
LLM_SEMANTIC_RULE_IDS: tuple[str, ...] = (
    "llm.semantic.overclaim",
    "llm.semantic.misleading",
    "llm.semantic.unsupported_claim",
    "llm.semantic.risky_advice",
    "llm.semantic.ambiguous_expression",
    "llm.semantic.inappropriate_tone",
    "llm.semantic.needs_human_review",
)


def _validate_optional_non_empty(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized == "":
        raise ValueError(f"{field_name} must not be empty")
    return normalized


class LLMReviewFinding(BaseModel):
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

    @field_validator(
        "suggestion",
        "rationale",
        "matched_text",
        "category",
    )
    @classmethod
    def validate_optional_non_empty(cls, value: str | None, info) -> str | None:
        return _validate_optional_non_empty(value, info.field_name)


class LLMReviewSummary(BaseModel):
    overall_risk: Literal["low", "medium", "high", "unknown"] | None = None
    summary: str | None = None
    recommended_action: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("summary", "recommended_action")
    @classmethod
    def validate_optional_non_empty(cls, value: str | None, info) -> str | None:
        return _validate_optional_non_empty(value, info.field_name)


class LLMReviewResult(BaseModel):
    schema_version: str = LLM_REVIEW_RESULT_SCHEMA_VERSION
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    profile_name: str | None = None
    findings: tuple[LLMReviewFinding, ...] = Field(default_factory=tuple)
    summary: LLMReviewSummary | None = None
    metadata: dict[str, str] | None = None

    @field_validator("provider", "model", "prompt_version", "profile_name")
    @classmethod
    def validate_optional_non_empty(cls, value: str | None, info) -> str | None:
        return _validate_optional_non_empty(value, info.field_name)


class LLMSidecarError(BaseModel):
    error_type: str
    message: str

    @field_validator("error_type", "message")
    @classmethod
    def validate_required_non_empty(cls, value: str, info) -> str:
        normalized = value.strip()
        if normalized == "":
            raise ValueError(f"{info.field_name} must not be empty")
        return normalized


class LLMSidecarSummary(BaseModel):
    file_count: int = Field(ge=0)
    succeeded_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)
    finding_count: int = Field(ge=0)


class LLMSidecarFile(BaseModel):
    path: str
    status: Literal["success", "failed", "skipped"]
    finding_count: int = Field(default=0, ge=0)
    review: LLMReviewResult | None = None
    error: LLMSidecarError | None = None

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        normalized = value.strip()
        if normalized == "":
            raise ValueError("path must not be empty")
        return normalized

    @model_validator(mode="after")
    def validate_status_payload(self) -> "LLMSidecarFile":
        if self.status == "success" and self.error is not None:
            raise ValueError("success sidecar files must not include error")
        if self.status == "failed" and self.error is None:
            raise ValueError("failed sidecar files must include error")
        if self.status == "skipped" and self.error is not None:
            raise ValueError("skipped sidecar files must not include error")
        return self


class LLMSidecarResult(BaseModel):
    schema_version: str = LLM_SIDECAR_RESULT_SCHEMA_VERSION
    llm_provider: str = "mock"
    llm_provider_source: Literal["explicit", "default", "config"] = "default"
    summary: LLMSidecarSummary
    files: tuple[LLMSidecarFile, ...] = Field(default_factory=tuple)

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, value: str) -> str:
        normalized = value.strip()
        if normalized == "":
            raise ValueError("llm_provider must not be empty")
        return normalized


class LLMReviewRequest(BaseModel):
    content: str
    profile_name: str | None = None
    content_path: str | None = None
    review_goal: str | None = None
    review_language: str = "zh-CN"
    deterministic_findings: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, str] | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = value.strip()
        if normalized == "":
            raise ValueError("content must not be empty")
        return normalized

    @field_validator("profile_name", "content_path", "review_goal", "review_language")
    @classmethod
    def validate_optional_non_empty(cls, value: str | None, info) -> str | None:
        return _validate_optional_non_empty(value, info.field_name)

    @field_validator("deterministic_findings")
    @classmethod
    def validate_deterministic_findings(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        normalized_findings: list[str] = []
        for item in value:
            normalized_item = item.strip()
            if normalized_item == "":
                raise ValueError("deterministic_findings items must not be empty")
            normalized_findings.append(normalized_item)
        return tuple(normalized_findings)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None

        normalized_metadata: dict[str, str] = {}
        for key, item_value in value.items():
            normalized_key = key.strip()
            normalized_value = item_value.strip()
            if normalized_key == "":
                raise ValueError("metadata keys must not be empty")
            if normalized_value == "":
                raise ValueError(f"metadata value for '{normalized_key}' must not be empty")
            normalized_metadata[normalized_key] = normalized_value
        return normalized_metadata


class ValidatedLLMSemanticFinding(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule_id: str
    severity: Literal["info", "warning", "error", "critical"]
    line: int | None = None
    column: int | None = None
    message: str
    evidence: str
    suggestion: str
    confidence: float | None = None


class ValidatedLLMSemanticReviewOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION
    summary: str
    findings: tuple[ValidatedLLMSemanticFinding, ...] = Field(default_factory=tuple)


__all__ = [
    "LLM_OVERALL_RISK_VALUES",
    "LLM_REVIEW_RESULT_SCHEMA_VERSION",
    "LLM_SEMANTIC_ALLOWED_SEVERITIES",
    "LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION",
    "LLM_SEMANTIC_RULE_IDS",
    "LLM_SIDECAR_PROVIDER_SOURCE_VALUES",
    "LLM_SIDECAR_RESULT_SCHEMA_VERSION",
    "LLM_SIDECAR_STATUS_VALUES",
    "LLMSidecarError",
    "LLMSidecarFile",
    "LLMSidecarResult",
    "LLMSidecarSummary",
    "LLMReviewFinding",
    "LLMReviewRequest",
    "LLMReviewResult",
    "LLMReviewSummary",
    "ValidatedLLMSemanticFinding",
    "ValidatedLLMSemanticReviewOutput",
]
