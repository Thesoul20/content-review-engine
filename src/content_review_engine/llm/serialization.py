from __future__ import annotations

import json
from typing import Any

from content_review_engine.llm.models import (
    LLMReviewFinding,
    LLMReviewResult,
    LLMReviewSummary,
)


def llm_review_finding_to_dict(finding: LLMReviewFinding) -> dict[str, Any]:
    return finding.model_dump(mode="json", exclude_none=True)


def llm_review_summary_to_dict(summary: LLMReviewSummary) -> dict[str, Any]:
    return summary.model_dump(mode="json", exclude_none=True)


def llm_review_result_to_dict(result: LLMReviewResult) -> dict[str, Any]:
    return result.model_dump(mode="json", exclude_none=True)


def llm_review_result_to_json(result: LLMReviewResult) -> str:
    return json.dumps(llm_review_result_to_dict(result), ensure_ascii=False, indent=2)


__all__ = [
    "llm_review_finding_to_dict",
    "llm_review_result_to_dict",
    "llm_review_result_to_json",
    "llm_review_summary_to_dict",
]
