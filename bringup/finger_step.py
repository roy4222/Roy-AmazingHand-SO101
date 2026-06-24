# AmazingHand bring-up — SMALL antagonistic direction check (run AFTER horns are on).
#
# Moves finger1 a few SMALL steps (low speed) to verify direction and no binding,
# then returns to MiddlePos and holds. This is NOT the full FingerTest open/close
# cycle (that uses +/-90 deg). Watch the finger and keep a hand on the 5V switch.
#
# readback is the bind detector: if a servo is commanded to +15 but present stays
# near 0 and does not move, the mechanism is binding -> power off.
#
# Guard AH_BRINGUP_ARM=1. Without it: DRY RUN (reads only, no motion).
#   ~/amazinghand/.venv/bin/python finger_step.py                # DRY RUN
#   AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python finger_step.py   # MOVE (small)
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
ID_1 = int(os.environ.get("AH_ID1", "1"))   # AH_ID1/AH_ID2 select the finger (f1=1,2 f2=3,4 f3=5,6 f4=7,8)
ID_2 = int(os.environ.get("AH_ID2", "2"))
MiddlePos_1, MiddlePos_2 = 0, 0
SPEED = 3        # gentle (mechanism engaged); upstream uses 6 = max
SETTLE = 2.0     # seconds per step to allow arrival at low speed

# (label, ID_1 deg, ID_2 deg) relative to middle — small antagonistic steps
STEPS = [
    ("close +15/-15", MiddlePos_1 + 15, MiddlePos_2 - 15),
    ("middle",        MiddlePos_1 +  0, MiddlePos_2 +  0),
    ("open  -10/+10", MiddlePos_1 - 10, MiddlePos_2 + 10),
    ("middle",        MiddlePos_1 +  0, MiddlePos_2 +  0),
]


def _scalar(v):
    try:
        return v[0]
    except (TypeError, IndexError, KeyError):
        return v


def _deg(sid):
    return float(np.rad2deg(_scalar(c.read_present_position(sid))))


c = Scs0009PyController(serial_port=SERIAL_PORT, baudrate=1000000, timeout=0.5)

# census + before
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
    print("DRY RUN: would do small antagonistic steps "
          f"{[s[0] for s in STEPS]} at speed {SPEED}.")
    print("Set AH_BRINGUP_ARM=1 to actually move. Exiting without motion.")
    raise SystemExit(0)

c.write_torque_enable(ID_1, 1)
c.write_torque_enable(ID_2, 1)
c.write_goal_speed(ID_1, SPEED)
c.write_goal_speed(ID_2, SPEED)

for label, a, b in STEPS:
    c.write_goal_position(ID_1, np.deg2rad(a))
    c.write_goal_position(ID_2, np.deg2rad(b))
    time.sleep(SETTLE)
    p1, p2 = _deg(ID_1), _deg(ID_2)
    d1, d2 = p1 - a, p2 - b
    flag = "  <-- CHECK (far from target)" if (abs(d1) > 8 or abs(d2) > 8) else ""
    print(f"{label:14s} cmd=({a:+4d},{b:+4d})  present=({p1:+6.1f},{p2:+6.1f}){flag}")

print("Returned to MiddlePos, holding. If any step showed CHECK or the finger buzzed, stop.")
