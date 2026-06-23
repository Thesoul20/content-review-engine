from __future__ import annotations

from pathlib import Path
from typing import Sequence

from content_review_engine.core.models import ReviewFinding


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
    findings: Sequence[ReviewFinding],
    *,
    document_path: str | Path | None = None,
    profile_name: str | None = None,
    profile_path: str | Path | None = None,
) -> str:
    document_label = _format_value(str(document_path) if document_path is not None else None)
    profile_label = _format_value(str(profile_path) if profile_path is not None else profile_name)

    lines = [
        "# Content Review Report",
        "",
        "## Summary",
        "",
        f"- Document: {document_label}",
        f"- Profile: {profile_label}",
        f"- Findings: {len(findings)}",
        "",
        "## Findings",
        "",
    ]

    if not findings:
        lines.append("No issues found.")
        return "\n".join(lines)

    for index, finding in enumerate(findings, start=1):
        lines.extend(_render_finding_details(finding))
        if index < len(findings):
            lines.append("")

    return "\n".join(lines)
