from __future__ import annotations

import os
import socket

import pytest

from content_review_engine.llm import (
    LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION,
    LLM_SEMANTIC_RULE_IDS,
    LLMReviewRequest,
    build_llm_semantic_review_prompt_contract,
    build_llm_semantic_review_system_prompt,
    build_llm_semantic_review_user_prompt,
)


def build_request(**overrides: object) -> LLMReviewRequest:
    base_request: dict[str, object] = {
        "content": "本产品绝对安全，三天内保证见效。",
        "profile_name": "wechat-strict",
        "content_path": "articles/launch.md",
        "review_goal": "semantic_review",
        "metadata": {
            "channel": "wechat",
            "api_key": "super-secret-value",
        },
    }
    base_request.update(overrides)
    return LLMReviewRequest(**base_request)


def test_build_prompt_contract_from_llm_review_request() -> None:
    contract = build_llm_semantic_review_prompt_contract(build_request())

    assert contract.prompt_version == "llm-semantic-review-prompt.v1"
    assert contract.output_schema_version == LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION
    assert contract.system_prompt == build_llm_semantic_review_system_prompt()
    assert contract.user_prompt == build_llm_semantic_review_user_prompt(build_request())


def test_system_prompt_contains_json_only_output_contract() -> None:
    prompt = build_llm_semantic_review_system_prompt()

    assert "Return JSON only." in prompt
    assert "Do not return Markdown, prose, explanations, code fences" in prompt
    assert LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION in prompt
    assert "Severity must be one of: info, warning, error, critical." in prompt
    assert "Each rule_id must start with the prefix llm." in prompt
    assert "Do not output free-form prose." in prompt
    for rule_id in LLM_SEMANTIC_RULE_IDS:
        assert rule_id in prompt


def test_user_prompt_contains_content_file_profile_and_risk_categories() -> None:
    prompt = build_llm_semantic_review_user_prompt(build_request())

    assert "content_path: articles/launch.md" in prompt
    assert "profile_name: wechat-strict" in prompt
    assert "review_language: zh-CN" in prompt
    assert "本产品绝对安全，三天内保证见效。" in prompt
    assert "夸大或绝对化表达" in prompt
    assert "医学、法律、金融等高风险建议" in prompt


def test_user_prompt_redacts_secret_like_metadata_values() -> None:
    prompt = build_llm_semantic_review_user_prompt(build_request())

    assert "super-secret-value" not in prompt
    assert "- api_key: [redacted]" in prompt
    assert "- channel: wechat" in prompt


def test_prompt_builder_is_stable_with_empty_deterministic_findings() -> None:
    request = build_request(deterministic_findings=())

    first = build_llm_semantic_review_prompt_contract(request)
    second = build_llm_semantic_review_prompt_contract(request)

    assert first == second
    assert "deterministic_findings_context:\n- (none)" in first.user_prompt


def test_user_prompt_injects_deterministic_findings_context() -> None:
    request = build_request(
        deterministic_findings=(
            "absolute_claims:error: line 3 contains '绝对'",
            "forbidden_terms:warning: line 5 contains '最强'",
        )
    )

    prompt = build_llm_semantic_review_user_prompt(request)

    assert "- absolute_claims:error: line 3 contains '绝对'" in prompt
    assert "- forbidden_terms:warning: line 5 contains '最强'" in prompt


def test_prompt_builder_does_not_read_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_getenv(*args: object, **kwargs: object) -> str:
        raise AssertionError("prompt builder should not read environment variables")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    contract = build_llm_semantic_review_prompt_contract(build_request())

    assert contract.output_schema_version == LLM_SEMANTIC_REVIEW_OUTPUT_SCHEMA_VERSION


def test_prompt_builder_does_not_access_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*args: object, **kwargs: object) -> socket.socket:
        raise AssertionError("prompt builder should not access the network")

    monkeypatch.setattr(socket, "create_connection", fail_network)

    prompt = build_llm_semantic_review_user_prompt(build_request())

    assert "response_contract:" in prompt
