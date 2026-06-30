from __future__ import annotations

from content_review_engine.llm.batch_combined_result import (
    BatchCombinedFileResult,
    BatchCombinedReviewResult,
)
from content_review_engine.llm.manual_review import (
    LLMBatchManualReviewItem,
    LLMExecutionReviewItem,
    build_llm_manual_review_items,
)
from content_review_engine.llm.policy import (
    format_llm_confidence_like_value,
    render_llm_finding_policy_note,
)
from content_review_engine.reports.markdown import render_batch_markdown_report


def _escape_cell(value: object) -> str:
    if value is None:
        return "-"
    if not isinstance(value, str):
        return str(value)
    if value == "":
        return "-"
    return value.replace("|", "\\|").replace("\n", "<br>")


def _append_table(lines: list[str], heading: str, rows: list[tuple[str, str]]) -> None:
    lines.extend([heading, "", "| Field | Value |", "| --- | --- |"])
    for label, value in rows:
        lines.append(f"| {label} | {value} |")
    lines.append("")


def _append_bullets(lines: list[str], heading: str, items: list[str]) -> None:
    lines.extend([heading, ""])
    for item in items:
        lines.append(f"- {item}")
    lines.append("")


def _format_location(file_result: BatchCombinedFileResult, original_index: int | None) -> str:
    if (
        original_index is None
        or file_result.llm_result is None
        or original_index >= len(file_result.llm_result.findings)
    ):
        return "-"

    finding = file_result.llm_result.findings[original_index]
    if finding.line is None:
        return "-"
    location = str(finding.line)
    if finding.column is not None:
        location = f"{location}:{finding.column}"
    return location


def _format_confidence(
    file_result: BatchCombinedFileResult,
    original_index: int | None,
) -> str:
    if (
        original_index is None
        or file_result.llm_result is None
        or original_index >= len(file_result.llm_result.findings)
    ):
        return "not provided"
    return format_llm_confidence_like_value(
        file_result.llm_result.findings[original_index]
    )


def _render_batch_status(result: BatchCombinedReviewResult) -> str:
    summary = result.llm_summary
    if summary.total_files == 0:
        return "not_run"
    if summary.not_run_count == summary.total_files:
        return "not_run"
    if summary.skipped_count == summary.total_files:
        return "skipped"
    if summary.succeeded_count == summary.total_files:
        return "all_succeeded"
    if summary.failed_count == summary.total_files:
        return "all_failed"
    if summary.failed_count > 0:
        return "partial_failure"
    return "mixed"


def _build_batch_manual_review_items(
    result: BatchCombinedReviewResult,
) -> tuple[LLMBatchManualReviewItem, ...]:
    items: list[LLMBatchManualReviewItem] = []
    checklist_index = 1
    for file_result in result.files:
        if file_result.llm_result is None:
            continue
        for item in build_llm_manual_review_items(file_result.llm_result):
            items.append(
                LLMBatchManualReviewItem(
                    checklist_id=f"LLM-{checklist_index:03d}",
                    file_path=file_result.file,
                    priority=item.priority,
                    status=item.status,
                    decision=item.decision,
                    quality_gate=item.quality_gate,
                    rule_id=item.rule_id,
                    location=item.location,
                    message=item.message,
                    notes=item.notes,
                )
            )
            checklist_index += 1
    return tuple(items)


def _build_execution_review_items(
    result: BatchCombinedReviewResult,
) -> tuple[LLMExecutionReviewItem, ...]:
    items: list[LLMExecutionReviewItem] = []
    checklist_index = 1
    for file_result in result.files:
        if file_result.llm_error is None:
            continue
        items.append(
            LLMExecutionReviewItem(
                checklist_id=f"LLM-ERR-{checklist_index:03d}",
                file_path=file_result.file,
                status="needs_rerun",
                suggested_action="rerun_llm_review",
                error_type=file_result.llm_error.type,
                error_message=file_result.llm_error.message,
            )
        )
        checklist_index += 1
    return tuple(items)


def _append_llm_summary(lines: list[str], result: BatchCombinedReviewResult) -> None:
    batch_status = _render_batch_status(result)
    provider = "-"
    provider_source = "-"
    if result.batch_llm_result is not None:
        provider = _escape_cell(result.batch_llm_result.llm_provider)
        provider_source = _escape_cell(result.batch_llm_result.llm_provider_source)

    _append_table(
        lines,
        "## LLM Summary",
        [
            ("LLM Batch Status", batch_status),
            ("LLM Provider", provider),
            ("LLM Provider Source", provider_source),
            ("LLM Total Files", str(result.llm_summary.total_files)),
            ("LLM Succeeded", str(result.llm_summary.succeeded_count)),
            ("LLM Failed", str(result.llm_summary.failed_count)),
            ("LLM Skipped", str(result.llm_summary.skipped_count)),
            ("LLM Not Run", str(result.llm_summary.not_run_count)),
            ("LLM Advisory Findings", str(result.llm_summary.advisory_finding_count)),
            (
                "Files With LLM Advisory Findings",
                str(result.llm_summary.files_with_advisory_findings),
            ),
            ("LLM Errors", str(result.llm_summary.error_count)),
            ("Advisory", "yes"),
            ("Quality Gate Participation", "no"),
            ("Policy Note", _escape_cell(render_llm_finding_policy_note())),
        ],
    )


def _append_file_status_summary(
    lines: list[str],
    result: BatchCombinedReviewResult,
) -> None:
    lines.extend(
        [
            "## File Status Summary",
            "",
            "| File | Status | Advisory Findings | Error |",
            "| --- | --- | ---: | --- |",
        ]
    )
    if not result.files:
        lines.extend(["| - | - | 0 | - |", ""])
        return

    for file_result in result.files:
        error_value = "-"
        if file_result.llm_error is not None:
            error_value = _escape_cell(
                f"{file_result.llm_error.type}: {file_result.llm_error.message}"
            )
        lines.append(
            "| "
            f"{_escape_cell(file_result.file)} | "
            f"{file_result.llm_status} | "
            f"{len(file_result.llm_finding_candidates)} | "
            f"{error_value} |"
        )
    lines.append("")


def _append_advisory_findings(
    lines: list[str],
    result: BatchCombinedReviewResult,
) -> None:
    lines.extend(["## LLM Advisory Findings", ""])
    if result.llm_summary.advisory_finding_count == 0:
        lines.extend(["No LLM advisory findings.", ""])
        return

    lines.extend(
        [
            "| File | Severity | Rule | Source | Advisory | Quality Gate | Confidence | Location | Message | Suggestion |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for file_result in result.files:
        for candidate in file_result.llm_finding_candidates:
            lines.append(
                "| "
                f"{_escape_cell(file_result.file)} | "
                f"{candidate.severity} | "
                f"{_escape_cell(candidate.rule_id)} | "
                f"{_escape_cell(candidate.source)} | "
                f"{'yes' if candidate.advisory else 'no'} | "
                f"no | "
                f"{_escape_cell(_format_confidence(file_result, candidate.original_index))} | "
                f"{_escape_cell(_format_location(file_result, candidate.original_index))} | "
                f"{_escape_cell(candidate.message)} | "
                f"{_escape_cell(candidate.suggestion)} |"
            )
    lines.append("")


def _append_error_summary(lines: list[str], result: BatchCombinedReviewResult) -> None:
    lines.extend(["## LLM Error Summary", ""])
    if result.llm_summary.error_count == 0:
        lines.extend(["No LLM errors.", ""])
        return

    lines.extend(
        [
            "| File | Type | Message | Provider | Retryable |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for file_result in result.files:
        if file_result.llm_error is None:
            continue
        retryable = "-"
        if file_result.llm_error.retryable is not None:
            retryable = str(file_result.llm_error.retryable).lower()
        lines.append(
            "| "
            f"{_escape_cell(file_result.file)} | "
            f"{_escape_cell(file_result.llm_error.type)} | "
            f"{_escape_cell(file_result.llm_error.message)} | "
            f"{_escape_cell(file_result.llm_error.provider)} | "
            f"{retryable} |"
        )
    lines.append("")


def _append_manual_review_sections(
    lines: list[str],
    result: BatchCombinedReviewResult,
) -> None:
    batch_status = _render_batch_status(result)
    manual_items = _build_batch_manual_review_items(result)
    execution_items = _build_execution_review_items(result)

    workflow_items = [
        "Review deterministic findings first; they remain the canonical batch output and the only quality-gate source.",
        "Treat LLM findings as advisory semantic suggestions that require human confirmation before any content change.",
        "Manual review checklist state is presentation-only and is not persisted into BatchReviewResult, LLMSidecarResult, or any review-state file.",
    ]
    if batch_status == "partial_failure":
        workflow_items.append(
            "This batch has partial LLM failure; inspect the LLM error summary, decide whether failed files should be rerun, and keep deterministic findings as the baseline for every file."
        )
    elif batch_status == "all_failed":
        workflow_items.append(
            "All LLM review attempts failed in this batch; use deterministic results as the complete audit baseline and decide separately whether an LLM rerun is warranted."
        )
    elif batch_status == "not_run":
        workflow_items.append(
            "No LLM review was run for this batch, so semantic follow-up remains a manual decision outside the deterministic quality gate."
        )
    elif batch_status == "skipped":
        workflow_items.append(
            "LLM review was skipped for this batch, so no advisory findings are available and semantic follow-up remains manual."
        )
    elif not manual_items:
        workflow_items.append(
            "The LLM review succeeded but returned no advisory findings; if semantic risk still matters, perform manual spot checks."
        )
    else:
        workflow_items.append(
            f"Current advisory checklist items: {len(manual_items)}."
        )
    if execution_items:
        workflow_items.append(
            f"Current execution follow-up items: {len(execution_items)}."
        )

    _append_bullets(lines, "## Manual Review Workflow", workflow_items)

    lines.extend(["## Manual Review Checklist", ""])
    if not manual_items:
        lines.extend(["No manual review checklist items.", ""])
    else:
        lines.extend(
            [
                "| ID | File | Priority | Status | Decision | Quality Gate | Rule | Location | Message | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for item in manual_items:
            lines.append(
                "| "
                f"{item.checklist_id} | "
                f"{_escape_cell(item.file_path)} | "
                f"{item.priority} | "
                f"{item.status} | "
                f"{item.decision} | "
                f"{item.quality_gate} | "
                f"{_escape_cell(item.rule_id)} | "
                f"{_escape_cell(item.location)} | "
                f"{_escape_cell(item.message)} | "
                f"{_escape_cell(item.notes)} |"
            )
        lines.append("")

    if not execution_items:
        return

    lines.extend(["## LLM Execution Review Checklist", ""])
    lines.extend(
        [
            "| ID | File | Status | Suggested Action | Error Type | Error Message | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in execution_items:
        lines.append(
            "| "
            f"{item.checklist_id} | "
            f"{_escape_cell(item.file_path)} | "
            f"{item.status} | "
            f"{item.suggested_action} | "
            f"{_escape_cell(item.error_type)} | "
            f"{_escape_cell(item.error_message)} | "
            f"{_escape_cell(item.notes)} |"
        )
    lines.append("")


def render_batch_combined_markdown_report(
    result: BatchCombinedReviewResult,
) -> str:
    deterministic_report = render_batch_markdown_report(result.batch_review_result)
    summary = result.batch_review_result.summary

    lines = ["# Batch Combined Content Review Report", ""]
    _append_table(
        lines,
        "## Summary",
        [
            ("Files Reviewed", str(summary.reviewed_count)),
            ("Deterministic Findings", str(summary.finding_count)),
            ("LLM Total Files", str(result.llm_summary.total_files)),
            ("LLM Succeeded", str(result.llm_summary.succeeded_count)),
            ("LLM Failed", str(result.llm_summary.failed_count)),
            ("LLM Skipped", str(result.llm_summary.skipped_count)),
            ("LLM Not Run", str(result.llm_summary.not_run_count)),
            ("LLM Advisory Findings", str(result.llm_summary.advisory_finding_count)),
            (
                "Files With LLM Advisory Findings",
                str(result.llm_summary.files_with_advisory_findings),
            ),
            ("LLM Errors", str(result.llm_summary.error_count)),
            ("Quality Gate Scope", "deterministic-only"),
        ],
    )
    _append_llm_summary(lines, result)
    _append_file_status_summary(lines, result)
    _append_advisory_findings(lines, result)
    _append_error_summary(lines, result)
    _append_manual_review_sections(lines, result)
    _append_bullets(
        lines,
        "## Quality Gate Boundary",
        [
            "Quality gate evaluation remains deterministic-only.",
            "LLM advisory findings do not participate in severity counts, rule counts, fail-on, quality gate, or exit code.",
            "Use the deterministic batch report below as the canonical audit record for automation and compliance checks.",
        ],
    )
    lines.extend(["## Deterministic Review", "", deterministic_report, ""])
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["render_batch_combined_markdown_report"]
