from __future__ import annotations

import importlib
import os
import socket
import sys
from typing import Any

import pytest

from content_review_engine.llm import (
    LLMProviderAuthError,
    LLMProviderConfig,
    LLMProviderConfigError,
    LLMProviderError,
    LLMProviderModelError,
    LLMProviderNetworkError,
    LLMProviderRateLimitError,
    LLMProviderRetryExhaustedError,
    LLMProviderRuntimeError,
    LLMProviderTimeoutError,
    LLMProviderSecretError,
    LLMResponseValidationError,
    LLMSemanticReviewExecutionError,
    LLMSemanticReviewOutputParseError,
    LLMSemanticReviewOutputValidationError,
    LLMReviewRequest,
    LLMReviewResult,
    LLMReviewer,
    PYDANTICAI_LIVE_CHECK_PROMPT,
    PydanticAIReviewMapper,
    PydanticAIReviewer,
    ResolvedLLMSecret,
    ValidatedLLMSemanticReviewOutput,
    build_pydanticai_runtime_agent,
)
from pydantic import SecretStr
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


def reviewer_secret(api_key_env: str) -> ResolvedLLMSecret:
    return ResolvedLLMSecret(api_key_env=api_key_env, api_key=SecretStr("test-secret-value"))


def test_build_pydanticai_runtime_agent_disables_sdk_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_openai_kwargs: dict[str, Any] = {}

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured_openai_kwargs.update(kwargs)

    class FakeProvider:
        def __init__(self, *, openai_client: Any) -> None:
            self.openai_client = openai_client

    class FakeModel:
        def __init__(self, model_name: str, *, provider: Any) -> None:
            self.model_name = model_name
            self.provider = provider

    class FakeAgent:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

    monkeypatch.setattr("content_review_engine.llm.pydanticai.AsyncOpenAI", FakeAsyncOpenAI)
    monkeypatch.setattr("content_review_engine.llm.pydanticai.OpenAIProvider", FakeProvider)
    monkeypatch.setattr("content_review_engine.llm.pydanticai.OpenAIChatModel", FakeModel)

    agent = build_pydanticai_runtime_agent(
        model="openai:gpt-4o-mini",
        system_prompt="system prompt",
        secret=reviewer_secret("OPENAI_API_KEY"),
        base_url="https://example.com/v1",
        timeout_seconds=30.0,
        agent_type=FakeAgent,
    )

    assert isinstance(agent, FakeAgent)
    assert captured_openai_kwargs["max_retries"] == 0
    assert captured_openai_kwargs["timeout"] == 30.0
    assert captured_openai_kwargs["base_url"] == "https://example.com/v1"


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
        == "LLM provider secret environment variable 'CONTENT_REVIEW_TEST_LLM_API_KEY' is not set."
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


def test_pydanticai_review_passes_retry_config_to_reviewer_state() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            retry_attempts=2,
            retry_backoff_seconds=1.25,
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=lambda _agent, _payload: {"findings": []},
    )

    reviewer.review(_build_request())

    assert reviewer.retry_attempts == 2
    assert reviewer.retry_backoff_seconds == 1.25


def test_pydanticai_review_passes_min_request_interval_to_reviewer_state() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            min_request_interval_seconds=2.5,
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=lambda _agent, _payload: {"findings": []},
    )

    reviewer.review(_build_request())

    assert reviewer.min_request_interval_seconds == 2.5


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


def test_pydanticai_review_retries_timeout_then_succeeds() -> None:
    calls: list[int] = []
    sleep_calls: list[float] = []

    def fake_runtime_runner(_agent, _payload):  # type: ignore[no-untyped-def]
        calls.append(len(calls) + 1)
        if len(calls) == 1:
            raise TimeoutError("hidden")
        return {"findings": []}

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            retry_attempts=1,
            retry_backoff_seconds=0.25,
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=fake_runtime_runner,
        sleep_func=lambda seconds: sleep_calls.append(seconds),
    )

    result = reviewer.review(_build_request())

    assert result.findings == ()
    assert calls == [1, 2]
    assert sleep_calls == [0.25]


def test_pydanticai_review_retries_network_then_succeeds() -> None:
    import httpx

    sleep_calls: list[float] = []
    request = httpx.Request("POST", "https://example.com/v1/chat/completions")
    attempts = {"count": 0}

    def fake_runtime_runner(_agent, _payload):  # type: ignore[no-untyped-def]
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise httpx.ConnectError("hidden", request=request)
        return {"findings": []}

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            retry_attempts=1,
            retry_backoff_seconds=0.5,
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=fake_runtime_runner,
        sleep_func=lambda seconds: sleep_calls.append(seconds),
    )

    result = reviewer.review(_build_request())

    assert result.findings == ()
    assert attempts["count"] == 2
    assert sleep_calls == [0.5]


def test_pydanticai_review_retries_rate_limit_then_succeeds() -> None:
    import httpx
    import openai

    sleep_calls: list[float] = []
    response = httpx.Response(
        429,
        request=httpx.Request("POST", "https://example.com/v1/chat/completions"),
        json={"error": {"message": "hidden"}},
    )
    attempts = {"count": 0}

    def fake_runtime_runner(_agent, _payload):  # type: ignore[no-untyped-def]
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise openai.RateLimitError("hidden", response=response, body={"error": "hidden"})
        return {"findings": []}

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            retry_attempts=1,
            retry_backoff_seconds=0.75,
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=fake_runtime_runner,
        sleep_func=lambda seconds: sleep_calls.append(seconds),
    )

    result = reviewer.review(_build_request())

    assert result.findings == ()
    assert attempts["count"] == 2
    assert sleep_calls == [0.75]


def test_pydanticai_review_raises_retry_exhausted_after_retryable_failures() -> None:
    attempts = {"count": 0}
    sleep_calls: list[float] = []

    def fake_runtime_runner(_agent, _payload):  # type: ignore[no-untyped-def]
        attempts["count"] += 1
        raise TimeoutError("hidden")

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            retry_attempts=2,
            retry_backoff_seconds=1.0,
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=fake_runtime_runner,
        sleep_func=lambda seconds: sleep_calls.append(seconds),
    )

    with pytest.raises(LLMProviderRetryExhaustedError) as exc_info:
        reviewer.review(_build_request())

    assert (
        str(exc_info.value)
        == "PydanticAI runtime retry attempts exhausted after 3 attempts due to LLMProviderTimeoutError."
    )
    assert attempts["count"] == 3
    assert sleep_calls == [1.0, 1.0]
    assert "hidden" not in str(exc_info.value)
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


def test_pydanticai_review_does_not_retry_auth_error() -> None:
    import httpx
    import openai

    request = httpx.Request("POST", "https://example.com/v1/chat/completions")
    response = httpx.Response(401, request=request, json={"error": {"message": "hidden"}})
    attempts = {"count": 0}
    sleep_calls: list[float] = []

    def fake_runtime_runner(_agent, _payload):  # type: ignore[no-untyped-def]
        attempts["count"] += 1
        raise openai.AuthenticationError(
            "hidden",
            response=response,
            body={"error": {"message": "hidden"}},
        )

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            retry_attempts=3,
            retry_backoff_seconds=1.0,
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=fake_runtime_runner,
        sleep_func=lambda seconds: sleep_calls.append(seconds),
    )

    with pytest.raises(LLMProviderAuthError):
        reviewer.review(_build_request())

    assert attempts["count"] == 1
    assert sleep_calls == []


def test_pydanticai_review_does_not_retry_model_error() -> None:
    import httpx
    import openai

    request = httpx.Request("POST", "https://example.com/v1/chat/completions")
    response = httpx.Response(404, request=request, json={"error": {"message": "hidden"}})
    attempts = {"count": 0}

    def fake_runtime_runner(_agent, _payload):  # type: ignore[no-untyped-def]
        attempts["count"] += 1
        raise openai.NotFoundError(
            "hidden",
            response=response,
            body={"error": {"message": "hidden"}},
        )

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            retry_attempts=2,
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=fake_runtime_runner,
    )

    with pytest.raises(LLMProviderModelError):
        reviewer.review(_build_request())

    assert attempts["count"] == 1


def test_pydanticai_review_does_not_retry_response_validation_error() -> None:
    attempts = {"count": 0}

    def fake_runtime_runner(_agent, _payload):  # type: ignore[no-untyped-def]
        attempts["count"] += 1
        return {"findings": [{"rule_id": "x", "severity": "medium", "message": "bad"}]}

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            retry_attempts=2,
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=fake_runtime_runner,
    )

    with pytest.raises(LLMResponseValidationError):
        reviewer.review(_build_request())

    assert attempts["count"] == 1


def test_pydanticai_review_does_not_retry_secret_error() -> None:
    attempts = {"count": 0}

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            retry_attempts=2,
        ),
        secret_resolver=lambda _config: (_ for _ in ()).throw(
            LLMProviderSecretError("missing secret")
        ),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=lambda _agent, _payload: attempts.__setitem__("count", attempts["count"] + 1),
    )

    with pytest.raises(LLMProviderSecretError):
        reviewer.review(_build_request())

    assert attempts["count"] == 0


def test_pydanticai_review_does_not_retry_config_error() -> None:
    attempts = {"count": 0}

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            retry_attempts=2,
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **_kwargs: (_ for _ in ()).throw(
            LLMProviderConfigError("config invalid")
        ),
        runtime_runner=lambda _agent, _payload: attempts.__setitem__("count", attempts["count"] + 1),
    )

    with pytest.raises(LLMProviderConfigError):
        reviewer.review(_build_request())

    assert attempts["count"] == 0


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
    assert reviewer.retry_attempts == 0
    assert reviewer.retry_backoff_seconds == 0.0
    assert reviewer.min_request_interval_seconds == 0.0
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
            api_key_env="OPENAI_API_KEY",
        ),
        secret_resolver=lambda config: reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **_kwargs: object(),
        runtime_runner=lambda _agent, _payload: {"findings": []},
    )

    result = reviewer.review(_build_request())

    assert result.findings == ()


def test_pydanticai_semantic_review_uses_prompt_contract_and_output_validation() -> None:
    captured: dict[str, Any] = {}

    def fake_semantic_agent_builder(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return object()

    def fake_semantic_runtime_runner(agent, prompt):  # type: ignore[no-untyped-def]
        assert agent is not None
        captured["user_prompt"] = prompt
        return '{"schema_version":"llm-semantic-review-output.v1","summary":"发现一处风险。","findings":[{"rule_id":"llm.semantic.overclaim","severity":"warning","line":2,"column":1,"message":"表述过于绝对。","evidence":"always safe","suggestion":"改为更审慎的说法。","confidence":0.81}]}'

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            base_url="https://example.com/v1",
        ),
        resolved_secret=reviewer_secret("CONTENT_REVIEW_TEST_LLM_API_KEY"),
        semantic_agent_builder=fake_semantic_agent_builder,
        semantic_runtime_runner=fake_semantic_runtime_runner,
    )

    result = reviewer.run_semantic_review(_build_request())

    assert isinstance(result, ValidatedLLMSemanticReviewOutput)
    assert not isinstance(result, LLMReviewResult)
    assert result.summary == "发现一处风险。"
    assert result.findings[0].rule_id == "llm.semantic.overclaim"
    assert captured["model"] == "gpt-4o-mini"
    assert captured["base_url"] == "https://example.com/v1"
    assert captured["timeout_seconds"] is None
    assert "Return JSON only." in captured["system_prompt"]
    assert "articles/example.md" in captured["user_prompt"]
    assert "test-secret-value" not in captured["system_prompt"]
    assert "test-secret-value" not in captured["user_prompt"]


def test_pydanticai_semantic_review_accepts_fenced_json_output() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        resolved_secret=reviewer_secret("CONTENT_REVIEW_TEST_LLM_API_KEY"),
        semantic_agent_builder=lambda **_kwargs: object(),
        semantic_runtime_runner=lambda _agent, _prompt: """```json
{"schema_version":"llm-semantic-review-output.v1","summary":"无明显风险。","findings":[]}
```""",
    )

    result = reviewer.run_semantic_review(_build_request())

    assert result.summary == "无明显风险。"
    assert result.findings == ()


def test_pydanticai_semantic_review_parse_failure_preserves_parse_error() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        resolved_secret=reviewer_secret("CONTENT_REVIEW_TEST_LLM_API_KEY"),
        semantic_agent_builder=lambda **_kwargs: object(),
        semantic_runtime_runner=lambda _agent, _prompt: "not json sk-test-secret-1234567890",
    )

    with pytest.raises(LLMSemanticReviewOutputParseError) as exc_info:
        reviewer.run_semantic_review(_build_request())

    message = str(exc_info.value)
    assert message == "raw_output: invalid JSON at line 1 column 1"
    assert "test-secret-value" not in message
    assert "sk-test-secret-1234567890" not in message


def test_pydanticai_semantic_review_validation_failure_preserves_validation_error() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        resolved_secret=reviewer_secret("CONTENT_REVIEW_TEST_LLM_API_KEY"),
        semantic_agent_builder=lambda **_kwargs: object(),
        semantic_runtime_runner=lambda _agent, _prompt: '{"schema_version":"llm-semantic-review-output.v1","summary":"x","findings":[{"rule_id":"llm.semantic.overclaim","severity":"medium","message":"bad","evidence":"snippet","suggestion":"fix"}]}',
    )

    with pytest.raises(LLMSemanticReviewOutputValidationError) as exc_info:
        reviewer.run_semantic_review(_build_request())

    message = str(exc_info.value)
    assert message == "findings[0].severity: must be one of: info, warning, error, critical"
    assert "test-secret-value" not in message


def test_pydanticai_semantic_review_provider_execution_failure_raises_runtime_error() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        resolved_secret=reviewer_secret("CONTENT_REVIEW_TEST_LLM_API_KEY"),
        semantic_agent_builder=lambda **_kwargs: object(),
        semantic_runtime_runner=lambda _agent, _prompt: (_ for _ in ()).throw(
            RuntimeError("test-secret-value should stay hidden")
        ),
    )

    with pytest.raises(LLMProviderRuntimeError) as exc_info:
        reviewer.run_semantic_review(_build_request())

    message = str(exc_info.value)
    assert message == "PydanticAI runtime call failed unexpectedly."
    assert "test-secret-value" not in message
    assert _build_request().content not in message


def test_pydanticai_semantic_review_rejects_non_text_runtime_output() -> None:
    class FakeResult:
        status = "ok"

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        resolved_secret=reviewer_secret("CONTENT_REVIEW_TEST_LLM_API_KEY"),
        semantic_agent_builder=lambda **_kwargs: object(),
        semantic_runtime_runner=lambda _agent, _prompt: FakeResult(),
    )

    with pytest.raises(LLMSemanticReviewExecutionError) as exc_info:
        reviewer.run_semantic_review(_build_request())

    assert str(exc_info.value) == "PydanticAI semantic review did not return text output."


def test_pydanticai_semantic_review_does_not_read_environment_variables_when_secret_is_pre_resolved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_getenv(*args: object, **kwargs: object) -> str:
        raise AssertionError("semantic review should not read environment variables")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        resolved_secret=reviewer_secret("CONTENT_REVIEW_TEST_LLM_API_KEY"),
        semantic_agent_builder=lambda **_kwargs: object(),
        semantic_runtime_runner=lambda _agent, _prompt: '{"schema_version":"llm-semantic-review-output.v1","summary":"ok","findings":[]}',
    )

    result = reviewer.run_semantic_review(_build_request())

    assert result.summary == "ok"


def test_pydanticai_semantic_review_does_not_make_network_calls_with_fake_runtime(
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
        resolved_secret=reviewer_secret("CONTENT_REVIEW_TEST_LLM_API_KEY"),
        semantic_agent_builder=lambda **_kwargs: object(),
        semantic_runtime_runner=lambda _agent, _prompt: '{"schema_version":"llm-semantic-review-output.v1","summary":"ok","findings":[]}',
    )

    result = reviewer.run_semantic_review(_build_request())

    assert result.findings == ()


def test_pydanticai_semantic_review_is_separate_from_construction_and_live_checks() -> None:
    state = {"construction": 0, "semantic": 0}

    def fake_agent_builder(**_kwargs):  # type: ignore[no-untyped-def]
        state["construction"] += 1
        return object()

    def fake_semantic_agent_builder(**_kwargs):  # type: ignore[no-untyped-def]
        state["semantic"] += 1
        return object()

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        resolved_secret=reviewer_secret("CONTENT_REVIEW_TEST_LLM_API_KEY"),
        agent_builder=fake_agent_builder,
        semantic_agent_builder=fake_semantic_agent_builder,
        semantic_runtime_runner=lambda _agent, _prompt: '{"schema_version":"llm-semantic-review-output.v1","summary":"ok","findings":[]}',
    )

    reviewer.run_construction_check()
    assert state == {"construction": 1, "semantic": 0}

    reviewer.run_semantic_review(_build_request())
    assert state == {"construction": 1, "semantic": 1}

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


def test_pydanticai_construction_check_uses_pre_resolved_secret_without_env_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_secret_resolver(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected secret resolution: {args!r} {kwargs!r}")

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="openai:gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        resolved_secret=reviewer_secret("CONTENT_REVIEW_TEST_LLM_API_KEY"),
        secret_resolver=fail_secret_resolver,
    )

    reviewer.run_construction_check()


def test_pydanticai_construction_check_does_not_access_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="openai:gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        resolved_secret=reviewer_secret("CONTENT_REVIEW_TEST_LLM_API_KEY"),
    )

    reviewer.run_construction_check()


def test_pydanticai_live_check_uses_pre_resolved_secret_without_env_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_secret_resolver(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected secret resolution: {args!r} {kwargs!r}")

    captured: dict[str, object] = {}

    def fake_build_live_agent(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return object()

    def fake_run_live_agent(agent, prompt):  # type: ignore[no-untyped-def]
        captured["agent"] = agent
        captured["prompt"] = prompt
        return "ok"

    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.build_pydanticai_live_check_agent",
        fake_build_live_agent,
    )
    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.run_pydanticai_live_check_agent",
        fake_run_live_agent,
    )

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="openai:gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            base_url="https://example.com/v1",
            timeout_seconds=12.5,
        ),
        resolved_secret=reviewer_secret("CONTENT_REVIEW_TEST_LLM_API_KEY"),
        secret_resolver=fail_secret_resolver,
    )

    reviewer.run_live_check()

    assert captured["model"] == "gpt-4o-mini"
    assert captured["base_url"] == "https://example.com/v1"
    assert captured["timeout_seconds"] == 12.5
    assert captured["prompt"] == PYDANTICAI_LIVE_CHECK_PROMPT
    assert "test-secret-value" not in repr(captured["secret"])


def test_pydanticai_live_check_rejects_empty_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="openai:gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
        ),
        resolved_secret=reviewer_secret("CONTENT_REVIEW_TEST_LLM_API_KEY"),
    )

    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.build_pydanticai_live_check_agent",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.run_pydanticai_live_check_agent",
        lambda agent, prompt: "",
    )

    with pytest.raises(LLMProviderRuntimeError) as exc_info:
        reviewer.run_live_check()

    assert str(exc_info.value) == "PydanticAI live smoke check returned an empty response."
