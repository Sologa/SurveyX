# SurveyX 環境管理與重現指南 (env/README)

> 本文件說明 **SurveyX**（既有 *survey 生成 pipeline*）的環境建立、快照、重建與版本控管策略。此 repo 的環境以 **conda** 為主；任何新功能（如 *paper-selection module*）請以 **獨立 repo + uv/pipx** 管理，並以 **CLI 邊界** 與本 pipeline 對接，避免相依衝突。

---

## 目錄結構（建議）

```
SurveyX/
├─ env/
│  ├─ env-survey.yml              # conda 環境快照（from-history）
│  ├─ requirements-freeze.txt     # pip 快照（如有使用 pip）
│  ├─ conda-explicit.txt          # （可選）conda --explicit 匯出
│  ├─ recreate_env.sh             # 一鍵重建腳本（可自行新增）
│  └─ README.md                   # 本文件
└─ README.md                      # 主 README（可指向 env/README）
```

> **不要**把任何實體環境資料夾（如 `.conda/`, `.mamba/`, `.venv/`）加入版控。

---

## TL;DR（5 行完成環境重建）

```bash
# 1) 建立/重建環境（若你已有 mamba，可將 conda 改為 mamba）
conda env create -n surveyx -f env/env-survey.yml

# 2) 啟用
conda activate surveyx

# 3) （若有）安裝 pip 快照
if [ -f env/requirements-freeze.txt ]; then pip install -r env/requirements-freeze.txt; fi

# 4) 驗證（印出關鍵套件版本）
python - << 'PY'
import sys, importlib
pkgs = ["numpy","pandas","torch","transformers","matplotlib","llama_index","tiktoken"]
for p in pkgs:
    try:
        m = importlib.import_module(p)
        print(f"{p}:", getattr(m, "__version__", "(no __version__)"))
    except Exception as e:
        print(f"{p}: ERROR {e}")
print("python:", sys.version)
PY
```

---

## A. 產生「快照」

在 **已可穩定執行** 的環境中，於 repo 根目錄執行：

```bash
# 只記錄你手動安裝過的 conda 套件（乾淨、不含解決後的所有轉換）
conda env export --from-history > env/env-survey.yml

# （可選）完整可重建通道的顯式列表：
conda list --explicit > env/conda-explicit.txt

# 如 pipeline 內也用到 pip 安裝部分（有才需要）：
pip freeze > env/requirements-freeze.txt
```

**何時更新快照？**
- 你新增/移除/升級了 **conda** 套件 → 重新 `conda env export --from-history`。
- 你新增/移除/升級了 **pip** 套件 → 重新 `pip freeze`。
- **原則**：能用 conda-forge 解決的盡量用 conda；**避免**在同一環境混裝大量 pip。

---

## B. 一鍵重建腳本（可選）

你可以新增 `env/recreate_env.sh`（需 `chmod +x env/recreate_env.sh`）：

```bash
#!/usr/bin/env bash
set -euo pipefail
ENV_NAME=${1:-surveyx}

# 1) 清掉舊環境（若存在）
conda env remove -n "$ENV_NAME" -y >/dev/null 2>&1 || true

# 2) 依 conda 快照重建
conda env create -n "$ENV_NAME" -f env/env-survey.yml

# 3) 啟用並（可選）安裝 pip 快照
# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"
if [ -f env/requirements-freeze.txt ]; then
  pip install -r env/requirements-freeze.txt
fi

# 4) 驗證
python - << 'PY'
import sys
print("python:", sys.version)
PY

echo "Done. Use: conda activate $ENV_NAME"
```

---

## C. Git 版控策略

**應該提交（push）**
- `env/env-survey.yml`：conda 快照
- `env/requirements-freeze.txt`（若有 pip）
- `env/conda-explicit.txt`（可選）
- `env/recreate_env.sh`（若建立了）
- 本文件 `env/README.md`

**不該提交**（請在 `.gitignore`）
```gitignore
# virtual envs / caches
.venv/
.conda/
.mamba/
__pycache__/
*.pyc
pip-wheel-metadata/
build/
dist/
```

---

## D. 平台與通道（channels）建議
- 建議統一使用 **conda-forge**，避免混用預設 `defaults`，可降低求解衝突。
- 需 GPU/CUDA 時，Python/Torch/CUDA 的版本搭配請以專案實測為準；更新快照前先在分支驗證。

`env/env-survey.yml` 範例通道（僅示意）：
```yaml
name: surveyx
channels:
  - conda-forge
dependencies:
  - python=3.11
  # 其餘套件...
```

---

## E. 與「paper-selection module」的關係（強烈建議解耦）

- *paper-selection module* 請放在 **獨立 repo**，使用 **uv** 管套件、**pipx** 發佈 CLI。
- 與本 pipeline 的**對接方式**：**CLI 邊界**（非 import）。也就是在本 pipeline（conda 環境）中用 `subprocess` 呼叫該 CLI，透過 **JSON 檔案** 或 **STDIN/STDOUT** 交換資料。

### 介面契約（建議）
- **輸入 JSON**（候選論文清單）：
  ```json
  [
    {"id":"p1","title":"...","abstract":"...","url":"..."},
    {"id":"p2","title":"...","abstract":"...","url":"..."}
  ]
  ```
- **輸出 JSON**（打分與選取）：
  ```json
  {
    "selected": ["p1","p2"],
    "scores": {"p1":0.91,"p2":0.77},
    "meta": {"top_k": 2, "version": "0.2.1"}
  }
  ```
- **CLI 介面**：
  ```bash
  paper-select --in in.json --out out.json --top-k 50 --config config.yaml
  ```
- **退出碼**：`0=成功`；非 0 視為失敗（pipeline 擷取 stderr 作為錯誤訊息）。

### pipeline 端最小呼叫範例
```python
import json, subprocess, tempfile, pathlib

def run_selector(records, cmd=("paper-select",), top_k=50):
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        inp = td/"in.json"; outp = td/"out.json"
        inp.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run([*cmd, "--in", str(inp), "--out", str(outp), "--top-k", str(top_k)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"paper-select failed: {proc.stderr[:500]}")
        return json.loads(outp.read_text(encoding="utf-8"))
```

> 好處：兩邊依賴樹完全分開，版本升降互不影響；回退只要鎖 CLI 版本（`pipx upgrade` 或 `uv lock`）。

---

## F. 操作守則（Do / Don’t）

**Do**
- ✅ 環境穩定後立即匯出快照並提交：`env/env-survey.yml`（必要）＋ `requirements-freeze.txt`（如有）。
- ✅ 每個重大變更開分支驗證後再更新快照。
- ✅ 優先使用 conda-forge；先用 conda 解決大多數二進位相依，再少量 pip（若必要）。
- ✅ 將 *paper-selection* 等新模組以 CLI 對接，避免把依賴灌入本環境。

**Don’t**
- ❌ 不要在 `base` 環境安裝專案依賴。
- ❌ 不要將 `.venv/`、`.conda/`、`.mamba/` 加入版控。
- ❌ 不要同時大規模混裝 conda 與 pip（特別是 `numpy/torch/transformers`）。

---

## G. 常見問題（FAQ）

**Q1. 我需要在本 repo 內 `conda activate` 嗎？**  
需要。在使用本 pipeline 前，請 `conda activate surveyx`（或你建立的環境名）。

**Q2. 我想在 pipeline 內 `import` paper-selection 可以嗎？**  
不建議。這會重新耦合相依；建議用 CLI 邊界呼叫（見上）。若一定要 import，請以固定版本 wheel `--no-deps` 安裝並評估衝突風險。

**Q3. CUDA/Torch 版本怎麼配？**  
以你的硬體與驅動為準，在分支測試可行組合後再更新 `env-survey.yml`。必要時為 GPU 與 CPU 準備兩份快照。

**Q4. 要不要用 conda-lock？**  
可選。對多平台團隊有幫助；本 repo 先用 `--from-history` + `pip freeze` 即可滿足大多數需求。

---

## H. 維護紀錄（建議保留）

- 2025-09-21：新增本文件；建立快照流程與 CLI 對接建議。
- （之後請在此追蹤每次環境重大變更）

---

## I. 相關連結（內部）

- `env/env-survey.yml`：conda 環境快照
- `env/requirements-freeze.txt`：pip 快照（若有）
- `env/recreate_env.sh`：一鍵重建腳本（若已建立）

