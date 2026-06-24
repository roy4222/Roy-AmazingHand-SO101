# AmazingHand bring-up — abduction (left-right) test: both servos move the SAME direction.
#
# 2 servos/finger = 2-DOF differential:
#   opposite signs (+/-) -> flexion/extension (open/close, up-down)
#   same signs     (+/+) -> abduction/adduction (left-right)   <-- THIS script
#
# Sways side to side AMP degrees, SWAYS times, then returns to middle. Auto-aborts on bind.
#
# Knobs (env): AH_AMP deg (5..45, default 20), AH_SWAYS (1..20, default 2),
#              AH_SPEED (1..6, default 4).
# Guard AH_BRINGUP_ARM=1. Without it: DRY RUN.
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
ID_1 = int(os.environ.get("AH_ID1", "1"))   # AH_ID1/AH_ID2 select the finger (f1=1,2 f2=3,4 f3=5,6 f4=7,8)
ID_2 = int(os.environ.get("AH_ID2", "2"))
AMP = max(5, min(90, int(os.environ.get("AH_AMP", "20"))))
SWAYS = max(1, min(20, int(os.environ.get("AH_SWAYS", "2"))))
SPEED = max(1, min(6, int(os.environ.get("AH_SPEED", "4"))))
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
    print(f"DRY RUN: would sway +/-{AMP} deg (both same direction), {SWAYS}x, speed {SPEED}.")
    print("Set AH_BRINGUP_ARM=1 to actually move. Exiting without motion.")
    raise SystemExit(0)

c.write_torque_enable(ID_1, 1)
c.write_torque_enable(ID_2, 1)
c.write_goal_speed(ID_1, SPEED)
c.write_goal_speed(ID_2, SPEED)

seq = []
for i in range(1, SWAYS + 1):
    seq.append((f"left #{i}", +AMP, +AMP))
    seq.append((f"right #{i}", -AMP, -AMP))

aborted = False
for label, a, b in seq:
    if step(label, a, b) > BIND_ABORT:
        aborted = True
        break

goto(0, 0)
print("!! BIND DETECTED — stopped early, returned to middle." if aborted
      else f"Done: {SWAYS} left-right sways at +/-{AMP} deg. Holding at middle.")
