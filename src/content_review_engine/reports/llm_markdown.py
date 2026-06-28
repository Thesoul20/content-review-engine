from __future__ import annotations

from content_review_engine.llm.models import LLMSidecarFile, LLMSidecarResult, LLMReviewFinding


def _escape_cell(value: str | None) -> str:
    if value is None or value == "":
        return "-"
    return value.replace("|", "\\|").replace("\n", "<br>")


def _format_inline_code(value: str | None) -> str:
    if value is None or value == "":
        return "`-`"
    return f"`{value}`"


def _format_error(file: LLMSidecarFile) -> str:
    if file.error is None:
        return "-"
    return _escape_cell(f"{file.error.error_type}: {file.error.message}")


def _append_summary(lines: list[str], result: LLMSidecarResult) -> None:
    summary = result.summary
    lines.extend(
        [
            "## Summary",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Files | {summary.file_count} |",
            f"| Succeeded | {summary.succeeded_count} |",
            f"| Failed | {summary.failed_count} |",
            f"| Skipped | {summary.skipped_count} |",
            f"| Findings | {summary.finding_count} |",
            "",
        ]
    )


def _append_file_status(lines: list[str], result: LLMSidecarResult) -> None:
    lines.extend(
        [
            "## File Status",
            "",
            "| File | Status | Findings | Error |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for file in result.files:
        lines.append(
            "| "
            f"{_escape_cell(file.path)} | "
            f"{file.status} | "
            f"{file.finding_count} | "
            f"{_format_error(file)} |"
        )
    if not result.files:
        lines.append("| - | - | 0 | - |")
    lines.append("")


def _append_review_summary(lines: list[str], file: LLMSidecarFile) -> None:
    review = file.review
    if review is None or review.summary is None:
        return

    summary = review.summary
    lines.extend(
        [
            "#### Review Summary",
            "",
            f"- Overall Risk: {_escape_cell(summary.overall_risk)}",
            f"- Summary: {_escape_cell(summary.summary)}",
            f"- Recommended Action: {_escape_cell(summary.recommended_action)}",
        ]
    )
    if summary.confidence is not None:
        lines.append(f"- Confidence: {summary.confidence}")
    lines.append("")


def _append_review_metadata(lines: list[str], file: LLMSidecarFile) -> None:
    review = file.review
    if review is None:
        return

    lines.extend(
        [
            "#### Review Metadata",
            "",
            f"- Schema Version: {_escape_cell(review.schema_version)}",
            f"- Provider: {_escape_cell(review.provider)}",
            f"- Model: {_escape_cell(review.model)}",
            f"- Prompt Version: {_escape_cell(review.prompt_version)}",
            f"- Profile Name: {_escape_cell(review.profile_name)}",
            "",
        ]
    )


def _append_finding_detail(
    lines: list[str],
    finding: LLMReviewFinding,
    *,
    index: int,
) -> None:
    lines.extend(
        [
            f"#### Finding {index}",
            "",
            f"- Severity: {finding.severity}",
            f"- Rule: {_format_inline_code(finding.rule_id)}",
            f"- Message: {_escape_cell(finding.message)}",
        ]
    )
    if finding.suggestion is not None:
        lines.append(f"- Suggestion: {_escape_cell(finding.suggestion)}")
    if finding.rationale is not None:
        lines.append(f"- Rationale: {_escape_cell(finding.rationale)}")
    if finding.category is not None:
        lines.append(f"- Category: {_escape_cell(finding.category)}")
    if finding.confidence is not None:
        lines.append(f"- Confidence: {finding.confidence}")
    if finding.matched_text is not None:
        lines.append(f"- Matched Text: {_format_inline_code(finding.matched_text)}")
    if finding.line is not None:
        location = f"line {finding.line}"
        if finding.column is not None:
            location += f", column {finding.column}"
        if finding.end_line is not None and finding.end_column is not None:
            location += f" to line {finding.end_line}, column {finding.end_column}"
        lines.append(f"- Location: {location}")
    lines.append("")


def _append_success_file(lines: list[str], file: LLMSidecarFile) -> None:
    _append_review_metadata(lines, file)
    _append_review_summary(lines, file)

    review = file.review
    if review is None or not review.findings:
        lines.extend(["No LLM findings.", ""])
        return

    for index, finding in enumerate(review.findings, start=1):
        _append_finding_detail(lines, finding, index=index)


def _append_failed_file(lines: list[str], file: LLMSidecarFile) -> None:
    lines.extend(["LLM review failed.", ""])
    if file.error is not None:
        lines.extend(
            [
                f"- Error Type: {_format_inline_code(file.error.error_type)}",
                f"- Message: {_escape_cell(file.error.message)}",
                "",
            ]
        )


def _append_skipped_file(lines: list[str], file: LLMSidecarFile) -> None:
    lines.extend(["LLM review skipped.", ""])
    if file.error is not None:
        lines.extend(
            [
                f"- Error Type: {_format_inline_code(file.error.error_type)}",
                f"- Message: {_escape_cell(file.error.message)}",
                "",
            ]
        )


def render_llm_sidecar_markdown_report(result: LLMSidecarResult) -> str:
    title = (
        "# LLM Sidecar Review Report"
        if result.summary.file_count == 1
        else "# Batch LLM Sidecar Review Report"
    )
    lines = [title, ""]
    _append_summary(lines, result)
    _append_file_status(lines, result)
    lines.extend(["## Findings by File", ""])

    if not result.files:
        lines.extend(["No files.", ""])
        return "\n".join(lines).rstrip()

    for file in result.files:
        lines.extend([f"### {_format_inline_code(file.path)}", ""])
        if file.status == "failed":
            _append_failed_file(lines, file)
            continue
        if file.status == "skipped":
            _append_skipped_file(lines, file)
            continue
        _append_success_file(lines, file)

    return "\n".join(lines).rstrip()


__all__ = ["render_llm_sidecar_markdown_report"]
