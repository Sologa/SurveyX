# 📚 LaTeX Assembly Demo - 索引

> 展示如何從 `mainbody_post_refined.tex` 組裝成 `survey.tex` 並編譯成 PDF

## 🎯 目的

這個 demo 展示 SurveyX Pipeline 最後階段的**純 coding 流程**：
- ✅ 無 LLM 參與
- ✅ 純檔案組裝
- ✅ 可離線執行
- ✅ 完全可重現

## 📖 文檔導覽

### 🚀 快速上手

1. **[QUICKSTART.md](QUICKSTART.md)** - 新手必讀
   - 環境準備（conda surveyx）
   - 一鍵執行指令
   - 預期輸出
   - 常見問題

2. **[COMPILATION_NOTES.md](COMPILATION_NOTES.md)** - 編譯說明
   - 編譯成功的判斷標準
   - 警告訊息解釋（重要！）
   - 警告 vs 錯誤的區別
   - 失敗時的診斷方法

### 📘 詳細說明

3. **[README.md](README.md)** - 完整文檔
   - 環境需求
   - 目錄結構
   - 流程說明
   - 腳本功能
   - 與 Pipeline 的對應

4. **[FILE_LIST.md](FILE_LIST.md)** - 檔案清單
   - 完整檔案列表
   - 檔案大小統計
   - 使用指南

## 🛠️ 腳本工具

### 主要腳本

| 腳本 | 用途 | 指令 |
|------|------|------|
| `run_all.sh` | 一鍵執行 | `bash scripts/run_all.sh` |
| `assemble_latex.py` | 組裝 LaTeX | `python3 scripts/assemble_latex.py` |
| `compile_survey.sh` | 編譯 PDF | `bash scripts/compile_survey.sh` |
| `add_watermark.py` | 加浮水印 | 自動調用 |

### 快速指令

```bash
# 從專案根目錄執行
cd /path/to/SurveyX

# 一鍵執行
bash sandbox/latex_assembly_demo/scripts/run_all.sh

# 或分步執行
python3 sandbox/latex_assembly_demo/scripts/assemble_latex.py
bash sandbox/latex_assembly_demo/scripts/compile_survey.sh
```

## 📁 目錄結構

```
latex_assembly_demo/
├── 📖 README.md          - 完整說明
├── 🚀 QUICKSTART.md      - 快速開始
├── 📋 FILE_LIST.md       - 檔案清單
├── 📚 INDEX.md           - 本文件
│
├── 📂 source_files/      - 源文件
│   ├── mainbody_post_refined.tex  ← 關鍵輸入
│   ├── abstract.tex
│   ├── outlines.json
│   └── survey.ini.tex
│
├── 📂 compiled_output/   - 編譯目錄
│   ├── survey.tex        ← 組裝輸出
│   ├── references.bib
│   ├── figs/
│   └── ...
│
└── 📂 scripts/           - 工具腳本
    ├── run_all.sh        ← 一鍵執行
    ├── assemble_latex.py
    ├── compile_survey.sh
    └── add_watermark.py
```

## 🔄 完整流程

```
┌──────────────────────┐
│  source_files/       │
│  所有組件              │
└──────────┬───────────┘
           │
           ▼
   ┌───────────────┐
   │ assemble_     │
   │ latex.py      │ ← 純 Python 組裝
   └───────┬───────┘
           │
           ▼
┌──────────────────────┐
│ compiled_output/     │
│ survey.tex           │ ← 完整 LaTeX 文檔
└──────────┬───────────┘
           │
           ▼
   ┌───────────────┐
   │ compile_      │
   │ survey.sh     │ ← latexmk 編譯
   └───────┬───────┘
           │
           ▼
┌──────────────────────┐
│ survey.pdf           │ ← 最終 PDF
│ survey_wtmk.pdf      │ ← 浮水印版
└──────────────────────┘
```

## ✅ 驗證清單

在執行前，請確認：

- [ ] Python 3.6+ 已安裝
- [ ] latexmk 已安裝（編譯需要）
- [ ] 所有源文件都存在於 `source_files/`
- [ ] 編譯資源都存在於 `compiled_output/`

## 📊 預期結果

成功執行後會生成：

```
sandbox/latex_assembly_demo/
├── survey.pdf          ← 85 頁，~2.3 MB
├── survey_wtmk.pdf     ← 浮水印版
└── compiled_output/
    ├── survey.tex      ← ~400 KB
    └── compile.log     ← 編譯日誌
```

## 🔍 學習路徑

### 新手路徑

1. 閱讀 [QUICKSTART.md](QUICKSTART.md)
2. 執行 `bash scripts/run_all.sh`
3. 查看生成的 `survey.pdf`

### 進階路徑

1. 閱讀 [README.md](README.md)
2. 查看 [FILE_LIST.md](FILE_LIST.md)
3. 研究 `scripts/assemble_latex.py` 源碼
4. 修改源文件並重新組裝

### 開發者路徑

1. 理解完整流程
2. 對照 `src/modules/latex_handler/latex_text_builder.py`
3. 客製化組裝邏輯
4. 整合到自己的 Pipeline

## 🎓 關鍵概念

### 為什麼要分離組裝與編譯？

- **組裝**（Python）：快速、可調試、純邏輯
- **編譯**（LaTeX）：較慢、依賴工具、產生最終 PDF

### 這個流程有 AI 嗎？

**完全沒有！**
- ❌ 無 LLM API
- ❌ 無 AI 推理
- ✅ 純檔案操作
- ✅ 字串拼接

### 與 Pipeline 的關係

| Pipeline 階段 | 此 Demo |
|--------------|---------|
| 階段 1-4 | ✗ 未包含 |
| 階段 5 (Post-refine) | ✗ 已完成（輸入） |
| 階段 6a (組裝) | ✅ `assemble_latex.py` |
| 階段 6b (編譯) | ✅ `compile_survey.sh` |

## 🔗 相關資源

### 專案內部

- 源碼實現：`src/modules/latex_handler/latex_text_builder.py`
- Generator：`src/models/generator/latex_generator.py`
- Pipeline 說明：`../../pipeline&modules.md`
- 代碼統計：`../../CodeStats/stats.md`

### 外部資源

- [LaTeX 官方文檔](https://www.latex-project.org/help/documentation/)
- [latexmk 手冊](https://mg.readthedocs.io/latexmk.html)
- [PyMuPDF 文檔](https://pymupdf.readthedocs.io/)

## 🆘 需要幫助？

1. 查看 [QUICKSTART.md](QUICKSTART.md) 的故障排除
2. 檢查 `compiled_output/compile.log`
3. 參考 [README.md](README.md) 的詳細說明
4. 查閱 [FILE_LIST.md](FILE_LIST.md) 確認檔案完整

## 📝 更新記錄

- **2025-10-25**: 初始版本建立
  - 複製源文件與編譯資源
  - 建立組裝與編譯腳本
  - 撰寫完整文檔

---

**開始使用**: [QUICKSTART.md](QUICKSTART.md) → `bash scripts/run_all.sh`
