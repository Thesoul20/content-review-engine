# Batch LLM Review Report

## Summary

| Field | Value |
| --- | --- |
| Schema Version | llm-sidecar-result.v2 |
| LLM Provider | mock |
| LLM Provider Source | config |
| Files Reviewed | 3 |
| Files With LLM Findings | 2 |
| Files With LLM Errors | 1 |
| Total LLM Findings | 2 |

## Advisory Policy

| Field | Value |
| --- | --- |
| Source | llm |
| Advisory | yes |
| Quality Gate Participation | no |
| Severity Semantics | LLM advisory severity only |
| Rule ID Semantics | LLM semantic review layer only |
| Policy Note | LLM findings are advisory semantic review suggestions from the LLM layer. They do not participate in deterministic finding counts, fail-on, or quality gate. |

## Severity Counts

| Severity | Count |
| --- | ---: |
| critical | 1 |
| error | 0 |
| warning | 1 |
| info | 0 |
| unknown | 0 |

## File Status

| File | Status | Findings | Error |
| --- | --- | ---: | --- |
| examples/llm_review_artifacts/batch/input/article-a.md | success | 1 | - |
| examples/llm_review_artifacts/batch/input/article-b.md | success | 1 | - |
| examples/llm_review_artifacts/batch/input/article-with-llm-error.md | failed | 0 | RuntimeError: provider timeout during semantic review |

## Manual Review Checklist

| ID | File | Priority | Status | Decision | Quality Gate | Rule | Location | Message | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LLM-001 | examples/llm_review_artifacts/batch/input/article-a.md | medium | needs_review | pending | no | llm.semantic.overclaim | line 3, column 14 to line 3, column 18 | The onboarding benefit sounds broader than the draft supports. | - |
| LLM-002 | examples/llm_review_artifacts/batch/input/article-b.md | high | needs_review | pending | no | llm.semantic.needs_human_review | not provided | The process recommendation needs a human check because it implies a broad staffing conclusion without review evidence. | - |

## LLM Execution Review Checklist

| ID | File | Status | Suggested Action | Error Type | Error Message | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| LLM-ERR-001 | examples/llm_review_artifacts/batch/input/article-with-llm-error.md | needs_rerun | rerun_llm_review | RuntimeError | provider timeout during semantic review | - |

## Findings By File

### `examples/llm_review_artifacts/batch/input/article-a.md`

- Status: success
- Findings: 1
- Overall Risk: medium
- Summary: One overclaim needs revision.
- Recommended Action: Revise the promise and confirm expected scope.
- Confidence: not provided

## Findings

| Severity | Rule | Source | Advisory | Quality Gate | Confidence | Line | Column | Message | Suggestion |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| warning | llm.semantic.overclaim | llm | yes | no | not provided | 3 | 14 | The onboarding benefit sounds broader than the draft supports. | Describe the rollout conditions and expected audience more precisely. |

## Detailed Findings

### 1. llm.semantic.overclaim

- Severity: warning
- Rule: `llm.semantic.overclaim`
- Source: llm
- Advisory: yes
- Quality Gate Participation: no
- Confidence: not provided
- Location: line 3, column 14 to line 3, column 18
- Message: The onboarding benefit sounds broader than the draft supports.
- Suggestion: Describe the rollout conditions and expected audience more precisely.
- Matched Text: `马上交付`

### `examples/llm_review_artifacts/batch/input/article-b.md`

- Status: success
- Findings: 1
- Overall Risk: high
- Summary: The draft needs human confirmation before reuse.
- Recommended Action: Route to manual review and collect reviewer notes.
- Confidence: not provided

## Findings

| Severity | Rule | Source | Advisory | Quality Gate | Confidence | Line | Column | Message | Suggestion |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| critical | llm.semantic.needs_human_review | llm | yes | no | 0.74 | - | - | The process recommendation needs a human check because it implies a broad staffing conclusion without review evidence. | Ask an editor or operations owner to confirm the staffing claim before reuse. |

## Detailed Findings

### 1. llm.semantic.needs_human_review

- Severity: critical
- Rule: `llm.semantic.needs_human_review`
- Source: llm
- Advisory: yes
- Quality Gate Participation: no
- Confidence: 0.74
- Location: unavailable
- Message: The process recommendation needs a human check because it implies a broad staffing conclusion without review evidence.
- Suggestion: Ask an editor or operations owner to confirm the staffing claim before reuse.
- Matched Text: `-`
- Category: review_required

### `examples/llm_review_artifacts/batch/input/article-with-llm-error.md`

- Status: failed
- Findings: 0
- Error Type: `RuntimeError`
- Message: provider timeout during semantic review
