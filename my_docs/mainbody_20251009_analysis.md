# `outputs/2025-10-09-1038_speec/tmp/mainbody.tex` 錯誤盤點

## 現存錯誤 (尚未進入 `survey.tex` 前就存在)
- **非 ASCII 符號**：大量段落直接使用長破折號 `—`、en dash `–` 與其他 Unicode 符號（例如 `systems—encompassing`、`tokens–to-SLM`），例如 `outputs/2025-10-09-1038_speec/tmp/mainbody.tex:15`, `35`, `61`, `69` 等多處。未轉義的非 ASCII 會在 `pdflatex` 中導致 `! Package inputenc Error`，正是 `latex_fix_module_plan.md` 中「UnicodeFixer」要處理的來源。
- **`label` 名稱含空格、逗號與句點**：所有章節/小節都繼承自然語言標題作為 `\label`，例如 `\label{subsec:1.1 Motivation and guiding questions}` (`mainbody.tex:5`)、`\label{sec:Background and Definitions}` (`mainbody.tex:127`)、`\label{sec:Encoders, Vocoders and Speech Synthesis}` (`mainbody.tex:555`) 以及 `\label{subsec:7.3 Task-specific evaluation across ASR, TTS, S2S, and multimodal tasks}` (`mainbody.tex:965`). LaTeX 不允許 `\label{...}` 中含空格或逗號，會在 `\ref`/`\autoref` 時直接回傳 `??`。這些錯誤會在後續 `survey.tex` 組裝時立即顯現。
- **段落行末多餘空白**：同一批 `\item` 行（例如 `mainbody.tex:15`, `21`, `35`）與許多段落在句尾留有空白字元，`chktex` 會將其視為 lint 警告。雖非致命，但「LintOrchestrator」應在自動化流程中清理以避免噪音。

## 與 `my_docs/latex_fix_module_plan.md` 中錯誤清單的對照
- `UnicodeFixer`：**已在 mainbody 出現**。大量 `—/–` 等非 ASCII 已在 raw 內容中，需要在進入 `survey.tex` 前就轉為 `---`、`--` 或對應的 LaTeX 指令。
- `CaptionXrefFixer`：**尚未觸發**。`mainbody.tex` 只包含文字，沒有 `\input{figs/...}` 或 TikZ 區塊，所以還看不到 `\caption@xref`。問題只有在 `survey.tex` 注入 `\input{figs/structure_fig}`、`figs/tree_figure_Model`（`outputs/2025-10-09-1038_speec/latex/survey.tex:59`, `485`）之後才會出現。
- `AutorefNormalizer`：**尚未觸發**。`mainbody.tex` 沒有 `\autoref{...}`，真正的 `\autoref` 只在 `survey.tex` 的引言結尾與模型章節（例如 `survey.tex:102`, `484`）才出現，因此 mainbody 無法直接暴露這個錯誤來源。
- `LintOrchestrator`：**部分命中**。雖然 `chktex` 尚未執行，但 mainbody 已含有「label 中的空格/逗號」「行尾空白」等 lint 問題，證明在 plan 中加入 lint 階段是必要的。
- `SafetyNet/其他編譯錯誤`：`mainbody.tex` 本身尚未引入 `\bibliography`、`tikz`、`\input`，因此只會產生較輕微的語法錯誤（label 命名），較重的 `latexmk` 失敗需要等 `survey.tex` 組裝後才會浮現。

## `mainbody.tex` 與 `survey.tex` 的主要差異
- **版面與前置作業**：`survey.tex` 有完整 preamble、`\title`、`\author`、`\begin{abstract}` 等結構（`outputs/2025-10-09-1038_speec/latex/survey.tex:1-52`），而 `mainbody.tex` 只包含章節內容。這表示 mainbody 的錯誤若不先處理，會在完整模板中放大。
- **圖表與引用**：`survey.tex` 會插入 `\input{figs/structure_fig}` 與 `\input{figs/tree_figure_Model}`（`survey.tex:59`, `485`），並在正文中新增 `\autoref{fig:chapter_structure}`、`\autoref{fig:tree_figure_Model}`（`survey.tex:102`, `484`）。這些元素在 mainbody 完全不存在，因此 `\caption@xref`／`autoref` 錯誤僅在整合步驟出現。
- **label 仍沿用 mainbody**：`survey.tex` 直接把 mainbody 中的章節與 label 嵌入，例`survey.tex:74` 仍含 `\subsection{1.1 …} \label{subsec:1.1 Motivation and guiding questions}`。因此若不先在 mainbody 階段修正 label，最終 PDF 也會持續顯示 `??`。
- **抽象與附加段落**：`survey.tex` 的引言在 `\section{Introduction}` 前新增 `Guiding questions` 合併段，並繼續沿用 mainbody 的段落內容；因此 mainbody 可視為 `survey.tex` 的正文來源，但不含任何模板或後處理。

## 結論
`mainbody.tex` 雖未包含 TikZ/figure，但已帶有兩類會立即破壞 LaTeX 編譯的問題：非 ASCII 字元與非法的 `\label` 命名。`latex_fix_module_plan.md` 中規劃的 Unicode 與 lint 階段因此需要在 mainbody 產生後就介入；而 CaptionXref 與 Autoref 的修復則必須等 `survey.tex` 注入圖表後才會重現。上述分析已寫入 `SurveyX/my_docs/mainbody_20251009_analysis.md` 供後續開發參考。***
