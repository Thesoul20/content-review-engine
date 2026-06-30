from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_review_engine.cli import build_parser, main
from content_review_engine.llm import (
    LLMProviderTimeoutError,
    ValidatedLLMSemanticReviewOutput,
)


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

    def run_semantic_review(self, request: object) -> ValidatedLLMSemanticReviewOutput:
        del request
        return self.output


def test_cli_review_parser_accepts_combined_output_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "review",
            "article.md",
            "--profile",
            "profile.yml",
            "--combined-output",
            "combined.md",
            "--combined-output-format",
            "json",
        ]
    )

    assert args.combined_output == "combined.md"
    assert args.combined_output_format == "json"


def test_single_file_review_combined_markdown_output_reuses_renderer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    combined_output_path = tmp_path / "review.combined.md"
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput.model_validate(
                {
                    "schema_version": "llm-semantic-review-output.v1",
                    "summary": "One semantic issue found.",
                    "findings": [
                        {
                            "rule_id": "Unsafe Medical Claim",
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
        ),
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-report",
            str(tmp_path / "review.llm.md"),
            "--combined-output",
            str(combined_output_path),
        ]
    )

    captured = capsys.readouterr()
    report = combined_output_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert captured.err == ""
    assert report.startswith("# Combined Content Review Report\n")
    assert "| LLM Status | succeeded |" in report
    assert "| warning | llm.unsafe_medical_claim | llm | yes | no | 0.84 | 1:1 | Possible overclaim. | Use a softer claim. |" in report
    assert "## Deterministic Review" in report


def test_single_file_review_combined_json_output_reuses_serializer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    combined_output_path = tmp_path / "review.combined.json"
    llm_output_path = tmp_path / "review.llm.json"
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput.model_validate(
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
        ),
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(llm_output_path),
            "--combined-output",
            str(combined_output_path),
            "--combined-output-format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(combined_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.err == ""
    assert payload["schema_version"] == "single-file-combined-review-result.v1"
    assert payload["review_result"]["schema_version"] == "review-result.v1"
    assert payload["llm"]["status"] == "succeeded"
    assert payload["llm"]["result"]["schema_version"] == "llm-review-result.v1"
    assert payload["llm"]["finding_candidates"][0]["rule_id"] == "llm.semantic_overclaim"


def test_single_file_review_combined_output_with_llm_disabled_records_not_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    combined_output_path = tmp_path / "review.combined.json"

    def fail_create_llm_reviewer(*args: object, **kwargs: object) -> None:
        raise AssertionError("LLM reviewer should not be created when LLM is disabled.")

    monkeypatch.setattr("content_review_engine.cli.create_llm_reviewer", fail_create_llm_reviewer)

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--combined-output",
            str(combined_output_path),
            "--combined-output-format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(combined_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.err == ""
    assert payload["llm"]["status"] == "not_run"
    assert payload["llm"]["error"] is None
    assert payload["llm"]["result"] is None
    assert payload["llm"]["finding_candidates"] == []


def test_single_file_review_combined_output_records_failed_llm_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    combined_output_path = tmp_path / "review.combined.json"
    llm_output_path = tmp_path / "review.llm.json"
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    class _FailingReviewer:
        model = "openai:gpt-4o-mini"
        config = type("Config", (), {"provider": "pydanticai"})()

        def run_semantic_review(self, request: object) -> object:
            del request
            raise LLMProviderTimeoutError(
                "Timed out while waiting for semantic review output."
            )

    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _FailingReviewer(),
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(llm_output_path),
            "--combined-output",
            str(combined_output_path),
            "--combined-output-format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(combined_output_path.read_text(encoding="utf-8"))

    assert exit_code == 2
    assert "Error: Timed out while waiting for semantic review output." in captured.err
    assert payload["llm"]["status"] == "failed"
    assert payload["llm"]["error"] == {
        "type": "LLMProviderTimeoutError",
        "message": "Timed out while waiting for semantic review output.",
        "provider": "pydanticai",
        "retryable": True,
    }
    assert payload["llm"]["result"] is None
    assert payload["llm"]["finding_candidates"] == []


def test_single_file_review_outputs_can_coexist_with_combined_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    review_output_path = tmp_path / "review.json"
    llm_output_path = tmp_path / "review.llm.json"
    combined_output_path = tmp_path / "review.combined.md"
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput(summary="No issues.", findings=())
        ),
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/forbidden_terms_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--format",
            "json",
            "--output",
            str(review_output_path),
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
            "--combined-output",
            str(combined_output_path),
        ]
    )

    captured = capsys.readouterr()
    review_payload = json.loads(review_output_path.read_text(encoding="utf-8"))
    llm_payload = json.loads(llm_output_path.read_text(encoding="utf-8"))
    combined_report = combined_output_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert review_payload["schema_version"] == "review-result.v1"
    assert "llm_review" not in review_payload
    assert llm_payload["schema_version"] == "llm-review-result.v1"
    assert combined_report.startswith("# Combined Content Review Report\n")


def test_single_file_review_without_combined_output_preserves_existing_behavior(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    review_output_path = tmp_path / "review.json"

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--format",
            "json",
            "--output",
            str(review_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert not (tmp_path / "review.combined.json").exists()


def test_single_file_review_combined_output_does_not_change_quality_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    combined_output_path = tmp_path / "review.combined.json"
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput.model_validate(
                {
                    "schema_version": "llm-semantic-review-output.v1",
                    "summary": "One semantic issue found.",
                    "findings": [
                        {
                            "rule_id": "llm.semantic.overclaim",
                            "severity": "critical",
                            "line": 1,
                            "column": 1,
                            "message": "Critical semantic issue.",
                            "evidence": "绝对安全",
                            "suggestion": "Use a softer claim.",
                            "confidence": 0.84,
                        }
                    ],
                }
            )
        ),
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/forbidden_terms_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--fail-on",
            "error",
            "--enable-llm",
            "--llm-output",
            str(tmp_path / "review.llm.json"),
            "--combined-output",
            str(combined_output_path),
            "--combined-output-format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(combined_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.err == ""
    assert payload["llm"]["status"] == "succeeded"
    assert payload["llm"]["finding_candidates"][0]["severity"] == "critical"


def test_cli_review_combined_output_format_rejects_invalid_value(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--combined-output",
            "combined.out",
            "--combined-output-format",
            "yaml",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "invalid choice: 'yaml'" in captured.err
