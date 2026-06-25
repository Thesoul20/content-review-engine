
# TASK-0020: Add Built-in Example Profiles

## Status

Planned

## Goal

Add official example review profiles and documentation so users can start using the content review engine without writing YAML profiles from scratch.

After this task, the repository should include a small set of ready-to-use example profiles, such as:

```text
profiles/examples/general-basic.yaml
profiles/examples/wechat-basic.yaml
profiles/examples/wechat-strict.yaml
```

These profiles should demonstrate how to configure:

* `forbidden_terms`
* `absolute_claims`
* `severity`
* `allow_terms`
* profile metadata
* profile validation workflow

This task improves onboarding, documentation quality, and real-world usability without changing the review engine behavior.

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
* `content-review profile validate <profile_path>`

However, users currently need to create their own profile YAML files manually.

Now that profile validation exists, the next useful step is to provide official example profiles that can be validated, copied, modified, and used as templates.

This task should make the tool easier to try, demonstrate best practices, and provide stable fixtures for future documentation and examples.

## Scope

This task includes:

1. Add a `profiles/examples/` directory.
2. Add `general-basic.yaml`.
3. Add `wechat-basic.yaml`.
4. Add `wechat-strict.yaml`.
5. Ensure all example profiles are valid according to `content-review profile validate`.
6. Add tests that load and validate all example profiles.
7. Add tests that run review against at least one example profile.
8. Add documentation explaining each example profile.
9. Add documentation showing how to copy and customize an example profile.
10. Update `docs/CLI.md` with example profile usage.
11. Add or update `docs/PROFILES.md`.
12. Update `PROJECT_STATE.md`.
13. Update `CHANGELOG.md`.

## Non-goals

This task must not implement:

* New review rules
* LLM-based review
* Auto-fix behavior
* Profile generation
* Profile auto-formatting
* Interactive profile wizard
* Remote profile loading
* Rule marketplace
* `content-review profile list`
* `content-review profile init`
* Built-in profile aliases such as `--profile wechat-basic`
* API server
* MCP server
* Frontend UI
* Database persistence
* Publishing integration

## Directory Design

Add the following directory:

```text
profiles/examples/
```

Recommended files:

```text
profiles/examples/general-basic.yaml
profiles/examples/wechat-basic.yaml
profiles/examples/wechat-strict.yaml
```

The examples should be committed to the repository.

They should be treated as documentation examples and test fixtures.

Do not add runtime profile discovery or profile alias resolution in this task.

Users should still pass profiles by path:

```bash
content-review review article.md --profile profiles/examples/wechat-basic.yaml
content-review batch articles --profile profiles/examples/wechat-strict.yaml --fail-on error
```

## Example Profile: general-basic.yaml

Purpose:

A conservative general-purpose profile for ordinary public-facing content.

Expected behavior:

* Uses `forbidden_terms`
* Uses `absolute_claims`
* Uses moderate severity defaults
* Avoids overly platform-specific assumptions

Suggested content:

```yaml
name: general-basic
target_platform: general

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
      - 绝对安全
      - 永久有效
      - 零风险
      - 100% 有效
      - 保证成功
      - 彻底解决
    allow_terms: []
```

Notes:

* The terms are examples, not a complete policy list.
* This profile should be safe and easy to understand.
* Do not claim that this profile guarantees legal, regulatory, or platform compliance.

## Example Profile: wechat-basic.yaml

Purpose:

A basic profile for WeChat Official Account style articles and public posts.

Expected behavior:

* Suitable for article drafts.
* Uses `forbidden_terms` for obvious blocked expressions.
* Uses `absolute_claims` for marketing exaggeration.
* Keeps severity moderate so users can start with warnings before adopting strict gates.

Suggested content:

```yaml
name: wechat-basic
target_platform: wechat

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
      - 绝对安全
      - 永久有效
      - 零风险
      - 100% 有效
      - 保证成功
      - 彻底解决
      - 唯一选择
    allow_terms:
      - 唯一标识符
```

Notes:

* This is an example profile, not an official WeChat policy implementation.
* Documentation should clearly state that users must customize terms based on their own publishing requirements.

## Example Profile: wechat-strict.yaml

Purpose:

A stricter profile for CI gates, release checks, and content publishing workflows.

Expected behavior:

* More aggressive than `wechat-basic`.
* Uses higher severity for risky expressions.
* Intended to be used with `--fail-on error`.

Suggested content:

```yaml
name: wechat-strict
target_platform: wechat

rules:
  - id: forbidden_terms
    enabled: true
    severity: critical
    terms:
      - 违规词
      - 敏感词
      - 禁用词
      - 不当表达
    allow_terms: []

  - id: absolute_claims
    enabled: true
    severity: error
    terms:
      - 全网最强
      - 行业第一
      - 绝对安全
      - 永久有效
      - 零风险
      - 100% 有效
      - 保证成功
      - 彻底解决
      - 永不失败
      - 立刻见效
      - 唯一选择
    allow_terms:
      - 唯一标识符
```

Recommended usage:

```bash
content-review profile validate profiles/examples/wechat-strict.yaml
content-review batch articles --profile profiles/examples/wechat-strict.yaml --fail-on error
```

## Example Profile Quality Rules

All example profiles must follow these rules:

1. They must be valid YAML.
2. They must pass `content-review profile validate`.
3. They must use the current `rules:` based profile format.
4. They must not rely on deprecated profile syntax unless the purpose is explicitly to document backward compatibility.
5. They must only use currently implemented rule ids.
6. They must only use canonical severity values:

```text
info
warning
error
critical
```

7. `terms` must be a list of strings.
8. `allow_terms` must be a list of strings.
9. Example term lists should be short and understandable.
10. Documentation must state that example profiles are starting points, not compliance guarantees.

## Documentation Design

Add a new documentation file if it does not already exist:

```text
docs/PROFILES.md
```

This document should explain:

1. What a ReviewProfile is.
2. Where example profiles live.
3. How to validate a profile.
4. How to run review with an example profile.
5. How to run batch review with an example profile.
6. How to customize terms.
7. How to customize severity.
8. How to use `allow_terms`.
9. How inline suppression relates to profiles.
10. The difference between `wechat-basic` and `wechat-strict`.

## docs/PROFILES.md Suggested Structure

Recommended headings:

```markdown
# Review Profiles

## What is a ReviewProfile?

## Example Profiles

## Validate a Profile

## Use a Profile for Single-File Review

## Use a Profile for Batch Review

## Customize Terms

## Customize Severity

## Use allow_terms

## Use Inline Suppression

## Example: Basic WeChat Profile

## Example: Strict WeChat Profile

## Notes and Limitations
```

## CLI Documentation Updates

Update `docs/CLI.md` with example profile usage.

Add examples:

```bash
content-review profile validate profiles/examples/wechat-basic.yaml
```

```bash
content-review review article.md --profile profiles/examples/wechat-basic.yaml
```

```bash
content-review batch articles --profile profiles/examples/wechat-strict.yaml --fail-on error
```

Also document the recommended workflow:

```bash
content-review profile validate profiles/examples/wechat-strict.yaml
content-review batch articles --profile profiles/examples/wechat-strict.yaml --fail-on error
```

## Important Documentation Wording

Documentation must not claim that example profiles provide full legal, regulatory, advertising, medical, or platform compliance.

Use wording such as:

```text
These profiles are examples and starting points. They do not guarantee compliance with any platform policy, legal requirement, advertising regulation, or medical content standard.
```

Also explain that users should customize terms for their own team, brand, jurisdiction, and publishing platform.

## Review Behavior

This task should not change review behavior.

Existing commands should continue to work:

```bash
content-review review article.md --profile profile.yaml
content-review batch articles --profile profile.yaml
content-review batch articles --profile profile.yaml --fail-on error
```

The new example profiles are normal profile files and should be used through existing CLI commands.

## Validation Behavior

The following commands should pass:

```bash
content-review profile validate profiles/examples/general-basic.yaml
content-review profile validate profiles/examples/wechat-basic.yaml
content-review profile validate profiles/examples/wechat-strict.yaml
```

Expected exit code:

```text
0
```

The following should also work:

```bash
content-review profile validate profiles/examples/wechat-basic.yaml --format json
```

Expected behavior:

* JSON output has `valid: true`.
* JSON output uses the existing profile validation result schema.
* Exit code is `0`.

## Packaging Behavior

If the current project packaging configuration already includes non-code repository files, ensure the example profiles are included appropriately.

If packaging non-code data is not currently configured, do not introduce a large packaging refactor in this task.

Minimum requirement:

* Example profiles exist in the repository.
* Tests can load them from the repository path.
* Documentation references them by repository path.

Do not implement runtime profile discovery or installed-package resource loading in this task.

## Testing Requirements

Add tests that validate all example profiles.

Suggested test file:

```text
tests/test_example_profiles.py
```

Suggested tests:

```text
example general-basic profile loads successfully
example wechat-basic profile loads successfully
example wechat-strict profile loads successfully
profile validate command returns 0 for all example profiles
profile validate --format json returns valid true for all example profiles
```

Add review integration tests using example profiles.

Suggested cases:

```text
review with wechat-basic detects an absolute claim
review with wechat-basic detects a forbidden term
review with wechat-strict can trigger --fail-on error
review with wechat-basic respects allow_terms
```

If existing CLI tests are already large, keep CLI coverage minimal and prefer loader-level tests for all example profiles.

## Backward Compatibility

This task must preserve existing behavior for:

* `forbidden_terms`
* `absolute_claims`
* `allow_terms`
* Inline suppression
* Single-file review
* Batch review
* Profile validation
* JSON output
* Text output
* Markdown output
* `--fail-on`
* Existing tests

No existing profile syntax should be removed.

No existing CLI command should be renamed.

## Acceptance Criteria

This task is complete when:

1. `profiles/examples/` exists.
2. `profiles/examples/general-basic.yaml` exists.
3. `profiles/examples/wechat-basic.yaml` exists.
4. `profiles/examples/wechat-strict.yaml` exists.
5. All example profiles pass `content-review profile validate`.
6. All example profiles can be loaded by the profile loader.
7. At least one example profile is used in a review integration test.
8. At least one example profile is used in a CLI validation test.
9. Documentation explains how to use example profiles.
10. Documentation explains how to customize example profiles.
11. Documentation explains `allow_terms`.
12. Documentation explains inline suppression in relation to profiles.
13. Documentation includes the compliance limitation disclaimer.
14. `docs/CLI.md` is updated with example profile usage.
15. `docs/PROFILES.md` is added or updated.
16. `PROJECT_STATE.md` is updated.
17. `CHANGELOG.md` is updated.
18. Existing review behavior remains unchanged.
19. Existing profile validation behavior remains unchanged.
20. `uv run pytest` passes.

## Suggested Test Command

```bash
uv run pytest
```

## Implementation Notes

Recommended implementation order:

1. Inspect existing profile fixtures and documentation.
2. Add `profiles/examples/` directory.
3. Add `general-basic.yaml`.
4. Add `wechat-basic.yaml`.
5. Add `wechat-strict.yaml`.
6. Validate profiles manually using `content-review profile validate`.
7. Add tests to load all example profiles.
8. Add tests to validate all example profiles through the CLI.
9. Add at least one review integration test using an example profile.
10. Add or update `docs/PROFILES.md`.
11. Update `docs/CLI.md`.
12. Update `PROJECT_STATE.md`.
13. Update `CHANGELOG.md`.
14. Run the full test suite.

