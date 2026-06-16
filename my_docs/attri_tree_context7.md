# Attribute Tree 構建（kit/context7 深度拆解）

## Context7 七層對應
- **Goal/Intent**：為每篇候選論文生成結構化「attribute tree」（方法／基準／理論／綜述專屬欄位），供後續掛載大綱、表格生成與 figure 檢索使用。
- **Surface/API**：主要在 `DataCleaner.get_attri`（`src/modules/preprocessor/data_cleaner.py`）中執行；離線全流程入口 `./run.sh offline ...`，或從 `./run.sh workflow <task_id>` 的清洗階段觸發。
- **Inputs**：  
  - 已裁切的 `paper["md_text"]`（長度上限 `MD_TEXT_LENGTH=20000` tokens）。  
  - `paper["paper_type"]`（由 `get_paper_type` 先行分類）。  
  - 對應提示詞模板 `resources/LLM/prompts/preprocessor/attri_tree_for_<type>.md`。
- **Data/State**：在 `self.papers`（list[dict]）就地填入 `attri` 鍵；持久化至 `outputs/<task_id>/papers/*.json`，並可被 `LatexBaseTableBuilder` 等模組消費。
- **Process/Algorithm**：批量→最多三輪重試；失敗樣本再入隊；解析 JSON 寫回。
- **Control/Config**：`CHAT_AGENT_WORKERS=4` 控制並行；`ChatAgent.batch_remote_chat` 為主，失敗時 `_safe_batch` 降級逐筆；`NonRetryToken`/`RetryToken` 控制重試邏輯。
- **Observability**：`TimeMonitor` 標記「clean paper」；`logger.debug` 記錄 JSON 解析失敗樣本（含截斷片段）。

## 提取流程細節
1. **預處理**：`check_md_text_length` 先用 `cut_text_by_token` 保證每篇 md_text 不超過 20000 tokens，避免超長 prompt。  
2. **類型判定**：`get_paper_type` 將每篇 abstract 套用 `paper_type_classification.md`，輸出 one-of {method, benchmark, theory, survey}；結果存入 `paper["paper_type"]`。  
3. **生成 prompts**：`get_attri` 依 `paper_type` 選擇對應 `attri_tree_for_*.md`，用 `load_prompt(..., paper=paper["md_text"])` 注入全文 Markdown。  
4. **批量呼叫**：每輪收集所有待處理 prompt → `ChatAgent.batch_remote_chat(prompts, desc="getting attribute tree from paper......")`。若整批失敗則降級為逐筆 `remote_chat`。  
5. **重試機制**：最多三輪。若回覆開頭為 `NonRetryToken` 或 `json.loads` 失敗，該樣本保留到下一輪；其餘成功樣本即時寫回。  
6. **寫回結構**：解析出的 dict 直接賦值 `paper["attri"] = {...}`，不做 schema 驗證；最終 `save_papers` 將 title/abstract/md_text/paper_type/attri/bib 等字段落盤。  
7. **下游消費**：  
   - `LatexBaseTableBuilder.cite_name_match*` 用於生成表格／指標，要求 `paper_type=="method"` 或 `benchmark` 且 attri 中的縮寫、資料集 size 等可用。  
   - Outlines 掛載（`mount_paper_on_plain_outline`）將 `attri` 內容作為線索生成 secondary outline。  
   - 後續 figure 檢索器會挑選 attri 中與圖表相關的描述。

## Prompt 中文翻譯（保持鍵名與格式不變）
- **分類 `paper_type_classification.md`**（輸出單字 Method/Benchmark/Theory/Survey）：  
  - 角色：學術論文分類器；根據摘要判斷四種類型。  
  - 輸出格式：僅一個單詞。  
  - 判準：Method=提出新方法；Benchmark=新數據集/評測；Theory=理論洞見或框架；Survey=文獻綜述。

- **Method 類 `attri_tree_for_method.md`**（JSON）：  
  - background: 問題背景（含為何需要突破）。  
  - problem: definition, key obstacle。  
  - idea: intuition, opinion(方法構想), innovation(與既有差異)。  
  - method: name, abbreviation, definition, description(一句話), method steps, principle(為何有效)。  
  - experiments: evaluation setting, evaluation method。  
  - conclusion。  
  - discussion: advantage, limitation, future work。  
  - other info: 其他補充（鍵值或巢狀）。  
  - 輸出格式：僅 JSON，無額外文本。

- **Benchmark 類 `attri_tree_for_benchmark.md`**（JSON）：  
  - background: problem background, purpose of benchmark。  
  - problem: definition, key obstacle。  
  - idea: intuition, opinion, innovation, benchmark abbreviation。  
  - dataset: source, description, content, size(需千分位), domain(單一細分領域), task format(單一主要任務)。  
  - metrics: metric name(1-2 主指標), aspect, principle, procedure。  
  - experiments: model, procedure, result, variability。  
  - conclusion。  
  - discussion: advantage, limitation, future work。  
  - other info。  
  - 輸出格式：僅 JSON。

- **Survey 類 `attri_tree_for_survey.md`**（JSON）：  
  - background: purpose, scope(含排除範圍)。  
  - problem: definition, key obstacle。  
  - architecture: perspective, fields/stages。  
  - conclusion: comparisions, results。  
  - discussion: advantage, limitation, gaps, future work/trends。  
  - other info。  
  - 輸出格式：僅 JSON。

- **Theory 類 `attri_tree_for_theory.md`**（JSON）：  
  - background。  
  - problem: definition, key obstacle。  
  - idea: intuition, opinion, innovation。  
  - Theory: perspective, opinion, proof。  
  - experiments: evaluation setting, evaluation method。  
  - conclusion。  
  - discussion: advantage, limitation, future work。  
  - other info。  
  - 輸出格式：僅 JSON。

> 所有提示詞開頭皆定義角色/背景/技能/目標與 OutputFormat，並要求「ONLY output the json content, WITHOUT ANY OTHER CHARACTER」，確保可直接 `json.loads`。

## 邊界與穩健性
- **長度控制**：若 md_text 超標會被切片，可能導致 attri 缺失；需要下游處理缺欄位情況（目前未做校驗）。  
- **解析失敗**：`json.loads` 失敗僅在 log 中記錄，該篇會在下一輪重試，三輪後仍失敗則 attri 留空。  
- **縮寫約束**：`LatexBaseTableBuilder.cite_name_match*` 會檢查 method/benchmark abbreviation 單詞數與 size 可解析性，否則跳過。  
- **Token 成本**：batch 調用使用 `CHAT_AGENT_WORKERS` 並行，但未對 prompt 自身做摘要，全文注入可能增加費用。

## 可操作建議（不改動程式碼）
- 若要提升成功率：可先用 `./run.sh validate` 確保 Markdown 標題/abstract 完整，再觸發 `offline`。  
- 若 attri 經常為空，可人工檢視 `logger.debug` 片段，對應的 prompt 可在 `resources/LLM/prompts/preprocessor/` 微調後再執行。  
- 下游使用 attri 前建議先做 schema 補齊（如缺少 abbreviation 時回退 method name 首字母組合）。
