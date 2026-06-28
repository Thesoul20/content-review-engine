from __future__ import annotations

from collections.abc import Callable
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
    classify_pydanticai_runtime_error,
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
        secret_resolver: Callable[[LLMProviderConfig], ResolvedLLMSecret] = resolve_llm_api_key,
        agent_builder: Callable[..., Agent] | None = None,
        runtime_runner: Callable[[Agent, PydanticAIReviewRequestPayload], Any] | None = None,
    ) -> None:
        self.config = config
        self.model = config.model
        self.api_key_env = config.api_key_env
        self.base_url = config.base_url
        self.timeout_seconds = config.timeout_seconds
        self._secret_resolver = secret_resolver
        self._agent_builder = agent_builder or build_pydanticai_runtime_agent
        self._runtime_runner = runtime_runner or run_pydanticai_runtime_agent
        self._agent_type = Agent
        self.mapping = PydanticAIReviewMapper(
            provider=PYDANTICAI_PROVIDER_NAME,
            model=config.model,
        )

    def resolve_secret(self) -> ResolvedLLMSecret:
        return self._secret_resolver(self.config)

    def build_request_payload(
        self,
        request: LLMReviewRequest,
    ) -> PydanticAIReviewRequestPayload:
        return self.mapping.build_request(request)

    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        payload = self.build_request_payload(request)
        secret = self.resolve_secret()
        agent = self._agent_builder(
            model=_normalize_model_name(self.model),
            system_prompt=payload.system_prompt,
            secret=secret,
            base_url=self.base_url,
            timeout_seconds=self.timeout_seconds,
            agent_type=self._agent_type,
        )
        try:
            response = self._runtime_runner(agent, payload)
        except LLMResponseValidationError:
            raise
        except Exception as exc:
            raise classify_pydanticai_runtime_error(exc) from exc
        return self.mapping.response_to_result(response, request)


__all__ = [
    "PYDANTICAI_NOT_IMPLEMENTED_MESSAGE",
    "PYDANTICAI_PROVIDER_NAME",
    "PydanticAIReviewer",
    "build_pydanticai_runtime_agent",
    "raise_pydanticai_not_implemented",
    "run_pydanticai_runtime_agent",
]
