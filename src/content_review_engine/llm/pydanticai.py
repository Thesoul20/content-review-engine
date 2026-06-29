from __future__ import annotations

from collections.abc import Callable
import time
from typing import Any

from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from content_review_engine.llm.config import LLMProviderConfig
from content_review_engine.llm.errors import (
    LLMProviderConfigError,
    LLMProviderError,
    LLMProviderNotImplementedError,
    LLMResponseValidationError,
)
from content_review_engine.llm.models import LLMReviewRequest, LLMReviewResult
from content_review_engine.llm.pydanticai_mapping import (
    PydanticAIReviewMapper,
    PydanticAIReviewRequestPayload,
    PydanticAIReviewResponse,
)
from content_review_engine.llm.pydanticai_errors import (
    build_pydanticai_retry_exhausted_error,
    classify_pydanticai_runtime_error,
    is_pydanticai_retryable_error,
)
from content_review_engine.llm.secrets import ResolvedLLMSecret, resolve_llm_api_key

PYDANTICAI_PROVIDER_NAME = "pydanticai"
PYDANTICAI_NOT_IMPLEMENTED_MESSAGE = (
    "Provider 'pydanticai' dependency and secret boundary is available, "
    "but review is not implemented yet."
)


def raise_pydanticai_not_implemented() -> None:
    raise LLMProviderNotImplementedError(PYDANTICAI_NOT_IMPLEMENTED_MESSAGE)


def _normalize_model_name(model: str | None) -> str:
    if model is None:
        raise LLMProviderConfigError(
            "LLM provider 'pydanticai' requires model to be configured."
        )
    if model.startswith("openai:"):
        normalized = model.removeprefix("openai:").strip()
        if normalized == "":
            raise LLMProviderConfigError(
                "LLM provider 'pydanticai' requires model to be configured."
            )
        return normalized
    return model


def build_pydanticai_runtime_agent(
    *,
    model: str,
    system_prompt: str,
    secret: ResolvedLLMSecret,
    base_url: str | None,
    timeout_seconds: float | None,
    agent_type: type[Agent] = Agent,
) -> Agent:
    openai_client = AsyncOpenAI(
        base_url=base_url,
        api_key=secret.api_key.get_secret_value(),
        timeout=timeout_seconds,
        max_retries=0,
    )
    provider = OpenAIProvider(
        openai_client=openai_client,
    )
    runtime_model = OpenAIChatModel(
        _normalize_model_name(model),
        provider=provider,
    )
    return agent_type(
        runtime_model,
        output_type=PydanticAIReviewResponse,
        system_prompt=system_prompt,
        defer_model_check=True,
    )


def run_pydanticai_runtime_agent(
    agent: Agent,
    payload: PydanticAIReviewRequestPayload,
) -> Any:
    return agent.run_sync(payload.user_prompt).output


class PydanticAIReviewer:
    """PydanticAI-backed reviewer using the project's stable mapping boundary."""

    def __init__(
        self,
        config: LLMProviderConfig,
        *,
        resolved_secret: ResolvedLLMSecret | None = None,
        secret_resolver: Callable[[LLMProviderConfig], ResolvedLLMSecret] = resolve_llm_api_key,
        agent_builder: Callable[..., Agent] | None = None,
        runtime_runner: Callable[[Agent, PydanticAIReviewRequestPayload], Any] | None = None,
        sleep_func: Callable[[float], None] | None = None,
        monotonic_func: Callable[[], float] | None = None,
    ) -> None:
        self.config = config
        self.model = config.model
        self.api_key_env = config.api_key_env
        self.base_url = config.base_url
        self.timeout_seconds = config.timeout_seconds
        self.retry_attempts = config.retry_attempts
        self.retry_backoff_seconds = config.retry_backoff_seconds
        self.min_request_interval_seconds = config.min_request_interval_seconds
        self._resolved_secret = resolved_secret
        self._secret_resolver = secret_resolver
        self._agent_builder = agent_builder or build_pydanticai_runtime_agent
        self._runtime_runner = runtime_runner or run_pydanticai_runtime_agent
        self._sleep_func = sleep_func or time.sleep
        self._monotonic_func = monotonic_func or time.monotonic
        self._last_request_started_at: float | None = None
        self._agent_type = Agent
        self.mapping = PydanticAIReviewMapper(
            provider=PYDANTICAI_PROVIDER_NAME,
            model=config.model,
        )

    def resolve_secret(self) -> ResolvedLLMSecret:
        if self._resolved_secret is not None:
            return self._resolved_secret
        return self._secret_resolver(self.config)

    def build_runtime_agent(self, system_prompt: str) -> Agent:
        return self._agent_builder(
            model=_normalize_model_name(self.model),
            system_prompt=system_prompt,
            secret=self.resolve_secret(),
            base_url=self.base_url,
            timeout_seconds=self.timeout_seconds,
            agent_type=self._agent_type,
        )

    def run_construction_check(self) -> None:
        self.build_runtime_agent("LLM smoke check construction-only prompt.")

    def build_request_payload(
        self,
        request: LLMReviewRequest,
    ) -> PydanticAIReviewRequestPayload:
        return self.mapping.build_request(request)

    def _apply_request_pacing(self) -> None:
        if self.min_request_interval_seconds <= 0:
            return

        now = self._monotonic_func()
        if self._last_request_started_at is None:
            self._last_request_started_at = now
            return

        elapsed = now - self._last_request_started_at
        remaining = self.min_request_interval_seconds - elapsed
        if remaining > 0:
            self._sleep_func(remaining)
            now = self._monotonic_func()
        self._last_request_started_at = now

    def _run_with_retries(
        self,
        *,
        agent: Agent,
        payload: PydanticAIReviewRequestPayload,
    ) -> Any:
        max_attempts = self.retry_attempts + 1
        last_error: LLMProviderRuntimeError | None = None

        for attempt_number in range(1, max_attempts + 1):
            try:
                self._apply_request_pacing()
                return self._runtime_runner(agent, payload)
            except LLMResponseValidationError:
                raise
            except Exception as exc:
                normalized_error = classify_pydanticai_runtime_error(exc)
                if not is_pydanticai_retryable_error(normalized_error):
                    raise normalized_error from exc
                last_error = normalized_error
                if attempt_number >= max_attempts:
                    if self.retry_attempts == 0:
                        raise normalized_error from exc
                    raise build_pydanticai_retry_exhausted_error(
                        attempts=attempt_number,
                        last_error=normalized_error,
                    ) from exc
                if self.retry_backoff_seconds > 0:
                    self._sleep_func(self.retry_backoff_seconds)

        if last_error is not None:
            raise build_pydanticai_retry_exhausted_error(
                attempts=max_attempts,
                last_error=last_error,
            )
        raise LLMProviderRuntimeError("PydanticAI runtime call failed unexpectedly.")

    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        payload = self.build_request_payload(request)
        agent = self.build_runtime_agent(payload.system_prompt)
        response = self._run_with_retries(agent=agent, payload=payload)
        return self.mapping.response_to_result(response, request)


__all__ = [
    "PYDANTICAI_NOT_IMPLEMENTED_MESSAGE",
    "PYDANTICAI_PROVIDER_NAME",
    "PydanticAIReviewer",
    "build_pydanticai_runtime_agent",
    "raise_pydanticai_not_implemented",
    "run_pydanticai_runtime_agent",
]
