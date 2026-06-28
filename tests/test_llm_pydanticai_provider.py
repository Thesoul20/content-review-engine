from __future__ import annotations

import importlib
import socket
import sys
from typing import Any

import pytest

from content_review_engine.llm import (
    LLMProviderAuthError,
    LLMProviderConfig,
    LLMProviderConfigError,
    LLMProviderError,
    LLMProviderRuntimeError,
    LLMProviderTimeoutError,
    LLMProviderSecretError,
    LLMResponseValidationError,
    LLMReviewRequest,
    LLMReviewer,
    PydanticAIReviewMapper,
    PydanticAIReviewer,
)
from content_review_engine.llm.mock import MockLLMReviewer


def _build_request() -> LLMReviewRequest:
    return LLMReviewRequest(
        content="This article claims it is always safe.",
        profile_name="wechat-strict",
        content_path="articles/example.md",
        review_goal="semantic_review",
    )


def test_pydanticai_reviewer_satisfies_provider_protocol() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
            base_url="https://example.com/v1",
        )
    )

    assert isinstance(reviewer, LLMReviewer)


def test_pydanticai_review_raises_secret_error_without_secret(
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
        reviewer.review(_build_request())

    assert (
        str(exc_info.value)
        == "LLM API key environment variable 'CONTENT_REVIEW_TEST_LLM_API_KEY' is not set."
    )


def test_pydanticai_review_returns_empty_findings_with_fake_runtime() -> None:
    captured: dict[str, Any] = {}

    def fake_agent_builder(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return object()

    def fake_runtime_runner(agent, payload):  # type: ignore[no-untyped-def]
        assert agent is not None
        assert payload.prompt_version == "pydanticai-review-prompt.v1"
        return {"findings": []}

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            base_url="https://example.com/v1",
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=fake_agent_builder,
        runtime_runner=fake_runtime_runner,
    )

    result = reviewer.review(_build_request())

    assert result.provider == "pydanticai"
    assert result.model == "gpt-4o-mini"
    assert result.findings == ()
    assert captured["model"] == "gpt-4o-mini"
    assert captured["base_url"] == "https://example.com/v1"
    assert captured["timeout_seconds"] is None
    assert "test-secret-value" not in repr(captured["secret"])


def test_pydanticai_review_passes_timeout_to_runtime_agent() -> None:
    captured: dict[str, Any] = {}

    def fake_agent_builder(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return object()

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            timeout_seconds=12.5,
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=fake_agent_builder,
        runtime_runner=lambda _agent, _payload: {"findings": []},
    )

    reviewer.review(_build_request())

    assert captured["timeout_seconds"] == 12.5


def test_pydanticai_review_maps_single_finding_with_fake_runtime() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=lambda _agent, _payload: {
            "findings": [
                {
                    "rule_id": "llm_semantic_risk",
                    "severity": "warning",
                    "message": "The claim sounds absolute.",
                }
            ]
        },
    )

    result = reviewer.review(_build_request())

    assert len(result.findings) == 1
    assert result.findings[0].rule_id == "llm_semantic_risk"
    assert result.findings[0].severity == "warning"


def test_pydanticai_review_maps_multiple_findings_and_summary_with_fake_runtime() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=lambda _agent, _payload: {
            "findings": [
                {
                    "rule_id": "llm_semantic_risk",
                    "severity": "warning",
                    "message": "First finding.",
                },
                {
                    "rule_id": "llm_compliance_gap",
                    "severity": "error",
                    "message": "Second finding.",
                },
            ],
            "summary": {
                "overall_risk": "medium",
                "summary": "Two issues were detected.",
                "recommended_action": "Revise before publishing.",
                "confidence": 0.7,
            },
        },
    )

    result = reviewer.review(_build_request())

    assert [finding.rule_id for finding in result.findings] == [
        "llm_semantic_risk",
        "llm_compliance_gap",
    ]
    assert result.summary is not None
    assert result.summary.summary == "Two issues were detected."


def test_pydanticai_review_raises_response_validation_error_for_invalid_response() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=lambda _agent, _payload: {
            "findings": [{"rule_id": "x", "severity": "medium", "message": "bad"}]
        },
    )

    with pytest.raises(LLMResponseValidationError) as exc_info:
        reviewer.review(_build_request())

    message = str(exc_info.value)
    assert "findings.0.severity" in message
    assert "test-secret-value" not in message
    assert _build_request().content not in message


def test_pydanticai_review_converts_timeout_exception_to_provider_timeout_error() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=lambda _agent, _payload: (_ for _ in ()).throw(TimeoutError("hidden")),
    )

    with pytest.raises(LLMProviderTimeoutError) as exc_info:
        reviewer.review(_build_request())

    assert str(exc_info.value) == "PydanticAI runtime request timed out."
    assert _build_request().content not in str(exc_info.value)


def test_pydanticai_review_converts_unknown_runtime_exception_to_provider_runtime_error() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=lambda _agent, _payload: (_ for _ in ()).throw(
            RuntimeError("test-secret-value should stay hidden")
        ),
    )

    with pytest.raises(LLMProviderRuntimeError) as exc_info:
        reviewer.review(_build_request())

    assert str(exc_info.value) == "PydanticAI runtime call failed unexpectedly."
    assert "test-secret-value" not in str(exc_info.value)
    assert _build_request().content not in str(exc_info.value)


def test_pydanticai_review_converts_auth_runtime_exception_to_provider_auth_error() -> None:
    import httpx
    import openai

    request = httpx.Request("POST", "https://example.com/v1/chat/completions")
    response = httpx.Response(401, request=request, json={"error": {"message": "hidden"}})

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=lambda _agent, _payload: (_ for _ in ()).throw(
            openai.AuthenticationError(
                "hidden",
                response=response,
                body={"error": {"message": "hidden"}},
            )
        ),
    )

    with pytest.raises(LLMProviderAuthError) as exc_info:
        reviewer.review(_build_request())

    assert str(exc_info.value) == "PydanticAI runtime authentication failed."


def test_pydanticai_reviewer_only_stores_config_names() -> None:
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
    assert reviewer.timeout_seconds is None
    assert isinstance(reviewer.mapping, PydanticAIReviewMapper)


def test_pydanticai_reviewer_builds_request_payload_without_network() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
        )
    )

    payload = reviewer.build_request_payload(_build_request())

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


def test_pydanticai_review_does_not_make_network_calls_with_fake_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=lambda _agent, _payload: {"findings": []},
    )

    result = reviewer.review(_build_request())

    assert result.findings == ()


def test_pydanticai_review_does_not_fallback_to_mock() -> None:
    called = {"mock": False}

    def fail_mock_review(self, request):  # type: ignore[no-untyped-def]
        called["mock"] = True
        raise AssertionError("Mock reviewer should not be used for pydanticai.")

    original_review = MockLLMReviewer.review
    MockLLMReviewer.review = fail_mock_review  # type: ignore[assignment]

    try:
        reviewer = PydanticAIReviewer(
            LLMProviderConfig(
                provider="pydanticai",
                model="gpt-4o-mini",
                api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            ),
            secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
            agent_builder=lambda **kwargs: object(),
            runtime_runner=lambda _agent, _payload: {"findings": []},
        )

        result = reviewer.review(_build_request())

        assert result.findings == ()
        assert called["mock"] is False
    finally:
        MockLLMReviewer.review = original_review  # type: ignore[assignment]


def test_pydanticai_review_requires_model_to_be_configured() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=lambda _agent, _payload: {"findings": []},
    )

    with pytest.raises(LLMProviderConfigError) as exc_info:
        reviewer.review(_build_request())

    assert str(exc_info.value) == "LLM provider 'pydanticai' requires model to be configured."


def test_pydanticai_review_secret_resolution_redacts_secret() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
    )

    secret = reviewer.resolve_secret()

    assert secret.api_key_env == "CONTENT_REVIEW_TEST_LLM_API_KEY"
    assert "test-secret-value" not in repr(secret)
    assert secret.model_dump() == {"api_key_env": "CONTENT_REVIEW_TEST_LLM_API_KEY"}


def reviewer_secret(env_name: str):
    from content_review_engine.llm.secrets import ResolvedLLMSecret
    from pydantic import SecretStr

    return ResolvedLLMSecret(
        api_key_env=env_name,
        api_key=SecretStr("test-secret-value"),
    )
