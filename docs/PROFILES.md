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

The repository now includes eight built-in example profiles:

- `profiles/examples/general-basic.yaml`
- `profiles/examples/general-publishing.yaml`
- `profiles/examples/health-content.yaml`
- `profiles/examples/marketing-copy.yaml`
- `profiles/examples/technical-blog.yaml`
- `profiles/examples/wechat-basic.yaml`
- `profiles/examples/wechat-article.yaml`
- `profiles/examples/wechat-strict.yaml`

These files are committed examples and test fixtures. They are not discovered
automatically at runtime. Use them by passing the profile path explicitly.

The same example profiles are also exposed as built-in templates through
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
uv run content-review profile init --template general-publishing --output profiles/publishing.yaml
uv run content-review profile init --template health-content --output profiles/health.yaml
uv run content-review profile init --template marketing-copy --output profiles/marketing.yaml
uv run content-review profile init --template technical-blog --output profiles/technical.yaml
uv run content-review profile init --template wechat-basic --output profiles/my-wechat.yaml
uv run content-review profile init --template wechat-article --output profiles/wechat-article.yaml
uv run content-review profile init --template wechat-strict --output profiles/wechat-strict.yaml
```

Supported template names:

- `general-basic`
- `general-publishing`
- `health-content`
- `marketing-copy`
- `technical-blog`
- `wechat-basic`
- `wechat-article`
- `wechat-strict`

`content-review profile list` and `content-review profile init` use the same
built-in template registry. The displayed order is deterministic:

- `general-basic`
- `general-publishing`
- `health-content`
- `marketing-copy`
- `technical-blog`
- `wechat-basic`
- `wechat-article`
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

Profiles can also define additional profile-specific regex rule IDs under
`regex_rules:`. Those IDs are dynamic runtime profile data, not built-in rule
metadata entries.

Current built-in metadata for these rule IDs is centralized in
`src/content_review_engine/core/rule_registry.py`.
That metadata registry is descriptive only. It does not replace YAML profile
configuration, does not decide which rules are enabled in a specific profile,
and does not replace profile parsing in the current review pipeline.

Some built-in examples only use `forbidden_terms` and `absolute_claims`.
The real-world templates also demonstrate `markdown_structure`,
`markdown_links_images`, and profile-configured `regex_rules` so users can
start from practical publishing checks without changing Python code.

Initialized profiles use the same YAML content as the built-in examples at the
time they are created. After initialization, the new file is a normal local
profile and is no longer linked to the example file in the repository.

## Regex Rules

Profiles can define optional deterministic regex-based checks:

```yaml
regex_rules:
  - id: exaggerated_claims
    pattern: "唯一|第一|最强|绝对|100%"
    severity: warning
    message: "Avoid absolute or exaggerated claims."
    suggestion: "Use a more cautious and evidence-based expression."
    case_sensitive: false
```

Current regex rule fields:

- `id`: required stable rule ID matching `^[a-z][a-z0-9_]*$`
- `pattern`: required Python regular expression
- `severity`: required `info`, `warning`, `error`, or `critical`
- `message`: required finding message
- `suggestion`: optional finding suggestion
- `case_sensitive`: optional boolean, default `false`

Validation behavior:

- invalid regex patterns are rejected during profile loading and profile
  validation
- duplicate regex rule IDs within `regex_rules` are rejected
- regex rules are optional and are not required in any profile

Execution behavior:

- regex rules scan raw Markdown line by line
- each match produces one finding
- findings use the configured regex rule `id` as `rule_id`
- cross-line regex matching is not supported in this task
- inline suppression works with the configured regex rule ID, for example
  `<!-- content-review-disable-line exaggerated_claims -->`

Regex rule IDs are not added to the built-in metadata registry in
`src/content_review_engine/core/rule_registry.py` because they are
profile-defined and dynamic.

## Profile Differences

`general-basic.yaml`

- General-purpose starter profile for ordinary public-facing content.
- Enables `forbidden_terms` and `absolute_claims`.
- Keeps `absolute_claims` at `warning`.
- Avoids WeChat-specific assumptions.

`general-publishing.yaml`

- General-purpose publishing profile for common Markdown workflows.
- Enables `markdown_structure` and `markdown_links_images`.
- Adds regex checks for draft placeholders and overconfident wording.
- Helps flag common risky wording patterns for review.

`health-content.yaml`

- Cautious health-content profile for general educational drafts.
- Uses regex checks for treatment guarantees, self-diagnosis language, and
  unresolved source placeholders.
- Does not provide legal, medical, advertising, regulatory, or platform
  compliance advice.

`marketing-copy.yaml`

- Marketing-oriented profile for guarantee-like wording, pressure tactics, and
  unverifiable superlatives.
- Uses `regex_rules` to flag riskier promotional phrasing while keeping the
  messages conservative.
- Does not claim advertising or legal compliance.

`technical-blog.yaml`

- Technical writing profile for unresolved draft markers, unfinished examples,
  and absolute technical claims.
- Enables structure and link checks in addition to term-based rules.
- Intended as a practical publishing review baseline, not a correctness proof.

`wechat-basic.yaml`

- Starter profile for WeChat article drafts and public posts.
- Uses WeChat-oriented title and paragraph defaults.
- Treats `forbidden_terms` as `error` and `absolute_claims` as `warning`.
- Includes one `allow_terms` example: `唯一标识符`.

`wechat-article.yaml`

- Public-account article profile for cautious public-facing draft review.
- Adds regex checks for exaggerated claims, engagement bait, and unfinished
  article placeholders.
- Helps flag common risky wording patterns for review.

`wechat-strict.yaml`

- Stricter WeChat-oriented profile for CI gates and publication checks.
- Uses tighter title and paragraph limits.
- Raises `absolute_claims` to `error`.
- Intended to work well with `--fail-on error`.

## Real-World Template Use Cases

- `general-publishing`: common publishing risks, placeholders, overconfident
  wording, and basic Markdown hygiene.
- `wechat-article`: WeChat article wording, exaggerated claims, engagement
  bait, placeholders, and Markdown hygiene.
- `marketing-copy`: guarantee-like wording, unverifiable superlatives, and
  pressure tactics that may need editorial review.
- `technical-blog`: TODO or FIXME markers, unresolved examples, and absolute
  technical claims.
- `health-content`: cautious health wording, treatment guarantees,
  self-diagnosis risks, and missing source placeholders.

## Validate A Profile

Validate before using a profile in review or batch:

```bash
uv run content-review profile validate profiles/examples/general-basic.yaml
uv run content-review profile validate profiles/examples/general-publishing.yaml
uv run content-review profile validate profiles/examples/health-content.yaml
uv run content-review profile validate profiles/examples/marketing-copy.yaml
uv run content-review profile validate profiles/examples/technical-blog.yaml
uv run content-review profile validate profiles/examples/wechat-basic.yaml
uv run content-review profile validate profiles/examples/wechat-article.yaml
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
They help flag common risky wording patterns for review.

## Customization

Common edits:

- Change `terms` in `forbidden_terms` to match your blocked expressions.
- Change `terms` in `absolute_claims` to match your risky claim vocabulary.
- Change `absolute_claims.severity` between `warning`, `error`, and `critical`
  based on how strict your workflow should be.
- Add exact-match `allow_terms` when a configured term is acceptable in a
  specific literal form.
- Add `regex_rules` when a deterministic pattern is easier to express as a
  regular expression than as literal terms.
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

The metadata registry does not replace profile configuration. Profiles still
control rule enablement, configured terms, rule-specific severity, and related
document constraints for deterministic review. A future LLM semantic review
layer would be a separate later architecture layer, not a replacement for the
current profile format in TASK-0029.

Example:

```markdown
不要使用“全网最强”这种表述。 <!-- content-review-disable-line absolute_claims -->
```

Suppression does not change the profile file. It only suppresses matching
findings for the annotated Markdown line or next line.
