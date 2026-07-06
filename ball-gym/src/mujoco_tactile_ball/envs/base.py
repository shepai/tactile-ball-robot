import gymnasium as gym
import numpy as np
from gymnasium import spaces
from mujoco import MjModel, MjData
from mujoco import mj_resetData
from importlib.resources import files
from mujoco import renderer
import mujoco 

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
    def is_robot_touching_floor(self):
        # Get the base robot body ID
        robot_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "robot")
        
        # Scan every body in your robot
        for body_idx in range(self.model.nbody):
            is_part_of_robot = (body_idx == robot_id) or (self.model.body_parentid[body_idx] == robot_id)
            
            if is_part_of_robot:
                part_z = self.data.xpos[body_idx][2]
                
                if part_z < 0.1: 
                    return True
                    
        return False
    def step(self, action):
        body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "robot")
        mujoco.mj_forward(self.model, self.data)
        self.control_robot_speed(action[0], action[1])
        
        if action[-1] == 1 and self.is_robot_touching_floor(): 
            for jnt_id in range(self.model.njnt):
                qpos_adr = self.model.jnt_qposadr[jnt_id]
                if self.model.jnt_type[jnt_id] == mujoco.mjtJoint.mjJNT_FREE:
                    #self.data.qpos[qpos_adr + 2] += 0.2  # Move free joint Z up
                    self.data.qvel[self.model.jnt_dofadr[jnt_id] + 2] = 1
            
            body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "robot")

            self.model.body_pos[body_id][2] += 0.5  # Lift structural Z axis
            
            mujoco.mj_forward(self.model, self.data)

        mujoco.mj_step(self.model, self.data)
        self.step_count += 1

        obs = self._get_obs()
        reward = self._reward()
        terminated = self._done()
        truncated = self.step_count >= self.max_steps

        return obs, reward, terminated, truncated, {}
    def set_visibility(self, visible_ids):
        for i in range(self.model.ngeom):
            self.model.geom_rgba[i][3] = 0.0
        for i in visible_ids:
            self.model.geom_rgba[i][3] = 1.0
    def _get_obs(self):
        self.renderer.update_scene(self.data, camera="front_cam")
        img = self.renderer.render()
        img = img.astype("float32") / 255.0
        all_geom_ids = np.arange(self.model.ngeom)
        self.model.tendon_rgba[:, 3] = 0.0
        self.set_visibility([])
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
        self.set_visibility(all_geom_ids)
        self.model.tendon_rgba[:, 3] = 1
        return obs

    def _reward(self):
        return np.random.randint(0,10)

    def _done(self):
        return False