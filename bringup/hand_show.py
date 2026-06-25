# AmazingHand bring-up — 10 CUSTOM gestures, composed from the CONFIRMED motion model.
#
# Confirmed by hardware probe (finger_probe.py, 2026-06-25):
#   two servos COUNTER-rotate (opposite sign) -> FLEXION  (curl up/down)
#   two servos CO-rotate      (same sign)      -> ABDUCTION (left/right)
#
# So per finger we specify (F, L):  F = flexion (curl), L = abduction (sideways), and
#   servo1 = F + L ,  servo2 = -F + L      (diff = 2F = flexion, common = 2L = abduction)
#   F: -30 (extended/straight) .. +90 (full curl)        L: -30 (right) .. +30 (left)
#
# Runs ONE gesture (AH_GESTURE=name) or ALL in sequence (default). Readback + bind-abort.
#
# Knobs: AH_GESTURE (a name, or 'all'), AH_SPEED 1..6 (default 4), AH_HOLD sec (default 1.2).
# Guard AH_BRINGUP_ARM=1. Without it: DRY RUN.
import os
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
FINGERS = ["index", "middle", "ring", "thumb"]
IDS = {"index": (1, 2), "middle": (3, 4), "ring": (5, 6), "thumb": (7, 8)}
CLAMP = 120

SPEED = max(1, min(6, int(os.environ.get("AH_SPEED", "4"))))
HOLD = float(os.environ.get("AH_HOLD", "1.2"))
SETTLE = 1.4
BIND_ABORT = 16.0

# Each gesture: {finger: (F, L)}  F=flexion(curl), L=abduction(left+/right-)
# KEY (hw-verified 2026-06-25): abduction (left/right) only has real amplitude near NEUTRAL
# flexion (F~=0). Extended/curled fingers lock out left/right. So all left/right gestures
# keep F~=0; flexion gestures use F as needed.
GESTURES = {
    # --- left/right gestures: fingers at NEUTRAL (F=0) so abduction is visible ---
    "wave_left":  {f: (0, +35) for f in FINGERS},          # whole hand leans left
    "wave_right": {f: (0, -35) for f in FINGERS},          # whole hand leans right
    "fan_spread": {"index": (0, +40), "middle": (0, +14), "ring": (0, -14), "thumb": (0, -40)},  # fan apart
    "fan_pinch":  {"index": (0, -16), "middle": (0, -5),  "ring": (0, +5),  "thumb": (0, +16)},  # converge
    "spock":      {"index": (0, +30), "middle": (0, +30), "ring": (0, -30), "thumb": (0, -30)},  # split 2+2
    # --- flexion gestures ---
    "claw":       {f: (+50, 0) for f in FINGERS},          # half-curled claw
    "fist":       {f: (+90, 0) for f in FINGERS},          # full fist
    "point":      {"index": (-30, 0), "middle": (+90, 0), "ring": (+90, 0), "thumb": (+90, 0)},
    "rock":       {"index": (-30, 0), "middle": (+90, 0), "ring": (+90, 0), "thumb": (-30, 0)},  # 🤘
    "relax":      {f: (+18, 0) for f in FINGERS},          # natural slight curl
    # clean V (index+middle up, ring+thumb curled) — for AH_SWAY note: V fingers are extended
    # so its left/right is limited; use wave_left/right or a NEUTRAL base for big sway.
    "victory":    {"index": (-25, 0), "middle": (-25, 0), "ring": (+90, 0), "thumb": (+90, 0)},
    "neutral":    {f: (0, 0) for f in FINGERS},            # flat neutral — best base for AH_SWAY
}
ORDER = ["wave_left", "wave_right", "fan_spread", "fan_pinch", "spock",
         "claw", "fist", "point", "rock", "relax"]

# The upstream 10 gesture POSES, rebuilt in OUR (F,L) model (NOT upstream raw angles).
# F=flexion(-30 extended .. +90 curl), L=abduction(left+/right-). Air gestures only.
OFFICIAL = {
    "open":     {f: (-35, 0) for f in FINGERS},
    "fist":     {f: (+90, 0) for f in FINGERS},
    "point":    {"index": (-35, 0),  "middle": (+90, 0), "ring": (+90, 0), "thumb": (+90, 0)},
    "midfinger":{"index": (+90, 0),  "middle": (-35, 0), "ring": (+90, 0), "thumb": (+90, 0)},
    "victory":  {"index": (-32, +30),"middle": (-32, -30),"ring": (+90, 0), "thumb": (+90, 0)},
    "spread":   {"index": (-35, +45),"middle": (-35, +15),"ring": (-35, -15),"thumb": (-35, -45)},
    "clench":   {f: (+72, 0) for f in FINGERS},
    "perfect":  {"index": (+60, -15),"middle": (-35, 0), "ring": (-35, 0),  "thumb": (+60, +15)},
    "pinch":    {"index": (+85, 0),  "middle": (+90, 0), "ring": (+90, 0),  "thumb": (+60, -28)},
    "scissors": {"index": (-32, +40),"middle": (-32, -40),"ring": (+90, 0), "thumb": (+90, 0)},
}
ORDER_OFFICIAL = ["open", "fist", "point", "midfinger", "victory",
                  "spread", "clench", "perfect", "pinch", "scissors"]

# pick gesture set: AH_SET=custom (default) | official
SETS = {"custom": (GESTURES, ORDER), "official": (OFFICIAL, ORDER_OFFICIAL)}
SET = os.environ.get("AH_SET", "custom").strip().lower()
GESTURES, ORDER = SETS.get(SET, (GESTURES, ORDER))

OPEN = {f: (-30, 0) for f in FINGERS}

# optional left/right sway: add a common-mode abduction offset (L) to EVERY finger
SWAY = max(0, min(60, int(os.environ.get("AH_SWAY", "0"))))   # 0 = no sway; else amplitude
SWAYS = max(1, min(20, int(os.environ.get("AH_SWAYS", "5"))))


def with_L(g, dL):
    return {f: (g[f][0], g[f][1] + dL) for f in FINGERS}


def _scalar(v):
    try:
        return v[0]
    except (TypeError, IndexError, KeyError):
        return v


def _deg(sid):
    return float(np.rad2deg(_scalar(c.read_present_position(sid))))


def _clamp(x):
    return max(-CLAMP, min(CLAMP, x))


def goto(g):
    tgt = {}
    for f in FINGERS:
        F, L = g[f]
        id1, id2 = IDS[f]
        a, b = _clamp(F + L), _clamp(-F + L)
        tgt[f] = (a, b)
        c.write_goal_position(id1, np.deg2rad(a))
        c.write_goal_position(id2, np.deg2rad(b))
    time.sleep(SETTLE)
    return tgt


def report(name, tgt):
    worst = 0.0
    cells = []
    for f in FINGERS:
        id1, id2 = IDS[f]
        ta, tb = tgt[f]
        p1, p2 = _deg(id1), _deg(id2)
        worst = max(worst, abs(p1 - ta), abs(p2 - tb))
        cells.append(f"{f[0]}=({p1:+5.0f},{p2:+5.0f})")
    flag = "  <-- CHECK" if worst > 8 else ""
    print(f"{name:11s} {'  '.join(cells)}  worst={worst:.1f}{flag}")
    return worst


sel = os.environ.get("AH_GESTURE", "all").strip().lower()
if sel != "all" and sel not in GESTURES:
    print(f"unknown AH_GESTURE={sel}. choices: all, {', '.join(ORDER)}")
    raise SystemExit(1)
todo = ORDER if sel == "all" else [sel]

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
print(f"before: all 8 present. running: {', '.join(todo)}")

if os.environ.get("AH_BRINGUP_ARM") != "1":
    print(f"DRY RUN: would run {len(todo)} gesture(s) at speed {SPEED}. No motion.")
    print("Set AH_BRINGUP_ARM=1 to actually move.")
    raise SystemExit(0)

for sid in range(1, 9):
    c.write_torque_enable(sid, 1)
    c.write_goal_speed(sid, SPEED)

aborted = False

if SWAY > 0 and len(todo) == 1:
    # hold the gesture and sway it left/right (common-mode abduction, OUR model)
    name = todo[0]
    base = GESTURES[name]
    print(f"sway '{name}' left/right +/-{SWAY} (abduction common-mode), x{SWAYS}")
    report("base", goto(base))
    time.sleep(0.4)
    seq = []
    for i in range(1, SWAYS + 1):
        seq.append((f"left #{i}", +SWAY))
        seq.append((f"right #{i}", -SWAY))
    for label, dL in seq:
        if report(label, goto(with_L(base, dL))) > BIND_ABORT:
            print(f"  !! bind, aborting")
            aborted = True
            break
    goto(base)
else:
    for name in todo:
        if report(name, goto(GESTURES[name])) > BIND_ABORT:
            print(f"  !! bind on '{name}', aborting")
            aborted = True
            break
        time.sleep(HOLD)
        if len(todo) > 1:
            goto(OPEN)  # reset between gestures for clarity
            time.sleep(0.4)
    goto(OPEN)

print("!! stopped early." if aborted else f"Done: {len(todo)} custom gesture(s).")
