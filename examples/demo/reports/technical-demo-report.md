# Content Review Report

## Summary

| Field | Value |
| --- | --- |
| File | `examples/demo/articles/technical-demo.md` |
| Profile | `examples/demo/profiles/technical-demo.yaml` |
| Total Findings | 6 |
| Quality Gate | Failed |
| Fail On | `warning` |
| Matched Gate Findings | 5 |

## Severity Counts

| Severity | Count |
| --- | ---: |
| critical | 0 |
| error | 0 |
| warning | 5 |
| info | 1 |

## Rule Counts

| Rule | Count |
| --- | ---: |
| absolute_claims | 2 |
| absolute_technical_claim | 1 |
| markdown_links_images | 1 |
| unresolved_draft_marker | 1 |
| unresolved_example | 1 |

## Findings

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| warning | absolute_claims | 5 | 10 | 发现可能存在绝对化表述：完全兼容 | 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。 |
| warning | absolute_claims | 5 | 17 | 发现可能存在绝对化表述：零风险 | 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。 |
| warning | markdown_links_images | 13 | 6 | 链接目标仍是占位符。 | - |
| warning | absolute_technical_claim | 7 | 8 | This technical claim may be too absolute for a general blog post. | Qualify the claim and describe scope, tradeoffs, or test conditions. |
| warning | unresolved_draft_marker | 9 | 1 | Resolve draft markers before publishing the technical post. | Replace the marker with completed guidance or remove it. |
| info | unresolved_example | 11 | 1 | This draft still references an unfinished example or benchmark. | Add the missing example, screenshot, or benchmark details. |

## Detailed Findings

### absolute_claims

- Severity: warning
- Message: 发现可能存在绝对化表述：完全兼容
- Matched Term: `完全兼容`
- Line: 5
- Column: 10
- Context: ...这篇记录用于整理命令行发布前的检查项。<br><br>当前方案在旧环境里完全兼容，而且零风险。<br><br>缓存层在高峰期永远不会产生延迟抖动。<br><br>T...
- Matched Text: `完全兼容`
- Suggestion: 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。

### absolute_claims

- Severity: warning
- Message: 发现可能存在绝对化表述：零风险
- Matched Term: `零风险`
- Line: 5
- Column: 17
- Context: ...理命令行发布前的检查项。<br><br>当前方案在旧环境里完全兼容，而且零风险。<br><br>缓存层在高峰期永远不会产生延迟抖动。<br><br>TODO: 补...
- Matched Text: `零风险`
- Suggestion: 建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，或补充支撑该结论的证据。

### markdown_links_images

- Severity: warning
- Message: 链接目标仍是占位符。
- Matched Term: `placeholder_link_target`
- Line: 13
- Column: 6
- Context: ...s 终端截图。<br><br>示例待补：补上回滚命令输出。<br><br>参考链接：[迁移步骤](#)<br><br>FIXME: 这个草稿标记专门用于 suppressio...
- Matched Text: `[迁移步骤](#)`

### absolute_technical_claim

- Severity: warning
- Message: This technical claim may be too absolute for a general blog post.
- Matched Term: `永远不会|绝不会|100% 兼容|没有任何性能损耗`
- Line: 7
- Column: 8
- Context: ...<br>当前方案在旧环境里完全兼容，而且零风险。<br><br>缓存层在高峰期永远不会产生延迟抖动。<br><br>TODO: 补上 Windows 终端截图...
- Matched Text: `永远不会`
- Suggestion: Qualify the claim and describe scope, tradeoffs, or test conditions.

### unresolved_draft_marker

- Severity: warning
- Message: Resolve draft markers before publishing the technical post.
- Matched Term: `TODO|FIXME|待验证`
- Line: 9
- Column: 1
- Context: ...容，而且零风险。<br><br>缓存层在高峰期永远不会产生延迟抖动。<br><br>TODO: 补上 Windows 终端截图。<br><br>示例待补：补上回滚命...
- Matched Text: `TODO`
- Suggestion: Replace the marker with completed guidance or remove it.

### unresolved_example

- Severity: info
- Message: This draft still references an unfinished example or benchmark.
- Matched Term: `示例待补|截图待补|benchmark 待补|基准待补`
- Line: 11
- Column: 1
- Context: ...迟抖动。<br><br>TODO: 补上 Windows 终端截图。<br><br>示例待补：补上回滚命令输出。<br><br>参考链接：[迁移步骤](#)<br><br>FI...
- Matched Text: `示例待补`
- Suggestion: Add the missing example, screenshot, or benchmark details.