#for windows: 
# pip install mediapipe
# pip install pandas

#for mac: 
    #if you have it installed: pip3 uninstall mediapipe -y
    #pip3 install mediapipe==0.10.30
    #pip3 install pandas

import csv
import cv2
import numpy as np
import mediapipe as mp
import pandas as pd
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from pathlib import Path

model_path = 'pose_landmarker_full.task';

header = ["video_no","frame", "timestamp_ms", "good"]
for i in range(33):
    header += [f"x{i}", f"y{i}", f"z{i}", f"visibility{i}"]

# reference https://gist.github.com/rmeziatisab/20820a7c8cc667a1da44f22bcbcb7923

BaseOptions = python.BaseOptions
PoseLandmarker = python.vision.PoseLandmarker
PoseLandmarkerOptions = python.vision.PoseLandmarkerOptions
VisionRunningMode = python.vision.RunningMode
options = PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=model_path),
                                running_mode=VisionRunningMode.VIDEO)
# Create a pose landmarker instance with the video mode:
options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.VIDEO)

data_folder = Path("trial_videos/data")
kick_output = Path("kick_csvs")
punch_output = Path("punch_csvs")
kick_output.mkdir(exist_ok=True)
punch_output.mkdir(exist_ok=True)

# Load input for each video in the folder
# Use OpenCV’s VideoCapture to load the input video.
for action_type_folder in data_folder.iterdir():
    if not action_type_folder.is_dir():
        continue 
    action = action_type_folder.name #punch, kick

    for correctness_folder in action_type_folder.iterdir():
        if not correctness_folder.is_dir():
            continue
        correctness = correctness_folder.name #good or bad

        video_files = list(correctness_folder.glob("*.mp4")) + list(correctness_folder.glob("*.mov"))

        for video_path in video_files:
            input_path = str(video_path)
            if action == "kick":
                out_csv = kick_output / f"{action}_{correctness}_{video_path.stem}_kick.csv"
            elif action == "punch":
                out_csv = punch_output / f"{action}_{correctness}_{video_path.stem}_punch.csv"

            cap = cv2.VideoCapture(input_path)

            if cap.isOpened() is False:
                print ("video not found :(")
                exit()

            # Load the frame rate of the video using OpenCV’s CV_CAP_PROP_FPS
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            # You’ll need it to calculate the timestamp for each frame.

            # Loop through each frame in the video using VideoCapture#read()
            # Convert the frame received from OpenCV to a MediaPipe’s Image object.
            # Detect poses from mages
            # Extract pose landmarks
            # Extract pose landmarks
            with open(out_csv, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)

                with PoseLandmarker.create_from_options(options) as landmarker:
                    frame_index = 0
                    while cap.isOpened():
                        hasFrame, image = cap.read()
                        if not hasFrame:
                            print('No more frames to read!')
                            break

                        # Reorder the RGB color channels as data is loaded with the BGR order with the read method
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        # Transform the frame to a NumPy ndarray before converting it to an Image
                        numpy_frame_from_opencv = np.asarray(image)
                        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=numpy_frame_from_opencv)
                        frame_index += 1 # you can use cap.get(cv2.CAP_PROP_POS_FRAMES) instead
                        # Compute the frame timestamp and cast it to int as required by the detect_for_video function
                        frame_timestamp_ms = int(1000*frame_index / fps)
                        result = landmarker.detect_for_video(mp_image, frame_timestamp_ms)
                        row = [video_path.stem, frame_index, frame_timestamp_ms, correctness]

                        #pose landmarks for each frame
                        if result.pose_landmarks:
                            landmarks = result.pose_landmarks[0]
                            for lm in landmarks:
                                row += [lm.x, lm.y, lm.z, lm.visibility]
                        else:
                            row += [""] * (33 * 4)

                        writer.writerow(row)
            cap.release()

all_kick_csv = list(kick_output.glob("*.csv"))
all_punch_csv = list(punch_output.glob("*.csv"))

if all_kick_csv:
    df_kick = pd.concat([pd.read_csv(f) for f in all_kick_csv], ignore_index=True)
    df_kick.to_csv(kick_output / "all_kick.csv", index=False)

if all_punch_csv:
    df_punch = pd.concat([pd.read_csv(f) for f in all_punch_csv], ignore_index=True)
    df_punch.to_csv(punch_output / "all_punch.csv", index=False)
