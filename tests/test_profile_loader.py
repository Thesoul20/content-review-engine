from pathlib import Path

import pytest
from pydantic import ValidationError

from content_review_engine.config import load_profile


def test_load_profile_from_yaml_file(tmp_path: Path) -> None:
    profile_path = tmp_path / "wechat.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: wechat",
                "target_platform: wechat",
                "tone: clear and professional",
                "max_title_length: 32",
                "max_paragraph_length: 220",
            ]
        ),
        encoding="utf-8",
    )

    profile = load_profile(profile_path)

    assert profile.name == "wechat"
    assert profile.target_platform == "wechat"
    assert profile.tone == "clear and professional"
    assert profile.max_title_length == 32
    assert profile.max_paragraph_length == 220


def test_load_profile_from_string_path(tmp_path: Path) -> None:
    profile_path = tmp_path / "wechat.yml"
    profile_path.write_text(
        "name: wechat\ntarget_platform: wechat\n",
        encoding="utf-8",
    )

    profile = load_profile(str(profile_path))

    assert profile.name == "wechat"
    assert profile.target_platform == "wechat"


def test_load_profile_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Profile file not found"):
        load_profile(tmp_path / "missing.yaml")


def test_load_profile_non_yaml_file_raises(tmp_path: Path) -> None:
    profile_path = tmp_path / "wechat.txt"
    profile_path.write_text("name: wechat", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected a YAML profile file"):
        load_profile(profile_path)


def test_load_profile_empty_yaml_raises(tmp_path: Path) -> None:
    profile_path = tmp_path / "empty.yaml"
    profile_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Profile file is empty"):
        load_profile(profile_path)


def test_load_profile_invalid_yaml_raises_value_error(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid.yaml"
    profile_path.write_text("name: [wechat", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid YAML"):
        load_profile(profile_path)


def test_load_profile_invalid_schema_raises_validation_error(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid.yaml"
    profile_path.write_text("name: wechat\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        load_profile(profile_path)


def test_load_profile_with_enabled_rules(tmp_path: Path) -> None:
    profile_path = tmp_path / "rules.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: wechat",
                "target_platform: wechat",
                "enabled_rules:",
                "  - forbidden_terms",
            ]
        ),
        encoding="utf-8",
    )

    profile = load_profile(profile_path)

    assert profile.enabled_rules == ["forbidden_terms"]


def test_load_profile_with_forbidden_terms_rule_configuration(
    tmp_path: Path,
) -> None:
    profile_path = tmp_path / "rules.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: wechat",
                "target_platform: wechat",
                "rules:",
                "  - id: forbidden_terms",
                "    enabled: true",
                "    severity: error",
                "    terms:",
                "      - 全网最强",
                "      - 永久有效",
                "    allow_terms:",
                "      - 永久有效",
            ]
        ),
        encoding="utf-8",
    )

    profile = load_profile(profile_path)

    assert profile.forbidden_terms == ["全网最强", "永久有效"]
    assert profile.forbidden_terms_allow_terms == ["永久有效"]


def test_load_profile_rejects_invalid_forbidden_terms_allow_terms(
    tmp_path: Path,
) -> None:
    profile_path = tmp_path / "invalid-allow-terms.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: wechat",
                "target_platform: wechat",
                "rules:",
                "  - id: forbidden_terms",
                "    terms:",
                "      - 全网最强",
                "    allow_terms: 全网最强",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="forbidden_terms.allow_terms"):
        load_profile(profile_path)


def test_load_profile_with_absolute_claims_rule_configuration(
    tmp_path: Path,
) -> None:
    profile_path = tmp_path / "absolute-claims.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: wechat",
                "target_platform: wechat",
                "rules:",
                "  - id: absolute_claims",
                "    enabled: true",
                "    severity: error",
                "    terms:",
                "      - 全网最强",
                "      - 永久有效",
                "    allow_terms:",
                "      - 永久有效",
            ]
        ),
        encoding="utf-8",
    )

    profile = load_profile(profile_path)

    assert profile.absolute_claims_terms == ["全网最强", "永久有效"]
    assert profile.absolute_claims_allow_terms == ["永久有效"]
    assert profile.absolute_claims_severity == "error"
    assert profile.enabled_rules == ["absolute_claims"]


def test_load_profile_rejects_invalid_absolute_claims_terms(
    tmp_path: Path,
) -> None:
    profile_path = tmp_path / "invalid-absolute-claims-terms.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: wechat",
                "target_platform: wechat",
                "rules:",
                "  - id: absolute_claims",
                "    terms: 全网最强",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="absolute_claims.terms"):
        load_profile(profile_path)


def test_load_profile_rejects_invalid_absolute_claims_allow_terms(
    tmp_path: Path,
) -> None:
    profile_path = tmp_path / "invalid-absolute-claims-allow-terms.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: wechat",
                "target_platform: wechat",
                "rules:",
                "  - id: absolute_claims",
                "    terms:",
                "      - 全网最强",
                "    allow_terms: 绝对安全",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="absolute_claims.allow_terms"):
        load_profile(profile_path)


def test_load_profile_rejects_invalid_absolute_claims_severity(
    tmp_path: Path,
) -> None:
    profile_path = tmp_path / "invalid-absolute-claims-severity.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: wechat",
                "target_platform: wechat",
                "rules:",
                "  - id: absolute_claims",
                "    severity: high",
                "    terms:",
                "      - 全网最强",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="absolute_claims.severity"):
        load_profile(profile_path)
