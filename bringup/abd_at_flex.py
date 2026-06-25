# AmazingHand bring-up — does ABDUCTION (left/right) depend on the FLEXION state?
#
# Hypothesis: the parallel mechanism only has visible left/right (abduction) near NEUTRAL
# flexion; when the finger is extended or fully curled, abduction authority drops.
#
# Test: on one finger, sway abduction L = +/-AMP (common-mode) at three flexion offsets F,
# slowly, with banners. WATCH which F shows the most left/right.
#   servo1 = F + L ,  servo2 = -F + L
#
# Knobs: AH_ID1/AH_ID2 (default 1,2), AH_AMP (default 35), AH_REPS (default 3),
#        AH_SPEED (default 2), AH_PAUSE (default 1.3). Guard AH_BRINGUP_ARM=1.
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
ID_1 = int(os.environ.get("AH_ID1", "1"))
ID_2 = int(os.environ.get("AH_ID2", "2"))
AMP = max(10, min(45, int(os.environ.get("AH_AMP", "35"))))
REPS = max(1, min(8, int(os.environ.get("AH_REPS", "3"))))
SPEED = max(1, min(6, int(os.environ.get("AH_SPEED", "2"))))
PAUSE = float(os.environ.get("AH_PAUSE", "1.3"))
SETTLE = 1.5
CLAMP = 120
FLEX_STATES = [("EXTENDED  F=-35", -35), ("NEUTRAL   F=  0", 0), ("CURLED    F=+45", +45)]


def _scalar(v):
    try:
        return v[0]
    except (TypeError, IndexError, KeyError):
        return v


def _deg(sid):
    return float(np.rad2deg(_scalar(c.read_present_position(sid))))


def _clamp(x):
    return max(-CLAMP, min(CLAMP, x))


def goto(F, L):
    a, b = _clamp(F + L), _clamp(-F + L)
    c.write_goal_position(ID_1, np.deg2rad(a))
    c.write_goal_position(ID_2, np.deg2rad(b))
    time.sleep(SETTLE)
    return _deg(ID_1), _deg(ID_2), a, b


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
print(f"before: ID {ID_1},{ID_2} present. abduction sway +/-{AMP} at F=-35/0/+45")

if os.environ.get("AH_BRINGUP_ARM") != "1":
    print("DRY RUN: would sway abduction at 3 flexion states. No motion.")
    raise SystemExit(0)

c.write_torque_enable(ID_1, 1)
c.write_torque_enable(ID_2, 1)
c.write_goal_speed(ID_1, SPEED)
c.write_goal_speed(ID_2, SPEED)

for label, F in FLEX_STATES:
    print(f"\n######## {label}  (sway L=+/-{AMP}) ########")
    goto(F, 0)
    time.sleep(PAUSE)
    for r in range(1, REPS + 1):
        for side, L in (("left", +AMP), ("right", -AMP)):
            p1, p2, a, b = goto(F, L)
            print(f"  {label} #{r} {side:5s} cmd=({a:+4d},{b:+4d}) present=({p1:+6.1f},{p2:+6.1f})")
            time.sleep(PAUSE)
    goto(F, 0)

goto(0, 0)
print("\nDone. >>> Which flexion state (EXTENDED / NEUTRAL / CURLED) showed the most LEFT-RIGHT?")
