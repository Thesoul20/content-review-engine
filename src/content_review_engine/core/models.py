from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high", "critical"]
FindingSeverity = Literal["info", "warning", "error", "critical"]
REVIEW_RESULT_SCHEMA_VERSION = "review-result.v1"
BATCH_REVIEW_RESULT_SCHEMA_VERSION = "batch-review-result.v1"
REVIEW_SUMMARY_SEVERITIES: tuple[str, ...] = ("info", "warning", "error", "critical")


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
    enabled_rules: list[str] | None = None


__all__ = [
    "FindingSeverity",
    "BATCH_REVIEW_RESULT_SCHEMA_VERSION",
    "REVIEW_RESULT_SCHEMA_VERSION",
    "REVIEW_SUMMARY_SEVERITIES",
    "ReviewDocumentMetadata",
    "BatchReviewResult",
    "BatchReviewSummary",
    "ReviewFinding",
    "ReviewIssue",
    "ReviewProfile",
    "ReviewProfileMetadata",
    "ReviewResult",
    "ReviewSummary",
    "SourceSpan",
    "Severity",
]
