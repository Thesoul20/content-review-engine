# CLI

## Current Command

```bash
content-review review <markdown_file> --profile <profile_file> [--format text|json|markdown] [--output <file>]
```

The CLI is a thin adapter over the core review pipeline.
It reads Markdown, loads a YAML profile, runs deterministic rules, and prints or exports the result.

## Output Formats

### Text

Text output shows a summary plus one block per finding.
When a finding has source location metadata, the CLI prints:

- `Line`
- `Column`
- `Matched`
- `Context`

Example:

```text
Review completed.

Findings: 1

[warning] forbidden_terms: 发现风险词：绝对
Line: 3
Column: 5
Matched: 绝对
Context: 这个方法绝对有效。
```

### JSON

JSON output is intended for automation and includes the finding list plus a summary object.
The finding entries include the nested `location` object when available.

Example shape:

```json
{
  "findings": [
    {
      "rule_id": "forbidden_terms",
      "severity": "warning",
      "message": "发现风险词：绝对",
      "matched_term": "绝对",
      "matched_text": "绝对",
      "location": {
        "start_line": 3,
        "start_column": 5,
        "end_line": 3,
        "end_column": 7,
        "start_offset": 12,
        "end_offset": 14,
        "matched_text": "绝对",
        "context": "这个方法绝对有效。"
      }
    }
  ],
  "summary": {
    "finding_count": 1
  }
}
```

### Markdown

Markdown output is intended for human-readable review reports.
It uses the existing review findings and renders a report with a summary section and per-finding details.

When `--output` is provided, the CLI writes the rendered output to the given file instead of printing it to stdout.
If the write fails, the command exits with code `2`.

Example shape:

```markdown
# Content Review Report

## Summary

- Document: `article.md`
- Profile: `profiles/wechat.yaml`
- Findings: 1

## Findings

### forbidden_terms

- Severity: warning
- Message: 发现风险词：保证赚钱
- Line: 3
- Column: 5
- Matched: `保证赚钱`
- Context: 这篇文章承诺保证赚钱。
```

## Notes

- The CLI does not implement review logic itself.
- The CLI does not add rewriting, diff tracking, batch review, watch mode, MCP, API, GUI, or report generation logic of its own.

## Example Files

You can run the CLI against the committed example files:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format text
uv run content-review review examples/article.md --profile examples/profile.yml --format json
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
```

For a saved Markdown report:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output examples/review-report.md
```
