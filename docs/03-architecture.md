# 03 — Architecture

> 機構 + 控制堆疊。權威數字來源為 upstream repo（README、`Demo/AHSimulation`），非推論。

## 機構（每指 2 DOF parallel mechanism）

- AmazingHand = **8 DOF / 4 指、每指 2 節**；每指由 **2× SCS0009 並聯驅動**（`README.md:27,39-40`、`Demo/docs/finger.png`：Motor 1 / Motor 2 並排、雙球頭連桿共同帶指尖）。
- 範圍（`Demo/AHSimulation/examples/finger_angle_control.py:34-36`）：
  - **flexion（遠指節）[0°, 140°]** — 主要可用動作。
  - **abduction（左右）[−20°, +20°]** — 設計上就小。
  - motors 0° ≈ 遠指節 pitch 121.9°。
- **servo 角度 ↔ (flexion, abduction) 為耦合非線性。**
  - 驅動慣例（同上游 `PythonExample`）：兩顆**反向**（+/−，close +90/−90）= flexion；兩顆**同向** = abduction。
  - 但 abduction 用 raw 同向角度**不準**；正解是 inverse kinematics。
- 實機 abduction 受列印公差/球頭桿手調/horn/塑膠彈性影響，比理論更小（README disclaimer）。

## Servo / 匯流排

- Feetech SCS0009：TTL serial bus、daisy-chain；標稱 6V、無載 ~150mA、堵轉 ~1.0A/顆；有 torque enable/feedback、位置/電流/溫度回授。
- 右手 ID 對應：`r_finger1`=1,2 / `r_finger2`=3,4 / `r_finger3`=5,6 / `r_finger4`=7,8（`Demo/AHControl/config/r_hand.toml`）。
- 1 條 USB-TTL（CH343）＋ 5V 外部電源驅動全部 8 顆。

## 控制堆疊

- **目前（bring-up）**：`bringup/` 內的 rustypot 腳本，直接寫 `goal_position`（raw servo 角度），用於設 ID、MiddlePos、per-finger flexion 驗證。
- **之後（正式）**：`Demo/AHSimulation`（MuJoCo 模型 + mink IK）+ dora-rs —— 給「指尖朝向」反解 motor 角度，才能正確做 abduction 與表情/追蹤動作（`Demo/README.md`、`AHSimulation/README.md`）。
- 另有 `Demo/AHControl`（Rust）與 `Demo/HandTracking`。

## bring-up 工具架構

`bringup/`（WSL 真相源 → rsync 到 Pi）：`bus_scan` / `set_id` / `middlepos_set` / `finger_step` / `finger_close_steps` / `finger_cycle` / `finger_abduct` / `servo_check`。共用安全機制：by-id port、`AH_BRINGUP_ARM`/`AH_SET_ID` 防呆、census 閘門、堵轉自動中止。
