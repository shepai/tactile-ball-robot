"""
keyboard_rig.py - live camera view (2D + 3D) with keyboard control of the rig.

Usage:  python keyboard_rig.py [serial_port]      (default /dev/ttyACM0)

Keys work when EITHER window (2D image or 3D point cloud) has focus.
Number keys (top row or numpad), same as your original controller:

    1 / 2       X axis  - / +
    3 / 4       Z axis  - / +
    5           DC motor forward
    6           DC motor reverse
    7           DC motor stop
    Space       STOP (all)
    [ / ]       smaller / bigger step
    - / =       slower / faster
    Q or Esc    quit (also closing either window)

Every key press prints "Key: ..." in the terminal, so you can see whether
keys are arriving. If "Key:" prints but nothing moves, it's the serial side.
"""

import os
import sys
import time

# Avoid the GTK/GSettings abort (VS Code snap + Wayland) before any GUI import.
os.environ.pop("WAYLAND_DISPLAY", None)
os.environ["XDG_SESSION_TYPE"] = "x11"
os.environ["GDK_BACKEND"] = "x11"
for v in ("GSETTINGS_SCHEMA_DIR", "GTK_PATH", "GTK_EXE_PREFIX",
          "GTK_IM_MODULE_FILE", "GTK_MODULES"):
    os.environ.pop(v, None)

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import open3d as o3d

from rig import Rig

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM1"

# key -> (axis, direction)
MOVE_KEYS = {
    "1": ("X", -1),
    "2": ("X", +1),
    "3": ("Z", -1),
    "4": ("Z", +1),
}

step = 100            # steps per key press
speed = 100           # steps/sec (max 400)
MIN_INTERVAL = 0.08   # seconds between moves (limits key auto-repeat flooding)
last_cmd = 0.0
quit_flag = False

# Free up matplotlib's built-in shortcuts so they don't clash with ours.
for k in list(plt.rcParams):
    if k.startswith("keymap."):
        plt.rcParams[k] = []


def set_title():
    fig.suptitle(f"step={step}  speed={speed}  DC={rig.dc_state}", fontsize=10)


def handle_key(key):
    """Shared by the matplotlib and Open3D windows."""
    global step, speed, last_cmd, quit_flag
    key = (key or "").lower()
    if key.startswith("kp_"):          # numpad, e.g. "kp_5" -> "5"
        key = key[3:]
    print(f"Key: {key!r}")

    if key in ("q", "escape"):
        quit_flag = True
    elif key in MOVE_KEYS:
        now = time.time()
        if now - last_cmd >= MIN_INTERVAL:
            axis, sign = MOVE_KEYS[key]
            rig.move(axis, sign * step, speed)
            last_cmd = now
    elif key == "5":
        rig.dc_forward()
    elif key == "6":
        rig.dc_reverse()
    elif key == "7":
        rig.dc_stop()
    elif key == " ":
        rig.stop()
    elif key == "]":
        step = min(step * 2, 2000)
    elif key == "[":
        step = max(step // 2, 5)
    elif key == "=":
        speed = min(speed + 50, 400)
    elif key == "-":
        speed = max(speed - 50, 50)
    set_title()


# GLFW key codes for the Open3D window -> our key names
O3D_KEYS = {256: "escape", 32: " ", 91: "[", 93: "]", 45: "-", 61: "=", ord("Q"): "q"}
for d in range(10):
    O3D_KEYS[ord(str(d))] = str(d)     # top-row digits
    O3D_KEYS[320 + d] = str(d)         # numpad digits


with Rig(PORT) as rig:
    w, h = rig.intrinsics[0], rig.intrinsics[1]

    plt.ion()
    fig, ax = plt.subplots(figsize=(9, 4))
    im = ax.imshow(np.zeros((h, w * 2, 3), np.uint8))
    ax.axis("off")
    fig.canvas.mpl_connect("key_press_event", lambda e: handle_key(e.key))
    set_title()
    plt.tight_layout()

    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window("Point cloud", 800, 600)
    for code, name in O3D_KEYS.items():
        vis.register_key_callback(code, lambda v, n=name: handle_key(n) or False)
    pcd = o3d.geometry.PointCloud()
    added = False

    print("Ready. Click either window, then use the keys.")
    try:
        while plt.fignum_exists(fig.number) and not quit_flag:
            result = rig.get_visual()
            if result is None:
                continue
            color, depth_vis, depth_raw = result

            im.set_data(np.hstack((color, depth_vis)))
            fig.canvas.draw_idle()
            fig.canvas.flush_events()   # process keyboard/mouse events

            new = rig.make_pointcloud(color, depth_raw, max_range_m=0.5)
            pcd.points, pcd.colors = new.points, new.colors
            if not added:
                vis.add_geometry(pcd)
                added = True
            else:
                vis.update_geometry(pcd)
            if not vis.poll_events():
                break
            vis.update_renderer()
    finally:
        vis.destroy_window()
        plt.close("all")
# Rig.__exit__ sends STOP + spin off, then closes the camera and serial port.