from __future__ import annotations

from content_review_engine.core.models import SourceSpan


def offset_to_line_column(text: str, offset: int) -> tuple[int, int]:
    if offset < 0 or offset > len(text):
        raise ValueError("Offset is out of range.")

    line = 1
    column = 1
    index = 0

    while index < offset:
        character = text[index]
        if character == "\r":
            if index + 1 < offset and text[index + 1] == "\n":
                index += 1
            line += 1
            column = 1
        elif character == "\n":
            line += 1
            column = 1
        else:
            column += 1
        index += 1

    return line, column


def extract_context_snippet(
    text: str,
    start_offset: int,
    end_offset: int,
    *,
    before_chars: int = 30,
    after_chars: int = 30,
) -> str:
    if start_offset < 0 or end_offset < start_offset or end_offset > len(text):
        raise ValueError("Offsets are out of range.")

    context_start = max(0, start_offset - before_chars)
    context_end = min(len(text), end_offset + after_chars)
    snippet = text[context_start:context_end]

    if context_start > 0:
        snippet = f"...{snippet}"
    if context_end < len(text):
        snippet = f"{snippet}..."

    return snippet


def build_source_span(text: str, start_offset: int, end_offset: int) -> SourceSpan:
    start_line, start_column = offset_to_line_column(text, start_offset)
    end_line, end_column = offset_to_line_column(text, end_offset)
    matched_text = text[start_offset:end_offset]
    context = extract_context_snippet(text, start_offset, end_offset)

    return SourceSpan(
        start_line=start_line,
        start_column=start_column,
        end_line=end_line,
        end_column=end_column,
        start_offset=start_offset,
        end_offset=end_offset,
        matched_text=matched_text,
        context=context,
    )


__all__ = [
    "build_source_span",
    "extract_context_snippet",
    "offset_to_line_column",
]
