#!/usr/bin/env bash
set -euo pipefail

# Formal Docling PDF → Markdown converter for SurveyX
#
# Usage:
#   scripts/docling_pdf_to_md.sh <INPUT_PATH> <OUTPUT_DIR> [-- ...extra docling flags]
#
# Environment knobs (optional):
#   DOCLING_ARTIFACTS_PATH   Path to local cached models (default: "$HOME/.cache/docling/models")
#   DOC_IMAGE_MODE           Image export mode: placeholder|embedded|referenced (default: placeholder)
#   DOC_USE_OCRMAC           If set to 1, try to use --ocr-engine ocrmac (only if package available)
#   DOC_OCR_LANG             OCR language (default: en-US)
#   DOC_DEVICE               Device for acceleration (default: auto; on macOS uses mps)
#   DOC_THREADS              --num-threads (default: 2)
#   DOC_PAGE_BATCH           --page-batch-size (default: 2)

INPUT_PATH=${1:-}
OUTPUT_DIR=${2:-}
shift 2 || true

if [[ -z "${INPUT_PATH}" || -z "${OUTPUT_DIR}" ]]; then
  echo "Usage: $0 <INPUT_PATH> <OUTPUT_DIR> [-- extra docling flags]" >&2
  exit 2
fi

# Defaults
: "${DOCLING_ARTIFACTS_PATH:="$HOME/.cache/docling/models"}"
: "${DOC_IMAGE_MODE:=placeholder}"
: "${DOC_USE_OCRMAC:=0}"
: "${DOC_OCR_LANG:=en-US}"

# Device heuristic: prefer MPS on macOS, else leave default
if [[ "$(uname -s)" == "Darwin" ]]; then
  : "${DOC_DEVICE:=mps}"
else
  : "${DOC_DEVICE:=auto}"
fi

: "${DOC_THREADS:=2}"
: "${DOC_PAGE_BATCH:=2}"

DOC_CMD=(docling "${INPUT_PATH}" --to md --output "${OUTPUT_DIR}" \
  --image-export-mode "${DOC_IMAGE_MODE}" \
  --num-threads "${DOC_THREADS}" --page-batch-size "${DOC_PAGE_BATCH}")

# Prefer local artifacts
if [[ -n "${DOCLING_ARTIFACTS_PATH:-}" ]]; then
  DOC_CMD+=(--artifacts-path "${DOCLING_ARTIFACTS_PATH}")
fi

# Device
if [[ -n "${DOC_DEVICE}" && "${DOC_DEVICE}" != "auto" ]]; then
  DOC_CMD+=(--device "${DOC_DEVICE}")
fi

# OCR engine (optional ocrmac)
if [[ "${DOC_USE_OCRMAC}" == "1" ]]; then
  if python - <<'PY' >/dev/null 2>&1; then
import importlib; import sys
sys.exit(0 if importlib.util.find_spec('ocrmac') else 1)
PY
  then
    DOC_CMD+=(--ocr true --ocr-engine ocrmac --ocr-lang "${DOC_OCR_LANG}")
  else
    echo "[info] ocrmac not installed, skipping --ocr-engine ocrmac" >&2
    DOC_CMD+=(--ocr true)
  fi
else
  # keep default OCR behavior (enabled by Docling, image/bitmap regions only)
  DOC_CMD+=(--ocr true)
fi

# Pass-through extra flags after --
if [[ "${1:-}" == "--" ]]; then
  shift
  DOC_CMD+=("$@")
fi

echo "Using DOCLING_ARTIFACTS_PATH=${DOCLING_ARTIFACTS_PATH}"
echo "Running: ${DOC_CMD[*]}"
"${DOC_CMD[@]}"

echo
echo "Listing generated files (up to 20):"
find "${OUTPUT_DIR}" -type f | head -n 20 || true
echo "Done. Markdown output at: ${OUTPUT_DIR}"

