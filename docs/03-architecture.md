# 03 — Architecture

> 機構 + 控制堆疊。權威數字來源為 upstream repo（README、`Demo/AHSimulation`），非推論。

## 機構（每指 2 DOF parallel mechanism）

- AmazingHand = **8 DOF / 4 指、每指 2 節**；每指由 **2× SCS0009 並聯驅動**（`README.md:27,39-40`、`Demo/docs/finger.png`：Motor 1 / Motor 2 並排、雙球頭連桿共同帶指尖）。
- 範圍（`Demo/AHSimulation/examples/finger_angle_control.py:34-36`）：
  - **flexion（遠指節）[0°, 140°]** — 主要可用動作。
  - **abduction（左右）[−20°, +20°]** — 設計上就小（指尖 roll）。
  - motors 0° ≈ 遠指節 pitch 121.9°。
- **實測確認的 servo↔動作對應**（`finger_probe.py` + 肉眼，2026-06-25，見 [run-log](04-run-log/2026-06-25-whole-hand-integration-motion-model.md)）：
  - 兩顆 servo **反向**（counter-rotate, +/−，如 close +90/−90）= **flexion（彎曲；前後抓握方向）**。
  - 兩顆 servo **同向**（co-rotate, +/+ 或 −/−，如 +30/+30 ↔ −30/−30）= **abduction（左右）**。**單指共模 ±30～±45 肉眼可見左右**——基本左右**不需 IK**。
- **合成模型（本 repo 自建手勢一律照此，不用上游 raw 角度）**：
  - 每指給 `(F=彎曲, L=左右)` → `servo1 = F + L`、`servo2 = −F + L`（差值 `2F`=flexion、共模 `2L`=abduction）。
  - F：−30（伸直）… +90（全握）。L：單指共模乾淨可到約 ±45。
- **IK 的定位 + 量化映射**（`sim/offline_ik.py` 實測,2026-06-25）：官方 MuJoCo+mink 離線 IK 解出——flexion=motor 反向、abduction=motor 同向（與上一致）,且 **1° 指尖 abduction ≈ 0.72° motor 共模;真實 ±20° abduction = motor 共模 ±14°**。⇒ raw 共模超過 ±14° 已過幾何上限,多推不會變更多真實左右。**幾何正確、大幅 abduction / 表情動作必須走 IK**;raw 共模只適合 ±14° 內基本左右。IK motor 角為**模型座標**（abd 正向時 index/middle/ring 共模為負、thumb 鏡像為正）。**model→servo 映射已硬體校準 = identity（四指不用翻符號）**（2026-06-25,見 [capability-map T9](10-capability-map.md)）→ IK 軌跡可經 `hand_pose_player AH_TRAJ=... AH_ALLOW_MODEL=1` 直接播到真手。拇指 abduction 機械幅度極小。
- 實機 abduction 受列印公差/球頭桿手調/horn/塑膠彈性影響，比理論更小（README disclaimer）。

## Servo / 匯流排

- Feetech SCS0009：TTL serial bus、daisy-chain；標稱 6V、無載 ~150mA、堵轉 ~1.0A/顆；有 torque enable/feedback、位置/電流/溫度回授。
- 右手 ID 對應：`r_finger1`=1,2 / `r_finger2`=3,4 / `r_finger3`=5,6 / `r_finger4`=7,8（`Demo/AHControl/config/r_hand.toml`）。
- 1 條 USB-TTL（CH343）＋ 5V 外部電源驅動全部 8 顆。

## 控制堆疊

- **目前（自建直驅）**：`bringup/` 內的 rustypot 腳本，用 `(F,L)` 合成模型寫 `goal_position`，做設 ID、MiddlePos、flexion 驗證、整手手勢、左右搖擺。
- **IK 路線（離線已跑起來）**：`sim/offline_ik.py` 在 WSL（venv `~/ah_sim/.venv`，mujoco+mink,**無 dora、無硬體**）複用官方 `Demo/AHSimulation` 模型解 IK,輸出 8 軸軌跡 CSV（`frame=model`）。`bringup/hand_pose_player.py` 可用 `AH_TRAJ=` 讀軌跡播放（model-frame 需 `AH_ALLOW_MODEL=1` 安全閘）。官方完整 dora 即時管線（webcam→IK→AHControl）延後。
- 另有 `Demo/AHControl`（Rust）與 `Demo/HandTracking`。

## bring-up / 動作工具架構

`bringup/`（WSL 真相源 → rsync 到 Pi）。共用安全機制：by-id port、`AH_BRINGUP_ARM`/`AH_SET_ID` 防呆、census 閘門、讀回驗證、堵轉自動中止、不死迴圈。

- **底層 / bring-up**：`bus_scan`（唯讀）、`set_id`、`middlepos_set`、`servo_check`。
- **單指動作**：`finger_step`（小角度方向）、`finger_cycle`（全行程開閉）、`finger_abduct`（同向左右）、`finger_tour`（2-DOF 巡禮）、`finger_close_steps`。
- **整手動作**：`hand_gesture`（官方手勢 gated 版）、`hand_tour`（全指 2-DOF）、`hand_sway`/`hand_wag`/`gesture_sway`（左右搖嘗試，部分用官方 raw，**待汰換**）。
- **⭐ 模型工具（本 repo 主力）**：`finger_probe`（動作對應探針）、`hand_show`（自建 `(F,L)` 手勢 + `AH_SWAY` 左右搖）。

> 詳見 `bringup/README.md`。**新手勢一律用 `hand_show` 的 `(F,L)` 模型寫，不要再沿用上游 raw 角度。**
