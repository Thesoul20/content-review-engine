from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from content_review_engine.api_models import (
    DeterministicQualityGateResult,
    ReviewArtifactPaths,
    ReviewBatchOptions,
    ReviewBatchWorkflowResult,
    ReviewFileOptions,
    ReviewFileWorkflowResult,
)
from content_review_engine.config import load_profile
from content_review_engine.core.models import BatchReviewResult, ReviewResult
from content_review_engine.core.quality_gate import (
    quality_gate_failed,
    severity_meets_threshold,
)
from content_review_engine.core.serialization import (
    batch_review_result_to_json,
    review_result_to_json,
)
from content_review_engine.llm import (
    BatchLLMReviewItem,
    LLMProviderConfig,
    LLMProviderNetworkError,
    LLMProviderRateLimitError,
    LLMProviderRetryExhaustedError,
    LLMProviderTimeoutError,
    LLMReviewError,
    LLMReviewResult,
    build_batch_combined_review_envelope,
    build_llm_review_request,
    build_single_file_combined_review_envelope,
    combined_review_envelope_to_json,
    create_llm_reviewer,
    evaluate_batch_llm_quality_gate,
    evaluate_llm_quality_gate,
    llm_review_result_to_json,
    llm_sidecar_result_to_json,
    load_llm_provider_config,
    load_llm_provider_config_file,
    merge_llm_provider_config,
    resolve_llm_provider_secret,
    run_batch_llm_review,
    run_single_file_llm_review,
)
from content_review_engine.parser import read_markdown
from content_review_engine.reports import (
    render_batch_markdown_report,
    render_batch_report_index,
    render_combined_markdown_report,
    render_llm_review_markdown,
    render_llm_sidecar_markdown,
    render_markdown_report,
    render_single_file_report_index,
)
from content_review_engine.review import review_document, review_markdown_directory


def _render_text_report(review_result: ReviewResult) -> str:
    lines = [
        "Review completed.",
        "",
        f"Findings: {review_result.summary.finding_count}",
        "",
    ]
    if not review_result.findings:
        lines.append("No issues found.")
        return "\n".join(lines)

    for finding in review_result.findings:
        lines.append(f"[{finding.severity}] {finding.rule_id}: {finding.message}")
        if finding.suggestion:
            lines.append(f"Suggestion: {finding.suggestion}")
        location = finding.location
        if location is not None:
            lines.append(f"Line: {location.start_line}")
            lines.append(f"Column: {location.start_column}")
            lines.append(f"Matched: {location.matched_text}")
            if location.context is not None:
                lines.append(f"Context: {location.context}")
        lines.append("")
    return "\n".join(lines)


def _render_batch_text_report(batch_result: BatchReviewResult) -> str:
    lines = [
        "Batch review completed.",
        "",
        f"Files discovered: {batch_result.summary.file_count}",
        f"Files reviewed: {batch_result.summary.reviewed_count}",
        f"Files with findings: {batch_result.summary.files_with_findings}",
        f"Findings: {batch_result.summary.finding_count}",
        "",
    ]
    if not batch_result.results:
        lines.append("No Markdown files found.")
        return "\n".join(lines)

    for review_result in batch_result.results:
        document_path = (
            review_result.document.path if review_result.document is not None else "Unknown"
        )
        lines.append(f"[{document_path}] Findings: {review_result.summary.finding_count}")
        if not review_result.findings:
            lines.append("No issues found.")
            lines.append("")
            continue

        for finding in review_result.findings:
            lines.append(f"[{finding.severity}] {finding.rule_id} - {finding.message}")
            if finding.suggestion:
                lines.append(f"Suggestion: {finding.suggestion}")
            location = finding.location
            if location is not None:
                lines.append(f"Line: {location.start_line}")
                lines.append(f"Column: {location.start_column}")
                lines.append(f"Matched: {location.matched_text}")
                if location.context is not None:
                    lines.append(f"Context: {location.context}")
            lines.append("")

    if lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def render_review_output(
    review_result: ReviewResult,
    *,
    output_format: str,
    fail_on: str | None = None,
) -> str:
    if output_format == "json":
        return review_result_to_json(review_result)
    if output_format == "markdown":
        return render_markdown_report(review_result, fail_on=fail_on, llm_result=None)
    return _render_text_report(review_result)


def render_batch_output(
    batch_result: BatchReviewResult,
    *,
    output_format: str,
    fail_on: str | None = None,
) -> str:
    if output_format == "json":
        return batch_review_result_to_json(batch_result)
    if output_format == "markdown":
        return render_batch_markdown_report(batch_result, fail_on=fail_on)
    return _render_batch_text_report(batch_result)


def _write_text_output(output_text: str, output_path: Path, *, label: str) -> None:
    try:
        output_path.write_text(output_text, encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Failed to write {label}: {output_path}: {exc}") from exc


def _build_deterministic_quality_gate_for_review(
    review_result: ReviewResult,
    threshold: str | None,
) -> DeterministicQualityGateResult:
    if threshold is None:
        return DeterministicQualityGateResult()

    matched_counts = {
        "info": 0,
        "warning": 0,
        "error": 0,
        "critical": 0,
    }
    matched_count = 0
    for finding in review_result.findings:
        if severity_meets_threshold(finding.severity, threshold):
            matched_counts[finding.severity] += 1
            matched_count += 1
    document_path = review_result.document.path if review_result.document is not None else None
    matched_files = (document_path,) if matched_count > 0 and document_path is not None else ()
    return DeterministicQualityGateResult(
        enabled=True,
        fail_on=threshold,
        failed=quality_gate_failed(review_result.summary.severity_counts, threshold),
        matched_finding_count=matched_count,
        matched_severity_counts=matched_counts,
        matched_file_count=1 if matched_files else 0,
        matched_files=matched_files,
    )


def _build_deterministic_quality_gate_for_batch(
    batch_result: BatchReviewResult,
    threshold: str | None,
) -> DeterministicQualityGateResult:
    if threshold is None:
        return DeterministicQualityGateResult()

    matched_counts = {
        "info": 0,
        "warning": 0,
        "error": 0,
        "critical": 0,
    }
    matched_count = 0
    matched_files: list[str] = []
    for review_result in batch_result.results:
        file_matched = False
        for finding in review_result.findings:
            if severity_meets_threshold(finding.severity, threshold):
                matched_counts[finding.severity] += 1
                matched_count += 1
                file_matched = True
        if file_matched and review_result.document is not None:
            matched_files.append(review_result.document.path)

    return DeterministicQualityGateResult(
        enabled=True,
        fail_on=threshold,
        failed=quality_gate_failed(batch_result.summary.severity_counts, threshold),
        matched_finding_count=matched_count,
        matched_severity_counts=matched_counts,
        matched_file_count=len(matched_files),
        matched_files=tuple(matched_files),
    )


def _build_llm_provider_config_from_options(
    options: ReviewFileOptions | ReviewBatchOptions,
) -> LLMProviderConfig:
    if options.llm_provider_config is not None:
        base_config = options.llm_provider_config
    elif options.llm_config_path is not None:
        base_config = load_llm_provider_config_file(options.llm_config_path)
    else:
        base_config = load_llm_provider_config()
    return merge_llm_provider_config(
        base_config,
        provider=options.llm_provider,
        model=options.llm_model,
        api_key_env=options.llm_api_key_env,
        base_url=options.llm_base_url,
        timeout_seconds=options.llm_timeout_seconds,
        retry_attempts=options.llm_retry_attempts,
        retry_backoff_seconds=options.llm_retry_backoff_seconds,
        min_request_interval_seconds=options.llm_min_request_interval_seconds,
    )


def _build_llm_reviewer_from_options(
    options: ReviewFileOptions | ReviewBatchOptions,
    *,
    reviewer_factory=None,
    secret_resolver=None,
):
    if reviewer_factory is None:
        reviewer_factory = create_llm_reviewer
    if secret_resolver is None:
        secret_resolver = resolve_llm_provider_secret
    if options.llm_provider in {"mock", "pydantic-ai-testmodel"}:
        return reviewer_factory(options.llm_provider)

    config = _build_llm_provider_config_from_options(options)
    if config.provider == "pydanticai" and config.model is None:
        raise ValueError(
            "LLM provider 'pydanticai' requires --llm-model or llm-config model."
        )
    secret_value = None
    if config.provider == "pydanticai":
        secret_value = secret_resolver(config)
    return reviewer_factory(config, secret_value=secret_value)


def _build_llm_sidecar_provider_metadata(
    options: ReviewFileOptions | ReviewBatchOptions,
) -> tuple[str, str]:
    if options.llm_provider is not None:
        return (options.llm_provider.strip().lower(), "explicit")
    config = _build_llm_provider_config_from_options(options)
    provider_source = "config" if options.llm_config_path is not None else "default"
    return (config.provider, provider_source)


def _run_single_file_llm(
    *,
    markdown_text: str,
    markdown_path: str,
    profile_name: str,
    reviewer,
) -> LLMReviewResult:
    request = build_llm_review_request(
        markdown_text=markdown_text,
        markdown_path=markdown_path,
        profile_name=profile_name,
    )
    return run_single_file_llm_review(
        request,
        reviewer=reviewer,
        provider=getattr(reviewer, "config", None).provider
        if getattr(reviewer, "config", None) is not None
        else getattr(reviewer, "provider", None),
        model=getattr(reviewer, "model", None),
    )


def _build_single_file_llm_error(exc: Exception, *, reviewer=None):
    provider = None
    reviewer_config = getattr(reviewer, "config", None)
    if reviewer_config is not None:
        provider = getattr(reviewer_config, "provider", None)
    if provider is None:
        provider = getattr(reviewer, "provider", None)
    return {
        "type": exc.__class__.__name__,
        "message": str(exc),
        "provider": provider,
        "retryable": isinstance(
            exc,
            (
                LLMProviderTimeoutError,
                LLMProviderNetworkError,
                LLMProviderRateLimitError,
                LLMProviderRetryExhaustedError,
            ),
        ),
    }


def _build_batch_llm_review_items(
    *,
    batch_result: BatchReviewResult,
    profile_name: str,
) -> list[BatchLLMReviewItem]:
    items: list[BatchLLMReviewItem] = []
    for review_result in batch_result.results:
        document = review_result.document
        if document is None:
            continue
        markdown_path = document.path
        try:
            markdown_text = read_markdown(markdown_path)
        except Exception as exc:  # pragma: no cover - exercised via sidecar result
            items.append(BatchLLMReviewItem(path=markdown_path, error=exc))
            continue
        items.append(
            BatchLLMReviewItem(
                path=markdown_path,
                request=build_llm_review_request(
                    markdown_text=markdown_text,
                    markdown_path=markdown_path,
                    profile_name=profile_name,
                ),
            )
        )
    return items


def execute_review_file(
    options: ReviewFileOptions,
    *,
    emit_output: Callable[[str], None] | None = None,
    reviewer_factory=None,
    secret_resolver=None,
) -> ReviewFileWorkflowResult:
    reviewer = None
    if options.enable_llm:
        reviewer = _build_llm_reviewer_from_options(
            options,
            reviewer_factory=reviewer_factory,
            secret_resolver=secret_resolver,
        )
    markdown_text = read_markdown(options.markdown_path)
    profile = load_profile(options.profile_path)
    review_result = review_document(
        markdown_text,
        profile,
        document_path=options.markdown_path,
        profile_path=options.profile_path,
    )
    output_text = render_review_output(
        review_result,
        output_format=options.output_format,
        fail_on=options.fail_on,
    )
    if options.output_path is not None:
        _write_text_output(output_text, options.output_path, label="review output")
    elif emit_output is not None:
        emit_output(output_text)

    artifacts = ReviewArtifactPaths(
        output_path=str(options.output_path) if options.output_path is not None else None,
    )
    deterministic_quality_gate = _build_deterministic_quality_gate_for_review(
        review_result,
        options.fail_on,
    )
    llm_result = None
    llm_status = "not_run"
    llm_error = None
    llm_quality_gate = evaluate_llm_quality_gate(None, options.llm_fail_on)
    combined_result = None

    if options.enable_llm:
        try:
            llm_result = _run_single_file_llm(
                markdown_text=markdown_text,
                markdown_path=str(options.markdown_path),
                profile_name=profile.name,
                reviewer=reviewer,
            )
            llm_status = "succeeded"
            llm_quality_gate = evaluate_llm_quality_gate(llm_result, options.llm_fail_on)
            if options.llm_output_path is not None:
                _write_text_output(
                    llm_review_result_to_json(llm_result),
                    options.llm_output_path,
                    label="LLM review result",
                )
                artifacts.llm_output_path = str(options.llm_output_path)
            if options.llm_report_path is not None:
                _write_text_output(
                    render_llm_review_markdown(llm_result, file_path=str(options.markdown_path)),
                    options.llm_report_path,
                    label="LLM Markdown report",
                )
                artifacts.llm_report_path = str(options.llm_report_path)
        except LLMReviewError as exc:
            llm_status = "failed"
            llm_quality_gate = evaluate_llm_quality_gate(
                None,
                options.llm_fail_on,
                execution_failed=True,
            )
            llm_error = _build_single_file_llm_error(exc, reviewer=reviewer)
            if options.raise_on_llm_error:
                combined_result = (
                    build_single_file_combined_review_envelope(
                        review_result=review_result,
                        llm_status=llm_status,
                        llm_error=llm_error,
                        llm_quality_gate=llm_quality_gate,
                    )
                    if options.include_combined_result or options.combined_output_path is not None
                    else None
                )
                if combined_result is not None and options.combined_output_path is not None:
                    combined_text = (
                        combined_review_envelope_to_json(combined_result)
                        if options.combined_output_format == "json"
                        else render_combined_markdown_report(combined_result)
                    )
                    _write_text_output(
                        combined_text,
                        options.combined_output_path,
                        label="combined review output",
                    )
                    artifacts.combined_output_path = str(options.combined_output_path)
                raise

    if options.include_combined_result or options.combined_output_path is not None:
        combined_result = build_single_file_combined_review_envelope(
            review_result=review_result,
            llm_result=llm_result,
            llm_status=llm_status,
            llm_error=llm_error,
            llm_quality_gate=llm_quality_gate,
        )
        if options.combined_output_path is not None:
            combined_text = (
                combined_review_envelope_to_json(combined_result)
                if options.combined_output_format == "json"
                else render_combined_markdown_report(combined_result)
            )
            _write_text_output(
                combined_text,
                options.combined_output_path,
                label="combined review output",
            )
            artifacts.combined_output_path = str(options.combined_output_path)

    if options.report_index_path is not None and llm_status != "failed":
        report_index_text = render_single_file_report_index(
            review_result,
            deterministic_output_path=(
                str(options.output_path) if options.output_path is not None else None
            ),
            deterministic_output_format=options.output_format,
            report_index_path=str(options.report_index_path),
            llm_enabled=options.enable_llm,
            llm_result=llm_result,
            llm_output_path=(
                str(options.llm_output_path) if options.llm_output_path is not None else None
            ),
            llm_report_path=(
                str(options.llm_report_path) if options.llm_report_path is not None else None
            ),
        )
        _write_text_output(report_index_text, options.report_index_path, label="report index")
        artifacts.report_index_path = str(options.report_index_path)

    return ReviewFileWorkflowResult(
        options=options,
        review_result=review_result,
        output_text=output_text,
        deterministic_quality_gate=deterministic_quality_gate,
        llm_result=llm_result,
        llm_status=llm_status,
        llm_error=llm_error,
        llm_quality_gate=llm_quality_gate,
        combined_result=combined_result,
        artifacts=artifacts,
    )


def execute_review_batch(
    options: ReviewBatchOptions,
    *,
    emit_output: Callable[[str], None] | None = None,
    reviewer_factory=None,
    secret_resolver=None,
) -> ReviewBatchWorkflowResult:
    reviewer = None
    if options.enable_llm:
        reviewer = _build_llm_reviewer_from_options(
            options,
            reviewer_factory=reviewer_factory,
            secret_resolver=secret_resolver,
        )
    profile = load_profile(options.profile_path)
    batch_result = review_markdown_directory(
        options.input_dir,
        profile,
        pattern=options.pattern,
        recursive=options.recursive,
        profile_path=options.profile_path,
    )
    output_text = render_batch_output(
        batch_result,
        output_format=options.output_format,
        fail_on=options.fail_on,
    )
    if options.output_path is not None:
        _write_text_output(output_text, options.output_path, label="batch review output")
    elif emit_output is not None:
        emit_output(output_text)

    artifacts = ReviewArtifactPaths(
        output_path=str(options.output_path) if options.output_path is not None else None,
    )
    deterministic_quality_gate = _build_deterministic_quality_gate_for_batch(
        batch_result,
        options.fail_on,
    )
    llm_sidecar_result = None
    llm_quality_gate = evaluate_batch_llm_quality_gate(None, options.llm_fail_on)
    combined_result = None

    if options.enable_llm:
        llm_provider, llm_provider_source = _build_llm_sidecar_provider_metadata(options)
        batch_items = _build_batch_llm_review_items(
            batch_result=batch_result,
            profile_name=profile.name,
        )
        llm_sidecar_result = run_batch_llm_review(
            batch_items,
            reviewer=reviewer,
            llm_provider=llm_provider,
            llm_provider_source=llm_provider_source,
            provider=getattr(reviewer, "config", None).provider
            if getattr(reviewer, "config", None) is not None
            else getattr(reviewer, "provider", None),
            model=getattr(reviewer, "model", None),
        )
        if options.llm_output_path is not None:
            _write_text_output(
                llm_sidecar_result_to_json(llm_sidecar_result),
                options.llm_output_path,
                label="LLM sidecar",
            )
            artifacts.llm_output_path = str(options.llm_output_path)
        if options.llm_report_path is not None:
            _write_text_output(
                render_llm_sidecar_markdown(llm_sidecar_result),
                options.llm_report_path,
                label="LLM Markdown report",
            )
            artifacts.llm_report_path = str(options.llm_report_path)
        llm_quality_gate = evaluate_batch_llm_quality_gate(
            llm_sidecar_result,
            options.llm_fail_on,
        )

    if options.include_combined_result or options.combined_output_path is not None:
        combined_result = build_batch_combined_review_envelope(
            batch_review_result=batch_result,
            batch_llm_result=llm_sidecar_result,
            default_llm_status="not_run" if llm_sidecar_result is None else "skipped",
            llm_quality_gate=llm_quality_gate,
        )
        if options.combined_output_path is not None:
            combined_text = (
                combined_review_envelope_to_json(combined_result)
                if options.combined_output_format == "json"
                else render_combined_markdown_report(combined_result)
            )
            _write_text_output(
                combined_text,
                options.combined_output_path,
                label="combined review output",
            )
            artifacts.combined_output_path = str(options.combined_output_path)

    if options.report_index_path is not None:
        report_index_text = render_batch_report_index(
            batch_result,
            input_dir=str(options.input_dir),
            profile_path=str(options.profile_path),
            deterministic_output_path=(
                str(options.output_path) if options.output_path is not None else None
            ),
            deterministic_output_format=options.output_format,
            report_index_path=str(options.report_index_path),
            llm_enabled=options.enable_llm,
            llm_result=llm_sidecar_result,
            llm_output_path=(
                str(options.llm_output_path) if options.llm_output_path is not None else None
            ),
            llm_report_path=(
                str(options.llm_report_path) if options.llm_report_path is not None else None
            ),
        )
        _write_text_output(report_index_text, options.report_index_path, label="report index")
        artifacts.report_index_path = str(options.report_index_path)

    result = ReviewBatchWorkflowResult(
        options=options,
        batch_result=batch_result,
        output_text=output_text,
        deterministic_quality_gate=deterministic_quality_gate,
        llm_sidecar_result=llm_sidecar_result,
        llm_quality_gate=llm_quality_gate,
        combined_result=combined_result,
        artifacts=artifacts,
    )
    if (
        options.raise_on_llm_error
        and llm_sidecar_result is not None
        and llm_sidecar_result.summary.failed_count > 0
    ):
        raise LLMReviewError("Batch LLM review failed for one or more files.")
    return result


__all__ = [
    "execute_review_batch",
    "execute_review_file",
    "render_batch_output",
    "render_review_output",
]
