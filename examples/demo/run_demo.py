from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from content_review_engine.api import review_batch, review_file
from content_review_engine.llm import LLMProviderConfig


REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_ROOT = REPO_ROOT / "examples" / "demo"
ARTICLES_DIR = DEMO_ROOT / "articles"
PROFILES_DIR = DEMO_ROOT / "profiles"
DEFAULT_OUTPUT_ROOT = Path("examples/demo/artifacts")

WECHAT_ARTICLE = ARTICLES_DIR / "wechat-demo.md"
TECHNICAL_ARTICLE = ARTICLES_DIR / "technical-demo.md"
WECHAT_PROFILE = PROFILES_DIR / "wechat-demo.yaml"
TECHNICAL_PROFILE = PROFILES_DIR / "technical-demo.yaml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_demo.py",
        description="Regenerate the unified end-to-end demo artifacts.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Directory where demo artifacts will be written.",
    )
    return parser


def _json_text(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _repo_arg_path(path: Path) -> str:
    if not path.is_absolute():
        return str(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json_text(payload), encoding="utf-8")


def _prepare_output_root(output_root: Path) -> None:
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)


def _pythonpath_env() -> dict[str, str]:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = (
        src_path if not existing_pythonpath else f"{src_path}{os.pathsep}{existing_pythonpath}"
    )
    return env


def _run_command(
    args: list[str],
    *,
    expected_exit_codes: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=REPO_ROOT,
        env=_pythonpath_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in expected_exit_codes:
        joined = " ".join(args)
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: {joined}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result


def _validate_demo_profiles() -> None:
    for profile_path in (WECHAT_PROFILE, TECHNICAL_PROFILE):
        _run_command(
            [
                sys.executable,
                "-m",
                "content_review_engine.cli",
                "profile",
                "validate",
                str(profile_path.relative_to(REPO_ROOT)),
            ]
        )


def _generate_cli_artifacts(output_root: Path) -> None:
    cli_root = output_root / "cli"
    single_root = cli_root / "single-file"
    batch_root = cli_root / "batch"
    single_root.mkdir(parents=True, exist_ok=True)
    batch_root.mkdir(parents=True, exist_ok=True)

    single_text = _run_command(
        [
            sys.executable,
            "-m",
            "content_review_engine.cli",
            "review",
            str(WECHAT_ARTICLE.relative_to(REPO_ROOT)),
            "--profile",
            str(WECHAT_PROFILE.relative_to(REPO_ROOT)),
        ]
    )
    (single_root / "review.txt").write_text(single_text.stdout, encoding="utf-8")

    _run_command(
        [
            sys.executable,
            "-m",
            "content_review_engine.cli",
            "review",
            str(WECHAT_ARTICLE.relative_to(REPO_ROOT)),
            "--profile",
            str(WECHAT_PROFILE.relative_to(REPO_ROOT)),
            "--format",
            "json",
            "--output",
            _repo_arg_path(single_root / "review.json"),
            "--enable-llm",
            "--llm-provider",
            "mock",
            "--llm-output",
            _repo_arg_path(single_root / "llm-result.json"),
            "--combined-output",
            _repo_arg_path(single_root / "combined.json"),
            "--combined-output-format",
            "json",
            "--llm-fail-on",
            "warning",
        ]
    )

    _run_command(
        [
            sys.executable,
            "-m",
            "content_review_engine.cli",
            "review",
            str(WECHAT_ARTICLE.relative_to(REPO_ROOT)),
            "--profile",
            str(WECHAT_PROFILE.relative_to(REPO_ROOT)),
            "--format",
            "markdown",
            "--output",
            _repo_arg_path(single_root / "review.md"),
            "--enable-llm",
            "--llm-provider",
            "mock",
            "--llm-output",
            _repo_arg_path(single_root / "llm-result.json"),
            "--llm-report",
            _repo_arg_path(single_root / "llm-report.md"),
            "--combined-output",
            _repo_arg_path(single_root / "combined.md"),
            "--combined-output-format",
            "markdown",
            "--report-index",
            _repo_arg_path(single_root / "report-index.md"),
            "--fail-on",
            "warning",
            "--llm-fail-on",
            "warning",
        ],
        expected_exit_codes=(1,),
    )

    batch_text = _run_command(
        [
            sys.executable,
            "-m",
            "content_review_engine.cli",
            "batch",
            str(ARTICLES_DIR.relative_to(REPO_ROOT)),
            "--profile",
            str(TECHNICAL_PROFILE.relative_to(REPO_ROOT)),
            "--pattern",
            "technical-*.md",
        ]
    )
    (batch_root / "review.txt").write_text(batch_text.stdout, encoding="utf-8")

    _run_command(
        [
            sys.executable,
            "-m",
            "content_review_engine.cli",
            "batch",
            str(ARTICLES_DIR.relative_to(REPO_ROOT)),
            "--profile",
            str(TECHNICAL_PROFILE.relative_to(REPO_ROOT)),
            "--pattern",
            "technical-*.md",
            "--format",
            "json",
            "--output",
            _repo_arg_path(batch_root / "review.json"),
            "--enable-llm",
            "--llm-provider",
            "mock",
            "--llm-output",
            _repo_arg_path(batch_root / "llm-result.json"),
            "--combined-output",
            _repo_arg_path(batch_root / "combined.json"),
            "--combined-output-format",
            "json",
            "--llm-fail-on",
            "warning",
        ]
    )

    _run_command(
        [
            sys.executable,
            "-m",
            "content_review_engine.cli",
            "batch",
            str(ARTICLES_DIR.relative_to(REPO_ROOT)),
            "--profile",
            str(TECHNICAL_PROFILE.relative_to(REPO_ROOT)),
            "--pattern",
            "technical-*.md",
            "--format",
            "markdown",
            "--output",
            _repo_arg_path(batch_root / "review.md"),
            "--enable-llm",
            "--llm-provider",
            "mock",
            "--llm-output",
            _repo_arg_path(batch_root / "llm-result.json"),
            "--llm-report",
            _repo_arg_path(batch_root / "llm-report.md"),
            "--combined-output",
            _repo_arg_path(batch_root / "combined.md"),
            "--combined-output-format",
            "markdown",
            "--report-index",
            _repo_arg_path(batch_root / "report-index.md"),
            "--fail-on",
            "warning",
            "--llm-fail-on",
            "warning",
        ],
        expected_exit_codes=(1,),
    )


def _generate_api_artifacts(output_root: Path) -> None:
    api_root = output_root / "api"
    api_root.mkdir(parents=True, exist_ok=True)
    mock_config = LLMProviderConfig(provider="mock")

    single_result = review_file(
        WECHAT_ARTICLE.relative_to(REPO_ROOT),
        WECHAT_PROFILE.relative_to(REPO_ROOT),
        output_format="json",
        output_path=api_root / "single-file.review.json",
        enable_llm=True,
        llm_provider_config=mock_config,
        llm_output_path=api_root / "single-file.llm.json",
        combined_output_path=api_root / "single-file.combined.json",
        combined_output_format="json",
        include_combined_result=True,
        llm_fail_on="warning",
    )
    (api_root / "single-file.workflow.json").write_text(
        single_result.model_dump_json(indent=2, exclude_none=True),
        encoding="utf-8",
    )

    batch_result = review_batch(
        ARTICLES_DIR.relative_to(REPO_ROOT),
        TECHNICAL_PROFILE.relative_to(REPO_ROOT),
        pattern="technical-*.md",
        output_format="json",
        output_path=api_root / "batch.review.json",
        enable_llm=True,
        llm_provider_config=mock_config,
        llm_output_path=api_root / "batch.llm.json",
        combined_output_path=api_root / "batch.combined.json",
        combined_output_format="json",
        include_combined_result=True,
        llm_fail_on="warning",
    )
    (api_root / "batch.workflow.json").write_text(
        batch_result.model_dump_json(indent=2, exclude_none=True),
        encoding="utf-8",
    )


async def _generate_mcp_artifacts_async(output_root: Path) -> None:
    try:
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "MCP support is required for the unified demo. Run `uv sync --extra mcp` first."
        ) from exc

    mcp_root = output_root / "mcp"
    mcp_root.mkdir(parents=True, exist_ok=True)

    single_request = {
        "markdown_path": str(WECHAT_ARTICLE.relative_to(REPO_ROOT)),
        "profile_path": str(WECHAT_PROFILE.relative_to(REPO_ROOT)),
        "enable_llm": True,
        "llm_provider_config": {"provider": "mock"},
        "llm_fail_on": "warning",
        "include_combined_result": True,
    }
    batch_request = {
        "input_dir": str(ARTICLES_DIR.relative_to(REPO_ROOT)),
        "profile_path": str(TECHNICAL_PROFILE.relative_to(REPO_ROOT)),
        "pattern": "technical-*.md",
        "include_combined_result": True,
    }

    _write_json(mcp_root / "single-file.request.json", single_request)
    _write_json(mcp_root / "batch.request.json", batch_request)

    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "content_review_engine.mcp_server"],
        env=_pythonpath_env(),
        cwd=str(REPO_ROOT),
    )

    async with stdio_client(server) as (read_stream, write_stream):
        session = ClientSession(read_stream, write_stream)
        async with session:
            initialize_result = await session.initialize()
            _write_json(
                mcp_root / "initialize.json",
                {
                    "server_name": initialize_result.serverInfo.name,
                    "server_version": initialize_result.serverInfo.version,
                    "protocol_version": initialize_result.protocolVersion,
                },
            )

            tools = await session.list_tools()
            _write_json(
                mcp_root / "tools.json",
                {
                    "tool_names": [tool.name for tool in tools.tools],
                },
            )

            single_response = await session.call_tool("content_review_file", single_request)
            if single_response.isError:
                raise RuntimeError("MCP single-file demo call returned an error.")
            _write_json(mcp_root / "single-file.response.json", single_response.structuredContent)

            batch_response = await session.call_tool("content_review_batch", batch_request)
            if batch_response.isError:
                raise RuntimeError("MCP batch demo call returned an error.")
            _write_json(mcp_root / "batch.response.json", batch_response.structuredContent)


def _generate_mcp_artifacts(output_root: Path) -> None:
    asyncio.run(_generate_mcp_artifacts_async(output_root))


def _artifact_summary(output_root: Path) -> str:
    paths = sorted(path.relative_to(output_root) for path in output_root.rglob("*") if path.is_file())
    lines = [f"- {path.as_posix()}" for path in paths]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    os.chdir(REPO_ROOT)
    output_root = Path(args.output_root)

    _prepare_output_root(output_root)
    _validate_demo_profiles()
    _generate_cli_artifacts(output_root)
    _generate_api_artifacts(output_root)
    _generate_mcp_artifacts(output_root)

    print("Unified demo artifacts regenerated.")
    print(f"Output root: {(REPO_ROOT / output_root).resolve() if not output_root.is_absolute() else output_root}")
    print("Artifacts:")
    print(_artifact_summary(output_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
