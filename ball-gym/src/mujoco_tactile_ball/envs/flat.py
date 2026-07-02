from .base import TactileGymEnv

class FlatTerrain(TactileGymEnv):
    def __init__(self):
        super().__init__(
            xml_subpath=["assets", "flat.xml"],
            obs_dim=9,
            action_dim=3
        )