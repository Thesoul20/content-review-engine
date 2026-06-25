from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from content_review_engine.config.profiles import load_profile
from content_review_engine.core.models import (
    ProfileValidationError,
    ProfileValidationProfileSummary,
    ProfileValidationResult,
    ProfileValidationRuleSummary,
    ReviewProfile,
)
from content_review_engine.rules.registry import build_default_rule_registry

_KNOWN_RULE_IDS = set(build_default_rule_registry().list_rule_ids())


def _error(message: str) -> ProfileValidationError:
    return ProfileValidationError(message=message)


def _format_validation_error(error: ValidationError) -> list[str]:
    messages: list[str] = []
    for item in error.errors():
        location = ".".join(str(part) for part in item.get("loc", ()))
        message = item.get("msg", "Validation error")
        if location:
            messages.append(f"{location}: {message}")
        else:
            messages.append(message)
    return messages


def _rule_severity(rule_id: str, profile: ReviewProfile) -> str:
    if rule_id == "absolute_claims":
        return profile.absolute_claims_severity
    return "warning"


def _add_rule_summary(
    summaries: list[ProfileValidationRuleSummary],
    seen_rule_ids: set[str],
    *,
    rule_id: str,
    profile: ReviewProfile,
) -> None:
    if rule_id in seen_rule_ids:
        return
    summaries.append(
        ProfileValidationRuleSummary(
            id=rule_id,
            enabled=True,
            severity=_rule_severity(rule_id, profile),
        )
    )
    seen_rule_ids.add(rule_id)


def _unknown_rule_ids(
    raw_data: object,
    profile: ReviewProfile,
) -> list[str]:
    unknown_rule_ids: list[str] = []
    seen_rule_ids: set[str] = set()

    def add_unknown(rule_id: str) -> None:
        if rule_id in seen_rule_ids:
            return
        seen_rule_ids.add(rule_id)
        unknown_rule_ids.append(rule_id)

    if isinstance(raw_data, dict):
        raw_rules = raw_data.get("rules")
        if isinstance(raw_rules, list):
            for rule_config in raw_rules:
                if not isinstance(rule_config, dict):
                    continue
                rule_id = rule_config.get("id")
                if isinstance(rule_id, str) and rule_id not in _KNOWN_RULE_IDS:
                    add_unknown(rule_id)

    if profile.enabled_rules is not None:
        for rule_id in profile.enabled_rules:
            if rule_id not in _KNOWN_RULE_IDS:
                add_unknown(rule_id)

    return unknown_rule_ids


def _build_profile_summary(
    raw_data: object,
    profile: ReviewProfile,
) -> ProfileValidationProfileSummary:
    rules: list[ProfileValidationRuleSummary] = []
    seen_rule_ids: set[str] = set()
    disabled_rule_count = 0

    if isinstance(raw_data, dict):
        raw_rules = raw_data.get("rules")
        if isinstance(raw_rules, list):
            for rule_config in raw_rules:
                if not isinstance(rule_config, dict):
                    continue
                rule_id = rule_config.get("id")
                if not isinstance(rule_id, str) or rule_id not in _KNOWN_RULE_IDS:
                    continue
                enabled = rule_config.get("enabled", True)
                if enabled is False:
                    disabled_rule_count += 1
                    continue
                _add_rule_summary(
                    rules,
                    seen_rule_ids,
                    rule_id=rule_id,
                    profile=profile,
                )
            return ProfileValidationProfileSummary(
                name=profile.name,
                target_platform=profile.target_platform,
                enabled_rule_count=len(rules),
                disabled_rule_count=disabled_rule_count,
                rules=rules,
            )

    if profile.enabled_rules is not None:
        for rule_id in profile.enabled_rules:
            if rule_id in _KNOWN_RULE_IDS:
                _add_rule_summary(
                    rules,
                    seen_rule_ids,
                    rule_id=rule_id,
                    profile=profile,
                )
    else:
        if profile.forbidden_terms or profile.forbidden_terms_allow_terms:
            _add_rule_summary(
                rules,
                seen_rule_ids,
                rule_id="forbidden_terms",
                profile=profile,
            )
        if profile.absolute_claims_terms or profile.absolute_claims_allow_terms:
            _add_rule_summary(
                rules,
                seen_rule_ids,
                rule_id="absolute_claims",
                profile=profile,
            )

    return ProfileValidationProfileSummary(
        name=profile.name,
        target_platform=profile.target_platform,
        enabled_rule_count=len(rules),
        disabled_rule_count=disabled_rule_count,
        rules=rules,
    )


def validate_profile(path: str | Path) -> ProfileValidationResult:
    profile_path = Path(path)
    path_text = str(profile_path)

    if not profile_path.exists():
        return ProfileValidationResult(
            valid=False,
            path=path_text,
            errors=[_error(f"Profile file not found: {profile_path}")],
        )

    if profile_path.suffix.lower() not in {".yaml", ".yml"}:
        return ProfileValidationResult(
            valid=False,
            path=path_text,
            errors=[_error(f"Expected a YAML profile file, got: {profile_path.suffix}")],
        )

    try:
        raw_text = profile_path.read_text(encoding="utf-8")
    except OSError as exc:
        return ProfileValidationResult(
            valid=False,
            path=path_text,
            errors=[_error(f"Profile file is not readable: {profile_path}")],
        )

    try:
        raw_data = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        return ProfileValidationResult(
            valid=False,
            path=path_text,
            errors=[_error(f"Invalid YAML: {exc}")],
        )

    if raw_data is None:
        return ProfileValidationResult(
            valid=False,
            path=path_text,
            errors=[_error(f"Profile file is empty: {profile_path}")],
        )

    try:
        profile = load_profile(profile_path)
    except FileNotFoundError as exc:
        return ProfileValidationResult(
            valid=False,
            path=path_text,
            errors=[_error(str(exc))],
        )
    except ValueError as exc:
        return ProfileValidationResult(
            valid=False,
            path=path_text,
            errors=[_error(str(exc))],
        )
    except ValidationError as exc:
        return ProfileValidationResult(
            valid=False,
            path=path_text,
            errors=[_error(message) for message in _format_validation_error(exc)],
        )

    unknown_rule_ids = _unknown_rule_ids(raw_data, profile)
    if unknown_rule_ids:
        return ProfileValidationResult(
            valid=False,
            path=path_text,
            errors=[_error(f"unknown rule id: {rule_id}") for rule_id in unknown_rule_ids],
        )

    return ProfileValidationResult(
        valid=True,
        path=path_text,
        profile=_build_profile_summary(raw_data, profile),
    )


__all__ = ["validate_profile"]
