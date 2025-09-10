# Git Helper Scripts

這個資料夾包含 Git 輔助腳本，用於：
1) 建立並維護「舊版穩定線 + 最新開發線」的分支策略。
2) 快速切出功能分支、改名、刪除分支。

## 1) init_branching.sh
- 目的：
  - 將目前提交點標記為舊版基線（包含 `docs/` 的狀態）。
  - 建立長期維護分支（例如 `legacy-stable`）。
  - 確保存在一條開發分支（例如 `main` 或 `develop`）。
  - 選配：推送分支與標籤到遠端。
- 需求：
  - 工作樹乾淨（無未提交/暫存變更）。
  - 在 repo 根目錄執行。
- 使用：
  - 預設（不推遠端）
    ```bash
    bash scripts/git/init_branching.sh
    ```
  - 預設並推送到 `origin`
    ```bash
    bash scripts/git/init_branching.sh --push
    ```
  - 自訂名稱與遠端
    ```bash
    bash scripts/git/init_branching.sh \
      --legacy-branch legacy-v1 \
      --legacy-tag v1.0.0-legacy \
      --dev-branch develop \
      --remote origin \
      --push
    ```
- 預設參數：
  - `--legacy-branch legacy-stable`
  - `--legacy-tag v0.1-legacy-with-docs`
  - `--dev-branch main`
  - `--remote origin`

## 2) new_feature_branch.sh
- 目的：
  - 從指定的開發分支（預設 `main`）切出新的功能分支，例如 `feat/refactor-io-layer`。
  - 選配：建立後直接推送至遠端。
- 需求：
  - 工作樹乾淨（無未提交/暫存變更）。
  - 在 repo 根目錄執行。
- 使用：
  - 從 `main` 切出 `feat/refactor-io-layer` 並推送：
    ```bash
    bash scripts/git/new_feature_branch.sh --name refactor-io-layer --push
    ```
  - 指定來源分支與前綴：
    ```bash
    bash scripts/git/new_feature_branch.sh \
      --name export-cli \
      --from develop \
      --prefix feat \
      --remote origin \
      --push
    ```
- 參數：
  - `--name <feature-name>`（必填）
  - `--from <dev-branch>`（預設：`main`）
  - `--prefix <prefix>`（預設：`feat`）
  - `--remote <remote>`（預設：`origin`）
  - `--push`（可選）

## 3) rename_branch.sh
- 目的：
  - 將某分支改名（包含目前所在分支也可改名），可選擇同步遠端：刪除舊遠端分支、推送新分支並設定追蹤。
- 使用：
  - 改名本地目前分支為 `feat/pdf-ingestion` 並推送：
    ```bash
    bash scripts/git/rename_branch.sh --new feat/pdf-ingestion --push
    ```
  - 指定舊名與新名（不切換當前分支）：
    ```bash
    bash scripts/git/rename_branch.sh --old feat/newest_dev --new feat/pdf-ingestion --push
    ```

## 4) delete_branch.sh
- 目的：
  - 刪除本地與/或遠端分支（安全檢查：不可刪除目前所在分支、需工作樹乾淨）。
- 使用：
  - 同時刪除本地與遠端：
    ```bash
    bash scripts/git/delete_branch.sh --name feat/newest_dev --both
    ```
  - 僅刪本地：
    ```bash
    bash scripts/git/delete_branch.sh --name feat/newest_dev --local
    ```
  - 僅刪遠端（指定遠端）：
    ```bash
    bash scripts/git/delete_branch.sh --name feat/newest_dev --remote-delete --remote origin
    ```

## 建議工作流
- 初始化：執行 `init_branching.sh` 產生 `legacy-stable` 與標籤。
- 開發：於 `main`（或 `develop`）上用 `new_feature_branch.sh` 切出 `feat/*` 分支，完成後開 PR 合回。
- 維護：在 `legacy-stable` 上僅做必要 hotfix，依需要發 `v0.1.x` 等標籤。

> 小提示：腳本不依賴可執行權限，可用 `bash scripts/...` 直接執行；若需改為直接執行可自行 `chmod +x`。
