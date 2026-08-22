# pip3 install fastapi uvicorn python-multipart scikit-learn joblib opencv-python mediapipe numpy pandas
# run main_test.py
# type in terminal: python -m uvicorn main_test:app --reload
# can do when says "Application startup complete"
import shutil
import tempfile
import json

import cv2
import numpy as np
from pathlib import Path
import pandas as pd
import joblib
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

ACTIONS = ["kick", "punch", "chop"]
POSE_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (18, 20), (11, 23),
    (12, 24), (23, 24), (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
    (24, 26), (26, 28), (28, 30), (30, 32), (28, 32), (11, 24),
)


# Models and load models
models = {}
feature_columns_by_action = {}

for action in ACTIONS:
    models[action] = joblib.load(f"{action}_random_forest_model.joblib")
    feature_columns_by_action[action] = joblib.load(f"{action}_model_feature_columns.joblib")

EXCLUDED_LANDMARK_INDICES = set(range(1, 11))  # must match training


# helpers
def extract_landmarks_from_video(video_path, pose_model_path="pose_landmarker_full.task"):
    BaseOptions = python.BaseOptions
    PoseLandmarker = python.vision.PoseLandmarker
    PoseLandmarkerOptions = python.vision.PoseLandmarkerOptions
    VisionRunningMode = python.vision.RunningMode

    output_dir = Path('./outputs')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_video_path = output_dir / 'result_coordinate.webm'
        

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=pose_model_path, delegate=BaseOptions.Delegate.CPU),
        running_mode=VisionRunningMode.VIDEO)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open video file")

    fps = cap.get(cv2.CAP_PROP_FPS)
    
    fps = 30

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(
        str(output_video_path), cv2.VideoWriter_fourcc(*'VP80'), fps,
        (width, height))
    if not writer.isOpened():
        raise ValueError('Could not create browser-compatible WebM output')

    print("VIDEO INFO:")
    print("FPS:", fps)
    print("Width:", width)
    print("Height:", height)

    rows = []

    with PoseLandmarker.create_from_options(options) as landmarker:
        frame_index = 0
        while cap.isOpened():
            hasFrame, image = cap.read()
            if not hasFrame:
                break

            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(image))
            frame_index += 1
            timestamp_ms = int(1000 * frame_index / fps)
            result = landmarker.detect_for_video(mp_image, timestamp_ms)
            annotated = image.copy()


            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]
                row = []
                for i, lm in enumerate(landmarks):
                    if i in EXCLUDED_LANDMARK_INDICES:
                        continue
                    row += [lm.x, lm.y, lm.z, lm.visibility]
                rows.append(row)

                points = []
                for landmark in landmarks:
                    point = (int(landmark.x * width), int(landmark.y * height))
                    points.append(point)
                    cv2.circle(annotated, point, 4, (0, 255, 0), -1)
                for start, end in POSE_CONNECTIONS:
                    cv2.line(annotated, points[start], points[end], (255, 0, 0), 2)

            writer.write(cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))

    cap.release()
    writer.release()

    if not rows:
        raise ValueError("No pose detected in any frame of the video")

    return rows


def predict_video(video_path, action):
    if action not in models:
        raise ValueError(f"Unknown action '{action}'. Must be one of {ACTIONS}")

    model = models[action]
    feature_columns = feature_columns_by_action[action]

    rows = extract_landmarks_from_video(video_path)
    df = pd.DataFrame(rows, columns=feature_columns)

    frame_preds = model.predict(df)
    frame_probs = model.predict_proba(df)

    values, counts = np.unique(frame_preds, return_counts=True)
    majority_label = values[np.argmax(counts)]

    class_index = list(model.classes_).index(majority_label)
    avg_confidence = frame_probs[:, class_index].mean()

    
    prediction = {
        "action": action,
        "label": str(majority_label),
        "confidence": round(float(avg_confidence), 3),
        "frames_analyzed": len(frame_preds)
    }

    output_dir = Path("./outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "prediction.json"
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(prediction, output_file, indent=2)

    return output_path


# Fast API
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "Martial arts classifier API is running", "actions": ACTIONS}


@app.post("/predict")
async def predict(file: UploadFile = File(...), action: str = Form(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        output_path = predict_video(tmp_path, action)
        return {
            "message": "Prediction saved",
            "output_file": str(output_path),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}