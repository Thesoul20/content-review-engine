# Batch Combined Content Review Report

## Artifact Boundary

- This file is an explicit batch combined artifact rendered from `BatchCombinedReviewResult`.
- It packages deterministic batch review data with optional batch LLM data for browsing, but it does not replace deterministic batch `--output` or raw batch `--llm-output`.
- LLM findings remain advisory and presentation-only in this report.

## Deterministic Batch Summary

| Field | Value |
| --- | --- |
| Files Discovered | 3 |
| Files Reviewed | 3 |
| Files With Findings | 2 |
| Total Findings | 2 |
| Severity Counts | info=1, warning=1, error=0, critical=0 |
| Rule Counts | absolute_claims=1, missing_evidence_note=1 |
| Quality Gate Source | deterministic findings only |

## LLM Batch Summary

| Field | Value |
| --- | --- |
| LLM Batch Status | partial_failure |
| LLM Provider | mock |
| LLM Provider Source | config |
| LLM Total Files | 3 |
| LLM Succeeded | 2 |
| LLM Failed | 1 |
| LLM Skipped | 0 |
| LLM Not Run | 0 |
| LLM Advisory Findings | 2 |
| Files With LLM Advisory Findings | 2 |
| LLM Errors | 1 |
| Advisory | yes |
| Quality Gate Participation | no |
| Explicit LLM Gate | disabled |
| LLM Gate Threshold | - |
| LLM Gate Status | passed |
| LLM Gate Evaluation | disabled |
| LLM Gate Matched Files | 0 |
| LLM Gate Matched Findings | 0 |
| LLM Gate Matched Severity Counts | info=0, warning=0, error=0, critical=0 |
| Policy Note | LLM findings are advisory semantic review suggestions from the LLM layer. They do not participate in deterministic finding counts, fail-on, or quality gate. |

## Combined File Results

| File | Deterministic Findings | LLM Status | LLM Advisory Findings | LLM Error |
| --- | ---: | --- | ---: | --- |
| examples/llm_review_artifacts/batch/input/article-a.md | 1 | succeeded | 1 | - |
| examples/llm_review_artifacts/batch/input/article-b.md | 1 | succeeded | 1 | - |
| examples/llm_review_artifacts/batch/input/article-with-llm-error.md | 0 | failed | 0 | RuntimeError: provider timeout during semantic review |

## Deterministic Findings by File

### examples/llm_review_artifacts/batch/input/article-a.md

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| warning | absolute_claims | 5 | 13 | 发现可能存在绝对化表述：马上交付 | 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。 |

### examples/llm_review_artifacts/batch/input/article-b.md

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| info | missing_evidence_note | 7 | 4 | This draft still contains an evidence placeholder. | 补充数据来源或删除占位说明。 |

### examples/llm_review_artifacts/batch/input/article-with-llm-error.md

No deterministic findings.

## LLM Findings by File

| File | Severity | Rule | Source | Advisory | Quality Gate | Confidence | Location | Message | Suggestion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| examples/llm_review_artifacts/batch/input/article-a.md | warning | llm.semantic_overclaim | llm | yes | no | not provided | 3:14 | The onboarding benefit sounds broader than the draft supports. | Describe the rollout conditions and expected audience more precisely. |
| examples/llm_review_artifacts/batch/input/article-b.md | critical | llm.semantic_needs_human_review | llm | yes | no | 0.74 | - | The process recommendation needs a human check because it implies a broad staffing conclusion without review evidence. | Ask an editor or operations owner to confirm the staffing claim before reuse. |

## LLM Error Summary

| File | Type | Message | Provider | Retryable |
| --- | --- | --- | --- | --- |
| examples/llm_review_artifacts/batch/input/article-with-llm-error.md | RuntimeError | provider timeout during semantic review | - | - |

## Manual Review Workflow

- Review deterministic findings first; they remain the canonical batch output and the only quality-gate source.
- Treat LLM findings as advisory semantic suggestions that require human confirmation before any content change.
- Manual review checklist state is presentation-only and is not persisted into BatchReviewResult, LLMSidecarResult, or any review-state file.
- This batch has partial LLM failure; inspect the LLM error summary, decide whether failed files should be rerun, and keep deterministic findings as the baseline for every file.
- Current execution follow-up items: 1.

## Manual Review Checklist

| ID | File | Priority | Status | Decision | Quality Gate | Rule | Location | Message | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LLM-001 | examples/llm_review_artifacts/batch/input/article-a.md | medium | needs_review | pending | no | llm.semantic.overclaim | line 3, column 14 to line 3, column 18 | The onboarding benefit sounds broader than the draft supports. | - |
| LLM-002 | examples/llm_review_artifacts/batch/input/article-b.md | high | needs_review | pending | no | llm.semantic.needs_human_review | not provided | The process recommendation needs a human check because it implies a broad staffing conclusion without review evidence. | - |

## LLM Execution Review Checklist

| ID | File | Status | Suggested Action | Error Type | Error Message | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| LLM-ERR-001 | examples/llm_review_artifacts/batch/input/article-with-llm-error.md | needs_rerun | rerun_llm_review | RuntimeError | provider timeout during semantic review | - |

## Quality Gate Behavior

- Quality gate evaluation remains deterministic-only.
- LLM advisory findings do not participate in severity counts, rule counts, fail-on, quality gate, or exit code.
- When `--llm-fail-on` is not set, LLM findings do not affect CLI exit code.
- When `--llm-fail-on` is set, it is evaluated independently from deterministic `--fail-on` and can also trigger CLI exit code `1`.

## Artifact Notes

- `--output`, `--llm-output`, and `--combined-output` can coexist in the same batch run.
- Use deterministic batch `--output` as the canonical automation artifact and raw batch `--llm-output` as the canonical machine-readable LLM artifact.
- This combined Markdown report is a presentation artifact derived from the combined envelope and does not replace either JSON contract.
