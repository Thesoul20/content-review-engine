
# TASK-0007: Add Finding Location and Context Snippets

## 1. Task Title

`TASK-0007: Add Finding Location and Context Snippets`

## 2. Task Status

Draft

## 3. Depends On

This task depends on:

* `TASK-0003: Add Markdown Reader and Profile Loading`
* `TASK-0004: Add Basic Forbidden Terms Rule`
* `TASK-0005: Add Minimal Review Pipeline`
* `TASK-0006: Add Minimal CLI Review Command`

Do not start this task unless TASK006 has been completed and the existing test suite passes.

## 4. Goal

Improve review findings by adding precise source location and context snippet information.

After this task, each finding produced by the existing rule-based review pipeline should be able to include:

* Matched text.
* Start line.
* Start column.
* End line.
* End column.
* Start character offset.
* End character offset.
* A short context snippet around the finding.

This task makes review results more useful for CLI output, future Markdown reports, future diff tracking, future LLM-assisted rewriting, and future API/MCP integration.

## 5. Background

Before TASK007, the project can already:

1. Read Markdown files.
2. Load YAML `ReviewProfile`.
3. Run a minimal review pipeline.
4. Detect forbidden terms.
5. Expose review through a minimal CLI.
6. Return structured review results.

However, the current findings are still too coarse.

A finding that only says:

```text
Found forbidden term: 绝对
```

is not enough for users to quickly locate and fix the issue.

The next step is to enrich findings with location and context information, while keeping the review engine rule-based and minimal.

## 6. Non-Goals

This task must not implement any of the following:

* LLM-based review.
* Automatic rewriting.
* Diff tracking.
* Markdown auto-fix.
* Full report generation.
* Batch review.
* Watch mode.
* MCP server.
* REST API.
* GUI.
* New high-level review strategy.
* New rule categories unrelated to forbidden terms.
* Rich terminal UI.
* Profile editing commands.

This task is only about improving the structure and usefulness of findings.

## 7. Required Reading Before Coding

Before making any code changes, read:

```text
AGENTS.md
PROJECT_STATE.md
ROADMAP.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
tasks/TASK-0003-markdown-reader-and-profile-loading.md
tasks/TASK-0004-basic-forbidden-terms-rule.md
tasks/TASK-0005-minimal-review-pipeline.md
tasks/TASK-0006-minimal-cli-review-command.md
```

If any of these files are missing, inspect the closest existing equivalent and mention the discrepancy in the final task summary.

## 8. Allowed Scope

This task may modify or add only the files needed to support finding location and context snippets.

Likely allowed files:

```text
src/content_review_engine/core/models.py
src/content_review_engine/core/review.py
src/content_review_engine/rules/forbidden_terms.py
src/content_review_engine/cli.py
tests/test_models.py
tests/test_forbidden_terms.py
tests/test_review_pipeline.py
tests/test_cli.py
docs/DATA_MODELS.md
docs/CLI.md
PROJECT_STATE.md
CHANGELOG.md
```

If the current repository uses different file names, follow the existing structure.

## 9. Forbidden Scope

Do not rewrite the whole review pipeline.

Do not duplicate rule execution logic.

Do not add a new parser framework unless already used by the project.

Do not introduce heavy Markdown AST dependencies.

Do not add new third-party dependencies unless there is a clear and documented reason.

Prefer simple Python string scanning for this task.

Do not change existing public APIs unless necessary.

If existing APIs must change, keep backward compatibility where reasonable.

## 10. Data Model Requirements

Add a small source location model or equivalent fields.

Preferred model name:

```python
SourceSpan
```

Suggested fields:

```python
start_line: int
start_column: int
end_line: int
end_column: int
start_offset: int
end_offset: int
matched_text: str
context: str | None = None
```

Rules:

* Line numbers should be 1-based.
* Column numbers should be 1-based.
* Character offsets should be 0-based.
* `end_offset` should be exclusive.
* `matched_text` should contain the exact matched text.
* `context` should contain a short snippet around the finding.

Then attach this model to `Finding`.

Preferred shape:

```python
class Finding:
    rule_id: str
    severity: Severity
    message: str
    suggestion: str | None = None
    location: SourceSpan | None = None
```

If the existing model style is different, adapt to the current codebase while preserving the same information.

## 11. Context Snippet Requirements

Add a helper that extracts a small context snippet around a finding.

Suggested behavior:

```text
before_chars = 30
after_chars = 30
```

Example input:

```text
这个方法绝对可以提升你的写作效率。
```

Matched term:

```text
绝对
```

Expected context may be:

```text
这个方法绝对可以提升你的写作效率。
```

For long text, the context should be trimmed.

Example:

```text
...前面的内容这个方法绝对可以提升你的写作效率后面的内容...
```

Requirements:

* Context should be stable and deterministic.
* Context should not include excessive text.
* Context should preserve the matched text.
* Context should handle findings at the beginning of the document.
* Context should handle findings at the end of the document.
* Context should handle Chinese and English text.
* Context should handle multiline Markdown.

## 12. Location Calculation Requirements

Add a small utility function or internal helper to convert character offsets into line and column positions.

Suggested helper:

```python
def offset_to_line_column(text: str, offset: int) -> tuple[int, int]:
    ...
```

Rules:

* Line and column should be 1-based.
* Newline handling should be deterministic.
* The first character in the document should be line `1`, column `1`.
* The first character after a newline should be column `1` of the next line.

Example:

```text
第一行
第二行绝对正确
```

The term `绝对` should report:

```text
start_line = 2
start_column = 4
```

## 13. Forbidden Terms Rule Update

Update the existing forbidden terms rule so that every finding includes a `SourceSpan` or equivalent location information.

For each forbidden term match, the finding should include:

```text
matched_text
start_line
start_column
end_line
end_column
start_offset
end_offset
context
```

The rule should continue to support all existing behavior from TASK004 and TASK005.

Do not change rule semantics beyond adding location metadata.

## 14. Review Pipeline Update

The review pipeline should preserve location metadata when returning `ReviewResult`.

If the pipeline already returns findings directly, no major pipeline change should be needed.

If serialization is used, ensure location information is preserved in JSON output.

## 15. CLI Output Update

Update the CLI output to display location information when available.

Text output should include at least:

```text
Line: 12
Column: 8
Matched: 绝对
Context: 这个方法绝对可以提升效率
```

Example text output:

```text
Review completed.

Findings: 1

[warning] forbidden_terms.absolute_claim
Message: Found forbidden term: 绝对
Line: 12
Column: 8
Matched: 绝对
Context: 这个方法绝对可以提升效率
Suggestion: Consider replacing it with a more cautious expression.
```

JSON output should include the full location object.

Example:

```json
{
  "findings": [
    {
      "rule_id": "forbidden_terms.absolute_claim",
      "severity": "warning",
      "message": "Found forbidden term: 绝对",
      "suggestion": "Consider replacing it with a more cautious expression.",
      "location": {
        "start_line": 12,
        "start_column": 8,
        "end_line": 12,
        "end_column": 10,
        "start_offset": 120,
        "end_offset": 122,
        "matched_text": "绝对",
        "context": "这个方法绝对可以提升效率"
      }
    }
  ],
  "summary": {
    "finding_count": 1
  }
}
```

## 16. Tests Required

Add or update tests for location and context support.

### 16.1 SourceSpan Model Test

Test that the source location model can be created and serialized.

Expected fields:

```text
start_line
start_column
end_line
end_column
start_offset
end_offset
matched_text
context
```

### 16.2 Offset to Line Column Test

Test offset conversion for:

* Single-line text.
* Multi-line text.
* Text with Chinese characters.
* Finding at the beginning of a line.
* Finding at the end of a line.

Example:

```text
第一行
第二行绝对正确
```

Expected:

```text
绝对 starts at line 2, column 4
```

### 16.3 Forbidden Term Location Test

Given Markdown containing a forbidden term:

```markdown
# 标题

这个方法绝对有效。
```

The forbidden term rule should return a finding with:

```text
matched_text = 绝对
start_line = 3
start_column = 5
context contains 绝对
```

### 16.4 Multiple Findings Test

Given Markdown with multiple forbidden terms, each finding should have its own correct location.

Example:

```text
这个方法绝对有效。
这个服务永久可用。
```

Expected:

* One finding for `绝对`.
* One finding for `永久`.
* Each finding has correct line and column.

### 16.5 CLI Text Output Test

When running the CLI against Markdown with a forbidden term, stdout should include:

```text
Line:
Column:
Matched:
Context:
```

Do not make the test too fragile by asserting the entire output.

### 16.6 CLI JSON Output Test

When running the CLI with:

```bash
--format json
```

The JSON output should include:

```text
findings[0].location.start_line
findings[0].location.start_column
findings[0].location.matched_text
findings[0].location.context
```

## 17. Documentation Required

Update:

```text
docs/DATA_MODELS.md
docs/CLI.md
```

`docs/DATA_MODELS.md` should explain the new finding location model.

It should include:

* Purpose of source location metadata.
* Line and column numbering rules.
* Offset numbering rules.
* Example `Finding` with `location`.

`docs/CLI.md` should explain that CLI output now includes line, column, matched text, and context when available.

## 18. PROJECT_STATE Update

Update `PROJECT_STATE.md`.

Mention:

* TASK007 completed.
* Findings now include source location metadata.
* Forbidden terms findings include matched text, line, column, offsets, and context snippet.
* CLI text and JSON outputs include location information.
* No LLM, rewriting, diff tracking, API, MCP, or GUI support was added.

## 19. CHANGELOG Update

Update `CHANGELOG.md`.

Suggested entry:

```markdown
## TASK-0007

### Added

- Added source location metadata for review findings.
- Added matched text, line, column, character offsets, and context snippets to forbidden term findings.
- Added location-aware CLI text output.
- Added location object to CLI JSON output.
- Added tests for offset conversion, forbidden term locations, multiple findings, and CLI output.

### Changed

- Extended finding data model with optional source location information.
- Updated data model and CLI documentation.

### Not Added

- No LLM review.
- No automatic rewriting.
- No diff tracking.
- No MCP server.
- No REST API.
- No GUI.
```

## 20. Validation Commands

After implementation, run:

```bash
uv run pytest
```

If the CLI entrypoint is available, also run a manual smoke test:

```bash
uv run content-review review path/to/sample.md --profile path/to/profile.yml
```

And JSON output smoke test:

```bash
uv run content-review review path/to/sample.md --profile path/to/profile.yml --format json
```

Use temporary files for smoke tests if the repository does not contain examples.

Do not commit unnecessary temporary files.

## 21. Completion Criteria

This task is complete only when:

* Findings can include source location metadata.
* Forbidden term findings include matched text.
* Forbidden term findings include line and column.
* Forbidden term findings include character offsets.
* Forbidden term findings include context snippets.
* CLI text output includes location details when available.
* CLI JSON output includes location object when available.
* Tests are added or updated.
* `uv run pytest` passes.
* `docs/DATA_MODELS.md` is updated.
* `docs/CLI.md` is updated.
* `PROJECT_STATE.md` is updated.
* `CHANGELOG.md` is updated.
* No out-of-scope features are implemented.

## 22. Final Agent Response Requirements

When the Agent finishes this task, it must report:

1. Files changed.
2. New or updated data model fields.
3. How location is calculated.
4. How forbidden term findings now include location.
5. CLI output changes.
6. Tests added.
7. Result of `uv run pytest`.
8. Whether `docs/DATA_MODELS.md` was updated.
9. Whether `docs/CLI.md` was updated.
10. Whether `PROJECT_STATE.md` was updated.
11. Whether `CHANGELOG.md` was updated.
12. Known limitations.

The final response must be concise and must not claim unsupported functionality.

