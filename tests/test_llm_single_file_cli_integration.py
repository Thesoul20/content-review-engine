from __future__ import annotations

import json
from pathlib import Path
import socket

import pytest

from content_review_engine.cli import main
from content_review_engine.llm import (
    LLMProviderError,
    LLMSemanticReviewOutputParseError,
    LLMSemanticReviewOutputValidationError,
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

    def run_semantic_review(
        self,
        request: object,
    ) -> ValidatedLLMSemanticReviewOutput:
        del request
        return self.output


def test_single_file_review_without_llm_preserves_existing_behavior(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_create_llm_reviewer(*args: object, **kwargs: object) -> None:
        raise AssertionError("LLM reviewer should not be created when LLM is disabled.")

    monkeypatch.setattr("content_review_engine.cli.create_llm_reviewer", fail_create_llm_reviewer)

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Review completed." in captured.out
    assert "Findings: 0" in captured.out
    assert captured.err == ""


def test_single_file_review_enable_llm_writes_raw_llm_review_result_sidecar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
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
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "llm.semantic.overclaim" not in captured.out
    assert captured.err == ""
    assert payload["schema_version"] == "llm-review-result.v1"
    assert payload["provider"] == "pydanticai"
    assert payload["model"] == "openai:gpt-4o-mini"
    assert payload["findings"][0]["rule_id"] == "llm.semantic.overclaim"
    assert payload["summary"]["summary"] == "One semantic issue found."


def test_single_file_review_sidecar_does_not_include_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llm_output_path = tmp_path / "review.llm.json"
    monkeypatch.setenv("OPENAI_API_KEY", "super-secret-value")
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput(summary="No issues.", findings=())
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
        ]
    )

    assert exit_code == 0
    assert "super-secret-value" not in llm_output_path.read_text(encoding="utf-8")


def test_single_file_review_enable_llm_report_only_writes_markdown_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_report_path = tmp_path / "review.llm.md"
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
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-report",
            str(llm_report_path),
        ]
    )

    captured = capsys.readouterr()
    report = llm_report_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert captured.err == ""
    assert "# LLM Review Report" in report
    assert "| File | tests/fixtures/markdown/clean_article.md |" in report
    assert "| Advisory | yes |" in report
    assert "| Quality Gate Participation | no |" in report
    assert "## Manual Review Checklist" in report
    assert "| LLM-001 | medium | needs_review | pending | no | llm.semantic.overclaim | line 1, column 1 | Possible overclaim. | - |" in report
    assert "Possible overclaim." in report
    assert not (tmp_path / "review.llm.json").exists()


def test_single_file_review_enable_llm_output_and_report_can_be_used_together(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "review.llm.json"
    llm_report_path = tmp_path / "review.llm.md"
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput(summary="No issues.", findings=())
        ),
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(llm_output_path),
            "--llm-report",
            str(llm_report_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert llm_output_path.exists()
    assert llm_report_path.exists()
    assert "# LLM Review Report" in llm_report_path.read_text(encoding="utf-8")


def test_single_file_review_report_index_includes_deterministic_and_llm_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    deterministic_output_path = tmp_path / "review.md"
    llm_output_path = tmp_path / "review.llm.json"
    llm_report_path = tmp_path / "review.llm.md"
    report_index_path = tmp_path / "review.index.md"
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
            "--format",
            "markdown",
            "--output",
            str(deterministic_output_path),
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(llm_output_path),
            "--llm-report",
            str(llm_report_path),
            "--report-index",
            str(report_index_path),
        ]
    )

    captured = capsys.readouterr()
    report = report_index_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert "| Deterministic Output | " in report
    assert "| LLM JSON Sidecar | " in report
    assert "| LLM Markdown Report | " in report
    assert "| Report Index | " in report
    assert "| Quality Gate Source | deterministic review only |" in report
    assert "| LLM Findings | 1 |" in report
    assert "| Summary | One semantic issue found. |" in report
    assert "| Advisory | yes |" in report
    assert "advisory semantic review suggestions" in report
    assert "## Manual Review Workflow" in report
    assert "Current manual review checklist items: 1." in report


def test_single_file_manual_review_does_not_change_exit_code_or_quality_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_report_path = tmp_path / "review.llm.md"
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
                            "severity": "critical",
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
            "--fail-on",
            "warning",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-report",
            str(llm_report_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Findings: 0" in captured.out
    assert "Possible overclaim." not in captured.out
    assert "| LLM-001 | high | needs_review | pending | no |" in llm_report_path.read_text(encoding="utf-8")


def test_single_file_review_llm_provider_flags_require_provider_or_config(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-output",
            str(tmp_path / "review.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: LLM provider config flags require --llm-provider or --llm-config." in captured.err


def test_single_file_review_pydanticai_requires_api_key_env(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
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
            "--llm-output",
            str(tmp_path / "review.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: LLM provider secret reference is missing" in captured.err


def test_single_file_review_pydanticai_missing_environment_variable_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

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
            str(tmp_path / "review.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: LLM provider secret environment variable 'OPENAI_API_KEY' is not set." in captured.err


def test_single_file_review_pydanticai_empty_environment_variable_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "   ")

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
            str(tmp_path / "review.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: LLM provider secret environment variable 'OPENAI_API_KEY' is empty." in captured.err


def test_single_file_review_provider_execution_failure_returns_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    class FailingReviewer:
        config = type("Config", (), {"provider": "pydanticai"})()
        model = "openai:gpt-4o-mini"

        def run_semantic_review(self, request: object) -> ValidatedLLMSemanticReviewOutput:
            del request
            raise LLMProviderError("provider failed")

    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: FailingReviewer(),
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(tmp_path / "review.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: provider failed" in captured.err


def test_single_file_review_parse_failure_returns_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    class ParseFailReviewer:
        config = type("Config", (), {"provider": "pydanticai"})()
        model = "openai:gpt-4o-mini"

        def run_semantic_review(self, request: object) -> ValidatedLLMSemanticReviewOutput:
            del request
            raise LLMSemanticReviewOutputParseError("Could not parse semantic output.")

    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: ParseFailReviewer(),
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(tmp_path / "review.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: Could not parse semantic output." in captured.err


def test_single_file_review_validation_failure_returns_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    class ValidationFailReviewer:
        config = type("Config", (), {"provider": "pydanticai"})()
        model = "openai:gpt-4o-mini"

        def run_semantic_review(self, request: object) -> ValidatedLLMSemanticReviewOutput:
            del request
            raise LLMSemanticReviewOutputValidationError("Semantic output schema mismatch.")

    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: ValidationFailReviewer(),
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(tmp_path / "review.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: Semantic output schema mismatch." in captured.err


def test_single_file_review_sidecar_write_failure_returns_error_after_deterministic_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "review.llm.json"
    original_write_text = Path.write_text
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput(summary="No issues.", findings=())
        ),
    )

    def fail_write_text(self: Path, data: str, encoding: str | None = None) -> int:
        if self == llm_output_path:
            raise OSError("disk full")
        return original_write_text(self, data, encoding=encoding)

    monkeypatch.setattr(Path, "write_text", fail_write_text)

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Findings: 0" in captured.out
    assert "Error: Failed to write LLM review result:" in captured.err
    assert "disk full" in captured.err


def test_single_file_review_llm_report_write_failure_returns_error_after_deterministic_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_report_path = tmp_path / "review.llm.md"
    original_write_text = Path.write_text
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput(summary="No issues.", findings=())
        ),
    )

    def fail_write_text(self: Path, data: str, encoding: str | None = None) -> int:
        if self == llm_report_path:
            raise OSError("disk full")
        return original_write_text(self, data, encoding=encoding)

    monkeypatch.setattr(Path, "write_text", fail_write_text)

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-report",
            str(llm_report_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Findings: 0" in captured.out
    assert "Error: Failed to write LLM Markdown report:" in captured.err
    assert "disk full" in captured.err


def test_single_file_review_report_index_write_failure_returns_error_after_other_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "review.llm.json"
    report_index_path = tmp_path / "review.index.md"
    original_write_text = Path.write_text
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput(summary="No issues.", findings=())
        ),
    )

    def fail_write_text(self: Path, data: str, encoding: str | None = None) -> int:
        if self == report_index_path:
            raise OSError("disk full")
        return original_write_text(self, data, encoding=encoding)

    monkeypatch.setattr(Path, "write_text", fail_write_text)

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(llm_output_path),
            "--report-index",
            str(report_index_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Findings: 0" in captured.out
    assert llm_output_path.exists()
    assert "Error: Failed to write report index:" in captured.err
    assert "disk full" in captured.err


def test_single_file_review_fake_semantic_path_does_not_touch_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")
    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Unexpected network call.")
        ),
    )
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput(summary="No issues.", findings=())
        ),
    )

    exit_code = main(
        [
            "review",
            "tests/fixtures/markdown/clean_article.md",
            "--profile",
            "tests/fixtures/profiles/default.yml",
            "--enable-llm",
            "--llm-config",
            "examples/llm/pydanticai/llm-provider.yml",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(tmp_path / "review.llm.json"),
        ]
    )

    assert exit_code == 0
