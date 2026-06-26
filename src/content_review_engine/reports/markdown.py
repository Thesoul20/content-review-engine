from __future__ import annotations

from content_review_engine.core.models import (
    REVIEW_SUMMARY_SEVERITIES,
    BatchReviewResult,
    ReviewFinding,
    ReviewResult,
)
from content_review_engine.core.quality_gate import (
    count_findings_at_or_above,
    quality_gate_failed,
    severity_rank,
)
from content_review_engine.llm.models import LLMReviewFinding, LLMReviewResult

_MARKDOWN_SEVERITY_ORDER: tuple[str, ...] = ("critical", "error", "warning", "info")


def _escape_cell(value: str | None) -> str:
    if value is None or value == "":
        return "-"
    return value.replace("|", "\\|").replace("\n", "<br>")


def _format_inline_code(value: str | None) -> str:
    if value is None or value == "":
        return "Unknown"
    return f"`{value}`"


def _finding_location_value(finding: ReviewFinding, field_name: str) -> str:
    if finding.location is None:
        return "-"
    return str(getattr(finding.location, field_name))


def _rule_counts(findings: list[ReviewFinding]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.rule_id] = counts.get(finding.rule_id, 0) + 1
    return sorted(counts.items(), key=lambda item: item[0])


def _highest_severity(findings: list[ReviewFinding]) -> str:
    if not findings:
        return "-"
    return max(findings, key=lambda finding: severity_rank(finding.severity)).severity


def _append_summary_table(
    lines: list[str],
    rows: list[tuple[str, str]],
) -> None:
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


def _append_severity_counts(
    lines: list[str],
    severity_counts: dict[str, int],
) -> None:
    lines.extend(
        [
            "## Severity Counts",
            "",
            "| Severity | Count |",
            "| --- | ---: |",
        ]
    )
    for severity in _MARKDOWN_SEVERITY_ORDER:
        lines.append(f"| {severity} | {severity_counts.get(severity, 0)} |")
    lines.append("")


def _append_rule_counts(
    lines: list[str],
    findings: list[ReviewFinding],
) -> None:
    lines.extend(
        [
            "## Rule Counts",
            "",
            "| Rule | Count |",
            "| --- | ---: |",
        ]
    )
    for rule_id, count in _rule_counts(findings):
        lines.append(f"| {rule_id} | {count} |")
    if not findings:
        lines.append("| - | 0 |")
    lines.append("")


def _append_findings_table(
    lines: list[str],
    findings: list[ReviewFinding],
    *,
    heading: str,
) -> None:
    lines.extend([heading, ""])

    if not findings:
        lines.append("No findings.")
        lines.append("")
        return

    lines.extend(
        [
            "| Severity | Rule | Line | Column | Message | Suggestion |",
            "| --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for finding in findings:
        suggestion = _escape_cell(finding.suggestion)
        message = _escape_cell(finding.message)
        lines.append(
            "| "
            f"{finding.severity} | "
            f"{finding.rule_id} | "
            f"{_finding_location_value(finding, 'start_line')} | "
            f"{_finding_location_value(finding, 'start_column')} | "
            f"{message} | "
            f"{suggestion} |"
        )
    lines.append("")


def _append_detailed_findings(
    lines: list[str],
    findings: list[ReviewFinding],
    *,
    heading: str,
) -> None:
    lines.extend([heading, ""])

    if not findings:
        lines.append("No findings.")
        lines.append("")
        return

    for finding in findings:
        lines.extend(
            [
                f"### {finding.rule_id}",
                "",
                f"- Severity: {finding.severity}",
                f"- Message: {_escape_cell(finding.message)}",
                f"- Matched Term: `{finding.matched_term}`",
            ]
        )
        matched_text = finding.matched_text
        if finding.location is None:
            lines.append("- Location: unavailable")
        else:
            lines.append(f"- Line: {finding.location.start_line}")
            lines.append(f"- Column: {finding.location.start_column}")
            matched_text = finding.location.matched_text
            if finding.location.context is not None:
                lines.append(f"- Context: {_escape_cell(finding.location.context)}")
        if matched_text:
            lines.append(f"- Matched Text: `{matched_text}`")
        if finding.suggestion:
            lines.append(f"- Suggestion: {_escape_cell(finding.suggestion)}")
        lines.append("")


def _llm_severity_counts(
    llm_result: LLMReviewResult,
) -> dict[str, int]:
    counts = {severity: 0 for severity in _MARKDOWN_SEVERITY_ORDER}
    for finding in llm_result.findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    return counts


def _append_llm_summary(
    lines: list[str],
    llm_result: LLMReviewResult,
) -> None:
    summary_rows = [
        ("Schema Version", _escape_cell(llm_result.schema_version)),
        ("Provider", _escape_cell(llm_result.provider)),
        ("Model", _escape_cell(llm_result.model)),
        ("Prompt Version", _escape_cell(llm_result.prompt_version)),
        ("Profile Name", _escape_cell(llm_result.profile_name)),
        ("Total Findings", str(len(llm_result.findings))),
    ]
    lines.extend(
        [
            "### LLM Summary",
            "",
            "| Field | Value |",
            "| --- | --- |",
        ]
    )
    for label, value in summary_rows:
        lines.append(f"| {label} | {value} |")
    lines.append("")


def _append_llm_severity_counts(
    lines: list[str],
    llm_result: LLMReviewResult,
) -> None:
    lines.extend(
        [
            "### LLM Severity Counts",
            "",
            "| Severity | Count |",
            "| --- | ---: |",
        ]
    )
    severity_counts = _llm_severity_counts(llm_result)
    for severity in _MARKDOWN_SEVERITY_ORDER:
        lines.append(f"| {severity} | {severity_counts[severity]} |")
    lines.append("")


def _append_llm_findings_table(
    lines: list[str],
    llm_result: LLMReviewResult,
) -> None:
    lines.extend(["### LLM Findings", ""])

    if not llm_result.findings:
        lines.append("No LLM findings.")
        lines.append("")
        return

    lines.extend(
        [
            "| Severity | Rule | Message | Suggestion |",
            "| --- | --- | --- | --- |",
        ]
    )
    for finding in llm_result.findings:
        lines.append(
            "| "
            f"{finding.severity} | "
            f"{_escape_cell(finding.rule_id)} | "
            f"{_escape_cell(finding.message)} | "
            f"{_escape_cell(finding.suggestion)} |"
        )
    lines.append("")


def _append_llm_finding_detail(
    lines: list[str],
    finding: LLMReviewFinding,
    *,
    index: int,
) -> None:
    lines.extend(
        [
            f"#### LLM Finding {index}",
            "",
            f"- Severity: {finding.severity}",
            f"- Rule: {_format_inline_code(finding.rule_id)}",
            f"- Message: {_escape_cell(finding.message)}",
        ]
    )
    if finding.line is not None:
        location = f"line {finding.line}"
        if finding.column is not None:
            location += f", column {finding.column}"
        if finding.end_line is not None and finding.end_column is not None:
            location += f" to line {finding.end_line}, column {finding.end_column}"
        lines.append(f"- Location: {location}")
    if finding.matched_text is not None:
        lines.append(f"- Matched Text: {_format_inline_code(finding.matched_text)}")
    if finding.category is not None:
        lines.append(f"- Category: {_escape_cell(finding.category)}")
    if finding.rationale is not None:
        lines.append(f"- Rationale: {_escape_cell(finding.rationale)}")
    if finding.confidence is not None:
        lines.append(f"- Confidence: {finding.confidence}")
    if finding.suggestion is not None:
        lines.append(f"- Suggestion: {_escape_cell(finding.suggestion)}")
    lines.append("")


def render_llm_review_markdown_section(llm_result: LLMReviewResult) -> str:
    lines = ["## LLM Review", ""]
    _append_llm_summary(lines, llm_result)
    _append_llm_severity_counts(lines, llm_result)
    _append_llm_findings_table(lines, llm_result)
    if llm_result.findings:
        lines.extend(["### LLM Detailed Findings", ""])
        for index, finding in enumerate(llm_result.findings, start=1):
            _append_llm_finding_detail(lines, finding, index=index)
    return "\n".join(lines).rstrip()


def _quality_gate_rows(
    severity_counts: dict[str, int],
    *,
    threshold: str | None,
) -> list[tuple[str, str]]:
    if threshold is None:
        return [("Quality Gate", "Not configured")]

    matched_count = count_findings_at_or_above(severity_counts, threshold)
    status = "Failed" if quality_gate_failed(severity_counts, threshold) else "Passed"
    return [
        ("Quality Gate", status),
        ("Fail On", f"`{threshold}`"),
        ("Matched Gate Findings", str(matched_count)),
    ]


def render_markdown_report(
    result: ReviewResult,
    *,
    fail_on: str | None = None,
    llm_result: LLMReviewResult | None = None,
) -> str:
    document_label = _format_inline_code(
        result.document.path if result.document is not None else None
    )
    profile_label = (
        "Unknown"
        if result.profile is None
        else _format_inline_code(result.profile.path or result.profile.name)
    )

    summary_rows = [
        ("File", document_label),
        ("Profile", profile_label),
        ("Total Findings", str(result.summary.finding_count)),
        *_quality_gate_rows(result.summary.severity_counts, threshold=fail_on),
    ]

    lines = ["# Content Review Report", ""]
    _append_summary_table(lines, summary_rows)
    _append_severity_counts(lines, result.summary.severity_counts)
    _append_rule_counts(lines, result.findings)
    _append_findings_table(lines, result.findings, heading="## Findings")
    _append_detailed_findings(lines, result.findings, heading="## Detailed Findings")
    if llm_result is not None:
        lines.extend(["", render_llm_review_markdown_section(llm_result)])
    return "\n".join(lines).rstrip()


def render_batch_markdown_report(
    result: BatchReviewResult,
    *,
    fail_on: str | None = None,
) -> str:
    all_findings = [finding for review in result.results for finding in review.findings]
    summary_rows = [
        ("Files Discovered", str(result.summary.file_count)),
        ("Files Reviewed", str(result.summary.reviewed_count)),
        ("Files With Findings", str(result.summary.files_with_findings)),
        ("Total Findings", str(result.summary.finding_count)),
        *_quality_gate_rows(result.summary.severity_counts, threshold=fail_on),
    ]

    lines = ["# Batch Content Review Report", ""]
    _append_summary_table(lines, summary_rows)
    _append_severity_counts(lines, result.summary.severity_counts)
    _append_rule_counts(lines, all_findings)

    lines.extend(
        [
            "## Files With Findings",
            "",
        ]
    )
    if result.summary.files_with_findings == 0:
        lines.append("No findings.")
        lines.append("")
    else:
        lines.extend(
            [
                "| File | Findings | Highest Severity |",
                "| --- | ---: | --- |",
            ]
        )
        for review_result in result.results:
            if review_result.summary.finding_count == 0:
                continue
            document_path = (
                review_result.document.path
                if review_result.document is not None
                else "Unknown"
            )
            lines.append(
                "| "
                f"{_format_inline_code(document_path)} | "
                f"{review_result.summary.finding_count} | "
                f"{_highest_severity(review_result.findings)} |"
            )
        lines.append("")

    lines.extend(["## Findings by File", ""])
    if not result.results:
        lines.append("No Markdown files found.")
        return "\n".join(lines).rstrip()

    if result.summary.finding_count == 0:
        lines.append("No findings.")
        lines.append("")

    for review_result in result.results:
        document_path = (
            review_result.document.path if review_result.document is not None else None
        )
        lines.extend([f"### {_format_inline_code(document_path)}", ""])
        _append_findings_table(lines, review_result.findings, heading="#### Findings")
        _append_detailed_findings(
            lines,
            review_result.findings,
            heading="#### Detailed Findings",
        )

    return "\n".join(lines).rstrip()


__all__ = [
    "REVIEW_SUMMARY_SEVERITIES",
    "render_batch_markdown_report",
    "render_llm_review_markdown_section",
    "render_markdown_report",
]
