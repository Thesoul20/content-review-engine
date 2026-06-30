from __future__ import annotations

from content_review_engine.llm.combined_result import (
    SingleFileCombinedReviewResult,
)
from content_review_engine.llm.manual_review import build_llm_manual_review_items
from content_review_engine.llm.policy import (
    format_llm_confidence_like_value,
    render_llm_finding_policy_note,
)
from content_review_engine.reports.markdown import render_markdown_report


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


def _append_llm_advisory_findings(
    lines: list[str], result: SingleFileCombinedReviewResult
) -> None:
    lines.extend(["## LLM Advisory Findings", ""])

    if result.llm_status != "succeeded":
        lines.append("No LLM advisory findings.")
        lines.append("")
        return

    if not result.llm_finding_candidates:
        lines.append("No LLM advisory findings.")
        lines.append("")
        return

    lines.extend(
        [
            "| Severity | Rule | Source | Advisory | Quality Gate | Confidence | Location | Message | Suggestion |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for candidate in result.llm_finding_candidates:
        location = "-"
        if candidate.line is not None:
            location = str(candidate.line)
            if candidate.column is not None:
                location = f"{location}:{candidate.column}"

        confidence = "not provided"
        if result.llm_result is not None and candidate.original_index is not None:
            confidence = format_llm_confidence_like_value(
                result.llm_result.findings[candidate.original_index]
            )

        lines.append(
            "| "
            f"{candidate.severity} | "
            f"{_escape_cell(candidate.rule_id)} | "
            f"{_escape_cell(candidate.source)} | "
            f"{'yes' if candidate.advisory else 'no'} | "
            f"no | "
            f"{_escape_cell(confidence)} | "
            f"{_escape_cell(location)} | "
            f"{_escape_cell(candidate.message)} | "
            f"{_escape_cell(candidate.suggestion)} |"
        )
    lines.append("")


def _append_llm_error(
    lines: list[str], result: SingleFileCombinedReviewResult
) -> None:
    if result.llm_status != "failed" or result.llm_error is None:
        return

    _append_table(
        lines,
        "## LLM Error",
        [
            ("Type", _escape_cell(result.llm_error.type)),
            ("Message", _escape_cell(result.llm_error.message)),
            ("Provider", _escape_cell(result.llm_error.provider)),
            (
                "Retryable",
                "-" if result.llm_error.retryable is None else str(result.llm_error.retryable).lower(),
            ),
        ],
    )


def _append_manual_review_workflow(
    lines: list[str], result: SingleFileCombinedReviewResult
) -> None:
    items = [
        "Review deterministic findings first; they remain the canonical review output and the only quality-gate source.",
        "Treat LLM findings as advisory semantic suggestions that require human confirmation before any content change.",
        "Manual review checklist state is presentation-only and is not persisted into ReviewResult, sidecar JSON, or any review-state file.",
    ]
    if result.llm_status == "failed":
        items.append(
            "Because the LLM review failed, inspect the structured error, decide whether a rerun is warranted, and continue using deterministic findings as the review baseline."
        )
    elif result.llm_status in {"not_run", "skipped"}:
        items.append(
            "No LLM findings are available in this run, so semantic follow-up remains a manual decision outside the deterministic quality gate."
        )
    elif not result.llm_finding_candidates:
        items.append(
            "The LLM review succeeded but returned no advisory findings; if semantic risk still matters, perform manual spot-checking."
        )
    else:
        items.append(
            f"Current advisory checklist items: {len(build_llm_manual_review_items(result.llm_result)) if result.llm_result is not None else 0}."
        )
    _append_bullets(lines, "## Manual Review Workflow", items)

    if result.llm_status != "succeeded" or result.llm_result is None:
        return

    checklist_items = build_llm_manual_review_items(result.llm_result)
    lines.extend(["## Manual Review Checklist", ""])
    if not checklist_items:
        lines.extend(["No manual review checklist items.", ""])
        return

    lines.extend(
        [
            "| ID | Priority | Status | Decision | Quality Gate | Rule | Location | Message | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in checklist_items:
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


def render_single_file_combined_markdown_report(
    result: SingleFileCombinedReviewResult,
) -> str:
    deterministic_report = render_markdown_report(result.review_result)
    document_path = (
        result.review_result.document.path
        if result.review_result.document is not None
        else "-"
    )
    profile_value = "-"
    if result.review_result.profile is not None:
        profile_value = (
            result.review_result.profile.path
            or result.review_result.profile.name
            or "-"
        )

    llm_error_value = "none"
    if result.llm_error is not None:
        llm_error_value = _escape_cell(
            f"{result.llm_error.type}: {result.llm_error.message}"
        )

    lines = ["# Combined Content Review Report", ""]
    _append_table(
        lines,
        "## Summary",
        [
            ("File", _escape_cell(document_path)),
            ("Profile", _escape_cell(profile_value)),
            (
                "Deterministic Findings",
                str(result.review_result.summary.finding_count),
            ),
            ("LLM Status", result.llm_status),
            ("LLM Advisory Findings", str(len(result.llm_finding_candidates))),
            ("LLM Advisory Policy", "yes"),
            ("Quality Gate Scope", "deterministic-only"),
            ("LLM Error", llm_error_value),
        ],
    )
    _append_table(
        lines,
        "## LLM Execution",
        [
            ("Status", result.llm_status),
            ("Advisory", "yes"),
            ("Quality Gate Participation", "no"),
            ("Policy Note", _escape_cell(render_llm_finding_policy_note())),
        ],
    )
    _append_llm_advisory_findings(lines, result)
    _append_llm_error(lines, result)
    _append_manual_review_workflow(lines, result)
    _append_bullets(
        lines,
        "## Quality Gate Boundary",
        [
            "Quality gate evaluation remains deterministic-only.",
            "LLM advisory findings do not participate in severity counts, rule counts, fail-on, quality gate, or exit code.",
            "Use the deterministic report below as the canonical audit record for automation and compliance checks.",
        ],
    )
    lines.extend(["## Deterministic Review", "", deterministic_report, ""])
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["render_single_file_combined_markdown_report"]
