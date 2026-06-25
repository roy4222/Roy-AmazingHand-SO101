# 06 — Metrics

> 量測數據。只記實際量到的數字，不杜撰；來源指回 `docs/04-run-log/`。

| 日期 | 指標 | 數值 | 條件 | run-log 來源 |
|------|------|------|------|--------------|
| 2026-06-24 | 各指 servo 追蹤誤差（flexion 全行程） | <2° | rustypot 直驅, baud 1M, speed 5, cmd ±90 對抗 | [2026-06-24-4finger-servo-bringup](04-run-log/2026-06-24-4finger-servo-bringup.md) |
| 2026-06-24 | finger4 close 實測（cmd +90/−90） | +89.4° / −90.0° | 3× open/close cycle, 零堵轉 | 同上 |
| 2026-06-24 | finger3 close 實測（cmd +90/−90） | +88.8° / −90.0° | 3× cycle | 同上 |
| 2026-06-24 | MiddlePos 收斂（各指 → 0°） | ≤1.5° 誤差 | settle 後 readback | 同上 |
| 2026-06-24 | flexion 設計範圍 | 0°–140° | repo 規格（非實測） | 同上 |
| 2026-06-24 | abduction 設計範圍 | −20°–+20° | repo 規格（非實測；幾何正確大幅 abduction 仍待 IK） | 同上 |
| 2026-06-25 | 8 顆首次同框 | `[1,2,3,4,5,6,7,8]` | 上手掌板後 `bus_scan`，唯讀 | [2026-06-25-whole-hand-integration-motion-model](04-run-log/2026-06-25-whole-hand-integration-motion-model.md) |
| 2026-06-25 | 整手 4 指 flexion 追蹤誤差 | <2.5° | 整手組裝, 全行程 ±90, 3× cycle | 同上 |
| 2026-06-25 | 官方手勢庫追蹤誤差（×2 輪） | ≤2.5° | 8 手勢依序, 可重現 | 同上 |
| 2026-06-25 | 自創手勢追蹤誤差（10 個, `(F,L)` 模型） | ≤1.9° | `hand_show.py`, speed 4 | 同上 |
| 2026-06-25 | 單指左右（abduction 共模）乾淨幅度 | ±45（finger1 肉眼可見） | 兩顆同向 ±45, 6 sway, 零堵轉 | 同上 |
| 2026-06-25 | 動作對應（實測確認） | 反向=flexion；同向=abduction | `finger_probe.py` + Roy 肉眼判定 | 同上 |
| 2026-06-25 | IK abduction→motor 共模映射 | 1° abd ≈ 0.72° 共模；±20°=±14° | `sim/offline_ik.py` MuJoCo+mink sweep | 同上 |
| 2026-06-25 | sim→real 映射 | identity（四指不用翻符號）| 單指 finger_abduct + Roy 肉眼 | 同上 |
| 2026-06-25 | IK 軌跡上真手追蹤誤差 | abd_wave ≤5.0° / abd_wide ≤7.5° | `hand_pose_player AH_TRAJ`, safe preset | 同上 |
