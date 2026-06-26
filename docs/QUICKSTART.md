# Quickstart

This quickstart walks through the first usable workflow for this repository:

```text
uv sync
  ↓
content-review profile list
  ↓
content-review profile init
  ↓
content-review profile validate
  ↓
content-review review
  ↓
content-review batch
  ↓
--fail-on and Markdown report output
```

## Prerequisites

- Python 3.11 or newer
- `uv`
- A Markdown file or a directory of Markdown files

This repository already includes sample Markdown files and built-in example
profiles, so you can follow the commands below directly from the project root.

## 1. Install Dependencies

Install the project and its dependencies:

```bash
uv sync
```

Verify that the CLI is available:

```bash
uv run content-review --help
```

## 2. List Available Profile Templates

Inspect the built-in starter and real-world templates:

```bash
uv run content-review profile list
```

Expected template names:

```text
general-basic
general-publishing
health-content
marketing-copy
technical-blog
wechat-basic
wechat-article
wechat-strict
```

JSON output is also available:

```bash
uv run content-review profile list --format json
```

## 3. Create a Review Profile

Initialize a local editable profile from a built-in template:

```bash
mkdir -p profiles
uv run content-review profile init --template wechat-basic --output profiles/my-wechat.yaml
```

If you want a stricter quality gate for CI, initialize the strict variant:

```bash
uv run content-review profile init --template wechat-strict --output profiles/my-wechat-strict.yaml
```

If you want to start from a practical publishing-oriented template instead of a
minimal starter, initialize one of the real-world templates such as
`general-publishing`, `marketing-copy`, `technical-blog`, `health-content`, or
`wechat-article`.

The generated file is normal YAML. After initialization, edit it like any other
local config file.

## 4. Validate the Profile

Validate the generated profile before reviewing content:

```bash
uv run content-review profile validate profiles/my-wechat.yaml
uv run content-review profile validate profiles/my-wechat.yaml --format json
```

This checks that the YAML is readable, the profile shape is valid, and rule IDs
are recognized.

## 5. Review One Markdown File

Use the sample article that already exists in the repository:

```bash
uv run content-review review examples/article.md --profile profiles/my-wechat.yaml
```

You can also review a specific fixture that is known to trigger the
`absolute_claims` rule:

```bash
uv run content-review review tests/fixtures/markdown/absolute_claims_article.md --profile profiles/my-wechat.yaml
```

## 6. Review A Directory

Run the same profile against a directory of Markdown files:

```bash
uv run content-review batch examples/batch/articles --profile profiles/my-wechat.yaml --recursive
```

You can narrow discovery with `--pattern` when needed:

```bash
uv run content-review batch examples/batch/articles --profile profiles/my-wechat.yaml --recursive --pattern "*.md"
```

## 7. Use A Quality Gate With `--fail-on`

Use `--fail-on` when findings at or above a severity should fail automation:

```bash
uv run content-review review examples/article.md --profile profiles/my-wechat.yaml --fail-on error
uv run content-review batch examples/batch/articles --profile profiles/my-wechat-strict.yaml --recursive --fail-on error
```

Severity order is:

```text
info < warning < error < critical
```

If `--fail-on` is omitted, `review` and `batch` still complete successfully even
when findings are present.

## 8. Generate A Markdown Report

Write a human-readable Markdown report to a file:

```bash
mkdir -p artifacts
uv run content-review review tests/fixtures/markdown/absolute_claims_article.md --profile profiles/my-wechat.yaml --format markdown --output artifacts/review-report.md --fail-on warning
```

Batch report example:

```bash
uv run content-review batch examples/batch/articles --profile profiles/my-wechat-strict.yaml --recursive --fail-on error --format markdown --output artifacts/batch-report.md
```

When the quality gate fails with exit code `1`, the Markdown report is still
written first if the output path is writable.

## 9. Suppress An Intentional Finding

Inline suppression works with exact rule IDs and affects only the current line
or next line.

Suppress the current line:

```markdown
这是一款全网最强的工具。 <!-- content-review-disable-line absolute_claims -->
```

Suppress the next line:

```markdown
<!-- content-review-disable-next-line forbidden_terms -->
这里包含违规词，但这是一个有意保留的测试样例。
```

Suppressed findings do not appear in text, JSON, or Markdown output, and they
do not count toward summaries or `--fail-on`.

## 10. Customize The Profile

The example templates are only starting points. Update terms, allowlists,
severity, and regex patterns to match your workflow.

Example customization aligned with the built-in WeChat profiles:

```yaml
rules:
  - id: forbidden_terms
    enabled: true
    severity: error
    terms:
      - 违规词
      - 敏感词
      - 禁用词
    allow_terms: []

  - id: absolute_claims
    enabled: true
    severity: warning
    terms:
      - 全网最强
      - 行业第一
      - 唯一选择
    allow_terms:
      - 唯一标识符
```

Typical edits:

- Add or remove entries in `terms`.
- Use `allow_terms` for exact literal exceptions.
- Raise `absolute_claims.severity` from `warning` to `error` for stricter CI.
- Adjust title and paragraph length limits for your publishing channel.

Validate again after changes:

```bash
uv run content-review profile validate profiles/my-wechat.yaml
```

## 11. Use In CI

A practical CI flow is:

```bash
uv run content-review profile validate profiles/my-wechat-strict.yaml
uv run content-review batch articles --profile profiles/my-wechat-strict.yaml --recursive --fail-on error
```

For a copyable GitHub Actions example, see
[CI Integration](./CI.md) and
`docs/examples/github-actions/content-review.yml`.

## Exit Codes

`review` and `batch`:

- `0`: command completed and the quality gate passed, or no quality gate was configured.
- `1`: command completed, but at least one finding met the `--fail-on` threshold.
- `2`: command usage, input, profile, or filesystem error.

`profile validate`:

- `0`: profile is valid.
- `2`: profile is invalid, missing, unreadable, or cannot be parsed.

## Next Steps

- Read [CLI Reference](./CLI.md) for all command options and output formats.
- Read [Rule System](./RULES.md), the canonical rule reference, for supported
  rule IDs, severity ordering, suppression behavior, counts, and quality
  gates.
- Read [Profiles](./PROFILES.md) for profile structure, template differences,
  and customization guidance.
- Read [CI Integration](./CI.md) for automation and GitHub Actions examples.

## Notes And Limitations

The current engine runs deterministic rules only.
Built-in example profiles and deterministic rules help catch configured wording
and structural issues, but they do not guarantee legal, advertising, medical,
regulatory, or platform compliance.
