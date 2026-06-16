# LaTeX Assembly Demo

這個目錄展示如何將 `mainbody_post_refined.tex` 組裝成完整的 `survey.tex` 並編譯成 PDF。

## ⚙️ 環境需求

### 必須：Conda 環境

所有操作需在 `surveyx` conda 環境中執行：

```bash
# 如果尚未建立環境
conda env create -n surveyx -f ../../env/env-survey.yml

# 啟用環境（每次執行前）
conda activate surveyx
```

### 必須：LaTeX 工具

- `latexmk` - LaTeX 編譯自動化工具
- `pdflatex` - PDF 生成器
- `bibtex` - 參考文獻處理

安裝方式：

```bash
# macOS
brew install --cask mactex

# Ubuntu/Debian
sudo apt install texlive-full

# 驗證安裝
latexmk --version
```

### 可選：Python 套件

浮水印功能需要：

```bash
pip install pymupdf  # 或 pip install PyMuPDF
```

## 📁 目錄結構

```
latex_assembly_demo/
├── source_files/              # 源文件（組裝前）
│   ├── mainbody_post_refined.tex   # 主體內容（已精修）
│   ├── abstract.tex                # 摘要
│   ├── outlines.json              # 大綱（包含標題）
│   └── survey.ini.tex             # LaTeX 模板
├── compiled_output/           # 編譯目錄
│   ├── references.bib             # 參考文獻
│   ├── neurips_2024.sty          # LaTeX 樣式檔
│   ├── watermark.png             # 浮水印圖片
│   ├── figs/                     # 圖表目錄
│   ├── *_table.tex               # 表格檔案
│   └── survey.tex                # 組裝後的完整文檔（生成）
├── scripts/                   # 腳本
│   ├── assemble_latex.py         # 組裝腳本（Python）
│   ├── compile_survey.sh         # 編譯腳本（Bash）
│   └── add_watermark.py          # 浮水印腳本（Python）
└── README.md                  # 本文件
```

## 🚀 快速開始

### 一鍵執行（推薦）

從專案根目錄執行：

```bash
# 確保在 surveyx 環境中
conda activate surveyx

# 一鍵執行（組裝 + 編譯）
bash sandbox/latex_assembly_demo/scripts/run_all.sh
```

`run_all.sh` 會自動檢查並啟用 conda 環境。

### 分步執行

如果想了解每個步驟：

```bash
# 進入 demo 目錄
cd sandbox/latex_assembly_demo

# 步驟 1: 組裝 LaTeX 文檔
python scripts/assemble_latex.py

# 步驟 2: 編譯 PDF
bash scripts/compile_survey.sh
```

## 📋 流程說明

### 步驟 1: 組裝 LaTeX 文檔 (`assemble_latex.py`)

這個腳本重現了 `LatexTextBuilder` 的功能，將各個組件組裝成完整的 LaTeX 文檔：

```python
# 組裝順序：
1. 載入模板 (survey.ini.tex)
2. 從 outlines.json 讀取標題
3. 加入標題與作者 (\title, \author, \begin{document})
4. 加入摘要 (abstract.tex)
5. 加入主體內容 (mainbody_post_refined.tex)
6. 加入參考文獻區塊 (\bibliography{references})
7. 加入免責聲明
8. 結束文檔 (\end{document})
9. 儲存為 compiled_output/survey.tex
```

**輸入**：
- `source_files/survey.ini.tex` - LaTeX 模板
- `source_files/outlines.json` - 大綱（含標題）
- `source_files/abstract.tex` - 摘要
- `source_files/mainbody_post_refined.tex` - 主體內容

**輸出**：
- `compiled_output/survey.tex` - 完整的 LaTeX 文檔

**特點**：
- ✅ **純 Python 程式碼**，無 LLM 參與
- ✅ 字串拼接與檔案讀寫
- ✅ 可獨立運行，不需要 API key

### 步驟 2: 編譯 PDF (`compile_survey.sh`)

這個腳本自動化編譯流程：

```bash
# 編譯流程：
1. 檢查必要檔案 (survey.tex, references.bib, neurips_2024.sty)
2. 切換到 compiled_output/ 目錄
3. 執行 latexmk 編譯
4. 清理中間檔案 (.aux, .log, .bbl 等)
5. 移動 PDF 到上層目錄
6. 加入浮水印 (可選)
```

**需求**：
- `latexmk` (LaTeX 編譯工具)
- `references.bib` (參考文獻)
- `neurips_2024.sty` (樣式檔)
- `figs/` (圖表目錄)

**輸出**：
- `survey.pdf` - 最終 PDF
- `survey_wtmk.pdf` - 浮水印版本（可選）
- `compiled_output/compile.log` - 編譯日誌

## 🔍 關鍵檔案說明

### source_files/mainbody_post_refined.tex

這是經過完整 post-refinement 流程處理的主體內容，包含：

- ✅ RAG 精修（準確引用）
- ✅ 章節重寫（壓縮優化）
- ✅ 圖表建構（視覺化）
- ✅ 規則精修（縮寫、引用映射）
- ✅ 表格生成（三種表格）

### source_files/survey.ini.tex

LaTeX 文檔頭部模板，包含：

```latex
\documentclass{article}
\usepackage{neurips_2024}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{hyperref}
\usepackage{url}
\usepackage{booktabs}
\usepackage{amsfonts}
\usepackage{nicefrac}
\usepackage{microtype}
\usepackage{xcolor}
% ... 更多 packages
```

### compiled_output/references.bib

BibTeX 參考文獻資料庫，格式：

```bibtex
@article{author2024title,
    title={Paper Title},
    author={Author Name},
    journal={Journal},
    year={2024}
}
```

## 🛠️ 依賴套件

### Python 依賴

```bash
# 基本組裝（必需）
# 無需額外套件，使用 Python 標準庫

# 浮水印功能（可選）
pip install pymupdf
```

### LaTeX 依賴

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install texlive-full

# macOS
brew install --cask mactex

# 驗證安裝
latexmk --version
```

## 📊 流程圖

```
┌─────────────────────────────────────────┐
│  source_files/                          │
│  ├── mainbody_post_refined.tex         │
│  ├── abstract.tex                      │
│  ├── outlines.json                     │
│  └── survey.ini.tex                    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ assemble_latex.py   │
        │ (純 Python 組裝)    │
        └─────────┬───────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  compiled_output/survey.tex             │
│  (完整的 LaTeX 文檔)                    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ compile_survey.sh   │
        │ (latexmk 編譯)      │
        └─────────┬───────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  survey.pdf                             │
│  survey_wtmk.pdf (浮水印版)             │
└─────────────────────────────────────────┘
```

## ❓ 常見問題

### Q1: 為什麼需要兩個步驟？

**A:** 分離關注點：
- **步驟 1 (組裝)**：純 Python，快速，可重複執行
- **步驟 2 (編譯)**：依賴 LaTeX，較慢，產生最終 PDF

### Q2: 可以只運行組裝步驟嗎？

**A:** 可以！如果只想查看生成的 `survey.tex` 內容：

```bash
python scripts/assemble_latex.py
# 查看結果
cat compiled_output/survey.tex
```

### Q3: 編譯失敗怎麼辦？

**A:** 檢查日誌：

```bash
# 查看完整編譯日誌
cat compiled_output/compile.log

# 查看最後 50 行
tail -n 50 compiled_output/compile.log
```

常見問題：
- 缺少 LaTeX 套件 → 安裝 `texlive-full`
- 圖片檔案不存在 → 檢查 `figs/` 目錄
- 參考文獻錯誤 → 檢查 `references.bib`

### Q4: 如何修改內容？

**A:** 修改源文件後重新組裝：

```bash
# 1. 編輯 source_files/ 中的檔案
# 2. 重新組裝
python scripts/assemble_latex.py
# 3. 重新編譯
bash scripts/compile_survey.sh
```

### Q5: 這個流程有 LLM 參與嗎？

**A:** **完全沒有！** 這是純 coding 流程：
- ❌ 無 LLM API 呼叫
- ❌ 無 AI 推理
- ✅ 純檔案讀寫
- ✅ 純字串拼接
- ✅ 可離線執行

## 📝 與原始 Pipeline 的對應

這個 demo 對應 SurveyX pipeline 的最後兩個步驟：

| Pipeline 階段 | 對應腳本 | LLM 參與 |
|--------------|---------|----------|
| 階段 5: Post-refinement | ✗ (已完成) | ✅ 有 |
| 階段 6a: 組裝 LaTeX | `assemble_latex.py` | ❌ 無 |
| 階段 6b: 編譯 PDF | `compile_survey.sh` | ❌ 無 |

## 🔗 相關文件

- 源碼：`src/modules/latex_handler/latex_text_builder.py`
- 源碼：`src/models/generator/latex_generator.py`
- Pipeline 說明：`pipeline&modules.md`
- 代碼統計：`CodeStats/stats.md`

## 📄 授權

此 demo 屬於 SurveyX 專案的一部分。

---

**提示**：這個 demo 展示了從 `mainbody_post_refined.tex` 到 `survey.tex` 的純 coding 轉換過程，不涉及任何 AI 或 LLM。
