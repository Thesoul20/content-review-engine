# Batch Content Review Report

## Summary

| Field | Value |
| --- | --- |
| Files Discovered | 3 |
| Files Reviewed | 3 |
| Files With Findings | 2 |
| Total Findings | 2 |
| Quality Gate | Passed |
| Fail On | `error` |
| Matched Gate Findings | 0 |

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
| warning | absolute_claims | 3 | 14 | 发现可能存在绝对化表述：马上交付 | 建议补充适用条件或改为更保守的结果描述。 |

#### Detailed Findings

### absolute_claims

- Severity: warning
- Message: 发现可能存在绝对化表述：马上交付
- Matched Term: `马上交付`
- Line: 3
- Column: 14
- Context: 这份 SOP 能让新同事马上交付。
- Matched Text: `马上交付`
- Suggestion: 建议补充适用条件或改为更保守的结果描述。

### `examples/llm_review_artifacts/batch/input/article-b.md`

#### Findings

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| info | missing_evidence_note | 6 | 4 | This draft still contains an evidence placeholder. | 补充数据来源或删除占位说明。 |

#### Detailed Findings

### missing_evidence_note

- Severity: info
- Message: This draft still contains an evidence placeholder.
- Matched Term: `补充数据`
- Line: 6
- Column: 4
- Context: 备注：补充数据。
- Matched Text: `补充数据`
- Suggestion: 补充数据来源或删除占位说明。

### `examples/llm_review_artifacts/batch/input/article-with-llm-error.md`

#### Findings

No findings.

#### Detailed Findings

No findings.
