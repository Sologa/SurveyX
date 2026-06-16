# `sandbox/latex_assembly_demo/compiled_output/survey.tex` 錯誤盤點

## 現存錯誤與風險
- **Non-ASCII/Unicode 直接嵌入**：檔案大量使用長破折號、箭頭與變音符號（如 `ASR→LLM→TTS`、`representation–latency–bitrate`、`speech‑AI`），在 `survey.tex:53`, `62`, `66`, `74` 等數百行皆可見。LaTeX 雖預設 UTF-8，但這些字符仍須透過命令 (`\\rightarrow`, `---`, `\\textendash`) 轉義才穩定；與 `latex_fix_module_plan.md` 中「UnicodeFixer」完全一致。
- **`\\label{}` 含空白或逗號**：每個章節與小節沿用自然語言標題作為 label，例如 `\\label{subsec:Why now: From cascaded pipelines to unified end-to-end Speech Language Models}` (`survey.tex:60`)、`\\label{sec:Background and Core Concepts}` (`survey.tex:258`)、`\\label{subsec:From waveform to language model and back: pipeline and terminology}` (`survey.tex:260`)。依 LaTeX2e 手冊 §7.1，label key 應由字母/數字/常見標點組成；空白與逗號會使 `\\ref`/`\\autoref` 解析成 `??`，需要先在本檔修正。
- **`\\autoref` 早於 label 清理**：文件多處使用 `\\autoref`（`survey.tex:240`, `355`, `461`, `515`...），一旦 label 內含空白或含有 `fig:` 之外的特殊符號會無法連結。因此「AutorefNormalizer」在這份檔案中已可以實際發揮作用，而不只是在 `mainbody` 階段假設。
- **大量 `\\input{figs/...}`**：主檔案拉入 15+ 個大型 TikZ/PGF (`survey.tex:59`, `362`, `468`, `520`, `579`, `608`, `647`, `704`, `771`, `897`, `977`, `1164`, `1290`, `1313`, `1375`, `1451`)。這與 sandbox/latex_citation_fix 的 `\\caption@xref` 問題相同：只要其中任一圖過大，`.aux` 就會留下 `\\caption@xref`，必須靠 `CaptionXrefFixer` 將圖外部化或改寫為 `\\includegraphics`。
- **行尾空白/格式 lint**：相同於 `mainbody`, 多數 `\\item` 或段落結尾仍保留空白，例如 `survey.tex:60-74`，呼應 `latex_fix_module_plan.md` 中 LintOrchestrator 所需處理的型態。

## 與 `latex_fix_module_plan.md` 的對照
| 模組 | 在本檔狀態 | 說明 |
|------|------------|------|
| UnicodeFixer | **立即需要** | 超過 300 行包含 `→`, `–`, `‐`, `‑` 等符號。 |
| CaptionXrefFixer | **高度風險** | 16 個 `\\input{figs/...}`，與 sandbox 問題一致；若不外部化就會重現 `\\caption@xref`。 |
| AutorefNormalizer | **已觸發** | 多處 `\\autoref{fig:...}`，而 label 異常將直接導致 `??`。 |
| LintOrchestrator | **需要** | 行尾空白、`\\item` 之後的空行與長 label 必須透過 lint 工具統一。 |
| SafetyNetFixer | **必要** | 由於本檔一旦修圖就需重新 `latexmk`，需有回滾與迭代上限。 |

## 與 `outputs/2025-10-09-1038_speec/tmp/mainbody.tex` 的差異
- `sandbox/latex_assembly_demo/compiled_output/survey.tex` 已嵌入完整 preamble 與所有 figure/表格，而 `mainbody.tex` 僅含純文字。因此這裡已能觀察到 `\\autoref` 和 TikZ 相關錯誤，而 mainbody 只能暴露 Unicode/label 問題。
- 此檔案的 label 仍完全沿用 mainbody 版本，證明在 `LatexFixPipeline` 中應於 mainbody → survey 之間插入正規化，避免圖表與 `\\autoref` 嵌入後再大量修補。
- sandbox 檔案來源於 `latex_assembly_demo`，可作為 `CaptionXrefFixer` 的回歸測試資料：包含多個 `tiny_tree_figure_*`、`tree_figure_Langu` 等已知會觸發 `\\caption@xref` 的圖。

## 建議
1. 先以 Unicode/label 清理器處理 `sandbox/latex_assembly_demo/compiled_output/survey.tex`，並備份原檔以供差異比對。
2. 套用 `CaptionXrefFixer`，對 `tree_figure_Langu`、`tiny_tree_figure_5` 等高風險 TikZ 圖採用 standalone+`\\includegraphics` 策略，並錄製 `.aux` 差異以驗證 `\\newlabel`。
3. 針對 `\\autoref` 加入降級策略（必要時改 `Figure~\\ref{...}`），確保在 label 修正前不會出現 `??`。
4. 利用此檔作為 `LatexFixPipeline` 的整合測試範例（含 `latexmk`、`chktex`、報告輸出）。*** End Patch
