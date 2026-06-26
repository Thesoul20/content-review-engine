from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field
from pydantic import field_validator, model_validator

Severity = Literal["low", "medium", "high", "critical"]
FindingSeverity = Literal["info", "warning", "error", "critical"]
REVIEW_RESULT_SCHEMA_VERSION = "review-result.v1"
BATCH_REVIEW_RESULT_SCHEMA_VERSION = "batch-review-result.v1"
PROFILE_VALIDATION_RESULT_SCHEMA_VERSION = "profile-validation-result.v1"
PROFILE_TEMPLATE_LIST_SCHEMA_VERSION = "profile-template-list.v1"
REVIEW_SUMMARY_SEVERITIES: tuple[str, ...] = ("info", "warning", "error", "critical")
REGEX_RULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _default_severity_counts() -> dict[str, int]:
    return {severity: 0 for severity in REVIEW_SUMMARY_SEVERITIES}


class SourceSpan(BaseModel):
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    start_offset: int
    end_offset: int
    matched_text: str
    context: str | None = None


class ReviewIssue(BaseModel):
    id: str
    severity: Severity
    category: str
    title: str
    description: str
    suggestion: str
    original_text: str | None = None
    start_line: int | None = None
    end_line: int | None = None


class ReviewFinding(BaseModel):
    rule_id: str
    severity: FindingSeverity
    message: str
    matched_term: str
    suggestion: str | None = None
    matched_text: str | None = None
    location: SourceSpan | None = None


class RegexRuleConfig(BaseModel):
    id: str
    pattern: str
    severity: FindingSeverity
    message: str
    suggestion: str | None = None
    case_sensitive: bool = False

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        normalized = value.strip()
        if not REGEX_RULE_ID_PATTERN.fullmatch(normalized):
            raise ValueError(
                "regex rule id must match ^[a-z][a-z0-9_]*$"
            )
        return normalized

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, value: str) -> str:
        if value == "":
            raise ValueError("regex rule pattern must not be empty")
        try:
            re.compile(value)
        except re.error as exc:
            raise ValueError(f"invalid regex pattern: {exc}") from exc
        return value

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        normalized = value.strip()
        if normalized == "":
            raise ValueError("regex rule message must not be empty")
        return normalized

    @field_validator("suggestion")
    @classmethod
    def normalize_suggestion(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ReviewSummary(BaseModel):
    finding_count: int = Field(ge=0)
    severity_counts: dict[str, int] = Field(default_factory=_default_severity_counts)

    @classmethod
    def from_findings(cls, findings: list[ReviewFinding]) -> "ReviewSummary":
        severity_counts = _default_severity_counts()
        for finding in findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
        return cls(
            finding_count=len(findings),
            severity_counts=severity_counts,
        )


class ReviewDocumentMetadata(BaseModel):
    path: str


class ReviewProfileMetadata(BaseModel):
    name: str
    path: str | None = None


class ProfileValidationIssue(BaseModel):
    path: str
    code: str
    message: str
    suggestion: str | None = None


class ProfileValidationRuleSummary(BaseModel):
    id: str
    enabled: bool
    severity: FindingSeverity | None = None


class ProfileValidationProfileSummary(BaseModel):
    name: str
    target_platform: str
    enabled_rule_count: int = Field(ge=0)
    disabled_rule_count: int = Field(ge=0)
    rules: list[ProfileValidationRuleSummary] = Field(default_factory=list)


class ProfileValidationResult(BaseModel):
    schema_version: str = PROFILE_VALIDATION_RESULT_SCHEMA_VERSION
    valid: bool
    path: str
    profile: ProfileValidationProfileSummary | None = None
    errors: list[ProfileValidationIssue] = Field(default_factory=list)


class ProfileTemplateSummary(BaseModel):
    name: str
    description: str


class ProfileTemplateListResult(BaseModel):
    schema_version: str = PROFILE_TEMPLATE_LIST_SCHEMA_VERSION
    templates: list[ProfileTemplateSummary] = Field(default_factory=list)


class ReviewResult(BaseModel):
    schema_version: str = REVIEW_RESULT_SCHEMA_VERSION
    summary: ReviewSummary
    findings: list[ReviewFinding] = Field(default_factory=list)
    document: ReviewDocumentMetadata | None = None
    profile: ReviewProfileMetadata | None = None

    @classmethod
    def from_findings(
        cls,
        findings: list[ReviewFinding],
        *,
        document: ReviewDocumentMetadata | None = None,
        profile: ReviewProfileMetadata | None = None,
    ) -> "ReviewResult":
        return cls(
            summary=ReviewSummary.from_findings(findings),
            findings=list(findings),
            document=document,
            profile=profile,
        )


class BatchReviewSummary(BaseModel):
    file_count: int = Field(ge=0)
    reviewed_count: int = Field(ge=0)
    finding_count: int = Field(ge=0)
    files_with_findings: int = Field(ge=0)
    severity_counts: dict[str, int] = Field(default_factory=_default_severity_counts)

    @classmethod
    def from_results(
        cls,
        *,
        file_count: int,
        results: list[ReviewResult],
    ) -> "BatchReviewSummary":
        severity_counts = _default_severity_counts()
        finding_count = 0
        files_with_findings = 0

        for result in results:
            finding_count += result.summary.finding_count
            if result.summary.finding_count > 0:
                files_with_findings += 1
            for severity, count in result.summary.severity_counts.items():
                severity_counts[severity] = severity_counts.get(severity, 0) + count

        return cls(
            file_count=file_count,
            reviewed_count=len(results),
            finding_count=finding_count,
            files_with_findings=files_with_findings,
            severity_counts=severity_counts,
        )


class BatchReviewResult(BaseModel):
    schema_version: str = BATCH_REVIEW_RESULT_SCHEMA_VERSION
    summary: BatchReviewSummary
    results: list[ReviewResult] = Field(default_factory=list)

    @classmethod
    def from_results(
        cls,
        results: list[ReviewResult],
        *,
        file_count: int,
    ) -> "BatchReviewResult":
        return cls(
            summary=BatchReviewSummary.from_results(
                file_count=file_count,
                results=results,
            ),
            results=list(results),
        )


class ReviewProfile(BaseModel):
    name: str
    target_platform: str
    tone: str = "clear and professional"
    max_title_length: int = 32
    max_paragraph_length: int = 220
    forbidden_terms: list[str] = Field(default_factory=list)
    forbidden_terms_allow_terms: list[str] = Field(default_factory=list)
    absolute_claims_terms: list[str] = Field(default_factory=list)
    absolute_claims_allow_terms: list[str] = Field(default_factory=list)
    absolute_claims_severity: FindingSeverity = "warning"
    regex_rules: list[RegexRuleConfig] = Field(default_factory=list)
    enabled_rules: list[str] | None = None

    @model_validator(mode="after")
    def validate_regex_rule_ids(self) -> "ReviewProfile":
        seen_rule_ids: set[str] = set()
        duplicate_rule_ids: list[str] = []

        for regex_rule in self.regex_rules:
            if regex_rule.id in seen_rule_ids:
                duplicate_rule_ids.append(regex_rule.id)
                continue
            seen_rule_ids.add(regex_rule.id)

        if duplicate_rule_ids:
            duplicates = ", ".join(sorted(set(duplicate_rule_ids)))
            raise ValueError(f"duplicate regex rule id: {duplicates}")

        return self


__all__ = [
    "FindingSeverity",
    "BATCH_REVIEW_RESULT_SCHEMA_VERSION",
    "PROFILE_TEMPLATE_LIST_SCHEMA_VERSION",
    "PROFILE_VALIDATION_RESULT_SCHEMA_VERSION",
    "REVIEW_RESULT_SCHEMA_VERSION",
    "REVIEW_SUMMARY_SEVERITIES",
    "ReviewDocumentMetadata",
    "BatchReviewResult",
    "BatchReviewSummary",
    "ReviewFinding",
    "ReviewIssue",
    "ProfileValidationIssue",
    "ProfileValidationProfileSummary",
    "ProfileValidationResult",
    "ProfileValidationRuleSummary",
    "ProfileTemplateListResult",
    "ProfileTemplateSummary",
    "RegexRuleConfig",
    "REGEX_RULE_ID_PATTERN",
    "ReviewProfile",
    "ReviewProfileMetadata",
    "ReviewResult",
    "ReviewSummary",
    "SourceSpan",
    "Severity",
]
