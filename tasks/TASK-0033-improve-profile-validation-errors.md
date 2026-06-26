# TASK-0033: Improve Profile Validation Errors

## Status

Planned

## Goal

Improve profile validation errors so users can understand exactly what is wrong in a review profile and how to fix it.

The project now supports real-world profile templates and configurable `regex_rules`. Users are expected to customize profiles. TASK-0033 should make profile validation errors structured, readable, actionable, and suitable for future API / GUI usage.

This task improves validation UX. It must not add new review rules or LLM review.

## Background

The project currently supports:

* review profile loading
* profile validation
* built-in deterministic rules
* `regex_rules`
* real-world profile templates
* profile template initialization
* demo profiles
* CLI command: `content-review profile validate`

As profile configuration becomes more powerful, users can make common mistakes such as:

```yaml
regex_rules:
  - id: 123_rule
    pattern: "["
    severity: warn
    message: ""
```

The current validation may detect these errors, but the next step is to make errors more helpful.

Ideal validation output should answer:

```text
Where is the error?
What kind of error is it?
Why is it invalid?
How can the user fix it?
```

Example target direction:

```text
Profile validation failed: profiles/wechat.yaml

1. regex_rules[0].id
   Code: invalid_rule_id
   Error: Rule ID must match ^[a-z][a-z0-9_]*$.
   Suggestion: Use a lowercase snake_case ID, such as exaggerated_claims.

2. regex_rules[0].pattern
   Code: invalid_regex_pattern
   Error: Invalid regex pattern: unterminated character set.
   Suggestion: Check the regex syntax or escape special characters.
```

## Scope

This task may modify:

* profile validation code
* profile loading error handling
* CLI rendering for `profile validate`
* tests for invalid profiles
* docs for profile validation
* Quickstart if needed
* CLI docs if needed
* demo docs if needed
* `PROJECT_STATE.md`
* `CHANGELOG.md`

Likely files to inspect:

```text
src/content_review_engine/config/validation.py
src/content_review_engine/config/templates.py
src/content_review_engine/core/models.py
src/content_review_engine/cli.py
tests/test_cli.py
tests/test_regex_rules.py
tests/test_profile_templates.py
tests/test_example_profiles.py
tests/test_quickstart_docs.py
docs/PROFILES.md
docs/CLI.md
docs/QUICKSTART.md
README.md
PROJECT_STATE.md
CHANGELOG.md
```

Exact paths should be confirmed from the repository.

## Non-goals

This task must not:

* add new review rule types
* change `regex_rules` matching behavior
* change built-in rule behavior
* change suppression behavior
* change quality gate semantics
* change Markdown report structure
* change JSON review output schema
* change batch review behavior
* add LLM review
* add PydanticAI
* add API endpoints
* add MCP support
* add GUI support
* change profile template semantics
* remove legacy profile compatibility
* introduce compliance guarantees

## Required Work

### 1. Inspect Current Validation Flow

Before making changes, inspect the current profile validation flow.

Identify:

* how profile YAML is loaded
* how model validation errors are raised
* how invalid severity is handled
* how invalid regex pattern is handled
* how duplicate regex rule IDs are handled
* how invalid regex rule IDs are handled
* how `content-review profile validate` renders success and failure
* what exit codes are currently used

Do not change exit code semantics.

### 2. Add Structured Validation Issue Model

Add a small structured validation issue model.

Suggested name:

```python
ProfileValidationIssue
```

Suggested fields:

```python
path: str
code: str
message: str
suggestion: str | None = None
```

Optional fields if useful:

```python
severity: str = "error"
details: str | None = None
```

Suggested location:

```text
src/content_review_engine/config/validation.py
```

or another existing validation module if more appropriate.

The model should be simple and deterministic.

### 3. Add Validation Error Container

Add a container exception or result type for multiple validation issues.

Suggested name:

```python
ProfileValidationError
```

It should contain:

```python
issues: tuple[ProfileValidationIssue, ...]
```

Behavior:

* preserve all collected issues where practical
* render readable text for CLI usage
* avoid Python tracebacks for normal user input errors
* keep existing exit code behavior for validation failure

If the project already has a validation exception type, extend it instead of adding a duplicate concept.

### 4. Improve Regex Rule Validation Errors

Improve validation messages for `regex_rules`.

At minimum, cover:

#### Invalid rule ID

Example:

```yaml
regex_rules:
  - id: 123_rule
    pattern: "test"
    severity: warning
    message: "Test."
```

Expected issue direction:

```text
path: regex_rules[0].id
code: invalid_rule_id
message: Rule ID must match the configured rule ID convention.
suggestion: Use lowercase snake_case, such as custom_rule.
```

#### Duplicate rule ID

Example:

```yaml
regex_rules:
  - id: repeated_rule
    pattern: "foo"
    severity: warning
    message: "Foo."

  - id: repeated_rule
    pattern: "bar"
    severity: warning
    message: "Bar."
```

Expected issue direction:

```text
path: regex_rules[1].id
code: duplicate_rule_id
message: Duplicate regex rule ID: repeated_rule.
suggestion: Use a unique ID for each regex rule.
```

#### Invalid regex pattern

Example:

```yaml
regex_rules:
  - id: broken_regex
    pattern: "["
    severity: warning
    message: "Broken regex."
```

Expected issue direction:

```text
path: regex_rules[0].pattern
code: invalid_regex_pattern
message: Invalid regex pattern: unterminated character set.
suggestion: Check the regex syntax or escape special characters.
```

#### Missing or empty message

Example:

```yaml
regex_rules:
  - id: missing_message
    pattern: "foo"
    severity: warning
    message: ""
```

Expected issue direction:

```text
path: regex_rules[0].message
code: missing_message
message: Regex rule message must not be empty.
suggestion: Add a concise explanation shown when the rule matches.
```

#### Invalid case sensitivity value

Example:

```yaml
regex_rules:
  - id: bad_case_sensitive
    pattern: "foo"
    severity: warning
    message: "Foo."
    case_sensitive: maybe
```

Expected issue direction:

```text
path: regex_rules[0].case_sensitive
code: invalid_boolean
message: case_sensitive must be true or false.
suggestion: Use true for case-sensitive matching or false for case-insensitive matching.
```

### 5. Improve Severity Validation Errors

Improve invalid severity errors.

Example:

```yaml
regex_rules:
  - id: invalid_severity
    pattern: "foo"
    severity: warn
    message: "Foo."
```

Expected issue direction:

```text
path: regex_rules[0].severity
code: invalid_severity
message: Unknown severity: warn.
suggestion: Use one of: critical, error, warning, info.
```

Do not change the canonical severity values.

### 6. Improve YAML Parse Error Handling

If the YAML file itself is invalid, render a user-friendly error.

Example:

```yaml
regex_rules:
  - id: broken
    pattern: "foo"
      severity: warning
```

Expected direction:

```text
path: <yaml>
code: invalid_yaml
message: Failed to parse YAML profile.
suggestion: Check indentation, quoting, and list structure.
```

Include the original parser message if available.

### 7. Improve Unknown Or Malformed Section Errors If Supported

If the current validation already detects unknown sections or malformed profile sections, render them through the structured issue model.

Examples:

```text
path: regex_rules
code: invalid_section_type
message: regex_rules must be a list.
suggestion: Use a YAML list of regex rule objects.
```

Do not introduce strict rejection of unknown fields unless the project already does so.

If unknown fields are currently tolerated, keep that behavior.

### 8. CLI Output For `profile validate`

Update `content-review profile validate` failure output to render structured issues.

Requirements:

* include profile path
* include total issue count
* list each issue with path, code, message, and suggestion if present
* keep output stable and readable
* do not print traceback for normal validation failures
* keep success output behavior unless a small wording improvement is needed
* keep exit code semantics unchanged

Suggested output:

```text
Profile validation failed: profiles/wechat.yaml
Issues: 3

1. regex_rules[0].id
   Code: invalid_rule_id
   Error: Rule ID must match ^[a-z][a-z0-9_]*$.
   Suggestion: Use lowercase snake_case, such as exaggerated_claims.

2. regex_rules[0].pattern
   Code: invalid_regex_pattern
   Error: Invalid regex pattern: unterminated character set.
   Suggestion: Check the regex syntax or escape special characters.

3. regex_rules[0].severity
   Code: invalid_severity
   Error: Unknown severity: warn.
   Suggestion: Use one of: critical, error, warning, info.
```

### 9. Preserve Review Command Error Behavior

Review and batch commands that load invalid profiles should also avoid tracebacks for normal validation errors.

If possible, reuse the same rendering helper.

Do not change review or batch exit code semantics.

### 10. Add Invalid Profile Fixtures

Add invalid profile fixtures for tests.

Suggested directory:

```text
tests/fixtures/profiles/invalid/
```

Suggested files:

```text
invalid-regex-pattern.yaml
invalid-regex-id.yaml
duplicate-regex-id.yaml
invalid-severity.yaml
empty-regex-message.yaml
invalid-case-sensitive.yaml
invalid-yaml.yaml
```

Use repository conventions if a fixture directory already exists.

Keep fixtures small.

### 11. Add Tests For Structured Validation

Add tests for the structured validation model and error collection.

Suggested file:

```text
tests/test_profile_validation_errors.py
```

Tests should cover:

* invalid regex pattern returns `invalid_regex_pattern`
* invalid regex rule ID returns `invalid_rule_id`
* duplicate regex rule ID returns `duplicate_rule_id`
* invalid severity returns `invalid_severity`
* empty message returns a clear issue
* invalid `case_sensitive` returns a clear issue
* invalid YAML returns `invalid_yaml`
* issue paths are stable
* issue suggestions are present for common errors
* multiple errors can be reported together where practical
* valid profiles still validate successfully

Do not overfit to exact full paragraphs unless necessary.

### 12. Add CLI Tests

Update or add CLI tests for:

```bash
uv run content-review profile validate invalid-profile.yaml
```

Tests should verify:

* validation failure uses the expected exit code
* output includes `Profile validation failed`
* output includes issue count
* output includes path
* output includes code
* output includes suggestion
* no traceback appears

Also test that review command with invalid profile fails cleanly if this behavior is supported.

### 13. Update Documentation

Update:

```text
docs/PROFILES.md
docs/CLI.md
docs/QUICKSTART.md
```

Documentation should explain:

* how to validate a profile
* what structured validation errors look like
* common regex rule mistakes
* common severity mistakes
* how to fix invalid regex patterns
* how to fix duplicate rule IDs
* exit code behavior remains unchanged

Keep docs concise.

### 14. Update README If Appropriate

Update `README.md` only if there is a concise place to mention improved profile validation.

Do not over-expand README.

### 15. Update Project State

Update:

```text
PROJECT_STATE.md
```

Mention:

* TASK-0033 completed
* profile validation errors are structured and more actionable
* regex rule validation errors now include path/code/message/suggestion
* CLI validation output is more readable
* no review behavior changed
* no LLM review was added

### 16. Update Changelog

Update:

```text
CHANGELOG.md
```

Add a TASK-0033 entry describing:

* improved profile validation errors
* added structured issue model
* improved CLI failure output
* added invalid profile fixtures
* added tests
* no runtime review behavior changes

## Acceptance Criteria

TASK-0033 is complete when:

* profile validation can produce structured issues
* each issue has at least path, code, message, and optional suggestion
* regex rule validation errors are user-friendly
* invalid severity errors are user-friendly
* YAML parse errors are user-friendly
* duplicate regex rule IDs are reported clearly
* CLI `profile validate` renders readable validation failures
* normal validation failures do not show tracebacks
* exit code semantics remain unchanged
* valid existing profiles and templates still validate successfully
* invalid profile fixtures are added
* tests cover structured validation errors and CLI rendering
* docs explain validation error output and common fixes
* `PROJECT_STATE.md` is updated
* `CHANGELOG.md` is updated
* all tests pass
* no LLM review is introduced
* no unrelated runtime behavior changes are introduced

## Validation Commands

Run:

```bash
uv run pytest
```

Manual checks:

```bash
uv run content-review profile validate tests/fixtures/profiles/invalid/invalid-regex-pattern.yaml
```

```bash
uv run content-review profile validate tests/fixtures/profiles/invalid/duplicate-regex-id.yaml
```

```bash
uv run content-review review examples/demo/articles/wechat-demo.md \
  --profile tests/fixtures/profiles/invalid/invalid-regex-pattern.yaml
```

Use actual repository paths if different.

