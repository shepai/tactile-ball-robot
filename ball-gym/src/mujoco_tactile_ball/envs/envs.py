from .base import TactileGymEnv
import mujoco 
from scipy.spatial.transform import Rotation as R
import numpy as np

class FlatTerrain(TactileGymEnv):
    def __init__(self):
        super().__init__(
            xml_subpath=["assets","flat.xml"],
            obs_dim=9,
            action_dim=3
        )

class Terrain(TactileGymEnv):
    def __init__(self):
        super().__init__(
            xml_subpath=["assets", "terrain.xml"],
            obs_dim=9,
            action_dim=3
        )

class Maze(TactileGymEnv):
    def __init__(self):
        super().__init__(
            xml_subpath=["assets", "maze.xml"],
            obs_dim=9,
            action_dim=3
        )

class Rig(TactileGymEnv):
    def __init__(self):
        super().__init__(
            xml_subpath=["assets", "move.xml"],
            obs_dim=9,
            action_dim=3
        )
        self.set_texture(1)
    def control_robot_speed(self, target_left_w, max_allowed_speed=10.0):
        # 1. Enforce safety speed ceiling
        max_target = abs(target_left_w)
        if max_target > max_allowed_speed:
            scale_factor = max_allowed_speed / max_target
            target_left_w *= scale_factor
        # 2. Write targets directly to MuJoCo's implicit velocity servos
        self.data.actuator('left_motor').ctrl[0] = target_left_w
    def _get_obs(self):
        opt_front=self.set_visibility([2])
        self.renderer.update_scene(self.data, camera="sensor_cam_left", scene_option=opt_front)
        Limg = self.renderer.render()
        Limg = Limg.astype("float32") / 255.0
        opt_front=self.set_visibility([1,0,2])
        self.renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SKYBOX] = 1
        obs = {
        "state": None,
        "sensor_cam_left": Limg

    }
        return obs
    def step(self,action):
        target_pos = np.array(action[0:3], dtype=np.float64)
        target_euler = np.array(action[3:6], dtype=np.float64) 
        self.control_robot_speed(action[-1])
        rotation = R.from_euler('xyz', target_euler)
        quat_xyzw = rotation.as_quat()
        target_quat = [quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]
        mocap_id = self.model.body_mocapid[self.model.body("robot").id]
        self.data.mocap_pos[mocap_id] = target_pos
        self.data.mocap_quat[mocap_id] = target_quat
        mujoco.mj_step(self.model, self.data)
        self.step_count += 1

        obs = self._get_obs()
        reward = self._reward()
        terminated = self._done()
        truncated = self.step_count >= self.max_steps

        return obs, reward, terminated, truncated, {}
    def set_texture(self,texture_id):
        texture_geoms = [
            "texture_geom_1",
            "texture_geom_2",
            "texture_geom_3",
            "texture_geom_4",
            "texture_geom_5",
            "texture_geom_6",
        ]
        for i, name in enumerate(texture_geoms):
            geom_id = mujoco.mj_name2id(
                self.model,
                mujoco.mjtObj.mjOBJ_GEOM,
                name
            )

            if i == texture_id:
                # visible + collidable
                self.model.geom_rgba[geom_id][3] = 1.0
                self.model.geom_contype[geom_id] = 1
                self.model.geom_conaffinity[geom_id] = 1

            else:
                # invisible + no collision
                self.model.geom_rgba[geom_id][3] = 0.0
                self.model.geom_contype[geom_id] = 0
                self.model.geom_conaffinity[geom_id] = 0
    def get_markers(self):
        marker_geoms = []
        for i in range(self.model.ngeom):
            name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, i)
            
            if name is not None and "marker" in name.lower():
                marker_geoms.append(self.data.geom_xpos[i].copy())
        return marker_geoms
class RandomTerrain(TactileGymEnv):
    pass