# uses the mover gym to press on different objects 
#gather the image and then map it to the vector movemet/ force and label of object in a csv 

DATA_SAVE_PATH="/home/dexter/Documents/data/simulation/"
import os
import csv
import time
import gymnasium as gym
import mujoco_tactile_ball  
import pandas as pd
import cv2
import numpy as np
from tqdm import tqdm
import shutil
def get_folder_size(folder_path):
    total_size = 0
    for dirpath, _, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024**3)  # GB


def get_disk_space(folder_path):
    total, used, free = shutil.disk_usage(folder_path)
    return free / (1024**3)  # GB
# store recordings here
recordings = []

env = gym.make("Rig-tactile-ball")
obs, info = env.reset()

model = env.unwrapped.model
data = env.unwrapped.data

start = [0.3,0.3,0.22,np.pi/2,0,0,0]
obs, reward, terminated, truncated, info = env.step(start.copy())
c = 0

# Calculate total number of samples for progress bar
total_samples = (
    len(np.arange(0,0.3,0.1)) *
    6 *
    len(np.arange(0,0.2,0.1)) *
    len(np.arange(0,0.2,0.1)) *
    len(np.arange(0,0.05,0.001))
)

with tqdm(total=total_samples, desc="Collecting data") as pbar:

    for speed in np.arange(0,0.3,0.1):

        start[-1] = speed
        for texture_id in range(6):
            env.unwrapped.set_texture(texture_id)
            for i in np.arange(0,0.2,0.1):
                for j in np.arange(0,0.2,0.1):
                    for k in np.arange(0,0.05,0.001):

                        target = start.copy()
                        target[0] = start[0] + i
                        target[1] = start[1] + j
                        target[2] = start[2] - k

                        obs, reward, terminated, truncated, info = env.step(target.copy())


                        # Save tactile image
                        image_name = f"{c}.png"
                        image_path = os.path.join(
                            DATA_SAVE_PATH,
                            "images",
                            image_name
                        )

                        left_view = cv2.cvtColor(
                            obs['sensor_cam_left']*255,
                            cv2.COLOR_RGB2BGR
                        ).astype(np.uint8)
                        gray = cv2.cvtColor(
                            left_view,
                            cv2.COLOR_BGR2GRAY
                        )
                        cv2.imwrite(image_path, gray,[cv2.IMWRITE_PNG_COMPRESSION, 9])


                        # Get marker positions
                        markers = env.unwrapped.get_markers()

                        row = {
                            "image_id": c,
                            "x": target[0],
                            "y": target[1],
                            "z": target[2],
                            "speed": speed,
                            "texture_id": texture_id,
                        }


                        # Add markers dynamically
                        for marker_id, marker in enumerate(markers):
                            row[f"marker_{marker_id}_x"] = marker[0]
                            row[f"marker_{marker_id}_y"] = marker[1]
                            row[f"marker_{marker_id}_z"] = marker[2]


                        recordings.append(row)


                        c += 1
                        if c % 100 == 0:
                            df = pd.DataFrame(recordings)

                            csv_path = os.path.join(
                                DATA_SAVE_PATH,
                                "recordings.csv"
                            )

                            # Append if file already exists
                            df.to_csv(
                                csv_path,
                                mode="a",
                                header=not os.path.exists(csv_path),
                                index=False
                            )

                            # Clear memory
                            recordings = []

                        folder_size = get_folder_size(DATA_SAVE_PATH)
                        free_space = get_disk_space(DATA_SAVE_PATH)

                        pbar.set_postfix({
                            "data": f"{folder_size:.2f} GB",
                            "free": f"{free_space:.2f} GB"
                        })
                        if folder_size >= free_space-50-folder_size: #keep 50GB
                            print("Storage limit reached. Stopping collection.")
                            exit()
                        pbar.update(1)

# Convert to dataframe
df = pd.DataFrame(recordings)

# Save CSV
csv_path = os.path.join(
    DATA_SAVE_PATH,
    "recordings.csv"
)

df.to_csv(csv_path, index=False)

print(f"Saved {len(df)} recordings")