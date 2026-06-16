# GPT-5.1-Codex LaTeX Fixing Plan

> 目標：在不開啟 PDF 的前提下，依靠 lint 與編譯日誌來迭代修復 `compiled_output/survey.tex` 中的錯誤與警告，最多 10 輪，直到產出乾淨的 `compile.log` 與可接受的 lint 結果。以下內容採用 sequential-thinking MCP 的建議路徑進行編排。

---

## 0. 目錄用途速記

- `source_files/`：組裝前的模板、摘要、主體與大綱；若重新組裝會覆寫 `compiled_output/survey.tex`。
- `scripts/assemble_latex.py`：以模板順序串接 source，輸出 `compiled_output/survey.tex`。
- `scripts/compile_survey.sh`：在 `compiled_output/` 內以 `latexmk` 編譯並輸出 `compile.log`、`survey.pdf`（雖禁止查看 PDF，但仍會生成）。
- `compiled_output/`：最終工作區；`survey.tex`、`references.bib`、`neurips_2024.sty`、各種圖表/表格 Tex 檔與 `compile.log` 均位於此。

理解此結構有助於定位錯誤來源並避免在錯誤位置動手。

---

## 1. 工具安裝與基本用法

### 1.1 LaTeX toolchain（一次性）

- **macOS**：`brew install --cask mactex`
- **Ubuntu/Debian**：`sudo apt-get install texlive-full`
- 驗證：`latexmk --version`, `pdflatex --version`, `bibtex --version`

### 1.2 Lint 工具：ChkTeX 與 LaCheck

| 平台 | 安裝 | 備註 |
| --- | --- | --- |
| macOS | `brew update && brew install chktex lacheck` | Homebrew 同時提供兩者 |
| Ubuntu/Debian | `sudo apt-get update && sudo apt-get install chktex lacheck` | 套件倉庫自帶 |

#### ChkTeX 使用範例（對 `compiled_output/survey.tex`）

```bash
# 最精簡：輸出檔名:行:列:代碼:訊息，利於程式解析
chktex -q -f%f:%l:%c:%d:%k:%n:%m\n compiled_output/survey.tex

# 忽略特定規則（例：1,8），避免噪音
chktex -q -n1 -n8 -f%f:%l:%c:%k:%n:%m\n compiled_output/survey.tex

# 使用自訂忽略設定
chktex -q -p scripts/.chktexrc compiled_output/survey.tex
```

#### LaCheck 使用範例

```bash
lacheck compiled_output/survey.tex > compiled_output/lacheck.out
```

> LaCheck 偵測較嚴重的語法問題；訊息較少但有助鎖定未關閉環境、拼錯命令等。

### 1.3 推薦整合腳本（可選）

若尚未建立，建議新增 `scripts/lint_and_compile.sh`（可複用 raptor-mini 範本）：

1. 依序執行 chktex、lacheck。
2. 在 `compiled_output/` 內執行 `latexmk -pdf -interaction=nonstopmode -f survey.tex`。
3. 收集輸出至 `compiled_output/chktex.out`、`compiled_output/lacheck.out`、`compiled_output/compile.log`，並額外輸出 JSON 摘要 `compiled_output/lint_report.json`（含最後 200 行編譯訊息）。

這個腳本讓 Agent 擁有單一入口命令以便重複調用。

---

## 2. Agent I/O 權限界線（無 PDF）

| 類別 | 可讀檔案 | 說明 |
| --- | --- | --- |
| **核心輸入** | `compiled_output/survey.tex` | 主要修復檔案 |
| | `compiled_output/compile.log`, `compiled_output/lint_report.json` | 收集錯誤與警告來源 |
| | `compiled_output/*.tex`, `compiled_output/references.bib`, `compiled_output/neurips_2024.sty` | 若錯誤指向表格、圖、樣式或引用 |
| **支援檔** | `source_files/abstract.tex`, `source_files/mainbody_post_refined.tex`, `source_files/outlines.json`, `source_files/survey.ini.tex` | 追溯內容與章節結構 |
| **腳本** | `scripts/assemble_latex.py`, `scripts/compile_survey.sh`, `scripts/lint_and_compile.sh` | 理解組裝與編譯邏輯 |

| 類別 | 可寫檔案 | 說明 |
| --- | --- | --- |
| **修改** | `compiled_output/survey.tex`, `compiled_output/*_table.tex`, `compiled_output/figs/*.tex` | 針對 lint/編譯報錯的區段修正 |
| **輸出** | `compiled_output/chktex.out`, `compiled_output/lacheck.out`, `compiled_output/lint_report.json`, `compiled_output/compile.log` | 由 lint + 編譯腳本產生或覆寫 |
| **日誌** | `compiled_output/iteration_<N>_summary.md` 或 `logs/iteration_<N>.md` | 每輪紀錄輸入、修改與結果 |
| **備份** | `compiled_output/survey.backup_<timestamp>.tex` | 快照供回滾 |

禁止讀寫：`survey.pdf`, `survey_wtmk.pdf` 等二進位輸出。

---


## 3. 10-Step Iterative Loop（Sequential-Thinking）

> 以「偵測 → 計畫 → 修復 → 驗證 → 記錄」為核心，每輪最多 10 次。

1. **初始化 (Iteration 0)**  
   - 確認在 `surveyx` conda 環境。  
   - `python scripts/assemble_latex.py`（可選，確保 `survey.tex` 最新）。  
   - `bash scripts/compile_survey.sh`（生成初始 `compile.log`）。

2. **產出診斷資料**  

   ```bash
   bash scripts/lint_and_compile.sh
   ```

   - 確保 `compiled_output/chktex.out`, `lacheck.out`, `compile.log`, `lint_report.json` 均更新。

3. **解析並分類**  
   - 讀 `lint_report.json` 與 `compile.log`：  
     - `Fatal`：`!` 開頭錯誤、Undefined control sequence、Missing }。  

     - `Structural`：環境未結束、圖表引用遺失。  

     - `Bibliography/Reference`：`Warning--I didn't find a database entry…`、`Label multiply defined`。  
     - `Stylistic`：ChkTeX 警告（空白、標點、math mode）。

4. **決定修復優先級**  
   - Fatal > Structural > Bibliography > Stylistic。  

   - 在 `compiled_output/iteration_<N>_summary.md` 中列出目標與來源檔案/行號。

5. **建立備份**  

   ```bash
   cp compiled_output/survey.tex compiled_output/survey.backup_$(date +%Y%m%d_%H%M%S).tex
   ```


6. **套用最小變更**  
   - 只在必要區塊修改，並以註解 `%% fix: <reason>` 標記。  
   - 若涉及表格/figure，維持子檔一致。  
   - 變化較大時拆成多個小 commit/patch。


7. **局部驗證**  
   - 針對修改區段可選擇性地用小型 latex 片段測試（若已抽離）。  
   - 確認未破壞其他引用（搜尋 `\label{`、`\ref{`）。

8. **重新 lint + 編譯**  

   ```bash
   bash scripts/lint_and_compile.sh
   ```

   - 比較新舊 `chktex.out`/`lacheck.out` 差異；  
   - 檢查 `compile.log` 新增/減少的 `!` 或 `Warning`。

9. **記錄結果與回滾判斷**  
   - 更新 `iteration_<N>_summary.md`：列出已修復、仍待修、下輪策略。  
   - 若錯誤變多或變嚴重：立即 `cp survey.backup_* survey.tex` 回滾，紀錄原因。

10. **終止條件**  

      - `latexmk` 成功且 `compile.log` 無 `!` 錯誤。  
      - `chktex`/`lacheck` 僅剩白名單允許的資訊。  
      - 已達 10 輪仍有阻塞 → 升級為人工審查或擴大修改範圍。  
      - 結束時輸出 `compiled_output/iteration_final_summary.md`，列出最終狀態與殘留風險。

---

## 4. 治理、驗證與溝通格式

1. **日誌標準**  
   - 每輪 `iteration_<N>_summary.md` 至少包含：  
     - `Input snapshot`：`${git rev-parse --short HEAD}`、`survey.tex` hash。  
     - `Commands executed`：實際的 lint/compile 指令。  
     - `Fix list`：每個修改段落（檔案、行範圍、原因）。  
     - `Post-check`：`chktex`/`lacheck` 計數與 `grep '^!' compile.log` 結果。  
     - `Next actions / blockers`。

2. **版本控管**  
   - Git 分支命名：`fix/latex-agent-pass-<date>`。  
   - 每輪可 commit：`git commit -am "raptor-mini-fix: iteration N"`。  
   - 若 agent 無權限 commit，至少保留 `survey.backup_*.tex`。

3. **回滾策略**  
   - 嚴格禁止未備份就大規模改動。  
   - 連續兩輪「致命錯誤數 ↑」時強制回滾。

4. **QA Checklist**  
   - `grep '^!' compiled_output/compile.log` → 應為空。  
   - `grep -c "Warning" compiled_output/compile.log` → 僅剩白名單。  
   - `wc -l compiled_output/chktex.out`、`wc -l lacheck.out` → 遞減趨勢。  
   - 如需更嚴謹，可加：`pdftotext survey.pdf - | wc -l`（僅檢查生成成功，不需閱讀 PDF）。

5. **通訊格式（建議）**  
   - 使用 `iteration_<N>_summary.md` 提供 `Findings → Fixes → Tests → Next` 的固定順序，方便後續接到 autogen 流程。

---

## 5. 後續延伸

- **Autogen / Multi-Agent**：當此高階流程穩定後，可由 Orchestrator agent 呼叫：
  1. `lint_and_compile.sh` 取得 JSON 報告；
  2. Planner agent 解析報告與 `survey.tex`；
  3. Worker agent 產生 patch；
  4. Reviewer agent 檢驗並回饋迭代計數。
- **可視化監控**：將 `lint_report.json` 輸入監控儀表（或 PR bot）以追蹤每輪警告量。
- **Rule Customization**：逐步蒐集需要忽略的 ChkTeX 規則，寫入 `scripts/.chktexrc`，保持 lint 訊號穩定。

---

## 6. 快速指令備忘（zsh）

```bash
# 1) 建立 / 切換至工作目錄
cd sandbox/latex_assembly_demo
conda activate surveyx

# 2) 一次完成 lint + 編譯（若已有 helper）
bash scripts/lint_and_compile.sh

# 3) 手動查看輸出
cat compiled_output/chktex.out | head
cat compiled_output/lacheck.out | head
tail -n 120 compiled_output/compile.log

# 4) 備份與回滾
cp compiled_output/survey.tex compiled_output/survey.backup_$(date +%Y%m%d_%H%M%S).tex
cp compiled_output/survey.backup_<timestamp>.tex compiled_output/survey.tex
```

---

藉由上述工具設定、權限邊界與 10-step 迭代流程，就能在不閱讀 PDF 的前提下穩定地修復 `compiled_output/survey.tex`，並為後續導入 Autogen/multi-agent pipeline 打下高層次基礎。
