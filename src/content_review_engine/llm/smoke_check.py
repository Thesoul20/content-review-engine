from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from content_review_engine.llm.config import LLMProviderConfig
from content_review_engine.llm.factory import create_llm_reviewer
from content_review_engine.llm.models import LLMReviewRequest
from content_review_engine.llm.pydanticai import PydanticAIReviewer


LLMSmokeCheckStatus = Literal["ok", "skipped"]

_SMOKE_CHECK_CONTENT = "LLM smoke check synthetic request."


@dataclass(frozen=True)
class LLMSmokeCheckResult:
    provider: str
    config_status: LLMSmokeCheckStatus
    secret_status: LLMSmokeCheckStatus
    runtime_status: LLMSmokeCheckStatus


def build_llm_smoke_check_request() -> LLMReviewRequest:
    return LLMReviewRequest(
        content=_SMOKE_CHECK_CONTENT,
        profile_name="llm-check",
        content_path="<llm-check>",
        review_goal="smoke_check",
        metadata={"mode": "smoke_check"},
    )


def run_llm_smoke_check(
    config: LLMProviderConfig,
    *,
    runtime: bool = False,
    reviewer_provider: str | None = None,
) -> LLMSmokeCheckResult:
    provider_name = config.provider
    if reviewer_provider is not None:
        provider_name = reviewer_provider.strip().lower()
        reviewer = create_llm_reviewer(reviewer_provider)
    else:
        reviewer = create_llm_reviewer(config)
    secret_status: LLMSmokeCheckStatus = "skipped"

    if isinstance(reviewer, PydanticAIReviewer):
        reviewer.resolve_secret()
        secret_status = "ok"

    runtime_status: LLMSmokeCheckStatus = "skipped"
    if runtime:
        reviewer.review(build_llm_smoke_check_request())
        runtime_status = "ok"

    return LLMSmokeCheckResult(
        provider=provider_name,
        config_status="ok",
        secret_status=secret_status,
        runtime_status=runtime_status,
    )


def render_llm_smoke_check_result(result: LLMSmokeCheckResult) -> str:
    return "\n".join(
        [
            "LLM provider check passed.",
            "",
            f"Provider: {result.provider}",
            f"Config: {result.config_status}",
            f"Secret: {result.secret_status}",
            f"Runtime: {result.runtime_status}",
        ]
    )


__all__ = [
    "LLMSmokeCheckResult",
    "build_llm_smoke_check_request",
    "render_llm_smoke_check_result",
    "run_llm_smoke_check",
]
