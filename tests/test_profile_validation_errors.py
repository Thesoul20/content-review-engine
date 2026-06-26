from __future__ import annotations

from pathlib import Path

from content_review_engine.config import validate_profile
from content_review_engine.config.profiles import ProfileValidationFailed, load_profile

INVALID_PROFILES_DIR = Path("tests/fixtures/profiles/invalid")


def _issue_map(profile_name: str) -> dict[str, object]:
    result = validate_profile(INVALID_PROFILES_DIR / profile_name)
    assert result.valid is False
    assert result.errors
    return {
        "result": result,
        "first": result.errors[0],
    }


def test_invalid_regex_pattern_returns_structured_issue() -> None:
    data = _issue_map("invalid-regex-pattern.yaml")
    issue = data["first"]

    assert issue.path == "regex_rules[0].pattern"
    assert issue.code == "invalid_regex_pattern"
    assert "Invalid regex pattern:" in issue.message
    assert issue.suggestion == "Check the regex syntax or escape special characters."


def test_invalid_regex_rule_id_returns_structured_issue() -> None:
    data = _issue_map("invalid-regex-id.yaml")
    issue = data["first"]

    assert issue.path == "regex_rules[0].id"
    assert issue.code == "invalid_rule_id"
    assert issue.message == "Rule ID must match ^[a-z][a-z0-9_]*$."
    assert issue.suggestion == "Use lowercase snake_case, such as custom_rule."


def test_duplicate_regex_rule_id_returns_structured_issue() -> None:
    data = _issue_map("duplicate-regex-id.yaml")
    issue = data["first"]

    assert issue.path == "regex_rules[1].id"
    assert issue.code == "duplicate_rule_id"
    assert issue.message == "Duplicate regex rule ID: repeated_rule."
    assert issue.suggestion == "Use a unique ID for each regex rule."


def test_invalid_severity_returns_structured_issue() -> None:
    data = _issue_map("invalid-severity.yaml")
    issue = data["first"]

    assert issue.path == "regex_rules[0].severity"
    assert issue.code == "invalid_severity"
    assert issue.message == "Unknown severity: warn."
    assert issue.suggestion == "Use one of: critical, error, warning, info."


def test_empty_regex_message_returns_structured_issue() -> None:
    data = _issue_map("empty-regex-message.yaml")
    issue = data["first"]

    assert issue.path == "regex_rules[0].message"
    assert issue.code == "empty_regex_message"
    assert issue.message == "Regex rule message must not be empty."
    assert issue.suggestion == "Add a concise explanation shown when the rule matches."


def test_invalid_case_sensitive_returns_structured_issue() -> None:
    data = _issue_map("invalid-case-sensitive.yaml")
    issue = data["first"]

    assert issue.path == "regex_rules[0].case_sensitive"
    assert issue.code == "invalid_boolean"
    assert issue.message == "case_sensitive must be true or false."
    assert issue.suggestion == (
        "Use true for case-sensitive matching or false for case-insensitive matching."
    )


def test_invalid_yaml_returns_structured_issue() -> None:
    data = _issue_map("invalid-yaml.yaml")
    issue = data["first"]

    assert issue.path == "<yaml>"
    assert issue.code == "invalid_yaml"
    assert issue.message.startswith("Failed to parse YAML profile:")
    assert issue.suggestion == "Check indentation, quoting, and list structure."


def test_multiple_issues_are_collected_when_practical(tmp_path: Path) -> None:
    profile_path = tmp_path / "multiple-issues.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: multi-issue",
                "target_platform: wechat",
                "regex_rules:",
                "  - id: 123_rule",
                '    pattern: "["',
                "    severity: warn",
                '    message: "   "',
                "  - id: repeated_rule",
                '    pattern: "foo"',
                "    severity: warning",
                '    message: "First duplicate."',
                "  - id: repeated_rule",
                '    pattern: "bar"',
                "    severity: error",
                '    message: "Second duplicate."',
            ]
        ),
        encoding="utf-8",
    )

    result = validate_profile(profile_path)

    assert result.valid is False
    assert {(issue.path, issue.code) for issue in result.errors} == {
        ("regex_rules[0].id", "invalid_rule_id"),
        ("regex_rules[0].pattern", "invalid_regex_pattern"),
        ("regex_rules[0].severity", "invalid_severity"),
        ("regex_rules[0].message", "empty_regex_message"),
        ("regex_rules[2].id", "duplicate_rule_id"),
    }


def test_load_profile_raises_structured_validation_failure() -> None:
    profile_path = INVALID_PROFILES_DIR / "invalid-regex-pattern.yaml"

    try:
        load_profile(profile_path)
    except ProfileValidationFailed as exc:
        assert exc.path == str(profile_path)
        assert exc.issues[0].path == "regex_rules[0].pattern"
        assert exc.issues[0].code == "invalid_regex_pattern"
    else:
        raise AssertionError("Expected ProfileValidationFailed to be raised.")
