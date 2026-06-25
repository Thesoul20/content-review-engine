# TASK-0021: Add Profile Init Command

## Status

Planned

## Goal

Add a CLI command for initializing a new review profile from a built-in template.

After this task, users should be able to run:

```bash
content-review profile init --template wechat-basic --output profile.yaml
```

to create a new editable `ReviewProfile` YAML file.

This task improves onboarding and profile authoring by turning the existing example profiles into a practical CLI workflow.

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
* Built-in example profiles under `profiles/examples/`

TASK-0020 added example profiles:

```text
profiles/examples/general-basic.yaml
profiles/examples/wechat-basic.yaml
profiles/examples/wechat-strict.yaml
```

Users can already copy these files manually, but the CLI does not yet provide a convenient way to create a new profile from a template.

This task adds:

```bash
content-review profile init --template wechat-basic --output profiles/my-wechat.yaml
```

The generated file should be a normal YAML profile that can be validated, edited, and used by existing commands.

## Scope

This task includes:

1. Add `content-review profile init`.
2. Support `--template <template_name>`.
3. Support `--output <output_path>`.
4. Support a safe overwrite policy.
5. Provide a clear list of supported template names in help text and error messages.
6. Generate a valid YAML profile file.
7. Ensure generated profiles pass `content-review profile validate`.
8. Add tests for successful profile initialization.
9. Add tests for invalid template names.
10. Add tests for output file overwrite behavior.
11. Add tests that validate generated profiles.
12. Update `docs/CLI.md`.
13. Update `docs/PROFILES.md`.
14. Update `PROJECT_STATE.md`.
15. Update `CHANGELOG.md`.

## Non-goals

This task must not implement:

* New review rules
* LLM-based review
* Profile generation from natural language
* Interactive profile wizard
* Profile auto-formatting
* Remote template loading
* User-defined template directories
* Template marketplace
* `content-review profile list`
* Profile aliases for review commands, such as `--profile wechat-basic`
* API server
* MCP server
* Frontend UI
* Database persistence
* Publishing integration

## CLI Design

Add a new command:

```bash
content-review profile init --template <template_name> --output <output_path>
```

Example:

```bash
content-review profile init --template wechat-basic --output profiles/my-wechat.yaml
```

Expected output:

```text
Profile created.

Template: wechat-basic
Output: profiles/my-wechat.yaml

Next steps:
1. Edit the profile terms and severity levels.
2. Validate it with:
   content-review profile validate profiles/my-wechat.yaml
3. Use it with:
   content-review review article.md --profile profiles/my-wechat.yaml
```

Exact wording may follow the existing CLI output style.

## Supported Templates

The command should support these template names:

```text
general-basic
wechat-basic
wechat-strict
```

These names should correspond to the example profiles added in TASK-0020:

```text
profiles/examples/general-basic.yaml
profiles/examples/wechat-basic.yaml
profiles/examples/wechat-strict.yaml
```

## Command Examples

Create a general profile:

```bash
content-review profile init --template general-basic --output profiles/general.yaml
```

Create a WeChat basic profile:

```bash
content-review profile init --template wechat-basic --output profiles/wechat.yaml
```

Create a strict WeChat profile:

```bash
content-review profile init --template wechat-strict --output profiles/wechat-strict.yaml
```

Validate the generated profile:

```bash
content-review profile validate profiles/wechat.yaml
```

Use the generated profile:

```bash
content-review review article.md --profile profiles/wechat.yaml
```

Use the generated profile in batch mode:

```bash
content-review batch articles --profile profiles/wechat-strict.yaml --recursive --fail-on error
```

## Required Options

The command should require:

```text
--template
--output
```

Invalid example:

```bash
content-review profile init --template wechat-basic
```

Expected behavior:

* Command should fail.
* Exit code should be `2`.
* Error should clearly mention missing output path.

Invalid example:

```bash
content-review profile init --output profile.yaml
```

Expected behavior:

* Command should fail.
* Exit code should be `2`.
* Error should clearly mention missing template name.

## Template Validation

Invalid template example:

```bash
content-review profile init --template unknown --output profile.yaml
```

Expected behavior:

```text
Profile initialization failed.

Error: unknown template: unknown
Available templates:
- general-basic
- wechat-basic
- wechat-strict
```

Exit code:

```text
2
```

The exact output can follow the existing CLI error style.

## Output File Behavior

By default, the command should not overwrite an existing file.

Example:

```bash
content-review profile init --template wechat-basic --output existing.yaml
```

If `existing.yaml` already exists:

```text
Profile initialization failed.

Error: output file already exists: existing.yaml
Use --force to overwrite.
```

Exit code:

```text
2
```

## Force Overwrite

Add a `--force` flag.

Example:

```bash
content-review profile init --template wechat-basic --output existing.yaml --force
```

Expected behavior:

* Existing file is overwritten.
* Exit code is `0`.
* Output clearly states that the file was written.

## Output Directory Behavior

If the parent directory does not exist, use the simplest behavior consistent with the current CLI style.

Recommended behavior:

```text
Do not create missing parent directories automatically.
```

Invalid example:

```bash
content-review profile init --template wechat-basic --output missing-dir/profile.yaml
```

Expected behavior:

* Command fails.
* Exit code is `2`.
* Error mentions that the parent directory does not exist.

Do not implement automatic directory creation in this task unless the current CLI already does so for other output paths.

## Template Source Design

The implementation should use a small internal template registry.

Possible location:

```text
src/content_review_engine/config/templates.py
```

Suggested shape:

```python
BUILTIN_PROFILE_TEMPLATES = {
    "general-basic": "...yaml...",
    "wechat-basic": "...yaml...",
    "wechat-strict": "...yaml...",
}
```

Suggested helpers:

```python
def list_profile_templates() -> list[str]:
    ...


def get_profile_template(name: str) -> str:
    ...
```

The implementation may alternatively read from `profiles/examples/` if the project already has a clean way to access repository data files.

However, avoid a large packaging refactor in this task.

The generated profile must be normal YAML and must pass the existing `load_profile()` validation.

## Consistency With Example Profiles

The built-in templates should stay consistent with the example profiles added in TASK-0020.

Recommended approach:

* Use the same YAML content as the example profiles.
* Add tests to ensure generated profiles are valid.
* Optionally add tests to ensure template names match example profile filenames.

Do not introduce a complex synchronization system in this task.

## Generated YAML Requirements

Generated YAML should:

1. Be valid YAML.
2. Use the current `rules:` based profile format.
3. Use only implemented rule ids.
4. Use only canonical severity values:

```text
info
warning
error
critical
```

5. Include `name`.
6. Include `target_platform`.
7. Include `forbidden_terms` where appropriate.
8. Include `absolute_claims` where appropriate.
9. Include `allow_terms` fields where appropriate.
10. Pass `content-review profile validate`.

## Exit Code Rules

Use the existing CLI command error policy.

```text
0 = profile file created successfully
2 = invalid template, missing required options, output conflict, invalid path, write error, or unexpected command error
```

Do not use exit code `1`.

Reason:

* Exit code `1` is reserved for quality gate failure.
* `profile init` errors are command/configuration errors.
* Therefore, failures should return exit code `2`.

## JSON Output

This task does not need to support JSON output for `profile init`.

Default text output is enough.

Do not add `--format json` for `profile init` unless it is very easy and consistent with the existing CLI design.

If JSON output is not implemented, document only text output.

## Help Output

The command should be visible in help output:

```bash
content-review profile --help
content-review profile init --help
```

The help text should clearly explain:

```text
Create a new review profile from a built-in template.
```

The help text should expose:

```text
--template
--output
--force
```

## Validation Workflow

After running:

```bash
content-review profile init --template wechat-basic --output profiles/my-wechat.yaml
```

This should pass:

```bash
content-review profile validate profiles/my-wechat.yaml
```

Expected exit code:

```text
0
```

The generated profile should also work with:

```bash
content-review review article.md --profile profiles/my-wechat.yaml
```

## Documentation Updates

Update `docs/CLI.md` with:

```bash
content-review profile init --template wechat-basic --output profiles/my-wechat.yaml
content-review profile validate profiles/my-wechat.yaml
content-review review article.md --profile profiles/my-wechat.yaml
```

Also document:

```bash
content-review profile init --template wechat-strict --output profiles/wechat-strict.yaml --force
```

Update `docs/PROFILES.md` with:

1. How to initialize a profile.
2. Available templates.
3. How to validate a generated profile.
4. How to customize generated terms.
5. How to customize severity.
6. How to use the generated profile in review.
7. How to use the generated profile in batch mode.
8. The difference between example profiles and initialized profiles.

Important wording:

```text
Generated profiles are starting points. They do not guarantee compliance with any platform policy, legal requirement, advertising regulation, medical content standard, or publishing rule.
```

## Testing Requirements

Add CLI tests for successful initialization.

Suggested cases:

```text
profile init creates general-basic profile
profile init creates wechat-basic profile
profile init creates wechat-strict profile
generated profile passes load_profile
generated profile passes profile validate command
```

Add tests for failure behavior.

Suggested cases:

```text
profile init fails for unknown template
profile init fails when output file already exists
profile init overwrites existing file with --force
profile init fails when parent directory does not exist
```

Add help tests if current CLI test style supports them.

Suggested cases:

```text
content-review profile --help includes init
content-review profile init --help includes template
content-review profile init --help includes output
content-review profile init --help includes force
```

Add template registry tests if a registry module is added.

Suggested cases:

```text
list_profile_templates returns general-basic, wechat-basic, wechat-strict
get_profile_template returns valid YAML
get_profile_template rejects unknown template
all built-in templates pass load_profile
```

## Backward Compatibility

This task must preserve existing behavior for:

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

1. `content-review profile init` exists.
2. `--template` is supported.
3. `--output` is supported.
4. `--force` is supported.
5. Supported templates include `general-basic`.
6. Supported templates include `wechat-basic`.
7. Supported templates include `wechat-strict`.
8. Unknown templates are rejected clearly.
9. Existing output files are not overwritten by default.
10. Existing output files can be overwritten with `--force`.
11. Missing parent directories fail clearly.
12. Generated profiles are valid YAML.
13. Generated profiles pass `content-review profile validate`.
14. Generated profiles can be loaded by `load_profile()`.
15. At least one generated profile is used in a review or validation test.
16. CLI help includes the new command.
17. Documentation is updated.
18. `PROJECT_STATE.md` is updated.
19. `CHANGELOG.md` is updated.
20. Existing tests still pass.
21. `uv run pytest` passes.

## Suggested Test Command

```bash
uv run pytest
```

## Implementation Notes

Recommended implementation order:

1. Inspect current `profile validate` CLI implementation.
2. Inspect example profiles added in TASK-0020.
3. Add a built-in profile template registry if needed.
4. Add `profile init` command under the existing `profile` command group.
5. Implement template lookup.
6. Implement output path validation.
7. Implement no-overwrite default behavior.
8. Implement `--force`.
9. Add tests for template registry.
10. Add tests for successful profile generation.
11. Add tests for failure cases.
12. Add help output tests.
13. Update `docs/CLI.md`.
14. Update `docs/PROFILES.md`.
15. Update `PROJECT_STATE.md`.
16. Update `CHANGELOG.md`.
17. Run the full test suite.

