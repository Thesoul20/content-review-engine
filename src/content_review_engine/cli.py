from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from content_review_engine.config import load_profile
from content_review_engine.core.models import ReviewFinding
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


def _build_json_payload(findings: list[ReviewFinding]) -> dict[str, object]:
    return {
        "findings": [finding.model_dump(mode="json") for finding in findings],
        "summary": {
            "finding_count": len(findings),
        },
    }


def _render_text_report(findings: list[ReviewFinding]) -> str:
    lines = [
        "Review completed.",
        "",
        f"Findings: {len(findings)}",
        "",
    ]

    if not findings:
        lines.append("No issues found.")
        return "\n".join(lines)

    for finding in findings:
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


def _render_json_report(findings: list[ReviewFinding]) -> str:
    payload = _build_json_payload(findings)
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _render_output(
    findings: list[ReviewFinding],
    *,
    output_format: str,
    markdown_file: str,
    profile_name: str,
    profile_path: str,
) -> str:
    if output_format == "json":
        return _render_json_report(findings)
    if output_format == "markdown":
        return render_markdown_report(
            findings,
            document_path=markdown_file,
            profile_name=profile_name,
            profile_path=profile_path,
        )
    return _render_text_report(findings)


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
        findings = review_document(markdown_text, profile)
        rendered_output = _render_output(
            findings,
            output_format=args.format,
            markdown_file=args.markdown_file,
            profile_name=profile.name,
            profile_path=args.profile,
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
