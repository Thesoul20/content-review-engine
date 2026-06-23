from __future__ import annotations

from pathlib import Path

from content_review_engine.core.models import ReviewProfile
from content_review_engine.rules import check_markdown_structure

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "markdown"


def _profile() -> ReviewProfile:
    return ReviewProfile(
        name="markdown-structure",
        target_platform="wechat",
        max_paragraph_length=80,
        forbidden_terms=[],
    )


def test_markdown_structure_missing_h1_returns_finding() -> None:
    markdown_text = (FIXTURES_DIR / "markdown_structure_missing_h1.md").read_text(
        encoding="utf-8"
    )

    findings = check_markdown_structure(markdown_text, _profile())

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "markdown_structure"
    assert finding.severity == "warning"
    assert finding.message == "Missing top-level H1 heading."
    assert finding.location is None


def test_markdown_structure_multiple_h1_returns_extra_heading_finding() -> None:
    markdown_text = (FIXTURES_DIR / "markdown_structure_multiple_h1.md").read_text(
        encoding="utf-8"
    )

    findings = check_markdown_structure(markdown_text, _profile())

    assert [finding.rule_id for finding in findings] == ["markdown_structure"]
    assert [finding.message for finding in findings] == [
        "Multiple H1 headings detected.",
    ]
    assert findings[0].location is not None
    assert findings[0].location.start_line == 5
    assert findings[0].location.start_column == 1


def test_markdown_structure_heading_jump_returns_finding() -> None:
    markdown_text = (FIXTURES_DIR / "markdown_structure_heading_jumps.md").read_text(
        encoding="utf-8"
    )

    findings = check_markdown_structure(markdown_text, _profile())

    assert len(findings) == 1
    finding = findings[0]
    assert finding.message == "Heading level jumps from H1 to H3."
    assert finding.location is not None
    assert finding.location.start_line == 3
    assert finding.location.start_column == 1


def test_markdown_structure_empty_headings_return_findings() -> None:
    markdown_text = (FIXTURES_DIR / "markdown_structure_empty_headings.md").read_text(
        encoding="utf-8"
    )

    findings = check_markdown_structure(markdown_text, _profile())

    assert [finding.message for finding in findings] == [
        "Empty heading detected.",
        "Empty heading detected.",
    ]
    assert [finding.location.start_line for finding in findings] == [3, 5]


def test_markdown_structure_long_paragraph_returns_finding() -> None:
    markdown_text = (FIXTURES_DIR / "markdown_structure_long_paragraph.md").read_text(
        encoding="utf-8"
    )

    findings = check_markdown_structure(markdown_text, _profile())

    assert len(findings) == 1
    finding = findings[0]
    assert finding.message.startswith("Paragraph exceeds maximum length (")
    assert finding.message.endswith(" > 80).")
    assert finding.matched_term == "paragraph"
    assert finding.location is not None
    assert finding.location.start_line == 3


def test_markdown_structure_ignores_heading_like_lines_in_code_blocks() -> None:
    markdown_text = (
        FIXTURES_DIR / "markdown_structure_code_block_headings.md"
    ).read_text(encoding="utf-8")

    findings = check_markdown_structure(markdown_text, _profile())

    assert findings == []
