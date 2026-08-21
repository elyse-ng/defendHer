import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# reference https://gist.github.com/rmeziatisab/20820a7c8cc667a1da44f22bcbcb7923

model_path = 'pose_landmarker_full.task';

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


# Load input
# Use OpenCV’s VideoCapture to load the input video.
input_path = "trial_videos/kick/kick_ac_1.mp4"
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
        print(frame_index)