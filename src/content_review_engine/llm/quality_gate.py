from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from content_review_engine.core.models import REVIEW_SUMMARY_SEVERITIES
from content_review_engine.core.quality_gate import severity_meets_threshold
from content_review_engine.llm.models import LLMSidecarResult, LLMReviewResult


LLM_QUALITY_GATE_EVALUATION_STATUS_VALUES: tuple[str, ...] = (
    "disabled",
    "not_run",
    "evaluated",
    "execution_failed",
)


def _build_empty_severity_counts() -> dict[str, int]:
    return {severity: 0 for severity in REVIEW_SUMMARY_SEVERITIES}


class LLMQualityGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    fail_on: str | None = None
    failed: bool = False
    evaluation_status: Literal[
        "disabled", "not_run", "evaluated", "execution_failed"
    ] = "disabled"
    matched_finding_count: int = Field(default=0, ge=0)
    matched_severity_counts: dict[str, int] = Field(
        default_factory=_build_empty_severity_counts
    )
    matched_file_count: int = Field(default=0, ge=0)
    matched_files: tuple[str, ...] = Field(default_factory=tuple)


def evaluate_llm_quality_gate(
    llm_result: LLMReviewResult | None,
    threshold: str | None,
    *,
    execution_failed: bool = False,
) -> LLMQualityGateResult:
    if threshold is None:
        return LLMQualityGateResult()

    if execution_failed:
        return LLMQualityGateResult(
            enabled=True,
            fail_on=threshold,
            failed=False,
            evaluation_status="execution_failed",
        )

    if llm_result is None:
        return LLMQualityGateResult(
            enabled=True,
            fail_on=threshold,
            failed=False,
            evaluation_status="not_run",
        )

    matched_severity_counts = _build_empty_severity_counts()
    matched_finding_count = 0
    for finding in llm_result.findings:
        if severity_meets_threshold(finding.severity, threshold):
            matched_severity_counts[finding.severity] += 1
            matched_finding_count += 1

    return LLMQualityGateResult(
        enabled=True,
        fail_on=threshold,
        failed=matched_finding_count > 0,
        evaluation_status="evaluated",
        matched_finding_count=matched_finding_count,
        matched_severity_counts=matched_severity_counts,
        matched_file_count=1 if matched_finding_count > 0 else 0,
    )


def evaluate_batch_llm_quality_gate(
    batch_llm_result: LLMSidecarResult | None,
    threshold: str | None,
) -> LLMQualityGateResult:
    if threshold is None:
        return LLMQualityGateResult()

    if batch_llm_result is None:
        return LLMQualityGateResult(
            enabled=True,
            fail_on=threshold,
            failed=False,
            evaluation_status="not_run",
        )

    matched_severity_counts = _build_empty_severity_counts()
    matched_finding_count = 0
    matched_files: list[str] = []

    for item in batch_llm_result.files:
        if item.review is None:
            continue
        file_matched = False
        for finding in item.review.findings:
            if severity_meets_threshold(finding.severity, threshold):
                matched_severity_counts[finding.severity] += 1
                matched_finding_count += 1
                file_matched = True
        if file_matched:
            matched_files.append(item.path)

    evaluation_status = "evaluated"
    if batch_llm_result.summary.failed_count > 0:
        evaluation_status = "execution_failed"

    return LLMQualityGateResult(
        enabled=True,
        fail_on=threshold,
        failed=matched_finding_count > 0,
        evaluation_status=evaluation_status,
        matched_finding_count=matched_finding_count,
        matched_severity_counts=matched_severity_counts,
        matched_file_count=len(matched_files),
        matched_files=tuple(matched_files),
    )


__all__ = [
    "LLM_QUALITY_GATE_EVALUATION_STATUS_VALUES",
    "LLMQualityGateResult",
    "evaluate_batch_llm_quality_gate",
    "evaluate_llm_quality_gate",
]
