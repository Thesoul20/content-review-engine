from __future__ import annotations

from content_review_engine.core.models import BatchReviewResult, REVIEW_SUMMARY_SEVERITIES, ReviewResult
from content_review_engine.llm.models import LLMSidecarFile, LLMSidecarResult, LLMReviewResult


def _escape_cell(value: str | None) -> str:
    if value is None or value == "":
        return "-"
    return value.replace("|", "\\|").replace("\n", "<br>")


def _append_table(lines: list[str], heading: str, rows: list[tuple[str, str]]) -> None:
    lines.extend([heading, "", "| Field | Value |", "| --- | --- |"])
    for label, value in rows:
        lines.append(f"| {label} | {value} |")
    lines.append("")


def _append_output_files_table(
    lines: list[str],
    rows: list[tuple[str, str, str, str, str]],
) -> None:
    lines.extend(
        [
            "## Output Files",
            "",
            "| Output | Path | Format | Purpose | Canonical |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for output_name, path, output_format, purpose, canonical in rows:
        lines.append(
            "| "
            f"{output_name} | "
            f"{_escape_cell(path)} | "
            f"{_escape_cell(output_format)} | "
            f"{_escape_cell(purpose)} | "
            f"{_escape_cell(canonical)} |"
        )
    lines.append("")


def _append_bullets(lines: list[str], heading: str, items: list[str]) -> None:
    lines.extend([heading, ""])
    for item in items:
        lines.append(f"- {item}")
    lines.append("")


def _format_output_path(path: str | None) -> str:
    if path is None:
        return "stdout (not written to file)"
    return path


def _deterministic_output_purpose(output_format: str) -> tuple[str, str]:
    if output_format == "json":
        return ("Canonical machine-readable deterministic review result", "yes")
    if output_format == "markdown":
        return ("Human-readable deterministic review report", "no")
    return ("Human-readable deterministic review summary", "no")


def _build_single_file_output_rows(
    *,
    deterministic_output_path: str | None,
    deterministic_output_format: str,
    llm_enabled: bool,
    llm_output_path: str | None,
    llm_report_path: str | None,
    report_index_path: str,
) -> list[tuple[str, str, str, str, str]]:
    deterministic_purpose, deterministic_canonical = _deterministic_output_purpose(
        deterministic_output_format
    )
    rows = [
        (
            "Deterministic Output",
            _format_output_path(deterministic_output_path),
            deterministic_output_format,
            deterministic_purpose,
            deterministic_canonical,
        ),
    ]
    if llm_enabled:
        rows.append(
            (
                "LLM JSON Sidecar",
                _format_output_path(llm_output_path),
                "json" if llm_output_path is not None else "-",
                "Machine-readable LLM semantic review result",
                "yes, for LLM layer" if llm_output_path is not None else "not written",
            )
        )
        rows.append(
            (
                "LLM Markdown Report",
                _format_output_path(llm_report_path),
                "markdown" if llm_report_path is not None else "-",
                "Human-readable LLM semantic review report",
                "no" if llm_report_path is not None else "not written",
            )
        )
    rows.append(
        (
            "Report Index",
            report_index_path,
            "markdown",
            "Navigation and interpretation guide across deterministic and LLM outputs",
            "no",
        )
    )
    return rows


def _append_deterministic_summary(lines: list[str], result: ReviewResult) -> None:
    rows = [("Total Findings", str(result.summary.finding_count))]
    for severity in REVIEW_SUMMARY_SEVERITIES:
        rows.append((f"{severity.title()} Findings", str(result.summary.severity_counts[severity])))
    _append_table(lines, "## Deterministic Review Summary", rows)


def _append_single_file_llm_summary(
    lines: list[str],
    *,
    llm_enabled: bool,
    llm_result: LLMReviewResult | None,
) -> None:
    if not llm_enabled:
        _append_table(
            lines,
            "## LLM Review Summary",
            [("Status", "LLM not enabled")],
        )
        return

    if llm_result is None:
        _append_table(
            lines,
            "## LLM Review Summary",
            [("Status", "LLM enabled, result unavailable")],
        )
        return

    rows = [
        ("Status", "completed"),
        ("Schema Version", _escape_cell(llm_result.schema_version)),
        ("Provider", _escape_cell(llm_result.provider)),
        ("Model", _escape_cell(llm_result.model)),
        ("Total Findings", str(len(llm_result.findings))),
    ]
    if llm_result.summary is not None:
        rows.extend(
            [
                ("Overall Risk", _escape_cell(llm_result.summary.overall_risk)),
                ("Summary", _escape_cell(llm_result.summary.summary)),
                (
                    "Recommended Action",
                    _escape_cell(llm_result.summary.recommended_action),
                ),
            ]
        )
    _append_table(lines, "## LLM Review Summary", rows)


def render_single_file_report_index(
    result: ReviewResult,
    *,
    deterministic_output_path: str | None,
    deterministic_output_format: str,
    report_index_path: str,
    llm_enabled: bool,
    llm_result: LLMReviewResult | None = None,
    llm_output_path: str | None = None,
    llm_report_path: str | None = None,
) -> str:
    document_path = result.document.path if result.document is not None else "-"
    profile_path = (
        result.profile.path if result.profile is not None and result.profile.path is not None else "-"
    )
    profile_name = result.profile.name if result.profile is not None else "-"

    llm_status_value = "enabled" if llm_enabled else "LLM not enabled"
    llm_findings_value = (
        str(len(llm_result.findings))
        if llm_result is not None
        else ("LLM not enabled" if not llm_enabled else "result unavailable")
    )

    lines = ["# Review Output Index", ""]
    _append_table(
        lines,
        "## Summary",
        [
            ("Mode", "single-file"),
            ("File", _escape_cell(document_path)),
            ("Profile", _escape_cell(profile_path)),
            ("Profile Name", _escape_cell(profile_name)),
            ("Deterministic Review", "completed"),
            ("LLM Review", llm_status_value),
            ("Deterministic Findings", str(result.summary.finding_count)),
            ("LLM Findings", llm_findings_value),
            ("Quality Gate Source", "deterministic review only"),
        ],
    )
    _append_output_files_table(
        lines,
        _build_single_file_output_rows(
            deterministic_output_path=deterministic_output_path,
            deterministic_output_format=deterministic_output_format,
            llm_enabled=llm_enabled,
            llm_output_path=llm_output_path,
            llm_report_path=llm_report_path,
            report_index_path=report_index_path,
        ),
    )
    _append_bullets(
        lines,
        "## Interpretation",
        [
            "Deterministic review is the stable review layer and the only quality-gate source.",
            "LLM review is advisory semantic analysis and does not change deterministic findings.",
            "LLM findings do not participate in fail-on or quality-gate decisions.",
            "Use deterministic output for compliance checks and CI gating.",
            "Use LLM output for semantic review suggestions and follow-up inspection.",
        ],
    )
    _append_deterministic_summary(lines, result)
    _append_single_file_llm_summary(lines, llm_enabled=llm_enabled, llm_result=llm_result)
    return "\n".join(lines).rstrip()


def _append_batch_deterministic_summary(lines: list[str], result: BatchReviewResult) -> None:
    rows = [
        ("Files Discovered", str(result.summary.file_count)),
        ("Files Reviewed", str(result.summary.reviewed_count)),
        ("Files With Findings", str(result.summary.files_with_findings)),
        ("Total Findings", str(result.summary.finding_count)),
    ]
    for severity in REVIEW_SUMMARY_SEVERITIES:
        rows.append((f"{severity.title()} Findings", str(result.summary.severity_counts[severity])))
    _append_table(lines, "## Deterministic Review Summary", rows)


def _append_batch_llm_summary(
    lines: list[str],
    *,
    llm_enabled: bool,
    llm_result: LLMSidecarResult | None,
) -> None:
    if not llm_enabled:
        _append_table(
            lines,
            "## LLM Review Summary",
            [("Status", "LLM not enabled")],
        )
        return

    if llm_result is None:
        _append_table(
            lines,
            "## LLM Review Summary",
            [("Status", "LLM enabled, result unavailable")],
        )
        return

    files_with_findings = sum(
        1
        for item in llm_result.files
        if item.status == "success" and item.finding_count > 0
    )
    rows = [
        ("Status", "completed"),
        ("Schema Version", _escape_cell(llm_result.schema_version)),
        ("Provider", _escape_cell(llm_result.llm_provider)),
        ("Provider Source", _escape_cell(llm_result.llm_provider_source)),
        ("Files Reviewed", str(llm_result.summary.file_count)),
        ("Files With LLM Findings", str(files_with_findings)),
        ("Files With LLM Errors", str(llm_result.summary.failed_count)),
        ("Total LLM Findings", str(llm_result.summary.finding_count)),
    ]
    _append_table(lines, "## LLM Review Summary", rows)


def _format_llm_file_error(item: LLMSidecarFile) -> str:
    if item.error is None:
        return "-"
    return _escape_cell(f"{item.error.error_type}: {item.error.message}")


def _append_batch_llm_file_status_summary(
    lines: list[str],
    *,
    llm_enabled: bool,
    llm_result: LLMSidecarResult | None,
) -> None:
    lines.extend(
        [
            "## LLM File Status Summary",
            "",
            "| File | Status | Findings | Error |",
            "| --- | --- | ---: | --- |",
        ]
    )
    if not llm_enabled:
        lines.extend(["| - | LLM not enabled | - | - |", ""])
        return
    if llm_result is None:
        lines.extend(["| - | result unavailable | - | - |", ""])
        return
    if not llm_result.files:
        lines.extend(["| - | - | 0 | - |", ""])
        return
    for item in llm_result.files:
        lines.append(
            "| "
            f"{_escape_cell(item.path)} | "
            f"{item.status} | "
            f"{item.finding_count} | "
            f"{_format_llm_file_error(item)} |"
        )
    lines.append("")


def _append_batch_llm_error_summary(
    lines: list[str],
    *,
    llm_enabled: bool,
    llm_result: LLMSidecarResult | None,
) -> None:
    if not llm_enabled or llm_result is None or llm_result.summary.failed_count == 0:
        return
    error_rows = [
        (item.path, f"{item.error.error_type}: {item.error.message}")
        for item in llm_result.files
        if item.error is not None
    ]
    lines.extend(["## LLM Error Summary", "", "| File | Error |", "| --- | --- |"])
    for file_path, error_value in error_rows:
        lines.append(f"| {_escape_cell(file_path)} | {_escape_cell(error_value)} |")
    lines.append("")


def _build_batch_output_rows(
    *,
    deterministic_output_path: str | None,
    deterministic_output_format: str,
    llm_enabled: bool,
    llm_output_path: str | None,
    llm_report_path: str | None,
    report_index_path: str,
) -> list[tuple[str, str, str, str, str]]:
    deterministic_purpose, deterministic_canonical = _deterministic_output_purpose(
        deterministic_output_format
    )
    rows = [
        (
            "Deterministic Output",
            _format_output_path(deterministic_output_path),
            deterministic_output_format,
            deterministic_purpose,
            deterministic_canonical,
        ),
    ]
    if llm_enabled:
        rows.append(
            (
                "LLM JSON Sidecar",
                _format_output_path(llm_output_path),
                "json" if llm_output_path is not None else "-",
                "Machine-readable aggregate LLM semantic review result",
                "yes, for LLM layer" if llm_output_path is not None else "not written",
            )
        )
        rows.append(
            (
                "LLM Markdown Report",
                _format_output_path(llm_report_path),
                "markdown" if llm_report_path is not None else "-",
                "Human-readable aggregate LLM semantic review report",
                "no" if llm_report_path is not None else "not written",
            )
        )
    rows.append(
        (
            "Report Index",
            report_index_path,
            "markdown",
            "Navigation and interpretation guide across batch deterministic and LLM outputs",
            "no",
        )
    )
    return rows


def render_batch_report_index(
    result: BatchReviewResult,
    *,
    input_dir: str,
    profile_path: str,
    deterministic_output_path: str | None,
    deterministic_output_format: str,
    report_index_path: str,
    llm_enabled: bool,
    llm_result: LLMSidecarResult | None = None,
    llm_output_path: str | None = None,
    llm_report_path: str | None = None,
) -> str:
    llm_status_value = "enabled" if llm_enabled else "LLM not enabled"
    llm_findings_value = (
        str(llm_result.summary.finding_count)
        if llm_result is not None
        else ("LLM not enabled" if not llm_enabled else "result unavailable")
    )

    lines = ["# Review Output Index", ""]
    _append_table(
        lines,
        "## Summary",
        [
            ("Mode", "batch"),
            ("Input Directory", _escape_cell(input_dir)),
            ("Profile", _escape_cell(profile_path)),
            ("Deterministic Review", "completed"),
            ("LLM Review", llm_status_value),
            ("Files Reviewed", str(result.summary.reviewed_count)),
            ("Deterministic Findings", str(result.summary.finding_count)),
            ("LLM Findings", llm_findings_value),
            ("Quality Gate Source", "deterministic review only"),
        ],
    )
    _append_output_files_table(
        lines,
        _build_batch_output_rows(
            deterministic_output_path=deterministic_output_path,
            deterministic_output_format=deterministic_output_format,
            llm_enabled=llm_enabled,
            llm_output_path=llm_output_path,
            llm_report_path=llm_report_path,
            report_index_path=report_index_path,
        ),
    )
    _append_bullets(
        lines,
        "## Interpretation",
        [
            "Deterministic batch review is the stable review layer and the only quality-gate source.",
            "Batch LLM review is advisory semantic analysis and remains separate from deterministic findings.",
            "LLM partial failures do not rewrite deterministic results, but they should be inspected before trusting LLM coverage.",
            "Use deterministic output for CI gating and rule-based compliance checks.",
            "Use LLM output for semantic suggestions and per-file follow-up review.",
        ],
    )
    _append_batch_deterministic_summary(lines, result)
    _append_batch_llm_summary(lines, llm_enabled=llm_enabled, llm_result=llm_result)
    _append_batch_llm_file_status_summary(lines, llm_enabled=llm_enabled, llm_result=llm_result)
    _append_batch_llm_error_summary(lines, llm_enabled=llm_enabled, llm_result=llm_result)
    return "\n".join(lines).rstrip()


__all__ = [
    "render_batch_report_index",
    "render_single_file_report_index",
]
