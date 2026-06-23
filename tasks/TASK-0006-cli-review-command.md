# TASK-0006: Add Minimal CLI Review Command

## Status

Planned

## Type

Feature / CLI

## Priority

High

## Depends On

* TASK-0001: Project Skeleton
* TASK-0002: Core Data Models
* TASK-0002.5: Package Import Config
* TASK-0003: Markdown Reader and Profile Loading
* TASK-0004: Forbidden Terms Rule
* TASK-0005: Minimal Review Pipeline

## Precondition

Before starting this task, TASK-0005 must already have a dedicated Git commit.

Expected TASK-0005 commit message:

```bash
feat(task-0005): add minimal review pipeline
```

Do not start implementing TASK-0006 if TASK-0005 changes are still uncommitted.

Before implementation, confirm:

```bash
git status
git log --oneline -5
```

If the working tree contains unrelated changes or TASK-0005 has not been committed, stop and report the issue.

## Background

The project currently has:

* A Markdown reader.
* A YAML profile loader.
* A sample WeChat review profile.
* The first deterministic review rule: `forbidden_terms`.
* A minimal in-memory review pipeline: `review_document()`.
* Unit tests for parser, config, deterministic rule, and review pipeline.

However, the project still does not provide a user-facing command-line entrypoint.

At this stage, users can only call the package from Python code. TASK-0006 adds the first minimal CLI command so the project can review a Markdown file from the terminal.

## Goal

Add a minimal CLI command that can review a Markdown file with a YAML profile.

Target usage:

```bash
content-review review article.md --profile profiles/wechat.yaml
```

The CLI should:

1. Read the Markdown file.
2. Load the YAML review profile.
3. Run the minimal review pipeline.
4. Print a simple human-readable result to stdout.
5. Exit successfully when the review completes.

## Scope

This task includes:

1. Add a CLI module.
2. Add a `review` command.
3. Wire the CLI command to:

   * `read_markdown()`
   * `load_profile()`
   * `review_document()`
4. Add a console script entry in `pyproject.toml`.
5. Add CLI tests.
6. Update architecture documentation.
7. Update project state.
8. Update changelog.
9. Run the full test suite.
10. Create a dedicated Git commit for TASK-0006.

## Non-Goals

This task must not implement:

* LLM-based review
* Prompt templates
* PydanticAI integration
* MCP server
* FastAPI server
* Supabase integration
* Frontend
* Database persistence
* Dynamic rule loading
* Rule registry
* Rule scheduler
* Markdown auto-rewrite
* Markdown AST parsing
* Line and column location tracking
* JSON report export
* HTML report export
* Interactive terminal UI
* Watch mode
* Batch directory review
* Config file discovery
* User authentication
* Remote API calls

These should be handled by future TASK files.

## Expected Files

The implementation may create or modify:

```text
src/content_review_engine/cli.py
tests/test_cli.py
pyproject.toml
docs/ARCHITECTURE.md
PROJECT_STATE.md
CHANGELOG.md
```

The implementation may also update package `__init__.py` files only if necessary for imports.

Do not modify parser, config, rules, or review pipeline code unless a small bug is discovered and required to make the CLI work. If such a bug is found, stop and report it before expanding the task scope.

## CLI Design Requirement

Use the Python standard library unless the project already has a CLI framework dependency.

Recommended approach:

```text
argparse
```

Do not add `typer`, `click`, or other CLI dependencies in this task unless the project already uses them.

## Console Script

Add a console script entry in `pyproject.toml`.

Suggested script name:

```toml
[project.scripts]
content-review = "content_review_engine.cli:main"
```

If `[project.scripts]` already exists, add the new entry without removing existing entries.

## CLI Command

Implement:

```bash
content-review review <markdown_file> --profile <profile_file>
```

Example:

```bash
content-review review article.md --profile profiles/wechat.yaml
```

The command should:

1. Accept a Markdown file path as positional argument.
2. Accept a profile path through `--profile`.
3. Use `read_markdown()` to read Markdown.
4. Use `load_profile()` to load the profile.
5. Use `review_document()` to run the review pipeline.
6. Print a simple review summary to stdout.
7. Return exit code `0` when the command completes successfully.

## CLI Output

The output should be simple and human-readable.

When findings exist, print something similar to:

```text
Review completed.

Findings: 2

[warning] forbidden_terms: 发现风险词：保证赚钱
[warning] forbidden_terms: 发现风险词：100%有效
```

When no findings exist, print something similar to:

```text
Review completed.

Findings: 0

No issues found.
```

The exact wording may follow existing model field names, but the output must include:

* Total finding count
* Rule id
* Severity
* Message

Do not implement JSON output in this task.

## Error Handling

The CLI should rely on existing exceptions where appropriate.

Expected behavior:

1. Missing Markdown file should result in a non-zero exit code.
2. Non-Markdown input should result in a non-zero exit code.
3. Missing profile file should result in a non-zero exit code.
4. Non-YAML profile input should result in a non-zero exit code.
5. Invalid profile schema should result in a non-zero exit code.

For this task, it is acceptable to print a simple error message to stderr.

Do not build a complex error system.

## Main Function

Add a main function similar to:

```python
def main(argv: list[str] | None = None) -> int:
    ...
```

The function should be testable without spawning a subprocess.

Recommended behavior:

1. `main()` returns an integer exit code.
2. `main()` accepts optional `argv`.
3. The console script calls `main()`.
4. Use `raise SystemExit(main())` only under the `if __name__ == "__main__":` guard.

## Tests

Add:

```text
tests/test_cli.py
```

The tests must cover at least the following cases.

### 1. CLI Review With Findings

Given a Markdown file containing a configured forbidden term and a valid YAML profile, running the CLI review command returns exit code `0` and prints at least one finding.

### 2. CLI Review Without Findings

Given a Markdown file with no configured forbidden terms and a valid YAML profile, running the CLI review command returns exit code `0` and prints that there are zero findings.

### 3. CLI Missing Markdown File

Given a missing Markdown path, the CLI returns a non-zero exit code.

### 4. CLI Missing Profile File

Given a missing profile path, the CLI returns a non-zero exit code.

### 5. CLI Help

Running the CLI with `--help` or the review command with `--help` should show usage information.

### 6. Full Test Suite

Run:

```bash
uv run pytest
```

All tests must pass.

## Documentation Updates

Update:

```text
docs/ARCHITECTURE.md
```

Add the CLI layer to the architecture.

Suggested architecture description:

```text
CLI
 ↓
Markdown Reader
 ↓
Profile Loader
 ↓
Review Pipeline
 ↓
Deterministic Rules
 ↓
Review Result
```

Mention that the current CLI only supports reviewing one Markdown file with one YAML profile.

Also clarify that the following features are not implemented yet:

* LLM review
* API server
* MCP server
* Persistence
* Frontend
* JSON / HTML report export
* Batch review

## Project State Update

Update:

```text
PROJECT_STATE.md
```

The update should mention:

* TASK-0006 is completed.
* A minimal CLI review command has been added.
* The CLI can review one Markdown file using one YAML profile.
* The CLI currently uses the existing in-memory review pipeline.
* The project still does not have LLM review, API, MCP, persistence, frontend, or report export.

## Changelog Update

Update:

```text
CHANGELOG.md
```

Add an entry for TASK-0006.

The entry should mention:

* Added minimal CLI entrypoint.
* Added `content-review review` command.
* Wired CLI to Markdown reader, profile loader, and review pipeline.
* Added CLI tests.
* Updated architecture documentation.
* Updated project state.

## Git Commit Requirement

After implementation and successful tests, create a dedicated Git commit for TASK-0006.

Expected commit message:

```bash
feat(task-0006): add minimal cli review command
```

Before committing, run:

```bash
git status
uv run pytest
```

After committing, run:

```bash
git status
git log --oneline -3
```

The working tree should be clean unless there are unrelated files.

## Acceptance Criteria

This task is complete only when all of the following are true:

1. TASK-0005 has already been committed.
2. A CLI module exists.
3. A console script entry exists in `pyproject.toml`.
4. `content-review review <markdown_file> --profile <profile_file>` works.
5. The CLI uses `read_markdown()`.
6. The CLI uses `load_profile()`.
7. The CLI uses `review_document()`.
8. The CLI prints a human-readable review summary.
9. The CLI returns exit code `0` for successful reviews.
10. The CLI returns a non-zero exit code for missing files or invalid inputs.
11. CLI tests exist.
12. `uv run pytest` passes.
13. `docs/ARCHITECTURE.md` is updated.
14. `PROJECT_STATE.md` is updated.
15. `CHANGELOG.md` is updated.
16. A dedicated TASK-0006 Git commit exists.
17. No unrelated changes are included in the TASK-0006 commit.

## Agent Output Required

After finishing the task, report:

1. Whether TASK-0005 had already been committed before starting.
2. Modified files.
3. New files.
4. Added CLI entrypoint.
5. Added console script name.
6. CLI command usage.
7. How the CLI calls `read_markdown()`, `load_profile()`, and `review_document()`.
8. Test command and result.
9. Documentation updates.
10. Git commit hash for TASK-0006.
11. Current `git status`.
12. Any unresolved issues.
13. Recommended next TASK.

## Next Task Preview

After this task, the recommended next task is:

```text
TASK-0007-json-output-format.md
```

The goal of TASK-0007 should be to add a machine-readable JSON output option to the CLI, for example:

```bash
content-review review article.md --profile profiles/wechat.yaml --format json
```

TASK-0007 should still avoid LLM integration.
