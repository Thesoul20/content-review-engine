from pathlib import Path


CLI_DOC = Path("docs/CLI.md")
ARCH_DOC = Path("docs/ARCHITECTURE.md")
DATA_MODELS_DOC = Path("docs/DATA_MODELS.md")
USAGE_DOC = Path("docs/LLM_PROVIDER_USAGE.md")
CI_DOC = Path("docs/CI.md")


def test_cli_docs_define_output_boundaries_and_behavior_matrix() -> None:
    content = CLI_DOC.read_text(encoding="utf-8")

    assert "## Output Artifact Boundaries" in content
    assert "## Combined Output Behavior Matrix" in content
    assert "`--output`: deterministic main output" in content
    assert "`--llm-output`: raw LLM sidecar output" in content
    assert "`--combined-output`: combined output" in content
    assert "`--combined-output` is explicit opt-in" in content
    assert "`--combined-output` does not auto-enable LLM review" in content
    assert "writes combined output with `llm.status = not_run`" in content
    assert "writes combined output with per-file `status = not_run`" in content
    assert "deterministic-only" in content


def test_architecture_and_data_model_docs_keep_combined_boundaries_aligned() -> None:
    architecture = ARCH_DOC.read_text(encoding="utf-8")
    data_models = DATA_MODELS_DOC.read_text(encoding="utf-8")

    assert "## Output Artifact Relationship" in architecture
    assert "SingleFileCombinedReviewResult / BatchCombinedReviewResult" in architecture
    assert "src/content_review_engine/llm/combined_envelope.py" in architecture
    assert "deterministic quality-gate evaluation remains upstream" in architecture
    assert "## Artifact Boundary Matrix" in data_models
    assert "| Combined output | `SingleFileCombinedReviewResult` | `BatchCombinedReviewResult` | `--combined-output` |" in data_models
    assert "src/content_review_engine/llm/combined_envelope.py" in data_models
    assert "when LLM is not enabled, combined output records `not_run` status" in data_models
    assert "LLM findings never enter deterministic `findings`" in data_models


def test_usage_and_ci_docs_explain_deterministic_only_quality_gate() -> None:
    usage = USAGE_DOC.read_text(encoding="utf-8")
    ci = CI_DOC.read_text(encoding="utf-8")

    assert "## Deterministic, Sidecar, And Combined Boundaries" in usage
    assert "`--combined-output` does not enable LLM by itself" in usage
    assert "src/content_review_engine/llm/combined_envelope.py" in usage
    assert "combined output does not change deterministic `severity_counts`" in usage
    assert "CI boundary for combined artifacts" in ci
    assert "`--combined-output` does not auto-enable LLM review" in ci
    assert "only deterministic findings can trigger exit code `1`" in ci
