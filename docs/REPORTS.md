# Reports

## Purpose

This project currently supports one report format:

- Markdown

The report renderer is a thin formatter over existing review output.
It does not run rules, read input files, or write files.

## Markdown Report

The Markdown report is produced from existing review findings and includes:

- Document path
- Profile path or profile name
- Finding count
- One section per finding

Each finding section can include:

- Rule ID
- Severity
- Message
- Line
- Column
- Matched text
- Context snippet
- Suggestion, when available

## CLI Usage

```bash
content-review review article.md --profile profiles/wechat.yaml --format markdown
content-review review article.md --profile profiles/wechat.yaml --format markdown --output review-report.md
```

When `--output` is provided, the CLI writes the rendered report to the file and returns exit code `2` if the write fails.

For the committed example files, the same flow is:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output examples/review-report.md
```
