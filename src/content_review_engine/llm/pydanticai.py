from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError
from pydantic_ai import Agent
from pydantic_ai.exceptions import AgentRunError
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from content_review_engine.llm.errors import (
    LLMProviderError,
    LLMResponseValidationError,
)
from content_review_engine.llm.models import (
    LLMReviewFinding,
    LLMReviewRequest,
    LLMReviewResult,
    LLMReviewSummary,
)

PYDANTICAI_OPENAI_PROVIDER_NAME = "pydanticai-openai"
PYDANTICAI_OPENAI_PROMPT_VERSION = "pydanticai-openai.v1"

_SYSTEM_PROMPT = """
Review the provided Markdown content and return structured semantic review output.

Requirements:
- Return only structured output matching the schema.
- Findings must use stable rule_id values.
- Use canonical severities: info, warning, error, critical.
- Prefer conservative findings over speculative ones.
- If there are no meaningful semantic issues, return an empty findings list.
- Keep summary concise and factual.
""".strip()


def _normalize_required_non_empty(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if normalized == "":
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _normalize_optional_non_empty(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized == "":
        raise ValueError(f"{field_name} must not be empty")
    return normalized


class _PydanticAIOutputFinding(BaseModel):
    rule_id: str
    severity: str
    message: str
    suggestion: str | None = None
    rationale: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    end_column: int | None = Field(default=None, ge=1)
    matched_text: str | None = None
    category: str | None = None


class _PydanticAIOutputSummary(BaseModel):
    overall_risk: str | None = None
    summary: str | None = None
    recommended_action: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class _PydanticAIOutputResult(BaseModel):
    findings: tuple[_PydanticAIOutputFinding, ...] = Field(default_factory=tuple)
    summary: _PydanticAIOutputSummary | None = None
    metadata: dict[str, str] | None = None


def _create_agent(*, model: str, api_key: str, base_url: str | None) -> Agent[None, Any]:
    model_adapter = OpenAIChatModel(
        model_name=model,
        provider=OpenAIProvider(api_key=api_key, base_url=base_url),
    )
    return Agent(
        model_adapter,
        output_type=_PydanticAIOutputResult,
        system_prompt=_SYSTEM_PROMPT,
    )


def _build_user_prompt(request: LLMReviewRequest) -> str:
    prompt_lines = ["Review this Markdown content semantically."]

    if request.profile_name is not None:
        prompt_lines.append(f"Profile name: {request.profile_name}")
    if request.content_path is not None:
        prompt_lines.append(f"Content path: {request.content_path}")
    if request.review_goal is not None:
        prompt_lines.append(f"Review goal: {request.review_goal}")
    if request.metadata:
        prompt_lines.append("Metadata:")
        for key, value in sorted(request.metadata.items()):
            prompt_lines.append(f"- {key}: {value}")

    prompt_lines.extend(["", "Markdown content:", request.content])
    return "\n".join(prompt_lines)


def _map_output_to_llm_result(
    *,
    output: Any,
    request: LLMReviewRequest,
    model: str,
) -> LLMReviewResult:
    try:
        structured_output = _PydanticAIOutputResult.model_validate(output)
        findings = tuple(
            LLMReviewFinding(
                rule_id=finding.rule_id,
                severity=finding.severity,
                message=finding.message,
                suggestion=finding.suggestion,
                rationale=finding.rationale,
                confidence=finding.confidence,
                line=finding.line,
                column=finding.column,
                end_line=finding.end_line,
                end_column=finding.end_column,
                matched_text=finding.matched_text,
                category=finding.category,
            )
            for finding in structured_output.findings
        )
        summary = None
        if structured_output.summary is not None:
            summary = LLMReviewSummary(
                overall_risk=structured_output.summary.overall_risk,
                summary=structured_output.summary.summary,
                recommended_action=structured_output.summary.recommended_action,
                confidence=structured_output.summary.confidence,
            )
        return LLMReviewResult(
            provider=PYDANTICAI_OPENAI_PROVIDER_NAME,
            model=model,
            prompt_version=PYDANTICAI_OPENAI_PROMPT_VERSION,
            profile_name=request.profile_name,
            findings=findings,
            summary=summary,
            metadata=structured_output.metadata,
        )
    except ValidationError as exc:
        raise LLMResponseValidationError(
            "PydanticAI OpenAI provider returned invalid structured output."
        ) from exc


class PydanticAIOpenAIReviewer:
    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        base_url: str | None = None,
    ) -> None:
        self._model = _normalize_required_non_empty(model, field_name="model")
        self._api_key = _normalize_required_non_empty(api_key, field_name="api_key")
        self._base_url = _normalize_optional_non_empty(base_url, field_name="base_url")
        self._agent = _create_agent(
            model=self._model,
            api_key=self._api_key,
            base_url=self._base_url,
        )

    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        try:
            run_result = self._agent.run_sync(_build_user_prompt(request))
            return _map_output_to_llm_result(
                output=run_result.output,
                request=request,
                model=self._model,
            )
        except LLMResponseValidationError:
            raise
        except AgentRunError as exc:
            raise LLMProviderError(
                "PydanticAI OpenAI provider request failed."
            ) from exc
        except Exception as exc:
            raise LLMProviderError(
                "PydanticAI OpenAI provider request failed."
            ) from exc


__all__ = [
    "PYDANTICAI_OPENAI_PROMPT_VERSION",
    "PYDANTICAI_OPENAI_PROVIDER_NAME",
    "PydanticAIOpenAIReviewer",
]
