# 05 — Failure Log

> 失敗、卡關、blocker 逐筆紀錄。只記真實發生的事，不杜撰。

| 日期 | 現象 | 推測原因 | 處置 | 狀態 |
|------|------|----------|------|------|
| 2026-06-24 | 第一次 ID 寫入丟例外、servo 未變更 | `write_lock(id, 0)` → `TypeError: 'int' cannot be cast as 'bool'`；lock 暫存器要 bool | 改成 `write_lock(id, False/True)`，重跑寫入成功；servo 全程未誤改（census + 重試安全） | 已解 |
| 2026-06-24 | `bus_scan` 掃到 0 顆（2 次：finger2、finger4 合掃時） | 5V 未開 / 串接線未到底（port 有開，只是每個 ID timeout） | 補電 / 重插串接線後恢復，掃到預期 ID | 已解 |
| 2026-06-24 | finger4 ID 8 MiddlePos readback 顯示 −16.4°（目標 0°） | 146° 大行程未走完就被讀（settle 2s 太短）的暫態，非堵轉 | 數秒後實測 −0.6°；把 middlepos_set settle 拉長到 3.5s | 已解（誤判） |
| 2026-06-24 | abduction（左右）幾乎不動，一度疑似故障 | 認知錯誤：誤以為「兩顆同向 raw 角度」能大幅 abduct。實為設計 ±20° 上限 + 需 IK，raw 角度不準 | 查 repo 規格確認屬正常；abduction 改列 IK 階段 | 已解（非故障） |
