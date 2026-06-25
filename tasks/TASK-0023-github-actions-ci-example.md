# TASK-0023: Add GitHub Actions CI Example

## Status

Planned

## Goal

Add a GitHub Actions CI example that demonstrates how to run the content review engine in an automated workflow.

After this task, users should be able to copy or adapt a workflow that runs:

```bash
content-review profile validate profiles/my-wechat.yaml
content-review batch articles --profile profiles/my-wechat.yaml --recursive --fail-on error
```

This task connects the existing CLI capabilities into a practical CI-based content review workflow.

## Background

The project currently supports:

* Markdown reading
* YAML `ReviewProfile` loading
* `forbidden_terms` rule
* `absolute_claims` rule
* `allow_terms`
* Inline suppression comments
* Single-file review
* Batch review
* Text / JSON / Markdown output
* CLI quality gate via `--fail-on`
* CI-friendly exit codes
* `content-review profile validate`
* `content-review profile init`
* `content-review profile list`
* Built-in example profiles

The CLI now has enough functionality to be used in CI:

```bash
content-review profile validate profiles/examples/wechat-strict.yaml
content-review batch articles --profile profiles/examples/wechat-strict.yaml --recursive --fail-on error
```

However, the repository does not yet provide a clear GitHub Actions example for users who want to integrate content review into pull requests or publishing workflows.

This task adds a documented CI example without changing review behavior.

## Scope

This task includes:

1. Add a GitHub Actions example workflow.
2. Demonstrate profile validation in CI.
3. Demonstrate batch content review in CI.
4. Demonstrate `--fail-on` quality gate behavior.
5. Add a sample articles directory if needed.
6. Add a sample CI profile if needed.
7. Document how exit codes affect CI pass/fail behavior.
8. Document how users should customize paths and profiles.
9. Add tests or validation checks for the workflow file if practical.
10. Update `docs/CLI.md`.
11. Update `docs/PROFILES.md`.
12. Add or update `docs/CI.md`.
13. Update `PROJECT_STATE.md`.
14. Update `CHANGELOG.md`.

## Non-goals

This task must not implement:

* New review rules
* LLM-based review
* Auto-fix behavior
* GitHub PR comments
* Review annotations
* SARIF output
* GitHub Checks API integration
* Marketplace GitHub Action
* Remote profile loading
* Secret management
* API server
* MCP server
* Frontend UI
* Database persistence
* Publishing integration

## Recommended File Layout

Add a documentation workflow example.

Recommended location:

```text
.github/workflows/content-review.example.yml
```

Alternative acceptable location:

```text
docs/examples/github-actions/content-review.yml
```

Recommended approach:

* Prefer adding the example under `docs/examples/github-actions/content-review.yml` if the project does not want CI to run automatically in this repository.
* Prefer `.github/workflows/content-review.example.yml` if you want it visible near GitHub Actions configuration but not active.
* Do not add an active workflow that may unexpectedly run on the repository unless the project already uses GitHub Actions and this is intentional.

For this task, the safer default is:

```text
docs/examples/github-actions/content-review.yml
```

## Example Workflow

Add an example workflow similar to:

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

If the repository does not have an `articles/` directory, the documentation should explain that users need to change this path.

## CI Workflow Behavior

The example should explain:

```text
profile validate exit code 0 = profile is valid
profile validate exit code 2 = profile is invalid or cannot be loaded

batch exit code 0 = review completed and quality gate passed
batch exit code 1 = review completed but findings met the --fail-on threshold
batch exit code 2 = command or configuration error
```

In GitHub Actions:

* Exit code `0` passes the step.
* Exit code `1` fails the step because the quality gate failed.
* Exit code `2` fails the step because the command or configuration is invalid.

## Example Profile

The workflow may use the built-in example profile:

```text
profiles/examples/wechat-strict.yaml
```

This keeps the example simple and avoids creating another profile file.

The documentation should also show how to initialize a custom profile:

```bash
content-review profile init --template wechat-strict --output profiles/my-wechat.yaml
content-review profile validate profiles/my-wechat.yaml
```

Then update the workflow:

```yaml
- name: Validate review profile
  run: uv run content-review profile validate profiles/my-wechat.yaml

- name: Run batch content review
  run: uv run content-review batch articles --profile profiles/my-wechat.yaml --recursive --fail-on error
```

## Example Articles Directory

Do not create a large sample article set.

If an example content directory is needed, add a minimal sample such as:

```text
examples/articles/demo.md
```

However, this task does not require adding sample articles if existing fixtures or examples already cover CLI usage.

The GitHub Actions workflow should be presented as a user-facing example, not necessarily as an active test workflow.

## Documentation Design

Add a new documentation file if it does not exist:

```text
docs/CI.md
```

Suggested structure:

```markdown
# CI Integration

## Why Run Content Review in CI?

## GitHub Actions Example

## Validate Profile Before Review

## Run Batch Review

## Use --fail-on as a Quality Gate

## Recommended Workflow

## Customizing Paths

## Customizing Profiles

## Exit Codes

## Notes and Limitations
```

## docs/CI.md Requirements

The CI documentation should include:

1. A complete GitHub Actions workflow example.
2. Explanation of profile validation.
3. Explanation of batch review.
4. Explanation of `--fail-on`.
5. Explanation of exit codes.
6. Explanation of how to customize article paths.
7. Explanation of how to customize profile paths.
8. Explanation that example profiles are starting points.
9. A reminder that deterministic rules do not guarantee legal, regulatory, advertising, medical, or platform compliance.

Important wording:

```text
This workflow is an example. It does not guarantee compliance with any platform policy, legal requirement, advertising regulation, medical content standard, or publishing rule.
```

## docs/CLI.md Updates

Update `docs/CLI.md` with a short CI example:

```bash
uv run content-review profile validate profiles/examples/wechat-strict.yaml
uv run content-review batch articles --profile profiles/examples/wechat-strict.yaml --recursive --fail-on error
```

Also add a reference to:

```text
docs/CI.md
```

## docs/PROFILES.md Updates

Update `docs/PROFILES.md` to mention that profiles can be used in CI:

```bash
content-review profile validate profiles/my-wechat.yaml
content-review batch articles --profile profiles/my-wechat.yaml --recursive --fail-on error
```

Explain that teams should validate profiles before running content review in automated workflows.

## Workflow File Validation

If practical, add a lightweight test that ensures the workflow example exists and contains expected commands.

Suggested test file:

```text
tests/test_docs_examples.py
```

Suggested tests:

```text
GitHub Actions example file exists
workflow example contains profile validate command
workflow example contains batch command
workflow example contains --fail-on error
workflow example references a valid example profile path
```

Do not add a dependency-heavy YAML workflow validator unless the project already has one.

A simple text-based test is sufficient.

## Testing Requirements

Add tests for documentation examples if practical.

Suggested cases:

```text
CI documentation exists
CI documentation mentions profile validate
CI documentation mentions batch review
CI documentation mentions --fail-on
CI documentation mentions exit code 0
CI documentation mentions exit code 1
CI documentation mentions exit code 2
GitHub Actions example exists
GitHub Actions example uses uv run content-review profile validate
GitHub Actions example uses uv run content-review batch
GitHub Actions example uses --fail-on error
```

If the current project avoids testing docs, keep this minimal.

Do not weaken existing tests.

## Backward Compatibility

This task must preserve existing behavior for:

* `content-review profile list`
* `content-review profile init`
* `content-review profile validate`
* `content-review review`
* `content-review batch`
* `forbidden_terms`
* `absolute_claims`
* `allow_terms`
* Inline suppression
* `--fail-on`
* Existing example profiles
* Existing output formats

No existing CLI command should be renamed.

No existing profile format should be removed.

No existing tests should be weakened.

## Acceptance Criteria

This task is complete when:

1. A GitHub Actions CI example exists.
2. The example validates a review profile.
3. The example runs batch review.
4. The example uses `--fail-on`.
5. The example uses existing CLI commands.
6. The example does not require new review behavior.
7. `docs/CI.md` is added or updated.
8. `docs/CLI.md` is updated with CI usage.
9. `docs/PROFILES.md` is updated with CI profile workflow notes.
10. Exit code behavior is documented.
11. Customization of article path is documented.
12. Customization of profile path is documented.
13. Compliance limitations are documented.
14. Tests or lightweight checks are added for the CI example if practical.
15. `PROJECT_STATE.md` is updated.
16. `CHANGELOG.md` is updated.
17. Existing tests still pass.
18. `uv run pytest` passes.

## Suggested Test Command

```bash
uv run pytest
```

## Implementation Notes

Recommended implementation order:

1. Inspect existing documentation structure.
2. Decide whether the workflow example should live in `docs/examples/github-actions/` or `.github/workflows/`.
3. Add the GitHub Actions workflow example.
4. Add `docs/CI.md`.
5. Update `docs/CLI.md`.
6. Update `docs/PROFILES.md`.
7. Add lightweight documentation/example tests if consistent with the project.
8. Update `PROJECT_STATE.md`.
9. Update `CHANGELOG.md`.
10. Run the full test suite.

