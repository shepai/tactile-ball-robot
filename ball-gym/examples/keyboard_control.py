import time
import gymnasium as gym
import mujoco_tactile_ball  

import mujoco
import cv2


def main():
    env = gym.make("Flat-tactile-ball")
    obs, info = env.reset()

    model = env.unwrapped.model
    data = env.unwrapped.data

    # Offscreen renderer configuration
    width, height = 640, 480
    renderer = env.unwrapped.renderer

    # Define driving speeds
    BASE_SPEED = 0.4
    TURN_SPEED = 1.5
    target_velocities = [0.0, 0.0]

    # Warmup loop
    for _ in range(100):
        obs, reward, terminated, truncated, info = env.step([0.0, 0.0])

    print("Control setup complete. CLICK AND FOCUS THE 'third_person_view' WINDOW TO DRIVE.")
    
    # Track physical loop timings
    dt = model.opt.timestep
    last_time = time.perf_counter()

    try:
        while True:
            # 1. Render and draw scenes regardless of keyboard interactions
            renderer.update_scene(data, camera="third person")
            rgb_img = renderer.render()

            bgr_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)

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
            else:
                # Gradual friction slowdown
                target_velocities[0] *= 0.85
                target_velocities[1] *= 0.85

                if abs(target_velocities[0]) < 0.05: target_velocities[0] = 0.0
                if abs(target_velocities[1]) < 0.05: target_velocities[1] = 0.0

            # 3. Environment physical update step
            obs, reward, terminated, truncated, info = env.step(target_velocities)

            if terminated:
                obs, info = env.reset()
                target_velocities = [0.0, 0.0]

            # 4. CRITICAL FIX: Precision timing loop to stop OS events from freezing frames
            elapsed = time.perf_counter() - last_time
            if elapsed < dt:
                time.sleep(dt - elapsed)
            last_time = time.perf_counter()

    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
