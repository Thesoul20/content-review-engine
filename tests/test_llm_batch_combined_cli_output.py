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
        self.calls: list[object] = []

    def run_semantic_review(
        self,
        request: object,
    ) -> ValidatedLLMSemanticReviewOutput:
        self.calls.append(request)
        return self.output


def test_cli_batch_parser_accepts_combined_output_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "batch",
            "articles",
            "--profile",
            "profile.yml",
            "--combined-output",
            "batch.combined.md",
            "--combined-output-format",
            "json",
        ]
    )

    assert args.combined_output == "batch.combined.md"
    assert args.combined_output_format == "json"


def test_batch_combined_markdown_output_reuses_renderer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    combined_output_path = tmp_path / "batch.combined.md"
    llm_output_path = tmp_path / "batch.llm.json"
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")
    reviewer = _SemanticReviewer(
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
    )
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: reviewer,
    )

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
            "--combined-output",
            str(combined_output_path),
        ]
    )

    captured = capsys.readouterr()
    report = combined_output_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert captured.err == ""
    assert report.startswith("# Batch Combined Content Review Report\n")
    assert "| LLM Batch Status | all_succeeded |" in report
    assert "| LLM Provider | pydanticai |" in report
    assert "| LLM Succeeded | 3 |" in report
    assert "| LLM Failed | 0 |" in report
    assert "| warning | llm.unsafe_medical_claim | llm | yes | no | 0.84 | 1:1 | Possible overclaim. | Use a softer claim. |" in report


def test_batch_combined_json_output_reuses_serializer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    combined_output_path = tmp_path / "batch.combined.json"
    llm_output_path = tmp_path / "batch.llm.json"
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
    assert payload["schema_version"] == "batch-combined-review-result.v1"
    assert payload["batch_review_result"]["schema_version"] == "batch-review-result.v1"
    assert payload["llm"]["summary"]["succeeded_count"] == 3
    assert payload["llm"]["summary"]["failed_count"] == 0
    assert payload["llm"]["result"]["schema_version"] == "llm-sidecar-result.v2"
    assert payload["llm"]["files"][0]["status"] == "succeeded"
    assert payload["llm"]["files"][0]["finding_candidates"][0]["rule_id"] == "llm.semantic_overclaim"


def test_batch_combined_output_with_llm_disabled_records_not_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    combined_output_path = tmp_path / "batch.combined.json"

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
    assert payload["llm"]["result"] is None
    assert payload["llm"]["summary"]["not_run_count"] == 3
    assert payload["llm"]["summary"]["failed_count"] == 0
    assert all(item["status"] == "not_run" for item in payload["llm"]["files"])


def test_batch_combined_output_records_partial_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    combined_output_path = tmp_path / "batch.combined.json"
    llm_output_path = tmp_path / "batch.llm.json"
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")

    class _PartialFailReviewer:
        model = "openai:gpt-4o-mini"
        config = type("Config", (), {"provider": "pydanticai"})()

        def __init__(self) -> None:
            self.calls = 0

        def run_semantic_review(
            self,
            request: object,
        ) -> ValidatedLLMSemanticReviewOutput:
            del request
            self.calls += 1
            if self.calls == 2:
                raise LLMProviderTimeoutError(
                    "Timed out while waiting for semantic review output."
                )
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

    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _PartialFailReviewer(),
    )

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
            "--combined-output",
            str(combined_output_path),
            "--combined-output-format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(combined_output_path.read_text(encoding="utf-8"))

    assert exit_code == 2
    assert captured.err == ""
    assert payload["llm"]["summary"]["succeeded_count"] == 2
    assert payload["llm"]["summary"]["failed_count"] == 1
    assert payload["llm"]["summary"]["error_count"] == 1
    assert [item["status"] for item in payload["llm"]["files"]] == [
        "succeeded",
        "failed",
        "succeeded",
    ]
    assert payload["llm"]["files"][1]["error"] == {
        "type": "LLMProviderTimeoutError",
        "message": "Timed out while waiting for semantic review output.",
    }


def test_batch_combined_output_records_all_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    combined_output_path = tmp_path / "batch.combined.md"
    llm_output_path = tmp_path / "batch.llm.json"
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
            "--combined-output",
            str(combined_output_path),
        ]
    )

    captured = capsys.readouterr()
    report = combined_output_path.read_text(encoding="utf-8")

    assert exit_code == 2
    assert captured.err == ""
    assert "| LLM Batch Status | all_failed |" in report
    assert "| LLM Failed | 3 |" in report
    assert "| LLM Errors | 3 |" in report
    assert "All LLM review attempts failed in this batch" in report
    assert report.count("LLMProviderTimeoutError") >= 3


def test_batch_outputs_can_coexist_with_combined_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    batch_output_path = tmp_path / "batch.json"
    llm_output_path = tmp_path / "batch.llm.json"
    combined_output_path = tmp_path / "batch.combined.md"
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput(summary="No issues.", findings=())
        ),
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
            str(batch_output_path),
            "--enable-llm",
            "--llm-output",
            str(llm_output_path),
            "--combined-output",
            str(combined_output_path),
        ]
    )

    captured = capsys.readouterr()
    batch_payload = json.loads(batch_output_path.read_text(encoding="utf-8"))
    llm_payload = json.loads(llm_output_path.read_text(encoding="utf-8"))
    combined_report = combined_output_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert batch_payload["schema_version"] == "batch-review-result.v1"
    assert llm_payload["schema_version"] == "llm-sidecar-result.v2"
    assert combined_report.startswith("# Batch Combined Content Review Report\n")


def test_batch_without_combined_output_preserves_existing_behavior(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    batch_output_path = tmp_path / "batch.json"

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
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert not (tmp_path / "batch.combined.json").exists()
    assert not (tmp_path / "batch.combined.md").exists()


def test_batch_combined_output_does_not_change_quality_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    combined_output_path = tmp_path / "batch.combined.json"
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput.model_validate(
                {
                    "schema_version": "llm-semantic-review-output.v1",
                    "summary": "One critical semantic issue found.",
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
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--recursive",
            "--fail-on",
            "error",
            "--enable-llm",
            "--llm-output",
            str(tmp_path / "batch.llm.json"),
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
    assert payload["llm"]["summary"]["succeeded_count"] == 3
    assert payload["llm"]["files"][0]["finding_candidates"][0]["severity"] == "critical"
    assert payload["batch_review_result"]["summary"]["severity_counts"]["error"] == 0


def test_cli_batch_combined_output_format_rejects_invalid_value(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "batch",
            "tests/fixtures/batch/articles",
            "--profile",
            "tests/fixtures/batch/profile.yml",
            "--combined-output",
            "combined.out",
            "--combined-output-format",
            "yaml",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "invalid choice: 'yaml'" in captured.err
