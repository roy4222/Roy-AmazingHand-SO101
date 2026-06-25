# AmazingHand bring-up — PRIMITIVE PROBE for one finger (default servos 1,2).
#
# Isolates the two pure 2-servo primitives so a HUMAN can label which DOF each is.
# The 2-servo parallel mechanism is a closed loop (no simple formula), so we MEASURE
# instead of guessing.
#
#   OPPOSITE primitive : (+MAG,-MAG) <-> (-MAG,+MAG)   (servos counter-rotate)
#   SAME     primitive : (+MAG,+MAG) <-> (-MAG,-MAG)   (servos co-rotate / common-mode)
#
# Runs each primitive REPS times, slowly, with a pause + clear banner, returning to
# middle between primitives. WATCH the fingertip and tell me, for EACH primitive,
# whether it is UP/DOWN (flexion) or LEFT/RIGHT (abduction).
#
# Knobs (env): AH_ID1/AH_ID2 (default 1,2), AH_MAG 10..45 (default 30),
#              AH_REPS 1..10 (default 3), AH_SPEED 1..6 (default 2 = slow), AH_PAUSE (default 1.5).
# Guard AH_BRINGUP_ARM=1. Without it: DRY RUN.
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
ID_1 = int(os.environ.get("AH_ID1", "1"))
ID_2 = int(os.environ.get("AH_ID2", "2"))
MAG = max(10, min(45, int(os.environ.get("AH_MAG", "30"))))
REPS = max(1, min(10, int(os.environ.get("AH_REPS", "3"))))
SPEED = max(1, min(6, int(os.environ.get("AH_SPEED", "2"))))
PAUSE = float(os.environ.get("AH_PAUSE", "1.5"))
SETTLE = 1.6
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
    p1, p2 = _deg(ID_1), _deg(ID_2)
    return p1, p2, max(abs(p1 - a), abs(p2 - b))


def primitive(name, poses):
    print(f"\n######## {name} ########")
    worst = 0.0
    goto(0, 0)
    time.sleep(PAUSE)
    for r in range(1, REPS + 1):
        for label, a, b in poses:
            p1, p2, e = goto(a, b)
            worst = max(worst, e)
            print(f"  {name} #{r} {label:7s} cmd=({a:+4d},{b:+4d}) present=({p1:+6.1f},{p2:+6.1f}) err={e:.1f}")
            if e > BIND_ABORT:
                print("  !! bind, aborting primitive")
                goto(0, 0)
                return worst
            time.sleep(PAUSE)
    goto(0, 0)
    return worst


c = Scs0009PyController(serial_port=SERIAL_PORT, baudrate=1000000, timeout=0.5)

present = []
for sid in (ID_1, ID_2):
    try:
        _deg(sid)
        present.append(sid)
    except Exception:
        print(f"before: ID {sid} NO RESPONSE")
if present != [ID_1, ID_2]:
    print(f"ABORT: need both ID {ID_1},{ID_2} present, got {present}.")
    raise SystemExit(1)
print(f"before: ID {ID_1},{ID_2} present. MAG={MAG} REPS={REPS} SPEED={SPEED}")

if os.environ.get("AH_BRINGUP_ARM") != "1":
    print("DRY RUN: would run OPPOSITE then SAME primitives. No motion.")
    print("Set AH_BRINGUP_ARM=1 to actually move.")
    raise SystemExit(0)

c.write_torque_enable(ID_1, 1)
c.write_torque_enable(ID_2, 1)
c.write_goal_speed(ID_1, SPEED)
c.write_goal_speed(ID_2, SPEED)

OPPOSITE = [("pos", +MAG, -MAG), ("neg", -MAG, +MAG)]
SAME = [("pos", +MAG, +MAG), ("neg", -MAG, -MAG)]

w1 = primitive("OPPOSITE (servos counter-rotate)", OPPOSITE)
w2 = primitive("SAME (servos co-rotate)", SAME)

goto(0, 0)
print(f"\nDone. OPPOSITE worst err {w1:.1f}, SAME worst err {w2:.1f}. Holding at middle.")
print(">>> TELL ME: which primitive was UP/DOWN (flexion) and which was LEFT/RIGHT (abduction)?")
