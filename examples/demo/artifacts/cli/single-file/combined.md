# Combined Content Review Report

## Artifact Boundary

- This file is an explicit combined artifact rendered from `SingleFileCombinedReviewResult`.
- It preserves deterministic review data and optional LLM review data in one human-readable report, but it does not replace canonical deterministic `--output` or raw `--llm-output` artifacts.
- LLM findings remain advisory and presentation-only in this report.

## Deterministic Review Summary

| Field | Value |
| --- | --- |
| File | examples/demo/articles/wechat-demo.md |
| Profile | examples/demo/profiles/wechat-demo.yaml |
| Total Findings | 6 |
| Severity Counts | info=2, warning=4, error=0, critical=0 |
| Rule Counts | absolute_claims=1, article_placeholder=1, engagement_bait=2, exaggerated_claims=1, markdown_links_images=1 |
| Quality Gate Source | deterministic findings only |

## Deterministic Findings

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| warning | absolute_claims | 5 | 14 | 发现可能存在绝对化表述：唯一选择 | 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。 |
| warning | markdown_links_images | 11 | 6 | 链接目标仍是占位符。 | - |
| info | engagement_bait | 1 | 3 | This phrase may read as engagement bait. | Prefer a clearer and more direct headline or transition. |
| warning | exaggerated_claims | 5 | 14 | Avoid absolute or exaggerated wording in public-facing drafts. | Use narrower wording and add evidence where needed. |
| info | engagement_bait | 7 | 22 | This phrase may read as engagement bait. | Prefer a clearer and more direct headline or transition. |
| warning | article_placeholder | 9 | 6 | Remove unfinished article placeholders before publishing. | Replace the placeholder with final article content. |

## LLM Review Summary

| Field | Value |
| --- | --- |
| Status | succeeded |
| Schema Version | llm-review-result.v1 |
| Provider | - |
| Model | - |
| Prompt Version | - |
| Profile Name | - |
| Advisory Findings | 0 |
| Advisory | yes |
| Quality Gate Participation | no |
| Explicit LLM Gate | enabled |
| LLM Gate Threshold | warning |
| LLM Gate Status | passed |
| LLM Gate Evaluation | evaluated |
| LLM Gate Matched Findings | 0 |
| LLM Gate Matched Severity Counts | info=0, warning=0, error=0, critical=0 |
| Policy Note | LLM findings are advisory semantic review suggestions from the LLM layer. They do not participate in deterministic finding counts, fail-on, or quality gate. |
| LLM Error | - |

## LLM Findings

LLM review succeeded but returned no advisory findings.

## Manual Review Workflow

- Review deterministic findings first; they remain the canonical review output and the only quality-gate source.
- Treat LLM findings as advisory semantic suggestions that require human confirmation before any content change.
- Manual review checklist state is presentation-only and is not persisted into ReviewResult, sidecar JSON, or any review-state file.
- The LLM review succeeded but returned no advisory findings; if semantic risk still matters, perform manual spot-checking.

## Manual Review Checklist

No manual review checklist items.

## Quality Gate Behavior

- Deterministic quality gate evaluation remains unchanged and still reads deterministic findings only.
- LLM advisory findings do not participate in deterministic severity counts, deterministic rule counts, or `--fail-on`.
- When `--llm-fail-on` is not set, LLM findings do not affect CLI exit code.
- When `--llm-fail-on` is set, it is evaluated independently from deterministic `--fail-on` and can also trigger CLI exit code `1`.

## Artifact Notes

- `--output`, `--llm-output`, and `--combined-output` can coexist in the same run.
- Use deterministic `--output` as the canonical automation artifact and raw `--llm-output` as the canonical machine-readable LLM artifact.
- This combined Markdown report is a presentation artifact derived from the combined envelope and does not replace either JSON contract.
