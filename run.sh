#!/usr/bin/env bash
set -euo pipefail

# SurveyX convenience runner
#
# Usage:
#   ./run.sh convert   <pdf_dir> <md_out_dir> [--recursive] [--title_from filename|metadata|firstline]
#   ./run.sh validate  <md_dir>
#   ./run.sh offline   <title> <keywords_csv> <md_dir>
#   ./run.sh workflow  <task_id>
#   ./run.sh examples  # show examples
#
# Notes:
# - Ensure Python deps installed: pip install -r requirements.txt
# - For PDF→MD: prefer Poppler (pdftotext). Otherwise install PyMuPDF (pip install pymupdf).

cmd=${1:-examples}
case "$cmd" in
  convert)
    pdf_dir=${2:-}
    md_dir=${3:-}
    if [[ -z "${pdf_dir}" || -z "${md_dir}" ]]; then
      echo "Usage: $0 convert <pdf_dir> <md_out_dir> [--recursive] [--title_from filename|metadata|firstline]"; exit 2
    fi
    shift 3 || true
    python scripts/pdf_to_md.py --in_dir "${pdf_dir}" --out_dir "${md_dir}" "$@"
    ;;

  validate)
    md_dir=${2:-}
    if [[ -z "${md_dir}" ]]; then
      echo "Usage: $0 validate <md_dir>"; exit 2
    fi
    python scripts/validate_md_refs.py --ref_path "${md_dir}"
    ;;

  offline)
    title=${2:-}
    keywords=${3:-}
    md_dir=${4:-}
    if [[ -z "${title}" || -z "${keywords}" || -z "${md_dir}" ]]; then
      echo "Usage: $0 offline <title> <keywords_csv> <md_dir>"; exit 2
    fi
    python tasks/offline_run.py --title "${title}" --key_words "${keywords}" --ref_path "${md_dir}"
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
# 1) Convert PDFs to Markdown
./run.sh convert /path/to/pdfs resources/offline_refs/your_topic --recursive --title_from filename

# 2) Validate Markdown references
./run.sh validate resources/offline_refs/your_topic

# 3) Run full offline pipeline
./run.sh offline "Controllable Text Generation for Large Language Models: A Survey" \
  "controlled text generation, text generation, large language model, LLM" \
  resources/offline_refs/your_topic

# 4) Run workflow phases after you have a task_id
#    (check outputs/<task_id>/tmp_config.json from previous run)
./run.sh workflow 2025-06-18-0935_kw
USAGE
    ;;
esac
