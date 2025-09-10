# SurveyX 使用與開發 Q&A（彙總）

> 本檔匯總目前討論的重點問題、結論與操作要點；後續問題可續填於文末或拆分為當日檔案並在此連結。

## 1) 現在的程式能否直接生成或下載論文？
- Q: 能否直接生成 survey？能否直接下載論文？
- A:
  - 生成：可以（離線）。前提是你提供本地參考文獻為 `.md`；跑 `tasks/offline_run.py` 會產出 `outputs/<task_id>/survey.pdf`。
  - 下載：不行。開源版未提供線上檢索/下載；`DataFetcher` 多處為佔位且依賴內部服務。
- Refs: `tasks/offline_run.py:66–74`、`src/modules/preprocessor/data_fetcher.py`

## 2) .md 參考文獻要放哪些內容？
- 最少需求：整篇文字內容於 Markdown（做為 `md_text`）。
- 建議格式：
  - 第一行為標題（如 `# Title`），未填會由首行推斷並截斷至 32 字。
  - 需包含可識別的 “Abstract” 段；若找不到會退回取前 2000 字作摘要。
  - 長度：後處理會按 `MD_TEXT_LENGTH=20000` 截斷。
  - 參考文獻 BibTeX：可省略，系統會為每篇自動生成 `references.bib` 條目。
- Refs: `src/modules/preprocessor/data_cleaner.py:46–62, 96–103, 64–95`

## 3) 我有 `.jsonl + PDF`，能直接吃嗎？
- 直接 PDF：不行，需先轉成文字/Markdown。
- `.jsonl`：可以轉為「每篇一檔」的 `.json`，且每筆至少含 `md_text` 欄位，放到 `outputs/<task_id>/jsons/`，再執行清洗與後續步驟。
- 另一條路：把所有 `.md` 放同一資料夾，用 `--ref_path` 走離線流程（最省事）。
- Refs: `src/modules/preprocessor/data_cleaner.py:30–44, 217–234`

## 4) 官方示例包含論文原圖，離線版怎麼辦？
- 開源離線版預設不會自動從引用論文抓原圖。圖檢索依賴外部 API（URL/Tokens 預設為空），且在後處理流程中已關閉呼叫。
- 若需啟用：
  - 需提供可用的 `FIG_RETRIEVE_URL/ENHANCED_FIG_RETRIEVE_URL` 與授權 Token，並確保每篇 paper 有可追溯的圖片來源欄位（如 `image/scholar_id/detail_id/from`）。
  - 解除 `PostRefiner` 中 `FigRetrieveRefiner.run(...)` 的註解，並確保下載與 LaTeX 整合流程可用。
- Refs: `src/modules/fig_retrieve/fig_retriever.py`、`src/models/post_refine/post_refiner.py`、`src/modules/post_refine/fig_retrieve_refiner.py`

## 5) 會呼叫哪些模型？如何改成我的 LLM（如 gpt-5-nano）？
- 會呼叫：
  - LLM：
    - 預處理（類型判定、屬性樹抽取）
    - 大綱（主/次級、去重、重組）
    - 內容生成、摘要、章節銜接
    - 後處理（RAG 重寫、章節重寫、表格與示意圖段落）
  - 嵌入模型：用於 LlamaIndex 檢索（預設 `BAAI/bge-base-en-v1.5`）。
- 切換你的 LLM：
  - 修改 `src/configs/config.py` 中 `REMOTE_URL`、`TOKEN`、`DEFAULT_CHATAGENT_MODEL`、`ADVANCED_CHATAGENT_MODEL` 為你的模型（如 `gpt-5-nano`）。
  - 嵌入：維持 `BAAI/bge-base-en-v1.5` 或改成本地可用模型；必要時設定 `EMBED_REMOTE_URL/EMBED_TOKEN`。
- Refs: `src/configs/config.py`、`src/models/LLM/ChatAgent.py`、`src/models/rag/modeling_llamaidx.py`

## 6) 離線最快上手指令
```bash
python tasks/offline_run.py \
  --title "Your Survey Title" \
  --key_words "kw1, kw2, ..." \
  --ref_path "/path/to/your/md_dir"
```

## 7) 待辦 / 想法
- [ ] 提供 `.jsonl → outputs/<task_id>/jsons/*.json` 轉換腳本（填入 `md_text` 必填欄位）
- [ ] 規劃以 Semantic Scholar / arXiv API 重寫 `DataFetcher`（合規線上檢索→PDF→轉文字→入庫）
- [ ] 視需求啟用圖檢索，補齊 API 與授權
