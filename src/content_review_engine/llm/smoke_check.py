from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Literal

from content_review_engine.llm.config import LLMProviderConfig
from content_review_engine.llm.factory import create_llm_reviewer
from content_review_engine.llm.models import LLMReviewRequest
from content_review_engine.llm.secrets import (
    redact_secret_value,
    resolve_llm_provider_secret,
)


LLMSmokeCheckStatus = Literal["ok", "skipped"]
LLMSmokeCheckSecretStatus = Literal["resolved", "not_required"]
LLMSmokeCheckLiveCallStatus = Literal["not run", "ok"]

_SMOKE_CHECK_CONTENT = "LLM smoke check synthetic request."
_UNSET_MODEL_TEXT = "<not configured>"


@dataclass(frozen=True)
class LLMSmokeCheckResult:
    provider: str
    model: str | None
    config_status: LLMSmokeCheckStatus
    secret_status: LLMSmokeCheckSecretStatus
    api_key_env: str | None
    redacted_secret: str | None
    construction_status: LLMSmokeCheckStatus
    live_call_status: LLMSmokeCheckLiveCallStatus


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
    env: Mapping[str, str] | None = None,
) -> LLMSmokeCheckResult:
    provider_name = config.provider
    secret_value: str | None = None
    secret_status: LLMSmokeCheckSecretStatus = "not_required"
    api_key_env: str | None = None
    redacted_secret: str | None = None

    if reviewer_provider is not None:
        provider_name = reviewer_provider.strip().lower()
        reviewer = create_llm_reviewer(reviewer_provider)
    else:
        if config.provider == "pydanticai":
            secret_value = resolve_llm_provider_secret(config, env=env)
            reviewer = create_llm_reviewer(config, secret_value=secret_value)
        else:
            reviewer = create_llm_reviewer(config)

    if reviewer_provider is None and config.provider == "pydanticai" and secret_value is not None:
        api_key_env = config.api_key_env
        redacted_secret = redact_secret_value(secret_value)
        secret_status = "resolved"

    construction_status: LLMSmokeCheckStatus = "ok"
    if reviewer_provider is None and hasattr(reviewer, "run_construction_check"):
        reviewer.run_construction_check()

    live_call_status: LLMSmokeCheckLiveCallStatus = "not run"
    if runtime:
        reviewer.review(build_llm_smoke_check_request())
        live_call_status = "ok"

    return LLMSmokeCheckResult(
        provider=provider_name,
        model=config.model,
        config_status="ok",
        secret_status=secret_status,
        api_key_env=api_key_env,
        redacted_secret=redacted_secret,
        construction_status=construction_status,
        live_call_status=live_call_status,
    )


def render_llm_smoke_check_result(result: LLMSmokeCheckResult) -> str:
    lines = [
        "LLM check passed.",
        "",
        f"Provider: {result.provider}",
        f"Model: {result.model or _UNSET_MODEL_TEXT}",
        f"Config: {result.config_status}",
    ]
    if result.secret_status == "resolved":
        lines.extend(
            [
                f"API key env: {result.api_key_env}",
                f"API key: {result.redacted_secret}",
                "Secret: resolved",
            ]
        )
    else:
        lines.append("Secret: not required")
    lines.append(f"Construction: {result.construction_status}")
    lines.append(f"Live call: {result.live_call_status}")
    return "\n".join(lines)


__all__ = [
    "LLMSmokeCheckResult",
    "build_llm_smoke_check_request",
    "render_llm_smoke_check_result",
    "run_llm_smoke_check",
]
