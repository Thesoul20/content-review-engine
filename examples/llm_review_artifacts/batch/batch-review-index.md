# Review Output Index

## Summary

| Field | Value |
| --- | --- |
| Mode | batch |
| Input Directory | examples/llm_review_artifacts/batch/input |
| Profile | examples/llm_review_artifacts/batch/profile.yml |
| Deterministic Review | completed |
| LLM Review | enabled |
| Files Reviewed | 3 |
| Deterministic Findings | 2 |
| LLM Findings | 2 |
| Quality Gate Source | deterministic review only |

## Output Files

| Output | Path | Format | Purpose | Canonical |
| --- | --- | --- | --- | --- |
| Deterministic Output | deterministic-report.md | markdown | Human-readable deterministic review report | no |
| LLM JSON Sidecar | batch-llm-result.json | json | Machine-readable aggregate LLM semantic review result | yes, for LLM layer |
| LLM Markdown Report | batch-llm-report.md | markdown | Human-readable aggregate LLM semantic review report | no |
| Report Index | batch-review-index.md | markdown | Navigation and interpretation guide across batch deterministic and LLM outputs | no |

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
- Current manual review checklist items: 2.
- Current LLM execution review checklist items: 1; treat them as rerun candidates and verify coverage manually.

## Deterministic Review Summary

| Field | Value |
| --- | --- |
| Files Discovered | 3 |
| Files Reviewed | 3 |
| Files With Findings | 2 |
| Total Findings | 2 |
| Info Findings | 1 |
| Warning Findings | 1 |
| Error Findings | 0 |
| Critical Findings | 0 |

## LLM Review Summary

| Field | Value |
| --- | --- |
| Status | completed |
| Schema Version | llm-sidecar-result.v2 |
| Provider | mock |
| Provider Source | config |
| Source | llm |
| Advisory | yes |
| Quality Gate Participation | no |
| Severity Semantics | LLM advisory severity only |
| Files Reviewed | 3 |
| Files With LLM Findings | 2 |
| Files With LLM Errors | 1 |
| Total LLM Findings | 2 |

## LLM File Status Summary

| File | Status | Findings | Error |
| --- | --- | ---: | --- |
| examples/llm_review_artifacts/batch/input/article-a.md | success | 1 | - |
| examples/llm_review_artifacts/batch/input/article-b.md | success | 1 | - |
| examples/llm_review_artifacts/batch/input/article-with-llm-error.md | failed | 0 | RuntimeError: provider timeout during semantic review |

## LLM Error Summary

| File | Error |
| --- | --- |
| examples/llm_review_artifacts/batch/input/article-with-llm-error.md | RuntimeError: provider timeout during semantic review |
