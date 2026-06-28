from __future__ import annotations

import builtins
import importlib
import sys

import pytest

from content_review_engine.llm import (
    LLMProviderNotImplementedError,
    LLMReviewRequest,
    LLMReviewer,
    PydanticAIReviewer,
    PYDANTICAI_NOT_IMPLEMENTED_MESSAGE,
)


def test_pydanticai_skeleton_satisfies_provider_protocol() -> None:
    reviewer = PydanticAIReviewer(
        model="gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        base_url="https://example.com/v1",
    )

    assert isinstance(reviewer, LLMReviewer)


def test_pydanticai_skeleton_review_raises_not_implemented_error() -> None:
    reviewer = PydanticAIReviewer(
        model="gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        base_url="https://example.com/v1",
    )

    with pytest.raises(LLMProviderNotImplementedError) as exc_info:
        reviewer.review(LLMReviewRequest(content="Future provider skeleton request."))

    assert str(exc_info.value) == PYDANTICAI_NOT_IMPLEMENTED_MESSAGE


def test_pydanticai_skeleton_only_stores_config_names() -> None:
    reviewer = PydanticAIReviewer(
        model="gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        base_url="https://example.com/v1",
    )

    assert reviewer.model == "gpt-4o-mini"
    assert reviewer.api_key_env == "OPENAI_API_KEY"
    assert reviewer.base_url == "https://example.com/v1"


def test_pydanticai_module_does_not_import_sdk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name.startswith("pydantic_ai"):
            raise AssertionError("Unexpected import of pydantic_ai SDK")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    sys.modules.pop("content_review_engine.llm", None)
    sys.modules.pop("content_review_engine.llm.pydanticai", None)

    module = importlib.import_module("content_review_engine.llm.pydanticai")

    reviewer = module.PydanticAIReviewer(model="gpt-4o-mini")

    with pytest.raises(LLMProviderNotImplementedError):
        reviewer.review(LLMReviewRequest(content="No SDK import should happen."))
