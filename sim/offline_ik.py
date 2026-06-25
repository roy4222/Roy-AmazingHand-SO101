#!/usr/bin/env python3
# AmazingHand — OFFLINE inverse kinematics (MuJoCo + mink), headless, no dora, no hardware.
#
# Reuses the OFFICIAL model (Demo/AHSimulation/.../AH_Right/mjcf/scene.xml) and the same mink
# QP-IK setup as Demo/AHSimulation/AHSimulation/mj_mink_right.py (closed-loop EqualityConstraint
# + posture + 4 orientation FrameTasks). Given a per-finger (flexion, abduction) target it solves
# for the 8 motor joint angles. This is how we get GEOMETRICALLY-correct large abduction /
# expressive trajectories that raw common-mode can't produce.
#
# Output motor angles are in the MODEL frame (radians). Mapping model->real-servo sign/offset is a
# later, hardware-gated calibration; here we only generate & inspect trajectories in sim.
#
# Usage:
#   python offline_ik.py --flex 0  --abd 20            # all fingers: flexion 0, abduction +20 deg
#   python offline_ik.py --sweep-abd 0:20:5 --flex 0   # sweep abduction, print motor angles
import argparse
import os
import numpy as np
import mujoco
import mink
from scipy.spatial.transform import Rotation

HERE = os.path.dirname(os.path.abspath(__file__))
SCENE = os.path.join(HERE, "..", "Demo", "AHSimulation", "AHSimulation", "AH_Right", "mjcf", "scene.xml")

TIPS = ["tip1", "tip2", "tip3", "tip4"]
MOTORS = [("finger1_motor1", "finger1_motor2"), ("finger2_motor1", "finger2_motor2"),
          ("finger3_motor1", "finger3_motor2"), ("finger4_motor1", "finger4_motor2")]


def build():
    model = mujoco.MjModel.from_xml_path(SCENE)
    config = mink.Configuration(model)
    tasks = [
        mink.EqualityConstraintTask(model, cost=1000.0),
        mink.PostureTask(model, cost=1e-2),
    ]
    frame_tasks = []
    for tip in TIPS:
        ft = mink.FrameTask(frame_name=tip, frame_type="site",
                            position_cost=0.0, orientation_cost=1.0, lm_damping=1.0)
        frame_tasks.append(ft)
        tasks.append(ft)
    return model, config, tasks, frame_tasks


def set_targets(config, frame_tasks, flex_deg, abd_deg):
    # target = rest tip orientation * relative(roll=abduction X, pitch=flexion Y)
    delta = Rotation.from_euler("XYZ", [np.radians(abd_deg), np.radians(flex_deg), 0.0])
    for tip, ft in zip(TIPS, frame_tasks):
        rest = config.get_transform_frame_to_world(tip, "site")
        rest_R = Rotation.from_matrix(rest.rotation().as_matrix())
        new_R = rest_R * delta
        ft.set_target(mink.SE3.from_rotation_and_translation(
            mink.SO3(np.roll(new_R.as_quat(), 1)), rest.translation()))  # scipy xyzw -> mink wxyz


def solve(config, tasks, frame_tasks, flex_deg, abd_deg, iters=200):
    config.update_from_keyframe("zero")
    tasks[1].set_target_from_configuration(config)  # posture = zero
    set_targets(config, frame_tasks, flex_deg, abd_deg)
    for _ in range(iters):
        vel = mink.solve_ik(config, tasks, 0.002, "quadprog", 1e-5)
        config.integrate_inplace(vel, 0.002)
    out = []
    for m1, m2 in MOTORS:
        out.append((float(np.degrees(config.data.joint(m1).qpos[0])),
                    float(np.degrees(config.data.joint(m2).qpos[0]))))
    return out


def flatten(res):
    """[(m1,m2)x4] -> [m1..m8] in servo-id order 1..8."""
    out = []
    for m1, m2 in res:
        out += [m1, m2]
    return out


def write_traj(path, rows, meta):
    """rows: list of (label, [m1..m8]). Writes CSV with a model-frame header."""
    with open(path, "w") as f:
        f.write(f"# amazinghand IK trajectory; frame=model; {meta}\n")
        f.write("label,m1,m2,m3,m4,m5,m6,m7,m8\n")
        for label, ang in rows:
            f.write(label + "," + ",".join(f"{a:.2f}" for a in ang) + "\n")
    print(f"wrote {len(rows)} frames -> {path}  (frame=model; calibrate model->servo before real hand)")


# predefined smooth trajectories: name -> list of (label, flex, abd)
def traj_keys(name):
    if name == "abd_wave":   # clean left/right sweep at neutral flexion (geometric max ~20)
        seq = [("right", 0, -20), ("mid", 0, 0), ("left", 0, +20), ("mid2", 0, 0)]
    elif name == "abd_wide":  # larger sweep, slightly past clean limit (mild curl coupling)
        seq = [("right", 0, -28), ("mid", 0, 0), ("left", 0, +28), ("mid2", 0, 0)]
    elif name == "flex_wave":  # curl in/out
        seq = [("open", -20, 0), ("mid", 0, 0), ("curl", 60, 0), ("mid2", 0, 0)]
    elif name == "diag":     # combined flexion+abduction corners
        seq = [("c1", -10, +15), ("c2", 40, +15), ("c3", 40, -15), ("c4", -10, -15)]
    else:
        raise SystemExit(f"unknown --traj {name}; choices: abd_wave, flex_wave, diag")
    return seq


# per-finger decode ratios (sim-derived): motor diff/common -> fingertip flexion/abduction (deg).
# index/middle/ring: flex≈diff/0.74 (abd≈-common/0.72); thumb mirrored: flex≈diff/-0.62, abd≈common/0.72.
DECODE = {0: (0.74, -0.72), 1: (0.74, -0.72), 2: (0.74, -0.72), 3: (-0.62, 0.72)}  # finger idx -> (flex_r, abd_r)


def preview(path):
    """Print a human-readable summary of an IK trajectory CSV (decode motors -> flex/abd est)."""
    print(f"# preview {path}  (~est fingertip deg decoded from model motors)")
    with open(path) as f:
        lines = [l.strip() for l in f if l.strip()]
    for line in lines:
        if line.startswith("#"):
            print(line)
            continue
        p = line.split(",")
        if p[0] == "label":
            continue
        ang = [float(x) for x in p[1:9]]
        cells = []
        for fi, nm in enumerate(["idx", "mid", "rng", "thb"]):
            m1, m2 = ang[fi * 2], ang[fi * 2 + 1]
            diff, common = (m1 - m2) / 2.0, (m1 + m2) / 2.0
            fr, ar = DECODE[fi]
            flex, abd = diff / fr, common / ar
            cells.append(f"{nm} flex{flex:+5.0f} abd{abd:+5.0f}")
        # one-line gist from the index finger (representative for whole-hand moves)
        d0 = (ang[0] - ang[1]) / 2.0
        c0 = (ang[0] + ang[1]) / 2.0
        gist = []
        if abs(c0) > 3:
            gist.append(f"{'LEFT' if -c0/0.72 > 0 else 'RIGHT'} ~{abs(c0)/0.72:.0f}°")
        if abs(d0) > 3:
            gist.append(f"{'CURL' if d0 > 0 else 'EXTEND'} ~{abs(d0)/0.74:.0f}°")
        print(f"  {p[0]:6s} | {'  '.join(cells)} | {' '.join(gist) or 'neutral'}")


def view(traj_name):
    """Open a MuJoCo 3D window (WSLg) and animate a trajectory in pure simulation. No hardware."""
    import time
    import mujoco.viewer
    model, config, tasks, frame_tasks = build()
    config.update_from_keyframe("zero")
    tasks[1].set_target_from_configuration(config)
    keys = traj_keys(traj_name)
    print(f"opening MuJoCo viewer: looping traj '{traj_name}' ({[k[0] for k in keys]}). Close window to stop.")
    with mujoco.viewer.launch_passive(config.model, config.data) as v:
        while v.is_running():
            for label, flex, abd in keys:
                set_targets(config, frame_tasks, flex, abd)
                for _ in range(140):
                    if not v.is_running():
                        break
                    vel = mink.solve_ik(config, tasks, 0.01, "quadprog", 1e-5)
                    config.integrate_inplace(vel, 0.01)
                    v.sync()
                    time.sleep(0.01)
                for _ in range(50):  # dwell
                    if not v.is_running():
                        break
                    v.sync()
                    time.sleep(0.01)


def render(traj_name, out_path, w=640, h=480, fps=30):
    """Offscreen-render an IK trajectory animation to MP4 (MUJOCO_GL=glfw). No hardware."""
    os.environ.setdefault("MUJOCO_GL", "glfw")
    import imageio.v2 as imageio
    model, config, tasks, frame_tasks = build()
    config.update_from_keyframe("zero")
    tasks[1].set_target_from_configuration(config)
    keys = traj_keys(traj_name)
    renderer = mujoco.Renderer(config.model, h, w)
    cam = mujoco.MjvCamera()
    cam.lookat[:] = [0.04, 0.0, 0.12]
    cam.distance, cam.azimuth, cam.elevation = 0.32, 160, -15
    frames = []
    for label, flex, abd in keys:
        set_targets(config, frame_tasks, flex, abd)
        for i in range(90):
            vel = mink.solve_ik(config, tasks, 0.01, "quadprog", 1e-5)
            config.integrate_inplace(vel, 0.01)
            if i % 3 == 0:
                renderer.update_scene(config.data, cam)
                frames.append(renderer.render())
        for _ in range(8):  # dwell
            renderer.update_scene(config.data, cam)
            frames.append(renderer.render())
    imageio.mimsave(out_path, frames, fps=fps)
    print(f"wrote {len(frames)} frames -> {out_path} ({w}x{h} @ {fps}fps, traj={traj_name})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flex", type=float, default=0.0)
    ap.add_argument("--abd", type=float, default=0.0)
    ap.add_argument("--sweep-abd", type=str, default="")  # start:stop:step
    ap.add_argument("--traj", type=str, default="")       # abd_wave|flex_wave|diag
    ap.add_argument("--out", type=str, default="")        # CSV path for sweep/traj
    ap.add_argument("--preview", type=str, default="")    # human-readable CSV summary
    ap.add_argument("--view", type=str, default="")        # open 3D viewer, animate traj (abd_wave|flex_wave|diag)
    ap.add_argument("--render", type=str, default="")       # offscreen-render traj to MP4
    ap.add_argument("--out-video", type=str, default="")    # MP4 path for --render
    args = ap.parse_args()

    if args.preview:
        preview(args.preview)
        return
    if args.view:
        view(args.view)
        return
    if args.render:
        render(args.render, args.out_video or f"ik_{args.render}.mp4")
        return

    model, config, tasks, frame_tasks = build()
    names = ["index", "middle", "ring", "thumb"]

    if args.traj:
        keys = traj_keys(args.traj)
        rows = []
        for label, flex, abd in keys:
            rows.append((label, [round(a, 2) for a in flatten(solve(config, tasks, frame_tasks, flex, abd))]))
            print(f"  {label:5s} flex={flex:+5.1f} abd={abd:+5.1f} -> {[round(x,1) for x in rows[-1][1]]}")
        out = args.out or f"ik_{args.traj}.csv"
        write_traj(out, rows, f"traj={args.traj}")
    elif args.sweep_abd:
        a, b, s = (float(x) for x in args.sweep_abd.split(":"))
        vals = np.arange(a, b + 1e-6, s)
        print(f"# sweep abduction {a}..{b} step {s}, flexion {args.flex} deg (motor angles deg)")
        print("abd_deg | " + " | ".join(f"{n}(m1,m2)" for n in names))
        rows = []
        for abd in vals:
            res = solve(config, tasks, frame_tasks, args.flex, abd)
            cells = " | ".join(f"({m1:+5.1f},{m2:+5.1f})" for m1, m2 in res)
            print(f"{abd:+6.1f} | {cells}")
            rows.append((f"abd{abd:+.0f}", [round(x, 2) for x in flatten(res)]))
        if args.out:
            write_traj(args.out, rows, f"sweep_abd={args.sweep_abd} flex={args.flex}")
    else:
        res = solve(config, tasks, frame_tasks, args.flex, args.abd)
        print(f"# flexion {args.flex} deg, abduction {args.abd} deg -> motor angles (deg)")
        for n, (m1, m2) in zip(names, res):
            print(f"  {n:7s} motor1={m1:+6.1f} motor2={m2:+6.1f}  (common={ (m1+m2)/2:+5.1f} diff={(m1-m2)/2:+5.1f})")


if __name__ == "__main__":
    main()
