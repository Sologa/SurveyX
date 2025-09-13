#!/usr/bin/env bash
set -euo pipefail

# Optional: auto-activate conda env "surveyx" if available
if [[ "${CONDA_DEFAULT_ENV:-}" != "surveyx" ]]; then
  if command -v conda >/dev/null 2>&1; then
    __conda_base="$(conda info --base 2>/dev/null || true)"
    if [[ -n "${__conda_base}" && -f "${__conda_base}/etc/profile.d/conda.sh" ]]; then
      # shellcheck disable=SC1091
      . "${__conda_base}/etc/profile.d/conda.sh" || true
      conda activate surveyx || true
    fi
  fi
fi

# Wrapper for scripts/download_papers.py
#
# Usage:
#   bash scripts/download_papers.sh [json_path] [out_dir] [-- ...extra python flags]
# Examples:
#   bash scripts/download_papers.sh \
#     resources/included_papers_20250825_balanced.json \
#     datasets/papers \
#     -- --concurrency 8 --max 50

JSON_PATH=${1:-resources/offline_refs/included_papers_20250825_balanced.json}
OUT_DIR=${2:-resources/offline_refs/pdfs}
shift 2 || true

python scripts/download_papers.py --json "${JSON_PATH}" --out-dir "${OUT_DIR}" "$@"
