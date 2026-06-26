from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from content_review_engine.config import (
    get_profile_template_content,
    list_profile_template_names,
    list_profile_templates,
    load_profile,
    validate_profile,
)
from content_review_engine.config.profiles import ProfileValidationFailed
from content_review_engine.core.models import (
    BatchReviewResult,
    ProfileValidationResult,
    ProfileTemplateListResult,
    ProfileTemplateSummary,
    ReviewResult,
)
from content_review_engine.core.quality_gate import (
    SEVERITY_ORDER,
    quality_gate_failed,
    severity_rank,
)
from content_review_engine.core.serialization import (
    batch_review_result_to_json,
    profile_template_list_result_to_json,
    profile_validation_result_to_json,
    review_result_to_json,
)
from content_review_engine.llm import (
    LLMReviewRequest,
    LLMReviewError,
    LLMReviewResult,
    LLMReviewRunner,
    MockLLMReviewer,
    PYDANTICAI_OPENAI_PROVIDER_NAME,
    PydanticAIOpenAIReviewer,
    llm_review_result_to_json,
)
from content_review_engine.parser import read_markdown
from content_review_engine.reports import (
    render_batch_markdown_report,
    render_markdown_report,
)
from content_review_engine.review import review_document, review_markdown_directory
from content_review_engine.rules import UnknownRuleError
from pydantic import ValidationError


def _parse_fail_on(value: str) -> str:
    try:
        severity_rank(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return value


def _parse_llm_provider(value: str) -> str:
    normalized = value.strip()
    if normalized not in {"mock", PYDANTICAI_OPENAI_PROVIDER_NAME}:
        raise argparse.ArgumentTypeError(
            "Unsupported LLM provider: "
            f"{value!r}. Supported providers are 'mock' and "
            f"'{PYDANTICAI_OPENAI_PROVIDER_NAME}'."
        )
    return normalized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="content-review",
        description="Review a Markdown document with a YAML profile.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    review_parser = subparsers.add_parser(
        "review",
        help="Review one Markdown file with one YAML profile.",
    )
    review_parser.add_argument("markdown_file", help="Path to the Markdown file.")
    review_parser.add_argument(
        "--profile",
        required=True,
        help="Path to the YAML review profile.",
    )
    review_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format for the review result.",
    )
    review_parser.add_argument(
        "--output",
        help="Write the rendered review output to a file.",
    )
    review_parser.add_argument(
        "--fail-on",
        metavar="SEVERITY",
        type=_parse_fail_on,
        choices=SEVERITY_ORDER,
        help="Exit with code 1 when findings are at or above the severity threshold.",
    )
    review_parser.add_argument(
        "--enable-llm",
        action="store_true",
        help="Enable experimental LLM review sidecar output.",
    )
    review_parser.add_argument(
        "--llm-provider",
        type=_parse_llm_provider,
        default=None,
        help=(
            "LLM provider for experimental sidecar review. "
            "Supported: 'mock', 'pydanticai-openai'."
        ),
    )
    review_parser.add_argument(
        "--llm-model",
        default=None,
        help="Model name for --llm-provider pydanticai-openai.",
    )
    review_parser.add_argument(
        "--llm-api-key-env",
        default=None,
        help=(
            "Environment variable name used to read the API key for "
            "--llm-provider pydanticai-openai. Defaults to OPENAI_API_KEY."
        ),
    )
    review_parser.add_argument(
        "--llm-base-url",
        default=None,
        help="Optional OpenAI-compatible base URL for --llm-provider pydanticai-openai.",
    )
    review_parser.add_argument(
        "--llm-output",
        help="Write the experimental LLM review result JSON sidecar to a file.",
    )
    review_parser.add_argument(
        "--include-llm-report",
        action="store_true",
        help="Append the LLM review result to --format markdown output.",
    )

    profile_parser = subparsers.add_parser(
        "profile",
        help="Validate review profile YAML files.",
    )
    profile_subparsers = profile_parser.add_subparsers(
        dest="profile_command",
        required=True,
    )
    validate_parser = profile_subparsers.add_parser(
        "validate",
        help="Validate a review profile YAML file.",
    )
    validate_parser.add_argument(
        "profile_path",
        help="Path to the YAML review profile.",
    )
    validate_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the validation result.",
    )
    init_parser = profile_subparsers.add_parser(
        "init",
        help="Create a new review profile from a built-in template.",
        description="Create a new review profile from a built-in template.",
    )
    init_parser.add_argument(
        "--template",
        required=True,
        choices=list_profile_template_names(),
        help="Built-in template name.",
    )
    init_parser.add_argument(
        "--output",
        required=True,
        help="Path to the generated YAML review profile.",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it already exists.",
    )
    list_parser = profile_subparsers.add_parser(
        "list",
        help="List available built-in review profile templates.",
        description="List available built-in review profile templates.",
    )
    list_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the template list.",
    )

    batch_parser = subparsers.add_parser(
        "batch",
        help="Review Markdown files in a directory with one YAML profile.",
    )
    batch_parser.add_argument("input_dir", help="Path to the Markdown directory.")
    batch_parser.add_argument(
        "--profile",
        required=True,
        help="Path to the YAML review profile.",
    )
    batch_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format for the batch review result.",
    )
    batch_parser.add_argument(
        "--output",
        help="Write the rendered batch output to a file.",
    )
    batch_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively discover Markdown files.",
    )
    batch_parser.add_argument(
        "--pattern",
        default="*.md",
        help="Glob pattern used to discover Markdown files.",
    )
    batch_parser.add_argument(
        "--fail-on",
        metavar="SEVERITY",
        type=_parse_fail_on,
        choices=SEVERITY_ORDER,
        help="Exit with code 1 when findings are at or above the severity threshold.",
    )

    return parser


def _render_text_report(review_result: ReviewResult) -> str:
    lines = [
        "Review completed.",
        "",
        f"Findings: {review_result.summary.finding_count}",
        "",
    ]

    if not review_result.findings:
        lines.append("No issues found.")
        return "\n".join(lines)

    for finding in review_result.findings:
        lines.append(f"[{finding.severity}] {finding.rule_id}: {finding.message}")
        if finding.suggestion:
            lines.append(f"Suggestion: {finding.suggestion}")
        location = finding.location
        if location is not None:
            lines.append(f"Line: {location.start_line}")
            lines.append(f"Column: {location.start_column}")
            lines.append(f"Matched: {location.matched_text}")
            if location.context is not None:
                lines.append(f"Context: {location.context}")
        lines.append("")

    return "\n".join(lines)


def _render_json_report(review_result: ReviewResult) -> str:
    return review_result_to_json(review_result)


def _render_output(
    review_result: ReviewResult,
    *,
    output_format: str,
    fail_on: str | None = None,
    llm_result: LLMReviewResult | None = None,
) -> str:
    if output_format == "json":
        return _render_json_report(review_result)
    if output_format == "markdown":
        return render_markdown_report(
            review_result,
            fail_on=fail_on,
            llm_result=llm_result,
        )
    return _render_text_report(review_result)


def _render_batch_text_report(batch_result: BatchReviewResult) -> str:
    lines = [
        "Batch review completed.",
        "",
        f"Files discovered: {batch_result.summary.file_count}",
        f"Files reviewed: {batch_result.summary.reviewed_count}",
        f"Files with findings: {batch_result.summary.files_with_findings}",
        f"Findings: {batch_result.summary.finding_count}",
        "",
    ]

    if not batch_result.results:
        lines.append("No Markdown files found.")
        return "\n".join(lines)

    for review_result in batch_result.results:
        document_path = (
            review_result.document.path if review_result.document is not None else "Unknown"
        )
        lines.append(f"[{document_path}] Findings: {review_result.summary.finding_count}")

        if not review_result.findings:
            lines.append("No issues found.")
            lines.append("")
            continue

        for finding in review_result.findings:
            lines.append(f"[{finding.severity}] {finding.rule_id} - {finding.message}")
            if finding.suggestion:
                lines.append(f"Suggestion: {finding.suggestion}")
            location = finding.location
            if location is not None:
                lines.append(f"Line: {location.start_line}")
                lines.append(f"Column: {location.start_column}")
                lines.append(f"Matched: {location.matched_text}")
                if location.context is not None:
                    lines.append(f"Context: {location.context}")
            lines.append("")

    if lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)


def _render_batch_json_report(batch_result: BatchReviewResult) -> str:
    return batch_review_result_to_json(batch_result)


def _render_batch_output(
    batch_result: BatchReviewResult,
    *,
    output_format: str,
    fail_on: str | None = None,
) -> str:
    if output_format == "json":
        return _render_batch_json_report(batch_result)
    if output_format == "markdown":
        return render_batch_markdown_report(batch_result, fail_on=fail_on)
    return _render_batch_text_report(batch_result)


def _render_profile_validation_text(result) -> str:
    if result.valid and result.profile is not None:
        lines = [
            "Profile validation passed.",
            "",
            f"Path: {result.path}",
        ]
        lines.extend(
            [
                f"Name: {result.profile.name}",
                f"Target Platform: {result.profile.target_platform}",
                f"Enabled Rules: {result.profile.enabled_rule_count}",
                f"Disabled Rules: {result.profile.disabled_rule_count}",
                "Rules:",
            ]
        )
        if result.profile.rules:
            for rule in result.profile.rules:
                lines.append(f"- {rule.id}")
        else:
            lines.append("- None")
        return "\n".join(lines)

        return "\n".join(lines)

    lines = [
        f"Profile validation failed: {result.path}",
        f"Issues: {len(result.errors)}",
    ]

    if result.errors:
        lines.append("")

    for index, error in enumerate(result.errors, start=1):
        lines.append(f"{index}. {error.path}")
        lines.append(f"   Code: {error.code}")
        lines.append(f"   Error: {error.message}")
        if error.suggestion:
            lines.append(f"   Suggestion: {error.suggestion}")
        if index != len(result.errors):
            lines.append("")

    return "\n".join(lines)


def _render_profile_validation_output(result, *, output_format: str) -> str:
    if output_format == "json":
        return profile_validation_result_to_json(result)
    return _render_profile_validation_text(result)


def _render_profile_init_text(*, template_name: str, output_path: Path) -> str:
    return "\n".join(
        [
            "Profile created.",
            "",
            f"Template: {template_name}",
            f"Output: {output_path}",
            "",
            "Next steps:",
            "1. Edit the profile terms and severity levels.",
            f"2. Validate it with: content-review profile validate {output_path}",
            f"3. Use it with: content-review review article.md --profile {output_path}",
        ]
    )


def _build_profile_template_list_result() -> ProfileTemplateListResult:
    return ProfileTemplateListResult(
        templates=[
            ProfileTemplateSummary(
                name=template.name,
                description=template.description,
            )
            for template in list_profile_templates()
        ]
    )


def _render_profile_list_text(result: ProfileTemplateListResult) -> str:
    lines = ["Available profile templates:", ""]

    for template in result.templates:
        lines.append(f"- {template.name}")
        lines.append(f"  {template.description}")
        lines.append("")

    lines.extend(
        [
            "Use a template:",
            "",
            "  content-review profile init --template wechat-basic --output profile.yaml",
        ]
    )
    return "\n".join(lines)


def _render_profile_list_output(*, output_format: str) -> str:
    result = _build_profile_template_list_result()
    if output_format == "json":
        return profile_template_list_result_to_json(result)
    return _render_profile_list_text(result)


def _write_or_print_output(output_text: str, output_path: str | None) -> int:
    if output_path is not None:
        try:
            Path(output_path).write_text(output_text, encoding="utf-8")
        except OSError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        return 0

    print(output_text)
    return 0


def _quality_gate_exit_code(
    severity_counts: dict[str, int],
    threshold: str | None,
) -> int:
    return 1 if quality_gate_failed(severity_counts, threshold) else 0


def _validate_review_llm_args(args: argparse.Namespace) -> None:
    if not args.enable_llm:
        if args.llm_output is not None:
            raise ValueError("--llm-output requires --enable-llm")
        if args.llm_provider is not None:
            raise ValueError("--llm-provider requires --enable-llm")
        if args.llm_model is not None:
            raise ValueError("--llm-model requires --enable-llm")
        if args.llm_api_key_env is not None:
            raise ValueError("--llm-api-key-env requires --enable-llm")
        if args.llm_base_url is not None:
            raise ValueError("--llm-base-url requires --enable-llm")
        if args.include_llm_report:
            raise ValueError("--include-llm-report requires --enable-llm")
        return

    if args.llm_output is None:
        raise ValueError("--enable-llm requires --llm-output")
    if args.include_llm_report and args.format != "markdown":
        raise ValueError("--include-llm-report requires --format markdown")

    provider = args.llm_provider or "mock"
    if provider == "mock":
        return

    if provider == PYDANTICAI_OPENAI_PROVIDER_NAME and args.llm_model is None:
        raise ValueError(
            "--llm-provider pydanticai-openai requires --llm-model"
        )


def _build_llm_reviewer(args: argparse.Namespace):
    provider = args.llm_provider or "mock"
    if provider == "mock":
        return MockLLMReviewer()

    api_key_env = args.llm_api_key_env or "OPENAI_API_KEY"
    api_key = os.environ.get(api_key_env, "").strip()
    if api_key == "":
        raise ValueError(
            "Environment variable "
            f"{api_key_env!r} is required for --llm-provider pydanticai-openai"
        )

    return PydanticAIOpenAIReviewer(
        model=args.llm_model,
        api_key=api_key,
        base_url=args.llm_base_url,
    )


def _build_llm_review_request(
    *,
    markdown_text: str,
    markdown_path: str,
    profile_name: str,
) -> LLMReviewRequest:
    return LLMReviewRequest(
        content=markdown_text,
        profile_name=profile_name,
        content_path=markdown_path,
        review_goal="semantic_review",
    )


def _run_llm_review(
    *,
    markdown_text: str,
    markdown_path: str,
    profile_name: str,
    reviewer,
) -> LLMReviewResult:
    request = _build_llm_review_request(
        markdown_text=markdown_text,
        markdown_path=markdown_path,
        profile_name=profile_name,
    )
    runner = LLMReviewRunner(reviewer=reviewer)
    return runner.run(request)


def _write_llm_sidecar(
    *,
    llm_result: LLMReviewResult,
    output_path: str,
) -> None:
    Path(output_path).write_text(
        llm_review_result_to_json(llm_result),
        encoding="utf-8",
    )


def _run_review_command(args: argparse.Namespace) -> int:
    _validate_review_llm_args(args)
    llm_reviewer = _build_llm_reviewer(args) if args.enable_llm else None
    markdown_text = read_markdown(args.markdown_file)
    profile = load_profile(args.profile)
    review_result = review_document(
        markdown_text,
        profile,
        document_path=args.markdown_file,
        profile_path=args.profile,
    )
    llm_result = None
    if args.enable_llm:
        llm_result = _run_llm_review(
            markdown_text=markdown_text,
            markdown_path=args.markdown_file,
            profile_name=profile.name,
            reviewer=llm_reviewer,
        )
    rendered_output = _render_output(
        review_result,
        output_format=args.format,
        fail_on=args.fail_on,
        llm_result=llm_result if args.include_llm_report else None,
    )
    output_exit_code = _write_or_print_output(rendered_output, args.output)
    if output_exit_code != 0:
        return output_exit_code
    if args.enable_llm:
        _write_llm_sidecar(
            llm_result=llm_result,
            output_path=args.llm_output,
        )
    return _quality_gate_exit_code(
        review_result.summary.severity_counts,
        args.fail_on,
    )


def _run_batch_command(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    batch_result = review_markdown_directory(
        Path(args.input_dir),
        profile,
        pattern=args.pattern,
        recursive=args.recursive,
        profile_path=args.profile,
    )
    rendered_output = _render_batch_output(
        batch_result,
        output_format=args.format,
        fail_on=args.fail_on,
    )
    output_exit_code = _write_or_print_output(rendered_output, args.output)
    if output_exit_code != 0:
        return output_exit_code
    return _quality_gate_exit_code(
        batch_result.summary.severity_counts,
        args.fail_on,
    )


def _run_profile_validate_command(args: argparse.Namespace) -> int:
    validation_result = validate_profile(args.profile_path)
    rendered_output = _render_profile_validation_output(
        validation_result,
        output_format=args.format,
    )
    output_exit_code = _write_or_print_output(rendered_output, None)
    if output_exit_code != 0:
        return output_exit_code
    return 0 if validation_result.valid else 2


def _render_profile_validation_exception(exc: ProfileValidationFailed) -> str:
    return _render_profile_validation_text(
        ProfileValidationResult(
            valid=False,
            path=exc.path,
            errors=list(exc.issues),
        )
    )


def _run_profile_init_command(args: argparse.Namespace) -> int:
    output_path = Path(args.output)
    parent_dir = output_path.parent

    if parent_dir != Path(".") and not parent_dir.exists():
        raise ValueError(f"Parent directory does not exist: {parent_dir}")

    if output_path.exists() and not args.force:
        raise ValueError(
            f"Output file already exists: {output_path}. Use --force to overwrite."
        )

    template_text = get_profile_template_content(args.template)

    output_path.write_text(template_text, encoding="utf-8")
    load_profile(output_path)

    rendered_output = _render_profile_init_text(
        template_name=args.template,
        output_path=output_path,
    )
    return _write_or_print_output(rendered_output, None)


def _run_profile_list_command(args: argparse.Namespace) -> int:
    rendered_output = _render_profile_list_output(output_format=args.format)
    return _write_or_print_output(rendered_output, None)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1

    try:
        if args.command == "review":
            return _run_review_command(args)
        if args.command == "profile" and args.profile_command == "validate":
            return _run_profile_validate_command(args)
        if args.command == "profile" and args.profile_command == "init":
            return _run_profile_init_command(args)
        if args.command == "profile" and args.profile_command == "list":
            return _run_profile_list_command(args)
        if args.command == "batch":
            return _run_batch_command(args)

        parser.print_help()
        return 1
    except UnknownRuleError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except ProfileValidationFailed as exc:
        print(_render_profile_validation_exception(exc), file=sys.stderr)
        return 2
    except (
        FileNotFoundError,
        NotADirectoryError,
        OSError,
        LLMReviewError,
        ValueError,
        ValidationError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
