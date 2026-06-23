from __future__ import annotations

import re

from content_review_engine.core.location import build_source_span
from content_review_engine.core.models import ReviewFinding, ReviewProfile

MARKDOWN_LINKS_IMAGES_RULE_ID = "markdown_links_images"
RULE_ID = MARKDOWN_LINKS_IMAGES_RULE_ID

_PLACEHOLDER_TARGETS = {
    "#",
    "TODO",
    "todo",
    "TBD",
    "tbd",
    "待补充",
    "待填写",
}
_IMAGE_PATTERN = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<target>[^)]*)\)")
_LINK_PATTERN = re.compile(r"(?<!\!)\[(?P<text>[^\]]*)\]\((?P<target>[^)]*)\)")


def _make_finding(
    *,
    rule_id: str,
    message: str,
    matched_term: str,
    text: str,
    start_offset: int,
    end_offset: int,
) -> ReviewFinding:
    location = build_source_span(text, start_offset, end_offset)
    return ReviewFinding(
        rule_id=rule_id,
        severity="warning",
        message=message,
        matched_term=matched_term,
        matched_text=location.matched_text,
        location=location,
    )


def _is_placeholder_target(target: str) -> bool:
    return target.strip() in _PLACEHOLDER_TARGETS


class MarkdownLinksImagesRule:
    rule_id = MARKDOWN_LINKS_IMAGES_RULE_ID

    def evaluate(
        self,
        text: str,
        profile: ReviewProfile,
    ) -> list[ReviewFinding]:
        del profile

        findings: list[ReviewFinding] = []
        in_fenced_code_block = False
        fence_marker: str | None = None

        lines = text.splitlines(keepends=True)
        offset = 0

        for line in lines:
            stripped_line = line.lstrip(" \t")

            if in_fenced_code_block:
                if fence_marker is not None and stripped_line.startswith(
                    fence_marker * 3
                ):
                    in_fenced_code_block = False
                    fence_marker = None
                offset += len(line)
                continue

            if stripped_line.startswith("```") or stripped_line.startswith("~~~"):
                in_fenced_code_block = True
                fence_marker = stripped_line[0]
                offset += len(line)
                continue

            for match in _IMAGE_PATTERN.finditer(line):
                start_offset = offset + match.start()
                end_offset = offset + match.end()
                alt_text = match.group("alt")
                target = match.group("target")

                if alt_text.strip() == "":
                    findings.append(
                        _make_finding(
                            rule_id=self.rule_id,
                            message="图片 alt 文本为空。",
                            matched_term="empty_image_alt_text",
                            text=text,
                            start_offset=start_offset,
                            end_offset=end_offset,
                        )
                    )

                normalized_target = target.strip()
                if normalized_target == "":
                    findings.append(
                        _make_finding(
                            rule_id=self.rule_id,
                            message="图片目标为空。",
                            matched_term="empty_image_target",
                            text=text,
                            start_offset=start_offset,
                            end_offset=end_offset,
                        )
                    )
                elif _is_placeholder_target(normalized_target):
                    findings.append(
                        _make_finding(
                            rule_id=self.rule_id,
                            message="图片目标仍是占位符。",
                            matched_term="placeholder_image_target",
                            text=text,
                            start_offset=start_offset,
                            end_offset=end_offset,
                        )
                    )

            for match in _LINK_PATTERN.finditer(line):
                start_offset = offset + match.start()
                end_offset = offset + match.end()
                link_text = match.group("text")
                target = match.group("target")

                if link_text.strip() == "":
                    findings.append(
                        _make_finding(
                            rule_id=self.rule_id,
                            message="链接文本为空。",
                            matched_term="empty_link_text",
                            text=text,
                            start_offset=start_offset,
                            end_offset=end_offset,
                        )
                    )

                normalized_target = target.strip()
                if normalized_target == "":
                    findings.append(
                        _make_finding(
                            rule_id=self.rule_id,
                            message="链接目标为空。",
                            matched_term="empty_link_target",
                            text=text,
                            start_offset=start_offset,
                            end_offset=end_offset,
                        )
                    )
                elif _is_placeholder_target(normalized_target):
                    findings.append(
                        _make_finding(
                            rule_id=self.rule_id,
                            message="链接目标仍是占位符。",
                            matched_term="placeholder_link_target",
                            text=text,
                            start_offset=start_offset,
                            end_offset=end_offset,
                        )
                    )

            offset += len(line)

        return findings


DEFAULT_MARKDOWN_LINKS_IMAGES_RULE = MarkdownLinksImagesRule()


def check_markdown_links_images(
    markdown_text: str,
    profile: ReviewProfile,
) -> list[ReviewFinding]:
    return DEFAULT_MARKDOWN_LINKS_IMAGES_RULE.evaluate(markdown_text, profile)


__all__ = [
    "DEFAULT_MARKDOWN_LINKS_IMAGES_RULE",
    "MARKDOWN_LINKS_IMAGES_RULE_ID",
    "MarkdownLinksImagesRule",
    "RULE_ID",
    "check_markdown_links_images",
]
