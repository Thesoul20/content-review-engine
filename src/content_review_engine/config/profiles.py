from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from content_review_engine.core.models import ProfileValidationIssue, ReviewProfile

_RULE_FIELD_PREFIXES = {
    "forbidden_terms": "forbidden_terms",
    "absolute_claims": "absolute_claims",
}
_RULE_SEVERITIES = {"info", "warning", "error", "critical"}
_SEVERITY_SUGGESTION = "Use one of: critical, error, warning, info."


class ProfileValidationFailed(ValueError):
    def __init__(
        self,
        *,
        path: str,
        issues: tuple[ProfileValidationIssue, ...],
    ) -> None:
        self.path = path
        self.issues = issues
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        issue_count = len(self.issues)
        suffix = "" if issue_count == 1 else "s"
        return f"Profile validation failed for {self.path} with {issue_count} issue{suffix}."


def _issue(
    path: str,
    code: str,
    message: str,
    suggestion: str | None = None,
) -> ProfileValidationIssue:
    return ProfileValidationIssue(
        path=path,
        code=code,
        message=message,
        suggestion=suggestion,
    )


def _format_error_path(location: tuple[object, ...]) -> str:
    parts: list[str] = []
    for part in location:
        if isinstance(part, int):
            if not parts:
                parts.append(f"[{part}]")
            else:
                parts[-1] = f"{parts[-1]}[{part}]"
            continue
        parts.append(str(part))
    return ".".join(parts)


def _normalize_message_punctuation(message: str) -> str:
    if message.endswith((".", "!", "?")):
        return message
    return f"{message}."


def _validation_failed(
    *,
    path_text: str,
    issues: list[ProfileValidationIssue] | tuple[ProfileValidationIssue, ...],
) -> ProfileValidationFailed:
    return ProfileValidationFailed(path=path_text, issues=tuple(issues))


def _validate_string_list(
    value: object,
    *,
    field_name: str,
    path_text: str,
) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise _validation_failed(
            path_text=path_text,
            issues=[
                _issue(
                    field_name,
                    "invalid_string_list",
                    f"{field_name} must be a list of strings.",
                    "Use a YAML list of strings.",
                )
            ],
        )
    return value


def _validate_rule_severity(
    value: object,
    *,
    field_name: str,
    path_text: str,
) -> str:
    if not isinstance(value, str) or value not in _RULE_SEVERITIES:
        invalid_value = value if isinstance(value, str) else repr(value)
        raise _validation_failed(
            path_text=path_text,
            issues=[
                _issue(
                    field_name,
                    "invalid_severity",
                    f"Unknown severity: {invalid_value}.",
                    _SEVERITY_SUGGESTION,
                )
            ],
        )
    return value


def _normalize_rule_configuration(data: object, *, path_text: str) -> object:
    if not isinstance(data, dict):
        return data

    normalized = dict(data)
    rules = normalized.get("rules")
    if rules is None:
        return normalized

    if not isinstance(rules, list):
        raise _validation_failed(
            path_text=path_text,
            issues=[
                _issue(
                    "rules",
                    "invalid_section_type",
                    "rules must be a list.",
                    "Use a YAML list of rule objects.",
                )
            ],
        )

    explicit_enabled_rules = list(normalized.get("enabled_rules") or [])
    saw_non_legacy_rule = False

    for index, rule_config in enumerate(rules):
        if not isinstance(rule_config, dict):
            raise _validation_failed(
                path_text=path_text,
                issues=[
                    _issue(
                        f"rules[{index}]",
                        "invalid_section_type",
                        "Each rules entry must be a mapping.",
                        "Use YAML objects with fields such as id, enabled, and terms.",
                    )
                ],
            )
        rule_id = rule_config.get("id")
        if rule_id not in _RULE_FIELD_PREFIXES:
            continue

        if rule_id != "forbidden_terms":
            saw_non_legacy_rule = True

        prefix = _RULE_FIELD_PREFIXES[rule_id]
        if "terms" in rule_config:
            normalized[f"{prefix}_terms" if prefix == "absolute_claims" else prefix] = _validate_string_list(
                rule_config["terms"],
                field_name=f"{rule_id}.terms",
                path_text=path_text,
            )
        if "allow_terms" in rule_config:
            normalized[f"{prefix}_allow_terms"] = _validate_string_list(
                rule_config["allow_terms"],
                field_name=f"{rule_id}.allow_terms",
                path_text=path_text,
            )
        if "severity" in rule_config and rule_id == "absolute_claims":
            normalized["absolute_claims_severity"] = _validate_rule_severity(
                rule_config["severity"],
                field_name="absolute_claims.severity",
                path_text=path_text,
            )

        enabled = rule_config.get("enabled", True)
        if not isinstance(enabled, bool):
            raise _validation_failed(
                path_text=path_text,
                issues=[
                    _issue(
                        f"rules[{index}].enabled",
                        "invalid_boolean",
                        f"{rule_id}.enabled must be true or false.",
                        "Use true to enable the rule or false to disable it.",
                    )
                ],
            )
        if enabled and rule_id not in explicit_enabled_rules:
            explicit_enabled_rules.append(rule_id)
        if not enabled and rule_id in explicit_enabled_rules:
            explicit_enabled_rules.remove(rule_id)

    if saw_non_legacy_rule or "enabled_rules" in normalized:
        normalized["enabled_rules"] = explicit_enabled_rules

    normalized.pop("rules", None)
    return normalized


def _load_raw_profile_data(profile_path: Path) -> object:
    path_text = str(profile_path)

    if not profile_path.exists():
        raise _validation_failed(
            path_text=path_text,
            issues=[
                _issue(
                    "<file>",
                    "file_not_found",
                    f"Profile file not found: {profile_path}.",
                    "Check the path and make sure the YAML profile exists.",
                )
            ],
        )

    if profile_path.suffix.lower() not in {".yaml", ".yml"}:
        raise _validation_failed(
            path_text=path_text,
            issues=[
                _issue(
                    "<file>",
                    "invalid_file_extension",
                    f"Expected a YAML profile file, got: {profile_path.suffix}.",
                    "Use a .yaml or .yml profile file.",
                )
            ],
        )

    try:
        raw_text = profile_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise _validation_failed(
            path_text=path_text,
            issues=[
                _issue(
                    "<file>",
                    "unreadable_file",
                    f"Profile file is not readable: {profile_path}.",
                    "Check file permissions and try again.",
                )
            ],
        ) from exc

    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise _validation_failed(
            path_text=path_text,
            issues=[
                _issue(
                    "<yaml>",
                    "invalid_yaml",
                    f"Failed to parse YAML profile: {exc}.",
                    "Check indentation, quoting, and list structure.",
                )
            ],
        ) from exc

    if data is None:
        raise _validation_failed(
            path_text=path_text,
            issues=[
                _issue(
                    "<file>",
                    "empty_profile",
                    "Profile file is empty.",
                    "Add YAML content with at least name and target_platform.",
                )
            ],
        )

    return data


def _collect_duplicate_regex_rule_issues(data: object) -> list[ProfileValidationIssue]:
    if not isinstance(data, dict):
        return []

    raw_rules = data.get("regex_rules")
    if not isinstance(raw_rules, list):
        return []

    issues: list[ProfileValidationIssue] = []
    seen_rule_ids: set[str] = set()

    for index, raw_rule in enumerate(raw_rules):
        if not isinstance(raw_rule, dict):
            continue
        rule_id = raw_rule.get("id")
        if not isinstance(rule_id, str):
            continue
        normalized = rule_id.strip()
        if normalized in seen_rule_ids:
            issues.append(
                _issue(
                    f"regex_rules[{index}].id",
                    "duplicate_rule_id",
                    f"Duplicate regex rule ID: {normalized}.",
                    "Use a unique ID for each regex rule.",
                )
            )
            continue
        seen_rule_ids.add(normalized)

    return issues


def _issues_from_pydantic_error(error: ValidationError) -> list[ProfileValidationIssue]:
    issues: list[ProfileValidationIssue] = []

    for item in error.errors():
        location = tuple(item.get("loc", ()))
        path = _format_error_path(location) or "<profile>"
        field = location[-1] if location else None
        message = item.get("msg", "Validation error")
        error_type = item.get("type", "")
        input_value = item.get("input")
        message_lower = message.lower()

        if not location and "duplicate regex rule id" in message_lower:
            continue

        if path == "regex_rules" and error_type == "list_type":
            issues.append(
                _issue(
                    path,
                    "invalid_section_type",
                    "regex_rules must be a list.",
                    "Use a YAML list of regex rule objects.",
                )
            )
            continue

        if field == "severity" and error_type == "literal_error":
            issues.append(
                _issue(
                    path,
                    "invalid_severity",
                    f"Unknown severity: {input_value}.",
                    _SEVERITY_SUGGESTION,
                )
            )
            continue

        if field == "case_sensitive" and error_type in {"bool_parsing", "bool_type"}:
            issues.append(
                _issue(
                    path,
                    "invalid_boolean",
                    "case_sensitive must be true or false.",
                    "Use true for case-sensitive matching or false for case-insensitive matching.",
                )
            )
            continue

        if field == "id" and "regex rule id must match" in message_lower:
            issues.append(
                _issue(
                    path,
                    "invalid_rule_id",
                    "Rule ID must match ^[a-z][a-z0-9_]*$.",
                    "Use lowercase snake_case, such as custom_rule.",
                )
            )
            continue

        if field == "pattern" and "invalid regex pattern:" in message_lower:
            detail = message.split("invalid regex pattern:", 1)[1].strip()
            issues.append(
                _issue(
                    path,
                    "invalid_regex_pattern",
                    _normalize_message_punctuation(f"Invalid regex pattern: {detail}"),
                    "Check the regex syntax or escape special characters.",
                )
            )
            continue

        if field == "pattern" and "must not be empty" in message_lower:
            issues.append(
                _issue(
                    path,
                    "invalid_regex_pattern",
                    "Regex rule pattern must not be empty.",
                    "Provide a valid Python regular expression.",
                )
            )
            continue

        if field == "message" and "must not be empty" in message_lower:
            issues.append(
                _issue(
                    path,
                    "empty_regex_message",
                    "Regex rule message must not be empty.",
                    "Add a concise explanation shown when the rule matches.",
                )
            )
            continue

        if error_type == "missing":
            issues.append(
                _issue(
                    path,
                    "missing_required_field",
                    _normalize_message_punctuation(message),
                )
            )
            continue

        issues.append(
            _issue(
                path,
                "invalid_profile",
                _normalize_message_punctuation(message.removeprefix("Value error, ").strip()),
            )
        )

    return issues


def _load_profile_with_context(path: str | Path) -> tuple[ReviewProfile, object]:
    profile_path = Path(path)
    path_text = str(profile_path)
    raw_data = _load_raw_profile_data(profile_path)
    normalized_data = _normalize_rule_configuration(raw_data, path_text=path_text)
    duplicate_issues = _collect_duplicate_regex_rule_issues(normalized_data)

    try:
        profile = ReviewProfile.model_validate(normalized_data)
    except ValidationError as exc:
        issues = _issues_from_pydantic_error(exc)
        issues.extend(duplicate_issues)
        raise _validation_failed(path_text=path_text, issues=issues) from exc

    if duplicate_issues:
        raise _validation_failed(path_text=path_text, issues=duplicate_issues)

    return profile, raw_data


def load_profile(path: str | Path) -> ReviewProfile:
    profile, _ = _load_profile_with_context(path)
    return profile
