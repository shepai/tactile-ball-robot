from .base import TactileGymEnv

class FlatTerrain(TactileGymEnv):
    def __init__(self):
        super().__init__(
            xml_subpath=["assets","robot", "mainbody.xml"],
            obs_dim=9,
            action_dim=3
        )

class Terrain(TactileGymEnv):
    def __init__(self):
        super().__init__(
            xml_subpath=["assets","robot", "terrain.xml"],
            obs_dim=9,
            action_dim=3
        )

class RandomTerrain(TactileGymEnv):
    pass