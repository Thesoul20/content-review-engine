from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from pydantic import field_validator

from content_review_engine.core.models import FindingSeverity

LLM_REVIEW_RESULT_SCHEMA_VERSION = "llm-review-result.v1"
LLM_OVERALL_RISK_VALUES: tuple[str, ...] = ("low", "medium", "high", "unknown")


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


class LLMReviewRequest(BaseModel):
    content: str
    profile_name: str | None = None
    content_path: str | None = None
    review_goal: str | None = None
    metadata: dict[str, str] | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = value.strip()
        if normalized == "":
            raise ValueError("content must not be empty")
        return normalized

    @field_validator("profile_name", "content_path", "review_goal")
    @classmethod
    def validate_optional_non_empty(cls, value: str | None, info) -> str | None:
        return _validate_optional_non_empty(value, info.field_name)

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


__all__ = [
    "LLM_OVERALL_RISK_VALUES",
    "LLM_REVIEW_RESULT_SCHEMA_VERSION",
    "LLMReviewFinding",
    "LLMReviewRequest",
    "LLMReviewResult",
    "LLMReviewSummary",
]
