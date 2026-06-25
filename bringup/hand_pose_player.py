# AmazingHand — SMOOTH pose-sequence player (interpolated, telemetry-monitored).
#
# Fixes the "moves but not fluid" problem: instead of hard-jumping between poses, it
# INTERPOLATES each transition over many small steps with cosine ease-in/ease-out, and
# periodically reads position/load/temperature/status to abort to a safe pose on over-limit.
#
# NOTE: SCS0009 (old Feetech protocol) does NOT support SYNC READ (sync_read_* times out),
# so this uses per-id read/write — same as the other bring-up scripts.
#
# Motion model (hw-verified): per finger (F,L) -> servo1=F+L, servo2=-F+L.
#   F=flexion(-30 extended..+90 curl), L=abduction(left+/right-). Abduction only shows
#   near neutral flexion. Air gestures only — no grasping.
#
# Knobs (env):
#   AH_PRESET motion rhythm: safe (default, stable demo) | natural (everyday) | snappy (short).
#             explicit AH_STEPS/AH_DT/AH_HOLD/AH_SPEED override the preset.
#   AH_SEQ    comma list of pose names (default a demo routine). `list` prints names.
#   AH_STEPS  interpolation steps per transition (8..60, default 28)
#   AH_DT     seconds per step (default 0.045 -> ~1.3 s/transition)
#   AH_SPEED  servo goal speed 1..6 (default 5; must track the sub-targets)
#   AH_HOLD   seconds to dwell at each pose (default 0.6)
#   AH_TEMP_ABORT  deg C hard abort (default 55)
#   AH_ERR_ABORT   deg tracking-error hard abort, checked at pose arrival (default 18)
#   AH_LOG    optional path to append per-sample telemetry CSV
#   AH_BRINGUP_ARM=1 required to move (bare run = DRY RUN).
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

# motion-rhythm presets (AH_PRESET); explicit AH_STEPS/AH_DT/AH_HOLD/AH_SPEED override.
PRESETS = {
    "safe":    dict(steps=40, dt=0.06,  hold=1.0,  speed=4),  # stable demo baseline (~2.4s/transition)
    "natural": dict(steps=30, dt=0.045, hold=0.6,  speed=5),  # everyday gestures (~1.35s)
    "snappy":  dict(steps=22, dt=0.03,  hold=0.35, speed=6),  # short demos; telemetry gate stays on
}
PRESET = os.environ.get("AH_PRESET", "safe").strip().lower()
_p = PRESETS.get(PRESET, PRESETS["safe"])
STEPS = max(8, min(60, int(os.environ.get("AH_STEPS", _p["steps"]))))
DT = float(os.environ.get("AH_DT", _p["dt"]))
SPEED = max(1, min(6, int(os.environ.get("AH_SPEED", _p["speed"]))))
HOLD = float(os.environ.get("AH_HOLD", _p["hold"]))
TEMP_ABORT = float(os.environ.get("AH_TEMP_ABORT", "55"))
ERR_ABORT = float(os.environ.get("AH_ERR_ABORT", "18"))
LOGPATH = os.environ.get("AH_LOG", "")

G = {
    "open":       {f: (-30, 0) for f in FINGERS},
    "neutral":    {f: (0, 0) for f in FINGERS},
    "fist":       {f: (+90, 0) for f in FINGERS},
    "relax":      {f: (+18, 0) for f in FINGERS},
    "claw":       {f: (+50, 0) for f in FINGERS},
    "wave_left":  {f: (0, +35) for f in FINGERS},
    "wave_right": {f: (0, -35) for f in FINGERS},
    "fan_spread": {"index": (0, +40), "middle": (0, +14), "ring": (0, -14), "thumb": (0, -40)},
    "fan_pinch":  {"index": (0, -16), "middle": (0, -5), "ring": (0, +5), "thumb": (0, +16)},
    "spock":      {"index": (0, +30), "middle": (0, +30), "ring": (0, -30), "thumb": (0, -30)},
    "point":      {"index": (-30, 0), "middle": (+90, 0), "ring": (+90, 0), "thumb": (+90, 0)},
    "midfinger":  {"index": (+90, 0), "middle": (-30, 0), "ring": (+90, 0), "thumb": (+90, 0)},
    "rock":       {"index": (-30, 0), "middle": (+90, 0), "ring": (+90, 0), "thumb": (-30, 0)},
    "victory":    {"index": (-25, 0), "middle": (-25, 0), "ring": (+90, 0), "thumb": (+90, 0)},
}
DEFAULT_SEQ = ["open", "wave_left", "wave_right", "neutral", "fan_spread", "fan_pinch",
               "spock", "point", "victory", "fist", "relax", "open"]


def _scalar(v):
    try:
        return v[0]
    except (TypeError, IndexError, KeyError):
        return v


def rd(reader):
    out = []
    for i in IDS:
        try:
            out.append(_scalar(reader(i)))
        except Exception:
            out.append(None)
    return out


def rd_pos_deg():
    return [None if v is None else float(np.rad2deg(v)) for v in rd(c.read_present_position)]


def servos(pose):
    out = {}
    for f in FINGERS:
        Fv, Lv = pose[f]
        i1, i2 = FID[f]
        out[i1] = max(-CLAMP, min(CLAMP, Fv + Lv))
        out[i2] = max(-CLAMP, min(CLAMP, -Fv + Lv))
    return out


def write_pose(targets):
    for i in IDS:
        c.write_goal_position(i, np.deg2rad(targets[i]))


def write_angles(arr):
    for k, i in enumerate(IDS):
        c.write_goal_position(i, np.deg2rad(arr[k]))


def lerp_ang(a, b, t):
    e = (1 - math.cos(math.pi * t)) / 2.0
    return [a[k] + (b[k] - a[k]) * e for k in range(8)]


def lerp_pose(a, b, t):
    e = (1 - math.cos(math.pi * t)) / 2.0  # cosine ease in/out
    return {f: (a[f][0] + (b[f][0] - a[f][0]) * e,
               a[f][1] + (b[f][1] - a[f][1]) * e) for f in FINGERS}


TRAJ = os.environ.get("AH_TRAJ", "")          # path to an IK trajectory CSV (label,m1..m8)
ALLOW_MODEL = os.environ.get("AH_ALLOW_MODEL") == "1"


def load_traj(path):
    """Return (frames, is_model). frames = [(label, [8 deg])]."""
    frames, is_model = [], False
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                if "frame=model" in line:
                    is_model = True
                continue
            parts = line.split(",")
            if parts[0] == "label":
                continue
            frames.append((parts[0], [float(x) for x in parts[1:9]]))
    return frames, is_model


seq = [s.strip() for s in os.environ.get("AH_SEQ", "").split(",") if s.strip()] or DEFAULT_SEQ
if not TRAJ:
    if seq == ["list"]:
        print("poses:", ", ".join(G))
        raise SystemExit(0)
    bad = [s for s in seq if s not in G]
    if bad:
        print(f"unknown poses {bad}. available: {', '.join(G)}")
        raise SystemExit(1)

c = Scs0009PyController(serial_port=SERIAL_PORT, baudrate=1000000, timeout=0.5)

pos0 = rd_pos_deg()
if any(p is None for p in pos0):
    print(f"ABORT: not all 8 servos responding: {pos0}")
    raise SystemExit(1)
traj_frames, traj_is_model = (load_traj(TRAJ) if TRAJ else ([], False))
mode = f"traj={TRAJ}({len(traj_frames)} frames, {'MODEL' if traj_is_model else 'servo'} frame)" if TRAJ else f"seq={seq}"
print(f"before: 8 servos present. preset={PRESET} {mode}  steps={STEPS} dt={DT} hold={HOLD} speed={SPEED}")

if os.environ.get("AH_BRINGUP_ARM") != "1":
    what = f"{len(traj_frames)} trajectory frames" if TRAJ else f"{len(seq)} poses"
    print(f"DRY RUN: would play {what} with {STEPS}-step cosine interpolation. No motion.")
    print("Set AH_BRINGUP_ARM=1 to actually move.")
    raise SystemExit(0)

# SAFETY: model-frame IK trajectories are NOT yet calibrated to real-servo sign/offset.
if TRAJ and traj_is_model and not ALLOW_MODEL:
    print("REFUSING to ARM a MODEL-frame trajectory on the real hand (signs/offsets uncalibrated).")
    print("Do sim->real calibration first; then set AH_ALLOW_MODEL=1 to override. (DRY RUN is always allowed.)")
    raise SystemExit(2)

logf = open(LOGPATH, "a") if LOGPATH else None
if logf and os.stat(LOGPATH).st_size == 0:
    logf.write("t,pose,id,cmd_deg,present_deg,err_deg,load,temp,status\n")
t_start = time.time()


def sample(label, targets):
    pos = rd_pos_deg()
    load = rd(c.read_present_load)
    temp = rd(c.read_present_temperature)
    status = rd(c.read_status)
    worst = 0.0
    hot = max([t for t in temp if t is not None], default=0)
    fault = any(s for s in status if s)
    for k, sid in enumerate(IDS):
        pdeg = pos[k]
        cmd = targets.get(sid, 0)
        err = abs(pdeg - cmd) if pdeg is not None else 0.0
        worst = max(worst, err)
        if logf:
            logf.write(f"{time.time()-t_start:.2f},{label},{sid},{cmd:.0f},"
                       f"{(pdeg if pdeg is not None else 0):.1f},{err:.1f},"
                       f"{load[k]},{temp[k]},{status[k]}\n")
    return worst, hot, fault


for sid in IDS:
    c.write_torque_enable(sid, 1)
    c.write_goal_speed(sid, SPEED)

aborted = None

if TRAJ:
    # trajectory playback: raw 8-angle frames, cosine-interpolated, telemetry-gated
    cur_ang = list(pos0)
    for label, frame in traj_frames:
        for s in range(1, STEPS + 1):
            write_angles(lerp_ang(cur_ang, frame, s / STEPS))
            time.sleep(DT)
        cur_ang = frame
        time.sleep(HOLD)
        tgt = {IDS[k]: frame[k] for k in range(8)}
        worst, hot, fault = sample(f"{label}", tgt)
        flag = "  <-- LIMIT" if (worst > ERR_ABORT or hot > TEMP_ABORT or fault) else ""
        print(f"{label:11s} worst_err={worst:.1f} hot={hot}C fault={fault}{flag}")
        if worst > ERR_ABORT or hot > TEMP_ABORT or fault:
            aborted = f"err {worst:.1f} / temp {hot} / fault {fault}"
            break
    # return to open smoothly (open in servo frame)
    open_ang = [servos(G["open"])[i] for i in IDS]
    for s in range(1, STEPS + 1):
        write_angles(lerp_ang(cur_ang, open_ang, s / STEPS))
        time.sleep(DT)
else:
    # start from current measured pose so the first transition is smooth, not a jump
    cur = {}
    for f in FINGERS:
        i1, i2 = FID[f]
        p1, p2 = pos0[IDS.index(i1)], pos0[IDS.index(i2)]
        cur[f] = ((p1 - p2) / 2.0, (p1 + p2) / 2.0)  # back out (F,L)
    for name in seq:
        target = G[name]
        for s in range(1, STEPS + 1):
            write_pose(servos(lerp_pose(cur, target, s / STEPS)))
            time.sleep(DT)
        cur = target
        time.sleep(HOLD)
        worst, hot, fault = sample(f"{name}", servos(target))
        flag = "  <-- LIMIT" if (worst > ERR_ABORT or hot > TEMP_ABORT or fault) else ""
        print(f"{name:11s} worst_err={worst:.1f} hot={hot}C fault={fault}{flag}")
        if worst > ERR_ABORT or hot > TEMP_ABORT or fault:
            aborted = f"err {worst:.1f} / temp {hot} / fault {fault}"
            break
    # return to a safe open pose smoothly
    for s in range(1, STEPS + 1):
        write_pose(servos(lerp_pose(cur, G["open"], s / STEPS)))
        time.sleep(DT)

if logf:
    logf.close()
n_played = len(traj_frames) if TRAJ else len(seq)
print(f"!! ABORTED ({aborted}) — returned to open." if aborted
      else f"Done: played {n_played} {'frames' if TRAJ else 'poses'} smoothly. Holding open."
           + (f" log={LOGPATH}" if LOGPATH else ""))
