from __future__ import annotations

from content_review_engine.llm.manual_review import (
    build_batch_llm_manual_review_items,
    build_llm_execution_review_items,
    build_llm_manual_review_items,
)
from content_review_engine.llm.models import LLMSidecarFile, LLMSidecarResult, LLMReviewFinding, LLMReviewResult
from content_review_engine.llm.policy import (
    LLM_FINDING_SEVERITY_ORDER,
    build_llm_finding_display_metadata,
    format_llm_confidence_like_value,
    render_llm_finding_policy_note,
)


def _escape_cell(value: str | None) -> str:
    if value is None or value == "":
        return "-"
    return value.replace("|", "\\|").replace("\n", "<br>")


def _format_inline_code(value: str | None) -> str:
    if value is None or value == "":
        return "`-`"
    return f"`{value}`"


def _format_location(finding: LLMReviewFinding) -> str:
    if finding.line is None:
        return "unavailable"
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


def _severity_counts(findings: tuple[LLMReviewFinding, ...]) -> dict[str, int]:
    counts = {severity: 0 for severity in LLM_FINDING_SEVERITY_ORDER}
    for finding in findings:
        metadata = build_llm_finding_display_metadata(finding)
        counts[metadata.severity] = counts.get(metadata.severity, 0) + 1
    return counts


def _append_summary_table(lines: list[str], rows: list[tuple[str, str]]) -> None:
    lines.extend(
        [
            "## Summary",
            "",
            "| Field | Value |",
            "| --- | --- |",
        ]
    )
    for label, value in rows:
        lines.append(f"| {label} | {value} |")
    lines.append("")


def _append_severity_counts(lines: list[str], findings: tuple[LLMReviewFinding, ...]) -> None:
    lines.extend(
        [
            "## Severity Counts",
            "",
            "| Severity | Count |",
            "| --- | ---: |",
        ]
    )
    counts = _severity_counts(findings)
    for severity in LLM_FINDING_SEVERITY_ORDER:
        lines.append(f"| {severity} | {counts[severity]} |")
    lines.append("")


def _append_policy_table(lines: list[str]) -> None:
    lines.extend(
        [
            "## Advisory Policy",
            "",
            "| Field | Value |",
            "| --- | --- |",
            "| Source | llm |",
            "| Advisory | yes |",
            "| Quality Gate Participation | no |",
            "| Severity Semantics | LLM advisory severity only |",
            "| Rule ID Semantics | LLM semantic review layer only |",
            f"| Policy Note | {_escape_cell(render_llm_finding_policy_note())} |",
            "",
        ]
    )


def _append_findings_table(lines: list[str], findings: tuple[LLMReviewFinding, ...]) -> None:
    lines.extend(["## Findings", ""])
    if not findings:
        lines.extend(["No LLM findings.", ""])
        return

    lines.extend(
        [
            "| Severity | Rule | Source | Advisory | Quality Gate | Confidence | Line | Column | Message | Suggestion |",
            "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for finding in findings:
        metadata = build_llm_finding_display_metadata(finding)
        lines.append(
            "| "
            f"{metadata.severity} | "
            f"{_escape_cell(metadata.rule_id)} | "
            f"{metadata.source} | "
            f"{metadata.advisory} | "
            f"{metadata.participates_in_quality_gate} | "
            f"{_escape_cell(metadata.confidence)} | "
            f"{finding.line if finding.line is not None else '-'} | "
            f"{finding.column if finding.column is not None else '-'} | "
            f"{_escape_cell(finding.message)} | "
            f"{_escape_cell(finding.suggestion)} |"
        )
    lines.append("")


def _append_detailed_findings(lines: list[str], findings: tuple[LLMReviewFinding, ...]) -> None:
    lines.extend(["## Detailed Findings", ""])
    if not findings:
        lines.extend(["No LLM findings.", ""])
        return

    for index, finding in enumerate(findings, start=1):
        metadata = build_llm_finding_display_metadata(finding)
        lines.extend(
            [
                f"### {index}. {_escape_cell(metadata.rule_id)}",
                "",
                f"- Severity: {metadata.severity}",
                f"- Rule: {_format_inline_code(metadata.rule_id)}",
                f"- Source: {metadata.source}",
                f"- Advisory: {metadata.advisory}",
                f"- Quality Gate Participation: {metadata.participates_in_quality_gate}",
                f"- Confidence: {metadata.confidence}",
                f"- Location: {_format_location(finding)}",
                f"- Message: {_escape_cell(finding.message)}",
                f"- Suggestion: {_escape_cell(finding.suggestion)}",
                f"- Matched Text: {_format_inline_code(finding.matched_text)}",
            ]
        )
        if finding.rationale is not None:
            lines.append(f"- Rationale: {_escape_cell(finding.rationale)}")
        if finding.category is not None:
            lines.append(f"- Category: {_escape_cell(finding.category)}")
        lines.append("")


def _append_manual_review_checklist(lines: list[str], result: LLMReviewResult) -> None:
    items = build_llm_manual_review_items(result)
    lines.extend(["## Manual Review Checklist", ""])
    if not items:
        lines.extend(["No manual review checklist items.", ""])
        return

    lines.extend(
        [
            "| ID | Priority | Status | Decision | Quality Gate | Rule | Location | Message | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in items:
        lines.append(
            "| "
            f"{item.checklist_id} | "
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


def render_llm_review_markdown(
    result: LLMReviewResult,
    *,
    file_path: str | None = None,
) -> str:
    summary_rows = [
        ("File", _escape_cell(file_path)),
        ("Schema Version", _escape_cell(result.schema_version)),
        ("Provider", _escape_cell(result.provider)),
        ("Model", _escape_cell(result.model)),
        ("Prompt Version", _escape_cell(result.prompt_version)),
        ("Profile Name", _escape_cell(result.profile_name)),
        ("Total Findings", str(len(result.findings))),
    ]
    if result.summary is not None:
        summary_rows.extend(
            [
                ("Overall Risk", _escape_cell(result.summary.overall_risk)),
                ("LLM Summary", _escape_cell(result.summary.summary)),
                ("Recommended Action", _escape_cell(result.summary.recommended_action)),
                (
                    "Confidence",
                    "-"
                    if result.summary.confidence is None
                    else str(result.summary.confidence),
                ),
            ]
        )

    lines = ["# LLM Review Report", ""]
    _append_summary_table(lines, summary_rows)
    _append_policy_table(lines)
    _append_severity_counts(lines, result.findings)
    _append_findings_table(lines, result.findings)
    _append_manual_review_checklist(lines, result)
    _append_detailed_findings(lines, result.findings)
    return "\n".join(lines).rstrip()


def _append_batch_summary(lines: list[str], result: LLMSidecarResult) -> None:
    files_with_findings = sum(
        1
        for file in result.files
        if file.status == "success" and file.finding_count > 0
    )
    _append_summary_table(
        lines,
        [
            ("Schema Version", _escape_cell(result.schema_version)),
            ("LLM Provider", _escape_cell(result.llm_provider)),
            ("LLM Provider Source", _escape_cell(result.llm_provider_source)),
            ("Files Reviewed", str(result.summary.file_count)),
            ("Files With LLM Findings", str(files_with_findings)),
            ("Files With LLM Errors", str(result.summary.failed_count)),
            ("Total LLM Findings", str(result.summary.finding_count)),
        ],
    )


def _append_batch_severity_counts(lines: list[str], result: LLMSidecarResult) -> None:
    all_findings: list[LLMReviewFinding] = []
    for file in result.files:
        if file.review is not None:
            all_findings.extend(file.review.findings)
    _append_severity_counts(lines, tuple(all_findings))


def _format_file_error(file: LLMSidecarFile) -> str:
    if file.error is None:
        return "-"
    return _escape_cell(f"{file.error.error_type}: {file.error.message}")


def _append_file_status(lines: list[str], result: LLMSidecarResult) -> None:
    lines.extend(
        [
            "## File Status",
            "",
            "| File | Status | Findings | Error |",
            "| --- | --- | ---: | --- |",
        ]
    )
    if not result.files:
        lines.extend(["| - | - | 0 | - |", ""])
        return

    for file in result.files:
        lines.append(
            "| "
            f"{_escape_cell(file.path)} | "
            f"{file.status} | "
            f"{file.finding_count} | "
            f"{_format_file_error(file)} |"
        )
    lines.append("")


def _append_batch_file_details(lines: list[str], result: LLMSidecarResult) -> None:
    lines.extend(["## Findings By File", ""])
    if not result.files:
        lines.extend(["No files.", ""])
        return

    for file in result.files:
        lines.extend([f"### {_format_inline_code(file.path)}", ""])
        lines.append(f"- Status: {file.status}")
        lines.append(f"- Findings: {file.finding_count}")
        if file.error is not None:
            lines.append(f"- Error Type: {_format_inline_code(file.error.error_type)}")
            lines.append(f"- Message: {_escape_cell(file.error.message)}")
            lines.append("")
            continue
        if file.review is None:
            lines.extend(["No LLM findings.", ""])
            continue

        summary = file.review.summary
        if summary is not None:
            lines.append(f"- Overall Risk: {_escape_cell(summary.overall_risk)}")
            lines.append(f"- Summary: {_escape_cell(summary.summary)}")
            lines.append(
                f"- Recommended Action: {_escape_cell(summary.recommended_action)}"
            )
            lines.append(f"- Confidence: {format_llm_confidence_like_value(summary)}")
        lines.append("")
        _append_findings_table(lines, file.review.findings)
        _append_detailed_findings(lines, file.review.findings)


def _append_batch_manual_review_checklist(lines: list[str], result: LLMSidecarResult) -> None:
    items = build_batch_llm_manual_review_items(result)
    lines.extend(["## Manual Review Checklist", ""])
    if not items:
        lines.extend(["No manual review checklist items.", ""])
        return

    lines.extend(
        [
            "| ID | File | Priority | Status | Decision | Quality Gate | Rule | Location | Message | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in items:
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


def _append_execution_review_checklist(lines: list[str], result: LLMSidecarResult) -> None:
    items = build_llm_execution_review_items(result)
    if not items:
        return

    lines.extend(["## LLM Execution Review Checklist", ""])
    lines.extend(
        [
            "| ID | File | Status | Suggested Action | Error Type | Error Message | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in items:
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


def render_llm_sidecar_markdown(result: LLMSidecarResult) -> str:
    lines = ["# Batch LLM Review Report", ""]
    _append_batch_summary(lines, result)
    _append_policy_table(lines)
    _append_batch_severity_counts(lines, result)
    _append_file_status(lines, result)
    _append_batch_manual_review_checklist(lines, result)
    _append_execution_review_checklist(lines, result)
    _append_batch_file_details(lines, result)
    return "\n".join(lines).rstrip()


__all__ = [
    "render_llm_review_markdown",
    "render_llm_sidecar_markdown",
]
