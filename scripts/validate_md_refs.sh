#!/usr/bin/env bash
set -euo pipefail

# Minimal validator for Markdown references used by SurveyX offline pipeline.
# Checks:
#  - First line is a Markdown heading (starts with '#')
#  - Contains an Abstract marker (case-insensitive; allows spaced letters)
#  - Minimum byte length (default 2KB)
#
# Usage:
#   scripts/validate_md_refs.sh <MD_DIR>
#
# Env knobs:
#   MIN_BYTES (default: 2048)

MD_DIR=${1:-}
if [[ -z "${MD_DIR}" ]]; then
  echo "Usage: $0 <MD_DIR>" >&2
  exit 2
fi

: "${MIN_BYTES:=2048}"

shopt -s nullglob
mds=("${MD_DIR}"/*.md)
if (( ${#mds[@]} == 0 )); then
  echo "No .md files found under ${MD_DIR}" >&2
  exit 1
fi

echo "Validating ${#mds[@]} Markdown files in: ${MD_DIR}"
err=0

for f in "${mds[@]}"; do
  base=$(basename "$f")
  ok=1

  # First line heading
  first_line=$(head -n1 "$f" || true)
  if [[ ! "$first_line" =~ ^\# ]]; then
    echo "[warn] $base: first line is not a Markdown heading (# ...)" >&2
    ok=0
  fi

  # Abstract detection (case-insensitive; permits spaced letters)
  if ! LC_ALL=C grep -Eiq "a\s*b\s*s\s*t\s*r\s*a\s*c\s*t" "$f"; then
    echo "[warn] $base: missing Abstract marker" >&2
    ok=0
  fi

  # Length check
  size=$(wc -c < "$f")
  if (( size < MIN_BYTES )); then
    echo "[warn] $base: file too short (${size} < ${MIN_BYTES} bytes)" >&2
    ok=0
  fi

  if (( ok == 1 )); then
    echo "[ok]   $base"
  else
    err=1
  fi
done

exit $err

