from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_review_engine.cli import main
from content_review_engine.config import load_profile, validate_profile
from content_review_engine.core.serialization import (
    batch_review_result_to_dict,
    review_result_to_dict,
)
from content_review_engine.reports import render_markdown_report
from content_review_engine.review import review_document, review_markdown_directory

DEMO_DIR = Path("examples/demo")
DEMO_ARTICLES_DIR = DEMO_DIR / "articles"
DEMO_PROFILES_DIR = DEMO_DIR / "profiles"
DEMO_REPORTS_DIR = DEMO_DIR / "reports"

WECHAT_ARTICLE_PATH = DEMO_ARTICLES_DIR / "wechat-demo.md"
TECHNICAL_ARTICLE_PATH = DEMO_ARTICLES_DIR / "technical-demo.md"
WECHAT_PROFILE_PATH = DEMO_PROFILES_DIR / "wechat-demo.yaml"
TECHNICAL_PROFILE_PATH = DEMO_PROFILES_DIR / "technical-demo.yaml"
WECHAT_REPORT_PATH = DEMO_REPORTS_DIR / "wechat-demo-report.md"
TECHNICAL_REPORT_PATH = DEMO_REPORTS_DIR / "technical-demo-report.md"


def test_demo_files_exist() -> None:
    expected_paths = [
        DEMO_DIR / "README.md",
        WECHAT_ARTICLE_PATH,
        TECHNICAL_ARTICLE_PATH,
        WECHAT_PROFILE_PATH,
        TECHNICAL_PROFILE_PATH,
        WECHAT_REPORT_PATH,
        TECHNICAL_REPORT_PATH,
    ]

    for path in expected_paths:
        assert path.exists(), path.as_posix()


def test_demo_profiles_validate_and_include_regex_rules() -> None:
    expected = {
        WECHAT_PROFILE_PATH: ("wechat-demo", "wechat"),
        TECHNICAL_PROFILE_PATH: ("technical-demo", "technical"),
    }

    for path, (name, target_platform) in expected.items():
        validation_result = validate_profile(path)
        profile = load_profile(path)

        assert validation_result.valid is True
        assert validation_result.profile is not None
        assert profile.name == name
        assert profile.target_platform == target_platform
        assert profile.regex_rules
        assert "markdown_links_images" in (profile.enabled_rules or [])


def test_wechat_demo_review_produces_findings_and_respects_suppression() -> None:
    markdown_text = WECHAT_ARTICLE_PATH.read_text(encoding="utf-8")
    profile = load_profile(WECHAT_PROFILE_PATH)

    result = review_document(
        markdown_text,
        profile,
        document_path=WECHAT_ARTICLE_PATH,
        profile_path=WECHAT_PROFILE_PATH,
    )

    assert result.summary.finding_count == 6
    assert result.summary.severity_counts == {
        "info": 2,
        "warning": 4,
        "error": 0,
        "critical": 0,
    }

    rule_ids = [finding.rule_id for finding in result.findings]
    assert "absolute_claims" in rule_ids
    assert "article_placeholder" in rule_ids
    assert "engagement_bait" in rule_ids
    assert "exaggerated_claims" in rule_ids
    assert "markdown_links_images" in rule_ids
    assert rule_ids.count("exaggerated_claims") == 1

    matched_texts = [finding.matched_text for finding in result.findings]
    assert "唯一标识符" not in matched_texts
    assert "[下载链接](TODO)" in matched_texts


def test_technical_demo_review_produces_findings_and_respects_suppression() -> None:
    markdown_text = TECHNICAL_ARTICLE_PATH.read_text(encoding="utf-8")
    profile = load_profile(TECHNICAL_PROFILE_PATH)

    result = review_document(
        markdown_text,
        profile,
        document_path=TECHNICAL_ARTICLE_PATH,
        profile_path=TECHNICAL_PROFILE_PATH,
    )

    assert result.summary.finding_count == 6
    assert result.summary.severity_counts == {
        "info": 1,
        "warning": 5,
        "error": 0,
        "critical": 0,
    }

    rule_ids = [finding.rule_id for finding in result.findings]
    assert rule_ids.count("absolute_claims") == 2
    assert "absolute_technical_claim" in rule_ids
    assert "markdown_links_images" in rule_ids
    assert rule_ids.count("unresolved_draft_marker") == 1
    assert "unresolved_example" in rule_ids

    matched_texts = [finding.matched_text for finding in result.findings]
    assert "FIXME" not in matched_texts
    assert "[迁移步骤](#)" in matched_texts


def test_demo_markdown_reports_match_committed_examples() -> None:
    report_inputs = [
        (WECHAT_ARTICLE_PATH, WECHAT_PROFILE_PATH, WECHAT_REPORT_PATH),
        (TECHNICAL_ARTICLE_PATH, TECHNICAL_PROFILE_PATH, TECHNICAL_REPORT_PATH),
    ]

    for article_path, profile_path, report_path in report_inputs:
        result = review_document(
            article_path.read_text(encoding="utf-8"),
            load_profile(profile_path),
            document_path=article_path,
            profile_path=profile_path,
        )

        rendered = render_markdown_report(result, fail_on="warning")
        expected_report = report_path.read_text(encoding="utf-8").rstrip("\n")

        assert rendered == expected_report


def test_demo_json_serialization_works() -> None:
    result = review_document(
        WECHAT_ARTICLE_PATH.read_text(encoding="utf-8"),
        load_profile(WECHAT_PROFILE_PATH),
        document_path=WECHAT_ARTICLE_PATH,
        profile_path=WECHAT_PROFILE_PATH,
    )

    payload = review_result_to_dict(result)
    serialized = json.loads(json.dumps(payload, ensure_ascii=False))

    assert serialized["schema_version"] == "review-result.v1"
    assert serialized["summary"]["finding_count"] == 6
    assert serialized["document"]["path"] == WECHAT_ARTICLE_PATH.as_posix()
    assert serialized["profile"]["path"] == WECHAT_PROFILE_PATH.as_posix()
    assert "exaggerated_claims" in {item["rule_id"] for item in serialized["findings"]}


def test_demo_batch_review_and_quality_gate_behavior(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    batch_result = review_markdown_directory(
        DEMO_ARTICLES_DIR,
        load_profile(TECHNICAL_PROFILE_PATH),
        pattern="technical-*.md",
        profile_path=TECHNICAL_PROFILE_PATH,
    )
    payload = batch_review_result_to_dict(batch_result)

    assert batch_result.summary.file_count == 1
    assert batch_result.summary.reviewed_count == 1
    assert batch_result.summary.finding_count == 6
    assert batch_result.summary.files_with_findings == 1
    assert payload["schema_version"] == "batch-review-result.v1"
    assert payload["results"][0]["document"]["path"] == TECHNICAL_ARTICLE_PATH.as_posix()

    review_report_path = tmp_path / "wechat-report.md"
    batch_report_path = tmp_path / "technical-batch-report.md"

    review_exit_code = main(
        [
            "review",
            str(WECHAT_ARTICLE_PATH),
            "--profile",
            str(WECHAT_PROFILE_PATH),
            "--format",
            "markdown",
            "--output",
            str(review_report_path),
            "--fail-on",
            "warning",
        ]
    )
    batch_exit_code = main(
        [
            "batch",
            str(DEMO_ARTICLES_DIR),
            "--profile",
            str(TECHNICAL_PROFILE_PATH),
            "--pattern",
            "technical-*.md",
            "--format",
            "markdown",
            "--output",
            str(batch_report_path),
            "--fail-on",
            "warning",
        ]
    )
    captured = capsys.readouterr()

    assert review_exit_code == 1
    assert batch_exit_code == 1
    assert captured.out == ""
    assert captured.err == ""
    assert review_report_path.exists()
    assert batch_report_path.exists()
    assert "| Quality Gate | Failed |" in review_report_path.read_text(encoding="utf-8")
    assert batch_report_path.read_text(encoding="utf-8").startswith(
        "# Batch Content Review Report\n"
    )


def test_demo_readme_and_docs_link_to_demo_and_include_commands() -> None:
    demo_readme = (DEMO_DIR / "README.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    quickstart = Path("docs/QUICKSTART.md").read_text(encoding="utf-8")
    cli_doc = Path("docs/CLI.md").read_text(encoding="utf-8")
    profiles_doc = Path("docs/PROFILES.md").read_text(encoding="utf-8")

    assert "uv run content-review profile validate examples/demo/profiles/wechat-demo.yaml" in demo_readme
    assert "uv run content-review review examples/demo/articles/wechat-demo.md --profile examples/demo/profiles/wechat-demo.yaml" in demo_readme
    assert "uv run content-review review examples/demo/articles/technical-demo.md --profile examples/demo/profiles/technical-demo.yaml" in demo_readme
    assert "--format markdown --output examples/demo/reports/wechat-demo-report.md --fail-on warning" in demo_readme
    assert "--format json" in demo_readme
    assert "uv run content-review batch examples/demo/articles --profile examples/demo/profiles/technical-demo.yaml --pattern \"technical-*.md\" --fail-on warning --format markdown --output examples/demo/reports/technical-demo-batch-report.md" in demo_readme

    assert "examples/demo/README.md" in readme
    assert "../examples/demo/README.md" in quickstart
    assert "../examples/demo/README.md" in cli_doc
    assert "../examples/demo/README.md" in profiles_doc


def test_demo_docs_and_profiles_avoid_compliance_guarantee_language() -> None:
    paths = [
        DEMO_DIR / "README.md",
        WECHAT_PROFILE_PATH,
        TECHNICAL_PROFILE_PATH,
        Path("README.md"),
        Path("docs/QUICKSTART.md"),
        Path("docs/CLI.md"),
        Path("docs/PROFILES.md"),
    ]
    combined = " ".join(path.read_text(encoding="utf-8") for path in paths).lower()
    normalized = " ".join(combined.split())

    assert "compliance guarantees" in normalized or "compliance advice" in normalized
    assert "this ensures compliance" not in normalized
    assert "guarantees compliance" not in normalized
    assert "guaranteed approval" not in normalized
