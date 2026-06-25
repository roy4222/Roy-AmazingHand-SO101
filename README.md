# Roy-AmazingHand-SO101

Roy's fork of **[pollen-robotics/AmazingHand](https://github.com/pollen-robotics/AmazingHand)** —
the open-source 3D-printed 8-DOF / 4-finger robotic hand — brought up on a Raspberry Pi 5 and
extended with our own rustypot tooling, a **hardware-verified motion model**, and a custom
gesture set. Part of the [RoyBot-Lab](https://github.com/roy4222) robot lines (pairs with SO-ARM101
as an expressive hand, **not a gripper**).

> Upstream design © Pollen Robotics. **Licensing preserved (see bottom).** This fork adds
> bring-up evidence, tooling, and docs; it does **not** modify the mechanical design.

---

## What this fork adds

- **Whole-hand bring-up on Pi 5** — 4 fingers / 8× Feetech SCS0009 over rustypot, IDs 1–8,
  per-finger flexion validated, then full-hand integration. Evidence in [`docs/04-run-log/`](docs/04-run-log/).
- **Confirmed motion model** (hardware-verified, not guessed) — see below.
- **Our tooling** in [`bringup/`](bringup/) — gated, readback-verified, bind-aborting scripts for
  scan / set-ID / MiddlePos / single-finger / whole-hand gestures / left-right sway.
- **Custom gesture set** built from our model (`bringup/hand_show.py`).

**Status (2026-06-25):** 8 servos co-existing on the bus, whole-hand flexion re-tested, upstream
gesture library reproducible ×2 rounds, 10 custom gestures + left/right sway validated, zero
binding. **Air gestures only — no object grasping yet.** Full detail:
[`docs/04-run-log/2026-06-25-whole-hand-integration-motion-model.md`](docs/04-run-log/2026-06-25-whole-hand-integration-motion-model.md).

## Motion model (hardware-verified 2026-06-25)

Each finger is a **parallel mechanism**: 2 servos jointly produce flexion *and* abduction.
Verified on hardware with `bringup/finger_probe.py` + eyes-on:

| two servos | motion |
|---|---|
| **counter-rotate** (opposite sign, e.g. `+90/−90`) | **flexion** — curl / grasp direction (前後抓握) |
| **co-rotate** (same sign, e.g. `+30/+30 ↔ −30/−30`) | **abduction** — left/right (左右搖擺) |

Compose any pose per finger from `(F, L)`:

```
servo1 = F + L      servo2 = -F + L         # diff 2F = flexion, common 2L = abduction
F: -30 (extended) .. +90 (full curl)        L: ~±45 raw left/right (single finger, clean)
```

- **All our gestures are built from this `(F,L)` model — we do not reuse upstream `PythonExample`
  raw angles** (they bake abduction into mixed poses and limit clean left/right).
- Basic left/right works with raw common-mode and does **not** need IK. **Geometrically-correct
  large abduction / tip-roll / expressive motion** is the job of IK
  (`Demo/AHSimulation`, MuJoCo + mink) — not yet wired up here.
- ID map: Index = 1,2 / Middle = 3,4 / Ring = 5,6 / Thumb = 7,8. MiddlePos = 0 (horns at neutral).

## Quickstart (our tooling)

Runs on the Pi 5 (`ssh pi5`), Python env `~/amazinghand/.venv` (rustypot 1.5.0, baud 1 M).
**WSL is the source of truth** — edit in `bringup/`, `rsync` to `~/amazinghand/bringup/`.
Motion needs `AH_BRINGUP_ARM=1` (bare run = DRY RUN). **To stop: power off the 5 V supply.**

```bash
# read-only bus scan (no motion)
ssh pi5 'cd ~/amazinghand/bringup && ~/amazinghand/.venv/bin/python bus_scan.py'

# our 10 custom gestures in sequence
ssh pi5 'cd ~/amazinghand/bringup && AH_GESTURE=all AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python hand_show.py'

# victory + left/right sway (our model)
ssh pi5 'cd ~/amazinghand/bringup && AH_GESTURE=victory AH_SWAY=45 AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python hand_show.py'
```

Full tool list, safety, and runs: [`bringup/README.md`](bringup/README.md).

## Docs

Entry order: [`docs/00-overview.md`](docs/00-overview.md) →
[`docs/03-architecture.md`](docs/03-architecture.md) (mechanism + motion model) →
[`docs/04-run-log/`](docs/04-run-log/) (evidence). Index: [`docs/README.md`](docs/README.md).
Hard rules (no fabricated success, unknown = TBD, no secrets, no large files): [`AGENTS.md`](AGENTS.md).

## Hardware / power

- USB-TTL: CH343 (`1a86:55d3`, serial `5B42133808`), addressed by stable by-id path so it can
  never hit the SO-101 adapters.
- Power: **external 5 V (≥2 A)** for the servos — **not** the SO-101 7.4 V rail; common ground
  with the USB-TTL only. SCS0009 ≈ 6 V nominal, ~150 mA no-load, ~1 A stall per servo.

---

## Upstream build resources

This fork does not change the mechanical design — build from upstream:

- **BOM / 3D-printed parts** — see upstream [AmazingHand BOM](https://docs.google.com/spreadsheets/d/1QH2ePseqXjAhkWdS9oBYAcHPrxaxkSRCgM_kOK0m52E/edit?gid=1269903342#gid=1269903342)
  and [3D Printing Guide](docs/AmazingHand_3DprintingTips.pdf).
- **CAD / Onshape / Assembly** — [`docs/AmazingHand_Assembly.pdf`](docs/AmazingHand_Assembly.pdf),
  [`docs/AmazingHand_Overview.pdf`](docs/AmazingHand_Overview.pdf), and upstream [cad/](https://github.com/pollen-robotics/AmazingHand/tree/main/cad).
- **Kits** — [Seeed Studio](https://www.seeedstudio.com/Amazing-Hand-Right-Hand-The-Open-Source-Robotic-Hand-Developer-Kit.html) ·
  [WowRobo](https://shop.wowrobo.com/products/amazing-hand-the-open-source-robotic-hand-kit).
- **Upstream demos / IK** — `PythonExample/`, `ArduinoExample/`, `Demo/` (AHControl, AHSimulation, HandTracking).

## Disclaimer (from upstream, still applies)

Real-life flexion/abduction angles vary from theory (3D-print tolerance, hand-adjusted ball-joint
rods, servo-horn rework, plastic flex). The design is **not** validated for long/complex
prehensile tasks — grasping objects safely needs smart control using the servos' torque/current
feedback. **We keep to air gestures.**

## Credits & License

Upstream **AmazingHand** by [Pollen Robotics](https://github.com/pollen-robotics/AmazingHand) —
huge thanks to [Steve N'Guyen](https://github.com/SteveNguyen) (rustypot Feetech, MuJoCo/Mink,
hand-tracking), [Pierre Rouanet](https://github.com/pierre-rouanet) (pypot Feetech),
Augustin Crampette & Matthieu Lapeyre.

- Code: [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- Mechanical design: [Creative Commons Attribution 4.0 International (CC BY 4.0)][cc-by]

[![CC BY 4.0][cc-by-shield]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY-lightgrey.svg
