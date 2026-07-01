from __future__ import annotations

from pathlib import Path

from content_review_engine.api_models import (
    CombinedOutputFormat,
    DeterministicQualityGateResult,
    ReviewArtifactPaths,
    ReviewBatchOptions,
    ReviewBatchWorkflowResult,
    ReviewFileOptions,
    ReviewFileWorkflowResult,
    ReviewOutputFormat,
)
from content_review_engine.llm import LLMProviderConfig
from content_review_engine.workflows import execute_review_batch, execute_review_file


def review_file(
    markdown_path: str | Path,
    profile_path: str | Path,
    *,
    output_format: ReviewOutputFormat = "text",
    output_path: str | Path | None = None,
    fail_on: str | None = None,
    enable_llm: bool = False,
    llm_fail_on: str | None = None,
    llm_output_path: str | Path | None = None,
    combined_output_path: str | Path | None = None,
    combined_output_format: CombinedOutputFormat = "markdown",
    include_combined_result: bool = False,
    llm_provider_config: LLMProviderConfig | None = None,
    llm_config_path: str | Path | None = None,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_api_key_env: str | None = None,
    llm_base_url: str | None = None,
    llm_timeout_seconds: float | None = None,
    llm_retry_attempts: int | None = None,
    llm_retry_backoff_seconds: float | None = None,
    llm_min_request_interval_seconds: float | None = None,
    raise_on_llm_error: bool = False,
) -> ReviewFileWorkflowResult:
    options = ReviewFileOptions(
        markdown_path=Path(markdown_path),
        profile_path=Path(profile_path),
        output_format=output_format,
        output_path=None if output_path is None else Path(output_path),
        fail_on=fail_on,
        enable_llm=enable_llm,
        llm_fail_on=llm_fail_on,
        llm_output_path=None if llm_output_path is None else Path(llm_output_path),
        combined_output_path=(
            None if combined_output_path is None else Path(combined_output_path)
        ),
        combined_output_format=combined_output_format,
        include_combined_result=include_combined_result,
        llm_provider_config=llm_provider_config,
        llm_config_path=None if llm_config_path is None else Path(llm_config_path),
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_api_key_env=llm_api_key_env,
        llm_base_url=llm_base_url,
        llm_timeout_seconds=llm_timeout_seconds,
        llm_retry_attempts=llm_retry_attempts,
        llm_retry_backoff_seconds=llm_retry_backoff_seconds,
        llm_min_request_interval_seconds=llm_min_request_interval_seconds,
        raise_on_llm_error=raise_on_llm_error,
    )
    return execute_review_file(options)


def review_batch(
    input_dir: str | Path,
    profile_path: str | Path,
    *,
    pattern: str = "*.md",
    recursive: bool = False,
    output_format: ReviewOutputFormat = "text",
    output_path: str | Path | None = None,
    fail_on: str | None = None,
    enable_llm: bool = False,
    llm_fail_on: str | None = None,
    llm_output_path: str | Path | None = None,
    combined_output_path: str | Path | None = None,
    combined_output_format: CombinedOutputFormat = "markdown",
    include_combined_result: bool = False,
    llm_provider_config: LLMProviderConfig | None = None,
    llm_config_path: str | Path | None = None,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_api_key_env: str | None = None,
    llm_base_url: str | None = None,
    llm_timeout_seconds: float | None = None,
    llm_retry_attempts: int | None = None,
    llm_retry_backoff_seconds: float | None = None,
    llm_min_request_interval_seconds: float | None = None,
    raise_on_llm_error: bool = False,
) -> ReviewBatchWorkflowResult:
    options = ReviewBatchOptions(
        input_dir=Path(input_dir),
        profile_path=Path(profile_path),
        pattern=pattern,
        recursive=recursive,
        output_format=output_format,
        output_path=None if output_path is None else Path(output_path),
        fail_on=fail_on,
        enable_llm=enable_llm,
        llm_fail_on=llm_fail_on,
        llm_output_path=None if llm_output_path is None else Path(llm_output_path),
        combined_output_path=(
            None if combined_output_path is None else Path(combined_output_path)
        ),
        combined_output_format=combined_output_format,
        include_combined_result=include_combined_result,
        llm_provider_config=llm_provider_config,
        llm_config_path=None if llm_config_path is None else Path(llm_config_path),
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_api_key_env=llm_api_key_env,
        llm_base_url=llm_base_url,
        llm_timeout_seconds=llm_timeout_seconds,
        llm_retry_attempts=llm_retry_attempts,
        llm_retry_backoff_seconds=llm_retry_backoff_seconds,
        llm_min_request_interval_seconds=llm_min_request_interval_seconds,
        raise_on_llm_error=raise_on_llm_error,
    )
    return execute_review_batch(options)


__all__ = [
    "CombinedOutputFormat",
    "DeterministicQualityGateResult",
    "ReviewArtifactPaths",
    "ReviewBatchOptions",
    "ReviewBatchWorkflowResult",
    "ReviewFileOptions",
    "ReviewFileWorkflowResult",
    "ReviewOutputFormat",
    "review_batch",
    "review_file",
]
