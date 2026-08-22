import csv
import cv2
import numpy as np
import mediapipe as mp
import pandas as pd
from pathlib import Path
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

POSE_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (18, 20), (11, 23),
    (12, 24), (23, 24), (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
    (24, 26), (26, 28), (28, 30), (30, 32), (28, 32), (11, 24),
)

def main(video_path):
    video_path = Path(video_path)
    model_path = 'pose_landmarker_full.task'
    output_dir = Path('./outputs')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_video_path = output_dir / f'{video_path.stem}_coordinate.mp4'
    output_csv_path = output_dir / f'{video_path.stem}_coordinate.csv'

    header = ["video_no","frame", "timestamp_ms", "good"]
    for i in range(33):
        header += [f"x{i}", f"y{i}", f"z{i}", f"visibility{i}"]

    BaseOptions = python.BaseOptions
    PoseLandmarker = python.vision.PoseLandmarker
    PoseLandmarkerOptions = python.vision.PoseLandmarkerOptions
    VisionRunningMode = python.vision.RunningMode
    options = PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=model_path),
                                    running_mode=VisionRunningMode.VIDEO)
    cap = cv2.VideoCapture(str(video_path))

    if cap.isOpened() is False:
        raise FileNotFoundError(f'Video not found: {video_path}')
    # Load the frame rate of the video using OpenCV’s CV_CAP_PROP_FPS
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(
        str(output_video_path), cv2.VideoWriter_fourcc(*'mp4v'), fps,
        (width, height))
    rows = []
    # You’ll need it to calculate the timestamp for each frame.
        
    # Loop through each frame in the video using VideoCapture#read()
    # Convert the frame received from OpenCV to a MediaPipe’s Image object.
    # Detect poses from mages
    # Extract pose landmarks
    # Extract pose landmarks
    

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
            frame_timestamp_ms = int(1000 * frame_index / fps)
            result = landmarker.detect_for_video(mp_image, frame_timestamp_ms)
            row = [video_path.stem, frame_index, frame_timestamp_ms, 'good']
            annotated = image.copy()
        
            #pose landmarks for each frame
            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]
                row.extend(
                    value for landmark in landmarks
                    for value in (landmark.x, landmark.y, landmark.z,
                                  landmark.visibility))
                points = []
                for landmark in landmarks:
                    point = (int(landmark.x * width), int(landmark.y * height))
                    points.append(point)
                    cv2.circle(annotated, point, 4, (0, 255, 0), -1)
                for start, end in POSE_CONNECTIONS:
                    cv2.line(annotated, points[start], points[end], (255, 0, 0), 2)
            else:
                row.extend([np.nan] * (33 * 4))

            rows.append(row)
            writer.write(cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))

        cap.release()
        writer.release()

    pd.DataFrame(rows, columns=header).to_csv(output_csv_path, index=False)
    return str(output_video_path), str(output_csv_path)


if __name__ == "__main__":
    output_vid_path, output_csv_path = main(video_path="trial_videos/punch/punch_cz_2.mp4")