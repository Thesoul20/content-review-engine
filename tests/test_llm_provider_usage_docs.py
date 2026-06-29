from __future__ import annotations

import re
from pathlib import Path

from content_review_engine.config import load_profile
from content_review_engine.parser import read_markdown


USAGE_DOC_PATH = Path("docs/LLM_PROVIDER_USAGE.md")
ENV_EXAMPLE_PATH = Path("examples/llm/pydanticai/.env.example")
PYDANTICAI_CONFIG_PATH = Path("examples/llm/pydanticai/llm-provider.yml")
MOCK_CONFIG_PATH = Path("examples/llm/mock/llm-provider.yml")
MANUAL_PROFILE_PATH = Path("examples/llm/pydanticai/manual-profile.yml")
MANUAL_MARKDOWN_PATH = Path("examples/llm/pydanticai/manual-review.md")
BATCH_DIR = Path("examples/llm/pydanticai/batch")


def _looks_like_real_api_key(content: str) -> bool:
    patterns = (
        r"sk-[A-Za-z0-9_-]{16,}",
        r"AIza[0-9A-Za-z\-_]{20,}",
        r"ghp_[A-Za-z0-9]{20,}",
    )
    return any(re.search(pattern, content) for pattern in patterns)


def test_manual_verification_fixtures_exist_and_are_non_empty() -> None:
    paths = (
        MANUAL_MARKDOWN_PATH,
        MANUAL_PROFILE_PATH,
        BATCH_DIR / "article-a.md",
        BATCH_DIR / "article-b.md",
        ENV_EXAMPLE_PATH,
        PYDANTICAI_CONFIG_PATH,
        MOCK_CONFIG_PATH,
    )

    for path in paths:
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip()


def test_env_example_contains_only_placeholders() -> None:
    content = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

    assert "YOUR_OPENAI_API_KEY_HERE" in content
    assert "your-openai-compatible-endpoint.example" in content
    assert not _looks_like_real_api_key(content)


def test_usage_docs_exist_and_cover_required_provider_flags_and_boundaries() -> None:
    content = USAGE_DOC_PATH.read_text(encoding="utf-8")

    assert "--llm-provider pydanticai" in content
    assert "--llm-provider pydantic-ai-testmodel" in content
    assert "test providers" in content
    assert "reserved real providers" in content
    assert "`openai`" in content
    assert "`anthropic`" in content
    assert "`gemini`" in content
    assert "`deepseek`" in content
    assert "`qwen`" in content
    assert "`local`" in content
    assert "reserved but not implemented yet" in content
    assert "unsupported provider names" in content
    assert "--llm-config" in content
    assert "llm-check" in content
    assert "--live" in content
    assert "--runtime" in content
    assert "--llm-model" in content
    assert "--llm-api-key-env" in content
    assert "--llm-base-url" in content
    assert "--llm-timeout-seconds" in content
    assert "secret resolver" in content
    assert "resolve_llm_provider_secret" in content
    assert "api_key_env is a secret reference" in content
    assert "does not read `.env`" in content
    assert "API key env:" in content
    assert "API key: <redacted>" in content
    assert "Secret: resolved" in content
    assert "Secret: not required" in content
    assert "Construction: ok" in content
    assert "Live call: not run" in content
    assert "Live call: failed" in content
    assert "LLM semantic review prompt contract" in content
    assert "llm-semantic-review-output.v1" in content
    assert "Return JSON only" in content
    assert "`llm.`" in content
    assert "info, warning, error, critical" in content
    assert "LLM semantic review output validation" in content
    assert "parse_llm_semantic_review_output" in content
    assert "validate_llm_semantic_review_output" in content
    assert "single fenced `json` block" in content
    assert "do not auto-fix malformed JSON" in content
    assert "do not coerce string confidence values" in content
    assert "PydanticAI semantic review execution" in content
    assert "run_semantic_review(request)" in content
    assert "ValidatedLLMSemanticReviewOutput" in content
    assert "convert_validated_semantic_output_to_llm_review_result" in content
    assert "Validated LLM semantic output to LLMReviewResult conversion" in content
    assert "Single-file CLI LLM integration" in content
    assert "--llm-output` writes raw `LLMReviewResult` JSON" in content
    assert "--llm-report` writes a separate Markdown report rendered from the same" in content
    assert "--report-index" in content
    assert "Report Index Boundary" in content
    assert "LLM not enabled" in content
    assert "matched_text" in content
    assert "confidence: null stays null" in content
    assert "advisory semantic review suggestions" in content
    assert "Manual Review Checklist" in content
    assert "LLM Execution Review Checklist" in content
    assert "needs_review" in content
    assert "pending" in content
    assert "needs_rerun" in content
    assert "rerun_llm_review" in content
    assert "LLM advisory severity" in content
    assert "llm.semantic_review" in content
    assert "not provided" in content
    assert "does not execute a real provider call" in content
    assert "`run_semantic_review()` is now reused by both `content-review review` and `content-review batch`" in content
    assert "deterministic JSON and Markdown reports do not include LLM findings" in content
    assert "Batch `--llm-output` writes one aggregate `LLMSidecarResult` JSON sidecar" in content
    assert "Real `pydanticai` provider calls must not run in default `pytest` or CI." in content
    assert "LLMProviderTimeoutError" in content
    assert "LLMProviderAuthError" in content
    assert "LLMProviderNetworkError" in content
    assert "LLMProviderRateLimitError" in content
    assert "LLMProviderModelError" in content
    assert "LLMProviderRuntimeError" in content
    assert "LLMResponseValidationError" in content
    assert "LLMProviderSecretError" in content
    assert not _looks_like_real_api_key(content)


def test_example_llm_config_files_are_placeholder_safe() -> None:
    pydanticai_config = PYDANTICAI_CONFIG_PATH.read_text(encoding="utf-8")
    mock_config = MOCK_CONFIG_PATH.read_text(encoding="utf-8")

    assert "OPENAI_API_KEY" in pydanticai_config
    assert "api_key:" not in pydanticai_config
    assert "secret:" not in pydanticai_config
    assert not _looks_like_real_api_key(pydanticai_config)
    assert "provider: mock" in mock_config


def test_manual_profile_fixture_loads_with_current_profile_loader() -> None:
    profile = load_profile(MANUAL_PROFILE_PATH)

    assert profile.name == "manual-pydanticai"


def test_manual_markdown_fixture_loads_with_current_reader() -> None:
    content = read_markdown(MANUAL_MARKDOWN_PATH)

    assert "LLM sidecar" in content


def test_docs_and_fixtures_do_not_require_real_network_or_real_api_key() -> None:
    usage_doc = USAGE_DOC_PATH.read_text(encoding="utf-8")
    env_example = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

    assert "replace-with-your-real-key" in usage_doc
    assert "mock`: safe for local tests and CI" in usage_doc
    assert "`pydantic-ai-testmodel`: package-level testing provider" in usage_doc
    assert "Reserved real provider names such as `openai` or `anthropic`" in usage_doc
    assert "must not be used" in usage_doc
    assert "Missing `api_key_env` fails before any real provider call." in usage_doc
    assert "Empty env vars also fail before any real provider call." in usage_doc
    assert "provider construction also stays local and does not access the network" in usage_doc
    assert "Use `--live` only for explicit manual verification." in usage_doc
    assert "Prompt construction does not read `.env`, does not read `os.environ`, and does not access the network." in usage_doc
    assert "prompt construction remains separate from output parsing, output validation," in usage_doc
    assert "the validated output is not the same thing as `LLMReviewResult`" in usage_doc
    assert "The conversion helper does not call a provider, does not read `os.environ`, and does not access the network." in usage_doc
    assert "provider execution reuses the shared prompt contract" in usage_doc
    assert "provider execution reuses `parse_llm_semantic_review_output()`" in usage_doc
    assert "Single-file `content-review review --enable-llm --llm-output ...` now writes" in usage_doc
    assert "raw `LLMReviewResult` JSON" in usage_doc
    assert "`--llm-report` writes a separate Markdown report rendered from the same" in usage_doc
    assert "`--report-index` can summarize deterministic output plus optional LLM output" in usage_doc
    assert "quality gate still uses deterministic review only" in usage_doc
    assert "LLM findings are advisory semantic review suggestions" in usage_doc
    assert "Batch `--llm-output` writes one aggregate `LLMSidecarResult` JSON sidecar" in usage_doc
    assert "default `pytest` or CI" in usage_doc
    assert "YOUR_OPENAI_API_KEY_HERE" in env_example
