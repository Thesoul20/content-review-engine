# Testing

## Run Tests

Run the current validation suite with:

```bash
uv run pytest
```

## Manual CLI Smoke Validation

After `uv sync`, validate the packaged console script directly:

```bash
uv run content-review --help
```

Then run the committed example file through the same entrypoint:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format text
uv run content-review review examples/article.md --profile examples/profile.yml --format json
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output /tmp/content-review-example-report.md
```

For the opt-in Markdown structure rule:

```bash
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format text
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format json
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format markdown
uv run content-review review examples/markdown-structure-article.md --profile examples/markdown-structure-profile.yml --format markdown --output /tmp/content-review-markdown-structure-report.md
```

## Fixture Layout

Automated tests use committed fixtures under `tests/fixtures/`.

The current layout is:

```text
tests/fixtures/
  markdown/
  profiles/
  expected_reports/
```

Use `tests/fixtures/markdown/` for Markdown inputs that should be reused across tests.
Use `tests/fixtures/profiles/` for YAML review profiles that should stay stable across test runs.
Use `tests/fixtures/expected_reports/` only when a report output is stable enough to compare directly.

The current Markdown structure fixtures cover:

- `markdown_structure_missing_h1.md`
- `markdown_structure_multiple_h1.md`
- `markdown_structure_heading_jumps.md`
- `markdown_structure_empty_headings.md`
- `markdown_structure_long_paragraph.md`
- `markdown_structure_code_block_headings.md`
- `markdown_structure_issues.md`

## Inline Strings Vs Fixtures

Keep small unit tests inline when the intent is clearer in code.

Use fixture files when a test becomes integration-like, needs multiple scenarios, or should mirror the manual CLI path more closely.

Current examples:

- Inline strings are still good for small location helpers and narrow model tests.
- Fixture files are better for CLI review runs, report rendering, and multiline Markdown scenarios.

## When To Add A Fixture

Add a fixture when:

1. The same Markdown or profile data is reused in more than one test.
2. The test setup becomes noisy with inline strings.
3. You want the test to read more like a real input file.
4. You need a stable expected report for comparison.

Do not add fixtures just to move simple unit-test data out of the test body.

## Fixtures Vs Examples

`tests/fixtures/` is for automated tests.

`examples/` is for manual local CLI usage.

The example files are intended to be run directly with the CLI and are not part of the automated fixture contract.

## Current Example Commands

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format text
uv run content-review review examples/article.md --profile examples/profile.yml --format json
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
```

To export a Markdown report file during manual checks:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output examples/review-report.md
```

## Notes

The current forbidden-terms rule scans the raw Markdown text, including fenced code blocks. The `markdown_with_code_block.md` fixture exists to preserve that current behavior for future test coverage.
