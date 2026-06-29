from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence, cast

from content_review_engine.llm.models import (
    LLMSidecarResult,
    LLMReviewRequest,
    LLMReviewResult,
)
from content_review_engine.llm.result_conversion import (
    convert_validated_semantic_output_to_llm_review_result,
)
from content_review_engine.llm.provider import LLMReviewer
from content_review_engine.llm.sidecar import (
    build_llm_sidecar_file_failed,
    build_llm_sidecar_file_success,
    build_llm_sidecar_result,
)


class LLMReviewRunner:
    def __init__(self, reviewer: LLMReviewer) -> None:
        self._reviewer = reviewer

    def run(self, request: LLMReviewRequest) -> LLMReviewResult:
        return self._reviewer.review(request)


class LLMSemanticReviewer(Protocol):
    model: str | None

    def run_semantic_review(self, request: LLMReviewRequest) -> Any: ...


@dataclass(frozen=True)
class BatchLLMReviewItem:
    path: str
    request: LLMReviewRequest | None = None
    error: Exception | None = None


def build_llm_review_request(
    *,
    markdown_text: str,
    markdown_path: str,
    profile_name: str,
) -> LLMReviewRequest:
    return LLMReviewRequest(
        content=markdown_text,
        profile_name=profile_name,
        content_path=markdown_path,
        review_goal="semantic_review",
    )


def run_single_file_llm_review(
    request: LLMReviewRequest,
    *,
    reviewer: LLMReviewer,
    provider: str | None = None,
    model: str | None = None,
) -> LLMReviewResult:
    semantic_reviewer = reviewer
    if hasattr(semantic_reviewer, "run_semantic_review"):
        semantic_output = cast(
            LLMSemanticReviewer,
            semantic_reviewer,
        ).run_semantic_review(request)
        resolved_model = model
        if resolved_model is None:
            resolved_model = getattr(semantic_reviewer, "model", None)
        return convert_validated_semantic_output_to_llm_review_result(
            semantic_output,
            request,
            provider=provider,
            model=resolved_model,
        )

    return reviewer.review(request)


def run_batch_llm_review(
    items: Sequence[BatchLLMReviewItem],
    *,
    reviewer: LLMReviewer,
    llm_provider: str,
    llm_provider_source: str,
    provider: str | None = None,
    model: str | None = None,
) -> LLMSidecarResult:
    sidecar_files = []
    for item in items:
        if item.error is not None:
            sidecar_files.append(build_llm_sidecar_file_failed(path=item.path, exc=item.error))
            continue
        if item.request is None:
            sidecar_files.append(
                build_llm_sidecar_file_failed(
                    path=item.path,
                    exc=ValueError("Missing LLM review request."),
                )
            )
            continue
        try:
            review_result = run_single_file_llm_review(
                item.request,
                reviewer=reviewer,
                provider=provider,
                model=model,
            )
        except Exception as exc:
            sidecar_files.append(build_llm_sidecar_file_failed(path=item.path, exc=exc))
            continue

        sidecar_files.append(
            build_llm_sidecar_file_success(
                path=item.path,
                review=review_result,
            )
        )

    return build_llm_sidecar_result(
        sidecar_files,
        llm_provider=llm_provider,
        llm_provider_source=llm_provider_source,
    )


__all__ = [
    "BatchLLMReviewItem",
    "LLMReviewRunner",
    "build_llm_review_request",
    "run_batch_llm_review",
    "run_single_file_llm_review",
]
