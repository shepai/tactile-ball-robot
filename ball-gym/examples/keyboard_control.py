import time
import gymnasium as gym
import mujoco_tactile_ball  

import mujoco
import cv2


def main():
    env = gym.make("Terrain-tactile-ball")
    obs, info = env.reset()

    model = env.unwrapped.model
    data = env.unwrapped.data

    # Offscreen renderer configuration
    width, height = 640, 480
    renderer = env.unwrapped.renderer

    # Define driving speeds
    BASE_SPEED = 1.5
    TURN_SPEED = 1.5
    target_velocities = [0.0, 0.0]

    # Warmup loop
    for _ in range(100):
        obs, reward, terminated, truncated, info = env.step([0.0, 0.0])

    print("Control setup complete. CLICK AND FOCUS THE 'third_person_view' WINDOW TO DRIVE.")
    
    # Track physical loop timings
    dt = model.opt.timestep
    last_time = time.perf_counter()
    recording=False
    video=False
    try:
        obs, reward, terminated, truncated, info = env.step(target_velocities)
        while True:
            # 1. Render and draw scenes regardless of keyboard interactions
            renderer.update_scene(data, camera="third person")
            rgb_img = renderer.render()
            robo_view=cv2.cvtColor(obs['front_cam']*255, cv2.COLOR_RGB2BGR)
            left_view=cv2.cvtColor(obs['sensor_cam_left']*255, cv2.COLOR_RGB2BGR)
            right_view=cv2.cvtColor(obs['sensor_cam_right']*255, cv2.COLOR_RGB2BGR)
            h, w = 100, 120
            robo_view = cv2.resize(robo_view, (w, h), interpolation=cv2.INTER_AREA)
            left_view = cv2.resize(left_view, (w, h), interpolation=cv2.INTER_AREA)
            right_view = cv2.resize(right_view, (w, h), interpolation=cv2.INTER_AREA)
            bgr_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)
            H, W = bgr_img.shape[:2]
            x1 = W - w
            x2 = W
            y1 = 0
            y2 = h
            bgr_img[y1:y2, x1:x2] = robo_view
            y1 = h
            y2 = 2 * h
            bgr_img[y1:y2, x1:x2] = left_view
            y1 = 2 * h
            y2 = 3 * h
            bgr_img[y1:y2, x1:x2] = right_view
            cv2.imshow("third_person_view", bgr_img)
            # 2. Extract input with 1ms cycle yield
            key = cv2.waitKey(1) & 0xFF
        
            if key == ord('q') or key == 27:
                break

            if key == ord('w'):
                target_velocities = [BASE_SPEED, -BASE_SPEED]
            elif key == ord('s'):
                target_velocities = [-BASE_SPEED, BASE_SPEED]
            elif key == ord('a'):
                target_velocities = [-TURN_SPEED, -TURN_SPEED]
            elif key == ord('d'):
                target_velocities = [TURN_SPEED, TURN_SPEED]
            elif key == ord("r"):
                if recording:
                    video.release()
                else:
                    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                    video = cv2.VideoWriter(
                        "keyboard_example.mp4",
                        fourcc,
                        30,
                        (640, 480)  
                    )
                recording=not recording
            else:
                # Gradual friction slowdown
                target_velocities[0] *= 0.85
                target_velocities[1] *= 0.85

                if abs(target_velocities[0]) < 0.05: target_velocities[0] = 0.0
                if abs(target_velocities[1]) < 0.05: target_velocities[1] = 0.0

            # 3. Environment physical update step
            obs, reward, terminated, truncated, info = env.step(target_velocities)
            if recording:
                video.write(bgr_img)
            if terminated:
                obs, info = env.reset()
                target_velocities = [0.0, 0.0]

            # 4. CRITICAL FIX: Precision timing loop to stop OS events from freezing frames
            elapsed = time.perf_counter() - last_time
            if elapsed < dt:
                time.sleep(dt - elapsed)
            last_time = time.perf_counter()

    finally:
        if recording:
            video.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
