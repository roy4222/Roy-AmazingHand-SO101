# 06 — Metrics

> 量測數據。只記實際量到的數字，不杜撰；來源指回 `docs/04-run-log/`。

| 日期 | 指標 | 數值 | 條件 | run-log 來源 |
|------|------|------|------|--------------|
| 2026-06-24 | 各指 servo 追蹤誤差（flexion 全行程） | <2° | rustypot 直驅, baud 1M, speed 5, cmd ±90 對抗 | [2026-06-24-4finger-servo-bringup](04-run-log/2026-06-24-4finger-servo-bringup.md) |
| 2026-06-24 | finger4 close 實測（cmd +90/−90） | +89.4° / −90.0° | 3× open/close cycle, 零堵轉 | 同上 |
| 2026-06-24 | finger3 close 實測（cmd +90/−90） | +88.8° / −90.0° | 3× cycle | 同上 |
| 2026-06-24 | MiddlePos 收斂（各指 → 0°） | ≤1.5° 誤差 | settle 後 readback | 同上 |
| 2026-06-24 | flexion 設計範圍 | 0°–140° | repo 規格（非實測） | 同上 |
| 2026-06-24 | abduction 設計範圍 | −20°–+20° | repo 規格（非實測；待 IK 實測） | 同上 |
