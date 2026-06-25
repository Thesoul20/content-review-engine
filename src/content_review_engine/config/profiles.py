from __future__ import annotations

from pathlib import Path

import yaml

from content_review_engine.core.models import ReviewProfile

_RULE_FIELD_PREFIXES = {
    "forbidden_terms": "forbidden_terms",
    "absolute_claims": "absolute_claims",
}
_RULE_SEVERITIES = {"info", "warning", "error", "critical"}


def _validate_string_list(value: object, *, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list of strings")
    return value


def _validate_rule_severity(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or value not in _RULE_SEVERITIES:
        allowed = ", ".join(sorted(_RULE_SEVERITIES))
        raise ValueError(f"{field_name} must be one of: {allowed}")
    return value


def _normalize_rule_configuration(data: object) -> object:
    if not isinstance(data, dict):
        return data

    normalized = dict(data)
    rules = normalized.get("rules")
    if rules is None:
        return normalized

    if not isinstance(rules, list):
        raise ValueError("rules must be a list")

    explicit_enabled_rules = list(normalized.get("enabled_rules") or [])
    saw_non_legacy_rule = False

    for rule_config in rules:
        if not isinstance(rule_config, dict):
            raise ValueError("rules entries must be mappings")
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
            )
        if "allow_terms" in rule_config:
            normalized[f"{prefix}_allow_terms"] = _validate_string_list(
                rule_config["allow_terms"],
                field_name=f"{rule_id}.allow_terms",
            )
        if "severity" in rule_config and rule_id == "absolute_claims":
            normalized["absolute_claims_severity"] = _validate_rule_severity(
                rule_config["severity"],
                field_name="absolute_claims.severity",
            )

        enabled = rule_config.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError(f"{rule_id}.enabled must be a boolean")
        if enabled and rule_id not in explicit_enabled_rules:
            explicit_enabled_rules.append(rule_id)
        if not enabled and rule_id in explicit_enabled_rules:
            explicit_enabled_rules.remove(rule_id)

    if saw_non_legacy_rule or "enabled_rules" in normalized:
        normalized["enabled_rules"] = explicit_enabled_rules

    normalized.pop("rules", None)
    return normalized


def load_profile(path: str | Path) -> ReviewProfile:
    profile_path = Path(path)

    if not profile_path.exists():
        raise FileNotFoundError(f"Profile file not found: {profile_path}")

    if profile_path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError(f"Expected a YAML profile file, got: {profile_path.suffix}")

    data = yaml.safe_load(profile_path.read_text(encoding="utf-8"))

    if data is None:
        raise ValueError(f"Profile file is empty: {profile_path}")

    data = _normalize_rule_configuration(data)

    return ReviewProfile.model_validate(data)
