#!/usr/bin/env bash
set -euo pipefail

echo "== Git status =="
git status --short --branch

if [[ -n "$(git status --short)" ]]; then
  echo "Working tree is not clean."
  exit 1
fi

echo "== Recent commits =="
git log --oneline -5

echo "== Run tests =="
uv run pytest

echo "== Check required files =="
test -f PROJECT_STATE.md
test -f CHANGELOG.md
test -d tasks
test -x scripts/check-task.sh

echo "== Done =="
