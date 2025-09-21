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

# SurveyX convenience runner
#
# Usage:
#   ./run.sh convert   <pdf_dir> <md_out_dir> [-- ...extra docling flags]
#   ./run.sh validate  <md_dir>
#   ./run.sh download  <json_path> <out_dir> [-- ...extra flags]
#   ./run.sh offline   <title> <keywords_csv> <md_dir>
#   ./run.sh workflow  <task_id>
#   ./run.sh examples  # show examples
#
# Notes:
# - Ensure Python deps installed: pip install -r requirements.txt
# - For PDF→MD: this wrapper uses Docling. Install: `pip install -U docling docling-tools`.
# - Optional (macOS OCR): `xcode-select --install && pip install -U ocrmac`.

cmd=${1:-examples}
case "$cmd" in
  convert)
    pdf_dir=${2:-}
    md_dir=${3:-}
    if [[ -z "${pdf_dir}" || -z "${md_dir}" ]]; then
      echo "Usage: $0 convert <pdf_dir> <md_out_dir> [-- ...extra docling flags]"; exit 2
    fi
    shift 2 || true
    bash scripts/docling_pdf_to_md.sh "${pdf_dir}" "${md_dir}" "$@"
    ;;

  validate)
    md_dir=${2:-}
    if [[ -z "${md_dir}" ]]; then
      echo "Usage: $0 validate <md_dir>"; exit 2
    fi
    bash scripts/validate_md_refs.sh "${md_dir}"
    ;;

  download)
    json_path=${2:-}
    out_dir=${3:-}
    if [[ -z "${json_path}" || -z "${out_dir}" ]]; then
      echo "Usage: $0 download <json_path> <out_dir> [-- ...extra flags]"; exit 2
    fi
    shift 3 || true
    # Forward extra flags to python downloader
    python scripts/download_papers.py --json "${json_path}" --out-dir "${out_dir}" "$@"
    ;;

  offline)
    title=${2:-}
    keywords=${3:-}
    md_dir=${4:-}
    if [[ -z "${title}" || -z "${keywords}" || -z "${md_dir}" ]]; then
      echo "Usage: $0 offline <title> <keywords_csv> <md_dir> [-- ...extra offline flags]"; exit 2
    fi
    shift 4 || true
    # Forward extra flags (e.g., --curated_json, --only_clean, --skip_llm) to Python entry
    python tasks/offline_run.py --title "${title}" --key_words "${keywords}" --ref_path "${md_dir}" "$@"
    ;;

  workflow)
    task_id=${2:-}
    if [[ -z "${task_id}" ]]; then
      echo "Usage: $0 workflow <task_id>"; exit 2
    fi
    python tasks/workflow/03_gen_outlines.py  --task_id "${task_id}"
    python tasks/workflow/04_gen_content.py   --task_id "${task_id}"
    python tasks/workflow/05_post_refine.py   --task_id "${task_id}"
    python tasks/workflow/06_gen_latex.py     --task_id "${task_id}"
    ;;

  examples|*)
    cat <<'USAGE'
Examples
---------
# 1) Convert PDFs to Markdown (Docling)
./run.sh convert /path/to/pdfs resources/offline_refs/your_topic -- --image-export-mode placeholder --device mps

# 2) Validate Markdown references
./run.sh validate resources/offline_refs/your_topic

# 3) Download PDFs from a paper list JSON
./run.sh download resources/included_papers_20250825_balanced.json datasets/papers -- --concurrency 6

# 3) Run offline cleaning / pipeline (with extra flags)
./run.sh offline "Controllable Text Generation for Large Language Models: A Survey" \
  "controlled text generation, text generation, large language model, LLM" \
  resources/offline_refs/your_topic \
  --curated_json resources/offline_refs/included_papers_20250825_balanced.json --only_clean

# 4) Run workflow phases after you have a task_id
#    (check outputs/<task_id>/tmp_config.json from previous run)
./run.sh workflow 2025-06-18-0935_kw
USAGE
    ;;
esac
