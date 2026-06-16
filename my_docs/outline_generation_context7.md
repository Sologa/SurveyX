# SurveyX Outline Generation（kit/context7 深度）

## Context7 對應表
- **Goal/Intent**：產出可直接驅動 content 生成的 `outlines.json`，涵蓋主題、關鍵字與掛載文獻後的層次化章節。參考 `kit/context7` 中強調的「目的優先、結構清晰」原則。 
- **Surface/API**：主要入口 `./run.sh workflow <task_id>`（呼叫 `tasks/workflow/03_gen_outlines.py`），離線一鍵流使用 `./run.sh offline ...` 直到 outline；程式級入口 `src/models/generator/outlines_generator.py:OutlinesGenerator.run`。
- **Inputs**：
  - `outputs/<task_id>/tmp_config.json`（由 `create_tmp_config` 產生的 title/key_words/topic）。
  - `outputs/<task_id>/papers/*.json`（DataCleaner 清洗後的 md_text、attri、bib_name 等）。
  - LLM prompts 位於 `resources/LLM/prompts/outline_generator/`。
- **Data/State**：
  - 中間件：`mount_details_outline.jpg`（掛載統計）、`outlines.json`（最終輸出）。
  - 監控：`TokenMonitor` & `TimeMonitor`（記錄到 `outputs/<task_id>/logs`）。
- **Process/Algorithm**：五步（主線稿 → 掛載 → 次級稿 → 去重 → 重組），下節詳述。
- **Control/Config**：`src/configs/config.py` 中 `ADVANCED_CHATAGENT_MODEL=gpt-5`，`CHAT_AGENT_WORKERS=4`；重試策略由 `tenacity` 控制（主/次級稿 JSON 解析失敗時最多 3/5 次）。
- **Observability & Failure**：`ChatAgent.safe_*` 確保批次失敗不崩潰；主綱失敗時退化為最小 JSON；重組失敗則回退 `plain_outline`。

## Pipeline（outline 前的資料流）
- **tmp_config 建立**：`src/modules/preprocessor/utils.create_tmp_config` 依 title/key_words 生成 task_id，並用 ChatAgent + prompt `generate_keyword.md`/`generate_topic.md` 產出 `key_words` 與 `topic`。
- **PaperRecaller**（`preprocessor/paper_recaller.py`）
  - 先以逗號分隔的初始關鍵字檢索 Google Scholar + arXiv（`DataFetcher`，支援 cache 至 `datasets/raw/papers`）。
  - 對已抓取文獻做 `bge-base` 向量化 → KMeans( k = |keyword_pool|+1 ) → 為每群生成新關鍵詞（prompt `PaperRecall_gen_key_word.md`）→ 以餘弦距離挑最遠的新詞擴充池；迭代上限 `DEFAULT_ITERATION_LIMIT=3`，文獻池上限 `DEFAULT_PAPER_POOL_LIMIT=1024`。
- **PaperFilter**（`preprocessor/paper_filter.py`）
  - 粗粒度：`LlamaIndexWrapper` 以 topic 檢索，取 `COARSE_GRAINED_TOPK=200`。
  - 細粒度：逐篇用 prompt `judge_relevance.md` 判斷（<Answer>1</Answer> 才保留）。
- **DataCleaner**（`preprocessor/data_cleaner.py`）
  - 來源：`outputs/<task_id>/jsons/*.json` 或 `offline_proc` 直接吃 Markdown。
  - 填充欄位：title（首行或 # 標題）、abstract（偵測 "abstract" 字樣或前 2000 字）、bib（`complete_bib` 生成 `references.bib`，並將 `bib_name` 回寫每篇）。
  - LLM 標註：prompt `paper_type_classification.md` → paper_type；依 type 選取對應 `attri_tree_for_*.md` 提取 `attri`（attribute tree）。
  - 長度控制：`MD_TEXT_LENGTH=20000` tokens 內裁切；結果寫入 `outputs/<task_id>/papers/*.json`。

## OutlinesGenerator 核心流程（`src/models/generator/outlines_generator.py`）
1. **建構**：讀入 `tmp_config`（Base），載入 papers，預設輸出 `outputs/<task_id>/outlines.json`。
2. **主綱產生** `gen_outline_sections`
   - prompt：`write_primary_outline.md`，輸入 topic、key_words、最多 60 篇 paper 的 `title/abstract` 摘要。
   - 呼叫 `ChatAgent.safe_remote_chat`（model=`ADVANCED_CHATAGENT_MODEL`，T=0.3）；若 JSON 解析失敗，退化為 `{title: topic, sections: []}`。
   - 將每節附帶 `subsections=[]`，構成 `plain_outline: Outlines`。
3. **文獻掛載**（Mount）
   - 對每篇 `paper['attri']` 生成 prompt `mout_paper_on_plain_outline.md`，批量 `safe_batch_remote_chat`（最多三輪，重試失敗的 prompt）。
   - `_check_response` 確認欄位 `section number`/`information` 才收錄；累計於 `mount_l`，並輸出 `tmp/mount_details_outline.jpg` 直方圖。
4. **次級綱產生**
   - 將 `mount_l` 依 section 號彙整 clue，逐節（除最後 Conclusion）以 prompt `write_secondary_outline.md` 生成 subsections；若 response 非 JSON 或缺欄位則重試（5 次）。
5. **去重**
   - 將所有 subsection 標題串成文本，喂給 prompt `deduplicate_subsection.md`，使用 `_safe_remote`；主要去除同義或重複小節。
6. **重組**
   - prompt `reorganize_outline.md`，輸入 primary + 去重後的 secondary；嘗試 `json.loads` 成 `Outlines`，失敗則回退 `plain_outline`。
7. **輸出與監控**
   - `final_outlines.save_to_file(outlines_save_path)`；`TimeMonitor` 記錄 `generate outline` 開始/結束。

## 重要資料結構與文件
- `Outlines`/`SingleOutline`（`src/schemas/outlines.py`）：提供 `from_dict`, `save_to_file`, `serial_no_to_single_outline`（章節序號轉對象）。
- 中繼產物：
  - `outputs/<task_id>/papers/`：含 `attri`、`paper_type`、`bib_name`。
  - `outputs/<task_id>/tmp/mount_details_outline.jpg`：mount 次數統計。
  - `outputs/<task_id>/outlines.json`：最終大綱。

## 失敗與穩健性
- 主綱/次綱都包 `tenacity` 重試（主 3 次、次 5 次）；`safe_batch_remote_chat` 會以 `__NON_RETRYABLE__` 標記 400/安全性錯誤，後續跳過或重提。
- JSON 解析失敗路徑：
  - 主綱 → 回退空綱。
  - 重組 → 回退 `plain_outline`。
- 掛載回合上限 3，避免壞樣本阻塞。

## 執行建議（僅文件層，未修改程式碼）
- 若只需到 outline：
  - 準備 MD 於 `resources/offline_refs/<topic>/`，先跑 `./run.sh validate ...`。
  - `./run.sh offline "<title>" "<kw_csv>" <md_dir> --only_clean` 可生成 papers 與 bib；接著 `./run.sh workflow <task_id>` 只會從 03 開始。
- 快速驗證：檢查 `outputs/<task_id>/outlines.json` 是否含子節，並確認 `mount_details_outline.jpg` 柱狀圖不全為 0。

## 備註
- 本說明遵循 `kit/context7` 的七層拆解法（目標、介面、輸入、狀態、演算法、控制、觀測），方便後續擴充 content/post-refine 時對齊上下文深度。
