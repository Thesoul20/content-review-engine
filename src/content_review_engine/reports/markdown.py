from __future__ import annotations

from content_review_engine.core.models import ReviewFinding, ReviewResult


def _format_value(value: str | None) -> str:
    if value is None or value == "":
        return "Unknown"
    return f"`{value}`"


def _render_finding_details(finding: ReviewFinding) -> list[str]:
    lines = [
        f"### {finding.rule_id}",
        "",
        f"- Severity: {finding.severity}",
        f"- Message: {finding.message}",
    ]

    location = finding.location
    matched_text = finding.matched_text
    if location is None:
        lines.append("- Location: unavailable")
    else:
        lines.extend(
            [
                f"- Line: {location.start_line}",
                f"- Column: {location.start_column}",
            ]
        )
        matched_text = location.matched_text
        if location.context is not None:
            lines.append(f"- Context: {location.context}")

    if matched_text is not None and matched_text != "":
        lines.append(f"- Matched: `{matched_text}`")

    suggestion = getattr(finding, "suggestion", None)
    if suggestion:
        lines.append(f"- Suggestion: {suggestion}")

    return lines


def render_markdown_report(
    result: ReviewResult,
) -> str:
    document_label = _format_value(
        result.document.path if result.document is not None else None
    )
    if result.profile is None:
        profile_label = "Unknown"
    else:
        profile_label = _format_value(result.profile.path or result.profile.name)

    lines = [
        "# Content Review Report",
        "",
        "## Summary",
        "",
        f"- Document: {document_label}",
        f"- Profile: {profile_label}",
        f"- Findings: {result.summary.finding_count}",
        "",
        "## Findings",
        "",
    ]

    if not result.findings:
        lines.append("No issues found.")
        return "\n".join(lines)

    for index, finding in enumerate(result.findings, start=1):
        lines.extend(_render_finding_details(finding))
        if index < len(result.findings):
            lines.append("")

    return "\n".join(lines)
