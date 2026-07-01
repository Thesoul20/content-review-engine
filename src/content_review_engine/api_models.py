from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from content_review_engine.core.models import BatchReviewResult, ReviewResult
from content_review_engine.llm import (
    BatchCombinedReviewResult,
    LLMQualityGateResult,
    LLMProviderConfig,
    LLMSidecarResult,
    LLMReviewResult,
    SingleFileCombinedLLMError,
    SingleFileCombinedReviewResult,
)

ReviewOutputFormat = Literal["text", "json", "markdown"]
CombinedOutputFormat = Literal["json", "markdown"]


def _default_gate_counts() -> dict[str, int]:
    return {
        "info": 0,
        "warning": 0,
        "error": 0,
        "critical": 0,
    }


class DeterministicQualityGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    fail_on: str | None = None
    failed: bool = False
    matched_finding_count: int = Field(default=0, ge=0)
    matched_severity_counts: dict[str, int] = Field(default_factory=_default_gate_counts)
    matched_file_count: int = Field(default=0, ge=0)
    matched_files: tuple[str, ...] = Field(default_factory=tuple)


class ReviewArtifactPaths(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_path: str | None = None
    llm_output_path: str | None = None
    combined_output_path: str | None = None
    llm_report_path: str | None = None
    report_index_path: str | None = None


class ReviewFileOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown_path: Path
    profile_path: Path
    output_format: ReviewOutputFormat = "text"
    output_path: Path | None = None
    fail_on: str | None = None
    enable_llm: bool = False
    llm_fail_on: str | None = None
    llm_output_path: Path | None = None
    combined_output_path: Path | None = None
    combined_output_format: CombinedOutputFormat = "markdown"
    include_combined_result: bool = False
    llm_report_path: Path | None = None
    report_index_path: Path | None = None
    llm_provider_config: LLMProviderConfig | None = None
    llm_config_path: Path | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key_env: str | None = None
    llm_base_url: str | None = None
    llm_timeout_seconds: float | None = None
    llm_retry_attempts: int | None = None
    llm_retry_backoff_seconds: float | None = None
    llm_min_request_interval_seconds: float | None = None
    raise_on_llm_error: bool = False

    @model_validator(mode="after")
    def validate_llm_config_sources(self) -> "ReviewFileOptions":
        if self.llm_provider_config is not None and self.llm_config_path is not None:
            raise ValueError(
                "llm_provider_config and llm_config_path cannot be used together."
            )
        return self


class ReviewBatchOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_dir: Path
    profile_path: Path
    pattern: str = "*.md"
    recursive: bool = False
    output_format: ReviewOutputFormat = "text"
    output_path: Path | None = None
    fail_on: str | None = None
    enable_llm: bool = False
    llm_fail_on: str | None = None
    llm_output_path: Path | None = None
    combined_output_path: Path | None = None
    combined_output_format: CombinedOutputFormat = "markdown"
    include_combined_result: bool = False
    llm_report_path: Path | None = None
    report_index_path: Path | None = None
    llm_provider_config: LLMProviderConfig | None = None
    llm_config_path: Path | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key_env: str | None = None
    llm_base_url: str | None = None
    llm_timeout_seconds: float | None = None
    llm_retry_attempts: int | None = None
    llm_retry_backoff_seconds: float | None = None
    llm_min_request_interval_seconds: float | None = None
    raise_on_llm_error: bool = False

    @model_validator(mode="after")
    def validate_llm_config_sources(self) -> "ReviewBatchOptions":
        if self.llm_provider_config is not None and self.llm_config_path is not None:
            raise ValueError(
                "llm_provider_config and llm_config_path cannot be used together."
            )
        return self


class ReviewFileWorkflowResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    options: ReviewFileOptions
    review_result: ReviewResult
    output_text: str
    deterministic_quality_gate: DeterministicQualityGateResult
    llm_result: LLMReviewResult | None = None
    llm_status: Literal["not_run", "skipped", "succeeded", "failed"] = "not_run"
    llm_error: SingleFileCombinedLLMError | None = None
    llm_quality_gate: LLMQualityGateResult = Field(default_factory=LLMQualityGateResult)
    combined_result: SingleFileCombinedReviewResult | None = None
    artifacts: ReviewArtifactPaths = Field(default_factory=ReviewArtifactPaths)


class ReviewBatchWorkflowResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    options: ReviewBatchOptions
    batch_result: BatchReviewResult
    output_text: str
    deterministic_quality_gate: DeterministicQualityGateResult
    llm_sidecar_result: LLMSidecarResult | None = None
    llm_quality_gate: LLMQualityGateResult = Field(default_factory=LLMQualityGateResult)
    combined_result: BatchCombinedReviewResult | None = None
    artifacts: ReviewArtifactPaths = Field(default_factory=ReviewArtifactPaths)


__all__ = [
    "CombinedOutputFormat",
    "DeterministicQualityGateResult",
    "ReviewArtifactPaths",
    "ReviewBatchOptions",
    "ReviewBatchWorkflowResult",
    "ReviewFileOptions",
    "ReviewFileWorkflowResult",
    "ReviewOutputFormat",
]
