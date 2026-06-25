# 00 — Overview

> Roy-AmazingHand-SO101 專案總覽。

## 這是什麼

pollen-robotics **AmazingHand**（開源 3D 列印機器手）的 Roy fork。目標是把右手帶上線、爆改、並與 SO-ARM101 等機器人線整合。AmazingHand = 8 DOF / 4 指、每指 2 節、每指由 2× Feetech SCS0009 以 **parallel mechanism** 驅動（flexion/extension + abduction/adduction），全致動器藏在手內、無外接線。

- upstream：`pollen-robotics/AmazingHand`（見根目錄 `docs/repo-map.md`）。
- 執行機：Raspberry Pi 5（`ssh pi5`），rustypot 直驅 serial bus。

## 目標

- 四指逐根 bring-up（設 ID → 機構 → MiddlePos → flexion 驗證），再整手整合。✅
- 用自建 `(F,L)` 動作模型做整手手勢 + 左右搖擺。✅
- 之後接 inverse kinematics（MuJoCo + mink）做幾何正確大幅 abduction / 表情動作。
- 與 SO-ARM101 的手臂整合（互動表現力升級件，非夾爪）。

## 動作模型（實測確認，2026-06-25）

- 兩顆 servo **反向** = **flexion（彎曲；前後抓握方向）**；兩顆 **同向** = **abduction（左右搖擺）**。
- 合成：每指 `(F=彎曲, L=左右)` → `servo1 = F+L`、`servo2 = −F+L`。
- **本 repo 手勢一律用此自建模型，不沿用上游 `PythonExample` 的 raw 角度。** 詳見 [`03-architecture.md`](03-architecture.md)。

## 非目標 / 範圍邊界

- **不做抓取（prehensile grasp）**：README 明示未安全驗證，需 torque/current feedback + smart control。目前只 air gesture。
- 不與 SO-101 共電（SCS0009 走獨立 5V，SO-101 為 7.4V）。
- 大檔（影片/dataset）只在 `docs/08-media-index.md` 留索引，不 commit。

## 目前狀態（2026-06-25）

四指已上手掌板、8 顆同框 `[1-8]`、整手 flexion 重測通過、官方手勢庫 ×2 輪可重現、10 個自創手勢（`(F,L)` 模型）+ 左右搖擺全部驗證通過、零堵轉。**動作對應已實測確認**（更正了昨天「左右需 IK」的暫定結論）。**尚未**做 IK 路線、未 MiddlePos 精校、未抓取。詳見 [`04-run-log/2026-06-25-whole-hand-integration-motion-model.md`](04-run-log/2026-06-25-whole-hand-integration-motion-model.md)。
