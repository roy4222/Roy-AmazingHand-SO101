# AmazingHand bring-up — per-servo functional check (run with horns OFF / bare shafts).
#
# Tests each servo INDIVIDUALLY (one at a time) through a sweep and reads back present
# position to confirm both motors track commands. With horns off there is no mechanism
# to bind, so a wider sweep is safe. Ends with both servos at 0 deg, holding, ready for
# horn re-fitting.
#
# Guard AH_BRINGUP_ARM=1. Without it: DRY RUN (reads only, no motion).
#   ~/amazinghand/.venv/bin/python servo_check.py                # DRY RUN
#   AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python servo_check.py   # MOVE each in turn
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
IDS = (int(os.environ.get("AH_ID1", "1")), int(os.environ.get("AH_ID2", "2")))   # select finger
SWEEP = [0, 45, 0, -45, 0]   # degrees, per servo
SPEED = 4
SETTLE = 1.2


def _scalar(v):
    try:
        return v[0]
    except (TypeError, IndexError, KeyError):
        return v


def _deg(sid):
    return float(np.rad2deg(_scalar(c.read_present_position(sid))))


c = Scs0009PyController(serial_port=SERIAL_PORT, baudrate=1000000, timeout=0.5)

# census
present = []
for sid in IDS:
    try:
        d = _deg(sid)
        present.append(sid)
        print(f"before: ID {sid} present = {d:+7.1f} deg")
    except Exception:
        print(f"before: ID {sid} NO RESPONSE")
if present != list(IDS):
    print(f"ABORT: need both ID {IDS} present, got {present}.")
    raise SystemExit(1)

if os.environ.get("AH_BRINGUP_ARM") != "1":
    print(f"DRY RUN: would sweep each servo {SWEEP} deg, one at a time, speed {SPEED}.")
    print("Set AH_BRINGUP_ARM=1 to actually move. Exiting without motion.")
    raise SystemExit(0)

worst = {}
for sid in IDS:
    print(f"--- testing ID {sid} ALONE (other servo not commanded) ---")
    c.write_torque_enable(sid, 1)
    c.write_goal_speed(sid, SPEED)
    w = 0.0
    for ang in SWEEP:
        c.write_goal_position(sid, np.deg2rad(ang))
        time.sleep(SETTLE)
        p = _deg(sid)
        err = abs(p - ang)
        w = max(w, err)
        flag = "  <-- CHECK (far from target)" if err > 8 else ""
        print(f"   ID {sid}  cmd={ang:+4d}  present={p:+7.1f}  err={err:4.1f}{flag}")
    worst[sid] = w

print("---")
for sid in IDS:
    verdict = "OK" if worst[sid] <= 8 else "REVIEW"
    print(f"ID {sid}: worst tracking error {worst[sid]:.1f} deg -> {verdict}")
print("Both servos left at 0 deg, holding. Re-fit horns at this neutral when ready.")
