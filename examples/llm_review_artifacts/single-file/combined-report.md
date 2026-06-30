# Combined Content Review Report

## Artifact Boundary

- This file is an explicit combined artifact rendered from `SingleFileCombinedReviewResult`.
- It preserves deterministic review data and optional LLM review data in one human-readable report, but it does not replace canonical deterministic `--output` or raw `--llm-output` artifacts.
- LLM findings remain advisory and presentation-only in this report.

## Deterministic Review Summary

| Field | Value |
| --- | --- |
| File | examples/llm_review_artifacts/single-file/input.md |
| Profile | artifact-single-file |
| Total Findings | 2 |
| Severity Counts | info=1, warning=1, error=0, critical=0 |
| Rule Counts | absolute_claims=1, unfinished_example=1 |
| Quality Gate Source | deterministic findings only |

## Deterministic Findings

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| warning | absolute_claims | 7 | 17 | 发现可能存在绝对化表述：保证成功 | 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。 |
| info | unfinished_example | 11 | 6 | This draft still references an unfinished example or evidence note. | 补充案例或删除占位说明。 |

## LLM Review Summary

| Field | Value |
| --- | --- |
| Status | succeeded |
| Schema Version | llm-review-result.v1 |
| Provider | mock |
| Model | mock-llm-v1 |
| Prompt Version | llm-semantic-review-prompt.v1 |
| Profile Name | artifact-single-file |
| Advisory Findings | 2 |
| Advisory | yes |
| Quality Gate Participation | no |
| Explicit LLM Gate | disabled |
| LLM Gate Threshold | - |
| LLM Gate Status | passed |
| LLM Gate Evaluation | disabled |
| LLM Gate Matched Findings | 0 |
| LLM Gate Matched Severity Counts | info=0, warning=0, error=0, critical=0 |
| Policy Note | LLM findings are advisory semantic review suggestions from the LLM layer. They do not participate in deterministic finding counts, fail-on, or quality gate. |
| LLM Error | - |

## LLM Findings

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

## Quality Gate Behavior

- Quality gate evaluation remains deterministic-only.
- LLM advisory findings do not participate in severity counts, rule counts, fail-on, quality gate, or exit code.
- When `--llm-fail-on` is not set, LLM findings do not affect CLI exit code.
- When `--llm-fail-on` is set, it is evaluated independently from deterministic `--fail-on` and can also trigger CLI exit code `1`.

## Artifact Notes

- `--output`, `--llm-output`, and `--combined-output` can coexist in the same run.
- Use deterministic `--output` as the canonical automation artifact and raw `--llm-output` as the canonical machine-readable LLM artifact.
- This combined Markdown report is a presentation artifact derived from the combined envelope and does not replace either JSON contract.
