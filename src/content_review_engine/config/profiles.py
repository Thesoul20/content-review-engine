from __future__ import annotations

from pathlib import Path

import yaml

from content_review_engine.core.models import ReviewProfile


def load_profile(path: str | Path) -> ReviewProfile:
    profile_path = Path(path)

    if not profile_path.exists():
        raise FileNotFoundError(f"Profile file not found: {profile_path}")

    if profile_path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError(f"Expected a YAML profile file, got: {profile_path.suffix}")

    data = yaml.safe_load(profile_path.read_text(encoding="utf-8"))

    if data is None:
        raise ValueError(f"Profile file is empty: {profile_path}")

    return ReviewProfile.model_validate(data)
