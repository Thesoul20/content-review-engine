# Combined Content Review Report

## Summary

| Field | Value |
| --- | --- |
| File | examples/llm_review_artifacts/single-file/input.md |
| Profile | artifact-single-file |
| Deterministic Findings | 2 |
| LLM Status | succeeded |
| LLM Advisory Findings | 2 |
| LLM Advisory Policy | yes |
| Quality Gate Scope | deterministic-only |
| LLM Error | none |

## LLM Execution

| Field | Value |
| --- | --- |
| Status | succeeded |
| Advisory | yes |
| Quality Gate Participation | no |
| Policy Note | LLM findings are advisory semantic review suggestions from the LLM layer. They do not participate in deterministic finding counts, fail-on, or quality gate. |

## LLM Advisory Findings

| Severity | Rule | Source | Advisory | Quality Gate | Confidence | Location | Message | Suggestion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| warning | llm.semantic_unsupported_claim | llm | yes | no | 0.82 | 5:12 | The success promise sounds stronger than the evidence shown in the draft. | Narrow the promise and add concrete onboarding evidence. |
| error | llm.semantic_needs_human_review | llm | yes | no | not provided | - | The draft asks readers to trust an operational result without explaining scope, reviewers, or exceptions. | Have a human reviewer confirm the rollout scope and exception handling before publishing. |

## Manual Review Workflow

- Review deterministic findings first; they remain the canonical review output and the only quality-gate source.
- Treat LLM findings as advisory semantic suggestions that require human confirmation before any content change.
- Manual review checklist state is presentation-only and is not persisted into ReviewResult, sidecar JSON, or any review-state file.
- Current advisory checklist items: 2.

## Manual Review Checklist

| ID | Priority | Status | Decision | Quality Gate | Rule | Location | Message | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LLM-001 | medium | needs_review | pending | no | llm.semantic.unsupported_claim | line 5, column 12 to line 5, column 16 | The success promise sounds stronger than the evidence shown in the draft. | - |
| LLM-002 | high | needs_review | pending | no | llm.semantic.needs_human_review | not provided | The draft asks readers to trust an operational result without explaining scope, reviewers, or exceptions. | - |

## Quality Gate Boundary

- Quality gate evaluation remains deterministic-only.
- LLM advisory findings do not participate in severity counts, rule counts, fail-on, quality gate, or exit code.
- Use the deterministic report below as the canonical audit record for automation and compliance checks.

## Deterministic Review

# Content Review Report

## Summary

| Field | Value |
| --- | --- |
| File | `examples/llm_review_artifacts/single-file/input.md` |
| Profile | `artifact-single-file` |
| Total Findings | 2 |
| Quality Gate | Not configured |

## Severity Counts

| Severity | Count |
| --- | ---: |
| critical | 0 |
| error | 0 |
| warning | 1 |
| info | 1 |

## Rule Counts

| Rule | Count |
| --- | ---: |
| absolute_claims | 1 |
| unfinished_example | 1 |

## Findings

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| warning | absolute_claims | 7 | 17 | 发现可能存在绝对化表述：保证成功 | 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。 |
| info | unfinished_example | 11 | 6 | This draft still references an unfinished example or evidence note. | 补充案例或删除占位说明。 |

## Detailed Findings

### absolute_claims

- Severity: warning
- Message: 发现可能存在绝对化表述：保证成功
- Matched Term: `保证成功`
- Line: 7
- Column: 17
- Context: ...清单，方便团队内部复用。<br><br>这份 onboarding 清单保证成功，任何新同事照着做都能马上交付。<br><br>发布说明：请在正式对外前...
- Matched Text: `保证成功`
- Suggestion: 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。

### unfinished_example

- Severity: info
- Message: This draft still references an unfinished example or evidence note.
- Matched Term: `待补案例|待补证据`
- Line: 11
- Column: 6
- Context: ...说明：请在正式对外前补充适用范围和负责人备注。<br><br>证据部分：待补案例。<br>
- Matched Text: `待补案例`
- Suggestion: 补充案例或删除占位说明。
