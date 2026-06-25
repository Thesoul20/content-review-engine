from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_EXAMPLE_PROFILES_DIR = (
    Path(__file__).resolve().parents[3] / "profiles" / "examples"
)


@dataclass(frozen=True)
class ProfileTemplate:
    name: str
    description: str
    path: Path

    @property
    def content(self) -> str:
        try:
            return self.path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"Template file is not readable: {self.path}") from exc


_BUILTIN_PROFILE_TEMPLATES: tuple[ProfileTemplate, ...] = (
    ProfileTemplate(
        name="general-basic",
        description="General-purpose starter profile for public-facing content.",
        path=_EXAMPLE_PROFILES_DIR / "general-basic.yaml",
    ),
    ProfileTemplate(
        name="wechat-basic",
        description="Basic WeChat article profile with moderate checks.",
        path=_EXAMPLE_PROFILES_DIR / "wechat-basic.yaml",
    ),
    ProfileTemplate(
        name="wechat-strict",
        description="Stricter WeChat profile intended for batch checks and CI gates.",
        path=_EXAMPLE_PROFILES_DIR / "wechat-strict.yaml",
    ),
)


def list_profile_templates() -> list[ProfileTemplate]:
    return list(_BUILTIN_PROFILE_TEMPLATES)


def list_profile_template_names() -> list[str]:
    return [template.name for template in _BUILTIN_PROFILE_TEMPLATES]


def get_profile_template(name: str) -> ProfileTemplate:
    for template in _BUILTIN_PROFILE_TEMPLATES:
        if template.name == name:
            return template

    available = ", ".join(list_profile_template_names())
    raise ValueError(f"unknown template: {name}. Available templates: {available}")


def get_profile_template_content(name: str) -> str:
    return get_profile_template(name).content


__all__ = [
    "ProfileTemplate",
    "get_profile_template",
    "get_profile_template_content",
    "list_profile_template_names",
    "list_profile_templates",
]
