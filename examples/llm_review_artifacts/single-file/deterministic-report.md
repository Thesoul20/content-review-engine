# Content Review Report

## Summary

| Field | Value |
| --- | --- |
| File | `examples/llm_review_artifacts/single-file/input.md` |
| Profile | `examples/llm_review_artifacts/single-file/profile.yml` |
| Total Findings | 2 |
| Quality Gate | Failed |
| Fail On | `warning` |
| Matched Gate Findings | 1 |

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
| warning | absolute_claims | 5 | 12 | 发现可能存在绝对化表述：保证成功 | 建议改为描述条件、范围和证据的审慎表述。 |
| info | unfinished_example | 7 | 6 | This draft still references an unfinished example or evidence note. | 补充案例或删除占位说明。 |

## Detailed Findings

### absolute_claims

- Severity: warning
- Message: 发现可能存在绝对化表述：保证成功
- Matched Term: `保证成功`
- Line: 5
- Column: 12
- Context: 这份 onboarding 清单保证成功，任何新同事照着做都能马上交付。
- Matched Text: `保证成功`
- Suggestion: 建议改为描述条件、范围和证据的审慎表述。

### unfinished_example

- Severity: info
- Message: This draft still references an unfinished example or evidence note.
- Matched Term: `待补案例`
- Line: 7
- Column: 6
- Context: 证据部分：待补案例。
- Matched Text: `待补案例`
- Suggestion: 补充案例或删除占位说明。
