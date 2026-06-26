# End-to-End Demo

This demo shows the current CLI workflow from Markdown input to structured
review output.

## Demo Layout

```text
examples/demo/
  README.md
  articles/
    technical-demo.md
    wechat-demo.md
  profiles/
    technical-demo.yaml
    wechat-demo.yaml
  reports/
    technical-demo-report.md
    wechat-demo-report.md
```

## Validate The Demo Profiles

```bash
uv run content-review profile validate examples/demo/profiles/wechat-demo.yaml
uv run content-review profile validate examples/demo/profiles/technical-demo.yaml
```

## Review One Markdown File

WeChat-oriented article demo:

```bash
uv run content-review review examples/demo/articles/wechat-demo.md --profile examples/demo/profiles/wechat-demo.yaml
```

Technical blog demo:

```bash
uv run content-review review examples/demo/articles/technical-demo.md --profile examples/demo/profiles/technical-demo.yaml
```

## Generate Markdown Reports

These commands reproduce the committed demo reports:

```bash
uv run content-review review examples/demo/articles/wechat-demo.md --profile examples/demo/profiles/wechat-demo.yaml --format markdown --output examples/demo/reports/wechat-demo-report.md --fail-on warning
uv run content-review review examples/demo/articles/technical-demo.md --profile examples/demo/profiles/technical-demo.yaml --format markdown --output examples/demo/reports/technical-demo-report.md --fail-on warning
```

The quality gate is expected to fail for both commands because the demo
articles intentionally include findings at `warning` or above. The CLI still
writes the Markdown report before returning exit code `1`.

## Generate JSON Output

```bash
uv run content-review review examples/demo/articles/wechat-demo.md --profile examples/demo/profiles/wechat-demo.yaml --format json
uv run content-review review examples/demo/articles/technical-demo.md --profile examples/demo/profiles/technical-demo.yaml --format json
```

## Run Batch Review

Use the directory-based `batch` command when you want the same profile to
review a set of matching demo files:

```bash
uv run content-review batch examples/demo/articles --profile examples/demo/profiles/wechat-demo.yaml --pattern "wechat-*.md" --fail-on warning
uv run content-review batch examples/demo/articles --profile examples/demo/profiles/technical-demo.yaml --pattern "technical-*.md" --fail-on warning --format markdown --output examples/demo/reports/technical-demo-batch-report.md
```

The second command demonstrates batch report output. It reviews the directory,
discovers files by pattern, and applies the same quality gate semantics as
single-file review.

## Inline Suppression

`examples/demo/articles/wechat-demo.md` suppresses a regex finding on the same
line:

```markdown
术语说明：唯一标识符用于数据库主键。 <!-- content-review-disable-line exaggerated_claims -->
```

`examples/demo/articles/technical-demo.md` suppresses a draft-marker regex
finding on the same line:

```markdown
FIXME: 这个草稿标记专门用于 suppression 演示。 <!-- content-review-disable-line unresolved_draft_marker -->
```

Suppressed findings do not appear in text output, JSON output, Markdown
reports, batch summaries, or quality-gate counts.

## Notes

- The demo uses only current deterministic rules and profile-configured
  `regex_rules`.
- The demo profiles are conservative examples, not compliance guarantees.
