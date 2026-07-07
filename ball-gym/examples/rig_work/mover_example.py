# demo file for making the mover 

# can switch between different 3D textures and objects

import time
import gymnasium as gym
import mujoco_tactile_ball  

import mujoco
import cv2
import numpy as np

def main():
    env = gym.make("Rig-tactile-ball")
    obs, info = env.reset()

    model = env.unwrapped.model
    data = env.unwrapped.data

    # Offscreen renderer configuration
    width, height = 640, 480
    renderer = env.unwrapped.renderer

    # Define driving speeds
    BASE_SPEED = 1.5
    TURN_SPEED = 1.5
    target_velocities = [0.1,0.1,0.1,np.pi/2,0,0,0]

    print("Control setup complete. CLICK AND FOCUS THE 'third_person_view' WINDOW TO DRIVE.")
    
    cam = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(cam)
    cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
    cam.trackbodyid = model.body('robot').id  # Locks onto your robot ID
    cam.distance = 1.5                         # Distance from the robot (meters)
    cam.elevation = -20                        # Vertical angle look-down
    cam.azimuth = 120 

    try:
        obs, reward, terminated, truncated, info = env.step(target_velocities.copy())
        for i in np.arange(0,0.2,0.001):
            for j in np.arange(0,0.2,0.001):
                for k in np.arange(0,0.05,0.001):
                    # 1. Render and draw scenes regardless of keyboard interactions
                    target_velocities[0]=i
                    target_velocities[1]=j
                    target_velocities[2]=0.1-k
                    renderer.update_scene(data, camera=cam)
                    rgb_img = renderer.render()
                    left_view=cv2.cvtColor(obs['sensor_cam_left']*255, cv2.COLOR_RGB2BGR).astype(np.uint8)
                    h, w = 100, 120
                    left_view = cv2.resize(left_view, (w, h), interpolation=cv2.INTER_AREA)
                    bgr_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)
                    H, W = bgr_img.shape[:2]
                    x1 = W - w
                    x2 = W
                    y1 = 0
                    y2 = h
                    y1 = h
                    y2 = 2 * h
                    bgr_img[y1:y2, x1:x2] = left_view
                    cv2.imshow("third_person_view", bgr_img)
                    # 2. Extract input with 1ms cycle yield
                    key = cv2.waitKey(1) & 0xFF
                
                    if key == ord('q') or key == 27:
                        break
                    obs, reward, terminated, truncated, info = env.step(target_velocities.copy())

    finally:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
