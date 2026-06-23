
# TASK-0010: Enable Packaged CLI Entrypoint

## 1. Task Title

`TASK-0010: Enable Packaged CLI Entrypoint`

## 2. Task Status

Draft

## 3. Depends On

This task depends on:

* `TASK-0006: Add Minimal CLI Review Command`
* `TASK-0008: Add Markdown Review Report Export`
* `TASK-0009: Add Markdown Fixtures and Example Review Files`

Do not start this task unless TASK009 has been completed and the existing test suite passes.

## 4. Goal

Fix the project packaging configuration so the documented CLI command works directly through uv:

```bash
uv run content-review --help
```

and:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
```

Currently, the CLI module works when run with:

```bash
PYTHONPATH=src uv run python -m content_review_engine.cli ...
```

but `uv run content-review ...` fails because uv skips installing project entry points when the project is not configured as a packaged project.

This task should make the existing `[project.scripts]` entrypoint actually available.

## 5. Background

The project already has a CLI entry in `pyproject.toml`, such as:

```toml
[project.scripts]
content-review = "content_review_engine.cli:main"
```

However, running:

```bash
uv sync
uv run content-review --help
```

currently reports:

```text
warning: Skipping installation of entry points (`project.scripts`) because this project is not packaged; to install entry points, set `tool.uv.package = true` or define a `build-system`
error: Failed to spawn: `content-review`
  Caused by: No such file or directory (os error 2)
```

This means the CLI implementation is present, but the project is not installed as a package into the uv environment, so the console script is not generated.

TASK010 fixes this packaging gap.

## 6. Non-Goals

This task must not implement any of the following:

* New review rules.
* New CLI commands.
* New CLI output formats.
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
* Changes to review result semantics.
* Changes to Markdown report content.

This task is only about enabling the existing CLI entrypoint through packaging configuration and documenting the correct usage.

## 7. Required Reading Before Coding

Before making any code changes, read:

```text
AGENTS.md
PROJECT_STATE.md
ROADMAP.md
docs/ARCHITECTURE.md
docs/CLI.md
docs/TESTING.md
docs/REPORTS.md
pyproject.toml
tasks/TASK-0008-markdown-review-report-export.md
tasks/TASK-0009-markdown-fixtures-and-examples.md
tasks/TASK-0010-enable-packaged-cli-entrypoint.md
```

If historical task files such as TASK0003-TASK0006 are missing, do not recreate them in this task.

Instead:

1. Inspect the current implementation.
2. Use existing docs, tests, and project state as the source of truth.
3. Mention missing historical task files in the final summary only if relevant.

## 8. Allowed Scope

This task may modify only packaging, tests, and documentation related to the CLI entrypoint.

Allowed files:

```text
pyproject.toml
tests/test_cli.py
docs/CLI.md
docs/TESTING.md
PROJECT_STATE.md
CHANGELOG.md
```

Optional, only if necessary:

```text
docs/ARCHITECTURE.md
```

Do not modify core review logic unless an import issue prevents packaging from working.

## 9. Forbidden Scope

Do not rewrite the CLI implementation.

Do not change the `review` command semantics.

Do not change report rendering behavior.

Do not change existing fixture content unless absolutely necessary.

Do not add unrelated dependencies.

Do not introduce a new CLI framework.

Do not rename the package.

Do not rename the console script unless there is a strong reason.

The command name should remain:

```text
content-review
```

## 10. Packaging Requirements

Update `pyproject.toml` so the current `src/` layout project is installable by uv.

Preferred solution:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/content_review_engine"]
```

Keep the existing script entrypoint:

```toml
[project.scripts]
content-review = "content_review_engine.cli:main"
```

If the project already uses a different build backend, follow the existing backend instead of adding Hatchling.

If using Hatchling, ensure it is compatible with the existing dependency management style.

Do not add packaging configuration that changes the package name or import path.

## 11. CLI Entrypoint Requirements

After this task, the following command must work from the project root:

```bash
uv run content-review --help
```

The following command must also work:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format text
```

And:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format json
```

And:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
```

And:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output /tmp/content-review-example-report.md
```

The previous fallback command may still work:

```bash
PYTHONPATH=src uv run python -m content_review_engine.cli review examples/article.md --profile examples/profile.yml --format markdown
```

But documentation should prefer the packaged console script.

## 12. Test Requirements

Add or update tests to verify the CLI entrypoint behavior as much as is practical.

### 12.1 Keep Existing CLI Unit Tests

Existing tests that call `main()` directly should continue to pass.

Do not remove direct `main()` tests if they are useful.

### 12.2 Add Packaging/Entrypoint Smoke Test If Practical

Add one lightweight smoke test that checks the project can expose the console script after sync/install only if this can be done reliably in the test environment.

If invoking `uv run content-review` from pytest would be too slow or brittle, do not force it into the unit test suite.

Instead, document it as a required manual smoke test.

### 12.3 Documentation Consistency Test Optional

If the project already has check-state or documentation validation scripts, update them only if needed.

Do not introduce a complex testing framework for this task.

## 13. Documentation Requirements

Update documentation to prefer the packaged CLI command.

### 13.1 `docs/CLI.md`

Ensure examples use:

```bash
uv run content-review review examples/article.md --profile examples/profile.yml --format text
uv run content-review review examples/article.md --profile examples/profile.yml --format json
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
```

Mention fallback usage only as a troubleshooting option, not the primary command:

```bash
PYTHONPATH=src uv run python -m content_review_engine.cli review examples/article.md --profile examples/profile.yml --format markdown
```

### 13.2 `docs/TESTING.md`

Add a short section explaining manual CLI smoke validation:

```bash
uv sync
uv run content-review --help
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
```

Also mention that `uv sync` should no longer warn:

```text
Skipping installation of entry points (`project.scripts`) because this project is not packaged
```

### 13.3 `PROJECT_STATE.md`

Update project state to mention:

* TASK010 completed.
* Project is now configured as an installable package.
* `content-review` console script works through `uv run`.
* Previous `PYTHONPATH=src python -m ...` fallback is no longer required for normal usage.
* No review behavior changes were introduced.

### 13.4 `CHANGELOG.md`

Add an entry similar to:

```markdown
## TASK-0010

### Fixed

- Enabled packaged CLI entrypoint generation for `content-review`.
- Added project build configuration for the existing `src/` layout package.
- Fixed `uv run content-review ...` so documented CLI commands work directly.

### Changed

- Updated CLI and testing documentation to prefer the packaged console script.

### Not Added

- No new review rules.
- No new CLI commands.
- No LLM review.
- No automatic rewriting.
- No MCP server.
- No REST API.
- No GUI.
```

## 14. Validation Commands

After implementation, run:

```bash
uv sync
```

Confirm that this warning no longer appears:

```text
Skipping installation of entry points (`project.scripts`) because this project is not packaged
```

Then run:

```bash
uv run pytest
```

Then run manual CLI smoke tests:

```bash
uv run content-review --help
uv run content-review review examples/article.md --profile examples/profile.yml --format text
uv run content-review review examples/article.md --profile examples/profile.yml --format json
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown
uv run content-review review examples/article.md --profile examples/profile.yml --format markdown --output /tmp/content-review-example-report.md
```

If the project has a check-state script, run it as well.

Do not commit generated files under `/tmp`.

Do not commit generated example reports unless the project intentionally tracks them.

## 15. Completion Criteria

This task is complete only when:

* `pyproject.toml` configures the project as an installable package.
* Existing `[project.scripts]` entrypoint is preserved.
* `uv sync` no longer skips entry point installation because the project is unpackaged.
* `uv run content-review --help` works.
* `uv run content-review review examples/article.md --profile examples/profile.yml --format text` works.
* `uv run content-review review examples/article.md --profile examples/profile.yml --format json` works.
* `uv run content-review review examples/article.md --profile examples/profile.yml --format markdown` works.
* `uv run pytest` passes.
* CLI documentation is updated.
* Testing documentation is updated.
* `PROJECT_STATE.md` is updated.
* `CHANGELOG.md` is updated.
* No review behavior changes are introduced.

## 16. Known Limitations To Preserve

Do not try to solve these in TASK010:

* Packaging is only for the local Python package.
* No PyPI publishing is added.
* No release workflow is added.
* No binary distribution is added.
* No standalone executable is built.
* No installer is created.
* No GUI packaging is added.
* No Docker image is added.

## 17. Final Agent Response Requirements

When the Agent finishes this task, it must report:

1. Files changed.
2. Packaging configuration added or changed.
3. Whether the existing `content-review` script entrypoint was preserved.
4. Result of `uv sync`.
5. Result of `uv run pytest`.
6. Result of `uv run content-review --help`.
7. Manual CLI smoke test results for text, JSON, Markdown, and Markdown `--output`.
8. Whether `docs/CLI.md` was updated.
9. Whether `docs/TESTING.md` was updated.
10. Whether `PROJECT_STATE.md` was updated.
11. Whether `CHANGELOG.md` was updated.
12. Known limitations.

The final response must be concise and must not claim unsupported functionality.

