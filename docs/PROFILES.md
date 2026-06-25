# Profiles

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
```

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
