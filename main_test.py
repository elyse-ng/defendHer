# pip3 install fastapi uvicorn python-multipart scikit-learn joblib opencv-python mediapipe numpy pandas

import shutil
import tempfile

import cv2
import numpy as np
import pandas as pd
import joblib
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

ACTIONS = ["kick", "punch", "chop"]

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

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=pose_model_path, delegate=BaseOptions.Delegate.CPU),
        running_mode=VisionRunningMode.VIDEO)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open video file")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30

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

            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]
                row = []
                for i, lm in enumerate(landmarks):
                    if i in EXCLUDED_LANDMARK_INDICES:
                        continue
                    row += [lm.x, lm.y, lm.z, lm.visibility]
                rows.append(row)

    cap.release()

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

    return {
        "action": action,
        "label": str(majority_label),
        "confidence": round(float(avg_confidence), 3),
        "frames_analyzed": len(frame_preds)
    }


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
        result = predict_video(tmp_path, action)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}