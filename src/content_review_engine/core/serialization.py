from __future__ import annotations

import json
from typing import Any

from content_review_engine.core.models import ReviewResult


def review_result_to_dict(result: ReviewResult) -> dict[str, Any]:
    return result.model_dump(mode="json", exclude_none=True)


def review_result_to_json(result: ReviewResult) -> str:
    return json.dumps(review_result_to_dict(result), ensure_ascii=False, indent=2)


__all__ = ["review_result_to_dict", "review_result_to_json"]
