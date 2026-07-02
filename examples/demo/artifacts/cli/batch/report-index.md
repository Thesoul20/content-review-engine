# Review Output Index

## Summary

| Field | Value |
| --- | --- |
| Mode | batch |
| Input Directory | examples/demo/articles |
| Profile | examples/demo/profiles/technical-demo.yaml |
| Deterministic Review | completed |
| LLM Review | enabled |
| Files Reviewed | 1 |
| Deterministic Findings | 6 |
| LLM Findings | 0 |
| Quality Gate Source | deterministic review only |

## Output Files

| Output | Path | Format | Purpose | Canonical |
| --- | --- | --- | --- | --- |
| Deterministic Output | examples/demo/artifacts/cli/batch/review.md | markdown | Human-readable deterministic review report | no |
| LLM JSON Sidecar | examples/demo/artifacts/cli/batch/llm-result.json | json | Machine-readable aggregate LLM semantic review result | yes, for LLM layer |
| LLM Markdown Report | examples/demo/artifacts/cli/batch/llm-report.md | markdown | Human-readable aggregate LLM semantic review report | no |
| Report Index | examples/demo/artifacts/cli/batch/report-index.md | markdown | Navigation and interpretation guide across batch deterministic and LLM outputs | no |

## Interpretation

- Deterministic batch review is the stable review layer and the only quality-gate source.
- Batch LLM review is advisory semantic analysis and remains separate from deterministic findings.
- LLM partial failures do not rewrite deterministic results, but they should be inspected before trusting LLM coverage.
- LLM findings are advisory semantic review suggestions from the LLM layer. They do not participate in deterministic finding counts, fail-on, or quality gate.
- Use deterministic output for CI gating and rule-based compliance checks.
- Use LLM output for semantic suggestions and per-file follow-up review.

## Manual Review Workflow

- Manual review checklist items are presentation-only workflow metadata for human follow-up.
- Checklist status and decision values are not persisted to JSON sidecars or any review-state file.
- Manual review checklist items do not change deterministic counts, fail-on, or quality-gate behavior.
- Current manual review checklist items: 0.

## Deterministic Review Summary

| Field | Value |
| --- | --- |
| Files Discovered | 1 |
| Files Reviewed | 1 |
| Files With Findings | 1 |
| Total Findings | 6 |
| Info Findings | 1 |
| Warning Findings | 5 |
| Error Findings | 0 |
| Critical Findings | 0 |

## LLM Review Summary

| Field | Value |
| --- | --- |
| Status | completed |
| Schema Version | llm-sidecar-result.v2 |
| Provider | mock |
| Provider Source | explicit |
| Source | llm |
| Advisory | yes |
| Quality Gate Participation | no |
| Severity Semantics | LLM advisory severity only |
| Files Reviewed | 1 |
| Files With LLM Findings | 0 |
| Files With LLM Errors | 0 |
| Total LLM Findings | 0 |

## LLM File Status Summary

| File | Status | Findings | Error |
| --- | --- | ---: | --- |
| examples/demo/articles/technical-demo.md | success | 0 | - |