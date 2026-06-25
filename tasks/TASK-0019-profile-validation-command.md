
# TASK-0019: Add Profile Validation Command

## Status

Planned

## Goal

Add a dedicated CLI command for validating review profile YAML files.

After this task, users should be able to run:

```bash
content-review profile validate profile.yaml
```

to check whether a `ReviewProfile` is valid before using it in `review` or `batch`.

This task improves usability, CI integration, and profile authoring workflows without adding new review rules.

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
* Rule registry / rule runner

As more rules and profile fields are added, invalid profile configuration becomes a common failure point.

Examples of invalid profile issues:

```yaml
rules:
  - id: absolute_claims
    enabled: true
    terms: 全网最强
```

The profile is invalid because `terms` should be a list of strings, not a single string.

Another example:

```yaml
rules:
  - id: forbidden_terms
    enabled: true
    severity: high
    terms:
      - 违规词
```

The profile is invalid because `high` is not part of the canonical severity values:

```text
info
warning
error
critical
```

Currently, users may only discover such errors while running a review command. This task adds an explicit validation command so users can validate profiles independently.

## Scope

This task includes:

1. Add a new CLI command group: `profile`.
2. Add a new subcommand: `profile validate <profile_path>`.
3. Reuse the existing profile loader and validation logic.
4. Return clear success output for valid profiles.
5. Return clear error output for invalid profiles.
6. Support output formats for validation results.
7. Return CI-friendly exit codes.
8. Add tests for valid and invalid profile validation.
9. Update CLI documentation.
10. Update architecture documentation if needed.
11. Update `PROJECT_STATE.md`.
12. Update `CHANGELOG.md`.

## Non-goals

This task must not implement:

* New review rules
* LLM-based review
* Auto-fix behavior
* Profile auto-formatting
* Profile migration
* Profile generation
* Interactive profile wizard
* Remote profile loading
* Built-in profile templates
* Rule marketplace
* API server
* MCP server
* Frontend UI
* Database persistence
* Publishing integration

## CLI Design

Add a new command:

```bash
content-review profile validate <profile_path>
```

Example:

```bash
content-review profile validate profiles/wechat.yaml
```

Expected success output:

```text
Profile validation passed.

Path: profiles/wechat.yaml
Name: wechat
Target Platform: wechat
Enabled Rules: 2
Rules:
- forbidden_terms
- absolute_claims
```

Exact wording may follow the existing CLI output style.

## Command Structure

The CLI should support:

```bash
content-review profile validate profile.yaml
```

This task should not add other profile subcommands yet.

Do not implement:

```bash
content-review profile list
content-review profile init
content-review profile format
content-review profile explain
```

Those can be future tasks.

## Output Formats

The command should support at least the default text output.

Recommended option:

```bash
content-review profile validate profile.yaml --format text
content-review profile validate profile.yaml --format json
```

If the current CLI output format system already supports `text`, `json`, and `markdown`, then `profile validate` may support all three:

```bash
content-review profile validate profile.yaml --format text
content-review profile validate profile.yaml --format json
content-review profile validate profile.yaml --format markdown
```

Minimum requirement:

```text
text
json
```

Markdown support is optional in this task unless it is easy to reuse existing rendering patterns.

## Text Output

For a valid profile, text output should include:

```text
Profile validation passed.

Path: profiles/wechat.yaml
Name: wechat
Target Platform: wechat
Enabled Rules: 2
Disabled Rules: 0
Rules:
- forbidden_terms
- absolute_claims
```

For an invalid profile, text output should include:

```text
Profile validation failed.

Path: profiles/wechat.yaml
Error: rules[0].terms must be a list of strings
```

Exact error wording may follow the existing profile loader exception style.

## JSON Output

For a valid profile, JSON output should be stable and machine-readable.

Suggested shape:

```json
{
  "schema_version": "profile-validation-result.v1",
  "valid": true,
  "path": "profiles/wechat.yaml",
  "profile": {
    "name": "wechat",
    "target_platform": "wechat",
    "enabled_rule_count": 2,
    "disabled_rule_count": 0,
    "rules": [
      {
        "id": "forbidden_terms",
        "enabled": true,
        "severity": "error"
      },
      {
        "id": "absolute_claims",
        "enabled": true,
        "severity": "warning"
      }
    ]
  },
  "errors": []
}
```

For an invalid profile:

```json
{
  "schema_version": "profile-validation-result.v1",
  "valid": false,
  "path": "profiles/wechat.yaml",
  "profile": null,
  "errors": [
    {
      "message": "rules[0].terms must be a list of strings"
    }
  ]
}
```

The implementation does not need to expose every internal profile field. The goal is to provide enough information for users and CI systems.

## Exit Code Rules

Use the existing CLI exit code policy:

```text
0 = profile is valid
2 = profile is invalid, missing, unreadable, or cannot be parsed
```

Do not use exit code `1` for invalid profiles.

Reason:

* Exit code `1` is already used for quality gate failure.
* Profile validation failure is a command/configuration error.
* Therefore, invalid profile should return exit code `2`.

Examples:

```bash
content-review profile validate valid-profile.yaml
```

Expected:

```text
exit code = 0
```

```bash
content-review profile validate invalid-profile.yaml
```

Expected:

```text
exit code = 2
```

```bash
content-review profile validate missing-profile.yaml
```

Expected:

```text
exit code = 2
```

## Validation Behavior

The command should reuse the existing profile loading and validation logic.

It should validate at least:

1. Profile file exists.
2. Profile file is readable.
3. YAML is valid.
4. Required profile fields are valid.
5. Rule list is valid.
6. Rule ids are known.
7. Rule severity values are valid.
8. `forbidden_terms.terms` is a list of strings.
9. `forbidden_terms.allow_terms` is a list of strings if provided.
10. `absolute_claims.terms` is a list of strings.
11. `absolute_claims.allow_terms` is a list of strings if provided.

Do not create a second validation implementation that duplicates the profile loader.

The validation command should be a thin CLI layer around the existing profile loader.

## Unknown Rule Behavior

Invalid example:

```yaml
rules:
  - id: unknown_rule
    enabled: true
```

Expected behavior:

* Validation should fail.
* Exit code should be `2`.
* Error message should clearly mention unknown rule id.

Example output:

```text
Profile validation failed.

Path: profiles/wechat.yaml
Error: unknown rule id: unknown_rule
```

Exact wording may follow existing error style.

## Severity Validation

Invalid example:

```yaml
rules:
  - id: absolute_claims
    enabled: true
    severity: high
    terms:
      - 全网最强
```

Expected behavior:

* Validation should fail.
* Exit code should be `2`.
* Error should mention valid severity values or the invalid value.

Canonical severity values:

```text
info
warning
error
critical
```

## Suggested Internal Design

Add a small validation result model if useful.

Possible location:

```text
src/content_review_engine/core/models.py
```

Suggested model:

```python
@dataclass(frozen=True)
class ProfileValidationResult:
    schema_version: str
    valid: bool
    path: str
    profile_summary: ProfileSummary | None
    errors: list[ProfileValidationError]
```

However, this is optional.

A simpler CLI-only structure is acceptable if it keeps the implementation clean and tested.

If adding models, avoid large model rewrites.

## Suggested Serializer

If JSON output is supported, add a serializer function if appropriate.

Possible location:

```text
src/content_review_engine/serialization.py
```

or wherever existing serializers live.

Suggested function:

```python
def profile_validation_result_to_dict(result: ProfileValidationResult) -> dict:
    ...
```

If the project already has a serialization module or pattern, follow it.

## CLI Integration

If the CLI currently uses Typer, Click, or argparse, follow the existing style.

The resulting command should appear in help output:

```bash
content-review --help
content-review profile --help
content-review profile validate --help
```

The help text should clearly explain:

```text
Validate a review profile YAML file.
```

## Testing Requirements

Add CLI tests for valid profiles.

Suggested cases:

```text
profile validate returns 0 for a valid forbidden_terms profile
profile validate returns 0 for a valid absolute_claims profile
profile validate returns 0 for a profile containing both forbidden_terms and absolute_claims
```

Add CLI tests for invalid profiles.

Suggested cases:

```text
profile validate returns 2 for missing profile file
profile validate returns 2 for invalid YAML
profile validate returns 2 for unknown rule id
profile validate returns 2 for invalid severity
profile validate returns 2 for non-list forbidden_terms.terms
profile validate returns 2 for non-list forbidden_terms.allow_terms
profile validate returns 2 for non-list absolute_claims.terms
profile validate returns 2 for non-list absolute_claims.allow_terms
```

Add tests for JSON output.

Suggested cases:

```text
profile validate --format json returns valid true for valid profile
profile validate --format json returns valid false for invalid profile
profile validate --format json includes schema_version
profile validate --format json includes error messages for invalid profile
```

Add tests for help output if current test style supports it.

Suggested cases:

```text
content-review profile --help includes validate
content-review profile validate --help includes profile_path
```

## Documentation Updates

Update `docs/CLI.md` with:

```bash
content-review profile validate profiles/wechat.yaml
content-review profile validate profiles/wechat.yaml --format json
```

Document exit codes:

```text
0 = profile is valid
2 = profile is invalid or command error
```

Document common validation errors:

```text
unknown rule id
invalid severity
terms must be a list of strings
allow_terms must be a list of strings
invalid YAML
missing profile file
```

Update `docs/ARCHITECTURE.md` if needed to mention:

```text
Profile validation reuses the same profile loader used by review and batch commands.
```

Update `PROJECT_STATE.md` with:

* TASK-0019 completed
* Added `content-review profile validate`
* Profile authoring and CI validation workflow improved

Update `CHANGELOG.md` with:

* Added profile validation CLI command
* Added machine-readable validation output if JSON is implemented

## Acceptance Criteria

This task is complete when:

1. `content-review profile validate <profile_path>` exists.
2. Valid profiles return exit code `0`.
3. Invalid profiles return exit code `2`.
4. Missing profile files return exit code `2`.
5. Invalid YAML returns exit code `2`.
6. Unknown rule ids are rejected.
7. Invalid severity values are rejected.
8. Invalid `terms` values are rejected.
9. Invalid `allow_terms` values are rejected.
10. Valid profiles with `forbidden_terms` pass.
11. Valid profiles with `absolute_claims` pass.
12. Valid profiles with both rules pass.
13. Text output clearly indicates pass or fail.
14. JSON output is supported or intentionally documented as not supported.
15. CLI tests are added.
16. Documentation is updated.
17. `PROJECT_STATE.md` is updated.
18. `CHANGELOG.md` is updated.
19. Existing review, batch, suppression, and quality gate tests still pass.
20. `uv run pytest` passes.

## Suggested Test Command

```bash
uv run pytest
```

## Implementation Notes

Recommended implementation order:

1. Inspect the existing CLI structure.
2. Inspect the existing profile loader and validation errors.
3. Add `profile` command group.
4. Add `profile validate <profile_path>` command.
5. Reuse existing profile loading logic.
6. Add text output for valid and invalid results.
7. Add JSON output if it fits the current CLI output design.
8. Add tests for valid profiles.
9. Add tests for invalid profiles.
10. Add tests for JSON output.
11. Update `docs/CLI.md`.
12. Update `docs/ARCHITECTURE.md` if needed.
13. Update `PROJECT_STATE.md`.
14. Update `CHANGELOG.md`.
15. Run the full test suite.

