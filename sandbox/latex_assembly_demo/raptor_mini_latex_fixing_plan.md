# Raptor Mini LaTeX Fixing Plan

本文檔為「由 agent 修復 LaTeX 文件（`compiled_output/survey.tex`）並迭代修正 warnings/errors」的制式化計劃。

語言：繁體中文（zh-tw）

目標：
- 使用 lint 工具（ChkTeX, lacheck）及 LaTeX 編譯器來定位問題（error / warning / lint），
- 指定 agent 能讀與能寫的檔案清單，並定義可重複迭代的工作流（支援最多 10 次迭代或直到問題解決），
- 維持不讓 agent view PDF 的約束（以 compile logs + lint output 作為唯一來源）。

---

## 1. 需要安裝與工具

推薦在 `surveyx` conda 環境或系統中安裝以下工具：

必備：
- TeX (Mac: MacTeX; Linux: texlive-full)
- latexmk, pdflatex, bibtex（用於編譯）
- chktex（LaTeX linter）
- lacheck（古老但仍用的 LaTeX 靜態檢查工具）
- grep/sed/awk 等 shell 命令
- python3（執行 repo 內腳本）

可選（加強）：
- PyMuPDF（if you want to watermark or test PDF features off-line）
- aspell/hunspell（拼字檢查）
- texlab/LaTeX workshop（IDE 支援）

macOS 安裝示例（zsh）：
```bash
# 安裝 MacTeX（包含 latexmk, pdflatex 等）
brew install --cask mactex
# 將 tlmgr 路徑加入，或在首次使用時依照 macOS 說明完成安裝

# 安裝 chktex
brew install chktex

# lacheck 通常包含在 TeX Live；若無
tlmgr install lacheck   # 或利用 brew / apt 查找包

# 驗證
chktex --version
lacheck --version
latexmk --version
```

Ubuntu / Debian 安裝示例：
```bash
sudo apt update
sudo apt install texlive-full chktex lacheck
```

chktex 與 lacheck 的簡要使用：
- ChkTeX（可自訂規則，輸出位置與警告）：
  - 基本執行：
    chktex -q -v0 compiled_output/survey.tex
  - 產生更詳細訊息（包含行數）:
    chktex -n 8 -f error_style.txt compiled_output/survey.tex
  - 用 `.chktexrc` 或 `-p` 來忽略某些規則（若上下文需要）

- lacheck：
  - 執行：
    lacheck compiled_output/survey.tex
  - lacheck 較不敏感，但可找出一些語法錯漏與奇怪命令用法

---

## 2. agent 能讀取與能修改的檔案建議

為避免 agent 無限制查看 PDF，你應把 agent 的 I/O 侷限成以下清單：

- 必須讀：
  - `compiled_output/survey.tex`  ← 主要修復檔
  - `compiled_output/compile.log`  ← latexmk 日誌（錯誤/警告）
  - `compiled_output/references.bib`  ← 參考文獻可能造成錯誤
  - `compiled_output/*.tex`（Summary/表格等） ← 可能的 section 輸出
  - `source_files/survey.ini.tex`、`source_files/outlines.json`、`source_files/abstract.tex` ← 可用來理解 header 與內容
  - `scripts/assemble_latex.py`、`scripts/compile_survey.sh` ← 確認組裝流程與編譯指令
  - `compiled_output/neurips_2024.sty`（如果編譯錯誤跟 style 有關）

- 能夠修改（有限）：
  - `compiled_output/survey.tex`（主要允許）
  - `compiled_output/*_table.tex`（如需要修表格）
  - `compiled_output/figs/*.tex`（如 figures 有 LaTeX 結構性的錯誤）

- 不被允許查看：
  - `survey.pdf` 或 `survey_wtmk.pdf`（不讓 agent 讀 PDF）

- 要額外提供：
  - `compiled_output/compile.log` 的最新版本（每一次編譯，agent 都只能讀新的 log）
  - `scripts/lint_and_compile.sh`（build helper，見下）

> 設計原則：給 agent 充分的文字/日誌+latex 檔案來推理修正，但不要給它二進位格式或影像檢視（避免成本）。

---

## 3. 修復環境：建議加入 CI / Helper 腳本

新增或更新：`scripts/lint_and_compile.sh`
- 功能：先執行 chktex + lacheck，列出警告，再執行 `latexmk`（輸出 compile.log），並把結果解析成便於 agent 消化的 json（`compiled_output/lint_report.json`）。

範例內容（可放於 `scripts/`）：
```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
COMPILED_DIR="$BASE_DIR/compiled_output"
SURVEY_TEX="$COMPILED_DIR/survey.tex"
REPORT_JSON="$COMPILED_DIR/lint_report.json"

# 1. Run chktex and lacheck
chktex -q -f "%f:%l:%c:%k:%n:%m\n" "$SURVEY_TEX" > "$COMPILED_DIR/chktex.out" || true
lacheck "$SURVEY_TEX" > "$COMPILED_DIR/lacheck.out" || true

# 2. Run latexmk and capture compile.log
cd "$COMPILED_DIR"
latexmk -pdf -interaction=nonstopmode -f survey.tex > compile.log 2>&1 || true

# 3. Create a simple json summary for agent
python3 - <<'PY'
import json
from pathlib import Path
base=Path('$COMPILED_DIR')
chk = base/'chktex.out'
lac = base/'lacheck.out'
log = base/'compile.log'
summary = {
  'chktex': chk.read_text() if chk.exists() else '',
  'lacheck': lac.read_text() if lac.exists() else '',
  'compile_log_tail': '\n'.join(log.read_text().splitlines()[-200:]) if log.exists() else ''
}
Path('$REPORT_JSON').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
PY

# 4. Output summary file location
echo "Wrote: $REPORT_JSON"
```

這樣 agent 每次讀取的就是 `compiled_output/lint_report.json`，有利於解析與決策。

---

## 4. agent 修復的安全策略與改動審核

- 每次 agent 提交更動時：
  - 先產生 patch（Git 或 patch 檔）並附上 `reason` 與 `lint` 視覺結果；
  - 人工審核或另一 agent 審核（核准後合併）；
  - 若改動影響 `source_files/` 的內容，需確認這並不是組裝步驟所應做的（通常不建議動 source 文件）。

版本化：對所有 agent 引入的變更，建立 commit 並使用 `COMMIT_MSG` 包含 `raptor-mini-fix: step X`。

---

## 5. 可重複迭代流程（Sequential, up to 10 iterations）

總體策略：可分為「偵測 → 優先分類 → 修正 → 檢查 → 記錄 → 下一輪」

每輪 iteration (1..N up to 10)：

1) 取得 lint report：agent 讀 `compiled_output/lint_report.json` 與 `compile.log`。
    - `chktex` 列出 syntax 與 style 警告（例如：未關閉 brace、空命令、math 環境錯誤）
    - `lacheck` 強調一些壞習慣
    - `compile.log` 提供 LaTeX 真正的 error line 和 warning line

2) 將 issues 分類：
    - A. Fatal errors（會中斷編譯，必須第一輪解決，例如 Undefined control sequence、missing `}`、
    - B. Bibliography / CITATION errors（如 .bib 格式或 \\cite 缺失）
    - C. Style / Lint warnings（可分多輪修復，例如行尾空格、數學顯示問題）
    - D. Duplicate labels / Reference warnings

3) 優先處理 A → B → C → D；把每個修復分成 atomic change（例如：一個 label rename、或是插入 `\protect`）。

4) 修正策略（agent 步驟範例）：
    - 以 `sed` 或小範圍手動修改 `compiled_output/survey.tex`，添加 comment 或修改命令，或在必要時把修正移回 `source_files/`。
    - 修改時把 change 備份 (e.g., `compiled_output/survey.tex.before.1`)。
    - 每次修改後 commit 並提供 `explain`（一行修復原因）

5) 重新跑 `scripts/lint_and_compile.sh`（或手動 run 2 步驟）生成新的 `lint_report.json`。

6) 檢視變化，若解決了 Fatal errors，則繼續修 Bib 證或 syntax；若還有新的 errors，迭代直到 10 次或沒有 errors。

7) 當 compile.log 只剩 warnings（或預設允許的警告白名單），則視為成功並 STOP。建議容忍 `Label multiply defined`（視情況）等非終止性警告，並記錄修復負擔。

---

## 6. agent 行為範本（高階）：

每次 iteration，agent 應：
1. 讀取並解析 `compiled_output/lint_report.json`；
2. 找出最嚴重的 error（compile log 中 `!` 開頭的行）；
3. 在 `survey.tex` 裡找相對的行或環境，並提出一種小修（ex: 增加括號、escape %、將 `\cite` 修成 `\citep` 等，或是註解某段造成問題的表格）；
4. 提交 patch（.patch 或 git commit）並記錄修復原因；
5. 呼叫 `scripts/lint_and_compile.sh` 重新生成 report；
6. 如果修復無效，回退 patch 並嘗試次選方案（比如短路法：註解造成錯誤的大塊內容，確保能成功編譯，再逐步縮小修復範圍）；
7. 跳到下一輪。

---

## 7. 迭代範例—常見問題與建議修法

- "Missing $ inserted": 檢查當前行是否混合了行內數學字元 `#` 或 `…`，或是忘了結束 `$`。
  - Fix: 在相對位置補上 `$` 或把 `\(`…`\)` 改寫。

- Undefined control sequence (eg \somepackagecommand): 確認住 `compiled_output/survey.tex` 前端已經 `usepackage{}`，或把 `\` 改寫；若來自 `source_files`，修 `source_files`。

- references/bibtex: `Warning--I didn't find a database entry for "..."` → 檢查 `.bib` 是否與 `\cite{}` id 匹配。

- Multiply defined label: 在 `compiled_output/` 檔案中尋找重複 `\label{}`，修改或合併引用。

- Lint rule (ChkTeX): 允許某些 style 規則不修（把該警告加入 `.chktexrc` ignore list）或修正樣式。

---

## 8. 逐輪進度報告樣板（agent 應當產生）

每輪完成後輸出 `compiled_output/iteration_N_summary.md`，包含：
- 解析出的 errors 與 warnings
- 已修復項目與變更描述
- 尚未處理的 items
- 下一步建議

---

## 9. 結果驗證

判斷已修復的標準：
1. `latexmk` 產生 `survey.pdf` 且 `compile.log` 不包含 `Error` 字樣（請使用 `grep "^!" compile.log` 追蹤）
2. `chktex` 或 `lacheck` 僅剩下已知且允許的 warnings（可在 `chktexrc` 中註明白名單）

若需要更保守驗證，可在 CI 中跑 `pdfinfo`（檢查 page 數、大小）與 `pdftotext`（檢查是否有損失關鍵句）。

---

## 10. Autogen 與後續（建議）

- 一旦方法穩定：把此流程包成一個 agent pipeline，讓 agent 在 `compiled_output/` 做修復，使用 `lint_and_compile.sh` 來做驗證，再提交 PR。
- Autogen 可以調度 agent 的迭代，每一輪在 agent 修正後，自動 run `scripts/lint_and_compile.sh`，若仍有 Error，則 agent 再嘗試下一策略。

---

## 11. 常見陷阱與提示

- 別把所有修復都直接改 `source_files`，否則下一次 `assemble_latex.py` 會覆蓋你改的 `compiled_output/survey.tex`。
- 建議 agent 先嘗試在 `compiled_output/survey.tex` 做修補；能在 `source_files/` 預修時，應把備註與 reason 一併寫到 commit message。
- 建議對大範圍的 table/figure 做分片註解，確認是那一段造成錯誤再修復，若註解能編譯通過，則 agent 可逐段解除註解以驗會。

---

## 12. 範例指令回顧（在 Mac/zsh）

1. 檢查工具：
```bash
# 偵測工具
chktex --version
lacheck --version
latexmk --version
```
2. 一鍵 lint + compile（由 helper 腳本）：
```bash
bash scripts/lint_and_compile.sh
cat compiled_output/lint_report.json | jq '.chktex'   # 檢視 chktex
cat compiled_output/compile.log | tail -n 200         # 檢視 compile log
```
3. 修復後重試：
```bash
# 例：在 agent 裡修改 compiled_output/survey.tex
git add compiled_output/survey.tex
git commit -m "raptor-mini-fix: correct missing brace on table caption"
bash scripts/lint_and_compile.sh
```

---

## 13. 總結

這份計畫把 agent 的可操作範圍侷限在 `compiled_output/` 下，利用 `chktex`, `lacheck` 與 `latexmk` 的工具鏈作為判讀來源，不讓 agent 讀取 PDF（只有 compile.log 與刪節輸出），並提供一套最多 10 次的逐輪（sequential）迭代流程。該流程適合先作高階修正，後續再結合 `autogen` 框架實作自動化 agent 迭代。

如需我把 `scripts/lint_and_compile.sh` 與 `compile_report.json` 類模組加入 repo，我可以幫你自動創建並測試。