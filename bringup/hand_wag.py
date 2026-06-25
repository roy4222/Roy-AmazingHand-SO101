# AmazingHand bring-up — WHOLE-HAND left/right WAG done the RIGHT way.
#
# Correct abduction recipe (matches upstream Nonono / SpreadHand):
#   1. SPREAD the fingers OPEN first  -> the two servos go OPPOSITE (a flexion-EXTENSION
#      offset). This is the "撐開" / "相反轉" step: servo1 = -EXT, servo2 = +EXT  (diff held).
#   2. WAG left/right by shifting BOTH servos the SAME direction (common-mode) by +/-AMP,
#      WITHOUT changing the diff -> the spread finger rolls side to side.
#
#   base  : (-EXT,        +EXT)
#   left  : (-EXT + AMP,  +EXT + AMP)
#   right : (-EXT - AMP,  +EXT - AMP)        # diff = -2*EXT stays constant the whole time
#
# Earlier hand_sway.py swayed around the NEUTRAL pose (EXT=0, fingers not spread) which is
# why it produced almost no visible motion. Spreading first is the fix.
#
# Knobs (env): AH_EXT 10..60 (default 45, how far spread open), AH_AMP 5..50 (default 40,
#              wag size), AH_SWAYS 1..20 (default 5), AH_SPEED 1..6 (default 3).
# Guard AH_BRINGUP_ARM=1. Without it: DRY RUN.
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
FINGERS = {"index": (1, 2), "middle": (3, 4), "ring": (5, 6), "thumb": (7, 8)}
CLAMP = 125

EXT = max(10, min(60, int(os.environ.get("AH_EXT", "45"))))
AMP = max(5, min(50, int(os.environ.get("AH_AMP", "40"))))
SWAYS = max(1, min(20, int(os.environ.get("AH_SWAYS", "5"))))
SPEED = max(1, min(6, int(os.environ.get("AH_SPEED", "3"))))
SETTLE = 1.4
BIND_ABORT = 16.0


def _scalar(v):
    try:
        return v[0]
    except (TypeError, IndexError, KeyError):
        return v


def _deg(sid):
    return float(np.rad2deg(_scalar(c.read_present_position(sid))))


def _clamp(x):
    return max(-CLAMP, min(CLAMP, x))


def goto(common):
    targets = {}
    for finger, (id1, id2) in FINGERS.items():
        ta, tb = _clamp(-EXT + common), _clamp(+EXT + common)
        targets[finger] = (ta, tb)
        c.write_goal_position(id1, np.deg2rad(ta))
        c.write_goal_position(id2, np.deg2rad(tb))
    time.sleep(SETTLE)
    return targets


def report(label, targets):
    worst = 0.0
    cells = []
    for finger, (id1, id2) in FINGERS.items():
        ta, tb = targets[finger]
        p1, p2 = _deg(id1), _deg(id2)
        worst = max(worst, abs(p1 - ta), abs(p2 - tb))
        cells.append(f"{finger[0]}=({p1:+5.0f},{p2:+5.0f})")
    flag = "  <-- CHECK" if worst > 8 else ""
    print(f"{label:8s} {'  '.join(cells)}  worst={worst:.1f}{flag}")
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
print(f"before: all 8 present. spread EXT={EXT} (diff held {-2*EXT}), wag AMP=+/-{AMP} x{SWAYS}")

if os.environ.get("AH_BRINGUP_ARM") != "1":
    print(f"DRY RUN: would spread open (EXT {EXT}) then wag left/right +/-{AMP}, {SWAYS}x, speed {SPEED}. No motion.")
    print("Set AH_BRINGUP_ARM=1 to actually move.")
    raise SystemExit(0)

for sid in range(1, 9):
    c.write_torque_enable(sid, 1)
    c.write_goal_speed(sid, SPEED)

# 1) spread open first
report("spread", goto(0))

# 2) wag left/right (common-mode only; diff stays = -2*EXT)
seq = []
for i in range(1, SWAYS + 1):
    seq.append((f"left #{i}", +AMP))
    seq.append((f"right #{i}", -AMP))

aborted = False
for label, common in seq:
    if report(label, goto(common)) > BIND_ABORT:
        aborted = True
        break

goto(0)  # back to spread-open
if aborted:
    print("!! BIND DETECTED — stopped, returned to spread-open.")
else:
    print(f"Done: spread + {SWAYS} left/right wags. Holding spread-open. Power off 5V or run hand_gesture open to reset.")
