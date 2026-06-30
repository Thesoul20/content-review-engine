from __future__ import annotations

import re
from pathlib import Path

from content_review_engine.core.models import REVIEW_SUMMARY_SEVERITIES, ReviewFinding
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

_ABSOLUTE_PATH_PATTERN = re.compile(r"^(?:/|[A-Za-z]:[\\/])")
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"AIza[0-9A-Za-z\\-_]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token)\b\s*[:=]\s*[^\s,;]+"),
)
_TRACEBACK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^Traceback \(most recent call last\):$"),
    re.compile(r'^  File "[^"]+", line \d+, in .+$'),
)


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


def _display_path(value: str | None) -> str:
    if value is None:
        return "-"
    normalized = value.strip()
    if normalized == "":
        return "-"
    if _ABSOLUTE_PATH_PATTERN.match(normalized):
        basename = Path(normalized).name.strip()
        if basename != "":
            return basename
        return "<absolute-path-redacted>"
    return normalized


def _sanitize_display_text(value: str | None) -> str:
    if value is None:
        return "-"

    cleaned_lines: list[str] = []
    for raw_line in value.splitlines():
        stripped = raw_line.strip()
        if stripped == "":
            continue
        if any(pattern.match(raw_line) for pattern in _TRACEBACK_PATTERNS):
            continue
        cleaned_lines.append(stripped)

    sanitized = " ".join(cleaned_lines) if cleaned_lines else value.strip()
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    return sanitized or "-"


def _format_severity_counts(severity_counts: dict[str, int]) -> str:
    return ", ".join(
        f"{severity}={severity_counts.get(severity, 0)}"
        for severity in REVIEW_SUMMARY_SEVERITIES
    )


def _format_rule_counts(findings: list[ReviewFinding]) -> str:
    if not findings:
        return "-"

    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.rule_id] = counts.get(finding.rule_id, 0) + 1
    return ", ".join(
        f"{rule_id}={count}" for rule_id, count in sorted(counts.items(), key=lambda item: item[0])
    )


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
        "## LLM Batch Summary",
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
            "## Combined File Results",
            "",
            "| File | Deterministic Findings | LLM Status | LLM Advisory Findings | LLM Error |",
            "| --- | ---: | --- | ---: | --- |",
        ]
    )
    if not result.files:
        lines.extend(["| - | 0 | - | 0 | - |", ""])
        return

    for review_result, file_result in zip(
        result.batch_review_result.results,
        result.files,
        strict=False,
    ):
        error_value = "-"
        if file_result.llm_error is not None:
            error_value = _escape_cell(
                _sanitize_display_text(
                    f"{file_result.llm_error.type}: {file_result.llm_error.message}"
                )
            )
        lines.append(
            "| "
            f"{_escape_cell(_display_path(file_result.file))} | "
            f"{review_result.summary.finding_count} | "
            f"{file_result.llm_status} | "
            f"{len(file_result.llm_finding_candidates)} | "
            f"{error_value} |"
        )
    lines.append("")


def _append_advisory_findings(
    lines: list[str],
    result: BatchCombinedReviewResult,
) -> None:
    lines.extend(["## LLM Findings by File", ""])
    if result.llm_summary.advisory_finding_count == 0:
        lines.extend(["No LLM advisory findings across reviewed files.", ""])
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
                f"{_escape_cell(_display_path(file_result.file))} | "
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
            f"{_escape_cell(_display_path(file_result.file))} | "
            f"{_escape_cell(file_result.llm_error.type)} | "
            f"{_escape_cell(_sanitize_display_text(file_result.llm_error.message))} | "
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
                f"{_escape_cell(_display_path(item.file_path))} | "
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
            f"{_escape_cell(_display_path(item.file_path))} | "
            f"{item.status} | "
            f"{item.suggested_action} | "
            f"{_escape_cell(item.error_type)} | "
            f"{_escape_cell(_sanitize_display_text(item.error_message))} | "
            f"{_escape_cell(item.notes)} |"
        )
    lines.append("")


def _append_artifact_boundary(lines: list[str]) -> None:
    _append_bullets(
        lines,
        "## Artifact Boundary",
        [
            "This file is an explicit batch combined artifact rendered from `BatchCombinedReviewResult`.",
            "It packages deterministic batch review data with optional batch LLM data for browsing, but it does not replace deterministic batch `--output` or raw batch `--llm-output`.",
            "LLM findings remain advisory and presentation-only in this report.",
        ],
    )


def _append_deterministic_batch_summary(
    lines: list[str],
    result: BatchCombinedReviewResult,
) -> None:
    summary = result.batch_review_result.summary
    all_findings = [
        finding
        for review_result in result.batch_review_result.results
        for finding in review_result.findings
    ]
    _append_table(
        lines,
        "## Deterministic Batch Summary",
        [
            ("Files Discovered", str(summary.file_count)),
            ("Files Reviewed", str(summary.reviewed_count)),
            ("Files With Findings", str(summary.files_with_findings)),
            ("Total Findings", str(summary.finding_count)),
            ("Severity Counts", _escape_cell(_format_severity_counts(summary.severity_counts))),
            ("Rule Counts", _escape_cell(_format_rule_counts(all_findings))),
            ("Quality Gate Source", "deterministic findings only"),
        ],
    )


def _append_deterministic_findings_by_file(
    lines: list[str],
    result: BatchCombinedReviewResult,
) -> None:
    lines.extend(["## Deterministic Findings by File", ""])
    if not result.batch_review_result.results:
        lines.extend(["No deterministic review results.", ""])
        return

    for review_result in result.batch_review_result.results:
        file_path = "-"
        if review_result.document is not None:
            file_path = _display_path(review_result.document.path)
        lines.extend([f"### {_escape_cell(file_path)}", ""])
        if not review_result.findings:
            lines.extend(["No deterministic findings.", ""])
            continue
        lines.extend(
            [
                "| Severity | Rule | Line | Column | Message | Suggestion |",
                "| --- | --- | ---: | ---: | --- | --- |",
            ]
        )
        for finding in review_result.findings:
            line_value = "-"
            column_value = "-"
            if finding.location is not None:
                line_value = str(finding.location.start_line)
                column_value = str(finding.location.start_column)
            lines.append(
                "| "
                f"{finding.severity} | "
                f"{_escape_cell(finding.rule_id)} | "
                f"{line_value} | "
                f"{column_value} | "
                f"{_escape_cell(finding.message)} | "
                f"{_escape_cell(finding.suggestion)} |"
            )
        lines.append("")


def render_batch_combined_markdown_report(
    result: BatchCombinedReviewResult,
) -> str:
    lines = ["# Batch Combined Content Review Report", ""]
    _append_artifact_boundary(lines)
    _append_deterministic_batch_summary(lines, result)
    _append_llm_summary(lines, result)
    _append_file_status_summary(lines, result)
    _append_deterministic_findings_by_file(lines, result)
    _append_advisory_findings(lines, result)
    _append_error_summary(lines, result)
    _append_manual_review_sections(lines, result)
    _append_bullets(
        lines,
        "## Quality Gate Behavior",
        [
            "Quality gate evaluation remains deterministic-only.",
            "LLM advisory findings do not participate in severity counts, rule counts, fail-on, quality gate, or exit code.",
            "Only deterministic findings can affect batch `--fail-on`, quality gate, or CLI exit code.",
        ],
    )
    _append_bullets(
        lines,
        "## Artifact Notes",
        [
            "`--output`, `--llm-output`, and `--combined-output` can coexist in the same batch run.",
            "Use deterministic batch `--output` as the canonical automation artifact and raw batch `--llm-output` as the canonical machine-readable LLM artifact.",
            "This combined Markdown report is a presentation artifact derived from the combined envelope and does not replace either JSON contract.",
        ],
    )
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["render_batch_combined_markdown_report"]
