#!/usr/bin/env bash
# 一鍵執行：組裝 + 編譯
# 
# 環境需求：
# - conda 環境: surveyx
# - 如果未啟用，腳本會嘗試自動啟用

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIRED_CONDA_ENV="surveyx"

echo "========================================"
echo "SurveyX LaTeX 組裝與編譯"
echo "========================================"
echo ""

# 檢查並啟用 conda 環境
if [[ -z "${CONDA_DEFAULT_ENV:-}" || "${CONDA_DEFAULT_ENV}" != "${REQUIRED_CONDA_ENV}" ]]; then
    echo "⚠️  當前不在 ${REQUIRED_CONDA_ENV} 環境中"
    echo "嘗試啟用 conda 環境..."
    
    # 初始化 conda (for bash)
    if [[ -f "${HOME}/miniconda3/etc/profile.d/conda.sh" ]]; then
        source "${HOME}/miniconda3/etc/profile.d/conda.sh"
    elif [[ -f "${HOME}/anaconda3/etc/profile.d/conda.sh" ]]; then
        source "${HOME}/anaconda3/etc/profile.d/conda.sh"
    elif [[ -f "/opt/conda/etc/profile.d/conda.sh" ]]; then
        source "/opt/conda/etc/profile.d/conda.sh"
    else
        echo "❌ 錯誤: 找不到 conda.sh，請手動啟用 conda"
        echo "請執行: conda activate ${REQUIRED_CONDA_ENV}"
        exit 1
    fi
    
    # 啟用環境
    if conda activate "${REQUIRED_CONDA_ENV}" 2>/dev/null; then
        echo "✓ 已啟用 conda 環境: ${REQUIRED_CONDA_ENV}"
    else
        echo "❌ 錯誤: 無法啟用 ${REQUIRED_CONDA_ENV} 環境"
        echo "請先建立環境: conda env create -n ${REQUIRED_CONDA_ENV} -f ../../env/env-survey.yml"
        exit 1
    fi
else
    echo "✓ 已在 ${REQUIRED_CONDA_ENV} 環境中"
fi
echo ""

# 步驟 1: 組裝
echo "步驟 1/2: 組裝 LaTeX 文檔"
echo "----------------------------------------"
python3 "${SCRIPT_DIR}/assemble_latex.py"
echo ""

# 步驟 2: 編譯
echo "步驟 2/2: 編譯 PDF"
echo "----------------------------------------"
bash "${SCRIPT_DIR}/compile_survey.sh"

echo ""
echo "✅ 全部完成！"
