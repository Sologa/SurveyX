# SurveyX LaTeX 修正模組規劃

## 背景與需求
- 依據 `AI-Scientist-v2/CodeStats/stats.md` 與 `AI-Scientist-v2/my_docs/pipeline_analysis_qa.md` 的流程總結，AI-Scientist 的寫稿階段會在「生成 → 編譯 → chktex → 反思修正」之間反覆循環，確保最終 LaTeX 能自動收斂成可編譯版本。[1][2]
- SurveyX 目前只由 `LatexTextBuilder` 串接章節並直接呼叫 `latexmk`；缺乏自動化的檢查、修正與報告機制，導致像 `outputs/2025-10-09-1630_speec` 這類大型產出需要人工外部化 TikZ、調整 `\autoref`、手動補救 Unicode 異常等。
- `sandbox/latex_citation_fix` 重現的 `\caption@xref` 與 en-dash 問題揭示：我們需要能夠自動定位「未解析參照」、「TikZ 過大造成 label 寫回失敗」、「非 ASCII 字元」等錯誤，並產生可追溯報告。

## 既有問題診斷
- **引用失敗 (`\caption@xref`)**：`survey.tex.ORIGINAL_BROKEN` 的 `fig:tree_figure_Langu`、`fig:tiny_tree_figure_5` 都被寫成 `\caption@xref` 佔位符，證明 TikZ 內聯過大時 label 不會寫回 `.aux`。[sandbox/latex_citation_fix/README.md]
- **Unicode 與標點**：`tmp/unicode_glitch_report.txt` 顯示單一檔案就有 500+ 個非 ASCII 符號，包含 en dash 等需要轉為對應命令的字元。
- **流程缺口**：缺乏集中式報告與備份，難以複現或回溯自動修復步驟；`survey.tex` 中同時殘留 `Figure~5` 與 `\autoref{fig:tiny_tree_figure_0}`，顯示人工修復沒有一致化。

## 模組整體架構
```
LatexFixPipeline
├─ ContextLoader          # 解析 task_id、檔案路徑、暫存資料
├─ DiagnosticsStage       # 生成一次編譯輸出，解析 compile.log / survey.aux
├─ IssueRegistry          # 將偵測到的問題標準化（類型、位置、建議修法）
├─ FixerRunner
│  ├─ CaptionXrefFixer    # TikZ 過大 → standalone 外部化 / includegraphics
│  ├─ AutorefNormalizer   # 將失敗的 \autoref 改為可控格式（\cref/\ref/Figure~）
│  ├─ UnicodeFixer        # 依 mapping 將非 ASCII 轉為 LaTeX 指令
│  ├─ LintOrchestrator    # 呼叫 chktex、latexindent 產生額外警告與格式化建議
│  └─ SafetyNetFixer      # 最多 N 輪修復迴圈，避免無限嘗試
└─ ReportWriter           # 產生 latex_fix_report.json / markdown 摘要
```

## 問題類型與對策
| 類型 | 偵測線索 | 修復策略 | 產出 |
|------|----------|----------|------|
| TikZ 造成 `\caption@xref` | `.aux` 行含 `\caption@xref`；`compile.log` 有 `Label(s) may have changed` 或 TikZ warning | 1) 建立 `figs/<name>_standalone.tex` 使用 `standalone` class；2) `latexmk -shell-escape` 生成 PDF；3) 原始 `.tex` -> `\includegraphics` 包裝並保留 `\caption`/`\label`；4) 更新 `survey.tex` 的 `\autoref` 仍指向原 label | `figs/<name>_standalone.*`、原檔 `.backup`、修復報告項目 |
| `\autoref` 仍失敗 | 第二次編譯後 `.aux` 仍找不到 label | 將 `\autoref{...}` 降級為 `Figure~\ref{...}`，必要時附註 `\phantomsection` 確保超連結；保留 `hyperref` 一致性 | `latex_fix_report.json` 中記錄替換行，供人工回顧 |
| Unicode / 非 ASCII | `unicode_glitch_report.txt` 或 `DiagnosticsStage` 直接掃描 | 使用可維護的 mapping (`resources/LLM/unicode_mapping.json`) 轉換為 `$\approx$` 等；en dash 轉 `--` | 產出 `unicode_fix_diff.patch`、更新 `.tex` |
| Lint / spacing | `chktex` 輸出代碼 3+ | 自動插入 `~`、修正多餘空白等（可選擇 dry-run）；若影響語意則加入 TODO | `chktex_report.txt` |
| 其他編譯錯誤 | `latexmk` 非零狀態或 `compile.log` 有 `!` | 偵測後停止自動修復，產出失敗報告並保留中間 artefacts | `latex_fix_report.json` 的 `status=failure` |

## 修復流程設計
1. **初始化**：`LatexFixPipeline(task_id, config)` 讀取 `outputs/<task_id>/latex`、`tmp/` 以及歷史備份，建立工作目錄（如 `outputs/<task_id>/tmp/latex_fix/`）。
2. **首次診斷**：呼叫 `latexmk -pdf -interaction=nonstopmode -f survey.tex`，並將日誌保存成 `compile_first.log`；同時記錄 `survey.aux`、`*.log` 的哈希值。
3. **問題登記**：
   - `CaptionXrefDetector` 從 `.aux` 擷取 `\newlabel{...}{\caption@xref ...}`；
   - `UnicodeScanner` 直接掃描 `survey.tex` 與 `figs/*.tex`；
   - `ChktexAdapter` 執行 `chktex`（參考官方說明其適合作為 LaTeX Lint 工具[3]）。
4. **修復迭代**（預設最多 3 輪）：
   - 依 IssueRegistry 優先順序執行對應 Fixer；
   - 每輪修復完重新編譯並比對 `compile.log` 差異；若沒有新問題則提前中止；
   - 若出現未知錯誤則回滾本輪改動，記錄到報告並停止。
5. **輸出報告**：
   - `latex_fix_report.json`: 列出偵測問題、修復策略、受影響檔案、耗時；
   - `latex_fix_report.md`: 提供給人類維護者閱讀的摘要；
   - 所有修改過的 `.tex` 自動備份到 `tmp/latex_fix/backups/`，命名含 timestamp。
6. **與 pipeline 整合**：`LatexGenerator.generate_full_survey()` 之後、`compile_single_survey()` 之前插入 `LatexFixPipeline.run()`，並將 TimeMonitor 納入記錄。

## 程式碼與檔案調整建議
- 新增模組：
  - `src/modules/latex_fix/pipeline.py`：主 orchestrator。
  - `src/modules/latex_fix/detectors.py`：封裝 log / aux 分析。
  - `src/modules/latex_fix/fixers/`：`caption_xref.py`、`unicode.py`、`autoref.py` 等。
  - `src/modules/latex_fix/reporters.py`：統一產生 JSON/Markdown。
- 既有檔案調整：
  - `src/models/generator/latex_generator.py`：導入新模組、調整 `generate_full_survey()`。
  - `tasks/workflow/06_gen_latex.py`：在產生 PDF 前增設 CLI flag（如 `--skip-latex-fix`）。
  - `run.sh`：補充說明與選項。
  - 視需要新增 `configs/latex_fix.yml` 供閾值（TikZ 行數上限、迭代次數）配置。
- 資源檔案：
  - `resources/LLM/unicode_mapping.json`（非 ASCII → 替代命令）。
  - `docs/` 內新增 `docs/resolved_issues/latex_fix/` 的更新紀錄。

## 測試與驗證計畫
- **單元測試**：為 `CaptionXrefFixer`、`UnicodeFixer` 撰寫 pytest，使用 sandbox 中的 broken 範例作為 fixture。
- **整合測試**：在 `./run.sh workflow <task_id>` 中新增 `--verify-latex-fix` 選項，執行 pipeline 並檢查最終 PDF 是否生成。
- **回歸測試**：對 `outputs/2025-10-09-1630_speec/tmp/mainbody_post_refined.tex` 重新跑全流程，確認不再需要人工修補。
- **Sandbox 驗證**：套用 `sandbox/latex_citation_fix/tools/latex_fix_toolkit.py` 的驗證腳本檢查成果，並記錄互相佐證的結果。

## 推動步驟（草案）
1. **階段 0**：建立模組骨架、配置檔與報告格式（1~2 天）。
2. **階段 1**：實作 CaptionXrefFixer + UnicodeFixer，針對 sandbox 用例通過測試（2~3 天）。
3. **階段 2**：整合 pipeline，補齊 logging 與備份，於實際 `task_id` 驗證（2 天）。
4. **階段 3**：導入 lint/格式化（chktex、latexindent），補齊文件與維護 SOP（1~2 天）。
5. **階段 4**：觀察期與調整（根據使用者回報迭代）。

## 風險與緩解
- **外部化需要 `-shell-escape`**：需確認執行環境允許；可在 `configs/latex_fix.yml` 提供 `allow_shell_escape` 選項，並於報告提示使用者授權。[4]
- **自動修復誤判**：所有改動保留 `*.backup` 與 diff；若檔案非預期變動則立即停止並要求人工覆核。
- **Unicode mapping 漏洞**：初期先覆蓋 `tmp/unicode_glitch_report.txt` 中的常見符號，並提供額外 YAML 允許使用者擴充。
- **執行時間增加**：每個 fix 迭代記錄耗時，若超過閾值可以讓使用者透過旗標跳過特定修復。

## 參考資料
[1] `AI-Scientist-v2/CodeStats/stats.md`，寫稿階段多輪編譯／修正流程概述。  
[2] `AI-Scientist-v2/my_docs/pipeline_analysis_qa.md`，Stage 4 Writeup 詳細流程與工具。  
[3] ChkTeX 官方網站，指出其作為 LaTeX semantic/syntactic checker，可補足 LaTeX 原生檢查不足之處：<https://www.nongnu.org/chktex/>。  
[4] TikZ External Library 手冊，說明 `\tikzexternalize` 會外部化圖像並正確處理 `\label` 等 aux 資料，提供自動處理大型 TikZ 的理論依據：<https://tikz.dev/library-external#section-library-external-introduction>。

