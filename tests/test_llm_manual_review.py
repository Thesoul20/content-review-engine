from __future__ import annotations

from content_review_engine.llm import (
    LLMReviewFinding,
    LLMReviewResult,
    build_batch_llm_manual_review_items,
    build_llm_execution_review_items,
    build_llm_manual_review_items,
    build_llm_sidecar_file_failed,
    build_llm_sidecar_file_success,
    build_llm_sidecar_result,
)


def test_single_file_manual_review_generates_stable_checklist_ids() -> None:
    result = LLMReviewResult(
        findings=(
            LLMReviewFinding(rule_id="llm.one", severity="warning", message="First"),
            LLMReviewFinding(rule_id="llm.two", severity="info", message="Second"),
        )
    )

    items = build_llm_manual_review_items(result)

    assert [item.checklist_id for item in items] == ["LLM-001", "LLM-002"]


def test_batch_manual_review_generates_global_incrementing_ids() -> None:
    result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_success(
                path="a.md",
                review=LLMReviewResult(
                    findings=(LLMReviewFinding(rule_id="llm.one", severity="warning", message="A"),)
                ),
            ),
            build_llm_sidecar_file_success(
                path="b.md",
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(rule_id="llm.two", severity="error", message="B"),
                        LLMReviewFinding(rule_id="llm.three", severity="info", message="C"),
                    )
                ),
            ),
        ]
    )

    items = build_batch_llm_manual_review_items(result)

    assert [(item.checklist_id, item.file_path) for item in items] == [
        ("LLM-001", "a.md"),
        ("LLM-002", "b.md"),
        ("LLM-003", "b.md"),
    ]


def test_execution_review_generates_error_ids() -> None:
    result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_failed(path="a.md", exc=RuntimeError("first failure")),
            build_llm_sidecar_file_failed(path="b.md", exc=ValueError("second failure")),
        ]
    )

    items = build_llm_execution_review_items(result)

    assert [(item.checklist_id, item.file_path) for item in items] == [
        ("LLM-ERR-001", "a.md"),
        ("LLM-ERR-002", "b.md"),
    ]


def test_manual_review_priority_rules_are_stable() -> None:
    result = LLMReviewResult(
        findings=(
            LLMReviewFinding(rule_id="llm.critical", severity="critical", message="critical"),
            LLMReviewFinding(rule_id="llm.error", severity="error", message="error"),
            LLMReviewFinding(rule_id="llm.warning", severity="warning", message="warning"),
            LLMReviewFinding(rule_id="llm.info", severity="info", message="info"),
        )
    )
    unknown_result = LLMReviewResult.model_construct(
        findings=(
            LLMReviewFinding.model_construct(
                rule_id="llm.unknown",
                severity="SEVERE",
                message="unknown",
            ),
        )
    )

    items = build_llm_manual_review_items(result)
    unknown_item = build_llm_manual_review_items(unknown_result)[0]

    assert [item.priority for item in items] == ["high", "high", "medium", "low"]
    assert unknown_item.priority == "review"


def test_manual_review_defaults_are_stable() -> None:
    result = LLMReviewResult(
        findings=(LLMReviewFinding(rule_id="llm.one", severity="warning", message="A"),)
    )

    item = build_llm_manual_review_items(result)[0]

    assert item.status == "needs_review"
    assert item.decision == "pending"
    assert item.quality_gate == "no"


def test_execution_review_defaults_are_stable() -> None:
    result = build_llm_sidecar_result(
        [build_llm_sidecar_file_failed(path="a.md", exc=RuntimeError("first failure"))]
    )

    item = build_llm_execution_review_items(result)[0]

    assert item.status == "needs_rerun"
    assert item.suggested_action == "rerun_llm_review"


def test_manual_review_uses_not_provided_for_missing_location_and_message() -> None:
    result = LLMReviewResult.model_construct(
        findings=(
            LLMReviewFinding.model_construct(
                rule_id="llm.one",
                severity="warning",
                message=" \n ",
                line=None,
                column=None,
            ),
        )
    )

    item = build_llm_manual_review_items(result)[0]

    assert item.location == "not provided"
    assert item.message == "not provided"


def test_manual_review_helper_does_not_modify_inputs() -> None:
    finding = LLMReviewFinding(rule_id="llm.one", severity="warning", message="A")
    result = LLMReviewResult(findings=(finding,))
    original_dump = result.model_dump()

    build_llm_manual_review_items(result)

    assert result.model_dump() == original_dump

