from pathlib import Path


def test_github_actions_example_exists_and_contains_key_commands() -> None:
    workflow_path = Path("docs/examples/github-actions/content-review.yml")

    assert workflow_path.exists()

    content = workflow_path.read_text(encoding="utf-8")

    assert "uv run content-review profile validate" in content
    assert "uv run content-review batch" in content
    assert "--fail-on error" in content
    assert "profiles/examples/wechat-strict.yaml" in content


def test_ci_docs_exist_and_explain_exit_codes_and_limits() -> None:
    ci_doc_path = Path("docs/CI.md")

    assert ci_doc_path.exists()

    content = ci_doc_path.read_text(encoding="utf-8")

    assert "docs/examples/github-actions/content-review.yml" in content
    assert "content-review profile validate" in content
    assert "content-review batch" in content
    assert "--fail-on error" in content
    assert "--combined-output" in content
    assert "does not auto-enable LLM review" in content
    assert "--llm-fail-on" in content
    assert "Only deterministic findings can trigger exit code `1` unless" in content
    assert "`0`" in content
    assert "`1`" in content
    assert "`2`" in content
    assert "legal, advertising, medical, regulatory, or platform compliance" in content
