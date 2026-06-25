# AmazingHand bring-up — WHOLE-HAND coordinated gesture (right hand, 8 servos).
#
# Plays ONE gesture per run on all four fingers, reads back every servo, then
# HOLDS (no infinite loop). Picks the gesture with AH_GESTURE=<name>.
#
# This is OUR adaptation of upstream PythonExample/AmazingHand_Demo.py:
#   - by-id serial port (not COM11)
#   - MiddlePos = 0 for all 8 (our calibration: horns fitted at neutral, run-log 2026-06-24)
#   - torque enabled on ALL 8 (upstream only enabled ID 1)
#   - AH_BRINGUP_ARM=1 guard; bare run = DRY RUN (reads only, no motion)
#   - per-finger readback + bind auto-abort -> returns to OPEN
#
# Finger map: index=(1,2) middle=(3,4) ring=(5,6) thumb=(7,8).
# Per finger Move(a,b): a,b are the two servo angles relative to MiddlePos.
#   opposite signs (e.g. +90/-90) = flexion (curl/extend)  <- "pure flexion", tracks well
#   same/asymmetric signs        = abduction (side spread)  <- real range ~+/-20 deg, needs IK,
#                                                              raw values are upstream's hand-tuned
#                                                              approximations; may not look clean.
#
# Run:
#   ~/amazinghand/.venv/bin/python hand_gesture.py                         # list gestures
#   AH_GESTURE=open ~/amazinghand/.venv/bin/python hand_gesture.py         # DRY RUN one gesture
#   AH_GESTURE=open AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python hand_gesture.py   # MOVE
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"

# our calibration: all fingers sit at mechanical neutral when servos read ~0
MIDDLE = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}

FINGERS = {"index": (1, 2), "middle": (3, 4), "ring": (5, 6), "thumb": (7, 8)}

SPEED = max(1, min(6, int(os.environ.get("AH_SPEED", "4"))))   # AH_SPEED 1..6, default 4 (gentle)
SETTLE = 1.6
BIND_ABORT = 16.0   # abduction gestures track looser than pure flexion; a touch above finger_cycle

# Each gesture: per-finger (a, b) relative to MiddlePos. Values mirror upstream
# AmazingHand_Demo.py Side=1 (right hand). "kind" is informational only.
GESTURES = {
    # ---- pure flexion: safe, tracks tightly ----
    "open":    {"kind": "flexion",   "index": (-35, 35), "middle": (-35, 35), "ring": (-35, 35), "thumb": (-35, 35)},
    "close":   {"kind": "flexion",   "index": (90, -90), "middle": (90, -90), "ring": (90, -90), "thumb": (90, -90)},
    "point":   {"kind": "flexion",   "index": (-40, 40), "middle": (90, -90), "ring": (90, -90), "thumb": (90, -90)},
    "midfing": {"kind": "flexion",   "index": (90, -90), "middle": (-35, 35), "ring": (90, -90), "thumb": (90, -90)},
    # ---- uses abduction: runnable but raw angles are approximate (needs IK for clean shape) ----
    "victory": {"kind": "abduction", "index": (-15, 65), "middle": (-65, 15), "ring": (90, -90), "thumb": (90, -90)},
    "spread":  {"kind": "abduction", "index": (4, 90),   "middle": (-32, 32), "ring": (-90, -4), "thumb": (-90, -4)},
    "perfect": {"kind": "abduction", "index": (50, -50), "middle": (0, 0),    "ring": (-20, 20), "thumb": (65, 12)},
    "pinch":   {"kind": "abduction", "index": (90, -90), "middle": (90, -90), "ring": (90, -90), "thumb": (0, -75)},
}

OPEN = GESTURES["open"]


def _scalar(v):
    try:
        return v[0]
    except (TypeError, IndexError, KeyError):
        return v


def _deg(sid):
    return float(np.rad2deg(_scalar(c.read_present_position(sid))))


def goto(g):
    for finger, (id1, id2) in FINGERS.items():
        a, b = g[finger]
        c.write_goal_position(id1, np.deg2rad(MIDDLE[id1] + a))
        c.write_goal_position(id2, np.deg2rad(MIDDLE[id2] + b))
    time.sleep(SETTLE)


def report(g):
    worst = 0.0
    for finger, (id1, id2) in FINGERS.items():
        a, b = g[finger]
        ta, tb = MIDDLE[id1] + a, MIDDLE[id2] + b
        p1, p2 = _deg(id1), _deg(id2)
        e1, e2 = abs(p1 - ta), abs(p2 - tb)
        flag = "  <-- CHECK" if (e1 > 8 or e2 > 8) else ""
        print(f"  {finger:7s} ({id1},{id2}) cmd=({ta:+4d},{tb:+4d}) present=({p1:+6.1f},{p2:+6.1f}) err=({e1:.1f},{e2:.1f}){flag}")
        worst = max(worst, e1, e2)
    return worst


name = os.environ.get("AH_GESTURE", "").strip().lower()
if name not in GESTURES:
    print("AH_GESTURE not set / unknown. Available gestures:")
    for k, v in GESTURES.items():
        print(f"  {k:9s} [{v['kind']}]")
    print("\nUsage: AH_GESTURE=open [AH_BRINGUP_ARM=1] python hand_gesture.py")
    raise SystemExit(0 if not name else 1)

g = GESTURES[name]

c = Scs0009PyController(serial_port=SERIAL_PORT, baudrate=1000000, timeout=0.5)

# census: all 8 must answer
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
print(f"before: all 8 servos present. gesture='{name}' [{g['kind']}]")

if g["kind"] == "abduction":
    print("note: this gesture uses abduction — raw angles are upstream approximations; "
          "real abduction range is ~+/-20 deg and needs IK. Shape may look off; watch for bind.")

if os.environ.get("AH_BRINGUP_ARM") != "1":
    print(f"DRY RUN: would move to '{name}' at speed {SPEED}, then hold. No motion.")
    print("Set AH_BRINGUP_ARM=1 to actually move.")
    raise SystemExit(0)

for sid in range(1, 9):
    c.write_torque_enable(sid, 1)
    c.write_goal_speed(sid, SPEED)

goto(g)
worst = report(g)

if worst > BIND_ABORT:
    print(f"!! BIND/CHECK: worst err {worst:.1f} deg > {BIND_ABORT}. Returning to OPEN.")
    goto(OPEN)
    report(OPEN)
    raise SystemExit(2)

print(f"Done: gesture '{name}' reached (worst err {worst:.1f} deg). Holding. "
      f"Run AH_GESTURE=open ... to reset, or power off 5V to stop.")
