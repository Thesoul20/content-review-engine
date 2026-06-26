# Profiles

For the end-to-end first-run workflow, see
[docs/QUICKSTART.md](./QUICKSTART.md).

For rule-system details such as supported `rule_id` values, severity ordering,
suppression comments, counts, and quality gates, see
[docs/RULES.md](./RULES.md), the canonical rule reference.

## Purpose

This document describes the repository's YAML review profiles and the built-in
example profiles under `profiles/examples/`.

A review profile is input data for the core package. It configures metadata,
basic document constraints, enabled deterministic rules, rule terms,
rule-specific severity, and optional allowlists.

Example profiles are starting points only. They do not guarantee legal,
advertising, medical, regulatory, or platform compliance. Users must review and
customize them for their own publication workflow.

## Example Profiles

The repository now includes three built-in example profiles:

- `profiles/examples/general-basic.yaml`
- `profiles/examples/wechat-basic.yaml`
- `profiles/examples/wechat-strict.yaml`

These files are committed examples and test fixtures. They are not discovered
automatically at runtime. Use them by passing the profile path explicitly.

The same three profiles are also exposed as built-in templates through
`content-review profile init`.

Discover the available built-in templates with:

```bash
uv run content-review profile list
uv run content-review profile list --format json
```

## Initialize A Profile

Create a new editable profile file from a built-in template:

```bash
uv run content-review profile init --template general-basic --output profiles/general.yaml
uv run content-review profile init --template wechat-basic --output profiles/my-wechat.yaml
uv run content-review profile init --template wechat-strict --output profiles/wechat-strict.yaml
```

Supported template names:

- `general-basic`
- `wechat-basic`
- `wechat-strict`

`content-review profile list` and `content-review profile init` use the same
built-in template registry. The displayed order is deterministic:

- `general-basic`
- `wechat-basic`
- `wechat-strict`

Generated profiles are starting points. They do not guarantee compliance with
any platform policy, legal requirement, advertising regulation, medical
content standard, or publishing rule.

By default, initialization does not overwrite an existing file.
Use `--force` only when you intentionally want to replace the output file:

```bash
uv run content-review profile init --template wechat-strict --output profiles/wechat-strict.yaml --force
```

If the parent directory does not exist, the command fails instead of creating
directories automatically.

## Profile Format

Example profiles use the current `rules:`-based format:

```yaml
name: wechat-basic
target_platform: wechat
tone: clear and professional
max_title_length: 32
max_paragraph_length: 220

rules:
  - id: forbidden_terms
    enabled: true
    severity: error
    terms:
      - 违规词
    allow_terms: []

  - id: absolute_claims
    enabled: true
    severity: warning
    terms:
      - 全网最强
    allow_terms: []
```

Current implemented rule IDs that can be used in example profiles:

- `forbidden_terms`
- `absolute_claims`
- `markdown_structure`
- `markdown_links_images`

The built-in examples only use `forbidden_terms` and `absolute_claims` so they
stay easy to read and customize.

Initialized profiles use the same YAML content as the built-in examples at the
time they are created. After initialization, the new file is a normal local
profile and is no longer linked to the example file in the repository.

## Profile Differences

`general-basic.yaml`

- General-purpose starter profile for ordinary public-facing content.
- Enables `forbidden_terms` and `absolute_claims`.
- Keeps `absolute_claims` at `warning`.
- Avoids WeChat-specific assumptions.

`wechat-basic.yaml`

- Starter profile for WeChat article drafts and public posts.
- Uses WeChat-oriented title and paragraph defaults.
- Treats `forbidden_terms` as `error` and `absolute_claims` as `warning`.
- Includes one `allow_terms` example: `唯一标识符`.

`wechat-strict.yaml`

- Stricter WeChat-oriented profile for CI gates and publication checks.
- Uses tighter title and paragraph limits.
- Raises `absolute_claims` to `error`.
- Intended to work well with `--fail-on error`.

## Validate A Profile

Validate before using a profile in review or batch:

```bash
uv run content-review profile validate profiles/examples/general-basic.yaml
uv run content-review profile validate profiles/examples/wechat-basic.yaml
uv run content-review profile validate profiles/examples/wechat-strict.yaml
uv run content-review profile validate profiles/my-wechat.yaml
```

JSON output is available for automation:

```bash
uv run content-review profile validate profiles/examples/wechat-strict.yaml --format json
```

## Run Review With An Example Profile

Single file:

```bash
uv run content-review review examples/article.md --profile profiles/examples/general-basic.yaml
uv run content-review review tests/fixtures/markdown/absolute_claims_article.md --profile profiles/examples/wechat-basic.yaml
```

Batch:

```bash
uv run content-review batch examples/batch/articles --profile profiles/examples/wechat-strict.yaml --recursive --fail-on error
uv run content-review batch articles --profile profiles/my-wechat.yaml --recursive --fail-on error
```

## Use Profiles In CI

The repository includes a GitHub Actions example at:

`docs/examples/github-actions/content-review.yml`

A practical CI flow is:

```bash
uv run content-review profile validate profiles/my-wechat.yaml
uv run content-review batch articles --profile profiles/my-wechat.yaml --recursive --fail-on error
```

To adapt the example:

- Change the profile path if your profile is not under `profiles/`.
- Change the articles path if your Markdown content is not under `articles/`.

Exit code behavior for CI:

- `profile validate`: `0` means valid, `2` means invalid or unreadable.
- `batch --fail-on error`: `0` means pass, `1` means findings met the quality
  gate, `2` means command or configuration error.

Built-in examples and initialized profiles are starting points only. They do
not guarantee legal, advertising, medical, regulatory, or platform compliance.

## Customization

Common edits:

- Change `terms` in `forbidden_terms` to match your blocked expressions.
- Change `terms` in `absolute_claims` to match your risky claim vocabulary.
- Change `absolute_claims.severity` between `warning`, `error`, and `critical`
  based on how strict your workflow should be.
- Add exact-match `allow_terms` when a configured term is acceptable in a
  specific literal form.
- Adjust `max_title_length` and `max_paragraph_length` for your publishing
  channel.

Typical workflow after initialization:

1. Run `content-review profile list` to inspect the built-in templates.
2. Run `content-review profile init` with the closest built-in template.
3. Edit `terms`, `allow_terms`, and rule severities for your workflow.
4. Validate the file with `content-review profile validate`.
5. Use the resulting profile with `review` or `batch`.

`allow_terms` is a literal allowlist. It does not support regex, wildcards, or
fuzzy matching.

## Inline Suppression

Profiles define what the engine checks. Inline suppression is a separate
document-level escape hatch for intentional exceptions.

Example:

```markdown
不要使用“全网最强”这种表述。 <!-- content-review-disable-line absolute_claims -->
```

Suppression does not change the profile file. It only suppresses matching
findings for the annotated Markdown line or next line.
