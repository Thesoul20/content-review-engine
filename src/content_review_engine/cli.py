from __future__ import annotations

import argparse
import sys
from pathlib import Path

from content_review_engine.config import load_profile
from content_review_engine.core.models import ReviewResult
from content_review_engine.core.serialization import review_result_to_json
from content_review_engine.parser import read_markdown
from content_review_engine.reports import render_markdown_report
from content_review_engine.review import review_document
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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1

    try:
        if args.command != "review":
            parser.print_help()
            return 1

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
        if args.output is not None:
            try:
                Path(args.output).write_text(rendered_output, encoding="utf-8")
            except OSError as exc:
                print(f"Error: {exc}", file=sys.stderr)
                return 2
        else:
            print(rendered_output)
        return 0
    except (FileNotFoundError, ValueError, ValidationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
