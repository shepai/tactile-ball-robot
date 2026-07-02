
from gymnasium.envs.registration import register

register(
    id="Flat-tactile-ball",
    entry_point="mujoco_tactile_ball.envs.flat:FlatTerrain",
)

register(
    id="Random-tactile-ball",
    entry_point="mujoco_tactile_ball.envs.generate_random:RandomTerrain",
)
