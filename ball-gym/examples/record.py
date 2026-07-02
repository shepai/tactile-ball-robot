import time
import gymnasium as gym
import mujoco_tactile_ball  

import cv2
import numpy as np
import mujoco

def main():

    env = gym.make("Flat-tactile-ball")

    obs, info = env.reset()

    model = env.unwrapped.model
    data = env.unwrapped.data

    # MuJoCo offscreen renderer (for gym view)
    renderer = mujoco.Renderer(model, height=480, width=480)

    # Video writer (side-by-side = double width)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(
        "rollout.mp4",
        fourcc,
        30,
        (480*4, 480)  # 2 x 480 width
    )

    try:
        action = env.action_space.sample()
        for _ in range(500):

            if _%100==0:
                action = env.action_space.sample()

            obs, reward, terminated, truncated, info = env.step(action)

            renderer.update_scene(data,camera="third person")
            gym_img = renderer.render()  # (H, W, 3), uint8
            for image_name in ["front_cam","sensor_cam_left","sensor_cam_right"]: #go through all cameras
                tactile_img = obs[image_name]

                # ensure correct format
                if tactile_img.dtype != np.uint8:
                    tactile_img = (tactile_img * 255).astype(np.uint8)

                # resize both to same height
                gym_img = cv2.resize(gym_img, (480, 480))
                tactile_img = cv2.resize(tactile_img, (480, 480))

                # convert RGB → BGR for OpenCV
                gym_img = cv2.cvtColor(gym_img, cv2.COLOR_RGB2BGR)
                tactile_img = cv2.cvtColor(tactile_img, cv2.COLOR_RGB2BGR)
                # 3. stack side-by-side
                gym_img = np.hstack([gym_img, tactile_img])
            # write frame
            video.write(gym_img)

            if terminated:
                    obs, info = env.reset()

            time.sleep(env.unwrapped.model.opt.timestep)

    finally:
        video.release()
        env.close()
        print("Saved rollout.mp4")

if __name__ == "__main__":
    main()