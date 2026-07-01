from __future__ import annotations

import argparse
import re

from mcp.server.fastmcp import FastMCP

from content_review_engine.api import (
    CombinedOutputFormat,
    ReviewBatchWorkflowResult,
    ReviewFileWorkflowResult,
    ReviewOutputFormat,
    review_batch,
    review_file,
)
from content_review_engine.llm import LLMProviderConfig

_DEFAULT_SERVER_NAME = "content-review-engine"
_SECRET_PATTERNS = (
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9._\-]+\b"),
    re.compile(
        r"(?i)\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*([^\s,;]+)"
    ),
)


def _sanitize_error_message(message: str) -> str:
    sanitized = message
    sanitized = _SECRET_PATTERNS[0].sub("Bearer [REDACTED]", sanitized)
    sanitized = _SECRET_PATTERNS[1].sub("[REDACTED]", sanitized)
    sanitized = _SECRET_PATTERNS[2].sub(r"\1=[REDACTED]", sanitized)
    return sanitized


def _raise_sanitized_error(exc: Exception) -> None:
    raise ValueError(_sanitize_error_message(str(exc))) from None


def create_mcp_server() -> FastMCP:
    mcp = FastMCP(
        _DEFAULT_SERVER_NAME,
        instructions=(
            "Structured Markdown content review tools backed by the "
            "content_review_engine Python API. Tools are deterministic-only by "
            "default. Optional LLM review remains explicit opt-in."
        ),
        json_response=True,
    )

    @mcp.tool(
        name="content_review_file",
        description=(
            "Review one Markdown file against one review profile. Uses "
            "content_review_engine.api.review_file(...) and returns a JSON-"
            "compatible structured workflow result."
        ),
        structured_output=True,
    )
    def content_review_file(
        markdown_path: str,
        profile_path: str,
        output_format: ReviewOutputFormat = "text",
        output_path: str | None = None,
        fail_on: str | None = None,
        enable_llm: bool = False,
        llm_fail_on: str | None = None,
        llm_output_path: str | None = None,
        combined_output_path: str | None = None,
        combined_output_format: CombinedOutputFormat = "markdown",
        include_combined_result: bool = False,
        llm_provider_config: LLMProviderConfig | None = None,
        llm_config_path: str | None = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
        llm_api_key_env: str | None = None,
        llm_base_url: str | None = None,
        llm_timeout_seconds: float | None = None,
        llm_retry_attempts: int | None = None,
        llm_retry_backoff_seconds: float | None = None,
        llm_min_request_interval_seconds: float | None = None,
    ) -> ReviewFileWorkflowResult:
        try:
            return review_file(
                markdown_path,
                profile_path,
                output_format=output_format,
                output_path=output_path,
                fail_on=fail_on,
                enable_llm=enable_llm,
                llm_fail_on=llm_fail_on,
                llm_output_path=llm_output_path,
                combined_output_path=combined_output_path,
                combined_output_format=combined_output_format,
                include_combined_result=include_combined_result,
                llm_provider_config=llm_provider_config,
                llm_config_path=llm_config_path,
                llm_provider=llm_provider,
                llm_model=llm_model,
                llm_api_key_env=llm_api_key_env,
                llm_base_url=llm_base_url,
                llm_timeout_seconds=llm_timeout_seconds,
                llm_retry_attempts=llm_retry_attempts,
                llm_retry_backoff_seconds=llm_retry_backoff_seconds,
                llm_min_request_interval_seconds=llm_min_request_interval_seconds,
            )
        except Exception as exc:
            _raise_sanitized_error(exc)

    @mcp.tool(
        name="content_review_batch",
        description=(
            "Review one directory of Markdown files against one review profile. "
            "Uses content_review_engine.api.review_batch(...) and returns a "
            "JSON-compatible structured workflow result."
        ),
        structured_output=True,
    )
    def content_review_batch(
        input_dir: str,
        profile_path: str,
        pattern: str = "*.md",
        recursive: bool = False,
        output_format: ReviewOutputFormat = "text",
        output_path: str | None = None,
        fail_on: str | None = None,
        enable_llm: bool = False,
        llm_fail_on: str | None = None,
        llm_output_path: str | None = None,
        combined_output_path: str | None = None,
        combined_output_format: CombinedOutputFormat = "markdown",
        include_combined_result: bool = False,
        llm_provider_config: LLMProviderConfig | None = None,
        llm_config_path: str | None = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
        llm_api_key_env: str | None = None,
        llm_base_url: str | None = None,
        llm_timeout_seconds: float | None = None,
        llm_retry_attempts: int | None = None,
        llm_retry_backoff_seconds: float | None = None,
        llm_min_request_interval_seconds: float | None = None,
    ) -> ReviewBatchWorkflowResult:
        try:
            return review_batch(
                input_dir,
                profile_path,
                pattern=pattern,
                recursive=recursive,
                output_format=output_format,
                output_path=output_path,
                fail_on=fail_on,
                enable_llm=enable_llm,
                llm_fail_on=llm_fail_on,
                llm_output_path=llm_output_path,
                combined_output_path=combined_output_path,
                combined_output_format=combined_output_format,
                include_combined_result=include_combined_result,
                llm_provider_config=llm_provider_config,
                llm_config_path=llm_config_path,
                llm_provider=llm_provider,
                llm_model=llm_model,
                llm_api_key_env=llm_api_key_env,
                llm_base_url=llm_base_url,
                llm_timeout_seconds=llm_timeout_seconds,
                llm_retry_attempts=llm_retry_attempts,
                llm_retry_backoff_seconds=llm_retry_backoff_seconds,
                llm_min_request_interval_seconds=llm_min_request_interval_seconds,
            )
        except Exception as exc:
            _raise_sanitized_error(exc)

    return mcp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="content-review-mcp",
        description="Run the content-review-engine MCP server.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default="stdio",
        help="MCP transport. Default: stdio.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    create_mcp_server().run(transport=args.transport)


__all__ = ["build_parser", "create_mcp_server", "main"]


if __name__ == "__main__":
    main()
