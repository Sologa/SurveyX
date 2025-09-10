#!/usr/bin/env bash
set -euo pipefail

# Purpose: Initialize legacy maintenance branch and tag, and keep a dev branch for ongoing work.
# Default behavior:
#   - Tag current commit as v0.1-legacy-with-docs (if not existing)
#   - Create legacy-stable branch (if not existing)
#   - Optionally push tag/branch to origin
#
# Usage:
#   scripts/git/init_branching.sh \
#     --legacy-branch legacy-stable \
#     --legacy-tag v0.1-legacy-with-docs \
#     --dev-branch main \
#     --remote origin \
#     --push
#
# Notes:
#   - Requires a clean working tree.
#   - Run from repo root.

LEGACY_BRANCH="legacy-stable"
LEGACY_TAG="v0.1-legacy-with-docs"
DEV_BRANCH="main"
REMOTE="origin"
DO_PUSH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --legacy-branch) LEGACY_BRANCH="$2"; shift 2;;
    --legacy-tag) LEGACY_TAG="$2"; shift 2;;
    --dev-branch) DEV_BRANCH="$2"; shift 2;;
    --remote) REMOTE="$2"; shift 2;;
    --push) DO_PUSH=true; shift 1;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

# preflight checks
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not a git repository" >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Error: working tree not clean. Commit or stash changes first." >&2
  exit 1
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: ${CURRENT_BRANCH}"

# create tag if missing
if git rev-parse -q --verify "refs/tags/${LEGACY_TAG}" >/dev/null; then
  echo "Tag ${LEGACY_TAG} already exists."
else
  echo "Creating tag ${LEGACY_TAG} at ${CURRENT_BRANCH}..."
  git tag -a "${LEGACY_TAG}" -m "Legacy baseline with docs"
fi

# create legacy branch if missing
if git show-ref --quiet --heads "${LEGACY_BRANCH}"; then
  echo "Branch ${LEGACY_BRANCH} already exists."
else
  echo "Creating branch ${LEGACY_BRANCH} from ${CURRENT_BRANCH}..."
  git branch "${LEGACY_BRANCH}" "${CURRENT_BRANCH}"
fi

# ensure dev branch exists locally
if git show-ref --quiet --heads "${DEV_BRANCH}"; then
  echo "Dev branch ${DEV_BRANCH} already exists."
else
  echo "Creating dev branch ${DEV_BRANCH} from ${CURRENT_BRANCH}..."
  git branch "${DEV_BRANCH}" "${CURRENT_BRANCH}"
fi

if [[ "${DO_PUSH}" == true ]]; then
  echo "Pushing ${LEGACY_BRANCH}, ${DEV_BRANCH}, and tag ${LEGACY_TAG} to ${REMOTE}..."
  git push "${REMOTE}" "${LEGACY_BRANCH}":"${LEGACY_BRANCH}" || true
  git push "${REMOTE}" "${DEV_BRANCH}":"${DEV_BRANCH}" || true
  git push "${REMOTE}" --tags || true
fi

cat <<EOF
Initialized branching:
  Legacy branch: ${LEGACY_BRANCH}
  Dev branch   : ${DEV_BRANCH}
  Legacy tag   : ${LEGACY_TAG}
Remote push    : ${DO_PUSH} (remote=${REMOTE})

Next steps:
  - Continue dev on ${DEV_BRANCH}
  - Maintain hotfixes on ${LEGACY_BRANCH}
  - Create feature branches from ${DEV_BRANCH}: git checkout -b feat/<name> ${DEV_BRANCH}
EOF

