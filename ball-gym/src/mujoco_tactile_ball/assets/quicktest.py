import mujoco
import mujoco.viewer

# Path to your robot XML
XML_PATH = "/home/dexter/Documents/GitHub/tactile-ball-robot/ball-gym/src/mujoco_tactile_ball/assets/flat.xml"

# Load model
model = mujoco.MjModel.from_xml_path(XML_PATH)
data = mujoco.MjData(model)

# Launch viewer
with mujoco.viewer.launch_passive(model, data) as viewer:
    while viewer.is_running():
        mujoco.mj_step(model, data)
        viewer.sync()