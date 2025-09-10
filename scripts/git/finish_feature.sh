#!/usr/bin/env bash
set -euo pipefail

# Purpose: Finish a feature branch by optionally merging into main and deleting the branch.
#
# Usage:
#   bash scripts/git/finish_feature.sh \
#     --branch feat/pdf-ingestion \
#     --target main \
#     --remote origin \
#     --merge-local \
#     --delete
#
# Behavior:
#   - Without --merge-local: push feature branch and print PR instructions.
#   - With --merge-local   : merge feature -> main locally, push main, optionally delete branch (local+remote).

FEATURE_BRANCH=""
TARGET_BRANCH="main"
REMOTE="origin"
MERGE_LOCAL=false
DO_DELETE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch) FEATURE_BRANCH="$2"; shift 2;;
    --target) TARGET_BRANCH="$2"; shift 2;;
    --remote) REMOTE="$2"; shift 2;;
    --merge-local) MERGE_LOCAL=true; shift 1;;
    --delete) DO_DELETE=true; shift 1;;
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
if [[ -z "$FEATURE_BRANCH" ]]; then
  FEATURE_BRANCH="$CUR"
fi

if [[ "$FEATURE_BRANCH" == "$TARGET_BRANCH" ]]; then
  echo "Error: feature branch equals target branch; specify --branch explicitly." >&2
  exit 1
fi

if ! git show-ref --quiet --heads "$FEATURE_BRANCH"; then
  echo "Error: branch $FEATURE_BRANCH not found locally." >&2
  exit 1
fi

echo "Fetching latest from $REMOTE ..."
git fetch "$REMOTE"

if [[ "$MERGE_LOCAL" == true ]]; then
  echo "Merging $FEATURE_BRANCH into $TARGET_BRANCH locally..."
  git checkout "$TARGET_BRANCH"
  # Ensure main is up-to-date
  git merge --ff-only "refs/remotes/$REMOTE/$TARGET_BRANCH" || true
  git merge --no-ff "$FEATURE_BRANCH"
  echo "Pushing $TARGET_BRANCH to $REMOTE ..."
  git push "$REMOTE" "$TARGET_BRANCH"

  if [[ "$DO_DELETE" == true ]]; then
    echo "Deleting feature branch locally and remotely..."
    git branch -D "$FEATURE_BRANCH" || true
    git push "$REMOTE" ":$FEATURE_BRANCH" || true
  fi

  cat <<EOF
Finished feature:
  Merged  : $FEATURE_BRANCH -> $TARGET_BRANCH (local)
  Deleted : $DO_DELETE
  Remote  : $REMOTE
EOF
else
  echo "Pushing $FEATURE_BRANCH and printing PR instructions..."
  git checkout "$FEATURE_BRANCH"
  git push -u "$REMOTE" "$FEATURE_BRANCH" || true
  cat <<EOF
Feature branch pushed.
Open a Pull Request:
  Source: $FEATURE_BRANCH
  Target: $TARGET_BRANCH
After merge, you can delete the branch with:
  bash scripts/git/delete_branch.sh --name $FEATURE_BRANCH --both
EOF
fi

