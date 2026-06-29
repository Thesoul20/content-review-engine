from __future__ import annotations

from content_review_engine.llm.models import LLMSidecarFile, LLMSidecarResult, LLMReviewFinding, LLMReviewResult

_MARKDOWN_SEVERITY_ORDER: tuple[str, ...] = ("critical", "error", "warning", "info")


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
    counts = {severity: 0 for severity in _MARKDOWN_SEVERITY_ORDER}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
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
    for severity in _MARKDOWN_SEVERITY_ORDER:
        lines.append(f"| {severity} | {counts[severity]} |")
    lines.append("")


def _append_findings_table(lines: list[str], findings: tuple[LLMReviewFinding, ...]) -> None:
    lines.extend(["## Findings", ""])
    if not findings:
        lines.extend(["No LLM findings.", ""])
        return

    lines.extend(
        [
            "| Severity | Rule | Line | Column | Message | Suggestion |",
            "| --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for finding in findings:
        lines.append(
            "| "
            f"{finding.severity} | "
            f"{_escape_cell(finding.rule_id)} | "
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
        lines.extend(
            [
                f"### {index}. {_escape_cell(finding.rule_id)}",
                "",
                f"- Severity: {finding.severity}",
                f"- Rule: {_format_inline_code(finding.rule_id)}",
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
        if finding.confidence is not None:
            lines.append(f"- Confidence: {finding.confidence}")
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
    _append_severity_counts(lines, result.findings)
    _append_findings_table(lines, result.findings)
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
            if summary.confidence is not None:
                lines.append(f"- Confidence: {summary.confidence}")
        lines.append("")
        _append_findings_table(lines, file.review.findings)
        _append_detailed_findings(lines, file.review.findings)


def render_llm_sidecar_markdown(result: LLMSidecarResult) -> str:
    lines = ["# Batch LLM Review Report", ""]
    _append_batch_summary(lines, result)
    _append_batch_severity_counts(lines, result)
    _append_file_status(lines, result)
    _append_batch_file_details(lines, result)
    return "\n".join(lines).rstrip()


__all__ = [
    "render_llm_review_markdown",
    "render_llm_sidecar_markdown",
]
