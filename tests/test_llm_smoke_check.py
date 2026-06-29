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

    assert result.success is True
    assert result.provider == "mock"
    assert result.model is None
    assert result.config_status == "ok"
    assert result.secret_status == "not_required"
    assert result.api_key_env is None
    assert result.redacted_secret is None
    assert result.construction_status == "ok"
    assert result.live_call_status == "not run"


def test_run_llm_smoke_check_mock_runtime_succeeds_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    result = run_llm_smoke_check(LLMProviderConfig(provider="mock"), live=True)

    assert result.success is True
    assert result.provider == "mock"
    assert result.secret_status == "not_required"
    assert result.construction_status == "ok"
    assert result.live_call_status == "ok"


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
        live=True,
        reviewer_provider="pydantic-ai-testmodel",
    )

    assert result.success is True
    assert captured_provider == {"value": "pydantic-ai-testmodel"}
    assert result.provider == "pydantic-ai-testmodel"
    assert result.secret_status == "not_required"
    assert result.construction_status == "ok"
    assert result.live_call_status == "ok"


def test_run_llm_smoke_check_pydanticai_secret_present_runs_construction_without_calling_review() -> None:
    review_called = {"value": False}
    construction_called = {"value": False}

    class GuardedReviewer:
        def run_construction_check(self) -> None:
            construction_called["value"] = True

        def review(self, request):  # type: ignore[no-untyped-def]
            del request
            review_called["value"] = True
            return LLMReviewResult()

    from content_review_engine.llm import smoke_check as module

    captured_secret_value: dict[str, str] = {}
    original_factory = module.create_llm_reviewer

    def fake_create_llm_reviewer(config, *, secret_value=None):  # type: ignore[no-untyped-def]
        del config
        captured_secret_value["value"] = secret_value or ""
        return GuardedReviewer()

    module.create_llm_reviewer = fake_create_llm_reviewer  # type: ignore[assignment]
    try:
        result = run_llm_smoke_check(
            LLMProviderConfig(
                provider="pydanticai",
                model="openai:gpt-4o-mini",
                api_key_env="OPENAI_API_KEY",
            ),
            live=False,
            env={"OPENAI_API_KEY": "test-secret-value"},
        )
    finally:
        module.create_llm_reviewer = original_factory  # type: ignore[assignment]

    assert result.success is True
    assert result.secret_status == "resolved"
    assert result.api_key_env == "OPENAI_API_KEY"
    assert result.redacted_secret == REDACTED_SECRET_TEXT
    assert result.construction_status == "ok"
    assert result.live_call_status == "not run"
    assert construction_called["value"] is True
    assert review_called["value"] is False
    assert captured_secret_value == {"value": "test-secret-value"}


def test_run_llm_smoke_check_pydanticai_live_success_with_fake_runtime() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="openai:gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
        ),
        resolved_secret=_reviewer_secret("OPENAI_API_KEY"),
    )
    reviewer.run_live_check = lambda: None  # type: ignore[method-assign]

    from content_review_engine.llm import smoke_check as module

    original_factory = module.create_llm_reviewer
    module.create_llm_reviewer = (  # type: ignore[assignment]
        lambda config, *, secret_value=None: reviewer
    )
    try:
        result = run_llm_smoke_check(
            reviewer.config,
            live=True,
            env={"OPENAI_API_KEY": "test-secret-value"},
        )
    finally:
        module.create_llm_reviewer = original_factory  # type: ignore[assignment]

    assert result.success is True
    assert result.secret_status == "resolved"
    assert result.api_key_env == "OPENAI_API_KEY"
    assert result.redacted_secret == REDACTED_SECRET_TEXT
    assert result.construction_status == "ok"
    assert result.live_call_status == "ok"


def test_run_llm_smoke_check_pydanticai_live_failure_returns_failed_result() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="openai:gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
        ),
        resolved_secret=_reviewer_secret("OPENAI_API_KEY"),
    )
    reviewer.run_live_check = lambda: (_ for _ in ()).throw(  # type: ignore[method-assign]
        LLMProviderRuntimeError("PydanticAI runtime request timed out.")
    )

    from content_review_engine.llm import smoke_check as module

    original_factory = module.create_llm_reviewer
    module.create_llm_reviewer = (  # type: ignore[assignment]
        lambda config, *, secret_value=None: reviewer
    )
    try:
        result = run_llm_smoke_check(
            reviewer.config,
            live=True,
            env={"OPENAI_API_KEY": "test-secret-value"},
        )
    finally:
        module.create_llm_reviewer = original_factory  # type: ignore[assignment]

    assert result.success is False
    assert result.secret_status == "resolved"
    assert result.construction_status == "ok"
    assert result.live_call_status == "failed"
    assert result.failure_message == "PydanticAI runtime request timed out."
    assert "test-secret-value" not in (result.failure_message or "")


def test_run_llm_smoke_check_construction_failure_does_not_continue_to_live() -> None:
    call_order: list[str] = []

    class GuardedReviewer:
        def run_construction_check(self) -> None:
            call_order.append("construction")
            raise LLMProviderRuntimeError("construction failed")

        def run_live_check(self) -> None:
            call_order.append("live")

    from content_review_engine.llm import smoke_check as module

    original_factory = module.create_llm_reviewer
    module.create_llm_reviewer = (  # type: ignore[assignment]
        lambda config, *, secret_value=None: GuardedReviewer()
    )
    try:
        with pytest.raises(LLMProviderRuntimeError) as exc_info:
            run_llm_smoke_check(
                LLMProviderConfig(
                    provider="pydanticai",
                    model="openai:gpt-4o-mini",
                    api_key_env="OPENAI_API_KEY",
                ),
                live=True,
                env={"OPENAI_API_KEY": "test-secret-value"},
            )
    finally:
        module.create_llm_reviewer = original_factory  # type: ignore[assignment]

    assert str(exc_info.value) == "construction failed"
    assert call_order == ["construction"]


def test_run_llm_smoke_check_secret_failure_does_not_continue_to_construction_or_live() -> None:
    from content_review_engine.llm import smoke_check as module

    reviewer_called = {"value": False}
    original_factory = module.create_llm_reviewer
    module.create_llm_reviewer = (  # type: ignore[assignment]
        lambda config, *, secret_value=None: reviewer_called.__setitem__("value", True)
    )
    try:
        with pytest.raises(MissingLLMProviderSecretEnvironmentVariableError):
            run_llm_smoke_check(
                LLMProviderConfig(
                    provider="pydanticai",
                    model="openai:gpt-4o-mini",
                    api_key_env="OPENAI_API_KEY",
                ),
                live=True,
                env={},
            )
    finally:
        module.create_llm_reviewer = original_factory  # type: ignore[assignment]

    assert reviewer_called["value"] is False


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
        run_llm_smoke_check(LLMProviderConfig(provider="mock"), live=True)
    )

    assert "LLM check passed." in rendered
    assert "Model: <not configured>" in rendered
    assert "Config: ok" in rendered
    assert "Secret: not required" in rendered
    assert "Construction: ok" in rendered
    assert "Live call: ok" in rendered
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
    assert "Construction: ok" in rendered
    assert "Live call: not run" in rendered
    assert "test-secret-value" not in rendered


def test_render_llm_smoke_check_failed_result_hides_secret_and_shows_reason() -> None:
    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="openai:gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
        ),
        resolved_secret=_reviewer_secret("OPENAI_API_KEY"),
    )
    reviewer.run_live_check = lambda: (_ for _ in ()).throw(  # type: ignore[method-assign]
        LLMProviderRuntimeError("PydanticAI runtime request timed out.")
    )

    from content_review_engine.llm import smoke_check as module

    original_factory = module.create_llm_reviewer
    module.create_llm_reviewer = (  # type: ignore[assignment]
        lambda config, *, secret_value=None: reviewer
    )
    try:
        rendered = render_llm_smoke_check_result(
            run_llm_smoke_check(
                reviewer.config,
                live=True,
                env={"OPENAI_API_KEY": "test-secret-value"},
            )
        )
    finally:
        module.create_llm_reviewer = original_factory  # type: ignore[assignment]

    assert "LLM check failed." in rendered
    assert "Live call: failed" in rendered
    assert "Reason: PydanticAI runtime request timed out." in rendered
    assert "test-secret-value" not in rendered
