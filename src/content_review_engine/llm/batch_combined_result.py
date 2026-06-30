from __future__ import annotations

from dataclasses import asdict
import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from content_review_engine.core.models import BatchReviewResult, ReviewResult
from content_review_engine.core.serialization import batch_review_result_to_dict
from content_review_engine.llm.finding_adapter import (
    LLMCoreFindingCandidate,
    adapt_llm_review_result_to_core_finding_candidates,
)
from content_review_engine.llm.models import LLMSidecarFile, LLMSidecarResult, LLMReviewResult
from content_review_engine.llm.policy import LLM_FINDING_ADVISORY
from content_review_engine.llm.quality_gate import LLMQualityGateResult
from content_review_engine.llm.serialization import (
    llm_review_result_to_dict,
    llm_sidecar_result_to_dict,
)
from content_review_engine.llm.secrets import REDACTED_SECRET_TEXT

BATCH_COMBINED_REVIEW_RESULT_SCHEMA_VERSION = "batch-combined-review-result.v1"
LLM_BATCH_STATUS_VALUES: tuple[str, ...] = (
    "not_run",
    "skipped",
    "succeeded",
    "failed",
)
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"AIza[0-9A-Za-z\\-_]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token)\b\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)environment variable\s+['\"]?[A-Z][A-Z0-9_]{2,}['\"]?"),
)
_TRACEBACK_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^Traceback \(most recent call last\):$"),
    re.compile(r'^  File "[^"]+", line \d+, in .+$'),
)


class BatchCombinedLLMError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    message: str
    provider: str | None = None
    retryable: bool | None = None


class BatchCombinedFileResult(BaseModel):
    file: str
    llm_status: Literal["not_run", "skipped", "succeeded", "failed"] = "not_run"
    llm_error: BatchCombinedLLMError | None = None
    llm_result: LLMReviewResult | None = None
    llm_finding_candidates: tuple[LLMCoreFindingCandidate, ...] = Field(
        default_factory=tuple
    )
    advisory: bool = LLM_FINDING_ADVISORY

    @field_validator("file")
    @classmethod
    def validate_file(cls, value: str) -> str:
        normalized = value.strip()
        if normalized == "":
            raise ValueError("file must not be empty")
        return normalized

    @model_validator(mode="after")
    def validate_consistency(self) -> "BatchCombinedFileResult":
        if self.advisory is not True:
            raise ValueError("advisory must be True")

        if self.llm_status == "failed":
            if self.llm_error is None:
                raise ValueError("failed status requires llm_error")
            if self.llm_finding_candidates:
                raise ValueError("failed status must not include llm_finding_candidates")
            return self

        if self.llm_error is not None:
            raise ValueError(f"{self.llm_status} status must not include llm_error")
        return self


class BatchCombinedLLMSummary(BaseModel):
    total_files: int = Field(ge=0)
    succeeded_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)
    not_run_count: int = Field(ge=0)
    advisory_finding_count: int = Field(ge=0)
    files_with_advisory_findings: int = Field(ge=0)
    error_count: int = Field(ge=0)


class BatchCombinedReviewResult(BaseModel):
    schema_version: str = BATCH_COMBINED_REVIEW_RESULT_SCHEMA_VERSION
    batch_review_result: BatchReviewResult
    batch_llm_result: LLMSidecarResult | None = None
    files: tuple[BatchCombinedFileResult, ...] = Field(default_factory=tuple)
    llm_summary: BatchCombinedLLMSummary
    advisory: bool = LLM_FINDING_ADVISORY
    llm_quality_gate: LLMQualityGateResult = Field(default_factory=LLMQualityGateResult)

    @model_validator(mode="after")
    def validate_consistency(self) -> "BatchCombinedReviewResult":
        if self.advisory is not True:
            raise ValueError("advisory must be True")
        if self.llm_summary.total_files != len(self.files):
            raise ValueError("llm_summary.total_files must equal files length")
        return self


def _sanitize_error_text(value: str | None) -> str | None:
    if value is None:
        return None

    lines: list[str] = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if line == "":
            continue
        if any(pattern.match(raw_line) for pattern in _TRACEBACK_LINE_PATTERNS):
            continue
        lines.append(line)

    sanitized = " ".join(lines) if lines else value.strip()
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub(REDACTED_SECRET_TEXT, sanitized)
    return sanitized or None


def _build_combined_llm_error_from_sidecar_file(
    sidecar_file: LLMSidecarFile,
) -> BatchCombinedLLMError | None:
    if sidecar_file.error is None:
        return None

    return BatchCombinedLLMError(
        type=sidecar_file.error.error_type,
        message=_sanitize_error_text(sidecar_file.error.message) or "LLM review failed.",
    )


def _get_review_result_path(result: ReviewResult, *, index: int) -> str:
    if result.document is not None and result.document.path.strip() != "":
        return result.document.path
    return f"<unknown-file-{index}>"


def _build_batch_combined_file_result(
    *,
    file_path: str,
    sidecar_file: LLMSidecarFile | None,
    default_llm_status: Literal["not_run", "skipped", "succeeded", "failed"],
) -> BatchCombinedFileResult:
    if sidecar_file is None:
        return BatchCombinedFileResult(file=file_path, llm_status=default_llm_status)

    if sidecar_file.status == "success":
        llm_result = sidecar_file.review
        finding_candidates: tuple[LLMCoreFindingCandidate, ...] = tuple()
        if llm_result is not None:
            finding_candidates = tuple(
                adapt_llm_review_result_to_core_finding_candidates(llm_result)
            )
        return BatchCombinedFileResult(
            file=file_path,
            llm_status="succeeded",
            llm_result=llm_result,
            llm_finding_candidates=finding_candidates,
            advisory=LLM_FINDING_ADVISORY,
        )

    if sidecar_file.status == "failed":
        return BatchCombinedFileResult(
            file=file_path,
            llm_status="failed",
            llm_error=_build_combined_llm_error_from_sidecar_file(sidecar_file),
            advisory=LLM_FINDING_ADVISORY,
        )

    return BatchCombinedFileResult(
        file=file_path,
        llm_status="skipped",
        advisory=LLM_FINDING_ADVISORY,
    )


def _build_batch_combined_llm_summary(
    files: tuple[BatchCombinedFileResult, ...],
) -> BatchCombinedLLMSummary:
    return BatchCombinedLLMSummary(
        total_files=len(files),
        succeeded_count=sum(1 for item in files if item.llm_status == "succeeded"),
        failed_count=sum(1 for item in files if item.llm_status == "failed"),
        skipped_count=sum(1 for item in files if item.llm_status == "skipped"),
        not_run_count=sum(1 for item in files if item.llm_status == "not_run"),
        advisory_finding_count=sum(len(item.llm_finding_candidates) for item in files),
        files_with_advisory_findings=sum(
            1 for item in files if len(item.llm_finding_candidates) > 0
        ),
        error_count=sum(1 for item in files if item.llm_error is not None),
    )


def build_batch_combined_review_result(
    *,
    batch_review_result: BatchReviewResult,
    batch_llm_result: LLMSidecarResult | None = None,
    default_llm_status: Literal["not_run", "skipped", "succeeded", "failed"] = "not_run",
    llm_quality_gate: LLMQualityGateResult | dict[str, Any] | None = None,
) -> BatchCombinedReviewResult:
    if not isinstance(batch_review_result, BatchReviewResult):
        raise TypeError("batch_review_result must be a BatchReviewResult")
    if batch_llm_result is not None and not isinstance(batch_llm_result, LLMSidecarResult):
        raise TypeError("batch_llm_result must be an LLMSidecarResult or None")
    if batch_llm_result is None and default_llm_status not in {"not_run", "skipped"}:
        raise ValueError(
            "default_llm_status must be 'not_run' or 'skipped' when batch_llm_result is None"
        )

    normalized_quality_gate: LLMQualityGateResult
    if llm_quality_gate is None:
        normalized_quality_gate = LLMQualityGateResult()
    elif isinstance(llm_quality_gate, LLMQualityGateResult):
        normalized_quality_gate = llm_quality_gate
    else:
        normalized_quality_gate = LLMQualityGateResult.model_validate(llm_quality_gate)

    sidecar_files_by_path: dict[str, LLMSidecarFile] = {}
    if batch_llm_result is not None:
        for sidecar_file in batch_llm_result.files:
            sidecar_files_by_path.setdefault(sidecar_file.path, sidecar_file)

    files = tuple(
        _build_batch_combined_file_result(
            file_path=_get_review_result_path(review_result, index=index),
            sidecar_file=sidecar_files_by_path.get(
                _get_review_result_path(review_result, index=index)
            ),
            default_llm_status=default_llm_status,
        )
        for index, review_result in enumerate(batch_review_result.results)
    )

    return BatchCombinedReviewResult(
        batch_review_result=batch_review_result,
        batch_llm_result=batch_llm_result,
        files=files,
        llm_summary=_build_batch_combined_llm_summary(files),
        advisory=LLM_FINDING_ADVISORY,
        llm_quality_gate=normalized_quality_gate,
    )


def _batch_combined_file_result_to_dict(
    result: BatchCombinedFileResult,
) -> dict[str, Any]:
    return {
        "file": result.file,
        "status": result.llm_status,
        "advisory": result.advisory,
        "error": (
            None
            if result.llm_error is None
            else result.llm_error.model_dump(mode="json", exclude_none=True)
        ),
        "result": (
            None
            if result.llm_result is None
            else llm_review_result_to_dict(result.llm_result)
        ),
        "finding_candidates": [
            asdict(candidate) for candidate in result.llm_finding_candidates
        ],
    }


def batch_combined_review_result_to_dict(
    result: BatchCombinedReviewResult,
) -> dict[str, Any]:
    if not isinstance(result, BatchCombinedReviewResult):
        raise TypeError("result must be a BatchCombinedReviewResult")

    return {
        "schema_version": result.schema_version,
        "batch_review_result": batch_review_result_to_dict(result.batch_review_result),
        "llm": {
            "advisory": result.advisory,
            "summary": result.llm_summary.model_dump(mode="json", exclude_none=True),
            "quality_gate": result.llm_quality_gate.model_dump(
                mode="json", exclude_none=True
            ),
            "result": (
                None
                if result.batch_llm_result is None
                else llm_sidecar_result_to_dict(result.batch_llm_result)
            ),
            "files": [_batch_combined_file_result_to_dict(item) for item in result.files],
        },
    }


def batch_combined_review_result_to_json(result: BatchCombinedReviewResult) -> str:
    return json.dumps(
        batch_combined_review_result_to_dict(result),
        ensure_ascii=False,
        indent=2,
    )


__all__ = [
    "BATCH_COMBINED_REVIEW_RESULT_SCHEMA_VERSION",
    "LLM_BATCH_STATUS_VALUES",
    "BatchCombinedFileResult",
    "BatchCombinedLLMError",
    "BatchCombinedLLMSummary",
    "BatchCombinedReviewResult",
    "batch_combined_review_result_to_dict",
    "batch_combined_review_result_to_json",
    "build_batch_combined_review_result",
]
