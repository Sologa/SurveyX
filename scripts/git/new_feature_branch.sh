#!/usr/bin/env bash
set -euo pipefail

# Purpose: Create a new feature branch from a given dev branch and optionally push to remote.
#
# Usage:
#   scripts/git/new_feature_branch.sh \
#     --name refactor-io-layer \
#     --from main \
#     --prefix feat \
#     --remote origin \
#     --push
#
# Notes:
#   - Requires a clean working tree.
#   - Run from repo root.

FEATURE_NAME=""
FROM_BRANCH="main"
PREFIX="feat"
REMOTE="origin"
DO_PUSH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) FEATURE_NAME="$2"; shift 2;;
    --from) FROM_BRANCH="$2"; shift 2;;
    --prefix) PREFIX="$2"; shift 2;;
    --remote) REMOTE="$2"; shift 2;;
    --push) DO_PUSH=true; shift 1;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ -z "${FEATURE_NAME}" ]]; then
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

# Ensure FROM branch exists locally; if not, try to fetch from remote
if ! git show-ref --quiet --heads "${FROM_BRANCH}"; then
  echo "Local branch ${FROM_BRANCH} not found. Attempting to fetch from ${REMOTE}..."
  git fetch "${REMOTE}" "${FROM_BRANCH}:${FROM_BRANCH}" || {
    echo "Error: could not fetch ${FROM_BRANCH} from ${REMOTE}" >&2
    exit 1
  }
fi

TARGET_BRANCH="${PREFIX}/${FEATURE_NAME}"

if git show-ref --quiet --heads "${TARGET_BRANCH}"; then
  echo "Branch ${TARGET_BRANCH} already exists. Aborting."
  exit 1
fi

echo "Creating branch ${TARGET_BRANCH} from ${FROM_BRANCH}..."
git branch "${TARGET_BRANCH}" "${FROM_BRANCH}"

echo "Switching to ${TARGET_BRANCH}..."
git checkout "${TARGET_BRANCH}"

if [[ "${DO_PUSH}" == true ]]; then
  echo "Pushing ${TARGET_BRANCH} to ${REMOTE}..."
  git push "${REMOTE}" "${TARGET_BRANCH}":"${TARGET_BRANCH}" || true
fi

cat <<EOF
Created feature branch:
  Name       : ${TARGET_BRANCH}
  From       : ${FROM_BRANCH}
  Remote push: ${DO_PUSH} (remote=${REMOTE})

Next steps:
  - Start coding on ${TARGET_BRANCH}
  - When ready, push and open a PR back to ${FROM_BRANCH}
EOF

