# TASK-0025: Add Quickstart Documentation

## Status

Planned

## Goal

Add a concise but complete Quickstart document that helps new users run the content review engine from zero to a working review workflow.

After this task, users should be able to follow one document and complete the core workflow:

```text
install / sync project
  ↓
list profile templates
  ↓
initialize a profile
  ↓
validate the profile
  ↓
review a single Markdown file
  ↓
batch review a directory
  ↓
generate a Markdown report
  ↓
understand CI usage
```

This task improves onboarding and documentation quality without changing runtime behavior.

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
* Markdown report output
* CLI quality gate via `--fail-on`
* CI-friendly exit codes
* `content-review profile list`
* `content-review profile init`
* `content-review profile validate`
* Built-in example profiles
* GitHub Actions CI example

The project now has enough features to be useful, but new users still need to read multiple documents to understand the full path.

This task adds a dedicated quickstart document that ties the existing capabilities together.

## Scope

This task includes:

1. Add `docs/QUICKSTART.md`.
2. Explain the minimal installation / setup workflow.
3. Show how to list available profile templates.
4. Show how to initialize a profile from a template.
5. Show how to validate a profile.
6. Show how to create or use a sample Markdown article.
7. Show how to run single-file review.
8. Show how to run batch review.
9. Show how to use `--fail-on` as a quality gate.
10. Show how to generate a Markdown report with `--format markdown --output`.
11. Explain basic exit code behavior.
12. Explain how to use inline suppression.
13. Explain how to customize `terms`, `allow_terms`, and severity.
14. Link to detailed docs such as `docs/CLI.md`, `docs/PROFILES.md`, and `docs/CI.md`.
15. Add lightweight tests to ensure the quickstart exists and includes key commands.
16. Update `README.md` if the repository has one.
17. Update `PROJECT_STATE.md`.
18. Update `CHANGELOG.md`.

## Non-goals

This task must not implement:

* New review rules
* LLM-based review
* Auto-fix behavior
* New CLI commands
* New output formats
* GitHub PR comments
* GitHub annotations
* SARIF output
* HTML report output
* PDF report output
* API server
* MCP server
* Frontend UI
* Database persistence
* Publishing integration

## Recommended File

Add:

```text
docs/QUICKSTART.md
```

If the repository has a root `README.md`, add a short link to the new quickstart:

```markdown
## Quickstart

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for a complete first-run workflow.
```

If the repository does not have a `README.md`, do not create one unless this project already expects it.

## Quickstart Audience

The quickstart should target users who want to run the tool, not contributors who want to understand every internal model.

The document should be practical and command-driven.

It should answer:

```text
How do I create a profile?
How do I validate it?
How do I review one Markdown file?
How do I review a folder?
How do I fail CI when serious findings exist?
How do I get a readable Markdown report?
How do I suppress intentional findings?
Where do I read more?
```

## Suggested docs/QUICKSTART.md Structure

Use this structure:

```markdown
# Quickstart

## Prerequisites

## 1. Install Dependencies

## 2. List Available Profile Templates

## 3. Create a Review Profile

## 4. Validate the Profile

## 5. Create a Sample Markdown Article

## 6. Review One Markdown File

## 7. Review a Directory

## 8. Use a Quality Gate

## 9. Generate a Markdown Report

## 10. Suppress an Intentional Finding

## 11. Customize the Profile

## 12. Use in CI

## Exit Codes

## Next Steps

## Notes and Limitations
```

## Prerequisites Section

The quickstart should mention:

```text
Python
uv
A Markdown file or directory of Markdown files
```

Use the existing project workflow.

Suggested commands:

```bash
uv sync
```

If the project currently uses a different install command, follow the existing repository documentation.

Do not introduce a new package manager.

## Step 1: Install Dependencies

Suggested content:

```bash
uv sync
```

Then verify the CLI:

```bash
uv run content-review --help
```

Expected explanation:

* `uv sync` installs project dependencies.
* `uv run content-review --help` verifies that the CLI is available.

## Step 2: List Available Profile Templates

Show:

```bash
uv run content-review profile list
```

Expected output should mention:

```text
general-basic
wechat-basic
wechat-strict
```

Also show JSON output briefly:

```bash
uv run content-review profile list --format json
```

## Step 3: Create a Review Profile

Show:

```bash
mkdir -p profiles
uv run content-review profile init --template wechat-basic --output profiles/my-wechat.yaml
```

Explain:

* `wechat-basic` is a starter profile.
* The generated file is normal YAML.
* Users should edit it for their own use case.

Also show strict mode option:

```bash
uv run content-review profile init --template wechat-strict --output profiles/my-wechat-strict.yaml
```

## Step 4: Validate the Profile

Show:

```bash
uv run content-review profile validate profiles/my-wechat.yaml
```

Mention JSON validation output:

```bash
uv run content-review profile validate profiles/my-wechat.yaml --format json
```

Explain:

* Valid profile returns exit code `0`.
* Invalid profile returns exit code `2`.

## Step 5: Create a Sample Markdown Article

Add a minimal sample that users can copy.

Suggested example:

```bash
mkdir -p articles
cat > articles/demo.md <<'EOF'
# Demo Article

这是一款全网最强的内容审计工具。

这里包含一个示例违规词。
EOF
```

Use terms that are likely present in example profiles, such as:

```text
全网最强
违规词
```

If the example profiles use different terms, align the quickstart with actual profile content.

## Step 6: Review One Markdown File

Show:

```bash
uv run content-review review articles/demo.md --profile profiles/my-wechat.yaml
```

Also show JSON:

```bash
uv run content-review review articles/demo.md --profile profiles/my-wechat.yaml --format json
```

Also show Markdown:

```bash
uv run content-review review articles/demo.md --profile profiles/my-wechat.yaml --format markdown
```

Explain that findings may include:

```text
forbidden_terms
absolute_claims
```

## Step 7: Review a Directory

Show:

```bash
uv run content-review batch articles --profile profiles/my-wechat.yaml --recursive
```

Show JSON output:

```bash
uv run content-review batch articles --profile profiles/my-wechat.yaml --recursive --format json
```

Show Markdown output:

```bash
uv run content-review batch articles --profile profiles/my-wechat.yaml --recursive --format markdown
```

## Step 8: Use a Quality Gate

Show:

```bash
uv run content-review batch articles --profile profiles/my-wechat.yaml --recursive --fail-on error
```

Explain:

* `--fail-on error` returns exit code `1` if any `error` or `critical` finding exists.
* This is useful for CI and publishing checks.
* `warning` findings do not fail when `--fail-on error` is used.

Also show stricter behavior:

```bash
uv run content-review batch articles --profile profiles/my-wechat.yaml --recursive --fail-on warning
```

## Step 9: Generate a Markdown Report

Show single-file report:

```bash
uv run content-review review articles/demo.md \
  --profile profiles/my-wechat.yaml \
  --format markdown \
  --output review-report.md
```

Show batch report:

```bash
uv run content-review batch articles \
  --profile profiles/my-wechat.yaml \
  --recursive \
  --fail-on error \
  --format markdown \
  --output content-review-report.md
```

Explain:

* Markdown reports include summary, severity counts, rule counts, findings, and detailed findings.
* Batch reports include per-file sections.
* When `--fail-on` fails, the report should still be written when possible.

## Step 10: Suppress an Intentional Finding

Show inline suppression:

```markdown
这是一款全网最强的工具。 <!-- content-review-disable-line absolute_claims -->
```

Show next-line suppression:

```markdown
<!-- content-review-disable-next-line forbidden_terms -->
这里故意讨论“违规词”这个表达。
```

Explain:

* Suppression is rule-specific.
* Suppressed findings do not appear in output.
* Suppressed findings do not count toward summaries.
* Suppressed findings do not trigger `--fail-on`.

## Step 11: Customize the Profile

Show a small YAML snippet.

Example:

```yaml
name: my-wechat
target_platform: wechat

rules:
  - id: forbidden_terms
    enabled: true
    severity: error
    terms:
      - 违规词
      - 敏感词
    allow_terms: []

  - id: absolute_claims
    enabled: true
    severity: warning
    terms:
      - 全网最强
      - 绝对安全
      - 永久有效
    allow_terms:
      - 唯一标识符
```

Explain:

* Add risky words under `terms`.
* Add intentional exceptions under `allow_terms`.
* Use severity values:

```text
info
warning
error
critical
```

## Step 12: Use in CI

Show minimal CI commands:

```bash
uv run content-review profile validate profiles/my-wechat.yaml
uv run content-review batch articles --profile profiles/my-wechat.yaml --recursive --fail-on error
```

Reference:

```text
docs/CI.md
docs/examples/github-actions/content-review.yml
```

Do not duplicate the full GitHub Actions workflow unless the quickstart remains concise.

## Exit Codes Section

Document:

```text
0 = command completed successfully, or quality gate passed
1 = review completed but quality gate failed
2 = command, input, profile, or configuration error
```

Clarify:

* `profile validate` uses `0` for valid and `2` for invalid.
* `review` and `batch` use `1` only for quality gate failures.
* CI systems usually treat non-zero exit codes as failure.

## Next Steps Section

Link to:

```text
docs/CLI.md
docs/PROFILES.md
docs/CI.md
docs/REVIEW_RULES.md
docs/RULES.md
```

Explain what each doc is for.

Suggested mapping:

```text
docs/CLI.md = full CLI reference
docs/PROFILES.md = profile templates and customization
docs/CI.md = GitHub Actions and CI integration
docs/REVIEW_RULES.md = review rule behavior
docs/RULES.md = supported rules and configuration examples
```

## Notes and Limitations

The quickstart must include a clear limitation notice:

```text
This tool uses deterministic review rules. It does not guarantee compliance with any platform policy, legal requirement, advertising regulation, medical content standard, or publishing rule.
```

Also mention:

```text
Example profiles are starting points. Teams should customize terms, severities, and allow_terms for their own use cases.
```

## Testing Requirements

Add lightweight documentation tests if the project already tests docs.

Suggested test file:

```text
tests/test_quickstart_docs.py
```

Suggested tests:

```text
docs/QUICKSTART.md exists
quickstart mentions content-review profile list
quickstart mentions content-review profile init
quickstart mentions content-review profile validate
quickstart mentions content-review review
quickstart mentions content-review batch
quickstart mentions --fail-on error
quickstart mentions --format markdown
quickstart mentions --output
quickstart mentions inline suppression syntax
quickstart mentions exit code 0
quickstart mentions exit code 1
quickstart mentions exit code 2
quickstart mentions compliance limitations
```

Optional tests:

```text
README.md links to docs/QUICKSTART.md if README.md exists
quickstart references docs/CLI.md
quickstart references docs/PROFILES.md
quickstart references docs/CI.md
```

Do not add heavy integration tests in this task.

Do not run commands from the quickstart as part of tests unless the project already has a stable docs command testing pattern.

## Documentation Updates

Update `docs/CLI.md` to reference `docs/QUICKSTART.md`.

Suggested addition:

```markdown
For a complete first-run workflow, see [Quickstart](QUICKSTART.md).
```

Update `docs/PROFILES.md` to reference the quickstart where appropriate.

Update `docs/CI.md` to reference the quickstart where appropriate.

Update `README.md` if it exists.

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
* Markdown reports
* JSON output
* Text output
* Existing example profiles
* Existing CI docs and examples

No existing CLI command should be renamed.

No existing profile format should be removed.

No JSON schema should be changed.

No existing tests should be weakened.

## Acceptance Criteria

This task is complete when:

1. `docs/QUICKSTART.md` exists.
2. The quickstart explains installation or dependency setup.
3. The quickstart shows `content-review profile list`.
4. The quickstart shows `content-review profile init`.
5. The quickstart shows `content-review profile validate`.
6. The quickstart shows single-file `content-review review`.
7. The quickstart shows `content-review batch`.
8. The quickstart shows `--fail-on`.
9. The quickstart shows Markdown report generation.
10. The quickstart explains inline suppression.
11. The quickstart explains profile customization.
12. The quickstart documents exit code `0`.
13. The quickstart documents exit code `1`.
14. The quickstart documents exit code `2`.
15. The quickstart links to detailed docs.
16. The quickstart includes compliance limitation wording.
17. `docs/CLI.md` links to the quickstart.
18. `docs/PROFILES.md` or `docs/CI.md` references the quickstart where useful.
19. `README.md` links to the quickstart if a README exists.
20. Lightweight docs tests are added if consistent with existing project style.
21. `PROJECT_STATE.md` is updated.
22. `CHANGELOG.md` is updated.
23. Existing tests still pass.
24. `uv run pytest` passes.

## Suggested Test Command

```bash
uv run pytest
```

## Implementation Notes

Recommended implementation order:

1. Inspect existing documentation structure.
2. Check whether `README.md` exists.
3. Add `docs/QUICKSTART.md`.
4. Add concise command-driven workflow.
5. Align example terms with existing example profiles.
6. Add links from `docs/CLI.md`.
7. Add links from `docs/PROFILES.md` and/or `docs/CI.md`.
8. Update `README.md` if present.
9. Add lightweight documentation tests.
10. Update `PROJECT_STATE.md`.
11. Update `CHANGELOG.md`.
12. Run the full test suite.

