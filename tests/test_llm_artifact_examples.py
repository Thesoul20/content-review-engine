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
    assert "advisory semantic review suggestions" in readme
    assert "Quality gate interpretation remains deterministic-only" in readme
    assert "not persisted to a" in readme
    assert "review-state file or back into JSON sidecars" in readme


def test_example_files_do_not_contain_api_key_or_secret_text() -> None:
    banned_patterns = (
        re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
        re.compile(r"api[_ -]?key", re.IGNORECASE),
        re.compile(r"secret", re.IGNORECASE),
    )

    for path in _iter_example_files():
        content = _read(path)
        assert not any(pattern.search(content) for pattern in banned_patterns), path
