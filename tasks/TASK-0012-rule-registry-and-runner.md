
# TASK-0012: Add Rule Registry and Rule Runner

## 1. Task Title

`TASK-0012: Add Rule Registry and Rule Runner`

## 2. Task Status

Draft

## 3. Depends On

This task depends on:

* `TASK-0005: Add Minimal Review Pipeline`
* `TASK-0007: Add Finding Location and Context Snippets`
* `TASK-0008: Add Markdown Review Report Export`
* `TASK-0010: Enable Packaged CLI Entrypoint`
* `TASK-0011: Stabilize ReviewResult Model and JSON Schema`

Do not start this task unless TASK0011 has been completed and the existing test suite passes.

## 4. Goal

Add a minimal rule registry and rule runner so review rules are no longer hardcoded directly inside the review pipeline.

After this task, the project should have a small rule execution layer that can:

1. Register review rules by rule ID.
2. Retrieve a rule by rule ID.
3. Run enabled rules against Markdown text.
4. Return a combined list of `ReviewFinding` objects.
5. Keep `review_document()` returning the canonical `ReviewResult`.
6. Preserve current forbidden-terms behavior.
7. Prepare the project for future rule types without adding those rule types now.

This task should make the rule system extensible while keeping the current deterministic review behavior unchanged.

## 5. Background

Before TASK0012, the project already supports:

* Reading Markdown files.
* Loading `ReviewProfile`.
* Running the minimal review pipeline.
* Running the forbidden-terms rule.
* Returning canonical `ReviewResult`.
* Serializing `ReviewResult` to JSON.
* Rendering Markdown reports.
* Running the packaged `content-review` CLI.

However, the review pipeline still has a limited rule execution structure.

As the project grows, future rules may include:

* Markdown heading structure checks.
* Forbidden terms.
* Absolute claim checks.
* Platform-specific checks.
* Citation/evidence checks.
* Risk-domain checks.
* Future LLM-assisted review rules.

Before adding these new rule categories, the project should first have a clean rule registry and rule runner.

TASK0012 adds that foundation.

## 6. Non-Goals

This task must not implement any of the following:

* New review rules.
* New forbidden terms behavior.
* LLM-based review.
* Automatic rewriting.
* Diff tracking.
* Markdown auto-fix.
* Batch review.
* Watch mode.
* MCP server.
* REST API.
* GUI.
* Database persistence.
* HTML/PDF report generation.
* Full plugin system.
* Dynamic third-party rule loading.
* Remote rule loading.
* Rule marketplace.
* Complex dependency injection framework.

This task is only about introducing a minimal internal rule registry and rule runner.

## 7. Required Reading Before Coding

Before making any code changes, read:

```text
AGENTS.md
PROJECT_STATE.md
ROADMAP.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
docs/REPORTS.md
docs/TESTING.md
docs/schemas/review-result.schema.json
pyproject.toml
tasks/TASK-0010-enable-packaged-cli-entrypoint.md
tasks/TASK-0011-stabilize-review-result-and-json-schema.md
tasks/TASK-0012-rule-registry-and-runner.md
```

If older task files such as TASK0003-TASK0006 are missing, do not recreate them in this task.

Instead:

1. Inspect the current implementation.
2. Use existing docs, tests, fixtures, and project state as the source of truth.
3. Mention missing historical task files in the final task summary only if relevant.

## 8. Allowed Scope

This task may modify or add files related to rule registration, rule execution, pipeline integration, tests, and documentation.

Likely allowed files:

```text
src/content_review_engine/core/models.py
src/content_review_engine/review/pipeline.py
src/content_review_engine/rules/__init__.py
src/content_review_engine/rules/base.py
src/content_review_engine/rules/registry.py
src/content_review_engine/rules/runner.py
src/content_review_engine/rules/forbidden_terms.py
tests/test_rule_registry.py
tests/test_rule_runner.py
tests/test_review_pipeline.py
tests/test_cli.py
docs/ARCHITECTURE.md
docs/RULES.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

If the current repository already has an equivalent rules module structure, follow the existing structure instead of creating duplicate modules.

## 9. Forbidden Scope

Do not change the canonical `ReviewResult` contract.

Do not change `ReviewFinding` semantics.

Do not change `SourceSpan` semantics.

Do not change forbidden-term matching behavior.

Do not introduce new rule categories.

Do not add new third-party dependencies.

Do not rewrite the CLI.

Do not rewrite the report renderer.

Do not add plugin loading from external files.

Do not load Python modules dynamically from user-provided paths.

Do not add async execution.

Do not add parallel execution.

The rule registry should remain simple, deterministic, and internal.

## 10. Rule Interface Requirements

Add a minimal internal rule interface.

Preferred approach:

```python
from typing import Protocol

class ReviewRule(Protocol):
    rule_id: str

    def evaluate(self, text: str, profile: ReviewProfile) -> list[ReviewFinding]:
        ...
```

Alternative acceptable approach:

```python
@dataclass
class RuleDefinition:
    rule_id: str
    evaluate: Callable[[str, ReviewProfile], list[ReviewFinding]]
```

Choose the simplest approach that fits the current codebase.

Requirements:

1. Every rule must have a stable `rule_id`.
2. Every rule must return `list[ReviewFinding]`.
3. Rules should not create `ReviewResult` directly.
4. Rules should not write files.
5. Rules should not print CLI output.
6. Rules should not know about report rendering.
7. Rules should be deterministic.

## 11. Rule Registry Requirements

Add a small `RuleRegistry`.

Preferred module:

```text
src/content_review_engine/rules/registry.py
```

Suggested behavior:

```python
class RuleRegistry:
    def register(self, rule: ReviewRule) -> None:
        ...

    def get(self, rule_id: str) -> ReviewRule:
        ...

    def has(self, rule_id: str) -> bool:
        ...

    def list_rule_ids(self) -> list[str]:
        ...
```

Requirements:

1. Register rules by `rule_id`.
2. Reject duplicate rule IDs.
3. Raise a clear error for unknown rule IDs.
4. Preserve deterministic rule order.
5. Provide a default registry that includes the existing forbidden-terms rule.
6. Do not load rules from external packages.
7. Do not discover rules dynamically from the file system.

Suggested helper:

```python
def build_default_rule_registry() -> RuleRegistry:
    ...
```

The default registry should include:

```text
forbidden_terms
```

or whatever canonical rule ID is currently used by the existing forbidden-terms rule.

## 12. Rule Runner Requirements

Add a small rule runner.

Preferred module:

```text
src/content_review_engine/rules/runner.py
```

Suggested function:

```python
def run_rules(
    text: str,
    profile: ReviewProfile,
    *,
    registry: RuleRegistry | None = None,
) -> list[ReviewFinding]:
    ...
```

Requirements:

1. Use the default registry when no registry is provided.
2. Determine which rules are enabled for the current profile.
3. Run enabled rules in deterministic order.
4. Combine findings from all executed rules.
5. Return only `list[ReviewFinding]`.
6. Do not construct `ReviewResult`.
7. Do not serialize output.
8. Do not render Markdown reports.

## 13. ReviewProfile Integration Requirements

Use the current `ReviewProfile` structure as the source of truth.

If the existing profile schema already has enabled rules, rule IDs, or rule configuration fields, use them.

If the existing profile schema does not yet support explicit rule selection, preserve current behavior by running the default forbidden-terms rule.

Do not invent a large new profile schema in this task.

A minimal addition is acceptable only if necessary, such as:

```python
enabled_rules: list[str] | None = None
```

If such a field is added:

1. Default behavior must remain backward compatible.
2. Existing profile fixtures must continue to work.
3. Documentation must explain the field.
4. Tests must cover both default and explicit rule selection.

## 14. Unknown Rule Behavior

If a profile explicitly references an unknown rule ID, the rule runner should fail clearly.

Preferred exception:

```python
class UnknownRuleError(ValueError):
    ...
```

Requirements:

1. Unknown rule errors should be human-readable.
2. CLI should convert expected unknown rule errors into exit code `2`.
3. Unit tests should cover unknown rule behavior.

If CLI error handling currently has a centralized expected-error path, use it.

Do not expose a long traceback for normal user configuration errors.

## 15. Duplicate Rule Behavior

If a duplicate rule ID is registered, the registry should fail clearly.

Preferred exception:

```python
class DuplicateRuleError(ValueError):
    ...
```

Tests should verify duplicate registration fails.

## 16. Forbidden Terms Rule Integration

Adapt the existing forbidden-terms rule to fit the new rule interface.

Requirements:

1. Keep the current rule ID.
2. Preserve current matching behavior.
3. Preserve current finding messages.
4. Preserve current severity behavior.
5. Preserve current location/context behavior.
6. Preserve current tests unless they are updated only for the new abstraction.
7. Do not add new forbidden terms.
8. Do not change how many matches are reported.

This task should change how the rule is called, not what the rule detects.

## 17. Review Pipeline Requirements

Update the review pipeline so it uses the rule runner.

Expected flow:

```text
review_document(markdown_text, profile)
→ run_rules(markdown_text, profile)
→ ReviewResult.from_findings(...)
→ return ReviewResult
```

The pipeline should still return the canonical `ReviewResult` introduced in TASK0011.

Do not move summary construction into the rule runner.

Do not make the rule registry responsible for `ReviewResult`.

## 18. CLI Requirements

The CLI should continue to work exactly as before from the user perspective.

The following commands must still work:

```bash
uv run content-review --help
uv run content-review review examples/article.md --profile examples/profile.yml --format text
uv run content-review review examples/article.md --profile examples/profile.yml --format json
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output /tmp/content-review-example-report.md
```

If a profile explicitly references an unknown rule, the CLI should:

1. Return exit code `2`.
2. Print a readable error message to stderr.
3. Not print a traceback for the expected user error.

## 19. Tests Required

Add or update tests for the rule registry and runner.

### 19.1 Rule Registry Registration Test

Given a test rule.

When it is registered.

Then:

* The registry can retrieve it by rule ID.
* `has(rule_id)` returns true.
* `list_rule_ids()` includes the rule ID.

### 19.2 Duplicate Rule ID Test

Given two rules with the same rule ID.

When registering both.

Then:

* The second registration raises a duplicate rule error.

### 19.3 Unknown Rule Test

Given an unknown rule ID.

When retrieving it.

Then:

* The registry raises an unknown rule error.

### 19.4 Default Registry Test

When building the default registry.

Then:

* The forbidden-terms rule is present.
* The rule ID matches the current canonical forbidden-terms rule ID.

### 19.5 Rule Runner Default Behavior Test

Given Markdown containing configured forbidden terms.

When running rules with the default registry.

Then:

* Findings are returned.
* Existing forbidden-term behavior is preserved.

### 19.6 Rule Runner Explicit Rule Selection Test

If profile-level rule selection is supported:

Given a profile with explicit enabled rule IDs.

Then:

* Only the selected rules are run.

If profile-level rule selection is not added in this task, skip this test and document that rule selection remains default-only.

### 19.7 Review Pipeline Integration Test

Given Markdown with forbidden terms.

When calling `review_document()`.

Then:

* It returns canonical `ReviewResult`.
* Findings are produced through the rule runner.
* Summary is still correct.

### 19.8 CLI Regression Test

Existing CLI tests should continue to pass.

If unknown rule configuration is supported, add a CLI test showing:

* Exit code `2`.
* Readable unknown rule message.

## 20. Documentation Required

Add or update:

```text
docs/RULES.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
PROJECT_STATE.md
CHANGELOG.md
```

### 20.1 `docs/RULES.md`

Add a new rules documentation file.

It should explain:

1. What a review rule is.
2. What `rule_id` means.
3. What the rule registry does.
4. What the rule runner does.
5. How the default registry works.
6. That the current default registry only includes the deterministic forbidden-terms rule.
7. How future rules should be added.
8. Current limitations.

### 20.2 `docs/ARCHITECTURE.md`

Update architecture docs to show:

```text
Markdown input
→ ReviewProfile
→ RuleRunner
→ RuleRegistry
→ ReviewFinding[]
→ ReviewResult
→ CLI JSON / Markdown report
```

Keep this update minimal.

### 20.3 `docs/DATA_MODELS.md`

Update only if `ReviewProfile` gains rule-selection fields or if rule-related models/exceptions are documented there.

Do not duplicate all of `docs/RULES.md`.

### 20.4 `docs/CLI.md`

Update only if CLI behavior changes for rule configuration errors.

If user-facing CLI behavior does not change, mention that CLI still runs the default configured rule set through the internal rule runner.

## 21. PROJECT_STATE Update

Update `PROJECT_STATE.md`.

Mention:

* TASK0012 completed.
* Rule registry added.
* Rule runner added.
* Existing forbidden-terms rule is now executed through the rule runner.
* Review pipeline still returns canonical `ReviewResult`.
* CLI behavior remains backward compatible.
* No new review rules were added.
* No LLM, rewrite, batch, API, MCP, GUI, or database support was added.

## 22. CHANGELOG Update

Update `CHANGELOG.md`.

Suggested entry:

```markdown
## TASK-0012

### Added

- Added internal rule registry for deterministic review rules.
- Added rule runner for executing registered rules.
- Added default rule registry containing the existing forbidden-terms rule.
- Added tests for rule registration, duplicate rules, unknown rules, default registry behavior, and rule runner integration.
- Added rules documentation.

### Changed

- Updated the review pipeline to execute rules through the rule runner.
- Preserved canonical `ReviewResult` output.
- Preserved existing forbidden-terms behavior.
- Updated architecture documentation.

### Not Added

- No new review rules.
- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No batch review.
- No MCP server.
- No REST API.
- No GUI.
- No database persistence.
```

## 23. Validation Commands

After implementation, run:

```bash
uv sync
uv run pytest
```

Run manual CLI smoke tests:

```bash
uv run content-review --help
uv run content-review review examples/article.md --profile examples/profile.yml --format text
uv run content-review review examples/article.md --profile examples/profile.yml --format json
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output /tmp/content-review-example-report.md
```

Do not commit files under `/tmp`.

If the project has a check-state script, run it as well.

## 24. Completion Criteria

This task is complete only when:

* A rule interface or equivalent rule definition exists.
* A `RuleRegistry` exists.
* Duplicate rule IDs fail clearly.
* Unknown rule IDs fail clearly.
* A default registry exists.
* The default registry includes the existing forbidden-terms rule.
* A rule runner exists.
* The review pipeline uses the rule runner.
* The review pipeline still returns canonical `ReviewResult`.
* Existing CLI behavior still works.
* Existing forbidden-terms behavior is preserved.
* Tests are added or updated.
* `uv run pytest` passes.
* Manual CLI smoke tests pass.
* `docs/RULES.md` is added.
* `docs/ARCHITECTURE.md` is updated.
* `PROJECT_STATE.md` is updated.
* `CHANGELOG.md` is updated.
* No out-of-scope features are implemented.

## 25. Known Limitations To Preserve

Do not try to solve these in TASK0012:

* No external plugin system.
* No dynamic rule discovery.
* No third-party rule packages.
* No LLM rules.
* No rule dependency graph.
* No rule execution priority system beyond deterministic registration order.
* No parallel rule execution.
* No batch review.
* No API/MCP integration.
* No GUI rule management.
* No runtime rule editor.

## 26. Final Agent Response Requirements

When the Agent finishes this task, it must report:

1. Files changed.
2. Rule interface or rule definition added.
3. Rule registry behavior.
4. Rule runner behavior.
5. How the forbidden-terms rule was integrated.
6. How the review pipeline now uses the rule runner.
7. Whether CLI behavior changed.
8. Tests added or updated.
9. Result of `uv sync`.
10. Result of `uv run pytest`.
11. Manual CLI smoke test results.
12. Whether `docs/RULES.md` was added.
13. Whether `docs/ARCHITECTURE.md` was updated.
14. Whether `PROJECT_STATE.md` was updated.
15. Whether `CHANGELOG.md` was updated.
16. Known limitations.

The final response must be concise and must not claim unsupported functionality.
