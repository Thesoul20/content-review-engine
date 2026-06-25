# TASK-0022: Add Profile List Command

## Status

Planned

## Goal

Add a CLI command for listing available built-in review profile templates.

After this task, users should be able to run:

```bash
content-review profile list
```

to discover the templates that can be used with:

```bash
content-review profile init --template <template_name> --output profile.yaml
```

This task improves discoverability and completes the basic profile authoring workflow:

```text
list available templates
  ↓
initialize a profile from a template
  ↓
validate the generated profile
  ↓
use the profile for review or batch
```

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
* `content-review profile init --template <template_name> --output <output_path>`

TASK-0021 added built-in profile initialization with these templates:

```text
general-basic
wechat-basic
wechat-strict
```

However, users currently need to know the template names from documentation.

This task adds a small discovery command:

```bash
content-review profile list
```

so users can see available templates directly from the CLI.

## Scope

This task includes:

1. Add `content-review profile list`.
2. List available built-in profile templates.
3. Reuse the existing built-in template registry from `config/templates.py`.
4. Show template names in text output.
5. Show short descriptions for each template if supported by the template registry.
6. Support JSON output for machine-readable use.
7. Add CLI tests for text output.
8. Add CLI tests for JSON output.
9. Add tests to ensure listed templates match supported `profile init` templates.
10. Update `docs/CLI.md`.
11. Update `docs/PROFILES.md`.
12. Update `PROJECT_STATE.md`.
13. Update `CHANGELOG.md`.

## Non-goals

This task must not implement:

* New review rules
* LLM-based review
* Profile generation from natural language
* Interactive profile wizard
* Remote template loading
* User-defined template directories
* Template marketplace
* Profile alias support such as `--profile wechat-basic`
* `content-review profile remove`
* `content-review profile edit`
* `content-review profile explain`
* API server
* MCP server
* Frontend UI
* Database persistence
* Publishing integration

## CLI Design

Add a new command:

```bash
content-review profile list
```

Expected text output:

```text
Available profile templates:

- general-basic
  General-purpose starter profile for public-facing content.

- wechat-basic
  Basic WeChat article profile with moderate checks.

- wechat-strict
  Stricter WeChat profile intended for batch checks and CI gates.

Use a template:

  content-review profile init --template wechat-basic --output profile.yaml
```

Exact wording may follow the current CLI style.

## Supported Templates

The command should list the same templates supported by `profile init`:

```text
general-basic
wechat-basic
wechat-strict
```

The list should come from the same source of truth used by `profile init`.

Do not duplicate the template list manually inside the CLI command handler.

## Template Metadata

If the current template registry only stores YAML content, extend it slightly to support metadata.

Recommended design:

```python
@dataclass(frozen=True)
class ProfileTemplate:
    name: str
    description: str
    content: str
```

Example registry shape:

```python
BUILTIN_PROFILE_TEMPLATES = {
    "general-basic": ProfileTemplate(
        name="general-basic",
        description="General-purpose starter profile for public-facing content.",
        content="...",
    ),
    "wechat-basic": ProfileTemplate(
        name="wechat-basic",
        description="Basic WeChat article profile with moderate checks.",
        content="...",
    ),
    "wechat-strict": ProfileTemplate(
        name="wechat-strict",
        description="Stricter WeChat profile intended for batch checks and CI gates.",
        content="...",
    ),
}
```

Suggested helper functions:

```python
def list_profile_templates() -> list[ProfileTemplate]:
    ...


def get_profile_template(name: str) -> ProfileTemplate:
    ...
```

If `get_profile_template()` currently returns a string, preserve backward compatibility or update all call sites carefully.

Avoid a large refactor.

## Output Formats

The command should support:

```bash
content-review profile list --format text
content-review profile list --format json
```

Default format:

```text
text
```

Do not add Markdown output unless it is already trivial and consistent with the existing CLI output design.

## Text Output

Text output should include:

1. A heading.
2. Template names.
3. Template descriptions.
4. A short usage example.

Example:

```text
Available profile templates:

- general-basic
  General-purpose starter profile for public-facing content.

- wechat-basic
  Basic WeChat article profile with moderate checks.

- wechat-strict
  Stricter WeChat profile intended for batch checks and CI gates.

Use a template:

  content-review profile init --template wechat-basic --output profile.yaml
```

## JSON Output

JSON output should be stable and machine-readable.

Suggested shape:

```json
{
  "schema_version": "profile-template-list.v1",
  "templates": [
    {
      "name": "general-basic",
      "description": "General-purpose starter profile for public-facing content."
    },
    {
      "name": "wechat-basic",
      "description": "Basic WeChat article profile with moderate checks."
    },
    {
      "name": "wechat-strict",
      "description": "Stricter WeChat profile intended for batch checks and CI gates."
    }
  ]
}
```

The JSON output should not include full YAML template content by default.

Reason:

* `profile list` is for discovery.
* Full YAML content can be generated through `profile init`.
* Avoid large JSON output and duplicated profile content.

## Exit Code Rules

Use the existing CLI command policy:

```text
0 = command completed successfully
2 = invalid option, unsupported output format, or unexpected command error
```

Do not use exit code `1`.

Reason:

* Exit code `1` is reserved for quality gate failure.
* `profile list` has no review findings or quality gate behavior.

## Command Examples

List templates:

```bash
content-review profile list
```

List templates as JSON:

```bash
content-review profile list --format json
```

Create a profile after listing templates:

```bash
content-review profile init --template wechat-basic --output profiles/my-wechat.yaml
```

Validate the generated profile:

```bash
content-review profile validate profiles/my-wechat.yaml
```

Use the generated profile:

```bash
content-review review article.md --profile profiles/my-wechat.yaml
```

Use the generated profile in batch mode:

```bash
content-review batch articles --profile profiles/my-wechat.yaml --recursive --fail-on error
```

## Relationship With profile init

`profile list` and `profile init` must use the same template registry.

The following should always be true:

```text
Every template shown by `profile list` can be used by `profile init`.
```

Example:

```bash
content-review profile list
content-review profile init --template wechat-basic --output profile.yaml
```

If a template appears in `profile list`, this command should work:

```bash
content-review profile init --template <listed_template_name> --output profile.yaml
```

## Validation Behavior

`profile list` itself does not validate generated files.

However, tests should ensure that every listed template can be generated and loaded by the existing profile loader.

Suggested invariant:

```text
For every template returned by list_profile_templates():
  - get_profile_template(template.name) succeeds
  - generated YAML can be loaded by load_profile()
```

## Help Output

The command should be visible in help output:

```bash
content-review profile --help
content-review profile list --help
```

The help text should clearly explain:

```text
List available built-in profile templates.
```

The help text should mention:

```text
--format
```

if `--format` is supported.

## Documentation Updates

Update `docs/CLI.md` with:

```bash
content-review profile list
content-review profile list --format json
```

Also show the complete workflow:

```bash
content-review profile list
content-review profile init --template wechat-basic --output profiles/my-wechat.yaml
content-review profile validate profiles/my-wechat.yaml
content-review batch articles --profile profiles/my-wechat.yaml --recursive --fail-on error
```

Update `docs/PROFILES.md` with:

1. How to list available templates.
2. How `profile list` relates to `profile init`.
3. Available built-in templates.
4. Template descriptions.
5. Reminder that generated profiles are starting points.
6. Reminder that profiles do not guarantee compliance.

Important wording:

```text
Built-in templates are examples and starting points. They do not guarantee compliance with any platform policy, legal requirement, advertising regulation, medical content standard, or publishing rule.
```

## Testing Requirements

Add CLI tests for text output.

Suggested cases:

```text
profile list returns exit code 0
profile list text output includes general-basic
profile list text output includes wechat-basic
profile list text output includes wechat-strict
profile list text output includes profile init usage example
```

Add CLI tests for JSON output.

Suggested cases:

```text
profile list --format json returns exit code 0
profile list --format json includes schema_version
profile list --format json includes templates array
profile list --format json includes general-basic
profile list --format json includes wechat-basic
profile list --format json includes wechat-strict
profile list --format json does not include full YAML content
```

Add template registry tests if needed.

Suggested cases:

```text
list_profile_templates returns all supported templates
template names are sorted deterministically
every listed template can be retrieved
every listed template has a non-empty description
every listed template content can be loaded as a valid profile
```

Add consistency tests between `profile list` and `profile init`.

Suggested cases:

```text
every listed template can be used with profile init
profile init generated file from each listed template passes load_profile
```

Add help tests if current CLI test style supports them.

Suggested cases:

```text
content-review profile --help includes list
content-review profile list --help includes format
```

## Sorting Rules

Template list output should be deterministic.

Recommended order:

```text
general-basic
wechat-basic
wechat-strict
```

Either preserve registry order or sort by template name.

Tests should not be flaky.

## Backward Compatibility

This task must preserve existing behavior for:

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

1. `content-review profile list` exists.
2. `content-review profile list --format text` works.
3. `content-review profile list --format json` works.
4. Text output lists `general-basic`.
5. Text output lists `wechat-basic`.
6. Text output lists `wechat-strict`.
7. JSON output includes `schema_version`.
8. JSON output includes a `templates` array.
9. JSON output includes template names and descriptions.
10. JSON output does not include full YAML template content.
11. Template list comes from the same registry used by `profile init`.
12. Every listed template can be used by `profile init`.
13. Every listed template generates a valid profile.
14. Help output includes the new command.
15. Documentation is updated.
16. `PROJECT_STATE.md` is updated.
17. `CHANGELOG.md` is updated.
18. Existing tests still pass.
19. `uv run pytest` passes.

## Suggested Test Command

```bash
uv run pytest
```

## Implementation Notes

Recommended implementation order:

1. Inspect `profile init` implementation from TASK-0021.
2. Inspect `src/content_review_engine/config/templates.py`.
3. Extend the template registry with descriptions if needed.
4. Add or update `list_profile_templates()`.
5. Add `profile list` under the existing `profile` command group.
6. Add text output.
7. Add JSON output.
8. Ensure deterministic template ordering.
9. Add CLI text output tests.
10. Add CLI JSON output tests.
11. Add template registry consistency tests if appropriate.
12. Add help output tests.
13. Update `docs/CLI.md`.
14. Update `docs/PROFILES.md`.
15. Update `PROJECT_STATE.md`.
16. Update `CHANGELOG.md`.
17. Run the full test suite.

