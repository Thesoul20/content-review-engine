# LLM Review Report

## Summary

| Field | Value |
| --- | --- |
| File | examples/llm_review_artifacts/single-file/input.md |
| Schema Version | llm-review-result.v1 |
| Provider | mock |
| Model | mock-llm-v1 |
| Prompt Version | llm-semantic-review-prompt.v1 |
| Profile Name | artifact-single-file |
| Total Findings | 2 |
| Overall Risk | medium |
| LLM Summary | One unsupported promise and one follow-up item need human review. |
| Recommended Action | Revise the success claim and complete a manual review before publication. |
| Confidence | 0.78 |

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
| critical | 0 |
| error | 1 |
| warning | 1 |
| info | 0 |
| unknown | 0 |

## Findings

| Severity | Rule | Source | Advisory | Quality Gate | Confidence | Line | Column | Message | Suggestion |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| warning | llm.semantic.unsupported_claim | llm | yes | no | 0.82 | 5 | 12 | The success promise sounds stronger than the evidence shown in the draft. | Narrow the promise and add concrete onboarding evidence. |
| error | llm.semantic.needs_human_review | llm | yes | no | not provided | - | - | The draft asks readers to trust an operational result without explaining scope, reviewers, or exceptions. | Have a human reviewer confirm the rollout scope and exception handling before publishing. |

## Manual Review Checklist

| ID | Priority | Status | Decision | Quality Gate | Rule | Location | Message | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LLM-001 | medium | needs_review | pending | no | llm.semantic.unsupported_claim | line 5, column 12 to line 5, column 16 | The success promise sounds stronger than the evidence shown in the draft. | - |
| LLM-002 | high | needs_review | pending | no | llm.semantic.needs_human_review | not provided | The draft asks readers to trust an operational result without explaining scope, reviewers, or exceptions. | - |

## Detailed Findings

### 1. llm.semantic.unsupported_claim

- Severity: warning
- Rule: `llm.semantic.unsupported_claim`
- Source: llm
- Advisory: yes
- Quality Gate Participation: no
- Confidence: 0.82
- Location: line 5, column 12 to line 5, column 16
- Message: The success promise sounds stronger than the evidence shown in the draft.
- Suggestion: Narrow the promise and add concrete onboarding evidence.
- Matched Text: `保证成功`

### 2. llm.semantic.needs_human_review

- Severity: error
- Rule: `llm.semantic.needs_human_review`
- Source: llm
- Advisory: yes
- Quality Gate Participation: no
- Confidence: not provided
- Location: unavailable
- Message: The draft asks readers to trust an operational result without explaining scope, reviewers, or exceptions.
- Suggestion: Have a human reviewer confirm the rollout scope and exception handling before publishing.
- Matched Text: `-`
- Rationale: Readers may interpret the claim as a universal outcome.
- Category: review_required
