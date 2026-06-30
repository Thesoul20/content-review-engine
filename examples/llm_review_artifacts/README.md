# LLM Review Artifact Examples

This directory is a committed reference set for the current LLM review
artifact layout.

Use it to inspect how deterministic review output, LLM JSON sidecars, LLM
Markdown reports, combined outputs, and report indexes relate to each other
without running a provider call.

All files in this directory are reference-only examples. They are not runtime
dependencies, schema definitions, or inputs that the package reads
automatically.

## Layout

```text
examples/llm_review_artifacts/
  README.md
  single-file/
    input.md
    profile.yml
    deterministic-report.md
    llm-result.json
    llm-report.md
    combined-result.json
    combined-report.md
    review-index.md
  batch/
    input/
      article-a.md
      article-b.md
      article-with-llm-error.md
    profile.yml
    deterministic-report.md
    batch-llm-result.json
    batch-llm-report.md
    batch-combined-result.json
    batch-combined-report.md
    batch-review-index.md
```

## Artifact Map

| Artifact | Format | Source | Purpose | Canonical |
| --- | --- | --- | --- | --- |
| `single-file/deterministic-report.md` | Markdown | deterministic review | Human-readable deterministic report example | no |
| `single-file/llm-result.json` | JSON | LLM review | Machine-readable single-file LLM result example | yes, for LLM layer |
| `single-file/llm-report.md` | Markdown | LLM review | Human-readable advisory LLM report example | no |
| `single-file/combined-result.json` | JSON | combined output | Machine-readable single-file combined envelope example | yes, for combined output |
| `single-file/combined-report.md` | Markdown | combined output | Human-readable single-file combined report example | no |
| `single-file/review-index.md` | Markdown | report index | Navigation and interpretation example | no |
| `batch/deterministic-report.md` | Markdown | deterministic batch review | Human-readable batch deterministic report example | no |
| `batch/batch-llm-result.json` | JSON | batch LLM review | Machine-readable aggregate LLM result example | yes, for LLM layer |
| `batch/batch-llm-report.md` | Markdown | batch LLM review | Human-readable aggregate advisory LLM report example | no |
| `batch/batch-combined-result.json` | JSON | combined output | Machine-readable batch combined envelope example | yes, for combined output |
| `batch/batch-combined-report.md` | Markdown | combined output | Human-readable batch combined report example | no |
| `batch/batch-review-index.md` | Markdown | report index | Batch navigation and interpretation example | no |

## How To Read These Examples

Start with the deterministic report to see the rule-based review layer.

Then read the LLM JSON sidecar to inspect the machine-readable advisory result.

Then read the combined JSON artifact to inspect how deterministic output and
raw LLM output are packaged together without changing either canonical schema.

Then read the LLM Markdown report and combined Markdown report to inspect
advisory policy, manual review checklist items, quality-gate boundary text,
and, in the batch example, execution review checklist items.

Finish with the report index to see the manual review workflow and the
interpretation boundary across outputs.

## Canonical And Presentation Boundary

The canonical deterministic data models remain `ReviewResult` and
`BatchReviewResult`.

The canonical LLM-layer data models remain `LLMReviewResult` for single-file
output and `LLMSidecarResult` for batch output.

The canonical combined-output data models remain
`SingleFileCombinedReviewResult` for single-file output and
`BatchCombinedReviewResult` for batch output.

The Markdown files in this directory are presentation artifacts derived from
those models. They are examples for browsing and review, not replacement
schemas.
The combined Markdown examples also show the current stable section contract
for `Artifact Boundary`, deterministic summary/findings, LLM summary/findings,
manual review workflow, deterministic-only `Quality Gate Behavior`, and
`Artifact Notes`.

## Deterministic And LLM Boundary

Deterministic review is the stable review layer.

LLM findings are advisory semantic review suggestions. They stay outside
deterministic finding counts, `--fail-on`, and quality gate decisions.

Combined output is explicit opt-in. It does not auto-enable LLM review, and
combined examples that include LLM content are only showing the artifact shape
after an LLM-enabled run.

Quality gate interpretation remains deterministic-only even when LLM artifacts
exist beside the deterministic output.

`--output`, `--llm-output`, and `--combined-output` remain separate output
families:

- `--output`: deterministic main output
- `--llm-output`: raw LLM sidecar output
- `--combined-output`: deterministic + LLM combined envelope or report output

## Manual Review Checklist Boundary

Manual review checklist items are presentation-only workflow hints for human
follow-up.

Checklist status, decision, rerun, and notes values are not persisted to a
review-state file or back into JSON sidecars.

The batch example also shows a partial failure case. One file keeps its
deterministic result, while the aggregate LLM sidecar and Markdown report mark
the LLM execution failure separately and add an execution review checklist item
for rerun handling.

The committed JSON examples are parseable reference artifacts. The committed
combined Markdown examples include `## Artifact Boundary`,
`## Deterministic Review Summary` or `## Deterministic Batch Summary`,
`## Quality Gate Behavior`, and artifact-notes sections so tests can verify
the current presentation contract without making `examples/` part of runtime
behavior.
