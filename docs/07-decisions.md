# 07 — Decisions

> 設計 / 選型 / 路線決策紀錄（輕量 ADR）。

## 2026-06-24 — 逐根 bring-up，不一次裝完整手

- 背景：4 指 8 顆 servo，出廠都是 ID 1。
- 決定：一根一根做（設 ID → 機構 → MiddlePos → flexion 驗證 → 下一根），四根都過才上手掌板。
- 理由：避免最後才發現某顆 ID/線/horn 錯而整手拆掉重來。

## 2026-06-24 — serial port 用 by-id 而非 /dev/ttyACM0

- 決定：腳本固定用 `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00`。
- 理由：鎖死此 AmazingHand adapter，插拔後不跳號，且絕不會誤指 SO-101 的 adapter（序號不同）。

## 2026-06-24 — 設 ID 用 rustypot 程式寫，但要物理隔離 + 閘門

- 決定：用 `set_id.py`（解鎖 EEPROM→`write_id`→上鎖→驗證），但每次只接「一顆 ID 1」，並用 DRY RUN census 閘門擋住誤寫。
- 理由：比開 Feetech 工具省事；隔離 + 閘門避免兩顆 ID 1 撞包/同時被寫。

## 2026-06-24 — abduction 留給 IK，不用 raw 角度硬做（**2026-06-25 部分推翻，見下**）

- 背景：左右 abduction 用「兩顆同向 raw 角度」幾乎不動。
- 當時決定：bring-up 階段只驗 flexion；abduction 之後用 `AHSimulation`（MuJoCo + mink IK）做。
- 當時理由：每指為 parallel mechanism，abduction 先天 ±20° 且 servo↔姿態耦合非線性，raw 角度不準。
- **更正（2026-06-25）**：「幾乎不動」是觀察誤判（全指同向視覺被洗掉 + 把共模疊在官方混合姿態上打架）。實測確認**兩顆同向共模就能做出肉眼可見左右**（見下一條與 run-log）。IK 仍是「幾何正確大幅 abduction」正解，但**基本左右不需 IK 才會動**。

## 2026-06-25 — 動作模型實測確認；之後手勢一律自建、丟棄官方 raw 角度

- 背景：左右一直「看似不動」，反覆猜測 servo↔動作對應而出錯。
- 方法：硬體探針 `finger_probe.py` 隔離兩種純動作，Roy 肉眼判定（見 [run-log](04-run-log/2026-06-25-whole-hand-integration-motion-model.md) 第 4 節）。
- 確認：**兩顆反向 = flexion（彎曲/前後抓握）；兩顆同向 = abduction（左右）。**
- 決定：
  1. 採用合成模型 `servo1 = F + L`、`servo2 = −F + L`（F=彎曲、L=左右），所有手勢用此自建。
  2. **不再沿用上游 `PythonExample` 的 raw 角度**——官方角度把 abduction 烤進混合姿態，疊共模會打架、左右受限。
  3. 仍用 IK 做幾何正確的大幅 abduction / 指尖 roll / 表情動作。
- 理由：自建模型左右乾淨、對稱、可開大；官方 raw 角度是這次左右受限的主因。

## 2026-06-24 — 獨立 venv，不污染 LeRobot 環境

- 決定：rustypot 裝在 `~/amazinghand/.venv`，不裝進 SO-101 用的 `~/lerobot/.venv`。
- 理由：AmazingHand 與 SO-101 線分離、相依乾淨。
