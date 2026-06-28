from __future__ import annotations

import builtins
import importlib
import socket
import sys

import pytest

from content_review_engine.llm import (
    LLMProviderConfig,
    LLMProviderConfigError,
    LLMProviderNotImplementedError,
    MockLLMReviewer,
    create_llm_reviewer,
    load_llm_provider_config,
)


def test_provider_factory_creates_mock_reviewer() -> None:
    reviewer = create_llm_reviewer(load_llm_provider_config())

    assert isinstance(reviewer, MockLLMReviewer)


def test_provider_factory_rejects_reserved_pydanticai_provider() -> None:
    config = load_llm_provider_config(provider="pydanticai")

    with pytest.raises(LLMProviderNotImplementedError) as exc_info:
        create_llm_reviewer(config)

    assert str(exc_info.value) == "Provider 'pydanticai' is recognized but not implemented yet."


def test_provider_factory_rejects_unknown_provider_defensively() -> None:
    config = LLMProviderConfig.model_construct(provider="openai")

    with pytest.raises(LLMProviderConfigError) as exc_info:
        create_llm_reviewer(config)

    assert str(exc_info.value) == "Unknown LLM provider 'openai'. Supported providers: 'mock', 'pydanticai'."


def test_provider_factory_does_not_fallback_pydanticai_to_mock() -> None:
    config = load_llm_provider_config(provider="pydanticai")

    with pytest.raises(LLMProviderNotImplementedError):
        reviewer = create_llm_reviewer(config)

    assert "reviewer" not in locals()


def test_provider_factory_does_not_import_pydanticai_sdk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name.startswith("pydantic_ai"):
            raise AssertionError("Unexpected import of pydantic_ai SDK")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    sys.modules.pop("content_review_engine.llm", None)
    sys.modules.pop("content_review_engine.llm.factory", None)
    sys.modules.pop("content_review_engine.llm.pydanticai", None)

    module = importlib.import_module("content_review_engine.llm.factory")

    reviewer = module.create_llm_reviewer(module.LLMProviderConfig())

    assert isinstance(reviewer, MockLLMReviewer)


def test_provider_factory_does_not_make_network_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    mock_reviewer = create_llm_reviewer(load_llm_provider_config(provider="mock"))

    assert isinstance(mock_reviewer, MockLLMReviewer)

    with pytest.raises(LLMProviderNotImplementedError):
        create_llm_reviewer(load_llm_provider_config(provider="pydanticai"))
