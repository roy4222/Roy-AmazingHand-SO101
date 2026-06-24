# AmazingHand bring-up — incremental antagonistic CLOSE steps (horns ON, linkage connected).
#
# Grows the close (flexion) angle in stages so you can watch the finger bend further at
# each step. NOT the full +/-90 FingerTest, and NOT a loop. Auto-aborts to middle if a
# servo cannot reach its target (binding).
#
# Guard AH_BRINGUP_ARM=1. Without it: DRY RUN.
#   ~/amazinghand/.venv/bin/python finger_close_steps.py               # DRY RUN
#   AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python finger_close_steps.py   # MOVE
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
ID_1 = int(os.environ.get("AH_ID1", "1"))   # AH_ID1/AH_ID2 select the finger (f1=1,2 f2=3,4 f3=5,6 f4=7,8)
ID_2 = int(os.environ.get("AH_ID2", "2"))
SPEED = 4
SETTLE = 2.0
BIND_ABORT = 12.0   # deg tracking error that triggers auto-abort to middle

# (label, ID_1 deg, ID_2 deg) — antagonistic close grows toward full close (90),
# then HOLDS at full close for inspection (does not auto-return).
STEPS = [
    ("middle",   0,   0),
    ("close 45", 45, -45),
    ("close 60", 60, -60),
    ("close 75", 75, -75),
    ("close 90", 90, -90),
]


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
    print(f"DRY RUN: would do incremental close {[s[0] for s in STEPS]} at speed {SPEED}.")
    print("Set AH_BRINGUP_ARM=1 to actually move. Exiting without motion.")
    raise SystemExit(0)

c.write_torque_enable(ID_1, 1)
c.write_torque_enable(ID_2, 1)
c.write_goal_speed(ID_1, SPEED)
c.write_goal_speed(ID_2, SPEED)

aborted = False
for label, a, b in STEPS:
    p1, p2 = goto(a, b)
    e1, e2 = abs(p1 - a), abs(p2 - b)
    flag = "  <-- CHECK" if (e1 > 8 or e2 > 8) else ""
    print(f"{label:9s} cmd=({a:+4d},{b:+4d})  present=({p1:+6.1f},{p2:+6.1f})  err=({e1:.1f},{e2:.1f}){flag}")
    if e1 > BIND_ABORT or e2 > BIND_ABORT:
        print("!! BIND DETECTED (servo can't reach target) — returning to middle and stopping.")
        goto(0, 0)
        aborted = True
        break

if aborted:
    print("Stopped at middle due to bind.")
else:
    print("Holding at FULL close (servo +/-90). Inspect finger curl + horn alignment.")
    print("Don't leave it held here long (heat); say the word and I'll return it to middle.")
