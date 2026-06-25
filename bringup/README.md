# AmazingHand bring-up & motion tools (right hand)

Roy's own rustypot tooling for the AmazingHand right hand on the Pi 5 — bring-up,
whole-hand gestures, and left/right sway. Upstream `PythonExample/` is left untouched;
these are **our** scripts, built on **our confirmed motion model** (see below).

**WSL is the source of truth.** Edit here, then `rsync` to the Pi at `~/amazinghand/bringup/`.
Do not hand-edit scripts on the Pi.

## Confirmed motion model (2026-06-25, hardware-verified)

Verified with `finger_probe.py` + eyes-on (see `docs/04-run-log/2026-06-25-...md`):

| two servos | motion |
|---|---|
| **counter-rotate** (opposite sign, e.g. `+90/−90`) | **flexion** — curl / grasp direction (前後抓握) |
| **co-rotate** (same sign, e.g. `+30/+30 ↔ −30/−30`) | **abduction** — left/right (左右搖擺) |

Compose any finger pose from `(F, L)`:

```
servo1 = F + L      servo2 = -F + L        # diff 2F = flexion, common 2L = abduction
F: -30 (extended) .. +90 (full curl)       L: ~±45 raw left/right (single finger, clean)
```

**Build all new gestures from this `(F,L)` model (see `hand_show.py`). Do NOT reuse upstream
`PythonExample` raw angles** — they bake abduction into mixed poses and fight the common-mode
sway, which is what limited left/right earlier. IK (`Demo/AHSimulation`) is still the route for
geometrically-correct *large* abduction / tip-roll; basic left/right does **not** need IK.

## Why the port is a `by-id` path

Upstream hardcodes `serial_port="COM11"` (Windows). The AmazingHand USB-TTL adapter is a
**CH343 (`1a86:55d3`), serial `5B42133808`**. We use the stable path:

```
/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00
```

This locks onto **this** adapter and can never address the SO-101 adapters
(serials `5AAF220371` / `5AAF220335`).

## Safety (all motion scripts)

- Motion scripts refuse to move without **`AH_BRINGUP_ARM=1`** (bare run = DRY RUN, reads only).
- `set_id.py` additionally needs `AH_SET_ID=1` and a single-ID-1 census gate.
- `bus_scan.py` is read-only (no guard).
- Every script: census check → readback verify → bind auto-abort (returns to a safe pose) →
  no infinite loop. **To stop: power off the 5V supply.**

## Tools

**Bring-up / low level**
- `bus_scan.py` — read-only scan of IDs 1..8.
- `set_id.py` — `AH_FROM_ID`/`AH_TO_ID`, `AH_SET_ID=1` to write (isolate one ID-1 servo first).
- `middlepos_set.py` — drive to MiddlePos, fit horns at neutral.
- `servo_check.py` — per-servo status readout.

**Single finger** (pick finger via `AH_ID1`/`AH_ID2`: f1=1,2 f2=3,4 f3=5,6 f4=7,8)
- `finger_step.py` — small antagonistic direction check.
- `finger_cycle.py` — bounded full-range open/close (flexion).
- `finger_abduct.py` — same-direction left/right sway (abduction).
- `finger_tour.py` — up/down/left/right 2-DOF tour.
- `finger_probe.py` — ⭐ isolates the two primitives to label flexion vs abduction (the tool
  that confirmed the model).

**Whole hand**
- `hand_gesture.py` — upstream gesture set, gated (`AH_GESTURE=open|close|point|…`). *Uses
  upstream raw angles — kept for reference, being superseded by `hand_show.py`.*
- `hand_tour.py` — all-finger synchronised 2-DOF tour.
- `hand_sway.py` / `hand_wag.py` / `gesture_sway.py` — left/right sway experiments (partly on
  upstream raw angles; **to be retired** in favour of the `(F,L)` model).
- `hand_show.py` — ⭐ **our** custom gestures in the `(F,L)` model + `AH_SWAY` left/right sway.
  `AH_GESTURE=all` runs the set; `AH_GESTURE=<name>` runs one; `AH_GESTURE=<name> AH_SWAY=40`
  holds it and sways left/right.

## Common runs

```bash
# read-only scan (no motion)
ssh pi5 'cd ~/amazinghand/bringup && ~/amazinghand/.venv/bin/python bus_scan.py'

# our custom gestures, all 10 in sequence
ssh pi5 'cd ~/amazinghand/bringup && AH_GESTURE=all AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python hand_show.py'

# victory + left/right sway (our model)
ssh pi5 'cd ~/amazinghand/bringup && AH_GESTURE=victory AH_SWAY=45 AH_SWAYS=6 AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python hand_show.py'

# single finger left/right (abduction), index
ssh pi5 'cd ~/amazinghand/bringup && AH_ID1=1 AH_ID2=2 AH_AMP=45 AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python finger_abduct.py'

# motion-model probe on a finger (DRY RUN without AH_BRINGUP_ARM)
ssh pi5 'cd ~/amazinghand/bringup && AH_ID1=1 AH_ID2=2 AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python finger_probe.py'
```

## Power

SCS0009: nominally 6V (usable ~4–7.4V), ~150 mA no-load, ~1.0 A stall per servo. Whole hand
(8 servos) moving ~1.2 A, worst-case stall much higher — use an **external 5V supply** for the
servos; do **not** power them from the SO-101 7.4V rail (separate supply, common ground with
the USB-TTL only).

## Notes

- ID map: Index=1,2 / Middle=3,4 / Ring=5,6 / Thumb=7,8 (assembly PDF p.24, `r_hand.toml`).
- MiddlePos = 0 for all (horns fitted at neutral); PDF step 5–6 fine-calibration not yet done.
- Author's `r_hand.toml` offsets are **his** hand — do not reuse.
- **Air gestures only — no object grasping** (prehensile grasp not safely validated).
