from __future__ import annotations

from pathlib import Path

from content_review_engine.core.models import (
    ReviewDocumentMetadata,
    ReviewProfile,
    ReviewProfileMetadata,
    ReviewResult,
)
from content_review_engine.core.suppression import (
    filter_suppressed_findings,
    parse_inline_suppressions,
)
from content_review_engine.rules import run_rules


def review_document(
    markdown_text: str,
    profile: ReviewProfile,
    *,
    document_path: str | Path | None = None,
    profile_path: str | Path | None = None,
) -> ReviewResult:
    findings = run_rules(markdown_text, profile)
    directives = parse_inline_suppressions(markdown_text)
    findings = filter_suppressed_findings(findings, directives)
    document = (
        ReviewDocumentMetadata(path=str(document_path))
        if document_path is not None
        else None
    )
    profile_metadata = ReviewProfileMetadata(
        name=profile.name,
        path=str(profile_path) if profile_path is not None else None,
    )
    return ReviewResult.from_findings(
        findings,
        document=document,
        profile=profile_metadata,
    )
