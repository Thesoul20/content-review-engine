from __future__ import annotations

from content_review_engine.llm import LLMProviderConfig, LLMReviewRequest, PydanticAIReviewer
from content_review_engine.llm.secrets import ResolvedLLMSecret
from pydantic import SecretStr


def _build_request(*, path: str = "articles/example.md") -> LLMReviewRequest:
    return LLMReviewRequest(
        content="This article claims it is always safe.",
        profile_name="wechat-strict",
        content_path=path,
        review_goal="semantic_review",
    )


def _reviewer_secret(api_key_env: str) -> ResolvedLLMSecret:
    return ResolvedLLMSecret(api_key_env=api_key_env, api_key=SecretStr("test-secret-value"))


class FakeClock:
    def __init__(self, *, now: float = 0.0) -> None:
        self.now = now
        self.monotonic_calls = 0
        self.sleep_calls: list[float] = []

    def monotonic(self) -> float:
        self.monotonic_calls += 1
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleep_calls.append(seconds)
        self.now += seconds


def _build_reviewer(*, clock: FakeClock, runtime_runner, interval: float) -> PydanticAIReviewer:
    return PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            min_request_interval_seconds=interval,
        ),
        secret_resolver=lambda config: _reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=runtime_runner,
        sleep_func=clock.sleep,
        monotonic_func=clock.monotonic,
    )


def test_pydanticai_first_runtime_call_does_not_sleep() -> None:
    clock = FakeClock(now=10.0)
    reviewer = _build_reviewer(
        clock=clock,
        interval=2.0,
        runtime_runner=lambda _agent, _payload: {"findings": []},
    )

    reviewer.review(_build_request())

    assert clock.sleep_calls == []
    assert reviewer._last_request_started_at == 10.0


def test_pydanticai_consecutive_runtime_calls_sleep_remaining_interval() -> None:
    clock = FakeClock(now=0.0)
    started_at: list[float] = []

    def fake_runtime_runner(_agent, _payload):  # type: ignore[no-untyped-def]
        started_at.append(clock.now)
        if len(started_at) == 1:
            clock.now += 0.75
        return {"findings": []}

    reviewer = _build_reviewer(clock=clock, interval=2.0, runtime_runner=fake_runtime_runner)

    reviewer.review(_build_request(path="articles/a.md"))
    reviewer.review(_build_request(path="articles/b.md"))

    assert started_at == [0.0, 2.0]
    assert clock.sleep_calls == [1.25]
    assert clock.monotonic_calls >= 3


def test_pydanticai_consecutive_runtime_calls_do_not_sleep_when_interval_already_satisfied() -> None:
    clock = FakeClock(now=0.0)

    def fake_runtime_runner(_agent, _payload):  # type: ignore[no-untyped-def]
        if reviewer._last_request_started_at == 0.0:
            clock.now = 3.5
        return {"findings": []}

    reviewer = _build_reviewer(clock=clock, interval=2.0, runtime_runner=fake_runtime_runner)

    reviewer.review(_build_request(path="articles/a.md"))
    reviewer.review(_build_request(path="articles/b.md"))

    assert clock.sleep_calls == []


def test_pydanticai_zero_min_request_interval_does_not_sleep() -> None:
    clock = FakeClock(now=5.0)
    reviewer = _build_reviewer(
        clock=clock,
        interval=0.0,
        runtime_runner=lambda _agent, _payload: {"findings": []},
    )

    reviewer.review(_build_request(path="articles/a.md"))
    reviewer.review(_build_request(path="articles/b.md"))

    assert clock.sleep_calls == []
    assert reviewer._last_request_started_at is None


def test_pydanticai_retry_backoff_then_pacing_sleeps_remaining_interval() -> None:
    clock = FakeClock(now=0.0)
    attempts = {"count": 0}

    def fake_runtime_runner(_agent, _payload):  # type: ignore[no-untyped-def]
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise TimeoutError("hidden")
        return {"findings": []}

    reviewer = PydanticAIReviewer(
        LLMProviderConfig(
            provider="pydanticai",
            model="gpt-4o-mini",
            api_key_env="CONTENT_REVIEW_TEST_LLM_API_KEY",
            retry_attempts=1,
            retry_backoff_seconds=0.5,
            min_request_interval_seconds=2.0,
        ),
        secret_resolver=lambda config: _reviewer_secret(config.api_key_env or "missing"),
        agent_builder=lambda **kwargs: object(),
        runtime_runner=fake_runtime_runner,
        sleep_func=clock.sleep,
        monotonic_func=clock.monotonic,
    )

    reviewer.review(_build_request())

    assert attempts["count"] == 2
    assert clock.sleep_calls == [0.5, 1.5]


def test_batch_pydanticai_reuse_of_same_reviewer_applies_pacing() -> None:
    clock = FakeClock(now=0.0)
    started_at: list[float] = []

    def fake_runtime_runner(_agent, payload):  # type: ignore[no-untyped-def]
        started_at.append(clock.now)
        return {"findings": [{"rule_id": payload.prompt_version, "severity": "info", "message": "ok"}]}

    reviewer = _build_reviewer(clock=clock, interval=1.0, runtime_runner=fake_runtime_runner)

    reviewer.review(_build_request(path="articles/a.md"))
    reviewer.review(_build_request(path="articles/b.md"))
    reviewer.review(_build_request(path="articles/c.md"))

    assert started_at == [0.0, 1.0, 2.0]
    assert clock.sleep_calls == [1.0, 1.0]
