from __future__ import annotations

from pathlib import Path

import pytest

from content_review_engine.config import load_profile, validate_profile
from content_review_engine.config.profiles import ProfileValidationFailed
from content_review_engine.core.quality_gate import quality_gate_failed
from content_review_engine.core.models import ReviewProfile
from content_review_engine.reports import render_markdown_report
from content_review_engine.review import review_document
from content_review_engine.review.batch import review_markdown_directory


def _write_profile(tmp_path: Path, body: str) -> Path:
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(body, encoding="utf-8")
    return profile_path


def _profile_with_regex_rules(regex_rules: list[dict[str, object]]) -> ReviewProfile:
    return ReviewProfile.model_validate(
        {
            "name": "regex-profile",
            "target_platform": "wechat",
            "regex_rules": regex_rules,
        }
    )


def test_valid_regex_profile_loads(tmp_path: Path) -> None:
    profile_path = _write_profile(
        tmp_path,
        "\n".join(
            [
                "name: regex-profile",
                "target_platform: wechat",
                "regex_rules:",
                "  - id: exaggerated_claims",
                '    pattern: "唯一|第一|最强|绝对|100%"',
                "    severity: warning",
                '    message: "Avoid absolute or exaggerated claims."',
                '    suggestion: "Use a more cautious and evidence-based expression."',
            ]
        ),
    )

    profile = load_profile(profile_path)

    assert len(profile.regex_rules) == 1
    assert profile.regex_rules[0].id == "exaggerated_claims"
    assert profile.regex_rules[0].case_sensitive is False


def test_invalid_regex_pattern_fails_validation(tmp_path: Path) -> None:
    profile_path = _write_profile(
        tmp_path,
        "\n".join(
            [
                "name: regex-profile",
                "target_platform: wechat",
                "regex_rules:",
                "  - id: exaggerated_claims",
                '    pattern: "["',
                "    severity: warning",
                '    message: "Avoid absolute or exaggerated claims."',
            ]
        ),
    )

    with pytest.raises(ProfileValidationFailed) as exc_info:
        load_profile(profile_path)

    assert exc_info.value.issues[0].code == "invalid_regex_pattern"


def test_duplicate_regex_ids_fail_validation(tmp_path: Path) -> None:
    profile_path = _write_profile(
        tmp_path,
        "\n".join(
            [
                "name: regex-profile",
                "target_platform: wechat",
                "regex_rules:",
                "  - id: exaggerated_claims",
                '    pattern: "最强"',
                "    severity: warning",
                '    message: "Avoid exaggerated claims."',
                "  - id: exaggerated_claims",
                '    pattern: "绝对"',
                "    severity: error",
                '    message: "Avoid absolute claims."',
            ]
        ),
    )

    with pytest.raises(ProfileValidationFailed) as exc_info:
        load_profile(profile_path)

    assert exc_info.value.issues[0].code == "duplicate_rule_id"


def test_regex_rule_id_validation_rejects_invalid_format(tmp_path: Path) -> None:
    profile_path = _write_profile(
        tmp_path,
        "\n".join(
            [
                "name: regex-profile",
                "target_platform: wechat",
                "regex_rules:",
                "  - id: ExaggeratedClaims",
                '    pattern: "最强"',
                "    severity: warning",
                '    message: "Avoid exaggerated claims."',
            ]
        ),
    )

    validation_result = validate_profile(profile_path)

    assert validation_result.valid is False
    assert validation_result.errors[0].path == "regex_rules[0].id"
    assert validation_result.errors[0].code == "invalid_rule_id"


def test_regex_rule_produces_finding_with_configured_rule_id_and_location() -> None:
    profile = _profile_with_regex_rules(
        [
            {
                "id": "exaggerated_claims",
                "pattern": "最强",
                "severity": "warning",
                "message": "Avoid exaggerated claims.",
                "suggestion": "Use a more cautious expression.",
            }
        ]
    )

    result = review_document("这是最强的解决方案。", profile)

    assert result.summary.finding_count == 1
    finding = result.findings[0]
    assert finding.rule_id == "exaggerated_claims"
    assert finding.severity == "warning"
    assert finding.message == "Avoid exaggerated claims."
    assert finding.suggestion == "Use a more cautious expression."
    assert finding.matched_term == "最强"
    assert finding.matched_text == "最强"
    assert finding.location is not None
    assert finding.location.start_line == 1
    assert finding.location.start_column == 3


def test_regex_rule_produces_one_finding_per_match() -> None:
    profile = _profile_with_regex_rules(
        [
            {
                "id": "exaggerated_claims",
                "pattern": "最强|绝对",
                "severity": "warning",
                "message": "Avoid exaggerated claims.",
            }
        ]
    )

    result = review_document("这是最强的方案，也是绝对可靠的方案。", profile)

    assert [finding.matched_text for finding in result.findings] == ["最强", "绝对"]
    assert [finding.location.start_column for finding in result.findings] == [3, 11]


def test_multiple_regex_rules_can_run_together() -> None:
    profile = _profile_with_regex_rules(
        [
            {
                "id": "exaggerated_claims",
                "pattern": "最强",
                "severity": "warning",
                "message": "Avoid exaggerated claims.",
            },
            {
                "id": "percent_claims",
                "pattern": "100%",
                "severity": "error",
                "message": "Avoid unsupported certainty percentages.",
            },
        ]
    )

    result = review_document("这是最强方案，而且100%有效。", profile)

    assert [finding.rule_id for finding in result.findings] == [
        "exaggerated_claims",
        "percent_claims",
    ]
    assert result.summary.severity_counts == {
        "info": 0,
        "warning": 1,
        "error": 1,
        "critical": 0,
    }


def test_regex_rule_default_matching_is_case_insensitive() -> None:
    profile = _profile_with_regex_rules(
        [
            {
                "id": "english_claims",
                "pattern": "best",
                "severity": "warning",
                "message": "Avoid exaggerated English claims.",
            }
        ]
    )

    result = review_document("This is the BEST choice.", profile)

    assert [finding.matched_text for finding in result.findings] == ["BEST"]


def test_regex_rule_case_sensitive_matching_can_be_enabled() -> None:
    profile = _profile_with_regex_rules(
        [
            {
                "id": "english_claims",
                "pattern": "best",
                "severity": "warning",
                "message": "Avoid exaggerated English claims.",
                "case_sensitive": True,
            }
        ]
    )

    result = review_document("This is the BEST choice.", profile)

    assert result.findings == []


def test_regex_suppression_works_by_configured_rule_id() -> None:
    profile = _profile_with_regex_rules(
        [
            {
                "id": "exaggerated_claims",
                "pattern": "最强|绝对",
                "severity": "warning",
                "message": "Avoid exaggerated claims.",
            }
        ]
    )
    markdown_text = "\n".join(
        [
            "这是最强的解决方案。 <!-- content-review-disable-line exaggerated_claims -->",
            "<!-- content-review-disable-next-line exaggerated_claims -->",
            "这是绝对安全的方案。",
        ]
    )

    result = review_document(markdown_text, profile)

    assert result.findings == []
    assert result.summary.finding_count == 0


def test_regex_rule_counts_and_markdown_report_include_configured_rule_id() -> None:
    profile = _profile_with_regex_rules(
        [
            {
                "id": "exaggerated_claims",
                "pattern": "最强|绝对",
                "severity": "warning",
                "message": "Avoid exaggerated claims.",
            }
        ]
    )

    result = review_document("这是最强的方案，也是绝对可靠的方案。", profile)
    report = render_markdown_report(result)

    assert result.summary.severity_counts["warning"] == 2
    assert "| exaggerated_claims | 2 |" in report
    assert "| warning | exaggerated_claims | 1 | 3 | Avoid exaggerated claims. | - |" in report


def test_quality_gate_counts_regex_findings() -> None:
    profile = _profile_with_regex_rules(
        [
            {
                "id": "percent_claims",
                "pattern": "100%",
                "severity": "error",
                "message": "Avoid unsupported certainty percentages.",
            }
        ]
    )

    result = review_document("这个方案100%有效。", profile)

    assert quality_gate_failed(result.summary.severity_counts, "error") is True


def test_batch_review_aggregates_regex_findings(tmp_path: Path) -> None:
    articles_dir = tmp_path / "articles"
    articles_dir.mkdir()
    (articles_dir / "one.md").write_text("这是最强的方案。", encoding="utf-8")
    (articles_dir / "two.md").write_text("这个方案100%有效。", encoding="utf-8")
    profile_path = _write_profile(
        tmp_path,
        "\n".join(
            [
                "name: regex-profile",
                "target_platform: wechat",
                "regex_rules:",
                "  - id: exaggerated_claims",
                '    pattern: "最强"',
                "    severity: warning",
                '    message: "Avoid exaggerated claims."',
                "  - id: percent_claims",
                '    pattern: "100%"',
                "    severity: error",
                '    message: "Avoid unsupported certainty percentages."',
            ]
        ),
    )
    profile = load_profile(profile_path)

    result = review_markdown_directory(articles_dir, profile, profile_path=profile_path)

    assert result.summary.file_count == 2
    assert result.summary.finding_count == 2
    assert result.summary.files_with_findings == 2
    assert result.summary.severity_counts == {
        "info": 0,
        "warning": 1,
        "error": 1,
        "critical": 0,
    }
    assert [finding.rule_id for item in result.results for finding in item.findings] == [
        "exaggerated_claims",
        "percent_claims",
    ]


def test_profile_validation_summary_includes_regex_rules(tmp_path: Path) -> None:
    profile_path = _write_profile(
        tmp_path,
        "\n".join(
            [
                "name: regex-profile",
                "target_platform: wechat",
                "enabled_rules:",
                "  - forbidden_terms",
                "rules:",
                "  - id: forbidden_terms",
                "    enabled: true",
                "    terms:",
                "      - 绝对安全",
                "regex_rules:",
                "  - id: exaggerated_claims",
                '    pattern: "最强"',
                "    severity: warning",
                '    message: "Avoid exaggerated claims."',
            ]
        ),
    )

    result = validate_profile(profile_path)

    assert result.valid is True
    assert result.profile is not None
    assert result.profile.enabled_rule_count == 2
    assert [rule.id for rule in result.profile.rules] == [
        "forbidden_terms",
        "exaggerated_claims",
    ]


def test_regex_rules_do_not_match_across_lines() -> None:
    profile = _profile_with_regex_rules(
        [
            {
                "id": "cross_line_attempt",
                "pattern": "最强[\\s\\S]*绝对",
                "severity": "warning",
                "message": "Should not match across lines.",
            }
        ]
    )

    result = review_document("这是最强\n这是绝对可靠", profile)

    assert result.findings == []
