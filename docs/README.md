# docs — Roy-AmazingHand-SO101

Roy fork 的文件集。進場先讀 `00-overview.md`，動作相關看 `03-architecture.md`，最新進度看 `04-run-log/`。

## 索引

| 檔案 | 內容 |
|---|---|
| [`00-overview.md`](00-overview.md) | 專案總覽、目標、動作模型摘要、目前狀態 |
| [`01-setup.md`](01-setup.md) | 環境 / venv / 連線 / 執行方式 |
| [`02-bom.md`](02-bom.md) | 料件 |
| [`03-architecture.md`](03-architecture.md) | 機構、**實測動作模型 `(F,L)`**、控制堆疊、工具架構 |
| [`04-run-log/`](04-run-log/) | 逐日實作紀錄（Evidence 主體）|
| [`05-failure-log.md`](05-failure-log.md) | 失敗 / 卡關 / 誤判更正 |
| [`06-metrics.md`](06-metrics.md) | 實測數據（指回 run-log）|
| [`07-decisions.md`](07-decisions.md) | 輕量 ADR（含動作模型決策）|
| [`08-media-index.md`](08-media-index.md) | 影片 / 大檔索引（不 commit 大檔）|
| [`09-public-notes.md`](09-public-notes.md) | 對外可公開摘要 |
| [`contact.md`](contact.md) | 上游聯絡 |

## run-log

- [`2026-06-24-4finger-servo-bringup.md`](04-run-log/2026-06-24-4finger-servo-bringup.md) — 四指逐根 bring-up（設 ID + flexion 驗證）
- [`2026-06-25-whole-hand-integration-motion-model.md`](04-run-log/2026-06-25-whole-hand-integration-motion-model.md) — 整手整合 + **動作模型實測確認**（左右搖擺 / 前後抓握）+ 自創手勢

## 真相歸屬

- 機構 / 動作模型 → `03-architecture.md`
- 實測數字 → `06-metrics.md`（一律指回 `04-run-log/`）
- 決策 → `07-decisions.md`
- 工具用法 → `bringup/README.md`
- 上游規格（PDF / CAD / license）→ 根 `README.md` 與 `docs/*.pdf`

> 規矩：不杜撰成功 / metrics；未知寫 TBD；不 commit secrets 或大檔；**新手勢一律用 `(F,L)` 自建模型**。
