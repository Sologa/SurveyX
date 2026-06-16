#!/usr/bin/env bash
set -euo pipefail

# 編譯 LaTeX 文檔為 PDF 的一鍵腳本
#
# 環境需求：
# - conda 環境: surveyx (建議，用於 Python 浮水印腳本)
# - LaTeX 工具: latexmk, pdflatex, bibtex
# 
# 功能：
# 1. 檢查並啟用 conda 環境（如需要）
# 2. 切換到編譯目錄
# 3. 執行 latexmk 編譯
# 4. 清理中間檔案
# 5. 移動 PDF 到上層目錄
# 6. 加入浮水印

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
COMPILE_DIR="${BASE_DIR}/compiled_output"
SURVEY_TEX="survey.tex"
SURVEY_PDF="survey.pdf"
SURVEY_WTMK_PDF="survey_wtmk.pdf"
REQUIRED_CONDA_ENV="surveyx"

echo "========================================"
echo "LaTeX Survey 編譯腳本"
echo "========================================"
echo ""

# 檢查並啟用 conda 環境（用於浮水印腳本）
if [[ -z "${CONDA_DEFAULT_ENV:-}" || "${CONDA_DEFAULT_ENV}" != "${REQUIRED_CONDA_ENV}" ]]; then
    echo "ℹ️  提示: 建議在 ${REQUIRED_CONDA_ENV} 環境中執行"
    echo "如需自動啟用，請使用: bash scripts/run_all.sh"
    echo ""
fi

# 檢查必要檔案
if [[ ! -f "${COMPILE_DIR}/${SURVEY_TEX}" ]]; then
    echo "❌ 錯誤: 找不到 ${SURVEY_TEX}"
    echo "請先執行: python scripts/assemble_latex.py"
    exit 1
fi

if [[ ! -f "${COMPILE_DIR}/references.bib" ]]; then
    echo "❌ 錯誤: 找不到 references.bib"
    exit 1
fi

if [[ ! -f "${COMPILE_DIR}/neurips_2024.sty" ]]; then
    echo "❌ 錯誤: 找不到 neurips_2024.sty"
    exit 1
fi

# 檢查 latexmk
if ! command -v latexmk >/dev/null 2>&1; then
    echo "❌ 錯誤: 未安裝 latexmk"
    echo "請安裝: sudo apt install texlive-full (Ubuntu)"
    echo "      或: brew install --cask mactex (macOS)"
    exit 1
fi

# 切換到編譯目錄
cd "${COMPILE_DIR}"
echo "✓ 工作目錄: ${COMPILE_DIR}"
echo ""

# 清理舊的 PDF
if [[ -f "${SURVEY_PDF}" ]]; then
    rm -f "${SURVEY_PDF}"
    echo "✓ 清除舊的 ${SURVEY_PDF}"
fi

if [[ -f "../${SURVEY_PDF}" ]]; then
    rm -f "../${SURVEY_PDF}"
    echo "✓ 清除舊的 ../${SURVEY_PDF}"
fi

if [[ -f "../${SURVEY_WTMK_PDF}" ]]; then
    rm -f "../${SURVEY_WTMK_PDF}"
    echo "✓ 清除舊的 ../${SURVEY_WTMK_PDF}"
fi

echo ""
echo "========================================"
echo "開始編譯 LaTeX..."
echo "========================================"
echo ""

# 執行 latexmk 編譯
# -pdf: 生成 PDF
# -interaction=nonstopmode: 遇到錯誤不停止
# -f: 強制編譯
if latexmk -pdf -synctex=1  -interaction=nonstopmode -f "${SURVEY_TEX}" > compile.log 2>&1; then
    echo "✅ LaTeX 編譯成功"
else
    echo "⚠️  LaTeX 編譯有警告，請檢查 compile.log"
    echo "最後 20 行日誌："
    tail -n 20 compile.log
fi

echo ""

# 檢查是否生成 PDF
if [[ ! -f "${SURVEY_PDF}" ]]; then
    echo "❌ 錯誤: PDF 生成失敗"
    echo "請檢查 ${COMPILE_DIR}/compile.log"
    exit 1
fi

echo "✓ PDF 已生成: ${SURVEY_PDF}"
PDF_SIZE=$(du -h "${SURVEY_PDF}" | cut -f1)
echo "  檔案大小: ${PDF_SIZE}"
echo ""

# 清理中間檔案
echo "========================================"
echo "清理中間檔案..."
echo "========================================"
latexmk -c > /dev/null 2>&1 || true
rm -f *.bbl 2>/dev/null || true
echo "✓ 中間檔案已清理"
echo ""

# 移動 PDF 到上層目錄
mv "${SURVEY_PDF}" "../${SURVEY_PDF}"
echo "✓ PDF 已移動到: ${BASE_DIR}/${SURVEY_PDF}"
echo ""

# 加入浮水印 (可選，需要 Python + fitz)
echo "========================================"
echo "加入浮水印..."
echo "========================================"

if command -v python3 >/dev/null 2>&1; then
    WATERMARK_SCRIPT="${SCRIPT_DIR}/add_watermark.py"
    if [[ -f "${WATERMARK_SCRIPT}" ]]; then
        if python3 "${WATERMARK_SCRIPT}" "../${SURVEY_PDF}" "../${SURVEY_WTMK_PDF}" "watermark.png"; then
            echo "✅ 浮水印版本已生成: ${SURVEY_WTMK_PDF}"
        else
            echo "⚠️  浮水印生成失敗（可能缺少 PyMuPDF）"
        fi
    else
        echo "ℹ️  未找到浮水印腳本，跳過"
    fi
else
    echo "ℹ️  未安裝 Python，跳過浮水印"
fi

echo ""
echo "========================================"
echo "✅ 編譯完成！"
echo "========================================"
echo ""
echo "輸出檔案："
echo "  - ${BASE_DIR}/${SURVEY_PDF}"
if [[ -f "../${SURVEY_WTMK_PDF}" ]]; then
    echo "  - ${BASE_DIR}/${SURVEY_WTMK_PDF}"
fi
echo ""
echo "編譯日誌: ${COMPILE_DIR}/compile.log"
echo ""
