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
        self.calls: list[object] = []

    def run_semantic_review(
        self,
        request: object,
    ) -> ValidatedLLMSemanticReviewOutput:
        self.calls.append(request)
        return self.output


def test_batch_review_without_llm_preserves_existing_behavior(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_create_llm_reviewer(*args: object, **kwargs: object) -> None:
        raise AssertionError("LLM reviewer should not be created when LLM is disabled.")

    monkeypatch.setattr("content_review_engine.cli.create_llm_reviewer", fail_create_llm_reviewer)

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Batch review completed." in captured.out
    assert captured.err == ""


def test_batch_review_enable_llm_writes_batch_sidecar_without_changing_deterministic_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    batch_output_path = tmp_path / "batch.json"
    llm_output_path = tmp_path / "batch.llm.json"
    reviewer = _SemanticReviewer(
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
    )

    create_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_create_llm_reviewer(*args: object, **kwargs: object) -> _SemanticReviewer:
        create_calls.append((args, kwargs))
        return reviewer

    monkeypatch.setattr("content_review_engine.cli.create_llm_reviewer", fake_create_llm_reviewer)
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

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
            str(batch_output_path),
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

    captured = capsys.readouterr()
    batch_payload = json.loads(batch_output_path.read_text(encoding="utf-8"))
    llm_payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert len(create_calls) == 1
    assert len(reviewer.calls) == 3
    assert batch_payload["schema_version"] == "batch-review-result.v1"
    assert "llm_provider" not in batch_payload
    assert "llm_review" not in batch_payload
    assert llm_payload["schema_version"] == "llm-sidecar-result.v2"
    assert llm_payload["llm_provider"] == "pydanticai"
    assert llm_payload["llm_provider_source"] == "explicit"
    assert llm_payload["summary"] == {
        "file_count": 3,
        "succeeded_count": 3,
        "failed_count": 0,
        "skipped_count": 0,
        "finding_count": 3,
    }
    assert llm_payload["files"][0]["review"]["findings"][0]["rule_id"] == "llm.semantic.overclaim"
    assert "test-secret-value" not in llm_output_path.read_text(encoding="utf-8")


def test_batch_review_writes_llm_report_without_changing_deterministic_markdown(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "batch.llm.json"
    llm_report_path = tmp_path / "batch.llm.md"

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--format",
            "markdown",
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
            "--llm-report",
            str(llm_report_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "# Batch Content Review Report" in captured.out
    assert "## LLM Review" not in captured.out
    assert "Batch LLM Review Report" in llm_report_path.read_text(encoding="utf-8")


def test_batch_review_enable_llm_report_only_writes_markdown_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_report_path = tmp_path / "batch.llm.md"

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--enable-llm",
            "--llm-report",
            str(llm_report_path),
        ]
    )

    captured = capsys.readouterr()
    report = llm_report_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert captured.err == ""
    assert "# Batch LLM Review Report" in report
    assert "| Files Reviewed | 3 |" in report
    assert not (tmp_path / "batch.llm.json").exists()


def test_batch_review_report_index_includes_deterministic_and_llm_outputs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    deterministic_output_path = tmp_path / "batch.md"
    llm_output_path = tmp_path / "batch.llm.json"
    llm_report_path = tmp_path / "batch.llm.md"
    report_index_path = tmp_path / "batch.index.md"

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--format",
            "markdown",
            "--output",
            str(deterministic_output_path),
            "--enable-llm",
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
    assert "| Files Reviewed | 3 |" in report
    assert "## LLM File Status Summary" in report


def test_batch_review_partial_llm_failure_is_recorded_and_returns_non_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "batch.llm.json"
    llm_report_path = tmp_path / "batch.llm.md"

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self
        if Path(request.content_path).name == "forbidden.md":
            raise LLMProviderError("mock provider failure")
        return ValidatedLLMSemanticReviewOutput(summary="No issues.", findings=())

    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.PydanticAIReviewer.run_semantic_review",
        fake_review,
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(llm_output_path),
            "--llm-report",
            str(llm_report_path),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(llm_output_path.read_text(encoding="utf-8"))
    report = llm_report_path.read_text(encoding="utf-8")

    assert exit_code == 2
    assert "Files discovered: 3" in captured.out
    assert "Files with findings: 2" in captured.out
    assert "Findings: 2" in captured.out
    assert captured.err == ""
    assert payload["summary"] == {
        "file_count": 3,
        "succeeded_count": 2,
        "failed_count": 1,
        "skipped_count": 0,
        "finding_count": 0,
    }
    assert payload["files"][1]["status"] == "failed"
    assert payload["files"][1]["error"] == {
        "error_type": "LLMProviderError",
        "message": "mock provider failure",
    }
    assert "| Files With LLM Errors | 1 |" in report
    assert "forbidden.md | failed | 0 | LLMProviderError: mock provider failure |" in report


def test_batch_review_partial_llm_failure_report_index_includes_error_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "batch.llm.json"
    report_index_path = tmp_path / "batch.index.md"

    def fake_review(self, request):  # type: ignore[no-untyped-def]
        del self
        if Path(request.content_path).name == "forbidden.md":
            raise LLMProviderError("mock provider failure")
        return ValidatedLLMSemanticReviewOutput(summary="No issues.", findings=())

    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.PydanticAIReviewer.run_semantic_review",
        fake_review,
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(llm_output_path),
            "--report-index",
            str(report_index_path),
        ]
    )

    captured = capsys.readouterr()
    report = report_index_path.read_text(encoding="utf-8")

    assert exit_code == 2
    assert captured.err == ""
    assert "| Files With LLM Errors | 1 |" in report
    assert "## LLM Error Summary" in report
    assert "mock provider failure" in report


def test_batch_review_provider_execution_failure_records_per_file_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llm_output_path = tmp_path / "batch.llm.json"

    def fail_run_semantic_review(self, request):  # type: ignore[no-untyped-def]
        del self, request
        raise LLMProviderError("provider exploded")

    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.PydanticAIReviewer.run_semantic_review",
        fail_run_semantic_review,
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
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

    payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 2
    assert payload["summary"]["failed_count"] == 3
    assert all(item["status"] == "failed" for item in payload["files"])


def test_batch_review_parse_failure_is_recorded_in_sidecar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llm_output_path = tmp_path / "batch.llm.json"

    def fail_run_semantic_review(self, request):  # type: ignore[no-untyped-def]
        del self, request
        raise LLMSemanticReviewOutputParseError("Invalid JSON response.")

    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.PydanticAIReviewer.run_semantic_review",
        fail_run_semantic_review,
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
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

    payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 2
    assert payload["files"][0]["error"]["error_type"] == "LLMSemanticReviewOutputParseError"


def test_batch_review_validation_failure_is_recorded_in_sidecar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llm_output_path = tmp_path / "batch.llm.json"

    def fail_run_semantic_review(self, request):  # type: ignore[no-untyped-def]
        del self, request
        raise LLMSemanticReviewOutputValidationError("findings[0].severity is invalid")

    monkeypatch.setattr(
        "content_review_engine.llm.pydanticai.PydanticAIReviewer.run_semantic_review",
        fail_run_semantic_review,
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
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

    payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 2
    assert payload["files"][0]["error"]["error_type"] == "LLMSemanticReviewOutputValidationError"


def test_batch_review_pydanticai_requires_api_key_env(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-output",
            str(tmp_path / "batch.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: LLM provider secret reference is missing" in captured.err


def test_batch_review_pydanticai_missing_environment_variable_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(tmp_path / "batch.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: LLM provider secret environment variable 'OPENAI_API_KEY' is not set." in captured.err


def test_batch_review_pydanticai_empty_environment_variable_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(tmp_path / "batch.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: LLM provider secret environment variable 'OPENAI_API_KEY' is empty." in captured.err


def test_batch_review_provider_construction_failure_returns_non_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    def fail_create_llm_reviewer(*args: object, **kwargs: object) -> None:
        raise LLMProviderError("construction failed")

    monkeypatch.setattr("content_review_engine.cli.create_llm_reviewer", fail_create_llm_reviewer)

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--enable-llm",
            "--llm-provider",
            "pydanticai",
            "--llm-model",
            "openai:gpt-4o-mini",
            "--llm-api-key-env",
            "OPENAI_API_KEY",
            "--llm-output",
            str(tmp_path / "batch.llm.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: construction failed" in captured.err


def test_batch_review_llm_output_write_failure_returns_non_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "batch.llm.json"
    original_write_text = Path.write_text

    def fail_write_text(self, data: str, encoding: str | None = None) -> int:
        if self == llm_output_path:
            raise OSError("disk full")
        return original_write_text(self, data, encoding=encoding)

    monkeypatch.setattr(Path, "write_text", fail_write_text)

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: Failed to write LLM sidecar:" in captured.err
    assert "disk full" in captured.err


def test_batch_review_llm_report_write_failure_returns_non_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_report_path = tmp_path / "batch.llm.md"
    original_write_text = Path.write_text

    def fail_write_text(self, data: str, encoding: str | None = None) -> int:
        if self == llm_report_path:
            raise OSError("disk full")
        return original_write_text(self, data, encoding=encoding)

    monkeypatch.setattr(Path, "write_text", fail_write_text)

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--enable-llm",
            "--llm-report",
            str(llm_report_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: Failed to write LLM Markdown report:" in captured.err
    assert "disk full" in captured.err


def test_batch_review_report_index_write_failure_returns_non_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "batch.llm.json"
    report_index_path = tmp_path / "batch.index.md"
    original_write_text = Path.write_text

    def fail_write_text(self, data: str, encoding: str | None = None) -> int:
        if self == report_index_path:
            raise OSError("disk full")
        return original_write_text(self, data, encoding=encoding)

    monkeypatch.setattr(Path, "write_text", fail_write_text)

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
            "--report-index",
            str(report_index_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert llm_output_path.exists()
    assert "Error: Failed to write report index:" in captured.err
    assert "disk full" in captured.err


def test_batch_review_testmodel_provider_does_not_access_real_network_or_api_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "batch.llm.json"

    def fail_create_connection(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError(f"Unexpected network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--enable-llm",
            "--llm-provider",
            "pydantic-ai-testmodel",
            "--llm-output",
            str(llm_output_path),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(llm_output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.err == ""
    assert payload["llm_provider"] == "pydantic-ai-testmodel"
