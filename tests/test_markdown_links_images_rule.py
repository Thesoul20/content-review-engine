from __future__ import annotations

from pathlib import Path

from content_review_engine.core.models import ReviewProfile
from content_review_engine.rules import check_markdown_links_images

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "markdown"


def _profile() -> ReviewProfile:
    return ReviewProfile(
        name="markdown-links-images",
        target_platform="wechat",
        forbidden_terms=[],
    )


def test_markdown_links_images_empty_link_text_returns_finding() -> None:
    findings = check_markdown_links_images("[](https://example.com)", _profile())

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "markdown_links_images"
    assert finding.severity == "warning"
    assert finding.message == "链接文本为空。"
    assert finding.matched_term == "empty_link_text"
    assert finding.location is not None
    assert finding.location.start_line == 1
    assert finding.location.start_column == 1
    assert finding.location.matched_text == "[](https://example.com)"


def test_markdown_links_images_empty_link_target_returns_finding() -> None:
    findings = check_markdown_links_images("[文档]()", _profile())

    assert len(findings) == 1
    finding = findings[0]
    assert finding.message == "链接目标为空。"
    assert finding.matched_term == "empty_link_target"
    assert finding.location is not None
    assert finding.location.start_line == 1
    assert finding.location.matched_text == "[文档]()"


def test_markdown_links_images_placeholder_link_target_returns_finding() -> None:
    findings = check_markdown_links_images("[文档](#)", _profile())

    assert len(findings) == 1
    finding = findings[0]
    assert finding.message == "链接目标仍是占位符。"
    assert finding.matched_term == "placeholder_link_target"
    assert finding.location is not None
    assert finding.location.start_line == 1
    assert finding.location.matched_text == "[文档](#)"


def test_markdown_links_images_empty_image_alt_text_returns_finding() -> None:
    findings = check_markdown_links_images("![](image.png)", _profile())

    assert len(findings) == 1
    finding = findings[0]
    assert finding.message == "图片 alt 文本为空。"
    assert finding.matched_term == "empty_image_alt_text"
    assert finding.location is not None
    assert finding.location.start_line == 1
    assert finding.location.matched_text == "![](image.png)"


def test_markdown_links_images_empty_image_target_returns_finding() -> None:
    findings = check_markdown_links_images("![示例图]()", _profile())

    assert len(findings) == 1
    finding = findings[0]
    assert finding.message == "图片目标为空。"
    assert finding.matched_term == "empty_image_target"
    assert finding.location is not None
    assert finding.location.start_line == 1
    assert finding.location.matched_text == "![示例图]()"


def test_markdown_links_images_placeholder_image_target_returns_finding() -> None:
    findings = check_markdown_links_images("![示例图](TODO)", _profile())

    assert len(findings) == 1
    finding = findings[0]
    assert finding.message == "图片目标仍是占位符。"
    assert finding.matched_term == "placeholder_image_target"
    assert finding.location is not None
    assert finding.location.start_line == 1
    assert finding.location.matched_text == "![示例图](TODO)"


def test_markdown_links_images_ignores_syntax_inside_fenced_code_blocks() -> None:
    markdown_text = (FIXTURES_DIR / "markdown_links_images_issues.md").read_text(
        encoding="utf-8"
    )

    findings = check_markdown_links_images(markdown_text, _profile())

    assert [finding.message for finding in findings] == [
        "链接文本为空。",
        "链接目标为空。",
        "链接目标仍是占位符。",
        "图片 alt 文本为空。",
        "图片目标为空。",
        "图片目标仍是占位符。",
    ]
    assert [finding.location.start_line for finding in findings] == [1, 2, 3, 4, 5, 6]


def test_markdown_links_images_valid_links_and_images_return_no_findings() -> None:
    markdown_text = "\n".join(
        [
            "[OpenAI](https://example.com)",
            "![架构图](images/architecture.png)",
        ]
    )

    findings = check_markdown_links_images(markdown_text, _profile())

    assert findings == []
