# ROADMAP.md

## v0.1.0 Core Package MVP

Goal:

- Create Python package structure.
- Read Markdown content.
- Load review profile.
- Run deterministic review rules.
- Return structured review result.
- Add basic tests.

Not included:

- PydanticAI
- MCP
- Skill
- API
- Database
- Frontend

---

## v0.2.0 CLI Stable

Goal:

- Add stable CLI command.
- Support JSON output.
- Support Markdown report output.
- Support local profile config.

Example target command:

```bash
content-review review examples/article.md --profile wechat --json
```

---

## v0.3.0 AI Review Adapter

Goal:

- Add PydanticAI reviewer.
- Add structured AI output.
- Add prompt versioning.
- Add LLM mock tests.
- Keep AI layer as adapter, not as core business logic.

---

## v0.4.0 Skill

Goal:

- Add Skill document.
- Explain when Agent should call the CLI.
- Explain how Agent should read the review report.
- Add examples.

---

## v0.5.0 MCP Server

Goal:

- Expose review tools through MCP.
- Add tools such as:

  - review_markdown
  - rewrite_markdown
  - list_profiles
  - generate_report

---

## v0.6.0 FastAPI Backend

Goal:

- Add server backend prototype.
- Add document review endpoint.
- Add review job records.
- Prepare for user system and storage.

---

## v1.0.0 Stable Release

Goal:

- Core package, CLI, AI adapter, MCP, and API have stable contracts.
- Documentation and tests are complete enough for long-term maintenance.
