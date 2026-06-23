from content_review_engine.core.location import (
    extract_context_snippet,
    offset_to_line_column,
)


def test_offset_to_line_column_single_line_text() -> None:
    assert offset_to_line_column("abcd", 0) == (1, 1)
    assert offset_to_line_column("abcd", 3) == (1, 4)


def test_offset_to_line_column_multi_line_chinese_text() -> None:
    text = "第一行\n第二行绝对正确"
    start_offset = text.index("绝对")
    end_offset = start_offset + len("绝对")

    assert offset_to_line_column(text, start_offset) == (2, 4)
    assert offset_to_line_column(text, end_offset) == (2, 6)


def test_extract_context_snippet_trims_around_match() -> None:
    text = "前面的内容这个方法绝对可以提升你的写作效率后面的内容"
    start_offset = text.index("绝对")
    end_offset = start_offset + len("绝对")

    snippet = extract_context_snippet(text, start_offset, end_offset, before_chars=6, after_chars=6)

    assert snippet.startswith("...")
    assert snippet.endswith("...")
    assert "绝对" in snippet


def test_extract_context_snippet_handles_document_boundaries() -> None:
    start_text = "绝对正确"
    end_text = "这是一个绝对"

    assert extract_context_snippet(start_text, 0, len("绝对")) == start_text
    assert extract_context_snippet(end_text, len("这是一个"), len(end_text)) == end_text
