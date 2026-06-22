#!/usr/bin/env bash
set -euo pipefail

echo "== Git status =="
git status --short

echo "== Run tests =="
uv run pytest

echo "== Check required files =="
test -f PROJECT_STATE.md
test -f CHANGELOG.md
test -d tasks

echo "== Done =="
