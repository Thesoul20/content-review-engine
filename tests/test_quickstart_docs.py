from pathlib import Path


def test_quickstart_exists_and_covers_core_commands() -> None:
    quickstart_path = Path("docs/QUICKSTART.md")

    assert quickstart_path.exists()

    content = quickstart_path.read_text(encoding="utf-8")
    normalized_content = " ".join(content.split())

    assert "uv sync" in content
    assert "uv run content-review profile list" in content
    assert "uv run content-review profile init" in content
    assert "uv run content-review profile validate" in content
    assert "uv run content-review review" in content
    assert "uv run content-review batch" in content
    assert "--fail-on" in content
    assert "--format markdown --output" in content
    assert "content-review-disable-line absolute_claims" in content
    assert "content-review-disable-next-line forbidden_terms" in content
    assert "`0`" in content
    assert "`1`" in content
    assert "`2`" in content
    assert "./CLI.md" in content
    assert "./PROFILES.md" in content
    assert "./CI.md" in content
    assert (
        "legal, advertising, medical, regulatory, or platform compliance"
        in normalized_content
    )


def test_quickstart_links_are_exposed_from_reference_docs() -> None:
    cli_doc = Path("docs/CLI.md").read_text(encoding="utf-8")
    profiles_doc = Path("docs/PROFILES.md").read_text(encoding="utf-8")
    ci_doc = Path("docs/CI.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "./QUICKSTART.md" in cli_doc
    assert "./QUICKSTART.md" in profiles_doc
    assert "./QUICKSTART.md" in ci_doc
    assert "docs/QUICKSTART.md" in readme
