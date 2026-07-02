# Batch Combined Content Review Report

## Artifact Boundary

- This file is an explicit batch combined artifact rendered from `BatchCombinedReviewResult`.
- It packages deterministic batch review data with optional batch LLM data for browsing, but it does not replace deterministic batch `--output` or raw batch `--llm-output`.
- LLM findings remain advisory and presentation-only in this report.

## Deterministic Batch Summary

| Field | Value |
| --- | --- |
| Files Discovered | 1 |
| Files Reviewed | 1 |
| Files With Findings | 1 |
| Total Findings | 6 |
| Severity Counts | info=1, warning=5, error=0, critical=0 |
| Rule Counts | absolute_claims=2, absolute_technical_claim=1, markdown_links_images=1, unresolved_draft_marker=1, unresolved_example=1 |
| Quality Gate Source | deterministic findings only |

## LLM Batch Summary

| Field | Value |
| --- | --- |
| LLM Batch Status | all_succeeded |
| LLM Provider | mock |
| LLM Provider Source | explicit |
| LLM Total Files | 1 |
| LLM Succeeded | 1 |
| LLM Failed | 0 |
| LLM Skipped | 0 |
| LLM Not Run | 0 |
| LLM Advisory Findings | 0 |
| Files With LLM Advisory Findings | 0 |
| LLM Errors | 0 |
| Advisory | yes |
| Quality Gate Participation | no |
| Explicit LLM Gate | enabled |
| LLM Gate Threshold | warning |
| LLM Gate Status | passed |
| LLM Gate Evaluation | evaluated |
| LLM Gate Matched Files | 0 |
| LLM Gate Matched Findings | 0 |
| LLM Gate Matched Severity Counts | info=0, warning=0, error=0, critical=0 |
| Policy Note | LLM findings are advisory semantic review suggestions from the LLM layer. They do not participate in deterministic finding counts, fail-on, or quality gate. |

## Combined File Results

| File | Deterministic Findings | LLM Status | LLM Advisory Findings | LLM Error |
| --- | ---: | --- | ---: | --- |
| examples/demo/articles/technical-demo.md | 6 | succeeded | 0 | - |

## Deterministic Findings by File

### examples/demo/articles/technical-demo.md

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| warning | absolute_claims | 5 | 10 | 发现可能存在绝对化表述：完全兼容 | 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。 |
| warning | absolute_claims | 5 | 17 | 发现可能存在绝对化表述：零风险 | 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。 |
| warning | markdown_links_images | 13 | 6 | 链接目标仍是占位符。 | - |
| warning | absolute_technical_claim | 7 | 8 | This technical claim may be too absolute for a general blog post. | Qualify the claim and describe scope, tradeoffs, or test conditions. |
| warning | unresolved_draft_marker | 9 | 1 | Resolve draft markers before publishing the technical post. | Replace the marker with completed guidance or remove it. |
| info | unresolved_example | 11 | 1 | This draft still references an unfinished example or benchmark. | Add the missing example, screenshot, or benchmark details. |

## LLM Findings by File

No LLM advisory findings across reviewed files.

## LLM Error Summary

No LLM errors.

## Manual Review Workflow

- Review deterministic findings first; they remain the canonical batch output and the only quality-gate source.
- Treat LLM findings as advisory semantic suggestions that require human confirmation before any content change.
- Manual review checklist state is presentation-only and is not persisted into BatchReviewResult, LLMSidecarResult, or any review-state file.
- The LLM review succeeded but returned no advisory findings; if semantic risk still matters, perform manual spot checks.

## Manual Review Checklist

No manual review checklist items.

## Quality Gate Behavior

- Deterministic batch quality gate evaluation remains unchanged and still reads deterministic findings only.
- LLM advisory findings do not participate in deterministic severity counts, deterministic rule counts, or batch `--fail-on`.
- When `--llm-fail-on` is not set, batch LLM findings do not affect CLI exit code.
- When `--llm-fail-on` is set, it is evaluated independently from deterministic `--fail-on` and can also trigger CLI exit code `1`.

## Artifact Notes

- `--output`, `--llm-output`, and `--combined-output` can coexist in the same batch run.
- Use deterministic batch `--output` as the canonical automation artifact and raw batch `--llm-output` as the canonical machine-readable LLM artifact.
- This combined Markdown report is a presentation artifact derived from the combined envelope and does not replace either JSON contract.
