from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from content_review_engine.llm.errors import LLMProviderError, LLMReviewError
from content_review_engine.llm.models import LLMReviewRequest, LLMReviewResult
from content_review_engine.llm.pydanticai_mapping import (
    PydanticAIReviewMapper,
    PydanticAIReviewRequestPayload,
    PydanticAIReviewResponse,
    build_pydanticai_review_request,
)

PYDANTIC_AI_TESTMODEL_PROVIDER_NAME = "pydanticai-testmodel"
PYDANTIC_AI_TESTMODEL_MODEL_NAME = "test"


def build_pydantic_ai_testmodel_request(
    request: LLMReviewRequest,
) -> PydanticAIReviewRequestPayload:
    return build_pydanticai_review_request(request)


def build_pydantic_ai_testmodel_response_args(
    *,
    findings: list[dict[str, Any]] | None = None,
    summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {"findings": findings or []}
    if summary is not None:
        response["summary"] = summary
    return response


def build_pydantic_ai_testmodel_agent(
    *,
    payload: PydanticAIReviewRequestPayload,
    model_name: str = PYDANTIC_AI_TESTMODEL_MODEL_NAME,
    output_args: dict[str, Any] | None = None,
    agent_type: type[Agent] = Agent,
) -> Agent:
    return agent_type(
        TestModel(
            model_name=model_name,
            custom_output_args=output_args
            or build_pydantic_ai_testmodel_response_args(),
        ),
        output_type=PydanticAIReviewResponse,
        system_prompt=payload.system_prompt,
        defer_model_check=True,
    )


def run_pydantic_ai_testmodel_agent(
    agent: Agent,
    payload: PydanticAIReviewRequestPayload,
) -> Any:
    return agent.run_sync(payload.user_prompt).output


class PydanticAITestModelReviewer:
    """LLM reviewer backed by PydanticAI TestModel for local tests only."""

    def __init__(
        self,
        *,
        model_name: str = PYDANTIC_AI_TESTMODEL_MODEL_NAME,
        output_args_builder: Callable[[LLMReviewRequest], dict[str, Any]] | None = None,
        agent_builder: Callable[..., Agent] | None = None,
        runtime_runner: Callable[[Agent, PydanticAIReviewRequestPayload], Any] | None = None,
    ) -> None:
        self.model_name = model_name
        self._output_args_builder = output_args_builder or (
            lambda _request: build_pydantic_ai_testmodel_response_args()
        )
        self._agent_builder = agent_builder or build_pydantic_ai_testmodel_agent
        self._runtime_runner = runtime_runner or run_pydantic_ai_testmodel_agent
        self.mapping = PydanticAIReviewMapper(
            provider=PYDANTIC_AI_TESTMODEL_PROVIDER_NAME,
            model=model_name,
        )

    def build_request_payload(
        self,
        request: LLMReviewRequest,
    ) -> PydanticAIReviewRequestPayload:
        return build_pydantic_ai_testmodel_request(request)

    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        try:
            payload = self.build_request_payload(request)
            output_args = self._output_args_builder(request)
            agent = self._agent_builder(
                payload=payload,
                model_name=self.model_name,
                output_args=output_args,
            )
            response = self._runtime_runner(agent, payload)
            return self.mapping.response_to_result(response, request)
        except LLMReviewError:
            raise
        except Exception as exc:
            raise LLMProviderError("PydanticAI TestModel reviewer failed.") from exc


__all__ = [
    "PYDANTIC_AI_TESTMODEL_MODEL_NAME",
    "PYDANTIC_AI_TESTMODEL_PROVIDER_NAME",
    "PydanticAITestModelReviewer",
    "build_pydantic_ai_testmodel_agent",
    "build_pydantic_ai_testmodel_request",
    "build_pydantic_ai_testmodel_response_args",
    "run_pydantic_ai_testmodel_agent",
]
