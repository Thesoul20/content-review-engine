from __future__ import annotations

import argparse
import json
import sys

from content_review_engine.config import load_profile
from content_review_engine.core.models import ReviewFinding
from content_review_engine.parser import read_markdown
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
        choices=["text", "json"],
        default="text",
        help="Output format for the review result.",
    )

    return parser


def _build_json_payload(findings: list[ReviewFinding]) -> dict[str, object]:
    return {
        "findings": [finding.model_dump(mode="json") for finding in findings],
        "summary": {
            "finding_count": len(findings),
        },
    }


def _print_text_findings(findings: list[ReviewFinding]) -> None:
    print("Review completed.")
    print()
    print(f"Findings: {len(findings)}")
    print()

    if not findings:
        print("No issues found.")
        return

    for finding in findings:
        print(f"[{finding.severity}] {finding.rule_id}: {finding.message}")
        location = finding.location
        if location is not None:
            print(f"Line: {location.start_line}")
            print(f"Column: {location.start_column}")
            print(f"Matched: {location.matched_text}")
            if location.context is not None:
                print(f"Context: {location.context}")
        print()


def _print_json_findings(findings: list[ReviewFinding]) -> None:
    payload = _build_json_payload(findings)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


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
        if args.format == "json":
            _print_json_findings(findings)
        else:
            _print_text_findings(findings)
        return 0
    except (FileNotFoundError, ValueError, ValidationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
