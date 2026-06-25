from __future__ import annotations

import pytest

from content_review_engine.core.quality_gate import (
    count_findings_at_or_above,
    quality_gate_failed,
    severity_meets_threshold,
    severity_rank,
)


@pytest.mark.parametrize(
    ("severity", "threshold", "expected"),
    [
        ("info", "warning", False),
        ("warning", "warning", True),
        ("error", "warning", True),
        ("critical", "error", True),
        ("warning", "error", False),
        ("critical", "critical", True),
        ("info", "info", True),
    ],
)
def test_severity_meets_threshold_uses_canonical_ordering(
    severity: str,
    threshold: str,
    expected: bool,
) -> None:
    assert severity_meets_threshold(severity, threshold) is expected


def test_severity_rank_rejects_unknown_values() -> None:
    with pytest.raises(ValueError, match="Invalid severity: 'high'"):
        severity_rank("high")


def test_count_findings_at_or_above_counts_matching_severities() -> None:
    severity_counts = {
        "info": 2,
        "warning": 3,
        "error": 5,
        "critical": 7,
    }

    assert count_findings_at_or_above(severity_counts, "error") == 12


def test_quality_gate_failed_uses_threshold_when_configured() -> None:
    severity_counts = {
        "info": 0,
        "warning": 2,
        "error": 0,
        "critical": 0,
    }

    assert quality_gate_failed(severity_counts, None) is False
    assert quality_gate_failed(severity_counts, "error") is False
    assert quality_gate_failed(severity_counts, "warning") is True
