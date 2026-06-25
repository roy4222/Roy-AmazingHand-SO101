# 10 — Capability Map & Limits（能力地圖 + 極限）

> AmazingHand 右手在**官方框架下**的能力盤點與極限文件。量化欄由實測 telemetry 填（rustypot readback）；**視覺/自然度欄我看不到實體,標 TBD 等 Roy 觀察填入**（不杜撰）。
> 量測日：2026-06-25。工具：`bringup/`。runtime：Pi 5 + Python rustypot。**全程空中、不抓取。**

## 量測方法

每輪入口 `bus_scan` 確認 ID[1-8]。手勢用 `hand_show.py`（`(F,L)` 模型）、左右用 `AH_SWAY`、單指用 `abd_at_flex`/`finger_tour`、全指用 `hand_tour`。每步 readback 位置算 worst tracking error；>8° 標 CHECK、>16° 自動 abort 回安全位。

## T1 Baseline

`responded IDs: [1,2,3,4,5,6,7,8]` ✅ 8 顆在線。

## T2 自創手勢穩定度（custom ×3 輪）

零 abort、高度可重現（3 輪 worst err 變異 ≤0.6°）。

| 手勢 | worst err (max/3輪) | 視覺自然度 |
|---|---|---|
| wave_left | 1.9° | TBD |
| wave_right | 1.9° | TBD |
| fan_spread | 2.5° | TBD |
| fan_pinch | 1.6° | TBD |
| spock | 1.6° | TBD |
| claw | 1.7° | TBD |
| fist | **3.6°**（拇指全握）| TBD |
| point | 0.7° | TBD |
| rock | 1.3° | TBD |
| relax | 1.3° | TBD |

## T3 官方姿勢（我們 (F,L) 參數版）

零 abort。abduction 類（victory/spread/scissors）改用我們模型後 err 低（1.1–1.4°）。

| 手勢 | worst err | 視覺（形狀對不對 / 左右明顯否）|
|---|---|---|
| open | 1.9° | TBD |
| fist | 3.6° | TBD |
| point | 1.0° | TBD |
| midfinger | 3.3° | TBD |
| victory | 1.1° | TBD（伸直→左右受限）|
| spread | 1.4° | TBD |
| clench | 0.9° | TBD |
| perfect | 1.9° | TBD |
| pinch | 1.1° | TBD |
| scissors | 1.3° | TBD |

## T4 左右擺幅 sweep（AH_SWAY 20/35/45/55）

**20 組合全部零 abort**，最大 worst err 3.7°（fan_spread@55）。→ **此範圍內 servo 不卡,左右的「牆」是視覺/幾何,不是堵轉。**

| base | 20 | 35 | 45 | 55 | 備註 |
|---|---|---|---|---|---|
| neutral | 1.5 | 1.9 | 2.2 | 2.6 | err 隨幅度上升=真的在大動 |
| wave_left | 2.3 | 2.9 | 3.2 | 2.4 | 同上 |
| wave_right | 2.0 | 2.6 | 2.4 | 1.8 | |
| fan_spread | 1.7 | 2.1 | 3.3 | 3.7 | 幅度最大組 |
| victory | 1.8 | 1.5 | 1.8 | 1.9 | **err 不隨幅度變→伸直時 abduction 被鎖、沒真的動** |

> 視覺「看得出左右 vs 開始不自然」的界線：**TBD（待 Roy 標每個幅度的觀感）**。

## T5 每指 abduction vs flexion（共模 ±35 @ 伸直/中位/握緊）

4 指在三種彎曲狀態 servo 都精準追到（誤差 <2°）→ **telemetry 層四指一致、即使握緊+左右也不卡**。

| 彎曲狀態 | servo 追蹤 | 可見左右幅度 |
|---|---|---|
| EXTENDED (F=−35) | <2° | TBD（Roy 先前：小）|
| NEUTRAL (F=0) | <2° | **最大（Roy 已確認）** |
| CURLED (F=+45) | <2° | TBD（Roy 先前：小）|

→ 結論:**左右幅度由彎曲狀態決定,非某指機構差。** 要左右明顯,手指留在中位。

## T6 低速 2-DOF tour

| 測試 | worst err | 結果 |
|---|---|---|
| hand_tour 全指同步（up −35/down +90/L±30）| 3.6° | 零 abort |
| finger_tour 食指 | 2.4° | 零 abort |

> 各 2-DOF 組合「視覺漂不漂亮」：TBD。

## T8 離線 IK（官方 MuJoCo + mink,WSL、無硬體）— 2026-06-25

`sim/offline_ik.py` 複用官方模型 + mink QP-IK（閉環 EqualityConstraint + posture + 4 指 orientation FrameTask）,給每指 (flexion, abduction) 解 8 軸 motor 角度。WSL venv `~/ah_sim/.venv`（mujoco 3.10 + mink）。

**IK 驗證並量化了動作模型:**

| 輸入 | IK 解出的 motor | 結論 |
|---|---|---|
| flexion 40° / abd 0 | 兩 motor **反向**（diff +29.7、common≈0）| ✅ 反向=彎曲 |
| abduction 20° / flex 0 | 兩 motor **同向**（common −14.4、diff≈0）| ✅ 同向=左右 |

**abduction → motor 共模 線性映射（sweep 0–20°）:**

| 指尖 abduction | 5° | 10° | 15° | 20°(設計上限) |
|---|---|---|---|---|
| motor 共模 | ~3.5° | ~7° | ~10.6° | **~14.4°** |

→ **1° 指尖 abduction ≈ 0.72° motor 共模;真實 ±20° abduction 只需 motor 共模 ±14°。**

**這解釋了「raw 左右為何不成比例」**:之前 raw 共模硬推到 ±30–55°,但 IK 證明真實 ±20° 上限只要 ±14° 共模——**超過 ~14° 共模就越過幾何上限**,多推不會變更多真實左右,只會耦合/變形。**IK 是乾淨大幅左右的唯一正解,現在能算了。**

**誠實註記(sim→real 未驗)**:motor 角在**模型座標**;IK 給 abd+20 共模為負（index/middle/ring）、thumb 鏡像為正,與 raw 符號不同 → **model→servo 符號/offset 要硬體 gated 校準後才可上真手**。flexion 40° 指尖 ≈ 30° motor（連桿比）。

## T9 sim→real 校準 + IK 軌跡上真手（2026-06-25,硬體 gated,Roy 在場）

單指、中位共模、慢速、空中,由 Roy 肉眼定方向（`finger_abduct.py`）:

| 指 | servo +共模 實際方向 | IK 模型 abd+ 共模符號 | 一致性 |
|---|---|---|---|
| 食指 (1,2) | 右 | 負（→左）| 模型 abd+=左 ✓ |
| 拇指 (7,8) | 右（**幅度極小**）| 正（→右）| 模型 abd+=右 ✓ |

→ 模型在 abd+ 時讓**食指往左、拇指往右**（兩邊張開=正確 spread）。

> ✅ **model→servo 映射 = identity（四指都不用翻符號)**——模型已內建每指(含拇指鏡像)正確符號,實測方向都對。flexion 符號亦早確認((+90,−90)=握)。middle/ring 與食指同構視為相同。
> ⚠️ **拇指 abduction 幅度先天極小**（機械,非符號錯）。

**IK 軌跡實際播到真手**（`hand_pose_player AH_TRAJ=... AH_ALLOW_MODEL=1`,safe preset,telemetry gate):

| 軌跡 | 幅度 | worst err | 溫度 | 結果 |
|---|---|---|---|---|
| `ik_abd_wave`（abd ±20,幾何乾淨上限）| 真實上限 | ≤5.0° | 27°C | ✅ 方向對、左右偏小 |
| `ik_abd_wide`（abd ±28,略過上限)| 堪用上限 | 6.3–7.5°（right frame 爬升）| 27→34°C | ✅ 左右較大,該 frame 較吃力 |

**結論**:**官方 模擬→IK→真手 管線打通**——可在 sim 生成自然動作直接上真手,不必手刻 raw 角度。**左右幅度小是真實幾何極限**（±20° 乾淨;>20° 後 IK 摻入彎曲耦合,index m1/m2 分岔;±28 為堪用上限,再大溫度/誤差上升)。

## 已量化的極限（servo / 控制層）

1. **無堵轉邊界**:flexion 全行程 ±90、abduction 共模到 raw ±55、所有 2-DOF tour——**測試包絡內 servo 完全不卡/不 abort**。真正機械死點在此包絡之外（未刻意去頂）。
2. **追蹤誤差天花板**:最差 ~3.6–3.7°（拇指全握 / fan_spread 最大擺），一般 <2°。
3. **可重現性**:custom 全套 3 輪 worst err 變異 ≤0.6°。
4. **abduction 視覺幅度與彎曲耦合**:量化佐證=err-vs-幅度斜率（中位上升、伸直平坦）。

## 尚未量化的極限（需補工具 / 實體量測）

- **真實可見 abduction 角度（度數）**:需量角器/錄影。`[NEEDS_PHYSICAL_MEASUREMENT]`
- **速度極限**（追蹤誤差爆開的 speed）:需 speed sweep。
- **持續動作熱/load 天花板**:需 telemetry logger（load+temp）長跑。
- **重複精度**（N 次回 pose 誤差分布）:需 cycle 測試。
- **IK 可達 vs raw 可達 abduction**:✅ 已答（見 T8）——真實 ±20° abduction = motor 共模 ±14°,raw 超過 ±14° 共模已過幾何上限。

## 工具狀態（依 grill 計畫）

| 工具 | 狀態 |
|---|---|
| `bringup/hand_pose_player.py`:餘弦插值 + telemetry abort + `safe/natural/snappy` preset | ✅ 完成（safe/natural 實機驗過）|
| telemetry log：`AH_LOG=` 記 cmd/present/err/load/temp/status | ✅ 完成（基線 load ±90–210、temp 25–35°C）|
| `sim/offline_ik.py`:WSL MuJoCo+mink 離線 IK,`--traj/--out/--sweep-abd` 輸出軌跡 CSV | ✅ 完成（sim 驗過）|
| `hand_pose_player` 讀 IK 軌跡 `AH_TRAJ=`（model-frame 需 `AH_ALLOW_MODEL=1` 安全閘）| ✅ 程式完成（Pi DRY RUN 待 Pi 上線補驗）|
| sim→real 符號/offset 校準（單指、小角度、慢速、硬體 gated）| ⏳ 未做（需你在場、開電源）|
| `pose_library.yaml`:官方/社群/custom pose 版本化 | ⏳ 未做 |

> 軌跡格式:CSV `label,m1..m8`（度）,header 標 `frame=model`。IK 輸出為**模型座標**,校準後才可上真手。

> telemetry 能力（已驗證 rustypot `Scs0009PyController`）：position / **load**（扭矩代理,無直接電流）/ **temperature** / voltage / speed / status / 可設 servo 內建過載保護;`sync_read` 可一次讀 8 顆。
