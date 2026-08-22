#windows: pip install scikit-learn
#mac: pip3 install scikit-learn
import joblib # save model
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

actions = ["kick", "punch", "chop"]
kick_data = None
punch_data = None
chop_data = None

for action in actions: 
    drop_columns = []
    for i in range(10):
        drop_columns += [f"x{i+1}", f"y{i+1}", f"z{i+1}", f"visibility{i+1}"]

    csv = f"{action}_csvs/all_{action}.csv" # CSV for coordinates
    df = pd.read_csv(csv)
    df = df.drop(columns=drop_columns)

    y = df["good"] #train to identify good/bad

    non_feature_columns = ["video_no", "frame", "timestamp_ms", "good"]
    X = df.drop(columns=non_feature_columns)

    print("X shape:", X.shape)
    print("y shape:", y.shape)
    print(y.value_counts())

    # Split into 70/30 training testing
    # Reference: https://madewithml.com/courses/mlops/splitting/
    train_size = 0.7
    val_size = 0.15
    test_size = 0.15

    # split train
    X_train, X_, y_train, y_ = train_test_split(X, y, train_size=train_size, stratify=y)

    #split test
    X_val, X_test, y_val, y_test = train_test_split(X_, y_, train_size=0.5, stratify=y_)

    #train model 
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Predict on validation set
    y_val_pred = model.predict(X_val)

    # Get accuracy metrics
    print("Validation Accuracy:", accuracy_score(y_val, y_val_pred))
    print("\nClassification Report:\n", classification_report(y_val, y_val_pred))
    print("\nConfusion Matrix:\n", confusion_matrix(y_val, y_val_pred))

    # save the model to ./models/[type]/[hyperparameter]_timestamp

    joblib.dump(model, f"{action}_random_forest_model.joblib")
    joblib.dump(list(X.columns), f"{action}_model_feature_columns.joblib")