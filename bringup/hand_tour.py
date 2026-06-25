# AmazingHand bring-up — WHOLE-HAND SYNCHRONISED 2-DOF tour (all 8 servos together).
#
# All four fingers move TOGETHER through: middle -> up -> middle -> down ->
# middle -> left -> middle -> right -> middle. Reads back all 8 each leg;
# auto-aborts ALL to middle on bind.
#
# Per finger, 2 servos (ID_1,ID_2) relative to MiddlePos=0:
#   up   = (-UP,  +UP)   flexion extend (open)
#   down = (+DOWN,-DOWN) flexion curl   (close)
#   left = (+ABD, +ABD)  abduction (same sign)
#   right= (-ABD, -ABD)  abduction (same sign)
# NOTE: abduction >20 deg is BEYOND the real mechanical range (raw, needs IK).
#
# Knobs (env): AH_UP (default 30), AH_DOWN (default 90), AH_ABD 5..45 (default 20),
#              AH_SPEED 1..6 (default 3), AH_LOOPS 1..10 (default 1).
# Guard AH_BRINGUP_ARM=1. Without it: DRY RUN (reads only, no motion).
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
FINGERS = {"index": (1, 2), "middle": (3, 4), "ring": (5, 6), "thumb": (7, 8)}

UP = max(5, min(90, int(os.environ.get("AH_UP", "30"))))
DOWN = max(5, min(90, int(os.environ.get("AH_DOWN", "90"))))
ABD = max(5, min(45, int(os.environ.get("AH_ABD", "20"))))   # >20 = beyond REAL abduction (raw, needs IK)
SPEED = max(1, min(6, int(os.environ.get("AH_SPEED", "3"))))
LOOPS = max(1, min(10, int(os.environ.get("AH_LOOPS", "1"))))
SETTLE = 1.6
BIND_ABORT = 16.0

# (label, a, b) applied to every finger's (ID_1, ID_2)
SEQ = [
    ("up",     -UP,  +UP),
    ("middle",   0,    0),
    ("down",   +DOWN, -DOWN),
    ("middle",   0,    0),
    ("left",   +ABD, +ABD),
    ("middle",   0,    0),
    ("right",  -ABD, -ABD),
    ("middle",   0,    0),
]


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
    print(f"{label:7s} cmd=({a:+4d},{b:+4d})  {'  '.join(cells)}  worst={worst:.1f}{flag}")
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

if ABD > 20:
    print(f"note: abduction +/-{ABD} deg is BEYOND the real ~+/-20 deg range — raw rotation, "
          "not true abduction (needs IK). Watch for bind.")

if os.environ.get("AH_BRINGUP_ARM") != "1":
    print(f"DRY RUN: would sync-tour up({UP})/down({DOWN}) + left/right abduction(+/-{ABD}), "
          f"{LOOPS}x, speed {SPEED}. No motion.")
    print("Set AH_BRINGUP_ARM=1 to actually move.")
    raise SystemExit(0)

for sid in range(1, 9):
    c.write_torque_enable(sid, 1)
    c.write_goal_speed(sid, SPEED)

aborted = False
for n in range(1, LOOPS + 1):
    if LOOPS > 1:
        print(f"--- loop {n}/{LOOPS} ---")
    for label, a, b in SEQ:
        goto(a, b)
        if report(label, a, b) > BIND_ABORT:
            aborted = True
            break
    if aborted:
        break

goto(0, 0)
print("!! BIND DETECTED — stopped early, all returned to middle." if aborted
      else f"Done: {LOOPS} synchronised tour(s), all 4 fingers. Holding at middle.")
