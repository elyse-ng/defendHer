# defendHer
Created by: Karate Kids: Amy Clinton, Catherine Zhou, Chanthana Lov, Crystal Wang, Daisy Thurlby, Elyse Ng

## Table of Contents
1. [Overview](#Overview)
2. [Demo Videos](#Demo-Videos)
2. [Project Structure](#Project-Structure)
3. [Prerequesites](#Prerequesites)
4. [Quick Start](#Quick-Start)
5. [Pipeline Details](#Pipeline-Details)
6. [AI Usage Decleration](#AI-Usage-Decleration)

## Overview
DefendHer is made by women, with the goal of empowering other women to learn self defense. 

A pipeline that records a user performing a self defense move via webcam, analyzes their body pose frame by frame with MediaPipe, and classifies whether their form is "good" or "bad" using a trained ML model.

DefendHer is a full stack educational web application that:
- Teaches three basic self defense moves (kick, punch, block)
- Has educational videos for each move with a walkthrough and demenstration 
- Has recording feature that tracks 33 points on your body which:
    - Can be replayed with pose tracker overlay
    - Feedback score with confidence rating

**Project Breakdown**

1. Data Collection: Videos of each move are organized into labeled folders and processed with MediaPipe's Pose Landmarker to extract 33 body landmark coordinates per frame.
2. Machine Learning Model Training: Used a Random Forest Classifier (per-frame prediction, aggregated by majority vote). ~400 source videos for trained models. 
3. Backend API: A FastAPI server loads the trained model(s) and accepts a video and returns a label + confidence score.
4. Front End: Fun UI design that is simple to use. Composing of 4 pages:
- Home: Introduction to start
- Levels: Three levels that have walkthrough, recording and feedback
- Tutorial: Teaches you how to use the interface
- About: A bit about our team :)
5. Connection from front end to back end: A webcam based recording interface (plain HTML/JS) captures the user's attempt, uploads it to the backend, and displays the altered video and feedback. 

## Demo Videos

https://github.com/user-attachments/assets/62dfc947-a535-4051-9c61-9f7f2a31daa9

https://github.com/user-attachments/assets/69d4689c-81a6-4d03-88ca-df7b60798810

https://github.com/user-attachments/assets/838f30c7-6be4-41fc-8b45-648f6feb5e40

https://github.com/user-attachments/assets/9e806f6a-4be2-45ac-9e20-705471a35291

https://github.com/user-attachments/assets/29079f5b-4923-428c-8fb5-9f8d75846740

## Project Structure
```
defendHer/
├── main.py                          # FastAPI backend — loads trained models, exposes /predict
├── pose_landmarker_full.task        # MediaPipe pose model
├── webm_to_mp4_converter.py         # helper for converting browser recordings if needed
│
├── get_coordinate.py                # extracts landmarks from a video -> CSV
├── get_coordinate_from_input.py
│
├── trial_videos/data/                # raw source videos, organized by action + label
│   ├── kick/{good,bad}/*.mp4|.mov
│   ├── punch/{good,bad}/*.mp4|.mov
│   └── chop/{good,bad}/*.mp4|.mov
│
├── kick_csvs/, punch_csvs/, chop_csvs/   # one CSV per video (landmarks per frame)
│   └── all_{action}.csv                  # combined dataset per action
│
├── model/
│   ├── classify_good_and_bad_punch_forest.py   # Random Forest training script
│   └── lstm_classifier.py                      # LSTM training script
│
├── {action}_random_forest_model.joblib         # trained Random Forest, per action
├── {action}_model_feature_columns.joblib       # feature column order, per action
│
│
├── outputs/                         # sample prediction outputs for debugging
│
└── website/                         # frontend
    ├── pages/                       # tutorial.html, level1-4.html, results pages, etc.
    ├── javascript/                  # camera.js, tutorialmain.js, results.js, per-level scripts
    ├── css/
    └── assets/
```

## Prerequisites
Browser Requirements: 
- MediaRecorder and getUserMedia support (Chrome, Safari, Firefox)
- Camera Permissions
Python ≥ 3.9
Live Server (extension)

mediapipe: Pose landmark detection from video

opencv-python: Video reading/frame handling (cv2)

numpy: Array/numeric operations

pandas: CSV handling, dataframes

scikit-learn: Random Forest model, train/test split, label encoding

joblib: Saving/loading the Random Forest model

fastapi	Backend: API framework

uvicorn: ASGI server to run the FastAPI app

python-multipart: Required by FastAPI to handle file uploads (UploadFile)

pillow / pillow-heif: Only needed if converting .HEIC images

### Note (if you want to train your own machine): Model/Data Files Required - Not installed by pip
The following model/data files exist on the GitHub for the model trained by source videos. To create your own model, upload data into trial_videos and classify them in the given folders. The following are produced by running the training scripts (model/classify_good_and_bad_punch_forest.py) against the CSV datasets. 

pose_landmarker_full.task — MediaPipe's pose landmark model file
Trained model artifacts, per action (kick, punch, chop):
{action}_random_forest_model.joblib
{action}_model_feature_columns.joblib

## Quick Start
1. Start backend
```bash
uvicorn main:app --reload
```
2. Start frontend
Acrivate live server

## Pipeline Details
Extracting landmarks -> Random Forest Model -> Backend FastAPI -> Frontend

### Extracting landmarks 
Uses `mediapipe.tasks.python.vision.PoseLandmarker` in `VIDEO` mode to detect 33 body landmarks per frame (x, y, z, visibility, presence). Each video's landmarks are written to a CSV with columns for `video_no`, `frame`, `timestamp_ms`, `correctness` (good/bad), and `x/y/z/visibility` per landmark. Per-video CSVs are combined into one dataset per action (`all_kick.csv`, etc.) using `pandas.concat`.

Note: Landmarks 1–10 (facial points: eyes, ears, nose, mouth) are excluded as irrelevant to pose classification.

### Random Forest Model 
- Trained directly on flattened per-frame feature rows.
- No label encoder needed — scikit-learn handles string labels (`"good"`/`"bad"`) natively.
- Saved artifacts: the model itself (`joblib.dump(model, ...)`) and the exact feature column order (`joblib.dump(list(X.columns), ...)`) — the column order **must** match at inference time.
- Inference: predicts every frame independently, then aggregates via majority vote across frames, with confidence as the average probability of the majority class.

### Backend Fast API
`main.py` loads all trained models into a dictionary at startup, keyed by action (`kick`, `punch`, `chop`), and exposes:

- `GET /` — health check
- `POST /predict` — accepts a video file (`file`) and an `action` field (`kick`/`punch`/`chop`)

Run locally:
```bash
uvicorn main:app --reload
```

### Front End
Plain HTML/CSS/JS (graphics, visuals, text)
- Requests webcam access via `getUserMedia`.
- Records with `MediaRecorder`, producing a `video/webm` Blob.
- On stop, uploads the blob to `/predict` via `fetch` + `FormData`.
- Displays the returned label and confidence.

**Icons and Assets** Hand-drawn

**Design Inspirations** Codex, Stardew Valley, T-rex game: Dino run

## Troubleshooting and Unresolved Issues

- **Unresponsive Video Upload**: make sure back end is running or restard backend. Start: uvicorn main:app --reload. Stop: CTR+C.

- **Media Pipe Mac Error**: Throws error for newest version of media pipe. If you have it installed,

```bash
pip3 uninstall mediapipe -y
pip3 install mediapipe==0.10.30
```
- **Library not installed" even though pip install succeeded**: Usually means pip3/python3 point to a different Python than the one actually running your script. Check with which python3 and which pip3, and reinstall using the exact interpreter you're running.

- **Camera won't turn on**: Make sure you've allowed camera access when your browser asked for permission. Close any other apps or browser tabs that might already be using your camera. Try refreshing the page and clicking "Start Camera" again.

- **No result**: Give it some time. Make sure your whole body is visible in frame and you have good lighting during your recording.

- **Strange results/seems incorrect**: Make sure you're doing the correct move for the level you're on, make sure your whole body is visible in frame and you have good lighting during your recording.

- **Frozen page**: Refresh or try another browser

### Unresolved Issues
- Different UI: UI can appear different on different devices
- Unresponsive: Sometimes video does not stop recording.
- Slow Feedback: Video generation can take up to one minute

## AI Usage Declaration
AI tools were used selectively to support the development of this project.

Tools and Usage:

ChatGPT: Used to develop the foundational code for camera.js. The generated code was heavily reviewed, edited, tested, and adapted by humans.

Claude: Used to assist with code generation and debugging for main_test.py and tutorial.js.

Human involvement: The overall project design, implementation, integration, testing, and final code decisions were completed by the project team. AI-generated code was reviewed and modified before being incorporated into the project.
