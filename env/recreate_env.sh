#!/usr/bin/env bash
set -euo pipefail
ENV_NAME=${1:-surveyx}

echo "[1/3] Create conda env: $ENV_NAME"
conda env remove -n "$ENV_NAME" -y >/dev/null 2>&1 || true
conda env create -n "$ENV_NAME" -f env/env-survey.yml

echo "[2/3] Activate and install pip extras (if any)"
# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"
if [ -f env/requirements-freeze.txt ]; then
  pip install -r env/requirements-freeze.txt
fi

echo "[3/3] Verify"
python -c "import sys; print('python', sys.version)"
echo "Done. Use: conda activate $ENV_NAME"
