# Batch Combined Content Review Report

## Summary

| Field | Value |
| --- | --- |
| Files Reviewed | 3 |
| Deterministic Findings | 2 |
| LLM Total Files | 3 |
| LLM Succeeded | 2 |
| LLM Failed | 1 |
| LLM Skipped | 0 |
| LLM Not Run | 0 |
| LLM Advisory Findings | 2 |
| Files With LLM Advisory Findings | 2 |
| LLM Errors | 1 |
| Quality Gate Scope | deterministic-only |

## LLM Summary

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
| Policy Note | LLM findings are advisory semantic review suggestions from the LLM layer. They do not participate in deterministic finding counts, fail-on, or quality gate. |

## File Status Summary

| File | Status | Advisory Findings | Error |
| --- | --- | ---: | --- |
| examples/llm_review_artifacts/batch/input/article-a.md | succeeded | 1 | - |
| examples/llm_review_artifacts/batch/input/article-b.md | succeeded | 1 | - |
| examples/llm_review_artifacts/batch/input/article-with-llm-error.md | failed | 0 | RuntimeError: provider timeout during semantic review |

## LLM Advisory Findings

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

## Quality Gate Boundary

- Quality gate evaluation remains deterministic-only.
- LLM advisory findings do not participate in severity counts, rule counts, fail-on, quality gate, or exit code.
- Use the deterministic batch report below as the canonical audit record for automation and compliance checks.

## Deterministic Review

# Batch Content Review Report

## Summary

| Field | Value |
| --- | --- |
| Files Discovered | 3 |
| Files Reviewed | 3 |
| Files With Findings | 2 |
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
| missing_evidence_note | 1 |

## Files With Findings

| File | Findings | Highest Severity |
| --- | ---: | --- |
| `examples/llm_review_artifacts/batch/input/article-a.md` | 1 | warning |
| `examples/llm_review_artifacts/batch/input/article-b.md` | 1 | info |

## Findings by File

### `examples/llm_review_artifacts/batch/input/article-a.md`

#### Findings

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| warning | absolute_claims | 5 | 13 | 发现可能存在绝对化表述：马上交付 | 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。 |

#### Detailed Findings

### absolute_claims

- Severity: warning
- Message: 发现可能存在绝对化表述：马上交付
- Matched Term: `马上交付`
- Line: 5
- Column: 13
- Context: ...h LLM artifacts。<br><br>这份 SOP 能让新同事马上交付。<br><br>如果团队准备复用，请在正式发布前补充适用范围。<br>
- Matched Text: `马上交付`
- Suggestion: 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。

### `examples/llm_review_artifacts/batch/input/article-b.md`

#### Findings

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| info | missing_evidence_note | 7 | 4 | This draft still contains an evidence placeholder. | 补充数据来源或删除占位说明。 |

#### Detailed Findings

### missing_evidence_note

- Severity: info
- Message: This draft still contains an evidence placeholder.
- Matched Term: `补充数据|待补数据`
- Line: 7
- Column: 4
- Context: ...并存。<br><br>文中建议把流程复盘模板发给更多团队参考。<br><br>备注：补充数据。<br>
- Matched Text: `补充数据`
- Suggestion: 补充数据来源或删除占位说明。

### `examples/llm_review_artifacts/batch/input/article-with-llm-error.md`

#### Findings

No findings.

#### Detailed Findings

No findings.
