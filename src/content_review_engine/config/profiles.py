from __future__ import annotations

from pathlib import Path

import yaml

from content_review_engine.core.models import ReviewProfile


def _validate_string_list(value: object, *, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list of strings")
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

    for rule_config in rules:
        if not isinstance(rule_config, dict):
            raise ValueError("rules entries must be mappings")
        if rule_config.get("id") != "forbidden_terms":
            continue

        if "terms" in rule_config:
            normalized["forbidden_terms"] = _validate_string_list(
                rule_config["terms"],
                field_name="forbidden_terms.terms",
            )
        if "allow_terms" in rule_config:
            normalized["forbidden_terms_allow_terms"] = _validate_string_list(
                rule_config["allow_terms"],
                field_name="forbidden_terms.allow_terms",
            )

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
