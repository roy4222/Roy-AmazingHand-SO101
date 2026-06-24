# 2026-06-24 — 四指 servo bring-up（ID 設定 + per-finger flexion 驗證）

> 範圍：把 AmazingHand **右手 4 指 / 8 顆 SCS0009** 從出廠狀態帶到「每顆 ID 正確、每指 flexion 全行程可動、零堵轉」。
> 在 Raspberry Pi 5 上、透過 rustypot 直接驅動。**未上手掌板、未做整手動作、未抓取。**
> 所有數字為實測 readback，非杜撰。工具見子 repo `bringup/`（WSL 為真相源，rsync 到 Pi `~/amazinghand/bringup/`）。

## 硬體 / 環境

- 執行機：Raspberry Pi 5（`ssh pi5`，走 Tailscale alias）。
- USB-TTL serial bus driver：**CH343（QinHeng `1a86:55d3`），序號 `5B42133808`** → `/dev/ttyACM0`。
  - 程式一律用穩定路徑 `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00`（鎖死此 adapter，避免插拔後編號跳掉，也不會誤指 SO-101 的 adapter）。
- **Bus 身分已確認非 SO-101**：SO-101 兩顆 adapter 序號為 `5AAF220371`(Leader)/`5AAF220335`(Follower)，與本顆 `5B42133808` 不同，且設定期間 SO-101 全程未接。
- Python 環境：`~/amazinghand/.venv`（uv，Python 3.10.20），`rustypot==1.5.0`、`numpy==2.2.6`。
- Serial：baudrate `1000000`。
- 電源：AmazingHand 外接 **5V**，與 SO-101（7.4V）分開、與 USB-TTL 共地。SCS0009 標稱 6V（可用約 4–7.4V）、無載 ~150mA、堵轉 ~1.0A/顆；上游作者以 5V/2A 跑整手 8 顆。

## Servo ID 配置（全部出廠 ID 1 → 用 `set_id.py` 隔離單顆改寫）

| 手指 | Servo ID | 設定方式 | 設定時 present_pos |
|---|---|---|---|
| finger1 / Index | **1, 2** | servo A 原為 ID 1；servo B 寫 1→2 | A 146.5° / B 107.8° |
| finger2 / Middle | **3, 4** | 各自單顆寫 1→3、1→4 | 143.0° / 145.9° |
| finger3 / Ring | **5, 6** | 各自單顆寫 1→5、1→6 | 145.3° / 142.1° |
| finger4 / Thumb | **7, 8** | 各自單顆寫 1→7、1→8 | 145.9° / −146.2° |

對應 `Demo/AHControl/config/r_hand.toml` 與 `AmazingHand_Assembly.pdf` 第 24 頁。

**設 ID 安全程序**（每顆都照做）：物理隔離成 bus 上「恰好一顆 ID 1」→ `bus_scan` 確認 → `set_id.py` DRY RUN 閘門（census 必須 `[1]`）→ `AH_SET_ID=1` 寫入（解鎖 EEPROM → `write_id` → 重新上鎖 → 驗證 `read_id`==新 ID 且舊 ID 消失）→ 獨立 `bus_scan` 複驗。全程**唯讀掃描 / 改 ID，無 servo 位移**。

## Per-finger 驗證（MiddlePos + flexion）

每指：MiddlePos（兩顆 → 0° 中位 hold）→ 裝 horn/機構 → 小角度方向確認（±15/±10）→ 全行程開閉循環（open −30/+30 ↔ close +90/−90）。讀回誤差皆 <2°、無堵轉、無 CHECK。

| 手指 | MiddlePos（before → after） | 全行程 close 實測（cmd ±90） |
|---|---|---|
| finger1 (1,2) | 146.5/107.8 → −0.6/+0.3 | 3× cycle OK；另測 abduction |
| finger2 (3,4) | 143.0/145.9 → 0.0/−0.3 | 小步 +13.5/−14.6 OK |
| finger3 (5,6) | 145.6/142.1 → 0.3/−0.3 | close +88.8/−90.0（3× cycle）|
| finger4 (7,8) | 145.0/−146.2 → 0.0/−0.6 | close +89.4/−90.0（3× cycle）|

## 機構規格（來源：repo，非推論）

- AmazingHand：**8 DOF / 4 指、每指 2 節**；**每指為 parallel mechanism**，2× SCS0009 共同產生 *flexion/extension 與 abduction/adduction*（`README.md:27,39-40`、`Demo/docs/finger.png`）。
- 範圍（`Demo/AHSimulation/examples/finger_angle_control.py:34-36`）：
  - **flexion（遠指節）[0°, 140°]**
  - **abduction（左右）[−20°, +20°]** ← 設計上就小
  - motors 0° ≈ 遠指節 pitch 121.9°
- **servo 角度 → (flexion, abduction) 是耦合非線性**；正確驅動 abduction 要走 **inverse kinematics**（`Demo/AHSimulation` 的 MuJoCo + mink），不是直接灌對稱 raw 角度。
- 驅動慣例（與上游 `PythonExample` 一致）：**兩顆反向**（+/−，如 close +90/−90）= flexion；**兩顆同向** = abduction（但上限 ±20°、且 raw 角度不準）。
- README disclaimer 提醒：實機 abduction 因列印公差/球頭桿手調/horn/塑膠彈性，會比理論更小。

## 過程中的真實狀況（詳見 `05-failure-log.md`）

- `write_lock(id, 0)` → `TypeError: 'int' cannot be cast as 'bool'`：lock 暫存器要 **bool**（`False`=解鎖、`True`=上鎖）。已修，第一次 ID 寫入失敗但 servo 未變更（安全）。
- 兩次 `bus_scan` 掃到 0 顆：皆為 **5V 未開 / 串接線未到底**，補電/重插後恢復。
- finger4 ID 8 MiddlePos readback 一度顯示 −16.4°：是 **146° 大行程未走完就被讀**（settle 2s 太短）的暫態；數秒後實測 −0.6°，非堵轉。已把 settle 拉長到 3.5s。
- 認知修正：先前把「兩顆同向 raw 角度」當大幅 abduction 是**錯的**；abduction 先天 ±20° 且需 IK。

## 尚未驗證 / 待辦（不是毛病，是還沒做）

1. **八顆未曾同時上 bus** —— 全員 `[1–8]` 同框掃描還沒做。
2. **未上手掌板、未測整手協調動作**。
3. **MiddlePos 僅用預設 0°、horn 肉眼對中位** —— 未做 PDF 第 5–6 步 closed-position 精校。
4. **abduction 待 IK 階段**（MuJoCo + mink）。
5. **不抓取** —— README 明示 prehensile grasp 未安全驗證（需 torque/current feedback 與 smart control）。

## 工具（`bringup/`，env 參數化）

- `bus_scan.py`（唯讀）、`set_id.py`（`AH_FROM_ID`/`AH_TO_ID`，`AH_SET_ID=1` 才寫）、`middlepos_set.py`、`finger_step.py`、`finger_close_steps.py`、`finger_cycle.py`、`finger_abduct.py`、`servo_check.py`。
- 選手指：`AH_ID1`/`AH_ID2`（f1=1,2 f2=3,4 f3=5,6 f4=7,8）。動作腳本要加 `AH_BRINGUP_ARM=1` 才會動（否則 DRY RUN）。
- 安全：by-id port 鎖 adapter、`AH_BRINGUP_ARM` 防呆、堵轉自動中止、要停就關 5V。
