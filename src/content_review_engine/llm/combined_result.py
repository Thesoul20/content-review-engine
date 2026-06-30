from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from content_review_engine.core.models import ReviewResult
from content_review_engine.core.serialization import review_result_to_dict
from content_review_engine.llm.finding_adapter import (
    LLMCoreFindingCandidate,
    adapt_llm_review_result_to_core_finding_candidates,
)
from content_review_engine.llm.models import LLMReviewResult
from content_review_engine.llm.policy import LLM_FINDING_ADVISORY
from content_review_engine.llm.quality_gate import LLMQualityGateResult
from content_review_engine.llm.serialization import llm_review_result_to_dict

SINGLE_FILE_COMBINED_REVIEW_RESULT_SCHEMA_VERSION = (
    "single-file-combined-review-result.v1"
)
LLM_SINGLE_FILE_STATUS_VALUES: tuple[str, ...] = (
    "not_run",
    "skipped",
    "succeeded",
    "failed",
)


class SingleFileCombinedLLMError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    message: str
    provider: str | None = None
    retryable: bool | None = None


class SingleFileCombinedReviewResult(BaseModel):
    schema_version: str = SINGLE_FILE_COMBINED_REVIEW_RESULT_SCHEMA_VERSION
    review_result: ReviewResult
    llm_result: LLMReviewResult | None = None
    llm_finding_candidates: tuple[LLMCoreFindingCandidate, ...] = Field(
        default_factory=tuple
    )
    llm_status: Literal["not_run", "skipped", "succeeded", "failed"] = "not_run"
    llm_error: SingleFileCombinedLLMError | None = None
    advisory: bool = LLM_FINDING_ADVISORY
    llm_quality_gate: LLMQualityGateResult = Field(default_factory=LLMQualityGateResult)

    @model_validator(mode="after")
    def validate_consistency(self) -> "SingleFileCombinedReviewResult":
        if self.advisory is not True:
            raise ValueError("advisory must be True")

        if self.llm_status == "succeeded":
            if self.llm_result is None:
                raise ValueError("succeeded status requires llm_result")
            if self.llm_error is not None:
                raise ValueError("succeeded status must not include llm_error")
            return self

        if self.llm_status == "failed":
            if self.llm_error is None:
                raise ValueError("failed status requires llm_error")
            if self.llm_finding_candidates:
                raise ValueError("failed status must not include llm_finding_candidates")
            return self

        if self.llm_error is not None:
            raise ValueError(f"{self.llm_status} status must not include llm_error")
        if self.llm_result is not None:
            raise ValueError(f"{self.llm_status} status must not include llm_result")
        if self.llm_finding_candidates:
            raise ValueError(
                f"{self.llm_status} status must not include llm_finding_candidates"
            )
        return self


def build_single_file_combined_review_result(
    *,
    review_result: ReviewResult,
    llm_result: LLMReviewResult | None = None,
    llm_status: Literal["not_run", "skipped", "succeeded", "failed"] | None = None,
    llm_error: dict[str, Any] | SingleFileCombinedLLMError | None = None,
    llm_quality_gate: LLMQualityGateResult | dict[str, Any] | None = None,
) -> SingleFileCombinedReviewResult:
    if not isinstance(review_result, ReviewResult):
        raise TypeError("review_result must be a ReviewResult")
    if llm_result is not None and not isinstance(llm_result, LLMReviewResult):
        raise TypeError("llm_result must be an LLMReviewResult or None")

    normalized_error: SingleFileCombinedLLMError | None
    if llm_error is None:
        normalized_error = None
    elif isinstance(llm_error, SingleFileCombinedLLMError):
        normalized_error = llm_error
    else:
        normalized_error = SingleFileCombinedLLMError.model_validate(llm_error)

    normalized_quality_gate: LLMQualityGateResult
    if llm_quality_gate is None:
        normalized_quality_gate = LLMQualityGateResult()
    elif isinstance(llm_quality_gate, LLMQualityGateResult):
        normalized_quality_gate = llm_quality_gate
    else:
        normalized_quality_gate = LLMQualityGateResult.model_validate(llm_quality_gate)

    normalized_status = llm_status
    if normalized_status is None:
        if normalized_error is not None:
            normalized_status = "failed"
        elif llm_result is not None:
            normalized_status = "succeeded"
        else:
            normalized_status = "not_run"

    finding_candidates: tuple[LLMCoreFindingCandidate, ...] = tuple()
    if normalized_status == "succeeded" and llm_result is not None:
        finding_candidates = tuple(
            adapt_llm_review_result_to_core_finding_candidates(llm_result)
        )

    return SingleFileCombinedReviewResult(
        review_result=review_result,
        llm_result=llm_result,
        llm_finding_candidates=finding_candidates,
        llm_status=normalized_status,
        llm_error=normalized_error,
        advisory=LLM_FINDING_ADVISORY,
        llm_quality_gate=normalized_quality_gate,
    )


def single_file_combined_review_result_to_dict(
    result: SingleFileCombinedReviewResult,
) -> dict[str, Any]:
    if not isinstance(result, SingleFileCombinedReviewResult):
        raise TypeError("result must be a SingleFileCombinedReviewResult")

    return {
        "schema_version": result.schema_version,
        "review_result": review_result_to_dict(result.review_result),
        "llm": {
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
            "quality_gate": result.llm_quality_gate.model_dump(
                mode="json", exclude_none=True
            ),
        },
    }


def single_file_combined_review_result_to_json(
    result: SingleFileCombinedReviewResult,
) -> str:
    return json.dumps(
        single_file_combined_review_result_to_dict(result),
        ensure_ascii=False,
        indent=2,
    )


__all__ = [
    "LLM_SINGLE_FILE_STATUS_VALUES",
    "SINGLE_FILE_COMBINED_REVIEW_RESULT_SCHEMA_VERSION",
    "SingleFileCombinedLLMError",
    "SingleFileCombinedReviewResult",
    "build_single_file_combined_review_result",
    "single_file_combined_review_result_to_dict",
    "single_file_combined_review_result_to_json",
]
