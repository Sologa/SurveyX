#!/usr/bin/env bash
set -euo pipefail

# Docling-only PDF->Markdown conversion test
# - Runs docling CLI on a sample folder (or user-provided path)
# - Supports offline mode if DOCLING_ARTIFACTS_PATH is set
#
# Usage:
#   bash tests/run_test_docling_to_md.sh [INPUT_PATH] [OUTPUT_DIR]
#
# Examples:
#   bash tests/run_test_docling_to_md.sh
#   bash tests/run_test_docling_to_md.sh examples/Computation_and_Language outputs/docling_md_test
#   DOCLING_ARTIFACTS_PATH="$HOME/.cache/docling/models" bash tests/run_test_docling_to_md.sh examples/Computation_and_Language

# Try to activate the common conda env if available (optional)
if command -v conda >/dev/null 2>&1; then
  # shellcheck disable=SC1091
  source "$(conda info --base)/etc/profile.d/conda.sh" || true
  conda activate surveyx 2>/dev/null || true
fi

export DOCLING_ARTIFACTS_PATH="$HOME/.cache/docling/models"

INPUT_PATH=${1:-resources/offline_refs/pdfs}
OUTPUT_DIR=${2:-resources/offline_refs/docling_md_test}

echo "Input:  ${INPUT_PATH}"
echo "Output: ${OUTPUT_DIR}"

mkdir -p "${OUTPUT_DIR}"

DOC_CMD=(docling "${INPUT_PATH}" --to md --image-export-mode placeholder --output "${OUTPUT_DIR}")

if [[ -n "${DOCLING_ARTIFACTS_PATH:-}" ]]; then
  echo "Using DOCLING_ARTIFACTS_PATH=${DOCLING_ARTIFACTS_PATH}"
  DOC_CMD+=(--artifacts-path "${DOCLING_ARTIFACTS_PATH}")
else
  echo "Note: Models may download on first run. To run fully offline, prefetch with:\n  docling-tools models download\nThen set DOCLING_ARTIFACTS_PATH to that models directory."
fi

echo "Running: ${DOC_CMD[*]}"
"${DOC_CMD[@]}"

echo
echo "Listing generated files (up to 20):"
find "${OUTPUT_DIR}" -type f | head -n 20
echo
echo "Done. Markdown output at: ${OUTPUT_DIR}"
