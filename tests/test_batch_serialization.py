from __future__ import annotations

import json
from pathlib import Path

from content_review_engine.config import load_profile
from content_review_engine.core.serialization import (
    batch_review_result_to_dict,
    batch_review_result_to_json,
)
from content_review_engine.review.batch import review_markdown_directory

BATCH_FIXTURES_DIR = Path("tests/fixtures/batch")
BATCH_ARTICLES_DIR = BATCH_FIXTURES_DIR / "articles"
BATCH_PROFILE_PATH = BATCH_FIXTURES_DIR / "profile.yml"


def _build_batch_result():
    profile = load_profile(BATCH_PROFILE_PATH)
    return review_markdown_directory(
        BATCH_ARTICLES_DIR,
        profile,
        recursive=True,
        profile_path=BATCH_PROFILE_PATH,
    )


def test_batch_review_result_to_dict_uses_canonical_shape() -> None:
    result = _build_batch_result()

    payload = batch_review_result_to_dict(result)

    assert payload == {
        "schema_version": "batch-review-result.v1",
        "summary": {
            "file_count": 3,
            "reviewed_count": 3,
            "finding_count": 2,
            "files_with_findings": 2,
            "severity_counts": {
                "info": 0,
                "warning": 2,
                "error": 0,
                "critical": 0,
            },
        },
        "results": [
            {
                "schema_version": "review-result.v1",
                "summary": {
                    "finding_count": 0,
                    "severity_counts": {
                        "info": 0,
                        "warning": 0,
                        "error": 0,
                        "critical": 0,
                    },
                },
                "findings": [],
                "document": {
                    "path": "tests/fixtures/batch/articles/clean.md",
                },
                "profile": {
                    "name": "batch-default",
                    "path": "tests/fixtures/batch/profile.yml",
                },
            },
            {
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
                            "context": "# 测试文章 绝对安全\n",
                        },
                    }
                ],
                "document": {
                    "path": "tests/fixtures/batch/articles/forbidden.md",
                },
                "profile": {
                    "name": "batch-default",
                    "path": "tests/fixtures/batch/profile.yml",
                },
            },
            {
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
                            "context": "# 测试文章 绝对安全\n",
                        },
                    }
                ],
                "document": {
                    "path": "tests/fixtures/batch/articles/nested/nested_forbidden.md",
                },
                "profile": {
                    "name": "batch-default",
                    "path": "tests/fixtures/batch/profile.yml",
                },
            },
        ],
    }


def test_batch_review_result_to_json_uses_canonical_shape() -> None:
    result = _build_batch_result()

    payload = json.loads(batch_review_result_to_json(result))

    assert payload["schema_version"] == "batch-review-result.v1"
    assert payload["summary"]["file_count"] == 3
    assert payload["summary"]["finding_count"] == 2
    assert payload["results"][0]["schema_version"] == "review-result.v1"
    assert payload["results"][1]["findings"][0]["location"]["matched_text"] == "绝对安全"
