from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_review_engine.api import review_batch, review_file
from content_review_engine.cli import main
from content_review_engine.llm import (
    LLMProviderConfig,
    ValidatedLLMSemanticReviewOutput,
)


PYTHON_API_DOC = Path("docs/PYTHON_API.md")
EXAMPLE_README = Path("examples/python_api_usage/README.md")


class _SemanticReviewer:
    def __init__(
        self,
        output: ValidatedLLMSemanticReviewOutput,
        *,
        provider: str = "pydanticai",
        model: str = "openai:gpt-4o-mini",
    ) -> None:
        self.output = output
        self.model = model
        self.config = type("Config", (), {"provider": provider})()
        self.calls: list[object] = []

    def run_semantic_review(
        self,
        request: object,
    ) -> ValidatedLLMSemanticReviewOutput:
        self.calls.append(request)
        return self.output


def _semantic_output() -> ValidatedLLMSemanticReviewOutput:
    return ValidatedLLMSemanticReviewOutput.model_validate(
        {
            "schema_version": "llm-semantic-review-output.v1",
            "summary": "One semantic issue found.",
            "findings": [
                {
                    "rule_id": "llm.semantic.overclaim",
                    "severity": "warning",
                    "line": 1,
                    "column": 1,
                    "message": "Possible overclaim.",
                    "evidence": "绝对安全",
                    "suggestion": "Use a softer claim.",
                    "confidence": 0.84,
                }
            ],
        }
    )


def test_review_file_deterministic_only_returns_structured_result() -> None:
    result = review_file(
        "tests/fixtures/markdown/forbidden_terms_article.md",
        "tests/fixtures/profiles/default.yml",
        fail_on="warning",
        include_combined_result=True,
    )

    assert result.review_result.schema_version == "review-result.v1"
    assert result.review_result.summary.finding_count == 1
    assert result.llm_result is None
    assert result.llm_status == "not_run"
    assert result.deterministic_quality_gate.enabled is True
    assert result.deterministic_quality_gate.failed is True
    assert result.llm_quality_gate.enabled is False
    assert result.combined_result is not None
    assert result.combined_result.llm_status == "not_run"


def test_review_batch_deterministic_only_returns_structured_result() -> None:
    result = review_batch(
        "tests/fixtures/batch/articles",
        "tests/fixtures/batch/profile.yml",
        recursive=True,
        fail_on="warning",
        include_combined_result=True,
    )

    assert result.batch_result.schema_version == "batch-review-result.v1"
    assert result.batch_result.summary.file_count == 3
    assert result.batch_result.summary.finding_count == 2
    assert result.llm_sidecar_result is None
    assert result.deterministic_quality_gate.enabled is True
    assert result.deterministic_quality_gate.failed is True
    assert result.combined_result is not None
    assert result.combined_result.llm_summary.not_run_count == 3


def test_review_file_enable_llm_returns_raw_llm_and_combined_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reviewer = _SemanticReviewer(_semantic_output())
    monkeypatch.setattr(
        "content_review_engine.workflows.create_llm_reviewer",
        lambda *args, **kwargs: reviewer,
    )

    result = review_file(
        "tests/fixtures/markdown/clean_article.md",
        "tests/fixtures/profiles/default.yml",
        enable_llm=True,
        llm_provider_config=LLMProviderConfig(provider="mock"),
        include_combined_result=True,
        llm_fail_on="warning",
    )

    assert result.review_result.summary.finding_count == 0
    assert result.llm_result is not None
    assert result.llm_result.findings[0].rule_id == "llm.semantic.overclaim"
    assert result.llm_status == "succeeded"
    assert result.llm_quality_gate.enabled is True
    assert result.llm_quality_gate.failed is True
    assert result.deterministic_quality_gate.failed is False
    assert result.combined_result is not None
    assert result.combined_result.llm_status == "succeeded"
    assert result.review_result.summary.severity_counts["warning"] == 0
    assert reviewer.calls


def test_review_batch_enable_llm_returns_sidecar_and_combined_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reviewer = _SemanticReviewer(_semantic_output())
    monkeypatch.setattr(
        "content_review_engine.workflows.create_llm_reviewer",
        lambda *args, **kwargs: reviewer,
    )

    result = review_batch(
        "tests/fixtures/batch/articles",
        "tests/fixtures/batch/profile.yml",
        recursive=True,
        enable_llm=True,
        llm_provider_config=LLMProviderConfig(provider="mock"),
        include_combined_result=True,
        llm_fail_on="warning",
    )

    assert result.llm_sidecar_result is not None
    assert result.llm_sidecar_result.summary.file_count == 3
    assert result.llm_sidecar_result.summary.succeeded_count == 3
    assert result.llm_quality_gate.enabled is True
    assert result.llm_quality_gate.failed is True
    assert result.combined_result is not None
    assert result.combined_result.llm_summary.succeeded_count == 3
    assert result.batch_result.summary.finding_count == 2
    assert result.batch_result.summary.severity_counts["warning"] == 2


def test_api_writes_deterministic_llm_and_combined_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reviewer = _SemanticReviewer(_semantic_output())
    monkeypatch.setattr(
        "content_review_engine.workflows.create_llm_reviewer",
        lambda *args, **kwargs: reviewer,
    )
    output_path = tmp_path / "review.json"
    llm_output_path = tmp_path / "review.llm.json"
    combined_output_path = tmp_path / "review.combined.json"

    result = review_file(
        "tests/fixtures/markdown/clean_article.md",
        "tests/fixtures/profiles/default.yml",
        output_format="json",
        output_path=output_path,
        enable_llm=True,
        llm_provider_config=LLMProviderConfig(provider="mock"),
        llm_output_path=llm_output_path,
        combined_output_path=combined_output_path,
        combined_output_format="json",
    )

    deterministic_payload = json.loads(output_path.read_text(encoding="utf-8"))
    llm_payload = json.loads(llm_output_path.read_text(encoding="utf-8"))
    combined_payload = json.loads(combined_output_path.read_text(encoding="utf-8"))

    assert result.artifacts.output_path == str(output_path)
    assert result.artifacts.llm_output_path == str(llm_output_path)
    assert result.artifacts.combined_output_path == str(combined_output_path)
    assert deterministic_payload["schema_version"] == "review-result.v1"
    assert llm_payload["schema_version"] == "llm-review-result.v1"
    assert combined_payload["schema_version"] == "single-file-combined-review-result.v1"


def test_combined_output_path_does_not_auto_enable_llm(tmp_path: Path) -> None:
    combined_output_path = tmp_path / "review.combined.json"

    result = review_file(
        "tests/fixtures/markdown/clean_article.md",
        "tests/fixtures/profiles/default.yml",
        combined_output_path=combined_output_path,
        combined_output_format="json",
    )

    payload = json.loads(combined_output_path.read_text(encoding="utf-8"))

    assert result.llm_result is None
    assert result.llm_status == "not_run"
    assert payload["llm"]["status"] == "not_run"


def test_llm_fail_on_does_not_auto_enable_llm() -> None:
    result = review_file(
        "tests/fixtures/markdown/clean_article.md",
        "tests/fixtures/profiles/default.yml",
        llm_fail_on="warning",
        include_combined_result=True,
    )

    assert result.llm_result is None
    assert result.llm_status == "not_run"
    assert result.llm_quality_gate.enabled is True
    assert result.llm_quality_gate.evaluation_status == "not_run"


def test_api_and_cli_single_file_main_path_stay_aligned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reviewer = _SemanticReviewer(_semantic_output())
    monkeypatch.setattr(
        "content_review_engine.workflows.create_llm_reviewer",
        lambda *args, **kwargs: reviewer,
    )
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: reviewer,
    )
    cli_output_path = tmp_path / "cli.review.json"
    cli_llm_output_path = tmp_path / "cli.review.llm.json"

    api_result = review_file(
        "tests/fixtures/markdown/clean_article.md",
        "tests/fixtures/profiles/default.yml",
        output_format="json",
        enable_llm=True,
        llm_provider_config=LLMProviderConfig(provider="mock"),
        llm_fail_on="warning",
        include_combined_result=True,
    )
    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--format",
            "json",
            "--output",
            str(cli_output_path),
            "--enable-llm",
            "--llm-output",
            str(cli_llm_output_path),
            "--llm-fail-on",
            "warning",
        ]
    )

    assert exit_code == 1
    assert api_result.review_result.model_dump(mode="json", exclude_none=True) == json.loads(
        cli_output_path.read_text(encoding="utf-8")
    )
    assert api_result.llm_result.model_dump(mode="json", exclude_none=True) == json.loads(
        cli_llm_output_path.read_text(encoding="utf-8")
    )


def test_api_and_cli_batch_main_path_stay_aligned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reviewer = _SemanticReviewer(_semantic_output())
    monkeypatch.setattr(
        "content_review_engine.workflows.create_llm_reviewer",
        lambda *args, **kwargs: reviewer,
    )
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: reviewer,
    )
    cli_output_path = tmp_path / "cli.batch.json"
    cli_llm_output_path = tmp_path / "cli.batch.llm.json"

    api_result = review_batch(
        "tests/fixtures/batch/articles",
        "tests/fixtures/batch/profile.yml",
        recursive=True,
        output_format="json",
        enable_llm=True,
        llm_provider_config=LLMProviderConfig(provider="mock"),
        llm_fail_on="warning",
        include_combined_result=True,
    )
    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--format",
            "json",
            "--output",
            str(cli_output_path),
            "--enable-llm",
            "--llm-output",
            str(cli_llm_output_path),
            "--llm-fail-on",
            "warning",
        ]
    )

    assert exit_code == 1
    assert api_result.batch_result.model_dump(mode="json", exclude_none=True) == json.loads(
        cli_output_path.read_text(encoding="utf-8")
    )
    assert api_result.llm_sidecar_result.model_dump(
        mode="json",
        exclude_none=True,
    ) == json.loads(cli_llm_output_path.read_text(encoding="utf-8"))


def test_python_api_docs_and_examples_exist_and_lock_boundaries() -> None:
    python_api_doc = PYTHON_API_DOC.read_text(encoding="utf-8")
    example_readme = EXAMPLE_README.read_text(encoding="utf-8")

    assert "review_file(" in python_api_doc
    assert "review_batch(" in python_api_doc
    assert "deterministic-only by default" in python_api_doc
    assert "enable_llm=False" in python_api_doc
    assert "does not auto-enable LLM" in python_api_doc
    assert "does not read `.env` automatically" in python_api_doc
    assert "does not accept raw API keys" in python_api_doc
    assert "LLM findings do not enter deterministic `ReviewResult.findings`" in python_api_doc
    assert "combined output remains explicit opt-in" in python_api_doc
    assert "examples/python_api_usage/single_file_review.py" in python_api_doc
    assert "examples/python_api_usage/batch_review.py" in python_api_doc
    assert "review_file(" in example_readme
    assert "review_batch(" in example_readme
    assert "mock" in example_readme


def test_python_api_examples_do_not_require_real_llm_api() -> None:
    single_example = Path("examples/python_api_usage/single_file_review.py").read_text(
        encoding="utf-8"
    )
    batch_example = Path("examples/python_api_usage/batch_review.py").read_text(
        encoding="utf-8"
    )

    assert "OPENAI_API_KEY" not in single_example
    assert "OPENAI_API_KEY" not in batch_example
    assert ".env" not in single_example
    assert ".env" not in batch_example
