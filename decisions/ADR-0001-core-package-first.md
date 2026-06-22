# ADR-0001: Core Package First

## Status

Accepted

---

## Context

This project is expected to evolve into multiple forms:

- Python package
- CLI
- Skill
- MCP Server
- FastAPI backend
- Frontend application

If the project starts from CLI, MCP, API, or frontend first, the core review logic may become duplicated and hard to maintain.

---

## Decision

Use a Python package-first architecture.

The core business logic should live in:

```text
src/content_review_engine/
```

External interfaces such as CLI, Skill, MCP, API, and frontend must call the core package instead of implementing their own review logic.

---

## Consequences

Benefits:

- Core logic is reusable.
- CLI, MCP, API, and frontend stay thin.
- Testing becomes easier.
- Long-term architecture is easier to maintain.
- Agent development has a clear boundary.

Tradeoffs:

- Early development requires more discipline.
- Data models must be designed carefully.
- Feature implementation may feel slower at the beginning.
