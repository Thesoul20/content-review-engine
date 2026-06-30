from __future__ import annotations

import json
import re
from pathlib import Path


EXAMPLE_ROOT = Path("examples/llm_review_artifacts")
README_PATH = EXAMPLE_ROOT / "README.md"

SINGLE_DIR = EXAMPLE_ROOT / "single-file"
SINGLE_INPUT = SINGLE_DIR / "input.md"
SINGLE_PROFILE = SINGLE_DIR / "profile.yml"
SINGLE_DETERMINISTIC_REPORT = SINGLE_DIR / "deterministic-report.md"
SINGLE_LLM_JSON = SINGLE_DIR / "llm-result.json"
SINGLE_LLM_REPORT = SINGLE_DIR / "llm-report.md"
SINGLE_COMBINED_JSON = SINGLE_DIR / "combined-result.json"
SINGLE_COMBINED_REPORT = SINGLE_DIR / "combined-report.md"
SINGLE_INDEX = SINGLE_DIR / "review-index.md"

BATCH_DIR = EXAMPLE_ROOT / "batch"
BATCH_INPUT_DIR = BATCH_DIR / "input"
BATCH_INPUT_A = BATCH_INPUT_DIR / "article-a.md"
BATCH_INPUT_B = BATCH_INPUT_DIR / "article-b.md"
BATCH_INPUT_ERROR = BATCH_INPUT_DIR / "article-with-llm-error.md"
BATCH_PROFILE = BATCH_DIR / "profile.yml"
BATCH_DETERMINISTIC_REPORT = BATCH_DIR / "deterministic-report.md"
BATCH_LLM_JSON = BATCH_DIR / "batch-llm-result.json"
BATCH_LLM_REPORT = BATCH_DIR / "batch-llm-report.md"
BATCH_COMBINED_JSON = BATCH_DIR / "batch-combined-result.json"
BATCH_COMBINED_REPORT = BATCH_DIR / "batch-combined-report.md"
BATCH_INDEX = BATCH_DIR / "batch-review-index.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _iter_example_files() -> tuple[Path, ...]:
    return tuple(path for path in EXAMPLE_ROOT.rglob("*") if path.is_file())


def test_example_root_readme_exists() -> None:
    assert README_PATH.exists()
    assert _read(README_PATH).strip()


def test_single_file_example_files_exist() -> None:
    paths = (
        SINGLE_INPUT,
        SINGLE_PROFILE,
        SINGLE_DETERMINISTIC_REPORT,
        SINGLE_LLM_JSON,
        SINGLE_LLM_REPORT,
        SINGLE_COMBINED_JSON,
        SINGLE_COMBINED_REPORT,
        SINGLE_INDEX,
    )

    for path in paths:
        assert path.exists()
        assert _read(path).strip()


def test_batch_example_files_exist() -> None:
    paths = (
        BATCH_INPUT_A,
        BATCH_INPUT_B,
        BATCH_INPUT_ERROR,
        BATCH_PROFILE,
        BATCH_DETERMINISTIC_REPORT,
        BATCH_LLM_JSON,
        BATCH_LLM_REPORT,
        BATCH_COMBINED_JSON,
        BATCH_COMBINED_REPORT,
        BATCH_INDEX,
    )

    for path in paths:
        assert path.exists()
        assert _read(path).strip()


def test_single_file_llm_json_is_parseable() -> None:
    data = json.loads(_read(SINGLE_LLM_JSON))

    assert data["schema_version"] == "llm-review-result.v1"
    assert len(data["findings"]) == 2


def test_batch_llm_json_is_parseable() -> None:
    data = json.loads(_read(BATCH_LLM_JSON))

    assert data["schema_version"] == "llm-sidecar-result.v2"
    assert data["summary"]["failed_count"] == 1
    assert any(item["status"] == "failed" for item in data["files"])


def test_single_file_combined_json_is_parseable() -> None:
    data = json.loads(_read(SINGLE_COMBINED_JSON))

    assert data["schema_version"] == "single-file-combined-review-result.v1"
    assert data["review_result"]["schema_version"] == "review-result.v1"
    assert data["llm"]["status"] == "succeeded"
    assert data["llm"]["advisory"] is True
    assert len(data["llm"]["finding_candidates"]) == 2


def test_batch_combined_json_is_parseable() -> None:
    data = json.loads(_read(BATCH_COMBINED_JSON))

    assert data["schema_version"] == "batch-combined-review-result.v1"
    assert data["batch_review_result"]["schema_version"] == "batch-review-result.v1"
    assert data["llm"]["summary"]["failed_count"] == 1
    assert data["llm"]["summary"]["advisory_finding_count"] == 2
    assert any(item["status"] == "failed" for item in data["llm"]["files"])


def test_single_file_llm_report_contains_advisory_policy() -> None:
    report = _read(SINGLE_LLM_REPORT)

    assert "## Advisory Policy" in report
    assert "LLM advisory severity only" in report
    assert "advisory semantic review suggestions" in report


def test_single_file_llm_report_contains_manual_review_checklist() -> None:
    report = _read(SINGLE_LLM_REPORT)

    assert "## Manual Review Checklist" in report
    assert "LLM-001" in report
    assert "needs_review" in report
    assert "pending" in report


def test_batch_llm_report_contains_execution_review_checklist() -> None:
    report = _read(BATCH_LLM_REPORT)

    assert "## LLM Execution Review Checklist" in report
    assert "LLM-ERR-001" in report
    assert "rerun_llm_review" in report


def test_combined_markdown_examples_contain_required_headings() -> None:
    single_report = _read(SINGLE_COMBINED_REPORT)
    batch_report = _read(BATCH_COMBINED_REPORT)

    assert "# Combined Content Review Report" in single_report
    assert "## Artifact Boundary" in single_report
    assert "## Deterministic Review Summary" in single_report
    assert "## LLM Review Summary" in single_report
    assert "## Quality Gate Behavior" in single_report
    assert "## Artifact Notes" in single_report
    assert "# Batch Combined Content Review Report" in batch_report
    assert "## Artifact Boundary" in batch_report
    assert "## Deterministic Batch Summary" in batch_report
    assert "## LLM Batch Summary" in batch_report
    assert "## Combined File Results" in batch_report
    assert "## LLM Findings by File" in batch_report
    assert "## Quality Gate Behavior" in batch_report
    assert "## Artifact Notes" in batch_report


def test_report_indexes_contain_manual_review_workflow() -> None:
    single_index = _read(SINGLE_INDEX)
    batch_index = _read(BATCH_INDEX)

    assert "## Manual Review Workflow" in single_index
    assert "## Manual Review Workflow" in batch_index
    assert "Current manual review checklist items: 2." in single_index
    assert "Current LLM execution review checklist items: 1;" in batch_index


def test_examples_readme_contains_artifact_map_and_boundaries() -> None:
    readme = _read(README_PATH)

    assert "## Artifact Map" in readme
    assert "## Canonical And Presentation Boundary" in readme
    assert "reference-only examples" in readme
    assert "`--output`: deterministic main output" in readme
    assert "`--llm-output`: raw LLM sidecar output" in readme
    assert "`--combined-output`: deterministic + LLM combined envelope or report output" in readme
    assert "combined-result.json" in readme
    assert "batch-combined-result.json" in readme
    assert "advisory semantic review suggestions" in readme
    assert "Quality gate interpretation remains deterministic-only" in readme
    assert "not persisted to a" in readme
    assert "review-state file or back into JSON sidecars" in readme


def test_example_files_do_not_contain_api_key_secret_or_traceback_text() -> None:
    banned_patterns = (
        re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
        re.compile(r"api[_ -]?key", re.IGNORECASE),
        re.compile(r"secret", re.IGNORECASE),
        re.compile(r"Traceback \(most recent call last\):"),
    )

    for path in _iter_example_files():
        content = _read(path)
        assert not any(pattern.search(content) for pattern in banned_patterns), path


def test_combined_markdown_examples_do_not_contain_local_absolute_paths() -> None:
    for path in (SINGLE_COMBINED_REPORT, BATCH_COMBINED_REPORT):
        content = _read(path)
        assert "/Users/" not in content
        assert "C:\\" not in content
