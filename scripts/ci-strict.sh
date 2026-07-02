#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT"

"$REPO_ROOT/scripts/ci.sh"

uv build

python -m venv /tmp/content-review-engine-wheel-smoke
/tmp/content-review-engine-wheel-smoke/bin/pip install dist/*.whl
/tmp/content-review-engine-wheel-smoke/bin/content-review --help >/dev/null

uv run python examples/demo/run_demo.py

git diff --exit-code -- examples/demo README.md README.en.md report_demo.md docs
