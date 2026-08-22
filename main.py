# pip3 install fastapi uvicorn python-multipart torch mediapipe opencv-python numpy scikit-learn

import shutil
import tempfile
import pickle

import cv2
import numpy as np
import torch
import torch.nn as nn
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware


# ----------------------------
# Model definition (must match training exactly)
# ----------------------------
class LSTMClassifier(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=1, num_classes=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        last_hidden = h_n[-1]
        out = self.fc(last_hidden)
        return out


# ----------------------------
# Load config, label encoder, and model once at startup
# ----------------------------
with open("kick_model_config.pkl", "rb") as f:
    config = pickle.load(f)

MAX_LEN = config["max_len"]
NUM_FEATURES = config["num_features"]

with open("kick_label_encoder.pkl", "rb") as f:
    le = pickle.load(f)

model = LSTMClassifier(input_size=NUM_FEATURES, hidden_size=64, num_classes=len(le.classes_))
model.load_state_dict(torch.load("kick_lstm_model.pth", map_location=torch.device("cpu")))
model.eval()

EXCLUDED_LANDMARK_INDICES = set(range(1, 11))  # must match training


# ----------------------------
# Inference helpers
# ----------------------------
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
        fps = 30  # fallback

    frames_data = []

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
                frames_data.append(row)

    cap.release()

    if not frames_data:
        raise ValueError("No pose detected in any frame of the video")

    return np.array(frames_data, dtype=np.float32)


def predict_video(video_path):
    seq = extract_landmarks_from_video(video_path)

    padded = np.zeros((MAX_LEN, seq.shape[1]), dtype=np.float32)
    length = min(seq.shape[0], MAX_LEN)
    padded[:length] = seq[:length]

    x = torch.tensor(padded, dtype=torch.float32).unsqueeze(0)

    with torch.no_grad():
        outputs = model(x)
        probs = torch.softmax(outputs, dim=1)
        pred_idx = torch.argmax(probs, dim=1).item()
        confidence = probs[0, pred_idx].item()

    label = le.inverse_transform([pred_idx])[0]
    return {"label": str(label), "confidence": round(confidence, 3)}


# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict this to your real frontend domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "Kick classifier API is running"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        print("yaaaa")

    try:
        result = predict_video(tmp_path)
        return result
    except ValueError as e:
        return {"error": str(e)}