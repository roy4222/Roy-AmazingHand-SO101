# AmazingHand bring-up — hold a GESTURE and sway it LEFT/RIGHT (abduction offset).
#
# Goes to a base gesture (e.g. victory), then adds a same-direction abduction offset to
# every finger's two servos and rocks left<->right around the pose, SWAYS times. The whole
# shape waves sideways. Reads back all 8; auto-aborts to MIDDLE on bind.
#
#   base   = gesture pose (per finger a,b)
#   left   = base + (+AMP, +AMP)        right = base + (-AMP, -AMP)
#
# Abduction offset >20 deg is past the real range (raw). Curled fingers + offset bind more
# easily, so default AMP is modest; the err>BIND abort returns everything to middle.
#
# Knobs (env): AH_GESTURE (default victory), AH_AMP 5..40 (default 18),
#              AH_SWAYS 1..20 (default 4), AH_SPEED 1..6 (default 4).
# Guard AH_BRINGUP_ARM=1. Without it: DRY RUN.
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
FINGERS = {"index": (1, 2), "middle": (3, 4), "ring": (5, 6), "thumb": (7, 8)}
CLAMP = 125  # deg, keep servo goals well inside SCS0009 travel

GESTURES = {
    "open":    {"index": (-35, 35), "middle": (-35, 35), "ring": (-35, 35), "thumb": (-35, 35)},
    "close":   {"index": (90, -90), "middle": (90, -90), "ring": (90, -90), "thumb": (90, -90)},
    "point":   {"index": (-40, 40), "middle": (90, -90), "ring": (90, -90), "thumb": (90, -90)},
    "victory": {"index": (-15, 65), "middle": (-65, 15), "ring": (90, -90), "thumb": (90, -90)},
    "spread":  {"index": (4, 90),   "middle": (-32, 32), "ring": (-90, -4), "thumb": (-90, -4)},
}

NAME = os.environ.get("AH_GESTURE", "victory").strip().lower()
AMP = max(5, min(40, int(os.environ.get("AH_AMP", "18"))))
SWAYS = max(1, min(20, int(os.environ.get("AH_SWAYS", "4"))))
SPEED = max(1, min(6, int(os.environ.get("AH_SPEED", "4"))))
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


def goto(base, off):
    targets = {}
    for finger, (id1, id2) in FINGERS.items():
        a, b = base[finger]
        ta, tb = _clamp(a + off), _clamp(b + off)
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


if NAME not in GESTURES:
    print(f"unknown AH_GESTURE={NAME}. choices: {', '.join(GESTURES)}")
    raise SystemExit(1)
base = GESTURES[NAME]

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
print(f"before: all 8 servos present. base='{NAME}', sway +/-{AMP} deg x{SWAYS}")
if AMP > 20:
    print(f"note: sway +/-{AMP} > real ~+/-20 abduction range (raw).")

if os.environ.get("AH_BRINGUP_ARM") != "1":
    print(f"DRY RUN: would hold '{NAME}' and sway left/right +/-{AMP} deg, {SWAYS}x, speed {SPEED}. No motion.")
    print("Set AH_BRINGUP_ARM=1 to actually move.")
    raise SystemExit(0)

for sid in range(1, 9):
    c.write_torque_enable(sid, 1)
    c.write_goal_speed(sid, SPEED)

# settle into the base pose first
report("base", goto(base, 0))

seq = []
for i in range(1, SWAYS + 1):
    seq.append((f"left #{i}", +AMP))
    seq.append((f"right #{i}", -AMP))

aborted = False
for label, off in seq:
    if report(label, goto(base, off)) > BIND_ABORT:
        aborted = True
        break

if aborted:
    goto(GESTURES["open"], 0)
    print("!! BIND DETECTED — stopped, returned to OPEN.")
else:
    report("back", goto(base, 0))
    print(f"Done: '{NAME}' swayed left/right {SWAYS}x. Holding pose. Run AH_GESTURE=open hand_gesture.py to reset.")
