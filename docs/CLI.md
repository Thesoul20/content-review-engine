# CLI

## Current Command

```bash
content-review review <markdown_file> --profile <profile_file> [--format text|json]
```

The CLI is a thin adapter over the core review pipeline.
It reads Markdown, loads a YAML profile, runs deterministic rules, and prints the result.

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

## Notes

- The CLI does not implement review logic itself.
- The CLI does not add rewriting, diff tracking, batch review, watch mode, MCP, API, or GUI support.
