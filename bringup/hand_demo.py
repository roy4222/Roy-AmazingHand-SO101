# AmazingHand — LOOPING DEMO player (our (F,L) params, smooth, telemetry-safe).
#
# Plays a curated gesture sequence on repeat for demos. Cosine-interpolated transitions,
# per-pose temperature/fault check (auto-stop on over-limit), graceful Ctrl-C -> return to open.
# Gestures are OUR (F,L) model (NOT upstream raw angles). Air gestures only — no grasping.
#
# Knobs (env):
#   AH_LOOPS  number of full passes; 0 = INFINITE (default 0 = loop forever)
#   AH_SEQ    comma list of pose names (default a demo routine). `list` prints names.
#   AH_PRESET safe (default) | natural | snappy   (rhythm; explicit AH_STEPS/AH_DT/AH_HOLD override)
#   AH_TEMP_ABORT  deg C auto-stop (default 55)
#   AH_BRINGUP_ARM=1 required to move (bare run = DRY RUN).
# Stop: Ctrl-C (returns to open), or power off 5V.
import os
import math
import time
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
FINGERS = ["index", "middle", "ring", "thumb"]
IDS = [1, 2, 3, 4, 5, 6, 7, 8]
FID = {"index": (1, 2), "middle": (3, 4), "ring": (5, 6), "thumb": (7, 8)}
CLAMP = 120

PRESETS = {
    "safe":    dict(steps=40, dt=0.06,  hold=0.8, speed=4),
    "natural": dict(steps=30, dt=0.045, hold=0.5, speed=5),
    "snappy":  dict(steps=22, dt=0.03,  hold=0.3, speed=6),
}
PRESET = os.environ.get("AH_PRESET", "safe").strip().lower()
_p = PRESETS.get(PRESET, PRESETS["safe"])
STEPS = max(8, min(60, int(os.environ.get("AH_STEPS", _p["steps"]))))
DT = float(os.environ.get("AH_DT", _p["dt"]))
SPEED = max(1, min(6, int(os.environ.get("AH_SPEED", _p["speed"]))))
HOLD = float(os.environ.get("AH_HOLD", _p["hold"]))
LOOPS = int(os.environ.get("AH_LOOPS", "0"))          # 0 = infinite
TEMP_ABORT = float(os.environ.get("AH_TEMP_ABORT", "55"))

# (F, L) per finger. F=flexion(-30 extended..+90 curl), L=abduction(left+/right-).
# left/right gestures keep F~=0 (abduction only shows near neutral flexion).
G = {
    "open":       {f: (-30, 0) for f in FINGERS},
    "fist":       {f: (+90, 0) for f in FINGERS},
    "relax":      {f: (+18, 0) for f in FINGERS},
    "point":      {"index": (-30, 0), "middle": (+90, 0), "ring": (+90, 0), "thumb": (+90, 0)},
    "victory":    {"index": (-25, 0), "middle": (-25, 0), "ring": (+90, 0), "thumb": (+90, 0)},
    "spock":      {"index": (0, +30), "middle": (0, +30), "ring": (0, -30), "thumb": (0, -30)},
    "fan_spread": {"index": (0, +40), "middle": (0, +14), "ring": (0, -14), "thumb": (0, -40)},
    "wave_left":  {f: (0, +35) for f in FINGERS},
    "wave_right": {f: (0, -35) for f in FINGERS},
}
DEFAULT_SEQ = ["open", "fist", "open", "point", "victory", "spock",
               "fan_spread", "wave_left", "wave_right", "relax", "open"]


def _scalar(v):
    try:
        return v[0]
    except (TypeError, IndexError, KeyError):
        return v


def deg(sid):
    return float(np.rad2deg(_scalar(c.read_present_position(sid))))


def servos(pose):
    out = {}
    for f in FINGERS:
        Fv, Lv = pose[f]
        i1, i2 = FID[f]
        out[i1] = max(-CLAMP, min(CLAMP, Fv + Lv))
        out[i2] = max(-CLAMP, min(CLAMP, -Fv + Lv))
    return out


def write_pose(t):
    for i in IDS:
        c.write_goal_position(i, np.deg2rad(t[i]))


def lerp(a, b, t):
    e = (1 - math.cos(math.pi * t)) / 2.0
    return {f: (a[f][0] + (b[f][0] - a[f][0]) * e, a[f][1] + (b[f][1] - a[f][1]) * e) for f in FINGERS}


def hottest_fault():
    hot, fault = 0, False
    for i in IDS:
        try:
            hot = max(hot, _scalar(c.read_present_temperature(i)))
            if _scalar(c.read_status(i)):
                fault = True
        except Exception:
            pass
    return hot, fault


seq = [s.strip() for s in os.environ.get("AH_SEQ", "").split(",") if s.strip()] or DEFAULT_SEQ
if seq == ["list"]:
    print("poses:", ", ".join(G))
    raise SystemExit(0)
bad = [s for s in seq if s not in G]
if bad:
    print(f"unknown poses {bad}. available: {', '.join(G)}")
    raise SystemExit(1)

c = Scs0009PyController(serial_port=SERIAL_PORT, baudrate=1000000, timeout=0.5)
present = [deg(i) for i in IDS]  # also acts as power/census check (raises if a servo is silent)
loops_txt = "INFINITE" if LOOPS <= 0 else str(LOOPS)
print(f"demo: preset={PRESET} loops={loops_txt} seq={seq}")

if os.environ.get("AH_BRINGUP_ARM") != "1":
    print(f"DRY RUN: would loop {len(seq)} poses x {loops_txt} with {STEPS}-step interpolation. No motion.")
    print("Set AH_BRINGUP_ARM=1 to actually move. Stop a live demo with Ctrl-C.")
    raise SystemExit(0)

for i in IDS:
    c.write_torque_enable(i, 1)
    c.write_goal_speed(i, SPEED)

# back out current (F,L) so the first transition is smooth
cur = {}
for f in FINGERS:
    i1, i2 = FID[f]
    p1, p2 = present[IDS.index(i1)], present[IDS.index(i2)]
    cur[f] = ((p1 - p2) / 2.0, (p1 + p2) / 2.0)

stop = None
n = 0
try:
    while LOOPS <= 0 or n < LOOPS:
        n += 1
        for name in seq:
            target = G[name]
            for s in range(1, STEPS + 1):
                write_pose(servos(lerp(cur, target, s / STEPS)))
                time.sleep(DT)
            cur = target
            time.sleep(HOLD)
        hot, fault = hottest_fault()
        print(f"cycle {n} done  hot={hot}C fault={fault}")
        if hot > TEMP_ABORT or fault:
            stop = f"temp {hot}C / fault {fault}"
            break
except KeyboardInterrupt:
    stop = "Ctrl-C"

# always return to open smoothly
for s in range(1, STEPS + 1):
    write_pose(servos(lerp(cur, G["open"], s / STEPS)))
    time.sleep(DT)
print(f"!! demo stopped ({stop}) — returned to open." if stop
      else f"demo done: {n} loops. Holding open.")
