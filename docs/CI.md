# CI Integration

For the complete local setup flow before CI, see
[docs/QUICKSTART.md](./QUICKSTART.md).

For the rule-system reference behind `--fail-on`, suppression comments, and
severity ordering, see [docs/RULES.md](./RULES.md), the canonical rule
reference.

## Purpose

This document shows how to run `content-review` in CI without changing core
review behavior.

The repository includes a copyable GitHub Actions example at:

`docs/examples/github-actions/content-review.yml`

The example is documentation only. It is not an active workflow in this
repository.

## GitHub Actions Example

```yaml
name: Content Review

on:
  pull_request:
    paths:
      - "articles/**/*.md"
      - "profiles/**/*.yaml"
      - "profiles/**/*.yml"
  push:
    branches:
      - main
    paths:
      - "articles/**/*.md"
      - "profiles/**/*.yaml"
      - "profiles/**/*.yml"

jobs:
  content-review:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Install project
        run: uv sync

      - name: Validate review profile
        run: uv run content-review profile validate profiles/examples/wechat-strict.yaml

      - name: Run batch content review
        run: uv run content-review batch articles --profile profiles/examples/wechat-strict.yaml --recursive --fail-on error
```

## Validate Profile Before Review

Validate the profile first so CI fails early when the YAML file is invalid or
cannot be loaded:

```bash
uv run content-review profile validate profiles/examples/wechat-strict.yaml
```

If you initialize your own profile, update the path:

```bash
uv run content-review profile init --template wechat-strict --output profiles/my-wechat.yaml
uv run content-review profile validate profiles/my-wechat.yaml
```

## Run Batch Review

Use `batch` to review a directory of Markdown files in one CI step:

```bash
uv run content-review batch articles --profile profiles/examples/wechat-strict.yaml --recursive --fail-on error
```

To keep a human-readable CI artifact, write the Markdown report to a file:

```bash
uv run content-review batch articles --profile profiles/examples/wechat-strict.yaml --recursive --fail-on error --format markdown --output artifacts/content-review-report.md
```

When the quality gate fails with exit code `1`, the command still writes the
Markdown report first when the output path is writable.

The example uses `articles` as a placeholder content directory. Change it to
match your repository layout, for example:

```bash
uv run content-review batch content/posts --profile profiles/my-wechat.yaml --recursive --fail-on error
uv run content-review batch docs/articles --profile profiles/examples/general-basic.yaml --recursive --fail-on error
```

## Customize Paths

Two paths usually need customization:

- Profile path: replace `profiles/examples/wechat-strict.yaml` with your own
  file such as `profiles/my-wechat.yaml`.
- Articles path: replace `articles` with the directory that contains your
  Markdown content such as `content/posts` or `docs/articles`.

Workflow example:

```yaml
- name: Validate review profile
  run: uv run content-review profile validate profiles/my-wechat.yaml

- name: Run batch content review
  run: uv run content-review batch content/posts --profile profiles/my-wechat.yaml --recursive --fail-on error
```

## Exit Codes

`content-review profile validate`:

- `0`: profile is valid.
- `2`: profile is invalid, missing, unreadable, or cannot be parsed.

`content-review batch ... --fail-on error`:

- `0`: review completed and the quality gate passed.
- `1`: review completed, but at least one finding met the `--fail-on` threshold.
- `2`: command usage, input, profile, or filesystem error.

If you also enable the experimental LLM sidecar path, LLM finding content and
LLM sidecar failures still do not affect the deterministic quality-gate exit
code. The same rule applies if you also write an independent LLM sidecar
Markdown report through `--llm-markdown-output`. The same boundary applies to
LLM provider config such as `--llm-provider`, `--llm-model`, or
`--llm-api-key-env`: they do not affect deterministic quality-gate evaluation.
Only deterministic findings contribute to exit code `1`.

In GitHub Actions, exit code `0` passes the step. Exit code `1` or `2` fails
the step.
If you also use `--format markdown --output ...`, exit code `1` still means the
report should already be available as an artifact unless the file write itself
failed.

## Notes And Limitations

This workflow example helps automate deterministic review checks, but it does
not guarantee legal, advertising, medical, regulatory, or platform compliance.
It also does not add PR comments, annotations, SARIF output, Checks API
integration, or remote profile loading.
