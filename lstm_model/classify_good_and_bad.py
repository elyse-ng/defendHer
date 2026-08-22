#windows: pip install scikit-learn
#mac: pip3 install scikit-learn

from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split

actions = ["kick", "punch"]
kick_data = None
punch_data = None

drop_columns = []
for i in range(10):
    drop_columns += [f"x{i+1}", f"y{i+1}", f"z{i+1}", f"visibility{i+1}"]

for action in actions: 
    csv = f"{action}_csvs/all_{action}.csv" # CSV for coordinates
    df = pd.read_csv(csv)
    df = df.drop(columns=drop_columns)

    if action == "kick":
        kick_data = df
    elif action == "punch":
        punch_data = df

    #CHECK 
    print(kick_data.columns.tolist())
    print(punch_data.columns.tolist())

    # Transform data to relevant formats

# Split into 70/30 training testing
# train, test = train_test_split({action}_data,test_size=0.3)

# Decide model hyperparameters
# Build model
# Train model

# Get accuracy metrics

# save the model to ./models/[type]/[hyperparameter]_timestamp
