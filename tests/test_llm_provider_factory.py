from __future__ import annotations

import importlib
import socket
import sys

import pytest

from content_review_engine.llm import (
    LLMProviderConfig,
    LLMProviderConfigError,
    MockLLMReviewer,
    PydanticAIReviewer,
    create_llm_reviewer,
    load_llm_provider_config,
)


def test_provider_factory_creates_mock_reviewer() -> None:
    reviewer = create_llm_reviewer(load_llm_provider_config())

    assert isinstance(reviewer, MockLLMReviewer)


def test_provider_factory_creates_pydanticai_skeleton() -> None:
    config = load_llm_provider_config(provider="pydanticai")
    reviewer = create_llm_reviewer(config)

    assert isinstance(reviewer, PydanticAIReviewer)
    assert reviewer.config is config


def test_provider_factory_rejects_unknown_provider_defensively() -> None:
    config = LLMProviderConfig.model_construct(provider="openai")

    with pytest.raises(LLMProviderConfigError) as exc_info:
        create_llm_reviewer(config)

    assert str(exc_info.value) == "Unknown LLM provider 'openai'. Supported providers: 'mock', 'pydanticai'."


def test_provider_factory_does_not_fallback_pydanticai_to_mock() -> None:
    config = load_llm_provider_config(provider="pydanticai")
    reviewer = create_llm_reviewer(config)

    assert isinstance(reviewer, PydanticAIReviewer)
    assert not isinstance(reviewer, MockLLMReviewer)


def test_provider_factory_does_not_import_pydanticai_sdk(
) -> None:
    sys.modules.pop("content_review_engine.llm", None)
    sys.modules.pop("content_review_engine.llm.factory", None)
    sys.modules.pop("content_review_engine.llm.pydanticai", None)

    module = importlib.import_module("content_review_engine.llm.factory")

    reviewer = module.create_llm_reviewer(module.LLMProviderConfig())

    assert isinstance(reviewer, MockLLMReviewer)
    assert module.PydanticAIReviewer.__name__ == "PydanticAIReviewer"


def test_provider_factory_does_not_make_network_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    mock_reviewer = create_llm_reviewer(load_llm_provider_config(provider="mock"))

    assert isinstance(mock_reviewer, MockLLMReviewer)

    pydanticai_reviewer = create_llm_reviewer(
        load_llm_provider_config(provider="pydanticai")
    )

    assert isinstance(pydanticai_reviewer, PydanticAIReviewer)
