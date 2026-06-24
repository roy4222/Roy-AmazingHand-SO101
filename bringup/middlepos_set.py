# AmazingHand bring-up — drive finger1 servos to MiddlePos and HOLD (for horn fitting).
#
# This MOVES the servos (torque enable + goal position). Intended to be run with the
# horns OFF (bare shafts) so the shaft rotates to its middle (0 deg); you then fit the
# horn at that neutral. If the finger is assembled, a large move could bind — check first.
#
# Bounded one-shot (NOT the upstream infinite loop): read before, enable torque,
# command MiddlePos, hold, read back present positions to confirm arrival, then exit
# leaving the servos HOLDING at MiddlePos (torque stays on until power-off).
#
# Guard: requires AH_BRINGUP_ARM=1. Without it -> DRY RUN (reads only, no motion).
#   ~/amazinghand/.venv/bin/python middlepos_set.py               # DRY RUN
#   AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python middlepos_set.py   # MOVE
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
ID_1 = int(os.environ.get("AH_ID1", "1"))   # AH_ID1/AH_ID2 select the finger (f1=1,2 f2=3,4 f3=5,6 f4=7,8)
ID_2 = int(os.environ.get("AH_ID2", "2"))
MiddlePos_1, MiddlePos_2 = 0, 0   # degrees — tune per hand after seeing horn alignment
SPEED = 6                          # upstream's value ("6 => max"); horns off => no bind


def _scalar(v):
    try:
        return v[0]
    except (TypeError, IndexError, KeyError):
        return v


def _deg(sid):
    return float(np.rad2deg(_scalar(c.read_present_position(sid))))


c = Scs0009PyController(serial_port=SERIAL_PORT, baudrate=1000000, timeout=0.5)

# census + before positions
present = []
for sid in (ID_1, ID_2):
    try:
        d = _deg(sid)
        present.append(sid)
        print(f"before: ID {sid} present = {d:7.1f} deg")
    except Exception:
        print(f"before: ID {sid} NO RESPONSE")

if present != [ID_1, ID_2]:
    print(f"ABORT: need both ID {ID_1},{ID_2} present, got {present}.")
    raise SystemExit(1)

if os.environ.get("AH_BRINGUP_ARM") != "1":
    print(f"DRY RUN: would torque-enable and drive ID {ID_1},{ID_2} to MiddlePos "
          f"({MiddlePos_1}, {MiddlePos_2}) deg at speed {SPEED}.")
    print("Set AH_BRINGUP_ARM=1 to actually move. Exiting without motion.")
    raise SystemExit(0)

# move to MiddlePos
c.write_torque_enable(ID_1, 1)
c.write_torque_enable(ID_2, 1)
c.write_goal_speed(ID_1, SPEED)
c.write_goal_speed(ID_2, SPEED)
c.write_goal_position(ID_1, np.deg2rad(MiddlePos_1))
c.write_goal_position(ID_2, np.deg2rad(MiddlePos_2))
time.sleep(3.5)  # allow a full large sweep (e.g. ~146 deg) to finish before readback

# read back to confirm arrival
for sid, target in ((ID_1, MiddlePos_1), (ID_2, MiddlePos_2)):
    try:
        print(f"after:  ID {sid} present = {_deg(sid):7.1f} deg   (target {target})")
    except Exception as e:
        print(f"after:  ID {sid} read failed: {e}")

print("Servos are HOLDING at MiddlePos (torque on). Fit the horns at this neutral.")
print("Power off the 5V when done (that releases them).")
