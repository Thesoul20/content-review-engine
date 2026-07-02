# Review Output Index

## Summary

| Field | Value |
| --- | --- |
| Mode | single-file |
| File | examples/demo/articles/wechat-demo.md |
| Profile | examples/demo/profiles/wechat-demo.yaml |
| Profile Name | wechat-demo |
| Deterministic Review | completed |
| LLM Review | enabled |
| Deterministic Findings | 6 |
| LLM Findings | 0 |
| Quality Gate Source | deterministic review only |

## Output Files

| Output | Path | Format | Purpose | Canonical |
| --- | --- | --- | --- | --- |
| Deterministic Output | examples/demo/artifacts/cli/single-file/review.md | markdown | Human-readable deterministic review report | no |
| LLM JSON Sidecar | examples/demo/artifacts/cli/single-file/llm-result.json | json | Machine-readable LLM semantic review result | yes, for LLM layer |
| LLM Markdown Report | examples/demo/artifacts/cli/single-file/llm-report.md | markdown | Human-readable LLM semantic review report | no |
| Report Index | examples/demo/artifacts/cli/single-file/report-index.md | markdown | Navigation and interpretation guide across deterministic and LLM outputs | no |

## Interpretation

- Deterministic review is the stable review layer and the only quality-gate source.
- LLM review is advisory semantic analysis and does not change deterministic findings.
- LLM findings do not participate in fail-on or quality-gate decisions.
- LLM findings are advisory semantic review suggestions from the LLM layer. They do not participate in deterministic finding counts, fail-on, or quality gate.
- Use deterministic output for compliance checks and CI gating.
- Use LLM output for semantic review suggestions and follow-up inspection.

## Manual Review Workflow

- Manual review checklist items are presentation-only workflow metadata for human follow-up.
- Checklist status and decision values are not persisted to JSON sidecars or any review-state file.
- Manual review checklist items do not change deterministic counts, fail-on, or quality-gate behavior.
- Current manual review checklist items: 0.

## Deterministic Review Summary

| Field | Value |
| --- | --- |
| Total Findings | 6 |
| Info Findings | 2 |
| Warning Findings | 4 |
| Error Findings | 0 |
| Critical Findings | 0 |

## LLM Review Summary

| Field | Value |
| --- | --- |
| Status | completed |
| Schema Version | llm-review-result.v1 |
| Provider | - |
| Model | - |
| Total Findings | 0 |
| Source | llm |
| Advisory | yes |
| Quality Gate Participation | no |
| Severity Semantics | LLM advisory severity only |