# Schemas

This directory documents the canonical JSON payloads emitted by the core package and CLI.

Current file:

- `review-result.schema.json`: canonical `ReviewResult` payload for JSON CLI output and future API-style responses.
- `batch-review-result.schema.json`: canonical `BatchReviewResult` payload for batch JSON CLI output.

Notes:

- These schemas are documentation artifacts only.
- The project does not perform runtime JSON Schema validation as part of this task.
- The source of truth for the payload shape is `src/content_review_engine/core/models.py` and the serialization helpers in `src/content_review_engine/core/serialization.py`.
