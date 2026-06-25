from __future__ import annotations

import json
from typing import Any

from content_review_engine.core.models import (
    BatchReviewResult,
    ProfileTemplateListResult,
    ProfileValidationResult,
    ReviewResult,
)


def review_result_to_dict(result: ReviewResult) -> dict[str, Any]:
    return result.model_dump(mode="json", exclude_none=True)


def review_result_to_json(result: ReviewResult) -> str:
    return json.dumps(review_result_to_dict(result), ensure_ascii=False, indent=2)


def batch_review_result_to_dict(result: BatchReviewResult) -> dict[str, Any]:
    return result.model_dump(mode="json", exclude_none=True)


def batch_review_result_to_json(
    result: BatchReviewResult,
    *,
    indent: int = 2,
) -> str:
    return json.dumps(batch_review_result_to_dict(result), ensure_ascii=False, indent=indent)


def profile_validation_result_to_dict(result: ProfileValidationResult) -> dict[str, Any]:
    return result.model_dump(mode="json")


def profile_validation_result_to_json(result: ProfileValidationResult) -> str:
    return json.dumps(profile_validation_result_to_dict(result), ensure_ascii=False, indent=2)


def profile_template_list_result_to_dict(
    result: ProfileTemplateListResult,
) -> dict[str, Any]:
    return result.model_dump(mode="json")


def profile_template_list_result_to_json(result: ProfileTemplateListResult) -> str:
    return json.dumps(
        profile_template_list_result_to_dict(result),
        ensure_ascii=False,
        indent=2,
    )


__all__ = [
    "batch_review_result_to_dict",
    "batch_review_result_to_json",
    "profile_template_list_result_to_dict",
    "profile_template_list_result_to_json",
    "review_result_to_dict",
    "review_result_to_json",
    "profile_validation_result_to_dict",
    "profile_validation_result_to_json",
]
