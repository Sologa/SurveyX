# 快速開始指南

## ⚙️ 環境準備

### Conda 環境（必須）

所有操作需在 `surveyx` conda 環境中執行：

```bash
# 如果尚未建立環境
conda env create -n surveyx -f ../../env/env-survey.yml

# 啟用環境
conda activate surveyx
```

### 驗證環境

```bash
# 確認在正確的環境中
conda env list | grep surveyx

# 確認 Python 版本
python --version  # 應顯示 Python 3.x
```

## 🚀 一鍵執行（最簡單）

從專案根目錄執行：

```bash
# 確保已啟用 surveyx 環境
conda activate surveyx

# 執行
bash sandbox/latex_assembly_demo/scripts/run_all.sh
```

這個腳本會自動：
1. 檢查並啟用 conda 環境（如需要）
2. 組裝 LaTeX 文檔
3. 編譯成 PDF

## 📦 輸出位置

執行完成後，檔案位於：

```
sandbox/latex_assembly_demo/
├── survey.pdf          ← 最終 PDF
├── survey_wtmk.pdf     ← 浮水印版本（如有）
└── compiled_output/
    ├── survey.tex      ← 組裝後的 LaTeX 文檔
    └── compile.log     ← 編譯日誌
```

## 🔍 分步執行（了解流程）

如果想逐步執行並查看每個步驟：

```bash
cd sandbox/latex_assembly_demo

# 步驟 1: 組裝（生成 survey.tex）
python3 scripts/assemble_latex.py

# 步驟 2: 編譯（生成 PDF）
bash scripts/compile_survey.sh
```

## ✅ 驗證結果

```bash
# 查看生成的 LaTeX 文檔
less compiled_output/survey.tex

# 查看 PDF（macOS）
open survey.pdf

# 查看 PDF（Linux）
xdg-open survey.pdf

# 檢查 PDF 資訊
pdfinfo survey.pdf
```

## 📊 預期輸出

### 組裝步驟輸出

```
============================================================
LaTeX 文檔組裝器
============================================================

✓ 載入模板: .../survey.ini.tex

步驟 2: 讀取大綱資訊
  標題: Speech Tokenizers and Speech Language Models...

步驟 3: 加入標題與作者
✓ 加入標題: Speech Tokenizers...
✓ 加入作者: www.surveyx.cn

步驟 4: 加入摘要
✓ 加入摘要 (1234 字元)

步驟 5: 加入主體內容 (mainbody_post_refined.tex)
✓ 加入主體內容 (567890 字元)

步驟 6: 加入參考文獻
✓ 加入參考文獻區塊

步驟 7: 加入免責聲明
✓ 加入免責聲明

步驟 8: 結束文檔
✓ 結束文檔

步驟 9: 儲存最終文檔
✓ 儲存到: .../survey.tex

============================================================
✅ 組裝完成！
============================================================

生成的檔案: .../compiled_output/survey.tex
檔案大小: 1,234,567 bytes

下一步: 執行 compile_survey.sh 來編譯 PDF
```

### 編譯步驟輸出

```
========================================
LaTeX Survey 編譯腳本
========================================

✓ 工作目錄: .../compiled_output

========================================
開始編譯 LaTeX...
========================================

✅ LaTeX 編譯成功

✓ PDF 已生成: survey.pdf
  檔案大小: 2.3M

========================================
清理中間檔案...
========================================
✓ 中間檔案已清理

✓ PDF 已移動到: .../survey.pdf

========================================
加入浮水印...
========================================
處理 85 頁...
  已處理 10 頁...
  已處理 20 頁...
  ...
✅ 浮水印版本已生成: survey_wtmk.pdf

========================================
✅ 編譯完成！
========================================

輸出檔案：
  - .../survey.pdf
  - .../survey_wtmk.pdf

編譯日誌: .../compile.log
```

## 🛠️ 故障排除

### 問題 1: Python 找不到模組

```bash
# 確認 Python 版本（需要 3.6+）
python3 --version

# 如果需要浮水印功能
pip3 install pymupdf
```

### 問題 2: latexmk 找不到

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install texlive-full

# macOS
brew install --cask mactex

# 驗證安裝
latexmk --version
```

### 問題 3: 編譯錯誤

```bash
# 查看詳細日誌
cat compiled_output/compile.log | less

# 查看最後的錯誤訊息
tail -n 50 compiled_output/compile.log
```

### 問題 4: 權限錯誤

```bash
# 添加執行權限
chmod +x scripts/*.sh scripts/*.py
```

## 🔄 重新執行

清除舊的輸出並重新執行：

```bash
# 清除 PDF
rm -f survey*.pdf

# 清除組裝的 LaTeX
rm -f compiled_output/survey.tex

# 重新執行
bash scripts/run_all.sh
```

## 📚 更多資訊

詳細說明請參閱：[README.md](README.md)

---

**提示**：整個流程完全不涉及 LLM，可離線執行！
