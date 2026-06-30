# CI Integration

For the complete local setup flow before CI, see
[docs/QUICKSTART.md](./QUICKSTART.md).

For explicit real-provider manual verification guidance, see
[docs/LLM_PROVIDER_USAGE.md](./LLM_PROVIDER_USAGE.md).

For committed example CI-style review artifacts that show deterministic output,
LLM sidecars, advisory Markdown reports, report indexes, manual review
checklists, and batch partial failure handling, see
[`examples/llm_review_artifacts/README.md`](../examples/llm_review_artifacts/README.md).

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

If you also want a compact artifact that explains deterministic output, LLM
sidecars, and quality-gate interpretation boundaries, write a separate report
index:

```bash
uv run content-review batch articles --profile profiles/examples/wechat-strict.yaml --recursive --fail-on error --format markdown --output artifacts/content-review-report.md --report-index artifacts/content-review-index.md
```

The example uses `articles` as a placeholder content directory. Change it to
match your repository layout, for example:

```bash
uv run content-review batch content/posts --profile profiles/my-wechat.yaml --recursive --fail-on error
uv run content-review batch docs/articles --profile profiles/examples/general-basic.yaml --recursive --fail-on error
```

If you also want one explicit opt-in combined artifact for later manual
inspection, write it separately:

```bash
uv run content-review review article.md --profile profiles/my-wechat.yaml --combined-output artifacts/review-combined.md
uv run content-review batch articles --profile profiles/my-wechat.yaml --recursive --combined-output artifacts/batch-combined.json --combined-output-format json
```

CI boundary for combined artifacts:

- `--combined-output` does not auto-enable LLM review
- combined output is optional documentation or inspection output, not the
  canonical gating output
- combined output may coexist with `--output`, `--llm-output`, and
  `--report-index`
- when LLM is disabled, combined output records `not_run` status instead of
  generating LLM findings
- when LLM fails, combined output may still be written with structured error
  metadata, but deterministic gating behavior stays unchanged

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
Markdown report through `--llm-report`, or a hybrid navigation index through
`--report-index`. The same boundary applies to
LLM provider config such as `--llm-config`, `--llm-provider`, `--llm-model`, or
`--llm-api-key-env`, or `--llm-timeout-seconds`,
`--llm-retry-attempts`, `--llm-retry-backoff-seconds`, or
`--llm-min-request-interval-seconds`: they do not affect
deterministic quality-gate evaluation. `pydanticai` now performs secret
preflight and a real runtime call, but its findings and provider failures
still do not change deterministic gate semantics. A missing or empty
`--llm-api-key-env` for `pydanticai` is still a command error with exit code
`2`, not a deterministic quality-gate failure. Runtime-side `pydanticai`
timeout, auth, network, rate-limit, model, retry-exhausted, and unknown
failures are serialized into LLM sidecars without changing the deterministic
exit code.
Only deterministic findings contribute to exit code `1`.

When LLM output artifacts are written in CI, treat every LLM finding as
`source = llm`, `advisory = yes`, and `quality gate participation = no`.
Advisory LLM severities such as `critical` or `error` remain display-only and
do not change deterministic gate semantics.
The same rule applies to combined output: combined artifacts can display
advisory findings, partial failures, and structured LLM errors, but only
deterministic findings can trigger exit code `1`.
In other words, only deterministic findings can trigger exit code `1`.
The same rule applies to the LLM Markdown `Manual Review Checklist` and the
batch `LLM Execution Review Checklist`: their default `needs_review`,
`pending`, `needs_rerun`, and `rerun_llm_review` values are presentation-only
workflow hints and do not change exit code `0`, `1`, or `2`.

CI boundary for providers:

- default CI should not run real `pydanticai` provider calls
- default CI should not require a real API key
- use deterministic review for gating
- if CI needs LLM-sidecar wiring coverage, use `--llm-provider mock`
- if CI needs reusable LLM-sidecar wiring coverage, it can also use
  `--llm-config examples/llm/mock/llm-provider.yml`
- if CI writes `--report-index`, treat it as a human-readable artifact only
  and keep gating decisions on deterministic review
- if CI needs non-review provider wiring checks, it can use
  `content-review llm-check --llm-config examples/llm/mock/llm-provider.yml`
- if you parse retry flags in CI, keep using `mock`; do not depend on real
  provider retries or real network failures
- if you parse `--llm-min-request-interval-seconds` in CI, keep using `mock`;
  do not depend on real provider pacing or real clocks
- do not store real API keys in `--llm-config` files; use only `api_key_env`
- do not run `content-review llm-check --runtime` against real providers in
  the default CI workflow
- manual `pydanticai` verification belongs in a local developer workflow, not
  in the default workflow example
- if you need a committed reference for artifact layout or manual reviewer
  expectations, inspect `examples/llm_review_artifacts/` rather than treating
  generated Markdown artifacts as schema definitions

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
