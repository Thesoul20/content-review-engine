from __future__ import annotations

from content_review_engine.core.models import REVIEW_SUMMARY_SEVERITIES

SEVERITY_ORDER: tuple[str, ...] = REVIEW_SUMMARY_SEVERITIES
_SEVERITY_RANKS = {
    severity: rank for rank, severity in enumerate(SEVERITY_ORDER)
}


def allowed_severities_text() -> str:
    return ", ".join(SEVERITY_ORDER)


def severity_rank(severity: str) -> int:
    """Return the numeric rank for a canonical severity value."""
    try:
        return _SEVERITY_RANKS[severity]
    except KeyError as exc:
        raise ValueError(
            f"Invalid severity: {severity!r}. Expected one of: {allowed_severities_text()}."
        ) from exc


def severity_meets_threshold(severity: str, threshold: str) -> bool:
    """Return whether severity is greater than or equal to threshold."""
    return severity_rank(severity) >= severity_rank(threshold)


def count_findings_at_or_above(
    severity_counts: dict[str, int],
    threshold: str,
) -> int:
    """Count findings whose severity meets or exceeds threshold."""
    severity_rank(threshold)
    total = 0
    for severity, count in severity_counts.items():
        if severity_meets_threshold(severity, threshold):
            total += count
    return total


def quality_gate_failed(
    severity_counts: dict[str, int],
    threshold: str | None,
) -> bool:
    """Return whether the configured quality gate should fail."""
    if threshold is None:
        return False
    return count_findings_at_or_above(severity_counts, threshold) > 0


__all__ = [
    "SEVERITY_ORDER",
    "allowed_severities_text",
    "count_findings_at_or_above",
    "quality_gate_failed",
    "severity_meets_threshold",
    "severity_rank",
]
