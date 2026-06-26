from __future__ import annotations

from types import SimpleNamespace

import pytest

from content_review_engine.llm import (
    LLMProviderError,
    LLMResponseValidationError,
    LLMReviewRequest,
    LLMReviewer,
    PydanticAIOpenAIReviewer,
)


class FakeAgent:
    def __init__(self, output=None, error: Exception | None = None) -> None:
        self.output = output
        self.error = error
        self.prompts: list[str] = []

    def run_sync(self, prompt: str) -> SimpleNamespace:
        self.prompts.append(prompt)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(output=self.output)


def test_pydanticai_reviewer_satisfies_provider_protocol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_agent = FakeAgent(output={"findings": []})
    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai._create_agent",
        lambda **kwargs: fake_agent,
    )

    reviewer = PydanticAIOpenAIReviewer(model="gpt-4o-mini", api_key="secret-key")

    assert isinstance(reviewer, LLMReviewer)


def test_pydanticai_reviewer_maps_empty_structured_output_to_llm_review_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_agent = FakeAgent(
        output={
            "findings": [],
            "summary": {
                "overall_risk": "low",
                "summary": "No semantic issues found.",
                "recommended_action": "Proceed.",
                "confidence": 0.8,
            },
            "metadata": {"source": "fake-agent"},
        }
    )
    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai._create_agent",
        lambda **kwargs: fake_agent,
    )
    reviewer = PydanticAIOpenAIReviewer(model="gpt-4o-mini", api_key="secret-key")

    result = reviewer.review(
        LLMReviewRequest(
            content="Semantic review content.",
            profile_name="default",
            content_path="article.md",
            review_goal="semantic_review",
        )
    )

    assert result.schema_version == "llm-review-result.v1"
    assert result.provider == "pydanticai-openai"
    assert result.model == "gpt-4o-mini"
    assert result.prompt_version == "pydanticai-openai.v1"
    assert result.profile_name == "default"
    assert result.findings == ()
    assert result.summary is not None
    assert result.summary.overall_risk == "low"
    assert result.metadata == {"source": "fake-agent"}
    assert "Semantic review content." in fake_agent.prompts[0]


def test_pydanticai_reviewer_maps_findings_to_llm_review_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_agent = FakeAgent(
        output={
            "findings": [
                {
                    "rule_id": "llm_semantic_risk",
                    "severity": "warning",
                    "message": "Possible unsupported claim.",
                    "suggestion": "Add evidence.",
                    "rationale": "The wording is absolute.",
                    "confidence": 0.9,
                    "line": 3,
                    "column": 2,
                    "end_line": 3,
                    "end_column": 8,
                    "matched_text": "绝对有效",
                    "category": "claim",
                }
            ]
        }
    )
    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai._create_agent",
        lambda **kwargs: fake_agent,
    )
    reviewer = PydanticAIOpenAIReviewer(model="gpt-4o-mini", api_key="secret-key")

    result = reviewer.review(LLMReviewRequest(content="Finding content."))

    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.rule_id == "llm_semantic_risk"
    assert finding.severity == "warning"
    assert finding.message == "Possible unsupported claim."
    assert finding.suggestion == "Add evidence."
    assert finding.rationale == "The wording is absolute."
    assert finding.confidence == 0.9
    assert finding.line == 3
    assert finding.column == 2
    assert finding.end_line == 3
    assert finding.end_column == 8
    assert finding.matched_text == "绝对有效"
    assert finding.category == "claim"


def test_pydanticai_reviewer_maps_provider_failures_to_llm_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_key = "super-secret-key"
    fake_agent = FakeAgent(error=RuntimeError(f"request failed for key {api_key}"))
    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai._create_agent",
        lambda **kwargs: fake_agent,
    )
    reviewer = PydanticAIOpenAIReviewer(model="gpt-4o-mini", api_key=api_key)

    with pytest.raises(LLMProviderError) as exc_info:
        reviewer.review(LLMReviewRequest(content="Provider failure content."))

    assert str(exc_info.value) == "PydanticAI OpenAI provider request failed."
    assert api_key not in str(exc_info.value)


def test_pydanticai_reviewer_maps_output_validation_failures_to_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_agent = FakeAgent(
        output={
            "findings": [
                {
                    "rule_id": "llm_semantic_risk",
                    "severity": "bad-severity",
                    "message": "Invalid severity from provider.",
                }
            ]
        }
    )
    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai._create_agent",
        lambda **kwargs: fake_agent,
    )
    reviewer = PydanticAIOpenAIReviewer(model="gpt-4o-mini", api_key="secret-key")

    with pytest.raises(LLMResponseValidationError) as exc_info:
        reviewer.review(LLMReviewRequest(content="Validation failure content."))

    assert (
        str(exc_info.value)
        == "PydanticAI OpenAI provider returned invalid structured output."
    )

