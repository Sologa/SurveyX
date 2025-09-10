#!/usr/bin/env bash
set -euo pipefail

# Purpose: Rename a local branch (optionally the current one) and sync to remote.
#
# Usage:
#   bash scripts/git/rename_branch.sh \
#     --old feat/newest_dev \
#     --new feat/pdf-ingestion \
#     --remote origin \
#     --push
#
# Notes:
#   - Works even if you are currently on the old branch name.
#   - Requires a clean working tree.

OLD_NAME=""
NEW_NAME=""
REMOTE="origin"
DO_PUSH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --old) OLD_NAME="$2"; shift 2;;
    --new) NEW_NAME="$2"; shift 2;;
    --remote) REMOTE="$2"; shift 2;;
    --push) DO_PUSH=true; shift 1;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ -z "$NEW_NAME" ]]; then
  echo "Error: --new <new-branch-name> is required" >&2
  exit 1
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not a git repository" >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Error: working tree not clean. Commit or stash changes first." >&2
  exit 1
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [[ -n "$OLD_NAME" ]]; then
  # explicit old name provided
  if git show-ref --quiet --heads "$NEW_NAME"; then
    echo "Error: target branch $NEW_NAME already exists." >&2
    exit 1
  fi
  echo "Renaming $OLD_NAME -> $NEW_NAME ..."
  git branch -m "$OLD_NAME" "$NEW_NAME"
else
  # rename current branch
  echo "Renaming current branch $CURRENT_BRANCH -> $NEW_NAME ..."
  git branch -m "$NEW_NAME"
  OLD_NAME="$CURRENT_BRANCH"
fi

if [[ "$DO_PUSH" == true ]]; then
  echo "Syncing to remote $REMOTE ..."
  # delete old remote branch if it exists
  if git ls-remote --heads "$REMOTE" "$OLD_NAME" | grep -q "$OLD_NAME"; then
    git push "$REMOTE" ":$OLD_NAME" || true
  fi
  # push new and set upstream
  git push -u "$REMOTE" "$NEW_NAME"
fi

cat <<EOF
Branch renamed:
  Old name : $OLD_NAME
  New name : $NEW_NAME
Remote sync: $DO_PUSH (remote=$REMOTE)
EOF

