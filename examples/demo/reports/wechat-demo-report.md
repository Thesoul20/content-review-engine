# Content Review Report

## Summary

| Field | Value |
| --- | --- |
| File | `examples/demo/articles/wechat-demo.md` |
| Profile | `examples/demo/profiles/wechat-demo.yaml` |
| Total Findings | 6 |
| Quality Gate | Failed |
| Fail On | `warning` |
| Matched Gate Findings | 4 |

## Severity Counts

| Severity | Count |
| --- | ---: |
| critical | 0 |
| error | 0 |
| warning | 4 |
| info | 2 |

## Rule Counts

| Rule | Count |
| --- | ---: |
| absolute_claims | 1 |
| article_placeholder | 1 |
| engagement_bait | 2 |
| exaggerated_claims | 1 |
| markdown_links_images | 1 |

## Findings

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| warning | absolute_claims | 5 | 14 | 发现可能存在绝对化表述：唯一选择 | 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。 |
| warning | markdown_links_images | 11 | 6 | 链接目标仍是占位符。 | - |
| info | engagement_bait | 1 | 3 | This phrase may read as engagement bait. | Prefer a clearer and more direct headline or transition. |
| warning | exaggerated_claims | 5 | 14 | Avoid absolute or exaggerated wording in public-facing drafts. | Use narrower wording and add evidence where needed. |
| info | engagement_bait | 7 | 22 | This phrase may read as engagement bait. | Prefer a clearer and more direct headline or transition. |
| warning | article_placeholder | 9 | 6 | Remove unfinished article placeholders before publishing. | Replace the placeholder with final article content. |

## Detailed Findings

### absolute_claims

- Severity: warning
- Message: 发现可能存在绝对化表述：唯一选择
- Matched Term: `唯一选择`
- Line: 5
- Column: 14
- Context: ...用一篇短文说明它适合哪些场景。<br><br>这套方法几乎成了很多团队的唯一选择，我们也把它写成了一个方便转发的模板。<br><br>如果你正在赶项目，...
- Matched Text: `唯一选择`
- Suggestion: 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。

### markdown_links_images

- Severity: warning
- Message: 链接目标仍是占位符。
- Matched Term: `placeholder_link_target`
- Line: 11
- Column: 6
- Context: ...收藏这份清单，不看后悔。<br><br>配图位置：待补图。<br><br>领取清单：[下载链接](TODO)<br><br>术语说明：唯一标识符用于数据库主键。 <!-- cont...
- Matched Text: `[下载链接](TODO)`

### engagement_bait

- Severity: info
- Message: This phrase may read as engagement bait.
- Matched Term: `速看|不看后悔`
- Line: 1
- Column: 3
- Context: # 速看：协作提效清单<br><br>最近我们整理了一份团队协作清单，想先用一篇...
- Matched Text: `速看`
- Suggestion: Prefer a clearer and more direct headline or transition.

### exaggerated_claims

- Severity: warning
- Message: Avoid absolute or exaggerated wording in public-facing drafts.
- Matched Term: `唯一|第一|最强|100%`
- Line: 5
- Column: 14
- Context: ...用一篇短文说明它适合哪些场景。<br><br>这套方法几乎成了很多团队的唯一选择，我们也把它写成了一个方便转发的模板。<br><br>如果你正在赶项...
- Matched Text: `唯一`
- Suggestion: Use narrower wording and add evidence where needed.

### engagement_bait

- Severity: info
- Message: This phrase may read as engagement bait.
- Matched Term: `速看|不看后悔`
- Line: 7
- Column: 22
- Context: ...便转发的模板。<br><br>如果你正在赶项目，可以先赶紧收藏这份清单，不看后悔。<br><br>配图位置：待补图。<br><br>领取清单：[下载链接](TODO...
- Matched Text: `不看后悔`
- Suggestion: Prefer a clearer and more direct headline or transition.

### article_placeholder

- Severity: warning
- Message: Remove unfinished article placeholders before publishing.
- Matched Term: `待补图|待补链接|这里补充`
- Line: 9
- Column: 6
- Context: ...正在赶项目，可以先赶紧收藏这份清单，不看后悔。<br><br>配图位置：待补图。<br><br>领取清单：[下载链接](TODO)<br><br>术语说明：唯一标...
- Matched Text: `待补图`
- Suggestion: Replace the placeholder with final article content.