import pytest

from content_review_engine.llm import (
    LLMProviderError,
    LLMReviewFinding,
    LLMReviewRequest,
    LLMReviewResult,
    LLMReviewRunner,
    LLMReviewSummary,
    MockLLMReviewer,
    ValidatedLLMSemanticReviewOutput,
    run_single_file_llm_review,
)


class RecordingReviewer:
    def __init__(self, result: LLMReviewResult) -> None:
        self.result = result
        self.calls: list[LLMReviewRequest] = []

    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        self.calls.append(request)
        return self.result


class FailingReviewer:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def review(self, request: LLMReviewRequest) -> LLMReviewResult:
        del request
        raise self.error


class SemanticReviewer:
    def __init__(self) -> None:
        self.model = "openai:gpt-4o-mini"
        self.calls: list[LLMReviewRequest] = []

    def run_semantic_review(
        self,
        request: LLMReviewRequest,
    ) -> ValidatedLLMSemanticReviewOutput:
        self.calls.append(request)
        return ValidatedLLMSemanticReviewOutput.model_validate(
            {
                "schema_version": "llm-semantic-review-output.v1",
                "summary": "One issue.",
                "findings": [
                    {
                        "rule_id": "llm.semantic.overclaim",
                        "severity": "warning",
                        "line": 3,
                        "column": 2,
                        "message": "Possible overclaim.",
                        "evidence": "always safe",
                        "suggestion": "Use more cautious wording.",
                        "confidence": 0.81,
                    }
                ],
            }
        )


def test_llm_review_runner_calls_reviewer_and_returns_result() -> None:
    request = LLMReviewRequest(
        content="Review this article semantically.",
        profile_name="semantic-risk",
    )
    expected_result = LLMReviewResult(
        provider="fake",
        model="recording-reviewer",
        findings=(
            LLMReviewFinding(
                rule_id="llm_semantic_risk",
                severity="warning",
                message="Possible unsupported claim.",
            ),
        ),
    )
    reviewer = RecordingReviewer(result=expected_result)
    runner = LLMReviewRunner(reviewer=reviewer)

    result = runner.run(request)

    assert result is expected_result
    assert reviewer.calls == [request]


def test_llm_review_runner_returns_configured_mock_result() -> None:
    configured_result = LLMReviewResult(
        provider="mock",
        model="deterministic-mock",
        findings=(
            LLMReviewFinding(
                rule_id="llm_semantic_risk",
                severity="error",
                message="This needs evidence.",
            ),
        ),
        summary=LLMReviewSummary(
            overall_risk="high",
            summary="Mock reviewer returned one configured finding.",
        ),
    )
    runner = LLMReviewRunner(reviewer=MockLLMReviewer(result=configured_result))

    result = runner.run(LLMReviewRequest(content="Configured runner request."))

    assert result is configured_result


def test_llm_review_runner_returns_empty_result_for_default_mock_reviewer() -> None:
    runner = LLMReviewRunner(reviewer=MockLLMReviewer())

    result = runner.run(LLMReviewRequest(content="Default runner request."))

    assert result == LLMReviewResult()
    assert result.findings == ()


def test_llm_review_runner_preserves_llm_result_schema_version() -> None:
    runner = LLMReviewRunner(reviewer=MockLLMReviewer())

    result = runner.run(LLMReviewRequest(content="Schema version request."))

    assert result.schema_version == "llm-review-result.v1"


def test_llm_review_runner_propagates_provider_errors() -> None:
    expected_error = LLMProviderError("provider failed")
    runner = LLMReviewRunner(reviewer=FailingReviewer(error=expected_error))

    with pytest.raises(LLMProviderError) as exc_info:
        runner.run(LLMReviewRequest(content="Failure request."))

    assert exc_info.value is expected_error


def test_run_single_file_llm_review_uses_semantic_pipeline_when_available() -> None:
    reviewer = SemanticReviewer()
    request = LLMReviewRequest(
        content="This article says the method is always safe.",
        profile_name="semantic-risk",
        content_path="articles/example.md",
        review_goal="semantic_review",
    )

    result = run_single_file_llm_review(
        request,
        reviewer=reviewer,  # type: ignore[arg-type]
        provider="pydanticai",
    )

    assert reviewer.calls == [request]
    assert result.provider == "pydanticai"
    assert result.model == "openai:gpt-4o-mini"
    assert result.findings[0].rule_id == "llm.semantic.overclaim"
    assert result.findings[0].matched_text == "always safe"
