# 2026-06-25 — 整手整合 + 動作模型實測確認（左右搖擺 / 前後抓握）

> 範圍：把昨天逐根 bring-up 完成的右手 4 指 / 8 顆 SCS0009 **裝上手掌板後整手整合**，跑官方手勢、做整手協調動作，並**用硬體探針確認 servo↔動作的真實對應**（這推翻了昨天「abduction 需 IK 才會動」的暫定結論）。
> 全部在 Pi 5 上以 rustypot 直驅。**未抓取實物（全程空中 air gesture）。** 所有數字為實測 readback，非杜撰。工具見 `bringup/`。

## 硬體 / 環境

同 [2026-06-24 run-log](2026-06-24-4finger-servo-bringup.md)：Pi 5（`ssh pi5`）、by-id port `usb-1a86_..._5B42133808-if00`、`~/amazinghand/.venv`、rustypot 1.5.0、baud 1M、AmazingHand 外接 5V。差別：本次 4 指**已上手掌板、8 顆同時上 bus**。

## 1) 8 顆首次同框 + 整手 flexion 重測

- `bus_scan.py`：`responded IDs: [1,2,3,4,5,6,7,8]`，present_pos 全在 ±3.5° 內（四指都歇在 MiddlePos 附近）。**首次 8 顆同時在線。**
- 逐指在整手組裝狀態重測 flexion（`finger_step` 小角度 → `finger_cycle` 全行程 ±90，各 3 cycle）：

| 指 (servo) | 全行程 close (cmd ±90) | open (cmd ∓30) | worst err | 結果 |
|---|---|---|---|---|
| f1 index (1,2) | +89.4 / −89.4 | −30.5 / +29.6 | <1° | ✅ |
| f2 middle (3,4) | +89.4 / −89.1 | −28.4 / +27.8 | ~2.5°（open 側順從性，三次一致）| ✅ |
| f3 ring (5,6) | +88.8 / −89.9 | −28.4 / +29.0 | <1.6° | ✅ |
| f4 thumb (7,8) | +89.4 / −89.4 | −29.6 / +28.7 | <1.3° | ✅ |

四指整手狀態全行程開閉乾淨、零堵轉、無 CHECK、無 abort。

## 2) 官方手勢庫（×2 輪，可重現）

把上游 `PythonExample/AmazingHand_Demo.py` 的手勢搬成 gated 腳本 `hand_gesture.py`（by-id、MiddlePos=0、8 顆全 torque、防呆、讀回、abort 回 open、不死迴圈）。依序跑 `open close point midfing victory spread perfect pinch open`，連跑兩輪：

- 兩輪數據幾乎重疊，worst err 全程 **≤2.5°**，零 abort/堵轉 → 手勢庫**穩定可重現**。
- 純 flexion 手勢（open/close/point/midfing）形狀正確。
- abduction 類官方手勢（victory/spread/perfect/pinch）servo 都追到角度（err ≤2.3°），**但肉眼左右形狀不明顯**——原因見第 4 節（官方角度把 abduction 烤進混合姿態 + raw，不是機構不會動）。

## 3) 整手 2-DOF tour 到設定上限

`finger_tour.py`（單指）/ `hand_tour.py`（全指同步）走 上→下→左→右：

- flexion：up −40 / down +90（真實全行程內），四指與全指同步皆乾淨（worst err ≤2.5°）。
- abduction：推到腳本上限（單指 ±45、全指 ±45 raw），servo 都追到（worst err ≤2.3°），無堵轉。
- **註明**：這是腳本設的上限、非機械死點；四指在此都沒卡，真死點更外面，未刻意去頂（頂死=堵轉拉電流）。

## 4) ⭐ 動作模型實測確認（本日核心發現，更正昨天結論）

**問題**：左右 abduction 一直「看起來沒在動」。昨天 run-log 與 03/05/07 docs 暫定結論是「raw 同向角度幾乎不動、需 IK 才會左右」。今天我一度又重申此結論——**這是錯的**。

**方法**：照 diagnose，停止腦補，做硬體探針 `finger_probe.py`，在 finger1（servo 1,2）上把**兩種純原始動作**隔離、慢速、各做數次，由 Roy 肉眼判定：
- OPPOSITE（兩顆反向 counter-rotate）：`(+30,−30) ↔ (−30,+30)`
- SAME（兩顆同向 co-rotate）：`(+30,+30) ↔ (−30,−30)`

**結果（Roy 實機觀察）**：

| 兩顆 servo | 動作 |
|---|---|
| **反向（counter-rotate, +/−）** | **flexion 彎曲（上下 / 前後抓握方向）** |
| **同向（co-rotate, +/+ 或 −/−）** | **abduction 左右（左右搖擺）** |

- 單指同向 ±30～±45 共模 → **肉眼明顯左右擺**（finger1 確認；err ≤1.9°）。
- 先前「沒感覺」的真因：(a) 全四指一起同向、視覺被洗掉；(b) 我把共模疊在**官方手勢的混合姿態**上、官方又預烤了 abduction，互相打架。**不是機構不會動、也不是非 IK 不可。**

**合成模型（之後所有手勢一律照此自建，丟棄官方 raw 角度）**：

> 每指給 `(F=flexion 彎曲, L=abduction 左右)` → `servo1 = F + L`、`servo2 = −F + L`
> （差值 `2F` = 彎曲、共模 `2L` = 左右）

- F：−30（伸直）… +90（全握）。L：±（單指共模乾淨可到約 ±45）。
- **IK 的角色更正**：IK（`AHSimulation` MuJoCo+mink）仍是「幾何正確、可控指尖 roll 的大幅 abduction」正解；但**基本左右搖擺用 raw 共模就做得出來**，不需要 IK 才會動。

## 5) 自創手勢（10 個，全用我們的模型）

`hand_show.py`（gestures 以 `(F,L)` 定義 → servo）。依序跑 10 個，全乾淨（worst err **≤1.9°**、零 abort）：
`wave_left, wave_right, fan_spread, fan_pinch, spock, claw, curl_left, point_tilt, rock, relax`。
另支援 `AH_SWAY` 對單一手勢加共模左右搖（例：乾淨版 `victory` + 左右搖 ±40～±55 對稱、worst err ≤1.9°）。

## 參數速查（本日定案，詳見 `06-metrics.md`）

- **前後抓握（flexion）**：close/grasp 方向 = 兩顆反向，全行程 cmd ±90 → 實測 +89/−89（err <2°）；open ≈ −30/+30。**僅空中、不抓實物。**
- **左右搖擺（abduction）**：兩顆同向（共模）。單指共模乾淨可到約 ±45；幾何正確大幅 abduction 仍需 IK（真實設計 ±20°）。
- Servo ID：f1=1,2 f2=3,4 f3=5,6 f4=7,8；MiddlePos 全 0（horn 中位）。

## 尚未驗證 / 待辦

1. ~~**IK 路線**尚未跑起來~~ → ✅ **已完成（同日,見 [capability-map T8/T9](../10-capability-map.md)）**:`sim/offline_ik.py` 在 WSL 離線跑官方 MuJoCo+mink,量化映射、生軌跡、3D viewer/mp4;sim→real 校準 = identity;IK 軌跡（abd_wave/abd_wide）已實際播到真手。完整 dora 即時 teleop（webcam）仍延後。
2. **MiddlePos 精校**（目前用預設 0° + 肉眼對中）未做 PDF 第 5–6 步。
3. **不抓取**：prehensile grasp 未安全驗證（需 torque/current feedback + smart control），維持紅線。
4. 把仍用官方 raw 角度的舊工具（`hand_gesture`/`gesture_sway`/`hand_sway`/`hand_wag`）統一改為 `(F,L)` 模型版。

## 新增 / 變更工具（`bringup/`）

- `hand_gesture.py`（官方手勢 gated 版）、`finger_tour.py`、`hand_tour.py`（單/全指 2-DOF tour）
- `hand_sway.py` / `gesture_sway.py` / `hand_wag.py`（左右搖嘗試；**註**：這幾支是過程中的探索，部分基於官方 raw 角度，將汰換）
- `finger_probe.py`（⭐ 動作模型探針——本日關鍵工具）
- `hand_show.py`（⭐ 自創手勢，`(F,L)` 模型，含 `AH_SWAY` 左右搖）
