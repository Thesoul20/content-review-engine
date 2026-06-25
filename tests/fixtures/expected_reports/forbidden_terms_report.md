# Content Review Report

## Summary

| Field | Value |
| --- | --- |
| File | `tests/fixtures/markdown/forbidden_terms_article.md` |
| Profile | `tests/fixtures/profiles/default.yml` |
| Total Findings | 1 |
| Quality Gate | Not configured |

## Severity Counts

| Severity | Count |
| --- | ---: |
| critical | 0 |
| error | 0 |
| warning | 1 |
| info | 0 |

## Rule Counts

| Rule | Count |
| --- | ---: |
| forbidden_terms | 1 |

## Findings

| Severity | Rule | Line | Column | Message | Suggestion |
| --- | --- | ---: | ---: | --- | --- |
| warning | forbidden_terms | 1 | 8 | 发现风险词：绝对安全 | - |

## Detailed Findings

### forbidden_terms

- Severity: warning
- Message: 发现风险词：绝对安全
- Matched Term: `绝对安全`
- Line: 1
- Column: 8
- Context: # 测试文章 绝对安全
- Matched Text: `绝对安全`
