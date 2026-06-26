from __future__ import annotations

from pathlib import Path

from content_review_engine.config.profiles import (
    ProfileValidationFailed,
    _load_profile_with_context,
)
from content_review_engine.core.models import (
    ProfileValidationIssue,
    ProfileValidationProfileSummary,
    ProfileValidationResult,
    ProfileValidationRuleSummary,
    ReviewProfile,
)
from content_review_engine.rules.registry import build_default_rule_registry

_KNOWN_RULE_IDS = set(build_default_rule_registry().list_rule_ids())


def _error(
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


def _rule_severity(rule_id: str, profile: ReviewProfile) -> str:
    if rule_id == "absolute_claims":
        return profile.absolute_claims_severity
    for regex_rule in profile.regex_rules:
        if regex_rule.id == rule_id:
            return regex_rule.severity
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
) -> list[tuple[str, str]]:
    unknown_rule_ids: list[tuple[str, str]] = []
    seen_rule_ids: set[tuple[str, str]] = set()
    regex_rule_ids = {regex_rule.id for regex_rule in profile.regex_rules}

    def add_unknown(path: str, rule_id: str) -> None:
        item = (path, rule_id)
        if item in seen_rule_ids:
            return
        seen_rule_ids.add(item)
        unknown_rule_ids.append(item)

    if isinstance(raw_data, dict):
        raw_rules = raw_data.get("rules")
        if isinstance(raw_rules, list):
            for index, rule_config in enumerate(raw_rules):
                if not isinstance(rule_config, dict):
                    continue
                rule_id = rule_config.get("id")
                if isinstance(rule_id, str) and rule_id not in _KNOWN_RULE_IDS:
                    add_unknown(f"rules[{index}].id", rule_id)

    if profile.enabled_rules is not None:
        for index, rule_id in enumerate(profile.enabled_rules):
            if rule_id not in _KNOWN_RULE_IDS and rule_id not in regex_rule_ids:
                add_unknown(f"enabled_rules[{index}]", rule_id)

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
                enabled_rule_count=len(rules) + len(profile.regex_rules),
                disabled_rule_count=disabled_rule_count,
                rules=rules
                + [
                    ProfileValidationRuleSummary(
                        id=regex_rule.id,
                        enabled=True,
                        severity=regex_rule.severity,
                    )
                    for regex_rule in profile.regex_rules
                ],
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
        enabled_rule_count=len(rules) + len(profile.regex_rules),
        disabled_rule_count=disabled_rule_count,
        rules=rules
        + [
            ProfileValidationRuleSummary(
                id=regex_rule.id,
                enabled=True,
                severity=regex_rule.severity,
            )
            for regex_rule in profile.regex_rules
        ],
    )


def validate_profile(path: str | Path) -> ProfileValidationResult:
    profile_path = Path(path)
    path_text = str(profile_path)

    try:
        profile, raw_data = _load_profile_with_context(profile_path)
    except ProfileValidationFailed as exc:
        return ProfileValidationResult(
            valid=False,
            path=path_text,
            errors=list(exc.issues),
        )

    unknown_rule_ids = _unknown_rule_ids(raw_data, profile)
    if unknown_rule_ids:
        return ProfileValidationResult(
            valid=False,
            path=path_text,
            errors=[
                _error(
                    path,
                    "unknown_rule_id",
                    f"Unknown rule ID: {rule_id}.",
                    "Use a built-in rule ID or remove the unsupported rule entry.",
                )
                for path, rule_id in unknown_rule_ids
            ],
        )

    return ProfileValidationResult(
        valid=True,
        path=path_text,
        profile=_build_profile_summary(raw_data, profile),
    )


__all__ = ["validate_profile"]
