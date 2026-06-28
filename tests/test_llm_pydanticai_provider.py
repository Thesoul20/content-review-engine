from __future__ import annotations

import importlib
import socket
import sys

import pytest

from content_review_engine.llm import (
    LLMProviderConfig,
    LLMProviderNotImplementedError,
    LLMProviderSecretError,
    LLMReviewRequest,
    LLMReviewer,
    PydanticAIReviewMapper,
    PydanticAIReviewer,
    PYDANTICAI_NOT_IMPLEMENTED_MESSAGE,
)


def test_pydanticai_skeleton_satisfies_provider_protocol() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
            base_url="https://example.com/v1",
        )
    )

    assert isinstance(reviewer, LLMReviewer)


def test_pydanticai_skeleton_review_raises_secret_error_without_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CONTENT_REVIEW_TEST_LLM_API_KEY", raising=False)
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        )
    )

    with pytest.raises(LLMProviderSecretError) as exc_info:
        reviewer.review(LLMReviewRequest(content="Future provider skeleton request."))

    assert (
        str(exc_info.value)
        == "LLM API key environment variable 'CONTENT_REVIEW_TEST_LLM_API_KEY' is not set."
    )


def test_pydanticai_skeleton_review_still_raises_not_implemented_with_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONTENT_REVIEW_TEST_LLM_API_KEY", "test-secret-value")
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            base_url="https://example.com/v1",
        )
    )

    with pytest.raises(LLMProviderNotImplementedError) as exc_info:
        reviewer.review(LLMReviewRequest(content="Future provider skeleton request."))

    assert str(exc_info.value) == PYDANTICAI_NOT_IMPLEMENTED_MESSAGE
    assert "test-secret-value" not in str(exc_info.value)


def test_pydanticai_skeleton_only_stores_config_names() -> None:
    config = LLMProviderConfig(
        provider="pydanticai",
        model="gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        base_url="https://example.com/v1",
    )
    reviewer = PydanticAIReviewer(config)

    assert reviewer.config is config
    assert reviewer.model == "gpt-4o-mini"
    assert reviewer.api_key_env == "OPENAI_API_KEY"
    assert reviewer.base_url == "https://example.com/v1"
    assert isinstance(reviewer.mapping, PydanticAIReviewMapper)


def test_pydanticai_skeleton_builds_request_payload_without_network() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
        )
    )

    payload = reviewer.build_request_payload(
        LLMReviewRequest(
            content="This content says it is always safe.",
            profile_name="wechat-strict",
            content_path="articles/example.md",
            review_goal="semantic_review",
        )
    )

    assert payload.prompt_version == "pydanticai-review-prompt.v1"
    assert "Severity must be one of: info, warning, error, critical." in payload.system_prompt
    assert "articles/example.md" in payload.user_prompt
    assert "findings: []" in payload.user_prompt


def test_pydanticai_module_can_import_sdk_dependency() -> None:
    sys.modules.pop("content_review_engine.llm", None)
    sys.modules.pop("content_review_engine.llm.pydanticai", None)

    module = importlib.import_module("content_review_engine.llm.pydanticai")
    reviewer = module.PydanticAIReviewer(
        module.LLMProviderConfig(provider="pydanticai")
    )

    assert reviewer._agent_type.__name__ == "Agent"


def test_pydanticai_skeleton_does_not_make_network_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)
    monkeypatch.setenv("CONTENT_REVIEW_TEST_LLM_API_KEY", "test-secret-value")
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        )
    )

    with pytest.raises(LLMProviderNotImplementedError):
        reviewer.review(LLMReviewRequest(content="No network should happen."))


def test_pydanticai_skeleton_secret_resolution_redacts_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONTENT_REVIEW_TEST_LLM_API_KEY", "test-secret-value")
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        )
    )

    secret = reviewer.resolve_secret()

    assert secret.api_key_env == "CONTENT_REVIEW_TEST_LLM_API_KEY"
    assert "test-secret-value" not in repr(secret)
    assert secret.model_dump() == {"api_key_env": "CONTENT_REVIEW_TEST_LLM_API_KEY"}
