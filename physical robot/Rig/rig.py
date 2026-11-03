"""
rig.py - RealSense D405 camera + Arduino rig control in one class.

    from rig import Rig

    with Rig("/dev/ttyACM0") as rig:
        color, depth_vis, depth_raw = rig.get_visual()
        rig.move_x(200)
        rig.move_z(-100)
        rig.dc_forward()    # sends "DC FORWARD"
        rig.dc_reverse()    # sends "DC REVERSE"
        rig.dc_stop()       # sends "DC STOP"
        rig.stop()          # sends "STOP"

Pass port=None to use the camera only, or camera=False for the rig only.
"""

import threading
import time

import numpy as np
import pyrealsense2 as rs
import serial

# ---- Settings you may need to change ---------------------------------------
BAUD_RATE = 115200

# Camera mode that works on USB 2 with the D405.
CAM_W, CAM_H, CAM_FPS = 480, 270, 15

# Arduino protocol (same as your original rig_control.py / keyboard code):
#   MOVE X <steps> <speed>    MOVE Z <steps> <speed>
#   DC FORWARD / DC REVERSE / DC STOP
#   STOP / STATUS
AXES = ("X", "Z")

MAX_COMMAND_STEPS = 10000
MAX_SPEED = 400       # your original move() limit
DEFAULT_SPEED = 100
# -----------------------------------------------------------------------------


class Rig:
    def __init__(self, port="/dev/ttyACM0", camera=True, print_arduino=True):
        self.print_arduino = print_arduino
        self.conn = None
        self.pipe = None
        self.dc_state = "stopped"   # stopped / forward / reverse
        self._lock = threading.Lock()
        self._stop_reader = threading.Event()
        self._reader = None

        if camera:
            self._start_camera()
        if port:
            self._start_serial(port)

    # ------------------------------------------------------------------ camera
    def _start_camera(self):
        self.pipe = rs.pipeline()
        cfg = rs.config()
        cfg.enable_stream(rs.stream.depth, CAM_W, CAM_H, rs.format.z16, CAM_FPS)
        cfg.enable_stream(rs.stream.color, CAM_W, CAM_H, rs.format.rgb8, CAM_FPS)
        profile = self.pipe.start(cfg)

        self.depth_scale = (
            profile.get_device().first_depth_sensor().get_depth_scale()
        )
        i = (profile.get_stream(rs.stream.color)
             .as_video_stream_profile().get_intrinsics())
        self.intrinsics = (i.width, i.height, i.fx, i.fy, i.ppx, i.ppy)
        self._colorizer = rs.colorizer()

    def get_visual(self, timeout_ms=5000):
        """
        Grab one frame set.
        Returns (color, depth_vis, depth_raw):
            color      HxWx3 uint8 RGB image
            depth_vis  HxWx3 uint8 RGB false-colour depth image
            depth_raw  HxW   uint16 raw depth (multiply by .depth_scale for metres)
        Returns None if the camera is not running or no frame arrived.
        """
        if self.pipe is None:
            return None
        frames = self.pipe.wait_for_frames(timeout_ms)
        d, c = frames.get_depth_frame(), frames.get_color_frame()
        if not d or not c:
            return None
        color = np.asanyarray(c.get_data()).copy()
        depth_raw = np.asanyarray(d.get_data()).copy()
        depth_vis = np.asanyarray(self._colorizer.colorize(d).get_data()).copy()
        return color, depth_vis, depth_raw

    def make_pointcloud(self, color, depth_raw, max_range_m=0.5):
        """Build an Open3D point cloud from a get_visual() result."""
        import open3d as o3d

        w, h, fx, fy, cx, cy = self.intrinsics
        pinhole = o3d.camera.PinholeCameraIntrinsic(w, h, fx, fy, cx, cy)
        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            o3d.geometry.Image(np.ascontiguousarray(color)),
            o3d.geometry.Image(np.ascontiguousarray(depth_raw)),
            depth_scale=1.0 / self.depth_scale,
            depth_trunc=max_range_m,
            convert_rgb_to_intensity=False,
        )
        pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd, pinhole)
        pcd.transform([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
        return pcd

    # ------------------------------------------------------------------ serial
    def _start_serial(self, port):
        self.conn = serial.Serial(
            port=port, baudrate=BAUD_RATE, timeout=0.2, write_timeout=2
        )
        time.sleep(2)  # Arduino resets when the port opens
        self.conn.reset_input_buffer()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self):
        while not self._stop_reader.is_set():
            try:
                if self.conn.in_waiting:
                    msg = self.conn.readline().decode("utf-8", "replace").strip()
                    if msg and self.print_arduino:
                        print(f"Arduino: {msg}")
                else:
                    time.sleep(0.02)
            except (serial.SerialException, OSError):
                break

    def send(self, command):
        """Send one newline-terminated line to the Arduino."""
        if self.conn is None:
            return
        with self._lock:
            self.conn.write((command + "\n").encode("ascii"))
            self.conn.flush()
        print(f"Sent: {command}")

    # ------------------------------------------------------------ rig commands
    def move(self, axis, steps, speed=DEFAULT_SPEED):
        """Relative move. axis is "X" or "Z"; sign of steps sets direction."""
        axis = axis.upper()
        if axis not in AXES:
            raise ValueError("axis must be X or Z")
        steps, speed = int(steps), int(speed)
        if steps == 0 or abs(steps) > MAX_COMMAND_STEPS:
            raise ValueError(f"steps must be non-zero and within {MAX_COMMAND_STEPS}")
        if not 0 < speed <= MAX_SPEED:
            raise ValueError(f"speed must be 1..{MAX_SPEED}")
        self.send(f"MOVE {axis} {steps} {speed}")

    def move_x(self, steps, speed=DEFAULT_SPEED):
        self.move("X", steps, speed)

    def move_z(self, steps, speed=DEFAULT_SPEED):
        self.move("Z", steps, speed)

    def dc_forward(self):
        self.send("DC FORWARD")
        self.dc_state = "forward"

    def dc_reverse(self):
        self.send("DC REVERSE")
        self.dc_state = "reverse"

    def dc_stop(self):
        self.send("DC STOP")
        self.dc_state = "stopped"

    def stop(self):
        self.send("STOP")

    def status(self):
        self.send("STATUS")

    # ----------------------------------------------------------------- cleanup
    def close(self):
        if self.conn is not None:
            try:
                self.stop()
                self.dc_stop()
                time.sleep(0.1)
            except (serial.SerialException, OSError):
                pass
            self._stop_reader.set()
            if self._reader:
                self._reader.join(timeout=1)
            self.conn.close()
            self.conn = None
        if self.pipe is not None:
            try:
                self.pipe.stop()
            except RuntimeError:
                pass
            self.pipe = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()