#!/usr/bin/env bash
set -euo pipefail

# Purpose: Delete a branch locally and/or remotely.
#
# Usage:
#   bash scripts/git/delete_branch.sh \
#     --name feat/newest_dev \
#     --remote origin \
#     --local --remote
#
# Flags:
#   --name   : branch name to delete (required)
#   --local  : delete local branch
#   --remote : delete remote branch on <remote> (default origin)
#
# Notes:
#   - Requires a clean working tree for local deletion.
#   - You cannot delete the branch you are currently on.

BRANCH_NAME=""
REMOTE="origin"
DEL_LOCAL=false
DEL_REMOTE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) BRANCH_NAME="$2"; shift 2;;
    --remote) REMOTE="$2"; shift 2;;
    --local) DEL_LOCAL=true; shift 1;;
    --remote-delete) DEL_REMOTE=true; shift 1;;
    --both) DEL_LOCAL=true; DEL_REMOTE=true; shift 1;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ -z "$BRANCH_NAME" ]]; then
  echo "Error: --name <branch> is required" >&2
  exit 1
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not a git repository" >&2
  exit 1
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [[ "$DEL_LOCAL" == true ]]; then
  if [[ "$CURRENT_BRANCH" == "$BRANCH_NAME" ]]; then
    echo "Error: cannot delete the current branch ($CURRENT_BRANCH). Checkout another branch first." >&2
    exit 1
  fi
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Error: working tree not clean. Commit or stash changes first." >&2
    exit 1
  fi
  if git show-ref --quiet --heads "$BRANCH_NAME"; then
    echo "Deleting local branch $BRANCH_NAME ..."
    git branch -D "$BRANCH_NAME"
  else
    echo "Local branch $BRANCH_NAME not found. Skipping local delete."
  fi
fi

if [[ "$DEL_REMOTE" == true ]]; then
  echo "Deleting remote branch $BRANCH_NAME on $REMOTE ..."
  git push "$REMOTE" ":$BRANCH_NAME" || true
fi

cat <<EOF
Delete summary:
  Branch : $BRANCH_NAME
  Local  : $DEL_LOCAL
  Remote : $DEL_REMOTE (remote=$REMOTE)
EOF

