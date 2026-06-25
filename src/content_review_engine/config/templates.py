from __future__ import annotations

from pathlib import Path

_TEMPLATE_NAMES = (
    "general-basic",
    "wechat-basic",
    "wechat-strict",
)

_EXAMPLE_PROFILES_DIR = (
    Path(__file__).resolve().parents[3] / "profiles" / "examples"
)


def list_profile_templates() -> list[str]:
    return list(_TEMPLATE_NAMES)


def get_profile_template(name: str) -> str:
    if name not in _TEMPLATE_NAMES:
        available = ", ".join(_TEMPLATE_NAMES)
        raise ValueError(f"unknown template: {name}. Available templates: {available}")

    template_path = _EXAMPLE_PROFILES_DIR / f"{name}.yaml"
    try:
        return template_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(
            f"Template file is not readable: {template_path}"
        ) from exc
