from __future__ import annotations

import re
from pathlib import Path

from content_review_engine.core.models import REVIEW_SUMMARY_SEVERITIES, ReviewFinding
from content_review_engine.llm.combined_result import (
    SingleFileCombinedReviewResult,
)
from content_review_engine.llm.manual_review import build_llm_manual_review_items
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


def _format_severity_counts(result: SingleFileCombinedReviewResult) -> str:
    return ", ".join(
        f"{severity}={result.review_result.summary.severity_counts.get(severity, 0)}"
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


def _append_deterministic_findings(
    lines: list[str],
    result: SingleFileCombinedReviewResult,
) -> None:
    lines.extend(["## Deterministic Findings", ""])
    if not result.review_result.findings:
        lines.extend(["No deterministic findings.", ""])
        return

    lines.extend(
        [
            "| Severity | Rule | Line | Column | Message | Suggestion |",
            "| --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for finding in result.review_result.findings:
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


def _append_artifact_boundary(lines: list[str]) -> None:
    _append_bullets(
        lines,
        "## Artifact Boundary",
        [
            "This file is an explicit combined artifact rendered from `SingleFileCombinedReviewResult`.",
            "It preserves deterministic review data and optional LLM review data in one human-readable report, but it does not replace canonical deterministic `--output` or raw `--llm-output` artifacts.",
            "LLM findings remain advisory and presentation-only in this report.",
        ],
    )


def _append_deterministic_summary(
    lines: list[str],
    result: SingleFileCombinedReviewResult,
) -> None:
    document_path = (
        result.review_result.document.path
        if result.review_result.document is not None
        else None
    )
    profile_value = None
    if result.review_result.profile is not None:
        profile_value = (
            result.review_result.profile.path or result.review_result.profile.name
        )

    _append_table(
        lines,
        "## Deterministic Review Summary",
        [
            ("File", _escape_cell(_display_path(document_path))),
            ("Profile", _escape_cell(_display_path(profile_value))),
            (
                "Total Findings",
                str(result.review_result.summary.finding_count),
            ),
            ("Severity Counts", _escape_cell(_format_severity_counts(result))),
            (
                "Rule Counts",
                _escape_cell(_format_rule_counts(result.review_result.findings)),
            ),
            ("Quality Gate Source", "deterministic findings only"),
        ],
    )


def _append_llm_advisory_findings(
    lines: list[str], result: SingleFileCombinedReviewResult
) -> None:
    lines.extend(["## LLM Findings", ""])

    if result.llm_status != "succeeded":
        if result.llm_status == "failed":
            lines.append("LLM review failed. No advisory findings are available in this artifact.")
        elif result.llm_status == "skipped":
            lines.append("LLM review was skipped. No advisory findings are available in this artifact.")
        else:
            lines.append("LLM review was not run. No advisory findings are available in this artifact.")
        lines.append("")
        return

    if not result.llm_finding_candidates:
        lines.append("LLM review succeeded but returned no advisory findings.")
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
            ("Message", _escape_cell(_sanitize_display_text(result.llm_error.message))),
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

    lines.extend(["## Manual Review Checklist", ""])
    if result.llm_status != "succeeded" or result.llm_result is None:
        lines.extend(["No manual review checklist items.", ""])
        return

    checklist_items = build_llm_manual_review_items(result.llm_result)
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


def _append_llm_summary(
    lines: list[str],
    result: SingleFileCombinedReviewResult,
) -> None:
    llm_schema = "-"
    llm_provider = "-"
    llm_model = "-"
    prompt_version = "-"
    profile_name = "-"
    llm_error_value = "-"

    if result.llm_result is not None:
        llm_schema = _escape_cell(result.llm_result.schema_version)
        llm_provider = _escape_cell(result.llm_result.provider)
        llm_model = _escape_cell(result.llm_result.model)
        prompt_version = _escape_cell(result.llm_result.prompt_version)
        profile_name = _escape_cell(result.llm_result.profile_name)

    if result.llm_error is not None:
        llm_error_value = _escape_cell(
            _sanitize_display_text(
                f"{result.llm_error.type}: {result.llm_error.message}"
            )
        )

    _append_table(
        lines,
        "## LLM Review Summary",
        [
            ("Status", result.llm_status),
            ("Schema Version", llm_schema),
            ("Provider", llm_provider),
            ("Model", llm_model),
            ("Prompt Version", prompt_version),
            ("Profile Name", profile_name),
            ("Advisory Findings", str(len(result.llm_finding_candidates))),
            ("Advisory", "yes"),
            ("Quality Gate Participation", "no"),
            ("Policy Note", _escape_cell(render_llm_finding_policy_note())),
            ("LLM Error", llm_error_value),
        ],
    )


def render_single_file_combined_markdown_report(
    result: SingleFileCombinedReviewResult,
) -> str:
    lines = ["# Combined Content Review Report", ""]
    _append_artifact_boundary(lines)
    _append_deterministic_summary(lines, result)
    _append_deterministic_findings(lines, result)
    _append_llm_summary(lines, result)
    _append_llm_advisory_findings(lines, result)
    _append_llm_error(lines, result)
    _append_manual_review_workflow(lines, result)
    _append_bullets(
        lines,
        "## Quality Gate Behavior",
        [
            "Quality gate evaluation remains deterministic-only.",
            "LLM advisory findings do not participate in severity counts, rule counts, fail-on, quality gate, or exit code.",
            "Only deterministic findings can affect `--fail-on`, quality gate, or CLI exit code.",
        ],
    )
    _append_bullets(
        lines,
        "## Artifact Notes",
        [
            "`--output`, `--llm-output`, and `--combined-output` can coexist in the same run.",
            "Use deterministic `--output` as the canonical automation artifact and raw `--llm-output` as the canonical machine-readable LLM artifact.",
            "This combined Markdown report is a presentation artifact derived from the combined envelope and does not replace either JSON contract.",
        ],
    )
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["render_single_file_combined_markdown_report"]
