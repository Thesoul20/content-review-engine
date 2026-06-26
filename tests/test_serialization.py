from __future__ import annotations

import json

from content_review_engine.core.models import (
    ProfileTemplateListResult,
    ProfileTemplateSummary,
    ReviewDocumentMetadata,
    ReviewFinding,
    ReviewProfileMetadata,
    ReviewResult,
    SourceSpan,
)
from content_review_engine.core.serialization import (
    profile_template_list_result_to_json,
    review_result_to_dict,
    review_result_to_json,
)


def _build_result() -> ReviewResult:
    finding = ReviewFinding(
        rule_id="forbidden_terms",
        severity="warning",
        message="发现风险词：绝对安全",
        matched_term="绝对安全",
        matched_text="绝对安全",
        location=SourceSpan(
            start_line=1,
            start_column=8,
            end_line=1,
            end_column=12,
            start_offset=7,
            end_offset=11,
            matched_text="绝对安全",
            context="# 测试文章 绝对安全",
        ),
    )
    return ReviewResult.from_findings(
        [finding],
        document=ReviewDocumentMetadata(
            path="tests/fixtures/markdown/forbidden_terms_article.md"
        ),
        profile=ReviewProfileMetadata(
            name="default",
            path="tests/fixtures/profiles/default.yml",
        ),
    )


def test_review_result_to_dict_uses_canonical_shape() -> None:
    result = _build_result()

    payload = review_result_to_dict(result)

    assert payload == {
        "schema_version": "review-result.v1",
        "summary": {
            "finding_count": 1,
            "severity_counts": {
                "info": 0,
                "warning": 1,
                "error": 0,
                "critical": 0,
            },
        },
        "findings": [
            {
                "rule_id": "forbidden_terms",
                "severity": "warning",
                "message": "发现风险词：绝对安全",
                "matched_term": "绝对安全",
                "matched_text": "绝对安全",
                "location": {
                    "start_line": 1,
                    "start_column": 8,
                    "end_line": 1,
                    "end_column": 12,
                    "start_offset": 7,
                    "end_offset": 11,
                    "matched_text": "绝对安全",
                    "context": "# 测试文章 绝对安全",
                },
            }
        ],
        "document": {
            "path": "tests/fixtures/markdown/forbidden_terms_article.md",
        },
        "profile": {
            "name": "default",
            "path": "tests/fixtures/profiles/default.yml",
        },
    }


def test_review_result_to_json_uses_canonical_shape() -> None:
    result = _build_result()

    payload = json.loads(review_result_to_json(result))

    assert payload["schema_version"] == "review-result.v1"
    assert payload["summary"]["finding_count"] == 1
    assert payload["findings"][0]["location"]["matched_text"] == "绝对安全"


def test_profile_template_list_result_to_json_uses_canonical_shape() -> None:
    result = ProfileTemplateListResult(
        templates=[
            ProfileTemplateSummary(
                name="general-basic",
                description="General-purpose starter profile for public-facing content.",
            ),
            ProfileTemplateSummary(
                name="general-publishing",
                description="Conservative publishing profile with placeholder and overclaim checks.",
            ),
            ProfileTemplateSummary(
                name="wechat-basic",
                description="Basic WeChat article profile with moderate checks.",
            ),
        ]
    )

    payload = json.loads(profile_template_list_result_to_json(result))

    assert payload == {
        "schema_version": "profile-template-list.v1",
        "templates": [
            {
                "name": "general-basic",
                "description": "General-purpose starter profile for public-facing content.",
            },
            {
                "name": "general-publishing",
                "description": "Conservative publishing profile with placeholder and overclaim checks.",
            },
            {
                "name": "wechat-basic",
                "description": "Basic WeChat article profile with moderate checks.",
            },
        ],
    }
