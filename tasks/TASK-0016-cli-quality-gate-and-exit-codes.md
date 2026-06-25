# TASK-0016: Add CLI Quality Gate and Exit Codes

## Status

Planned

## Goal

Add quality-gate behavior to the CLI so review results can control process exit codes.

After this task, both `content-review review` and `content-review batch` should be usable in CI, publishing scripts, and automated content workflows.

The CLI should be able to fail when findings at or above a configured severity threshold are detected.

## Background

TASK-0015 added batch review support:

* `content-review batch <input_dir> --profile <profile_path>`
* Deterministic Markdown file discovery
* Batch summary model
* Text / JSON / Markdown output support
* Aggregate severity counts

However, the command currently only reports findings. It does not provide a reliable way for automation systems to decide whether the review should pass or fail.

This task adds a small but important automation layer:

* Quality gate
* Severity threshold comparison
* CI-friendly exit codes

After this task, the review engine can be used not only as a reporting tool, but also as a publishing gate.

## Scope

This task includes:

1. Add `--fail-on <severity>` option to the `review` command.
2. Add `--fail-on <severity>` option to the `batch` command.
3. Define canonical severity ordering.
4. Return non-zero exit code when findings meet or exceed the configured threshold.
5. Keep existing output behavior stable.
6. Add tests for exit-code behavior.
7. Update CLI documentation.
8. Update `PROJECT_STATE.md`.
9. Update `CHANGELOG.md`.

## Non-goals

This task must not implement:

* New content review rules
* LLM-based review
* Auto-fix behavior
* Inline suppressions
* `.gitignore` support
* API server
* MCP server
* Frontend UI
* Database persistence
* Authentication
* Rule marketplace
* Publishing integration

## CLI Design

### Single File Review

Command example:

```bash
content-review review article.md --profile profile.yaml --fail-on error
```

Expected behavior:

* If no finding has severity `error` or `critical`, exit with code `0`.
* If at least one finding has severity `error` or `critical`, exit with code `1`.
* If command input is invalid, exit with code `2`.

### Batch Review

Command example:

```bash
content-review batch ./articles --profile profile.yaml --fail-on critical
```

Expected behavior:

* If no file contains `critical` findings, exit with code `0`.
* If at least one file contains `critical` findings, exit with code `1`.
* If input directory, profile path, or output path is invalid, exit with code `2`.

## Severity Ordering

The canonical severity order should be:

```text
info < warning < error < critical
```

Allowed severity values:

```text
info
warning
error
critical
```

Severity comparison examples:

```python
severity_meets_threshold("critical", "error") == True
severity_meets_threshold("error", "error") == True
severity_meets_threshold("warning", "error") == False
severity_meets_threshold("info", "warning") == False
```

## Exit Code Rules

Use the following exit code policy:

```text
0 = command completed and quality gate passed
1 = command completed but quality gate failed
2 = command failed because of invalid input, invalid profile, file error, or unexpected runtime error
```

The intended behavior is:

* Exit code `0`: safe for automation to continue.
* Exit code `1`: review completed successfully, but findings violated the configured threshold.
* Exit code `2`: command itself failed and should be treated as an operational error.

## Output Behavior

The existing output formats should remain supported:

```bash
--format text
--format json
--format markdown
```

The task should avoid changing the batch JSON schema unless strictly necessary.

For text and markdown output, it is acceptable to add a short quality-gate summary at the end, for example:

```text
Quality Gate: failed
Fail On: error
Matched Findings: 3
Exit Code: 1
```

For JSON output, prefer keeping the existing serialized review result stable.

Recommended approach:

* Keep `ReviewResult` and `BatchReviewResult` schemas stable.
* Compute quality-gate status in the CLI layer.
* Do not modify `BatchReviewResult` unless there is a strong reason.
* If JSON output needs gate information, document the schema change clearly.

## Suggested Internal Design

Add a small helper module if appropriate:

```text
src/content_review_engine/core/quality_gate.py
```

Suggested functions:

```python
def severity_rank(severity: str) -> int:
    """Return the numeric rank for a canonical severity value."""
    ...


def severity_meets_threshold(severity: str, threshold: str) -> bool:
    """Return whether severity is greater than or equal to threshold."""
    ...


def count_findings_at_or_above(
    severity_counts: dict[str, int],
    threshold: str,
) -> int:
    """Count findings whose severity meets or exceeds threshold."""
    ...


def quality_gate_failed(
    severity_counts: dict[str, int],
    threshold: str | None,
) -> bool:
    """Return whether the configured quality gate should fail."""
    ...
```

The CLI should call these helpers instead of hardcoding severity comparisons in command handlers.

## Validation Rules

The CLI should reject invalid severity values.

Invalid example:

```bash
content-review batch ./articles --profile profile.yaml --fail-on high
```

Expected behavior:

* Show a clear CLI error.
* Exit with code `2`.
* Do not silently map `high` to another severity value.

Valid values are only:

```text
info
warning
error
critical
```

## Review Command Requirements

The `review` command should support:

```bash
content-review review article.md --profile profile.yaml --fail-on warning
```

Behavior:

* Run the existing single-file review pipeline.
* Render output using the selected output format.
* Evaluate findings against the `--fail-on` threshold.
* Exit with code `1` if any finding meets or exceeds the threshold.
* Exit with code `0` otherwise.

If `--fail-on` is not provided, the command should preserve the current behavior and return `0` when the command succeeds.

## Batch Command Requirements

The `batch` command should support:

```bash
content-review batch ./articles --profile profile.yaml --fail-on error
```

Behavior:

* Run the existing batch review pipeline.
* Render output using the selected output format.
* Evaluate aggregate severity counts against the `--fail-on` threshold.
* Exit with code `1` if any finding meets or exceeds the threshold.
* Exit with code `0` otherwise.

If `--fail-on` is not provided, the command should preserve the current behavior and return `0` when the command succeeds.

## Testing Requirements

Add tests for the quality-gate helper.

Example test cases:

```text
info vs warning => false
warning vs warning => true
error vs warning => true
critical vs error => true
warning vs error => false
critical vs critical => true
info vs info => true
```

Add CLI tests for the `review` command:

```text
review command exits 0 when no finding meets threshold
review command exits 1 when finding meets threshold
review command rejects invalid --fail-on value
review command preserves existing behavior when --fail-on is omitted
```

Add CLI tests for the `batch` command:

```text
batch command exits 0 when severity_counts are below threshold
batch command exits 1 when severity_counts meet threshold
batch command exits 2 for invalid threshold
batch command preserves existing behavior when --fail-on is omitted
```

If the current CLI test structure makes direct exit-code testing difficult, add focused tests around the helper first and add minimal CLI integration tests.

## Documentation Updates

Update CLI documentation to include examples:

```bash
content-review review article.md --profile profile.yaml --fail-on error
content-review batch ./articles --profile profile.yaml --fail-on warning
```

Explain the exit codes:

```text
0 = passed
1 = quality gate failed
2 = command error
```

Update `PROJECT_STATE.md` with:

* TASK-0016 completed
* Quality gate support added
* CLI now supports automation-friendly exit codes

Update `CHANGELOG.md` with:

* Added `--fail-on` option
* Added severity threshold comparison
* Added CI-friendly exit-code behavior

## Acceptance Criteria

This task is complete when:

1. `content-review review` supports `--fail-on`.
2. `content-review batch` supports `--fail-on`.
3. Severity threshold comparison is centralized and tested.
4. Commands return exit code `1` when findings meet or exceed the threshold.
5. Commands return exit code `0` when the quality gate passes.
6. Commands return exit code `2` for invalid severity values or command errors.
7. Existing text / JSON / Markdown output behavior remains compatible.
8. Existing tests still pass.
9. New quality-gate tests pass.
10. `PROJECT_STATE.md` is updated.
11. `CHANGELOG.md` is updated.

## Suggested Test Command

```bash
uv run pytest
```

## Implementation Notes

Recommended implementation order:

1. Inspect current CLI command implementation.
2. Inspect current severity representation in data models.
3. Add `core/quality_gate.py`.
4. Add unit tests for severity comparison.
5. Add `--fail-on` to `review`.
6. Add `--fail-on` to `batch`.
7. Add CLI integration tests.
8. Update docs, `PROJECT_STATE.md`, and `CHANGELOG.md`.
9. Run the full test suite.
