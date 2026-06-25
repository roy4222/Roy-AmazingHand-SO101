# AmazingHand bring-up — WHOLE-HAND pure LEFT/RIGHT sway (abduction only, all 8 servos).
#
# This isolates the LEFT-RIGHT degree of freedom: both servos of every finger move the
# SAME direction (+ = left, - = right). It does NOT mix in flexion, so the sideways
# motion is as clean as the parallel mechanism allows.
#
#   left  = (+AMP, +AMP) on all fingers
#   right = (-AMP, -AMP) on all fingers
#
# NOTE: real abduction range is ~+/-20 deg. AMP>20 is raw rotation (servos still move,
# but it is past the geometrically meaningful range; true large abduction needs IK).
#
# Knobs (env): AH_AMP 5..45 (default 25), AH_SWAYS 1..20 (default 4), AH_SPEED 1..6 (default 4).
# Guard AH_BRINGUP_ARM=1. Without it: DRY RUN (reads only, no motion).
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
FINGERS = {"index": (1, 2), "middle": (3, 4), "ring": (5, 6), "thumb": (7, 8)}

AMP = max(5, min(45, int(os.environ.get("AH_AMP", "25"))))
SWAYS = max(1, min(20, int(os.environ.get("AH_SWAYS", "4"))))
SPEED = max(1, min(6, int(os.environ.get("AH_SPEED", "4"))))
SETTLE = 1.4
BIND_ABORT = 16.0


def _scalar(v):
    try:
        return v[0]
    except (TypeError, IndexError, KeyError):
        return v


def _deg(sid):
    return float(np.rad2deg(_scalar(c.read_present_position(sid))))


def goto(a, b):
    for (id1, id2) in FINGERS.values():
        c.write_goal_position(id1, np.deg2rad(a))
        c.write_goal_position(id2, np.deg2rad(b))
    time.sleep(SETTLE)


def report(label, a, b):
    worst = 0.0
    cells = []
    for finger, (id1, id2) in FINGERS.items():
        p1, p2 = _deg(id1), _deg(id2)
        e1, e2 = abs(p1 - a), abs(p2 - b)
        worst = max(worst, e1, e2)
        cells.append(f"{finger[0]}=({p1:+5.0f},{p2:+5.0f})")
    flag = "  <-- CHECK" if worst > 8 else ""
    print(f"{label:8s} cmd=({a:+4d},{b:+4d})  {'  '.join(cells)}  worst={worst:.1f}{flag}")
    return worst


c = Scs0009PyController(serial_port=SERIAL_PORT, baudrate=1000000, timeout=0.5)

present = []
for sid in range(1, 9):
    try:
        _deg(sid)
        present.append(sid)
    except Exception:
        print(f"before: ID {sid} NO RESPONSE")
if present != list(range(1, 9)):
    print(f"ABORT: need all 8 servos present, got {present}.")
    raise SystemExit(1)
print("before: all 8 servos present.")

if AMP > 20:
    print(f"note: AMP +/-{AMP} deg is BEYOND the real ~+/-20 deg abduction range — raw rotation "
          "(servos move, but past the geometrically true range; large clean abduction needs IK).")

if os.environ.get("AH_BRINGUP_ARM") != "1":
    print(f"DRY RUN: would sway LEFT/RIGHT +/-{AMP} deg (both servos same dir), {SWAYS}x, speed {SPEED}. No motion.")
    print("Set AH_BRINGUP_ARM=1 to actually move.")
    raise SystemExit(0)

for sid in range(1, 9):
    c.write_torque_enable(sid, 1)
    c.write_goal_speed(sid, SPEED)

seq = []
for i in range(1, SWAYS + 1):
    seq.append((f"left #{i}", +AMP, +AMP))
    seq.append((f"right #{i}", -AMP, -AMP))

aborted = False
for label, a, b in seq:
    goto(a, b)
    if report(label, a, b) > BIND_ABORT:
        aborted = True
        break

goto(0, 0)
print("!! BIND DETECTED — stopped early, all returned to middle." if aborted
      else f"Done: {SWAYS} left/right sways, all 4 fingers. Holding at middle.")
