#!/usr/bin/env bash
set -euo pipefail

# Purpose: Keep a feature branch up to date with latest main via merge or rebase.
#
# Usage:
#   bash scripts/git/sync_with_main.sh \
#     --branch feat/pdf-ingestion \
#     --mode merge|rebase \
#     --remote origin
#
# Notes:
#   - Requires a clean working tree.
#   - If --branch is omitted, operates on current branch.

TARGET_BRANCH=""
MODE="merge"   # or rebase
REMOTE="origin"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch) TARGET_BRANCH="$2"; shift 2;;
    --mode) MODE="$2"; shift 2;;
    --remote) REMOTE="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not a git repository" >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Error: working tree not clean. Commit or stash changes first." >&2
  exit 1
fi

CUR=$(git rev-parse --abbrev-ref HEAD)
if [[ -z "$TARGET_BRANCH" ]]; then
  TARGET_BRANCH="$CUR"
fi

if ! git show-ref --quiet --heads "$TARGET_BRANCH"; then
  echo "Error: branch $TARGET_BRANCH not found locally." >&2
  exit 1
fi

echo "Fetching latest main from $REMOTE ..."
git fetch "$REMOTE" main

echo "Switching to $TARGET_BRANCH ..."
git checkout "$TARGET_BRANCH"

if [[ "$MODE" == "rebase" ]]; then
  echo "Rebasing $TARGET_BRANCH onto $REMOTE/main ..."
  git rebase "refs/remotes/$REMOTE/main"
else
  echo "Merging $REMOTE/main into $TARGET_BRANCH ..."
  git merge --no-edit "refs/remotes/$REMOTE/main"
fi

cat <<EOF
Synced $TARGET_BRANCH with $REMOTE/main using $MODE.
If conflicts occurred, resolve them and continue (rebase --continue / commit merge).
EOF

