from __future__ import annotations

from pathlib import Path


def read_markdown(path: str | Path) -> str:
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {file_path}")

    if file_path.suffix.lower() not in {".md", ".markdown"}:
        raise ValueError(f"Expected a Markdown file, got: {file_path.suffix}")

    return file_path.read_text(encoding="utf-8")
