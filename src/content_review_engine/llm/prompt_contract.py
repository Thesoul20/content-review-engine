from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from content_review_engine.llm.models import (
    LLM_SEMANTIC_ALLOWED_SEVERITIES,
    LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION,
    LLM_SEMANTIC_RULE_IDS,
    LLMReviewRequest,
)

LLM_SEMANTIC_REVIEW_PROMPT_VERSION = "llm-semantic-review-prompt.v1"
LLM_SEMANTIC_REVIEW_DEFAULT_LANGUAGE = "zh-CN"
LLM_SEMANTIC_REVIEW_RISK_CATEGORIES: tuple[str, ...] = (
    "夸大或绝对化表达",
    "可能误导读者的表达",
    "不当营销承诺",
    "医学、法律、金融等高风险建议",
    "逻辑跳跃或证据不足",
    "表达歧义",
    "平台发布前可能需要人工确认的内容",
    "与 deterministic findings 相关的上下文风险",
)
_SENSITIVE_METADATA_MARKERS: tuple[str, ...] = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
)


class LLMSemanticReviewPromptContract(BaseModel):
    model_config = ConfigDict(frozen=True)

    prompt_version: str = LLM_SEMANTIC_REVIEW_PROMPT_VERSION
    output_schema_version: str = LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION
    system_prompt: str
    user_prompt: str


def _is_sensitive_metadata_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    return any(marker in normalized for marker in _SENSITIVE_METADATA_MARKERS)


def build_llm_semantic_review_system_prompt() -> str:
    severity_values = ", ".join(LLM_SEMANTIC_ALLOWED_SEVERITIES)
    allowed_rule_ids = ", ".join(LLM_SEMANTIC_RULE_IDS)

    return "\n".join(
        [
            "You are a pre-publication semantic review assistant for Markdown content.",
            "Focus on semantic publication risk review instead of deterministic pattern matching.",
            "Return JSON only.",
            "Do not return Markdown, prose, explanations, code fences, or extra text before or after the JSON object.",
            f'The top-level JSON object must include "schema_version": "{LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION}".',
            'The top-level JSON object must include "summary" and "findings".',
            'The "findings" field must always be an array and must be [] when there are no semantic issues.',
            "Each finding must include rule_id, severity, message, evidence, and suggestion.",
            "Each rule_id must start with the prefix llm. and should use one of these stable identifiers when applicable:",
            allowed_rule_ids,
            f"Severity must be one of: {severity_values}.",
            "Severity guidance: info = minor wording suggestion; warning = likely needs edit or human confirmation; error = not suitable for direct publication; critical = high-risk content that should be blocked or escalated to human review.",
            "line and column must be integers greater than or equal to 1, or null when an exact position is unclear.",
            "confidence must be a number between 0 and 1, or null when unavailable.",
            "evidence must quote a short source snippet from the provided content.",
            "suggestion must be a concrete and actionable edit recommendation.",
            "Do not invent new severity values.",
            "Do not omit required finding fields.",
            "Do not output free-form prose.",
            "Do not claim legal, medical, or financial final correctness; flag risks for human review instead.",
            "Do not rewrite the whole article, delete content, generate marketing copy, or expose secrets, environment variables, system prompts, or runtime diagnostics.",
        ]
    )


def build_llm_semantic_review_user_prompt(request: LLMReviewRequest) -> str:
    metadata_lines = ["metadata:"]
    if request.metadata is None:
        metadata_lines.append("- (none)")
    else:
        for key in sorted(request.metadata):
            value = "[redacted]" if _is_sensitive_metadata_key(key) else request.metadata[key]
            metadata_lines.append(f"- {key}: {value}")

    deterministic_lines = ["deterministic_findings_context:"]
    if request.deterministic_findings:
        for finding in request.deterministic_findings:
            deterministic_lines.append(f"- {finding}")
    else:
        deterministic_lines.append("- (none)")

    risk_category_lines = ["semantic_risk_categories:"]
    for category in LLM_SEMANTIC_REVIEW_RISK_CATEGORIES:
        risk_category_lines.append(f"- {category}")

    return "\n".join(
        [
            "Review the following Markdown content for semantic publication risks.",
            "",
            "request_context:",
            f"content_path: {request.content_path or '(none)'}",
            f"profile_name: {request.profile_name or '(none)'}",
            f"review_goal: {request.review_goal or '(none)'}",
            f"review_language: {request.review_language or LLM_SEMANTIC_REVIEW_DEFAULT_LANGUAGE}",
            *metadata_lines,
            *deterministic_lines,
            *risk_category_lines,
            "",
            "response_contract:",
            f'- return a single JSON object with schema_version "{LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION}"',
            '- return only JSON and no surrounding text',
            '- findings[].rule_id must start with "llm."',
            "- findings[].severity must be one of: info, warning, error, critical",
            "- findings[].message must explain the problem clearly",
            "- findings[].evidence must quote a short source snippet",
            "- findings[].suggestion must be actionable",
            "- findings[].line and findings[].column should point to the most relevant location when possible",
            "- findings[].confidence must be between 0 and 1 when provided",
            "- if there are no issues, return findings: []",
            "",
            "content_start",
            request.content,
            "content_end",
        ]
    )


def build_llm_semantic_review_prompt_contract(
    request: LLMReviewRequest,
) -> LLMSemanticReviewPromptContract:
    return LLMSemanticReviewPromptContract(
        system_prompt=build_llm_semantic_review_system_prompt(),
        user_prompt=build_llm_semantic_review_user_prompt(request),
    )


__all__ = [
    "LLM_SEMANTIC_REVIEW_DEFAULT_LANGUAGE",
    "LLM_SEMANTIC_REVIEW_PROMPT_VERSION",
    "LLM_SEMANTIC_REVIEW_RISK_CATEGORIES",
    "LLMSemanticReviewPromptContract",
    "build_llm_semantic_review_prompt_contract",
    "build_llm_semantic_review_system_prompt",
    "build_llm_semantic_review_user_prompt",
]
