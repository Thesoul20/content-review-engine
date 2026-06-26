# TASK-0032: Add End-to-End Demo Project

## Status

Planned

## Goal

Add an end-to-end demo project that shows how to use the content review engine against realistic Markdown content.

TASK-0031 added real-world profile templates. TASK-0032 should add a complete runnable demo that connects:

* example Markdown input
* real-world profile template usage
* single-file review
* batch review
* Markdown report output
* JSON output
* quality gate behavior
* suppression examples
* expected demo results

The goal is to make the CLI MVP easy to understand, test, and demonstrate.

## Background

The project now supports:

* Markdown review
* review profiles
* built-in deterministic rules
* `regex_rules`
* profile templates
* inline suppression
* text / JSON / Markdown output
* single-file review
* batch review
* quality gates
* rule counts
* severity counts
* documentation for rule system and profile usage

However, users still need a concrete end-to-end example.

TASK-0032 should provide a small demo workspace that users can run without inventing their own article or profile.

The demo should answer:

```text id="o6wohj"
What does the input look like?
Which profile should I use?
Which command should I run?
What findings should I expect?
What does the Markdown report look like?
How does quality gate failure look?
How do suppressions work?
```

## Scope

This task may modify or add:

* `examples/`
* demo Markdown articles
* demo profiles or generated profile copies
* expected demo reports
* docs for running the demo
* tests for demo files and demo commands
* README links
* Quickstart links
* CLI docs links
* `PROJECT_STATE.md`
* `CHANGELOG.md`

Likely files or directories:

```text id="w3sp6b"
examples/
examples/demo/
examples/demo/articles/
examples/demo/profiles/
examples/demo/reports/
examples/demo/README.md
tests/
README.md
docs/QUICKSTART.md
docs/CLI.md
docs/PROFILES.md
PROJECT_STATE.md
CHANGELOG.md
```

Exact paths should follow the current repository conventions.

## Non-goals

This task must not:

* add LLM review
* add PydanticAI
* add API endpoints
* add MCP support
* add GUI support
* change rule matching behavior
* change regex rule behavior
* change suppression syntax
* change quality gate semantics
* change Markdown report structure
* change JSON output schema
* change profile template behavior
* add new rule types
* claim legal, medical, advertising, regulatory, or platform compliance
* create a large fixture set that makes tests brittle

## Required Work

### 1. Inspect Current Examples And Test Fixtures

Before making changes, inspect the repository for existing examples, fixtures, and expected outputs.

Check:

```text id="7q0xkn"
examples/
profiles/examples/
tests/fixtures/
tests/fixtures/expected_reports/
docs/QUICKSTART.md
docs/CLI.md
docs/PROFILES.md
README.md
```

Reuse existing conventions where possible.

Do not duplicate large test fixtures unnecessarily.

### 2. Add Demo Directory

Add a dedicated demo directory.

Recommended structure:

```text id="n9q4lo"
examples/demo/
  README.md
  articles/
    wechat-demo.md
    technical-demo.md
  profiles/
    wechat-demo.yaml
    technical-demo.yaml
  reports/
    wechat-demo-report.md
    technical-demo-report.md
```

Alternative structure is acceptable if it better matches the repository.

Keep the demo small and readable.

### 3. Add Demo Articles

Add at least two Markdown demo articles.

Recommended articles:

```text id="ywrgm8"
wechat-demo.md
technical-demo.md
```

#### `wechat-demo.md`

Purpose:

Show common public-facing article issues.

Should intentionally include:

* exaggerated wording
* placeholder text
* engagement bait
* at least one Markdown issue if current rules support it
* one inline suppression example
* enough clean text to look realistic

Example issues:

```text id="lxgwvm"
唯一
最强
100%
不看后悔
TODO
待补充
```

Include one suppression example:

```markdown id="q5z53a"
这是一个用于演示 suppression 的句子。 <!-- content-review-disable-line exaggerated_claims -->
```

Do not make the article too long.

#### `technical-demo.md`

Purpose:

Show technical blog review behavior.

Should intentionally include:

* TODO / FIXME marker
* absolute technical claim
* unresolved example text
* possible Markdown link or image issue if supported
* one inline suppression example

Example issues:

```text id="6ac0uz"
TODO
FIXME
永远不会
零风险
待验证
```

### 4. Add Demo Profiles

Add demo-specific profile files under:

```text id="udb961"
examples/demo/profiles/
```

Recommended profiles:

```text id="ef0nxx"
wechat-demo.yaml
technical-demo.yaml
```

These profiles may be copied from or adapted from the real-world templates added in TASK-0031.

They should be stable demo profiles, not generated during tests.

Requirements:

* must validate successfully
* must include `regex_rules`
* should use conservative messages and suggestions
* should avoid compliance guarantee language
* should produce predictable findings against the demo articles

The profiles can be smaller than the full templates if that makes expected outputs easier to maintain.

### 5. Add Expected Demo Reports

Add expected Markdown reports under:

```text id="0t5jlk"
examples/demo/reports/
```

Recommended files:

```text id="7v025m"
wechat-demo-report.md
technical-demo-report.md
```

These should demonstrate the report format.

They do not need to be exhaustive if the project already has full report fixture tests.

However, they should be generated from real commands or kept consistent with expected output.

If exact report output is too brittle, use tests that validate key sections and key findings rather than exact full-file equality.

### 6. Add Demo README

Add:

```text id="j04q5r"
examples/demo/README.md
```

The README should explain:

* what the demo contains
* how to run single-file review
* how to run batch review
* how to generate Markdown report output
* how to generate JSON output
* how to test quality gate behavior
* how inline suppression appears in the demo
* limitations and non-goals

Suggested commands:

```bash id="6lp4ro"
uv run content-review review examples/demo/articles/wechat-demo.md \
  --profile examples/demo/profiles/wechat-demo.yaml
```

```bash id="udnvqt"
uv run content-review review examples/demo/articles/wechat-demo.md \
  --profile examples/demo/profiles/wechat-demo.yaml \
  --format markdown \
  --output /tmp/wechat-demo-report.md
```

```bash id="xbugoj"
uv run content-review review examples/demo/articles/wechat-demo.md \
  --profile examples/demo/profiles/wechat-demo.yaml \
  --format json
```

```bash id="jcbstt"
uv run content-review batch examples/demo/articles \
  --profile examples/demo/profiles/wechat-demo.yaml \
  --format markdown \
  --output /tmp/demo-batch-report.md
```

```bash id="xyy8nv"
uv run content-review review examples/demo/articles/wechat-demo.md \
  --profile examples/demo/profiles/wechat-demo.yaml \
  --fail-on warning
```

Use the actual CLI syntax from the repository.

### 7. Add Demo Tests

Add tests for the demo project.

Suggested file:

```text id="x8lml0"
tests/test_demo_project.py
```

Tests should verify:

* demo articles exist
* demo profiles exist
* demo profiles validate successfully
* demo articles produce findings
* demo review includes configured regex rule IDs
* suppression works in at least one demo article
* Markdown report generation works for demo input
* JSON output serialization works for demo input
* batch review works against the demo article directory
* quality gate fails when expected with `--fail-on warning` or `--fail-on error`
* demo README includes key commands
* demo docs include limitation wording and no compliance guarantees

Avoid brittle tests that depend on exact full report text unless the project already uses stable expected fixtures for this.

Prefer testing durable sections such as:

```text id="v4kc84"
# Content Review Report
## Summary
## Severity Counts
## Rule Counts
## Findings
## Detailed Findings
```

### 8. Update Main README

Update:

```text id="6jq2e9"
README.md
```

Add a short section or link:

```markdown id="i7c8po"
## Demo

See [End-to-End Demo](examples/demo/README.md) for a runnable example using real-world profile templates, regex rules, Markdown reports, JSON output, batch review, inline suppression, and quality gates.
```

Keep it concise.

### 9. Update Quickstart

Update:

```text id="w718qo"
docs/QUICKSTART.md
```

Add a short note pointing users to the end-to-end demo.

Do not duplicate the full demo instructions.

### 10. Update CLI Documentation

Update:

```text id="inbb4c"
docs/CLI.md
```

Add a short demo command section or link to `examples/demo/README.md`.

### 11. Update Profile Documentation

Update:

```text id="zitywu"
docs/PROFILES.md
```

Mention that demo profiles are available under `examples/demo/profiles/` and are separate from reusable templates under `profiles/examples/`.

Clarify:

* templates are starting points
* demo profiles are stable examples for demonstration
* neither provides compliance guarantees

### 12. Update Project State

Update:

```text id="ftu9ql"
PROJECT_STATE.md
```

Mention:

* TASK-0032 completed
* end-to-end demo project added
* demo includes articles, profiles, reports, suppression, quality gate examples, and batch review
* no LLM review was added
* no rule behavior changed

### 13. Update Changelog

Update:

```text id="34yocc"
CHANGELOG.md
```

Add a TASK-0032 entry describing:

* added end-to-end demo project
* added demo articles and profiles
* added demo report examples
* added demo tests
* updated README / Quickstart / CLI / Profile docs
* no runtime behavior changes

## Acceptance Criteria

TASK-0032 is complete when:

* `examples/demo/` exists
* demo articles exist
* demo profiles exist
* demo profiles validate successfully
* demo profiles include `regex_rules`
* demo review produces predictable findings
* inline suppression is demonstrated
* Markdown report generation is demonstrated
* JSON output is demonstrated
* batch review is demonstrated
* quality gate behavior is demonstrated
* demo README contains runnable commands
* README links to the demo
* Quickstart links to the demo
* CLI docs link to or mention the demo
* Profile docs distinguish templates from demo profiles
* tests cover demo files and durable demo behavior
* `PROJECT_STATE.md` is updated
* `CHANGELOG.md` is updated
* all tests pass
* no LLM review is introduced
* no unrelated runtime behavior changes are introduced
* no compliance guarantee is added

## Validation Commands

Run:

```bash id="rsyavr"
uv run pytest
```

Manual demo checks:

```bash id="e5my0k"
uv run content-review review examples/demo/articles/wechat-demo.md \
  --profile examples/demo/profiles/wechat-demo.yaml
```

```bash id="pxrxab"
uv run content-review review examples/demo/articles/wechat-demo.md \
  --profile examples/demo/profiles/wechat-demo.yaml \
  --format markdown \
  --output /tmp/wechat-demo-report.md
```

```bash id="ccg6d8"
uv run content-review review examples/demo/articles/wechat-demo.md \
  --profile examples/demo/profiles/wechat-demo.yaml \
  --format json
```

```bash id="ej3xuk"
uv run content-review batch examples/demo/articles \
  --profile examples/demo/profiles/wechat-demo.yaml \
  --format markdown \
  --output /tmp/demo-batch-report.md
```

```bash id="71fusn"
uv run content-review review examples/demo/articles/wechat-demo.md \
  --profile examples/demo/profiles/wechat-demo.yaml \
  --fail-on warning
```

Use actual CLI syntax if the repository differs.

