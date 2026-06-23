from __future__ import annotations

import argparse
import sys
from pathlib import Path

from content_review_engine.config import load_profile
from content_review_engine.core.models import BatchReviewResult, ReviewResult
from content_review_engine.core.serialization import (
    batch_review_result_to_json,
    review_result_to_json,
)
from content_review_engine.parser import read_markdown
from content_review_engine.reports import (
    render_batch_markdown_report,
    render_markdown_report,
)
from content_review_engine.review import review_document, review_markdown_directory
from content_review_engine.rules import UnknownRuleError
from pydantic import ValidationError


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
) -> str:
    if output_format == "json":
        return _render_json_report(review_result)
    if output_format == "markdown":
        return render_markdown_report(review_result)
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
) -> str:
    if output_format == "json":
        return _render_batch_json_report(batch_result)
    if output_format == "markdown":
        return render_batch_markdown_report(batch_result)
    return _render_batch_text_report(batch_result)


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


def _run_review_command(args: argparse.Namespace) -> int:
    markdown_text = read_markdown(args.markdown_file)
    profile = load_profile(args.profile)
    review_result = review_document(
        markdown_text,
        profile,
        document_path=args.markdown_file,
        profile_path=args.profile,
    )
    rendered_output = _render_output(
        review_result,
        output_format=args.format,
    )
    return _write_or_print_output(rendered_output, args.output)


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
    )
    return _write_or_print_output(rendered_output, args.output)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1

    try:
        if args.command == "review":
            return _run_review_command(args)
        if args.command == "batch":
            return _run_batch_command(args)

        parser.print_help()
        return 1
    except UnknownRuleError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except (FileNotFoundError, NotADirectoryError, ValueError, ValidationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2 if args.command == "batch" else 1


if __name__ == "__main__":
    raise SystemExit(main())
