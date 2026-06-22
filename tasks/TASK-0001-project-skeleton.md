# TASK-0001: Create Project Skeleton

## Goal

Create the initial Python package skeleton and basic project control documents.

This task should not implement real review logic yet.

---

## Background

The project follows a Python package-first architecture.

The core package should eventually live under:

```text
src/content_review_engine/
```

The first implementation milestone is to create a minimal importable package and a placeholder test.

---

## Scope

Implement only:

1. Basic source directory.
2. Package `__init__.py`.
3. Placeholder test.
4. Initial docs if missing.
5. Update `PROJECT_STATE.md`.
6. Update `CHANGELOG.md`.

---

## Files To Create Or Modify

Allowed:

```text
src/content_review_engine/__init__.py
tests/test_placeholder.py
PROJECT_STATE.md
CHANGELOG.md
README.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/REVIEW_RULES.md
```

---

## Do Not Modify

Do not add:

```text
MCP server
Skill files
FastAPI files
Supabase files
Frontend files
PydanticAI integration
Complex review rules
```

---

## Acceptance Criteria

- `src/content_review_engine/__init__.py` exists.
- `tests/test_placeholder.py` exists.
- Tests can run.
- `PROJECT_STATE.md` records the current status.
- `CHANGELOG.md` records the initialization.
- No MCP/API/Skill/frontend code is added.

---

## Suggested Placeholder Test

```python
def test_placeholder():
    assert True
```

---

## Completion Requirements

After finishing this task, update `PROJECT_STATE.md` with:

- Completed work
- Changed files
- Test result
- Next recommended task
