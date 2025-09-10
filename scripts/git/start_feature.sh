#!/usr/bin/env bash
set -euo pipefail

# Purpose: Start a new feature branch from up-to-date main, optionally seed QA note, and push.
#
# Usage:
#   bash scripts/git/start_feature.sh \
#     --name pdf-ingestion \
#     --prefix feat \
#     --remote origin \
#     --seed-qa \
#     --push
#
# Notes:
#   - Requires a clean working tree.
#   - Run from repo root.

FEATURE_NAME=""
PREFIX="feat"
REMOTE="origin"
SEED_QA=false
DO_PUSH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) FEATURE_NAME="$2"; shift 2;;
    --prefix) PREFIX="$2"; shift 2;;
    --remote) REMOTE="$2"; shift 2;;
    --seed-qa) SEED_QA=true; shift 1;;
    --push) DO_PUSH=true; shift 1;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ -z "$FEATURE_NAME" ]]; then
  echo "Error: --name <feature-name> is required" >&2
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

echo "Ensuring local 'main' is up to date..."
git checkout main >/dev/null 2>&1 || {
  echo "Error: main branch not found locally." >&2; exit 1;
}
git fetch "$REMOTE" main
git merge --ff-only "refs/remotes/$REMOTE/main" || {
  echo "Fast-forward merge failed. Please resolve manually." >&2; exit 1;
}

TARGET_BRANCH="${PREFIX}/${FEATURE_NAME}"
if git show-ref --quiet --heads "$TARGET_BRANCH"; then
  echo "Error: branch $TARGET_BRANCH already exists." >&2
  exit 1
fi

echo "Creating and switching to $TARGET_BRANCH ..."
git checkout -b "$TARGET_BRANCH" main

if [[ "$SEED_QA" == true ]]; then
  TODAY=$(date +%F)
  SAFE_NAME=$(echo "$FEATURE_NAME" | tr '/ ' '-_')
  QA_FILE="docs/qa-notes/${TODAY}-${SAFE_NAME}-qa.md"
  TEMPLATE="docs/qa-notes/_TEMPLATE_DAILY_QA.md"
  mkdir -p "docs/qa-notes"
  if [[ -f "$TEMPLATE" ]]; then
    sed "s#<YYYY-MM-DD>#$TODAY#g" "$TEMPLATE" > "$QA_FILE"
  else
    cat > "$QA_FILE" <<EOF
# ${TODAY} QA 記錄（每日）

- Topic: ${FEATURE_NAME}
- Owner: <your-name>
- Related Task IDs: <task-ids-if-any>

## Q&A
- Q: <問題敘述>
- A: <結論與依據>
- Refs: <程式路徑或連結>

## Decisions
- <關鍵決策> － 依據 / 影響範圍

## Action Items
- [ ] <待辦>

## Notes
- <補充、坑點、實驗觀察>
EOF
  fi
  git add "$QA_FILE"
  git commit -m "chore(docs): seed QA note for ${FEATURE_NAME}"
fi

if [[ "$DO_PUSH" == true ]]; then
  echo "Pushing $TARGET_BRANCH to $REMOTE ..."
  git push -u "$REMOTE" "$TARGET_BRANCH"
fi

cat <<EOF
Started feature branch:
  Branch   : $TARGET_BRANCH
  Seed QA  : $SEED_QA
  Pushed   : $DO_PUSH (remote=$REMOTE)

Next:
  - Start coding on $TARGET_BRANCH
  - Periodically sync with main using: bash scripts/git/sync_with_main.sh --branch $TARGET_BRANCH --mode merge
EOF

