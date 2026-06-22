# Architecture

## Architecture Style

This project follows a Python package-first architecture.

The core package is the center of the system.

External interfaces such as CLI, Skill, MCP, API, and frontend are adapters.

---

## Target Architecture

```text
Frontend / Web / Tauri
        ↓
FastAPI Backend
        ↓
MCP Server / CLI / Skill
        ↓
Python Core Package
        ↓
Review Rules / AI Adapter / Diff / Reports
```

---

## Current Architecture

Current phase only includes:

```text
Python Core Package
Docs
Tasks
Tests
```

MCP, Skill, API, and frontend are planned but not implemented yet.

The current core package input layer includes:

```text
src/content_review_engine/parser/
src/content_review_engine/config/
profiles/
```

---

## Core Package Responsibility

The core package should handle:

- Markdown input processing
- Review profile loading
- Rule execution
- Structured review results
- Report generation
- Diff generation
- AI review adapter in later versions

Current implemented input helpers:

- `content_review_engine.parser.read_markdown`
- `content_review_engine.config.load_profile`

---

## Adapter Responsibility

Adapters should only call the core package.

Adapters include:

- CLI
- Skill
- MCP Server
- FastAPI backend
- Frontend

Adapters must not duplicate core review logic.

---

## Forbidden Architecture

Do not do this:

```text
CLI contains review logic
MCP contains separate review prompt
API contains separate review pipeline
Skill contains business logic
```

Correct design:

```text
CLI / MCP / API / Skill
        ↓
content_review_engine core package
```
