# AmazingHand bring-up — BOUNDED open/close cycles (a few reps, NOT the infinite loop).
#
# open  = (ID1 -30, ID2 +30)   close = (ID1 +90, ID2 -90)   [upstream FingerTest values]
# Runs CYCLES open/close reps with readback, then returns to MiddlePos. Auto-aborts to
# middle if a servo cannot reach its target (binding).
#
# Guard AH_BRINGUP_ARM=1. Without it: DRY RUN.
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
ID_1 = int(os.environ.get("AH_ID1", "1"))   # AH_ID1/AH_ID2 select the finger (f1=1,2 f2=3,4 f3=5,6 f4=7,8)
ID_2 = int(os.environ.get("AH_ID2", "2"))
OPEN = (-30, 30)
CLOSE = (90, -90)
CYCLES = max(1, min(20, int(os.environ.get("AH_CYCLES", "3"))))   # AH_CYCLES env, 1..20
SPEED = max(1, min(6, int(os.environ.get("AH_SPEED", "5"))))      # AH_SPEED env, 1..6
SETTLE = 1.4
BIND_ABORT = 14.0


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
    print(f"{label:9s} cmd=({a:+4d},{b:+4d})  present=({p1:+6.1f},{p2:+6.1f})  err=({e1:.1f},{e2:.1f}){flag}")
    return max(e1, e2)


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

if os.environ.get("AH_BRINGUP_ARM") != "1":
    print(f"DRY RUN: would run {CYCLES} open/close cycles at speed {SPEED}.")
    print("Set AH_BRINGUP_ARM=1 to actually move. Exiting without motion.")
    raise SystemExit(0)

c.write_torque_enable(ID_1, 1)
c.write_torque_enable(ID_2, 1)
c.write_goal_speed(ID_1, SPEED)
c.write_goal_speed(ID_2, SPEED)

aborted = False
for i in range(1, CYCLES + 1):
    if step(f"open #{i}", *OPEN) > BIND_ABORT:
        aborted = True
        break
    if step(f"close #{i}", *CLOSE) > BIND_ABORT:
        aborted = True
        break

goto(0, 0)
if aborted:
    print("!! BIND DETECTED — stopped early, returned to middle.")
else:
    print(f"Done: {CYCLES} clean open/close cycles. Holding at middle.")
