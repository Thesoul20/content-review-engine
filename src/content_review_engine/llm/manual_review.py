from __future__ import annotations

from dataclasses import dataclass

from content_review_engine.llm.models import LLMSidecarResult, LLMReviewFinding, LLMReviewResult
from content_review_engine.llm.policy import normalize_llm_finding_rule_id, normalize_llm_finding_severity

LLM_MANUAL_REVIEW_DEFAULT_STATUS = "needs_review"
LLM_MANUAL_REVIEW_DEFAULT_DECISION = "pending"
LLM_MANUAL_REVIEW_DEFAULT_QUALITY_GATE = "no"
LLM_MANUAL_REVIEW_EXECUTION_STATUS = "needs_rerun"
LLM_MANUAL_REVIEW_EXECUTION_ACTION = "rerun_llm_review"
LLM_MANUAL_REVIEW_MISSING_LOCATION = "not provided"
LLM_MANUAL_REVIEW_MISSING_MESSAGE = "not provided"


@dataclass(frozen=True)
class LLMManualReviewItem:
    checklist_id: str
    priority: str
    status: str
    decision: str
    quality_gate: str
    rule_id: str
    location: str
    message: str
    notes: str = ""


@dataclass(frozen=True)
class LLMBatchManualReviewItem:
    checklist_id: str
    file_path: str
    priority: str
    status: str
    decision: str
    quality_gate: str
    rule_id: str
    location: str
    message: str
    notes: str = ""


@dataclass(frozen=True)
class LLMExecutionReviewItem:
    checklist_id: str
    file_path: str
    status: str
    suggested_action: str
    error_type: str
    error_message: str
    notes: str = ""


def _format_checklist_id(prefix: str, index: int) -> str:
    return f"{prefix}{index:03d}"


def _normalize_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def _format_location(finding: LLMReviewFinding) -> str:
    if finding.line is None:
        return LLM_MANUAL_REVIEW_MISSING_LOCATION

    location = f"line {finding.line}"
    if finding.column is not None:
        location += f", column {finding.column}"
    if finding.end_line is not None:
        location += f" to line {finding.end_line}"
        if finding.end_column is not None:
            location += f", column {finding.end_column}"
    elif finding.end_column is not None:
        location += f" to column {finding.end_column}"
    return location


def _format_message(finding: LLMReviewFinding) -> str:
    message = _normalize_text(getattr(finding, "message", None))
    if message == "":
        return LLM_MANUAL_REVIEW_MISSING_MESSAGE
    return message


def _priority_for_finding(finding: LLMReviewFinding) -> str:
    severity = normalize_llm_finding_severity(getattr(finding, "severity", None))
    if severity in {"critical", "error"}:
        return "high"
    if severity == "warning":
        return "medium"
    if severity == "info":
        return "low"
    return "review"


def build_llm_manual_review_items(result: LLMReviewResult) -> tuple[LLMManualReviewItem, ...]:
    items: list[LLMManualReviewItem] = []
    for index, finding in enumerate(result.findings, start=1):
        items.append(
            LLMManualReviewItem(
                checklist_id=_format_checklist_id("LLM-", index),
                priority=_priority_for_finding(finding),
                status=LLM_MANUAL_REVIEW_DEFAULT_STATUS,
                decision=LLM_MANUAL_REVIEW_DEFAULT_DECISION,
                quality_gate=LLM_MANUAL_REVIEW_DEFAULT_QUALITY_GATE,
                rule_id=normalize_llm_finding_rule_id(getattr(finding, "rule_id", None)),
                location=_format_location(finding),
                message=_format_message(finding),
            )
        )
    return tuple(items)


def build_batch_llm_manual_review_items(result: LLMSidecarResult) -> tuple[LLMBatchManualReviewItem, ...]:
    items: list[LLMBatchManualReviewItem] = []
    checklist_index = 1
    for file in result.files:
        if file.review is None:
            continue
        for finding in file.review.findings:
            items.append(
                LLMBatchManualReviewItem(
                    checklist_id=_format_checklist_id("LLM-", checklist_index),
                    file_path=file.path,
                    priority=_priority_for_finding(finding),
                    status=LLM_MANUAL_REVIEW_DEFAULT_STATUS,
                    decision=LLM_MANUAL_REVIEW_DEFAULT_DECISION,
                    quality_gate=LLM_MANUAL_REVIEW_DEFAULT_QUALITY_GATE,
                    rule_id=normalize_llm_finding_rule_id(getattr(finding, "rule_id", None)),
                    location=_format_location(finding),
                    message=_format_message(finding),
                )
            )
            checklist_index += 1
    return tuple(items)


def build_llm_execution_review_items(result: LLMSidecarResult) -> tuple[LLMExecutionReviewItem, ...]:
    items: list[LLMExecutionReviewItem] = []
    checklist_index = 1
    for file in result.files:
        if file.error is None:
            continue
        items.append(
            LLMExecutionReviewItem(
                checklist_id=_format_checklist_id("LLM-ERR-", checklist_index),
                file_path=file.path,
                status=LLM_MANUAL_REVIEW_EXECUTION_STATUS,
                suggested_action=LLM_MANUAL_REVIEW_EXECUTION_ACTION,
                error_type=file.error.error_type,
                error_message=file.error.message,
            )
        )
        checklist_index += 1
    return tuple(items)


__all__ = [
    "LLMBatchManualReviewItem",
    "LLMExecutionReviewItem",
    "LLMManualReviewItem",
    "LLM_MANUAL_REVIEW_DEFAULT_DECISION",
    "LLM_MANUAL_REVIEW_DEFAULT_QUALITY_GATE",
    "LLM_MANUAL_REVIEW_DEFAULT_STATUS",
    "LLM_MANUAL_REVIEW_EXECUTION_ACTION",
    "LLM_MANUAL_REVIEW_EXECUTION_STATUS",
    "LLM_MANUAL_REVIEW_MISSING_LOCATION",
    "LLM_MANUAL_REVIEW_MISSING_MESSAGE",
    "build_batch_llm_manual_review_items",
    "build_llm_execution_review_items",
    "build_llm_manual_review_items",
]
