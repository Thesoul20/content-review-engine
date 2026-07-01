from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path


def test_mcp_dependency_is_optional_in_pyproject() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    dependencies = pyproject["project"]["dependencies"]
    optional_dependencies = pyproject["project"]["optional-dependencies"]
    dev_dependencies = pyproject["dependency-groups"]["dev"]

    assert all(not dep.startswith("mcp[cli]") for dep in dependencies)
    assert optional_dependencies["mcp"] == ["mcp[cli]>=1.27,<2"]
    assert "mcp[cli]>=1.27,<2" in dev_dependencies


def test_mcp_module_entrypoint_help_smoke() -> None:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        "src" if not existing_pythonpath else f"src{os.pathsep}{existing_pythonpath}"
    )

    result = subprocess.run(
        [sys.executable, "-m", "content_review_engine.mcp_server", "--help"],
        cwd=Path.cwd(),
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0
    assert "content-review-mcp" in result.stdout
    assert "--transport" in result.stdout


def test_mcp_client_config_examples_are_valid_json() -> None:
    for path in (
        Path("examples/mcp_server/codex-config.example.json"),
        Path("examples/mcp_server/claude-desktop-config.example.json"),
    ):
        payload = json.loads(path.read_text(encoding="utf-8"))
        server = payload["mcpServers"]["content-review-engine"]

        assert server["command"] == "uv"
        assert server["args"] == [
            "run",
            "--directory",
            "/ABSOLUTE/PATH/TO/content-review-engine",
            "content-review-mcp",
        ]
        assert server["env"] == {}
        assert "OPENAI_API_KEY" not in path.read_text(encoding="utf-8")


def test_mcp_tool_call_examples_are_valid_json_and_do_not_include_raw_api_keys() -> None:
    examples_dir = Path("examples/mcp_server/tool-call-examples")
    example_paths = sorted(examples_dir.glob("*.json"))

    assert example_paths

    for path in example_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        serialized = json.dumps(payload)

        assert isinstance(payload, dict)
        assert "api_key" not in serialized.lower()
        assert "sk-" not in serialized

