from pathlib import Path


def test_architecture_docs_describe_rule_registry_boundary() -> None:
    content = Path("docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    normalized = " ".join(content.split())

    assert "## Rule Registry Boundaries" in content
    assert "src/content_review_engine/core/rule_registry.py" in content
    assert "src/content_review_engine/rules/registry.py" in content
    assert "metadata registry is descriptive only" in normalized
    assert "execution registry is operational" in normalized
    assert "They should not be merged yet." in content
    assert "Optional Future LLM Semantic Review" in content
    assert "Rule Metadata Registry" in content
    assert "Docs / Tests / Future CLI metadata display / Profile guidance" in content


def test_rules_docs_distinguish_metadata_from_execution_and_future_llm_layer() -> None:
    content = Path("docs/RULES.md").read_text(encoding="utf-8")
    normalized = " ".join(content.split())

    assert "docs/RULES.md` remains the canonical user-facing rule reference." in content
    assert "src/content_review_engine/core/rule_registry.py" in content
    assert "src/content_review_engine/rules/registry.py" in content
    assert "The registry is descriptive only. It does not run rules" in content
    assert "remains execution-focused" in content
    assert "future LLM semantic review layer is added" in normalized
    assert "produce compatible findings later" in normalized


def test_data_models_docs_state_registry_metadata_does_not_change_json_schema() -> None:
    content = Path("docs/DATA_MODELS.md").read_text(encoding="utf-8")
    normalized = " ".join(content.split())

    assert "internal metadata only" in normalized
    assert "It is not a field in the canonical review or batch JSON output schemas" in normalized
    assert "does not add fields to `ReviewFinding`, `ReviewResult`, or `BatchReviewResult`" in normalized
    assert "TASK-0029 does not add an LLM-specific finding schema." in normalized


def test_profiles_docs_state_metadata_registry_does_not_replace_profile_configuration() -> None:
    content = Path("docs/PROFILES.md").read_text(encoding="utf-8")
    normalized = " ".join(content.split())

    assert "That metadata registry is descriptive only." in content
    assert "does not replace YAML profile configuration" in normalized
    assert "The metadata registry does not replace profile configuration." in content
    assert "future LLM semantic review layer would be a separate later architecture layer" in normalized
