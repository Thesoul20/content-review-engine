from __future__ import annotations

from content_review_engine.llm.models import (
    LLMReviewFinding,
    LLMReviewRequest,
    LLMReviewResult,
    LLMReviewSummary,
    ValidatedLLMSemanticReviewOutput,
)
from content_review_engine.llm.prompt_contract import (
    LLM_SEMANTIC_REVIEW_PROMPT_VERSION,
)

LLM_SEMANTIC_OUTPUT_SCHEMA_METADATA_KEY = "semantic_output_schema_version"


def convert_validated_semantic_output_to_llm_review_result(
    output: ValidatedLLMSemanticReviewOutput,
    request: LLMReviewRequest,
    *,
    provider: str | None = None,
    model: str | None = None,
) -> LLMReviewResult:
    findings = tuple(
        LLMReviewFinding(
            rule_id=finding.rule_id,
            severity=finding.severity,
            message=finding.message,
            suggestion=finding.suggestion,
            confidence=finding.confidence,
            line=finding.line,
            column=finding.column,
            matched_text=finding.evidence,
        )
        for finding in output.findings
    )

    return LLMReviewResult(
        provider=provider,
        model=model,
        prompt_version=LLM_SEMANTIC_REVIEW_PROMPT_VERSION,
        profile_name=request.profile_name,
        findings=findings,
        summary=LLMReviewSummary(summary=output.summary),
        metadata={
            LLM_SEMANTIC_OUTPUT_SCHEMA_METADATA_KEY: output.schema_version,
        },
    )


__all__ = [
    "LLM_SEMANTIC_OUTPUT_SCHEMA_METADATA_KEY",
    "convert_validated_semantic_output_to_llm_review_result",
]
