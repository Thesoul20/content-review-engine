from __future__ import annotations

from content_review_engine.llm.errors import LLMReviewError
from content_review_engine.llm.models import (
    LLMSidecarError,
    LLMSidecarFile,
    LLMSidecarResult,
    LLMSidecarSummary,
    LLMReviewResult,
)


def build_llm_sidecar_error(exc: Exception) -> LLMSidecarError:
    error_type = type(exc).__name__.strip() or "LLMReviewError"
    message = str(exc).strip()
    if message == "":
        if isinstance(exc, LLMReviewError):
            message = "LLM review failed."
        else:
            message = "Unexpected LLM review failure."
    return LLMSidecarError(error_type=error_type, message=message)


def build_llm_sidecar_file_success(
    *,
    path: str,
    review: LLMReviewResult | None = None,
) -> LLMSidecarFile:
    finding_count = 0 if review is None else len(review.findings)
    return LLMSidecarFile(
        path=path,
        status="success",
        finding_count=finding_count,
        review=review,
    )


def build_llm_sidecar_file_failed(
    *,
    path: str,
    exc: Exception,
) -> LLMSidecarFile:
    return LLMSidecarFile(
        path=path,
        status="failed",
        finding_count=0,
        error=build_llm_sidecar_error(exc),
    )


def build_llm_sidecar_summary(
    files: tuple[LLMSidecarFile, ...] | list[LLMSidecarFile],
) -> LLMSidecarSummary:
    file_count = len(files)
    succeeded_count = sum(1 for item in files if item.status == "success")
    failed_count = sum(1 for item in files if item.status == "failed")
    skipped_count = sum(1 for item in files if item.status == "skipped")
    finding_count = sum(item.finding_count for item in files if item.status == "success")
    return LLMSidecarSummary(
        file_count=file_count,
        succeeded_count=succeeded_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        finding_count=finding_count,
    )


def build_llm_sidecar_result(
    files: tuple[LLMSidecarFile, ...] | list[LLMSidecarFile],
) -> LLMSidecarResult:
    sidecar_files = tuple(files)
    return LLMSidecarResult(
        summary=build_llm_sidecar_summary(sidecar_files),
        files=sidecar_files,
    )


__all__ = [
    "build_llm_sidecar_error",
    "build_llm_sidecar_file_failed",
    "build_llm_sidecar_file_success",
    "build_llm_sidecar_result",
    "build_llm_sidecar_summary",
]
