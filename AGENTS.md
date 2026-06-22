# AGENTS.md

## Project

This project is a Python package-first content review engine.

The core goal is to review Markdown content and return structured review results.

The project may later expand to:

- CLI
- Skill
- MCP Server
- FastAPI backend
- Web or desktop frontend

But the first priority is to build a clean and reusable Python core package.

---

## Architecture Rules

1. Core business logic must stay in `src/content_review_engine/`.
2. CLI, Skill, MCP, and API are adapters around the core package.
3. Do not duplicate review logic in CLI, MCP, Skill, or API layers.
4. Review output must use Pydantic models defined in the core package.
5. Any change to ReviewResult or ReviewIssue requires updating `docs/DATA_MODELS.md`.
6. Any new review rule must have a stable `rule_id` and be documented in `docs/REVIEW_RULES.md`.
7. Any major architecture change requires a new ADR in `decisions/`.
8. Do not introduce large abstractions before there are at least two real use cases.

---

## Before Coding

Read these files first:

1. `PROJECT_STATE.md`
2. `ROADMAP.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DATA_MODELS.md`
5. The current task file in `tasks/`

---

## After Coding

Update these files when relevant:

1. `PROJECT_STATE.md`
2. `CHANGELOG.md`
3. Related docs
4. Related tests

---

## Do Not

- Do not introduce MCP before the CLI contract is stable.
- Do not introduce FastAPI before the core package is stable.
- Do not put API, database, or user-auth logic into the core package.
- Do not change public data models without documenting the reason.
- Do not let generated code bypass the core pipeline.
- Do not implement features outside the current task file.
