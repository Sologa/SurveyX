#!/usr/bin/env bash
set -euo pipefail

# Purpose: Sync specific paths from a source branch into a target branch, commit, and optionally push.
#
# Usage:
#   bash scripts/git/sync_paths_to_branch.sh \
#     --from main \
#     --to legacy-stable \
#     --paths "scripts docs/qa-notes" \
#     --remote origin \
#     --push
#
# Notes:
#   - Requires a clean working tree.
#   - Run from repo root.
#   - If no changes in selected paths, no commit will be created.

SOURCE_BRANCH="main"
TARGET_BRANCH="legacy-stable"
REMOTE="origin"
PATHS=""
DO_PUSH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from) SOURCE_BRANCH="$2"; shift 2;;
    --to) TARGET_BRANCH="$2"; shift 2;;
    --paths) PATHS="$2"; shift 2;;
    --remote) REMOTE="$2"; shift 2;;
    --push) DO_PUSH=true; shift 1;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ -z "$PATHS" ]]; then
  echo "Error: --paths \"<space-separated-paths>\" is required" >&2
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

# Ensure branches exist locally or fetch them
if ! git show-ref --quiet --heads "$SOURCE_BRANCH"; then
  echo "Local branch $SOURCE_BRANCH not found. Attempting to fetch from $REMOTE..."
  git fetch "$REMOTE" "$SOURCE_BRANCH:$SOURCE_BRANCH" || true
fi
if ! git show-ref --quiet --heads "$TARGET_BRANCH"; then
  echo "Local branch $TARGET_BRANCH not found. Attempting to fetch from $REMOTE..."
  git fetch "$REMOTE" "$TARGET_BRANCH:$TARGET_BRANCH" || {
    echo "Error: could not prepare local $TARGET_BRANCH" >&2
    exit 1
  }
fi

echo "Switching to $TARGET_BRANCH ..."
git checkout "$TARGET_BRANCH"

echo "Syncing paths from $SOURCE_BRANCH -> $TARGET_BRANCH ..."
CHANGED=false
for p in $PATHS; do
  # Bring selected path from source branch into current working tree
  if git checkout "$SOURCE_BRANCH" -- "$p" 2>/dev/null; then
    CHANGED=true
  else
    echo "Warning: path '$p' not found in $SOURCE_BRANCH (skipped)."
  fi
done

if [[ "$CHANGED" == true ]]; then
  git add $PATHS || true
  if ! git diff --cached --quiet; then
    git commit -m "chore(sync): sync paths from $SOURCE_BRANCH -> $TARGET_BRANCH: $PATHS"
    if [[ "$DO_PUSH" == true ]]; then
      echo "Pushing $TARGET_BRANCH to $REMOTE ..."
      git push "$REMOTE" "$TARGET_BRANCH"
    fi
    echo "Paths synced and committed on $TARGET_BRANCH."
  else
    echo "No staged changes detected; nothing to commit."
  fi
else
  echo "No paths were updated; nothing to do."
fi

cat <<EOF
Done.
  Source : $SOURCE_BRANCH
  Target : $TARGET_BRANCH
  Paths  : $PATHS
  Pushed : $DO_PUSH (remote=$REMOTE)
EOF

