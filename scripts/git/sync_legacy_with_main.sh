#!/usr/bin/env bash
set -euo pipefail

# Purpose: Make legacy branch match main (source) branch using one of three modes.
#
# Usage:
#   bash scripts/git/sync_legacy_with_main.sh \
#     --legacy-branch legacy-stable \
#     --source-branch main \
#     --mode fast-forward|merge|hard-reset \
#     --remote origin \
#     --push
#
# Modes:
#   - fast-forward: attempt ff-only merge (safe, no new merge commit). Fails if history diverged.
#   - merge       : create a merge commit to bring legacy up to date with source.
#   - hard-reset  : force legacy to exactly match source (history rewrite!).
#
# Notes:
#   - Requires a clean working tree.
#   - Run from repo root.

LEGACY_BRANCH="legacy-stable"
SOURCE_BRANCH="main"
MODE="fast-forward"   # fast-forward|merge|hard-reset
REMOTE="origin"
DO_PUSH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --legacy-branch) LEGACY_BRANCH="$2"; shift 2;;
    --source-branch) SOURCE_BRANCH="$2"; shift 2;;
    --mode) MODE="$2"; shift 2;;
    --remote) REMOTE="$2"; shift 2;;
    --push) DO_PUSH=true; shift 1;;
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

# Ensure local branches exist or fetch them
if ! git show-ref --quiet --heads "$LEGACY_BRANCH"; then
  echo "Local branch $LEGACY_BRANCH not found. Attempting to fetch from $REMOTE..."
  git fetch "$REMOTE" "$LEGACY_BRANCH:$LEGACY_BRANCH" || {
    echo "Error: could not prepare local $LEGACY_BRANCH" >&2
    exit 1
  }
fi

if ! git show-ref --quiet --heads "$SOURCE_BRANCH"; then
  echo "Local branch $SOURCE_BRANCH not found. Attempting to fetch from $REMOTE..."
  git fetch "$REMOTE" "$SOURCE_BRANCH:$SOURCE_BRANCH" || true
fi

echo "Fetching latest refs from $REMOTE ..."
git fetch "$REMOTE"

echo "Switching to $LEGACY_BRANCH ..."
git checkout "$LEGACY_BRANCH"

case "$MODE" in
  fast-forward)
    echo "Attempting fast-forward: $LEGACY_BRANCH <- $REMOTE/$SOURCE_BRANCH ..."
    if git merge --ff-only "refs/remotes/$REMOTE/$SOURCE_BRANCH"; then
      echo "Fast-forward completed."
    else
      echo "Fast-forward failed (diverged history). Try --mode merge or --mode hard-reset." >&2
      exit 1
    fi
    ;;
  merge)
    echo "Merging: $LEGACY_BRANCH <- $REMOTE/$SOURCE_BRANCH ..."
    git merge --no-ff "refs/remotes/$REMOTE/$SOURCE_BRANCH"
    ;;
  hard-reset)
    echo "HARD RESET: $LEGACY_BRANCH will be made identical to $REMOTE/$SOURCE_BRANCH"
    echo "WARNING: This rewrites history on $LEGACY_BRANCH."
    git reset --hard "refs/remotes/$REMOTE/$SOURCE_BRANCH"
    ;;
  *)
    echo "Unknown mode: $MODE (expected fast-forward|merge|hard-reset)" >&2
    exit 1
    ;;
esac

if [[ "$DO_PUSH" == true ]]; then
  echo "Pushing $LEGACY_BRANCH to $REMOTE ..."
  if [[ "$MODE" == "hard-reset" ]]; then
    git push -f "$REMOTE" "$LEGACY_BRANCH"
  else
    git push "$REMOTE" "$LEGACY_BRANCH"
  fi
fi

cat <<EOF
Sync complete.
  Legacy : $LEGACY_BRANCH
  Source : $SOURCE_BRANCH
  Mode   : $MODE
  Pushed : $DO_PUSH (remote=$REMOTE)
EOF

