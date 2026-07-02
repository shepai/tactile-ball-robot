import time
import gymnasium as gym
import mujoco_tactile_ball  

import mujoco.viewer
import cv2
import glfw  # MuJoCo uses GLFW under the hood for key codes


# Global variable or dictionary to track key presses
pressed_keys = {
    "forward": False,
    "backward": False,
    "left": False,
    "right": False
}

def key_callback(keycode):
    """Callback function triggered when a key is pressed or released in the viewer."""
    # Maps GLFW key numbers to directions. 
    # Use ASCII values or GLFW constants (e.g., GLFW_KEY_W is 87)
    
    # Check if a key was pressed or released (MuJoCo passes the raw keycode)
    # Note: launch_passive natively handles standard ASCII values for characters
    key_char = chr(keycode).lower() if 32 <= keycode <= 126 else ""

    # Reset keys first if you want discrete presses, 
    # or implement press/release tracking depending on your exact setup.
    # The default MuJoCo passive viewer callback triggers on standard key down events.
    if key_char == 'w':
        pressed_keys["forward"] = True
    elif key_char == 's':
        pressed_keys["backward"] = True
    elif key_char == 'a':
        pressed_keys["left"] = True
    elif key_char == 'd':
        pressed_keys["right"] = True
    else:
        # Clear movement when any other key or no key is recognized
        for key in pressed_keys:
            pressed_keys[key] = False


def get_velocities_from_keys(base_speed=5.0, turn_speed=2.5):
    """Converts active directions into left and right target velocities."""
    left_vel = 0.0
    right_vel = 0.0

    if pressed_keys["forward"]:
        left_vel = base_speed
        right_vel = base_speed
    elif pressed_keys["backward"]:
        left_vel = -base_speed
        right_vel = -base_speed
    elif pressed_keys["left"]:
        left_vel = -turn_speed
        right_vel = turn_speed
    elif pressed_keys["right"]:
        left_vel = turn_speed
        right_vel = -turn_speed

    # Reset flags after reading so it stops when you release/stop pressing
    # (Since passive viewer callback captures single discrete keydown ticks)
    for key in pressed_keys:
        pressed_keys[key] = False

    return [left_vel, right_vel]


def main():

    env = gym.make("Flat-tactile-ball")

    obs, info = env.reset()

    model = env.unwrapped.model
    data = env.unwrapped.data

    # Launch viewer and assign the key callback function
    with mujoco.viewer.launch_passive(model, data, key_callback=key_callback) as viewer:

        while viewer.is_running():
            
            # 1. Translate current keyboard flags into velocity values
            target_velocities = get_velocities_from_keys(base_speed=0.3, turn_speed=0.6)

            # 2. Pass the [left_velocity, right_velocity] directly to your step function
            obs, reward, terminated, truncated, info = env.step(target_velocities)

            # Sync viewer with updated physics
            viewer.sync()

            # reset if episode ends
            if terminated:
                obs, info = env.reset()
            # small sleep so it doesn't max CPU
            time.sleep(env.unwrapped.model.opt.timestep)


if __name__ == "__main__":
    main()
