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

    # MuJoCo offscreen renderer config (Width=640, Height=480)
    renderer = mujoco.Renderer(model, height=480, width=640)

    # Video writer (1 master view + 3 camera feeds = 4 panels horizontally)
    # Total width = 640 * 4 = 2560 pixels wide
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(
        "rollout.mp4",
        fourcc,
        30,
        ((640//2) * 4, 480//2)  
    )

    try:
        action = env.action_space.sample()
        for _ in range(500):

            if _ % 100 == 0:
                action = env.action_space.sample()

            obs, reward, terminated, truncated, info = env.step(action)

            # 1. Render the main third-person scene
            renderer.update_scene(data, camera="third person")
            raw_gym_img = renderer.render()  # (480, 640, 3)
            
            # Convert RGB → BGR and match orientation mapping
            gym_img = cv2.cvtColor(raw_gym_img, cv2.COLOR_RGB2BGR)
            # FIX 1: Corrected Resize to (Width, Height)
            gym_img = cv2.resize(gym_img, (640//2, 480//2))
            # Start an array tracking list containing our first main frame panel
            panels = [gym_img]
            # 2. Iterate through and collect the tactile frames
            for image_name in ["front_cam", "sensor_cam_left", "sensor_cam_right"]:
                tactile_img = obs[image_name]
                #print(image_name,np.average(tactile_img))
                if tactile_img.dtype != np.uint8:
                    tactile_img = (tactile_img * 255).astype(np.uint8)
                # Format layout space for sub-cameras
                tactile_bgr = cv2.cvtColor(tactile_img, cv2.COLOR_RGB2BGR)
                # FIX 2: Corrected Resize dimensions to (Width, Height)
                tactile_resized = cv2.resize(tactile_bgr, (640//2, 480//2))
                # Append this processed block to your canvas list
                panels.append(tactile_resized)

            # FIX 3: Horizontally stack all 4 clean panels together at once
            final_composite_frame = np.hstack(panels)

            # Display the aligned image canvas layout
            cv2.imshow("display", final_composite_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
                
            # Stream the complete frame out to the video file
            video.write(final_composite_frame)
            
            if terminated:
                obs, info = env.reset()

            time.sleep(env.unwrapped.model.opt.timestep)

    finally:
        video.release()
        env.close()
        cv2.destroyAllWindows()
        print("Saved rollout.mp4 successfully.")

if __name__ == "__main__":
    main()
