# AmazingHand bring-up (finger1 / right hand)

Local bring-up copies for calibrating the **first finger** (`r_finger1`, servo ID **1,2**)
on Roy's Pi 5. Upstream `PythonExample/` is left untouched; these are the copies we run.

**WSL is the source of truth.** Edit here, then `rsync` to the Pi at `~/amazinghand/bringup/`.
Do not hand-edit long scripts on the Pi.

## Why the port is a `by-id` path

Upstream hardcodes `serial_port="COM11"` (Windows). On the Pi the AmazingHand USB-TTL
adapter is a **CH343 (`1a86:55d3`), serial `5B42133808`**, which enumerates as
`/dev/ttyACM0`. We use the stable path instead:

```
/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00
```

This locks onto **this** adapter and can never accidentally address the SO-101 adapters
(serials `5AAF220371` / `5AAF220335`), even if they are plugged back in later.

## Safety guard

`AmazingHand_Hand_FingerMiddlePos.py` and `AmazingHand_FingerTest.py` will **not open the
bus, enable torque, or move** unless `AH_BRINGUP_ARM=1` is set. A bare run just prints a
refusal and exits. `bus_scan.py` has no guard because it is **read-only** (never writes).

## Order of operations

1. **`bus_scan.py`** — read-only. Confirm only ID 1,2 answer on the bus. *(No motion.)*
2. Set servo IDs with the Feetech FD tool if needed (factory default is ID 1; finger1
   needs one servo at ID 1 and one at ID 2). Per assembly PDF: Index=1,2 / Middle=3,4 /
   Ring=5,6 / Thumb=7,8.
3. **`AmazingHand_Hand_FingerMiddlePos.py`** (`AH_BRINGUP_ARM=1`) — drive to MiddlePos,
   fit the horns at neutral, tune `MiddlePos_1/2` (degrees) until the finger sits at the
   real mechanical middle. *Moves servos — Roy must approve first.*
4. **`AmazingHand_FingerTest.py`** (`AH_BRINGUP_ARM=1`) — open/close cycle to verify the
   calibrated middle. Air movement only, no objects. *Gated behind step 3 + approval.*
5. Record the calibrated `MiddlePos_1/2` (each finger has its own) in the child repo
   `docs/04-run-log/`.

## Power

SCS0009 is nominally 6V (usable ~4–7.4V), ~150 mA no-load, ~1.0 A stall **per servo**.
One finger (2 servos) draws ~0.3 A moving, ~2 A worst-case stall — a 5V/≥2A supply is
ample. Use an **external 5V supply for the servos**; do **not** power them from the
SO-101 7.4V rail (separate supply, common ground with the USB-TTL only).

## Notes

- Author's `r_hand.toml` offsets (~7° / 5° for finger1) are **his** hand — do not reuse.
- Upstream `FingerTest` enabled torque on ID_1 only; both servos move, so the bring-up
  copy enables torque on both.
- The two servos per finger are **antagonistic** (opposite-sign goals) — that is the
  differential flexion/extension mechanism, not a bug.
