# Reports

## Purpose

This project currently supports one report format:

- Markdown

The report renderer is a thin formatter over the canonical `ReviewResult`.
It does not run rules, read input files, or write files.

The batch report renderer follows the same boundary and formats a canonical `BatchReviewResult`.

## Markdown Report

The Markdown report is produced from an existing `ReviewResult` and includes:

- Document path, when available
- Profile path or profile name, when available
- Finding count from `ReviewSummary`
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

## Batch Markdown Report

The batch Markdown report is produced from an existing `BatchReviewResult` and includes:

- File discovery summary
- Review count summary
- Files with findings count
- One section per reviewed file

Each file section can include:

- File path
- Finding count
- Per-finding rule details
- Location metadata when available
- A `No issues found.` block for clean files

## CLI Usage

```bash
content-review review article.md --profile profiles/wechat.yaml --format markdown
content-review review article.md --profile profiles/wechat.yaml --format markdown --output review-report.md
content-review batch docs/articles --profile profiles/wechat.yaml --recursive --format markdown
content-review batch docs/articles --profile profiles/wechat.yaml --recursive --format markdown --output batch-report.md
```

When `--output` is provided, the CLI writes the rendered report to the file and returns exit code `2` if the write fails.

For the committed example files, the same flow is:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output examples/review-report.md
```
