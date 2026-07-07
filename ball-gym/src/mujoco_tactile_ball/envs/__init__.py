
from gymnasium.envs.registration import register

register(
    id="Flat-tactile-ball",
    entry_point="mujoco_tactile_ball.envs.envs:FlatTerrain",
)

register(
    id="Random-tactile-ball",
    entry_point="mujoco_tactile_ball.envs.envs:RandomTerrain",
)

register(
    id="Terrain-tactile-ball",
    entry_point="mujoco_tactile_ball.envs.envs:Terrain",
)

register(
    id="Maze-tactile-ball",
    entry_point="mujoco_tactile_ball.envs.envs:Maze",
)