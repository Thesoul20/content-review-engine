from __future__ import annotations

import re

from content_review_engine.core.location import build_source_span
from content_review_engine.core.models import ReviewFinding, ReviewProfile

MARKDOWN_STRUCTURE_RULE_ID = "markdown_structure"
RULE_ID = MARKDOWN_STRUCTURE_RULE_ID

_ATX_HEADING_PATTERN = re.compile(
    r"^(?P<indent>[ \t]{0,3})(?P<markers>#{1,6})(?:(?P<separator>[ \t]+)(?P<text>.*?))?[ \t]*$"
)


def _line_bounds(line_start_offset: int, line: str) -> tuple[int, int]:
    line_end_offset = line_start_offset + len(line.rstrip("\r\n"))
    return line_start_offset, line_end_offset


def _make_heading_finding(
    *,
    rule_id: str,
    message: str,
    matched_term: str,
    text: str,
    line_start_offset: int,
    line: str,
    indent: str,
) -> ReviewFinding:
    start_offset = line_start_offset + len(indent)
    _, end_offset = _line_bounds(line_start_offset, line)
    location = build_source_span(text, start_offset, end_offset)
    return ReviewFinding(
        rule_id=rule_id,
        severity="warning",
        message=message,
        matched_term=matched_term,
        matched_text=location.matched_text,
        location=location,
    )


def _make_paragraph_finding(
    *,
    rule_id: str,
    text: str,
    start_offset: int,
    end_offset: int,
    paragraph_length: int,
    max_length: int,
) -> ReviewFinding:
    location = build_source_span(text, start_offset, end_offset)
    return ReviewFinding(
        rule_id=rule_id,
        severity="warning",
        message=(
            f"Paragraph exceeds maximum length "
            f"({paragraph_length} > {max_length})."
        ),
        matched_term="paragraph",
        matched_text=location.matched_text,
        location=location,
    )


class MarkdownStructureRule:
    rule_id = MARKDOWN_STRUCTURE_RULE_ID

    def evaluate(
        self,
        text: str,
        profile: ReviewProfile,
    ) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []

        h1_count = 0
        previous_heading_level: int | None = None
        in_fenced_code_block = False
        fence_marker: str | None = None
        paragraph_start_offset: int | None = None
        paragraph_end_offset: int | None = None

        lines = text.splitlines(keepends=True)
        offset = 0

        for line in lines:
            stripped_line = line.lstrip(" \t")
            line_start_offset = offset
            line_end_offset = line_start_offset + len(line.rstrip("\r\n"))

            if in_fenced_code_block:
                if fence_marker is not None and stripped_line.startswith(fence_marker * 3):
                    in_fenced_code_block = False
                    fence_marker = None
                offset += len(line)
                continue

            if stripped_line.startswith("```") or stripped_line.startswith("~~~"):
                if paragraph_start_offset is not None and paragraph_end_offset is not None:
                    paragraph_text = text[paragraph_start_offset:paragraph_end_offset]
                    paragraph_length = len(paragraph_text.replace("\n", " ").strip())
                    if paragraph_length > profile.max_paragraph_length:
                        findings.append(
                            _make_paragraph_finding(
                                rule_id=self.rule_id,
                                text=text,
                                start_offset=paragraph_start_offset,
                                end_offset=paragraph_end_offset,
                                paragraph_length=paragraph_length,
                                max_length=profile.max_paragraph_length,
                            )
                        )
                    paragraph_start_offset = None
                    paragraph_end_offset = None

                in_fenced_code_block = True
                fence_marker = stripped_line[0]
                offset += len(line)
                continue

            heading_match = _ATX_HEADING_PATTERN.match(stripped_line)
            if heading_match is not None:
                if paragraph_start_offset is not None and paragraph_end_offset is not None:
                    paragraph_text = text[paragraph_start_offset:paragraph_end_offset]
                    paragraph_length = len(paragraph_text.replace("\n", " ").strip())
                    if paragraph_length > profile.max_paragraph_length:
                        findings.append(
                            _make_paragraph_finding(
                                rule_id=self.rule_id,
                                text=text,
                                start_offset=paragraph_start_offset,
                                end_offset=paragraph_end_offset,
                                paragraph_length=paragraph_length,
                                max_length=profile.max_paragraph_length,
                            )
                        )
                    paragraph_start_offset = None
                    paragraph_end_offset = None

                markers = heading_match.group("markers")
                heading_level = len(markers)
                heading_text = (heading_match.group("text") or "").strip()

                if heading_level == 1:
                    h1_count += 1
                    if h1_count > 1:
                        findings.append(
                            _make_heading_finding(
                                rule_id=self.rule_id,
                                message="Multiple H1 headings detected.",
                                matched_term="H1",
                                text=text,
                                line_start_offset=line_start_offset,
                                line=line,
                                indent=heading_match.group("indent") or "",
                            )
                        )

                if previous_heading_level is not None and heading_level > previous_heading_level + 1:
                    findings.append(
                        _make_heading_finding(
                            rule_id=self.rule_id,
                            message=(
                                f"Heading level jumps from H{previous_heading_level} "
                                f"to H{heading_level}."
                            ),
                            matched_term=f"H{heading_level}",
                            text=text,
                            line_start_offset=line_start_offset,
                            line=line,
                            indent=heading_match.group("indent") or "",
                        )
                    )

                if heading_text == "":
                        findings.append(
                            _make_heading_finding(
                                rule_id=self.rule_id,
                                message="Empty heading detected.",
                                matched_term=f"H{heading_level}",
                                text=text,
                                line_start_offset=line_start_offset,
                                line=line,
                                indent=heading_match.group("indent") or "",
                            )
                    )

                previous_heading_level = heading_level
                offset += len(line)
                continue

            if stripped_line.strip() == "":
                if paragraph_start_offset is not None and paragraph_end_offset is not None:
                    paragraph_text = text[paragraph_start_offset:paragraph_end_offset]
                    paragraph_length = len(paragraph_text.replace("\n", " ").strip())
                    if paragraph_length > profile.max_paragraph_length:
                        findings.append(
                            _make_paragraph_finding(
                                rule_id=self.rule_id,
                                text=text,
                                start_offset=paragraph_start_offset,
                                end_offset=paragraph_end_offset,
                                paragraph_length=paragraph_length,
                                max_length=profile.max_paragraph_length,
                            )
                        )
                    paragraph_start_offset = None
                    paragraph_end_offset = None
                offset += len(line)
                continue

            if paragraph_start_offset is None:
                paragraph_start_offset = line_start_offset
            paragraph_end_offset = line_end_offset

            offset += len(line)

        if paragraph_start_offset is not None and paragraph_end_offset is not None:
            paragraph_text = text[paragraph_start_offset:paragraph_end_offset]
            paragraph_length = len(paragraph_text.replace("\n", " ").strip())
            if paragraph_length > profile.max_paragraph_length:
                findings.append(
                    _make_paragraph_finding(
                        rule_id=self.rule_id,
                        text=text,
                        start_offset=paragraph_start_offset,
                        end_offset=paragraph_end_offset,
                        paragraph_length=paragraph_length,
                        max_length=profile.max_paragraph_length,
                    )
                )

        if h1_count == 0:
            findings.append(
                ReviewFinding(
                    rule_id=self.rule_id,
                    severity="warning",
                    message="Missing top-level H1 heading.",
                    matched_term="H1",
                    matched_text=None,
                    location=None,
                )
            )

        return findings


DEFAULT_MARKDOWN_STRUCTURE_RULE = MarkdownStructureRule()


def check_markdown_structure(
    markdown_text: str,
    profile: ReviewProfile,
) -> list[ReviewFinding]:
    return DEFAULT_MARKDOWN_STRUCTURE_RULE.evaluate(markdown_text, profile)


__all__ = [
    "DEFAULT_MARKDOWN_STRUCTURE_RULE",
    "MARKDOWN_STRUCTURE_RULE_ID",
    "MarkdownStructureRule",
    "RULE_ID",
    "check_markdown_structure",
]
