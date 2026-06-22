from pathlib import Path

import pytest

from content_review_engine.parser import read_markdown


def test_read_markdown_from_path(tmp_path: Path) -> None:
    file_path = tmp_path / "article.md"
    file_path.write_text("# 标题\n\n内容。", encoding="utf-8")

    assert read_markdown(file_path) == "# 标题\n\n内容。"


def test_read_markdown_from_string_path(tmp_path: Path) -> None:
    file_path = tmp_path / "article.markdown"
    file_path.write_text("正文", encoding="utf-8")

    assert read_markdown(str(file_path)) == "正文"


def test_read_markdown_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Markdown file not found"):
        read_markdown(tmp_path / "missing.md")


def test_read_markdown_non_markdown_file_raises(tmp_path: Path) -> None:
    file_path = tmp_path / "article.txt"
    file_path.write_text("正文", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected a Markdown file"):
        read_markdown(file_path)
