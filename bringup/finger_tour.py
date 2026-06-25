# AmazingHand bring-up — single-finger 2-DOF TOUR: up / down / left / right.
#
# 2 servos/finger = 2-DOF differential:
#   opposite signs (+/-) -> flexion/extension  => UP (open) / DOWN (close)
#   same signs     (+/+) -> abduction/adduction => LEFT / RIGHT
#
# Walks: middle -> up -> middle -> down -> middle -> left -> middle -> right -> middle.
# Reads back every step; auto-aborts to middle on bind. Default finger = thumb (7,8).
#
# Abduction legs use +/- AH_ABD deg (default 20 = the REAL mechanical range; raw angles
# beyond that don't map to real abduction without IK). Flexion legs use AH_UP / AH_DOWN.
#
# Knobs (env): AH_ID1/AH_ID2 (default 7,8), AH_UP (default 30), AH_DOWN (default 90),
#              AH_ABD (5..20, default 20), AH_SPEED (1..6, default 3), AH_LOOPS (1..10, default 1).
# Guard AH_BRINGUP_ARM=1. Without it: DRY RUN (reads only, no motion).
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
ID_1 = int(os.environ.get("AH_ID1", "7"))
ID_2 = int(os.environ.get("AH_ID2", "8"))
UP = max(5, min(90, int(os.environ.get("AH_UP", "30"))))
DOWN = max(5, min(90, int(os.environ.get("AH_DOWN", "90"))))
ABD = max(5, min(45, int(os.environ.get("AH_ABD", "20"))))   # >20 = beyond REAL abduction range (raw, needs IK)
SPEED = max(1, min(6, int(os.environ.get("AH_SPEED", "3"))))
LOOPS = max(1, min(10, int(os.environ.get("AH_LOOPS", "1"))))
SETTLE = 1.5
BIND_ABORT = 16.0


def _scalar(v):
    try:
        return v[0]
    except (TypeError, IndexError, KeyError):
        return v


def _deg(sid):
    return float(np.rad2deg(_scalar(c.read_present_position(sid))))


def goto(a, b):
    c.write_goal_position(ID_1, np.deg2rad(a))
    c.write_goal_position(ID_2, np.deg2rad(b))
    time.sleep(SETTLE)
    return _deg(ID_1), _deg(ID_2)


def step(label, a, b):
    p1, p2 = goto(a, b)
    e1, e2 = abs(p1 - a), abs(p2 - b)
    flag = "  <-- CHECK" if (e1 > 8 or e2 > 8) else ""
    print(f"{label:10s} cmd=({a:+4d},{b:+4d})  present=({p1:+6.1f},{p2:+6.1f})  err=({e1:.1f},{e2:.1f}){flag}")
    return max(e1, e2)


# leg = (label, ID_1 deg, ID_2 deg)
SEQ = [
    ("up",     -UP,  +UP),    # flexion: extend/open
    ("middle",   0,    0),
    ("down",   +DOWN, -DOWN), # flexion: curl/close
    ("middle",   0,    0),
    ("left",   +ABD, +ABD),   # abduction: both same sign
    ("middle",   0,    0),
    ("right",  -ABD, -ABD),   # abduction: both other sign
    ("middle",   0,    0),
]

c = Scs0009PyController(serial_port=SERIAL_PORT, baudrate=1000000, timeout=0.5)

present = []
for sid in (ID_1, ID_2):
    try:
        d = _deg(sid)
        present.append(sid)
        print(f"before: ID {sid} present = {d:+7.1f} deg")
    except Exception:
        print(f"before: ID {sid} NO RESPONSE")
if present != [ID_1, ID_2]:
    print(f"ABORT: need both ID {ID_1},{ID_2} present, got {present}.")
    raise SystemExit(1)

if ABD > 20:
    print(f"note: abduction set to +/-{ABD} deg — BEYOND the real ~+/-20 deg range. "
          "Servos will rotate but this is raw (not true abduction); watch for bind.")

if os.environ.get("AH_BRINGUP_ARM") != "1":
    print(f"DRY RUN: would tour up({UP})/down({DOWN}) flexion + left/right abduction(+/-{ABD}), "
          f"{LOOPS}x, speed {SPEED}. No motion.")
    print("Set AH_BRINGUP_ARM=1 to actually move.")
    raise SystemExit(0)

c.write_torque_enable(ID_1, 1)
c.write_torque_enable(ID_2, 1)
c.write_goal_speed(ID_1, SPEED)
c.write_goal_speed(ID_2, SPEED)

aborted = False
for n in range(1, LOOPS + 1):
    if LOOPS > 1:
        print(f"--- loop {n}/{LOOPS} ---")
    for label, a, b in SEQ:
        if step(label, a, b) > BIND_ABORT:
            aborted = True
            break
    if aborted:
        break

goto(0, 0)
print("!! BIND DETECTED — stopped early, returned to middle." if aborted
      else f"Done: {LOOPS} tour(s) up/down/left/right. Holding at middle.")
