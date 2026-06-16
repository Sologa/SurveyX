# LaTeX 組裝與編譯操作手冊

本文件說明本資料夾的檔案結構與完整使用流程，讓你可直接修改 LaTeX 來源並編譯出 PDF。

## 1) 目錄結構（必要檔案）

```
latex_assembly_bundle/
├── source_files/                  # 來源內容（可修改）
│   ├── mainbody_post_refined.tex
│   ├── abstract.tex
│   ├── outlines.json
│   └── survey.ini.tex
├── compiled_output/               # 編譯所需資源 + 生成的 survey.tex
│   ├── survey.tex                 # 組裝後的完整 LaTeX（可直接改）
│   ├── references.bib
│   ├── neurips_2024.sty
│   ├── watermark.png
│   ├── figs/                       # 圖表檔
│   ├── summary_table.tex
│   ├── comparison_table.tex
│   ├── benchmark_table.tex
│   ├── Arbitrary_table_1.tex
│   ├── Arbitrary_table_2.tex
│   └── Arbitrary_table_3.tex
└── scripts/
    ├── assemble_latex.py
    ├── compile_survey.sh
    ├── run_all.sh
    └── add_watermark.py
```

## 2) 環境需求

- Conda 環境：`surveyx`
- LaTeX 工具鏈：`latexmk`、`pdflatex`、`bibtex`
- （可選）浮水印需要：Python + `PyMuPDF`

## 3) 可修改範圍

### 建議修改（穩定且可重建）
- `source_files/mainbody_post_refined.tex`
- `source_files/abstract.tex`
- `source_files/survey.ini.tex`
- `source_files/outlines.json`

### 快速修補（可直接編譯）
- `compiled_output/survey.tex`
- `compiled_output/*_table.tex`
- `compiled_output/figs/*.tex`

> 注意：只要重新執行組裝，`compiled_output/survey.tex` 會被覆蓋。

## 4) 完整操作流程（推薦）

### 步驟 A：修改來源
1. 編輯 `source_files/` 內的內容

### 步驟 B：組裝
```bash
python3 scripts/assemble_latex.py
```
完成後會生成：`compiled_output/survey.tex`

### 步驟 C：編譯
```bash
bash scripts/compile_survey.sh
```
成功後會在本資料夾根目錄產生：
- `survey.pdf`
- `survey_wtmk.pdf`（若浮水印成功）

## 5) 快速修補流程（不重組裝）

1. 直接修改 `compiled_output/survey.tex`
2. 直接編譯：
```bash
bash scripts/compile_survey.sh
```

## 6) 日誌與錯誤排查

- 編譯日誌：`compiled_output/compile.log`
- 只看錯誤：
```bash
grep "^!" compiled_output/compile.log
```
- 只看最後 100 行：
```bash
tail -n 100 compiled_output/compile.log
```

## 7) Linting（可選）

### 安裝 lint 工具
- macOS：若已安裝 TeX Live / MacTeX，通常已包含 `chktex` 與 `lacheck`。
- Ubuntu：可用 `apt` 安裝對應套件名稱 `chktex` 與 `lacheck`。

### ChkTeX（風格/排版類警告）
```bash
chktex compiled_output/survey.tex
```

輸出若需要機器可解析格式：
```bash
chktex -q -v0 -f "%f:%l:%c:%k:%n:%m\n" compiled_output/survey.tex
```

### lacheck（一致性檢查）
```bash
lacheck compiled_output/survey.tex
```

> Linting 只提供警告/建議，不會產生 PDF。

## 8) 常見問題

- 找不到 `survey.tex`：先跑 `assemble_latex.py`
- 找不到 `references.bib` 或 `neurips_2024.sty`：確認 `compiled_output/` 檔案完整
- 沒有 `latexmk`：請安裝完整 LaTeX 發行版（如 TeX Live / MacTeX）
- 浮水印失敗：通常是缺少 `PyMuPDF`，可先忽略

## 9) 清理說明

`compile_survey.sh` 會自動清理中間檔（`latexmk -c`），不會刪除你的來源檔。

---

如需轉移到其他資料夾，務必保持以上相對路徑結構一致。
