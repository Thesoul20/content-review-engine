from __future__ import annotations

from content_review_engine.core.models import ReviewFinding, SourceSpan
from content_review_engine.core.suppression import (
    filter_suppressed_findings,
    parse_inline_suppressions,
)


def _finding(*, rule_id: str = "forbidden_terms", line: int = 1) -> ReviewFinding:
    return ReviewFinding(
        rule_id=rule_id,
        severity="warning",
        message="finding",
        matched_term="全网最强",
        matched_text="全网最强",
        location=SourceSpan(
            start_line=line,
            start_column=1,
            end_line=line,
            end_column=5,
            start_offset=0,
            end_offset=4,
            matched_text="全网最强",
        ),
    )


def test_disable_line_suppresses_finding_on_same_line() -> None:
    markdown = "This line has 全网最强. <!-- content-review-disable-line forbidden_terms -->"
    directives = parse_inline_suppressions(markdown)

    assert filter_suppressed_findings([_finding(line=1)], directives) == []


def test_disable_next_line_suppresses_finding_on_next_line() -> None:
    markdown = "\n".join(
        [
            "<!-- content-review-disable-next-line forbidden_terms -->",
            "This line has 全网最强.",
        ]
    )
    directives = parse_inline_suppressions(markdown)

    assert filter_suppressed_findings([_finding(line=2)], directives) == []


def test_disable_line_does_not_suppress_other_lines() -> None:
    markdown = "line 1 <!-- content-review-disable-line forbidden_terms -->\nline 2"
    finding = _finding(line=2)

    active_findings = filter_suppressed_findings(
        [finding],
        parse_inline_suppressions(markdown),
    )

    assert active_findings == [finding]


def test_disable_next_line_does_not_suppress_two_lines_later() -> None:
    markdown = "\n".join(
        [
            "<!-- content-review-disable-next-line forbidden_terms -->",
            "line 2",
            "line 3",
        ]
    )
    finding = _finding(line=3)

    active_findings = filter_suppressed_findings(
        [finding],
        parse_inline_suppressions(markdown),
    )

    assert active_findings == [finding]


def test_suppression_for_other_rule_id_does_not_suppress_forbidden_terms() -> None:
    markdown = "line 1 <!-- content-review-disable-line markdown_structure -->"
    finding = _finding(rule_id="forbidden_terms", line=1)

    active_findings = filter_suppressed_findings(
        [finding],
        parse_inline_suppressions(markdown),
    )

    assert active_findings == [finding]


def test_optional_whitespace_in_suppression_comment_is_tolerated() -> None:
    markdown = "line 1 <!--  content-review-disable-line forbidden_terms  -->"
    directives = parse_inline_suppressions(markdown)

    assert filter_suppressed_findings([_finding(line=1)], directives) == []


def test_compact_suppression_comment_is_tolerated() -> None:
    markdown = "line 1 <!--content-review-disable-line forbidden_terms-->"
    directives = parse_inline_suppressions(markdown)

    assert filter_suppressed_findings([_finding(line=1)], directives) == []


def test_multiple_rule_ids_are_supported() -> None:
    markdown = "line 1 <!-- content-review-disable-line other_rule forbidden_terms -->"
    directives = parse_inline_suppressions(markdown)

    assert filter_suppressed_findings([_finding(line=1)], directives) == []


def test_absolute_claims_suppression_matches_by_rule_id() -> None:
    markdown = "line 1 <!-- content-review-disable-line absolute_claims -->"
    finding = _finding(rule_id="absolute_claims", line=1)

    assert filter_suppressed_findings([finding], parse_inline_suppressions(markdown)) == []
