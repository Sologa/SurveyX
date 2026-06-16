# GPT-5 Chat 系列錯誤分析（context7）

- **現象**：將模型設為 `gpt-5-chat-latest` 或 `gpt-5.2-chat-latest` 時，API 回傳 400（常見訊息：`Unrecognized request argument 'reasoning'`），流程中斷。

- **代碼觀察**
  - `src/configs/config.py:41-67` 將所有以 `gpt-5` 開頭的模型視為 reasoning，統一走 Responses API。
  - `src/models/LLM/ChatAgent.py:128-181` 前綴比對觸發 Responses 路徑，並固定帶上 `temperature=1.0` 及 `reasoning.effort`（預設 `medium`）。

- **規格比對**
  - 標準 **gpt‑5‑chat** 不支援 reasoning 參數；在 Azure/OpenAI 上加入 `reasoning_effort` 會直接回 `400 Unrecognized request argument`。citeturn0search2turn0search8
  - **gpt‑5.1/5.2 系列** 僅在 `reasoning.effort = "none"` 時允許帶一般溫度/隨機性參數；使用 `medium`（本程式預設）會被 API 拒絕。citeturn0search4

- **根因**：前綴規則把所有 `gpt-5*` 誤分類為 reasoning，強制使用 Responses API 並附加 `reasoning.effort`，與 GPT‑5 Chat 系列的允許參數衝突，因此報錯。

- **修復建議（不改現行程式碼時可作為操作指引）**
  1) **收斂允許清單**：將 `REASONING_MODELS` 限縮為確定支援 reasoning 的模型（如 `o4`、`o4-mini`、`o3`、必要時單獨的 `gpt-5` reasoning 變體），並排除 `*-chat-latest`。 
  2) **顯式模型能力表**：改用 dict 描述 `{model: {api: responses|chat, reasoning: true|false}}`，調用前先查能力再決定端點與 payload，避免前綴誤判。 
  3) **臨時繞過（不改碼）**：
     - 若必須用 `gpt-5-chat-latest` / `gpt-5.2-chat-latest`，在呼叫處傳入 `reasoning_effort="none"` 或於環境變數設定 `OPENAI_REASONING_EFFORT=none`，避免 ChatAgent 添附 reasoning 欄位；仍有 400 時，改走 Chat Completions 端點（`REMOTE_URL`）而非 Responses API。 
  4) **回歸驗證**：以 `curl` 向 `/v1/responses` 測試同樣 payload，觀察是否仍出現 `reasoning` 相關 400；再以 Chat Completions 端點對照確認可正常回應。

- **後續建議**：建立自動化健康檢查，對配置中的每個模型執行一次最小請求，將失敗訊息寫入 `outputs/<task_id>/metrics/model_health.json`，避免新模型加入時再次踩到端點/參數不兼容問題。
