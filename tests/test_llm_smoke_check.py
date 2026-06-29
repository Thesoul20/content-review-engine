from __future__ import annotations

import socket

import pytest

from content_review_engine.llm import (
    EmptyLLMProviderSecretEnvironmentVariableError,
    LLMProviderConfig,
    LLMProviderRuntimeError,
    LLMReviewResult,
    MissingLLMProviderSecretEnvironmentVariableError,
    MissingLLMProviderSecretReferenceError,
    PydanticAIReviewer,
    PydanticAITestModelReviewer,
    REDACTED_SECRET_TEXT,
    ResolvedLLMSecret,
    build_llm_smoke_check_request,
    render_llm_smoke_check_result,
    run_llm_smoke_check,
)
from pydantic import SecretStr


def _reviewer_secret(api_key_env: str) -> ResolvedLLMSecret:
    return ResolvedLLMSecret(
        api_key_env=api_key_env,
        api_key=SecretStr("test-secret-value"),
    )


def test_build_llm_smoke_check_request_uses_synthetic_minimal_content() -> None:
    request = build_llm_smoke_check_request()

    assert request.content == "LLM smoke check synthetic request."
    assert request.profile_name == "llm-check"
    assert request.content_path == "<llm-check>"
    assert request.review_goal == "smoke_check"
    assert request.metadata == {"mode": "smoke_check"}


def test_run_llm_smoke_check_mock_config_only_succeeds() -> None:
    result = run_llm_smoke_check(LLMProviderConfig(provider="mock"))

    assert result.provider == "mock"
    assert result.model is None
    assert result.config_status == "ok"
    assert result.secret_status == "not_required"
    assert result.api_key_env is None
    assert result.redacted_secret is None
    assert result.runtime_status == "skipped"


def test_run_llm_smoke_check_mock_runtime_succeeds_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    result = run_llm_smoke_check(LLMProviderConfig(provider="mock"), runtime=True)

    assert result.provider == "mock"
    assert result.secret_status == "not_required"
    assert result.runtime_status == "ok"


def test_run_llm_smoke_check_provider_mode_uses_factory_name_and_testmodel_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from content_review_engine.llm import smoke_check as module

    captured_provider: dict[str, str] = {}

    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    def fake_create_llm_reviewer(provider):  # type: ignore[no-untyped-def]
        captured_provider["value"] = provider
        return PydanticAITestModelReviewer()

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)
    monkeypatch.setattr(module, "create_llm_reviewer", fake_create_llm_reviewer)

    result = run_llm_smoke_check(
        LLMProviderConfig(provider="mock"),
        runtime=True,
        reviewer_provider="pydantic-ai-testmodel",
    )

    assert captured_provider == {"value": "pydantic-ai-testmodel"}
    assert result.provider == "pydantic-ai-testmodel"
    assert result.secret_status == "not_required"
    assert result.runtime_status == "ok"


def test_run_llm_smoke_check_pydanticai_secret_present_without_runtime_resolves_secret_without_calling_review() -> None:
    review_called = {"value": False}

    class GuardedReviewer:
        def review(self, request):  # type: ignore[no-untyped-def]
            del request
            review_called["value"] = True
            return LLMReviewResult()

    from content_review_engine.llm import smoke_check as module

    original_factory = module.create_llm_reviewer
    module.create_llm_reviewer = lambda config: GuardedReviewer()  # type: ignore[assignment]
    try:
        result = run_llm_smoke_check(
            LLMProviderConfig(
                provider="pydanticai",
                model="openai:gpt-4o-mini",
                api_key_env="OPENAI_API_KEY",
            ),
            runtime=False,
            env={"OPENAI_API_KEY": "test-secret-value"},
        )
    finally:
        module.create_llm_reviewer = original_factory  # type: ignore[assignment]

    assert result.secret_status == "resolved"
    assert result.api_key_env == "OPENAI_API_KEY"
    assert result.redacted_secret == REDACTED_SECRET_TEXT
    assert result.runtime_status == "skipped"
    assert review_called["value"] is False


def test_run_llm_smoke_check_pydanticai_runtime_success_with_fake_runtime() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="openai:gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
        ),
        secret_resolver=lambda config: _reviewer_secret(config.api_key_env or "missing"),
        runtime_runner=lambda _agent, _payload: {"findings": []},
    )

    from content_review_engine.llm import smoke_check as module

    original_factory = module.create_llm_reviewer
    module.create_llm_reviewer = lambda config: reviewer  # type: ignore[assignment]
    try:
        result = run_llm_smoke_check(
            reviewer.config,
            runtime=True,
            env={"OPENAI_API_KEY": "test-secret-value"},
        )
    finally:
        module.create_llm_reviewer = original_factory  # type: ignore[assignment]

    assert result.secret_status == "resolved"
    assert result.api_key_env == "OPENAI_API_KEY"
    assert result.redacted_secret == REDACTED_SECRET_TEXT
    assert result.runtime_status == "ok"


def test_run_llm_smoke_check_pydanticai_runtime_failure_with_fake_runtime() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="openai:gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
        ),
        secret_resolver=lambda config: _reviewer_secret(config.api_key_env or "missing"),
        runtime_runner=lambda _agent, _payload: (_ for _ in ()).throw(
            TimeoutError("hidden runtime timeout")
        ),
    )

    from content_review_engine.llm import smoke_check as module

    original_factory = module.create_llm_reviewer
    module.create_llm_reviewer = lambda config: reviewer  # type: ignore[assignment]
    try:
        with pytest.raises(LLMProviderRuntimeError) as exc_info:
            run_llm_smoke_check(
                reviewer.config,
                runtime=True,
                env={"OPENAI_API_KEY": "test-secret-value"},
            )
    finally:
        module.create_llm_reviewer = original_factory  # type: ignore[assignment]

    assert str(exc_info.value) == "PydanticAI runtime request timed out."


def test_run_llm_smoke_check_pydanticai_rejects_missing_api_key_env() -> None:
    with pytest.raises(MissingLLMProviderSecretReferenceError) as exc_info:
        run_llm_smoke_check(
            LLMProviderConfig(
                provider="pydanticai",
                model="openai:gpt-4o-mini",
            )
        )

    assert "api_key_env is required for secret resolution." in str(exc_info.value)


def test_run_llm_smoke_check_pydanticai_rejects_unset_env_var() -> None:
    with pytest.raises(MissingLLMProviderSecretEnvironmentVariableError) as exc_info:
        run_llm_smoke_check(
            LLMProviderConfig(
                provider="pydanticai",
                model="openai:gpt-4o-mini",
                api_key_env="OPENAI_API_KEY",
            ),
            env={},
        )

    assert str(exc_info.value) == "LLM provider secret environment variable 'OPENAI_API_KEY' is not set."
    assert "test-secret-value" not in str(exc_info.value)


def test_run_llm_smoke_check_pydanticai_rejects_empty_env_var() -> None:
    with pytest.raises(EmptyLLMProviderSecretEnvironmentVariableError) as exc_info:
        run_llm_smoke_check(
            LLMProviderConfig(
                provider="pydanticai",
                model="openai:gpt-4o-mini",
                api_key_env="OPENAI_API_KEY",
            ),
            env={"OPENAI_API_KEY": "   "},
        )

    assert str(exc_info.value) == "LLM provider secret environment variable 'OPENAI_API_KEY' is empty."
    assert "test-secret-value" not in str(exc_info.value)


def test_render_llm_smoke_check_result_does_not_include_full_synthetic_request() -> None:
    rendered = render_llm_smoke_check_result(
        run_llm_smoke_check(LLMProviderConfig(provider="mock"), runtime=True)
    )

    assert "LLM check passed." in rendered
    assert "Model: <not configured>" in rendered
    assert "Config: ok" in rendered
    assert "Secret: not required" in rendered
    assert "Runtime: ok" in rendered
    assert "LLM smoke check synthetic request." not in rendered
    assert "<llm-check>" not in rendered


def test_render_llm_smoke_check_result_shows_redacted_secret_only() -> None:
    rendered = render_llm_smoke_check_result(
        run_llm_smoke_check(
            LLMProviderConfig(
                provider="pydanticai",
                model="openai:gpt-4o-mini",
                api_key_env="OPENAI_API_KEY",
            ),
            env={"OPENAI_API_KEY": "test-secret-value"},
        )
    )

    assert "Provider: pydanticai" in rendered
    assert "Model: openai:gpt-4o-mini" in rendered
    assert "API key env: OPENAI_API_KEY" in rendered
    assert f"API key: {REDACTED_SECRET_TEXT}" in rendered
    assert "Secret: resolved" in rendered
    assert "test-secret-value" not in rendered
