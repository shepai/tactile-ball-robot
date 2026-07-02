import gymnasium as gym
import numpy as np
from gymnasium import spaces
from mujoco import MjModel, MjData
from mujoco import mj_step, mj_resetData, mj_forward
from importlib.resources import files
from mujoco import renderer

class TactileGymEnv(gym.Env):
    """
    Shared MuJoCo + Gym logic for all tactile environments.
    """

    def __init__(self, xml_subpath, obs_dim, action_dim):
        super().__init__()

        self.xml_path = files("mujoco_tactile_ball").joinpath(*xml_subpath)

        self.model = MjModel.from_xml_path(str(self.xml_path))
        self.data = MjData(self.model)

        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(action_dim,), dtype=np.float32
        )

        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )
        self.renderer = renderer.Renderer(self.model,height=480, width=640)
        self.step_count = 0
        self.max_steps = 200
    def control_robot_speed(self, target_left_w, target_right_w, max_allowed_speed=10.0):
        # 1. Enforce safety speed ceiling
        max_target = max(abs(target_left_w), abs(target_right_w))
        if max_target > max_allowed_speed:
            scale_factor = max_allowed_speed / max_target
            target_left_w *= scale_factor
            target_right_w *= scale_factor

        # 2. Write targets directly to MuJoCo's implicit velocity servos
        self.data.actuator('left_motor').ctrl[0] = target_left_w
        self.data.actuator('right_motor').ctrl[0] = target_right_w
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mj_resetData(self.model, self.data)
        self.step_count = 0
        return self._get_obs(), {}

    def step(self, action):
        mj_forward(self.model, self.data)
        self.control_robot_speed(*action)
        mj_step(self.model, self.data)
        self.step_count += 1

        obs = self._get_obs()
        reward = self._reward()
        terminated = self._done()
        truncated = self.step_count >= self.max_steps

        return obs, reward, terminated, truncated, {}

    def _get_obs(self):
        self.renderer.update_scene(self.data, camera="front_cam")
        img = self.renderer.render()
        img = img.astype("float32") / 255.0
        self.renderer.update_scene(self.data, camera="sensor_cam_left")
        Limg = self.renderer.render()
        Limg = Limg.astype("float32") / 255.0
        self.renderer.update_scene(self.data, camera="sensor_cam_right")
        Rimg = self.renderer.render()
        Rimg = Rimg.astype("float32") / 255.0
        obs = {
        "state": None,
        "sensor_cam_left": Limg,
        "sensor_cam_right": Rimg,
        "front_cam": img,
    }
        return obs

    def _reward(self):
        return np.random.randint(0,10)

    def _done(self):
        return False