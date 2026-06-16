# LaTeX Assembly Demo - 檔案清單

## 📁 完整目錄結構

```
sandbox/latex_assembly_demo/
├── README.md                         # 完整說明文件
├── QUICKSTART.md                     # 快速開始指南
├── FILE_LIST.md                      # 本文件
│
├── source_files/                     # 源文件（組裝前）
│   ├── mainbody_post_refined.tex    # 397 KB - 已精修的主體內容
│   ├── abstract.tex                 # 2.0 KB - 摘要
│   ├── outlines.json                # 27 KB  - 大綱（含標題）
│   └── survey.ini.tex               # 1.4 KB - LaTeX 模板頭部
│
├── compiled_output/                  # 編譯目錄與資源
│   ├── survey.tex                   # 400 KB - 組裝後的完整文檔（生成）
│   ├── references.bib               # 74 KB  - 參考文獻資料庫
│   ├── neurips_2024.sty            # 11 KB  - LaTeX 樣式檔
│   ├── watermark.png                # 18 KB  - 浮水印圖片
│   ├── figs/                        # 圖表目錄
│   ├── summary_table.tex            # 2.2 KB - 彙總表格
│   ├── comparison_table.tex         # 1.4 KB - 比較表格
│   ├── benchmark_table.tex          # 2.1 KB - 基準表格
│   ├── Arbitrary_table_1.tex        # 1.5 KB - 任意表格 1
│   ├── Arbitrary_table_2.tex        # 1.3 KB - 任意表格 2
│   └── Arbitrary_table_3.tex        # 1.3 KB - 任意表格 3
│
└── scripts/                          # 腳本工具
    ├── run_all.sh                   # 一鍵執行腳本
    ├── assemble_latex.py            # 組裝腳本（Python）
    ├── compile_survey.sh            # 編譯腳本（Bash）
    └── add_watermark.py             # 浮水印腳本（Python）
```

## 📝 檔案說明

### 🔵 源文件 (source_files/)

| 檔案 | 大小 | 說明 | 來源 |
|------|------|------|------|
| `mainbody_post_refined.tex` | 397 KB | 已完成所有 LLM 精修的主體內容 | `outputs/2025-10-09-1630_speec/tmp/` |
| `abstract.tex` | 2.0 KB | 論文摘要 | `outputs/2025-10-09-1630_speec/tmp/` |
| `outlines.json` | 27 KB | 包含標題、章節結構 | `outputs/2025-10-09-1630_speec/` |
| `survey.ini.tex` | 1.4 KB | LaTeX 文檔頭部模板 | `resources/latex/` |

### 🟢 編譯資源 (compiled_output/)

| 檔案 | 大小 | 說明 | 來源 |
|------|------|------|------|
| `survey.tex` | 400 KB | **生成的完整 LaTeX 文檔** | 由 `assemble_latex.py` 生成 |
| `references.bib` | 74 KB | BibTeX 參考文獻 | `outputs/.../latex/` |
| `neurips_2024.sty` | 11 KB | NeurIPS 2024 樣式檔 | `resources/latex/` |
| `watermark.png` | 18 KB | SurveyX 浮水印 | `resources/latex/` |
| `figs/` | - | 圖表目錄（包含結構圖等） | `outputs/.../latex/figs/` |
| `*_table.tex` | 各約 1-2 KB | 由 LLM 生成的表格 | `outputs/.../latex/` |

### 🟡 腳本工具 (scripts/)

| 檔案 | 行數 | 說明 | 語言 |
|------|------|------|------|
| `run_all.sh` | 24 | 一鍵執行：組裝 + 編譯 | Bash |
| `assemble_latex.py` | 165 | 將各組件組裝成 survey.tex | Python |
| `compile_survey.sh` | 136 | 編譯 LaTeX 為 PDF | Bash |
| `add_watermark.py` | 73 | 為 PDF 加入浮水印 | Python |

## 🔄 檔案流程

```
source_files/
├── survey.ini.tex ────┐
├── outlines.json ─────┤
├── abstract.tex ──────┼─→ assemble_latex.py ─→ survey.tex
└── mainbody_post_refined.tex ─┘

compiled_output/
├── survey.tex ────────┐
├── references.bib ────┤
├── neurips_2024.sty ──┼─→ compile_survey.sh ─→ survey.pdf
├── figs/ ─────────────┤
└── *_table.tex ───────┘
```

## 🎯 關鍵檔案

### 最重要的 3 個檔案

1. **`source_files/mainbody_post_refined.tex`** (397 KB)
   - 包含所有章節內容
   - 已完成 RAG、章節重寫、圖表、表格等精修
   - 這是 Pipeline 階段 5 的最終輸出

2. **`scripts/assemble_latex.py`** (165 行)
   - 核心組裝邏輯
   - 純 Python，無 LLM
   - 展示如何從組件生成完整 LaTeX

3. **`compiled_output/survey.tex`** (400 KB)
   - 完整的 LaTeX 文檔
   - 可直接用 `latexmk` 編譯
   - 包含所有引用、圖表、表格

## 📊 檔案大小統計

```
總計: ~1.3 MB

源文件:        ~427 KB (33%)
├── mainbody  397 KB
├── outlines   27 KB
├── abstract    2 KB
└── template    1 KB

編譯資源:      ~890 KB (67%)
├── survey.tex 400 KB
├── references  74 KB
├── figs/      多個檔案
├── tables      ~10 KB
├── sty         11 KB
└── watermark   18 KB
```

## 🔍 如何使用這些檔案

### 查看源文件

```bash
# 查看主體內容
less source_files/mainbody_post_refined.tex

# 查看大綱
cat source_files/outlines.json | jq '.title'

# 查看摘要
cat source_files/abstract.tex
```

### 組裝與編譯

```bash
# 方式 1: 一鍵執行
bash scripts/run_all.sh

# 方式 2: 分步執行
python3 scripts/assemble_latex.py
bash scripts/compile_survey.sh
```

### 檢查輸出

```bash
# 查看組裝結果
less compiled_output/survey.tex

# 查看編譯日誌
less compiled_output/compile.log

# 檢視 PDF
open survey.pdf  # macOS
```

## 🛠️ 修改指南

### 如果要修改內容

```bash
# 1. 編輯源文件
vim source_files/mainbody_post_refined.tex

# 2. 重新組裝
python3 scripts/assemble_latex.py

# 3. 重新編譯
bash scripts/compile_survey.sh
```

### 如果要修改樣式

```bash
# 編輯模板
vim source_files/survey.ini.tex

# 或編輯樣式檔
vim compiled_output/neurips_2024.sty
```

### 如果要修改表格

```bash
# 編輯表格檔案
vim compiled_output/summary_table.tex

# 重新編譯即可（不需重新組裝）
bash scripts/compile_survey.sh
```

## ✅ 檔案驗證

### 檢查所有必需檔案

```bash
# 檢查源文件
ls -lh source_files/
# 應該有 4 個檔案

# 檢查編譯資源
ls -lh compiled_output/
# 應該有 references.bib, neurips_2024.sty, figs/ 等

# 檢查腳本
ls -lh scripts/
# 應該有 4 個可執行腳本
```

### 驗證檔案完整性

```bash
# 檢查主體內容不為空
wc -l source_files/mainbody_post_refined.tex
# 應該有數千行

# 檢查參考文獻
grep -c '^@' compiled_output/references.bib
# 應該有數十到數百筆引用

# 檢查圖表目錄
ls compiled_output/figs/ | wc -l
# 應該有多個 .tex 或 .pdf 檔案
```

## 📚 相關資源

- **完整說明**: `README.md`
- **快速開始**: `QUICKSTART.md`
- **源碼參考**: 
  - `src/modules/latex_handler/latex_text_builder.py`
  - `src/models/generator/latex_generator.py`
- **Pipeline 文檔**: `../../pipeline&modules.md`

---

最後更新: 2025-10-25
