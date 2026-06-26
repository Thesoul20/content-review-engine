# Content Review Engine

Content Review Engine is a Python package-first project for reviewing Markdown content and returning structured review results.

The project starts as a reusable Python package and may later expand to:

- CLI
- Skill
- MCP Server
- FastAPI backend
- Frontend application

---

## Current Status

Current phase:

```text
M0: Project initialization
```

The project is not production-ready yet.

---

## Core Principle

The core review logic must live in the Python package.

CLI, Skill, MCP, API, and frontend should only be adapters around the core package.

---

## Development Workflow

Before each Agent coding session, read:

1. `AGENTS.md`
2. `PROJECT_STATE.md`
3. `ROADMAP.md`
4. `docs/ARCHITECTURE.md`
5. Current task file in `tasks/`

Each development task must have:

- Clear goal
- Clear scope
- Files allowed to modify
- Files not allowed to modify
- Acceptance criteria
- Tests when applicable

## Quickstart

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for the complete first-run
workflow from dependency installation to profile setup, review, batch review,
Markdown reports, and CI-oriented exit codes.

The repository includes starter and real-world profile templates for general
publishing, WeChat articles, marketing copy, technical blogs, and health
content. They help flag common risky wording patterns for review and do not
provide legal, medical, advertising, regulatory, or platform compliance
advice.

## Rule Reference

See [docs/RULES.md](docs/RULES.md), the canonical rule system reference, for
supported rule IDs, severity ordering, suppression comments, rule counts,
severity counts, and quality-gate behavior.
