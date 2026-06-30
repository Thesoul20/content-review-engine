from __future__ import annotations

from pathlib import Path

import pytest

from content_review_engine.cli import build_parser, main
from content_review_engine.llm import ValidatedLLMSemanticReviewOutput


class _SemanticReviewer:
    def __init__(self, output: ValidatedLLMSemanticReviewOutput) -> None:
        self.output = output
        self.model = "openai:gpt-4o-mini"
        self.config = type("Config", (), {"provider": "pydanticai"})()

    def run_semantic_review(
        self,
        request: object,
    ) -> ValidatedLLMSemanticReviewOutput:
        del request
        return self.output


def test_cli_batch_parser_accepts_llm_fail_on() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "batch",
            "articles",
            "--profile",
            "profile.yml",
            "--llm-fail-on",
            "critical",
        ]
    )

    assert args.llm_fail_on == "critical"


def test_cli_batch_llm_fail_on_requires_enable_llm(
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
            "--llm-fail-on",
            "warning",
            "--combined-output",
            str(tmp_path / "batch.combined.json"),
            "--combined-output-format",
            "json",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Error: --llm-fail-on requires --enable-llm" in captured.err


def test_cli_batch_default_quality_gate_ignores_llm_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "batch.llm.json"
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput.model_validate(
                {
                    "schema_version": "llm-semantic-review-output.v1",
                    "summary": "Critical issue found.",
                    "findings": [
                        {
                            "rule_id": "llm.semantic.risky_advice",
                            "severity": "critical",
                            "line": 1,
                            "column": 1,
                            "message": "Critical semantic issue.",
                            "evidence": "evidence",
                            "suggestion": "fix",
                            "confidence": 0.9,
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
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Batch review completed." in captured.out
    assert captured.err == ""


def test_cli_batch_llm_fail_on_returns_exit_code_one_for_matching_llm_finding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    llm_output_path = tmp_path / "batch.llm.json"
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")
    monkeypatch.setattr(
        "content_review_engine.cli.create_llm_reviewer",
        lambda *args, **kwargs: _SemanticReviewer(
            ValidatedLLMSemanticReviewOutput.model_validate(
                {
                    "schema_version": "llm-semantic-review-output.v1",
                    "summary": "Error issue found.",
                    "findings": [
                        {
                            "rule_id": "llm.semantic.risky_advice",
                            "severity": "error",
                            "line": 1,
                            "column": 1,
                            "message": "Error semantic issue.",
                            "evidence": "evidence",
                            "suggestion": "fix",
                            "confidence": 0.9,
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
            "--llm-fail-on",
            "error",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Batch review completed." in captured.out
    assert captured.err == ""
