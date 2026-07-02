#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT"

uv sync --extra mcp --group dev

uv run pytest

uv run content-review --help >/dev/null
uv run content-review-mcp --help >/dev/null

uv run content-review profile validate profiles/examples/wechat-article.yaml
uv run content-review profile validate examples/demo/profiles/wechat-demo.yaml
uv run content-review profile validate examples/demo/profiles/technical-demo.yaml

uv run content-review review \
  examples/demo/articles/wechat-demo.md \
  --profile examples/demo/profiles/wechat-demo.yaml

uv run content-review batch \
  examples/demo/articles \
  --profile examples/demo/profiles/technical-demo.yaml \
  --pattern 'technical-*.md'
