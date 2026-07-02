from pathlib import Path


def test_local_ci_scripts_exist_and_contain_expected_commands() -> None:
    standard = Path("scripts/ci.sh")
    strict = Path("scripts/ci-strict.sh")

    assert standard.exists()
    assert strict.exists()

    standard_content = standard.read_text(encoding="utf-8")
    strict_content = strict.read_text(encoding="utf-8")

    assert "uv sync --extra mcp --group dev" in standard_content
    assert "uv run pytest" in standard_content
    assert "content-review-mcp --help" in standard_content
    assert "scripts/ci.sh" in strict_content
    assert "uv build" in strict_content
    assert "git diff --exit-code" in strict_content


def test_active_github_actions_workflow_exists_and_contains_core_steps() -> None:
    workflow_path = Path(".github/workflows/ci.yml")

    assert workflow_path.exists()

    content = workflow_path.read_text(encoding="utf-8")

    assert "uv sync --extra mcp --group dev" in content
    assert "uv run pytest" in content
    assert "uv run content-review --help" in content
    assert "uv run content-review-mcp --help" in content
    assert "examples/demo/profiles/wechat-demo.yaml" in content


def test_strict_github_actions_workflow_exists_and_checks_for_artifact_drift() -> None:
    workflow_path = Path(".github/workflows/ci-strict.yml")

    assert workflow_path.exists()

    content = workflow_path.read_text(encoding="utf-8")

    assert "uv sync --extra mcp --group dev" in content
    assert "uv run pytest" in content
    assert "uv build" in content
    assert "dist/*.whl" in content
    assert "uv run python examples/demo/run_demo.py" in content
    assert "git diff --exit-code" in content


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
    assert ".github/workflows/ci.yml" in content
    assert ".github/workflows/ci-strict.yml" in content
    assert "scripts/ci.sh" in content
    assert "scripts/ci-strict.sh" in content
    assert "content-review profile validate" in content
    assert "content-review batch" in content
    assert "--fail-on error" in content
    assert "--combined-output" in content
    assert "does not auto-enable LLM review" in content
    assert "--llm-fail-on" in content
    assert "Only deterministic findings can trigger exit code `1` unless" in content
    assert "provider configuration is only responsible for LLM execution" in content
    assert "`0`" in content
    assert "`1`" in content
    assert "`2`" in content
    assert "legal, advertising, medical, regulatory, or platform compliance" in content
