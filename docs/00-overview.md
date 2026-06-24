# 00 — Overview

> Roy-AmazingHand-SO101 專案總覽。

## 這是什麼

pollen-robotics **AmazingHand**（開源 3D 列印機器手）的 Roy fork。目標是把右手帶上線、爆改、並與 SO-ARM101 等機器人線整合。AmazingHand = 8 DOF / 4 指、每指 2 節、每指由 2× Feetech SCS0009 以 **parallel mechanism** 驅動（flexion/extension + abduction/adduction），全致動器藏在手內、無外接線。

- upstream：`pollen-robotics/AmazingHand`（見根目錄 `docs/repo-map.md`）。
- 執行機：Raspberry Pi 5（`ssh pi5`），rustypot 直驅 serial bus。

## 目標

- 四指逐根 bring-up（設 ID → 機構 → MiddlePos → flexion 驗證），再整手整合。
- 之後接 inverse kinematics（MuJoCo + mink）做 abduction / 表情動作。
- 與 SO-ARM101 的手臂整合（互動表現力升級件，非夾爪）。

## 非目標 / 範圍邊界

- **不做抓取（prehensile grasp）**：README 明示未安全驗證，需 torque/current feedback + smart control。目前只 air gesture。
- 不與 SO-101 共電（SCS0009 走獨立 5V，SO-101 為 7.4V）。
- 大檔（影片/dataset）只在 `docs/08-media-index.md` 留索引，不 commit。

## 目前狀態（2026-06-24）

四指 8 顆 servo ID 設定完成（1–8）、每指 flexion 全行程單獨驗證通過、零堵轉。**尚未**上手掌板、未測整手、未做 IK abduction、未抓取。詳見 [`04-run-log/2026-06-24-4finger-servo-bringup.md`](04-run-log/2026-06-24-4finger-servo-bringup.md)。
